"""Learning-effectiveness measurement engine.

Computes deterministic, interpretable metrics by comparing assessment data
across lifecycle phases.  All computations use assessment scores, difficulty
information, and misconception data — never LLM judgments.

Metrics produced:
- Observed improvement (raw score delta)
- Independent improvement (unassisted-only delta)
- Difficulty-adjusted comparison flag
- Misconception resolution analysis
- Evidence sufficiency and confidence level
- Retention measurement
- Transfer performance

Important: these are *observed measurements*, not causal claims.  Actual
improvement must be validated with pilot assessment data.  Do not present
these metrics as proof that tutoring caused the improvement.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.effectiveness_models import (
    AssessmentPhase,
    AssessmentStatus,
    EffectivenessSnapshot,
    LearningAssessment,
)
from app.models import StudentSkill

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Minimum items to consider evidence sufficient
MIN_EVIDENCE_ITEMS = 3

# Maximum difficulty gap that still counts as "comparable"
MAX_DIFFICULTY_GAP = 1.0

# Confidence thresholds based on evidence count
CONFIDENCE_THRESHOLDS = {
    "HIGH": 8,       # >= 8 items across both assessments
    "MODERATE": 5,   # >= 5 items
    "LOW": 3,        # >= 3 items
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MisconceptionAnalysis:
    """Analysis of misconception changes between assessments."""
    baseline: list[str]
    comparison: list[str]
    resolved: list[str]     # in baseline but not in comparison
    persisting: list[str]   # in both
    new: list[str]          # in comparison but not in baseline


@dataclass(frozen=True)
class EffectivenessMetrics:
    """Complete effectiveness measurement for a student-skill pair.

    This is the primary output of the measurement engine.  All fields
    are deterministically computed from assessment data.
    """
    student_id: uuid.UUID
    skill_id: uuid.UUID
    measurement_type: str  # "GROWTH", "RETENTION", "TRANSFER"

    baseline_score: Decimal | None
    baseline_independent_score: Decimal | None
    comparison_score: Decimal | None
    comparison_independent_score: Decimal | None

    # GROWTH / RETENTION: score delta (same-skill comparison)
    # TRANSFER: None — cross-skill subtraction is never used
    observed_improvement: Decimal | None
    independent_improvement: Decimal | None

    baseline_difficulty_mean: Decimal | None
    comparison_difficulty_mean: Decimal | None
    difficulty_comparable: bool

    misconception_analysis: MisconceptionAnalysis

    evidence_count: int
    evidence_sufficient: bool
    confidence_level: str  # "INSUFFICIENT", "LOW", "MODERATE", "HIGH"

    # Fields with defaults must come after all required fields
    # TRANSFER only: absolute performance on the target skill
    transfer_performance: Decimal | None = None
    baseline_assessment_id: uuid.UUID | None = None
    comparison_assessment_id: uuid.UUID | None = None


@dataclass
class SkillEffectivenessReport:
    """Aggregated effectiveness report for one skill across all phases."""
    student_id: uuid.UUID
    skill_id: uuid.UUID
    skill_code: str
    skill_name: str

    # Current mastery state from StudentSkill
    current_mastery: Decimal | None = None
    current_confidence: Decimal | None = None
    attempt_count: int = 0
    independent_correct_count: int = 0

    # Phase assessments
    baseline: LearningAssessment | None = None
    post_instruction: LearningAssessment | None = None
    retention: LearningAssessment | None = None
    transfer: LearningAssessment | None = None

    # Computed metrics
    growth: EffectivenessMetrics | None = None
    retention_metrics: EffectivenessMetrics | None = None
    transfer_metrics: EffectivenessMetrics | None = None

    # Status flags
    has_baseline: bool = False
    has_post_instruction: bool = False
    has_retention: bool = False
    has_transfer: bool = False
    retention_scheduled: bool = False

    def to_dict(self) -> dict:
        """JSON-serialisable summary."""
        return {
            "skill_code": self.skill_code,
            "skill_name": self.skill_name,
            "current_mastery": float(self.current_mastery) if self.current_mastery else None,
            "current_confidence": float(self.current_confidence) if self.current_confidence else None,
            "attempt_count": self.attempt_count,
            "independent_correct_count": self.independent_correct_count,
            "has_baseline": self.has_baseline,
            "has_post_instruction": self.has_post_instruction,
            "has_retention": self.has_retention,
            "has_transfer": self.has_transfer,
            "retention_scheduled": self.retention_scheduled,
            "growth": _metrics_dict(self.growth),
            "retention": _metrics_dict(self.retention_metrics),
            "transfer": _metrics_dict(self.transfer_metrics),
        }


def _metrics_dict(m: EffectivenessMetrics | None) -> dict | None:
    if m is None:
        return None
    return {
        "observed_improvement": float(m.observed_improvement) if m.observed_improvement is not None else None,
        "independent_improvement": float(m.independent_improvement) if m.independent_improvement is not None else None,
        "transfer_performance": float(m.transfer_performance) if m.transfer_performance is not None else None,
        "difficulty_comparable": m.difficulty_comparable,
        "evidence_sufficient": m.evidence_sufficient,
        "confidence_level": m.confidence_level,
        "misconceptions_resolved": m.misconception_analysis.resolved,
        "misconceptions_persisting": m.misconception_analysis.persisting,
        "misconceptions_new": m.misconception_analysis.new,
    }


# ---------------------------------------------------------------------------
# Core measurement functions
# ---------------------------------------------------------------------------

def _analyse_misconceptions(
    baseline: LearningAssessment | None,
    comparison: LearningAssessment | None,
) -> MisconceptionAnalysis:
    """Compare misconceptions between two assessments."""
    base_misc = set(baseline.misconceptions_detected or []) if baseline else set()
    comp_misc = set(comparison.misconceptions_detected or []) if comparison else set()
    return MisconceptionAnalysis(
        baseline=sorted(base_misc),
        comparison=sorted(comp_misc),
        resolved=sorted(base_misc - comp_misc),
        persisting=sorted(base_misc & comp_misc),
        new=sorted(comp_misc - base_misc),
    )


def _compute_confidence(evidence_count: int) -> str:
    """Determine confidence level from evidence count."""
    if evidence_count >= CONFIDENCE_THRESHOLDS["HIGH"]:
        return "HIGH"
    if evidence_count >= CONFIDENCE_THRESHOLDS["MODERATE"]:
        return "MODERATE"
    if evidence_count >= CONFIDENCE_THRESHOLDS["LOW"]:
        return "LOW"
    return "INSUFFICIENT"


def _safe_decimal(value: Decimal | None) -> Decimal:
    """Return value or 0 if None.

    WARNING: only appropriate for display defaults and non-measurement
    contexts.  NEVER use for computing learning improvement — a missing
    score is not the same as a zero score.  Use ``_optional_decimal``
    for measurement calculations.
    """
    return value if value is not None else Decimal("0.000")


def _optional_decimal(value: Decimal | None) -> Decimal | None:
    """Convert to Decimal preserving None.

    None means evidence is missing, unavailable, or invalid.
    Decimal("0") means a valid assessment demonstrated zero performance.
    These two states must never be interchangeable.
    """
    if value is None:
        return None
    return Decimal(str(value))


def _subtract_optional(
    a: Decimal | None, b: Decimal | None,
) -> Decimal | None:
    """Subtract two optional Decimal values.

    Returns None when *either* operand is None — a missing score
    must not be treated as zero in a learning-improvement calculation.
    """
    if a is None or b is None:
        return None
    return (a - b).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def compute_effectiveness(
    *,
    baseline: LearningAssessment | None,
    comparison: LearningAssessment,
    measurement_type: str,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
) -> EffectivenessMetrics:
    """Compute effectiveness metrics by comparing two assessments.

    Parameters
    ----------
    baseline : completed baseline assessment (may be None for transfer)
    comparison : the post/retention/transfer assessment being measured
    measurement_type : "GROWTH", "RETENTION", or "TRANSFER"

    For GROWTH and RETENTION, baseline and comparison assess the *same* skill,
    so a score difference is a same-skill comparison.

    For TRANSFER, the comparison is on a *different* skill.  Cross-skill score
    differences are NOT reported as learning gains — only the absolute
    transfer performance is recorded.

    Missing-value semantics:
    - None means evidence is missing, unavailable, or invalid.
    - Decimal("0") means a valid assessment demonstrated zero performance.
    - If either score is None, the improvement is None (not zero).
    """
    comp_score = _optional_decimal(comparison.score)
    comp_ind = _optional_decimal(comparison.independent_score)

    transfer_perf: Decimal | None = None
    if measurement_type == "TRANSFER":
        # Transfer: report absolute performance on the target skill.
        # Do NOT subtract source-skill scores — different skills are
        # not directly comparable as improvement.
        observed = None
        independent = None
        transfer_perf = comp_score
        base_diff = None
        comp_diff = comparison.difficulty_mean
        comparable = comp_diff is not None  # target difficulty must be recorded
    else:
        # GROWTH / RETENTION: same-skill comparison.
        # Use nullable arithmetic — if either score is None, the
        # improvement is None (we cannot compute a delta from
        # missing evidence).
        base_score = _optional_decimal(
            baseline.score if baseline else None,
        )
        base_ind = _optional_decimal(
            baseline.independent_score if baseline else None,
        )
        observed = _subtract_optional(comp_score, base_score)
        independent = _subtract_optional(comp_ind, base_ind)
        base_diff = baseline.difficulty_mean if baseline else None
        comp_diff = comparison.difficulty_mean
        if base_diff is not None and comp_diff is not None:
            gap = abs(float(comp_diff) - float(base_diff))
            comparable = gap <= MAX_DIFFICULTY_GAP
        else:
            comparable = False  # unknown difficulty is not proven comparable

    # Count answered items, not just items displayed.  Legacy assessments
    # with no answered count retain their historical total as a fallback.
    base_items = (baseline.items_total or 0) if baseline else 0
    comp_items = comparison.items_total or 0
    base_answered = (
        baseline.items_answered if baseline and baseline.items_answered is not None
        else base_items
    )
    comp_answered = (
        comparison.items_answered if comparison.items_answered is not None
        else comp_items
    )
    # Transfer confidence is based solely on independent target-skill evidence.
    # Source-skill baseline questions cannot strengthen transfer confidence.
    total_evidence = (
        comp_answered if measurement_type == "TRANSFER"
        else base_answered + comp_answered
    )

    # Growth and retention require a valid same-skill baseline.  Transfer
    # measures absolute target performance and does not require one.
    requires_baseline = measurement_type != "TRANSFER"
    base_valid = (
        not requires_baseline
        or (
            baseline is not None
            and baseline.status == AssessmentStatus.COMPLETED
            and baseline.score is not None
            and baseline.independent_score is not None
            and baseline.assessment_mode != "COMPROMISED"
            and baseline.coverage_sufficient is not False
            and base_answered >= MIN_EVIDENCE_ITEMS
        )
    )
    comp_valid = (
        comparison.status == AssessmentStatus.COMPLETED
        and comparison.score is not None
        and comparison.independent_score is not None
        and comparison.assessment_mode != "COMPROMISED"
        and comparison.coverage_sufficient is not False
        and comp_answered >= MIN_EVIDENCE_ITEMS
    )
    sufficient = base_valid and comp_valid and comparable

    misconceptions = _analyse_misconceptions(baseline, comparison)
    # Volume alone never overrides compromised, incomplete, non-independent,
    # uncovered, or difficulty-incomparable evidence.
    confidence = _compute_confidence(total_evidence) if sufficient else "INSUFFICIENT"

    return EffectivenessMetrics(
        student_id=student_id,
        skill_id=skill_id,
        measurement_type=measurement_type,
        baseline_score=baseline.score if baseline else None,
        baseline_independent_score=baseline.independent_score if baseline else None,
        comparison_score=comparison.score,
        comparison_independent_score=comparison.independent_score,
        observed_improvement=observed,
        independent_improvement=independent,
        transfer_performance=transfer_perf,
        baseline_difficulty_mean=base_diff,
        comparison_difficulty_mean=comp_diff,
        difficulty_comparable=comparable,
        misconception_analysis=misconceptions,
        evidence_count=total_evidence,
        evidence_sufficient=sufficient,
        confidence_level=confidence,
        baseline_assessment_id=baseline.id if baseline else None,
        comparison_assessment_id=comparison.id,
    )


# ---------------------------------------------------------------------------
# Snapshot persistence
# ---------------------------------------------------------------------------

def save_snapshot(
    db: Session,
    metrics: EffectivenessMetrics,
    *,
    now: datetime | None = None,
) -> EffectivenessSnapshot:
    """Persist an effectiveness measurement as a snapshot row.

    Uses upsert semantics: if a snapshot already exists for the same
    (student_id, skill_id, measurement_type), it is updated.
    """
    now = now or datetime.now(UTC)

    existing = db.scalars(
        select(EffectivenessSnapshot).where(
            EffectivenessSnapshot.student_id == metrics.student_id,
            EffectivenessSnapshot.skill_id == metrics.skill_id,
            EffectivenessSnapshot.measurement_type == metrics.measurement_type,
        )
    ).first()

    if existing:
        snap = existing
    else:
        snap = EffectivenessSnapshot(
            student_id=metrics.student_id,
            skill_id=metrics.skill_id,
            measurement_type=metrics.measurement_type,
        )
        db.add(snap)

    snap.baseline_assessment_id = metrics.baseline_assessment_id
    snap.comparison_assessment_id = metrics.comparison_assessment_id
    snap.baseline_score = metrics.baseline_score
    snap.baseline_independent_score = metrics.baseline_independent_score
    snap.comparison_score = metrics.comparison_score
    snap.comparison_independent_score = metrics.comparison_independent_score
    snap.observed_improvement = metrics.observed_improvement
    snap.independent_improvement = metrics.independent_improvement
    snap.transfer_performance = metrics.transfer_performance
    snap.baseline_difficulty_mean = metrics.baseline_difficulty_mean
    snap.comparison_difficulty_mean = metrics.comparison_difficulty_mean
    snap.difficulty_comparable = metrics.difficulty_comparable
    snap.baseline_misconceptions = metrics.misconception_analysis.baseline
    snap.comparison_misconceptions = metrics.misconception_analysis.comparison
    snap.misconceptions_resolved = metrics.misconception_analysis.resolved
    snap.misconceptions_persisting = metrics.misconception_analysis.persisting
    snap.misconceptions_new = metrics.misconception_analysis.new
    snap.evidence_count = metrics.evidence_count
    snap.evidence_sufficient = metrics.evidence_sufficient
    snap.confidence_level = metrics.confidence_level
    snap.computed_at = now

    return snap


# ---------------------------------------------------------------------------
# Orchestration — measure growth after post-instruction
# ---------------------------------------------------------------------------

def measure_growth(
    db: Session,
    *,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    now: datetime | None = None,
) -> EffectivenessMetrics | None:
    """Compute and save growth metrics after post-instruction assessment.

    Returns None if either baseline or post-instruction assessment is missing.
    """
    baseline = db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.skill_id == skill_id,
            LearningAssessment.phase == AssessmentPhase.BASELINE,
            LearningAssessment.status == AssessmentStatus.COMPLETED,
        ).order_by(LearningAssessment.completed_at.desc())
    ).first()

    post = db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.skill_id == skill_id,
            LearningAssessment.phase == AssessmentPhase.POST_INSTRUCTION,
            LearningAssessment.status == AssessmentStatus.COMPLETED,
        ).order_by(LearningAssessment.completed_at.desc())
    ).first()

    if baseline is None or post is None:
        return None

    metrics = compute_effectiveness(
        baseline=baseline,
        comparison=post,
        measurement_type="GROWTH",
        student_id=student_id,
        skill_id=skill_id,
    )
    save_snapshot(db, metrics, now=now)
    return metrics


def measure_retention(
    db: Session,
    *,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    now: datetime | None = None,
) -> EffectivenessMetrics | None:
    """Compute and save retention metrics.

    Compares the retention assessment against the post-instruction baseline.
    If no post-instruction exists, compares against the original baseline.
    """
    # Use post-instruction as the "baseline" for retention if available;
    # otherwise fall back to the original baseline.
    post = db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.skill_id == skill_id,
            LearningAssessment.phase == AssessmentPhase.POST_INSTRUCTION,
            LearningAssessment.status == AssessmentStatus.COMPLETED,
        ).order_by(LearningAssessment.completed_at.desc())
    ).first()

    baseline = post or db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.skill_id == skill_id,
            LearningAssessment.phase == AssessmentPhase.BASELINE,
            LearningAssessment.status == AssessmentStatus.COMPLETED,
        ).order_by(LearningAssessment.completed_at.desc())
    ).first()

    retention = db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.skill_id == skill_id,
            LearningAssessment.phase == AssessmentPhase.RETENTION,
            LearningAssessment.status == AssessmentStatus.COMPLETED,
        ).order_by(LearningAssessment.completed_at.desc())
    ).first()

    if retention is None:
        return None

    metrics = compute_effectiveness(
        baseline=baseline,
        comparison=retention,
        measurement_type="RETENTION",
        student_id=student_id,
        skill_id=skill_id,
    )
    save_snapshot(db, metrics, now=now)
    return metrics


def measure_transfer(
    db: Session,
    *,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    now: datetime | None = None,
) -> EffectivenessMetrics | None:
    """Compute and save transfer metrics.

    Transfer assessments have no same-skill baseline; the measurement
    captures performance on a *related* skill.
    """
    transfer = db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.skill_id == skill_id,
            LearningAssessment.phase == AssessmentPhase.TRANSFER,
            LearningAssessment.status == AssessmentStatus.COMPLETED,
        ).order_by(LearningAssessment.completed_at.desc())
    ).first()

    if transfer is None:
        return None

    # For transfer, the "baseline" is the student's performance on the
    # *source* skill's post-instruction (what they learned).
    source_baseline = None
    if transfer.source_skill_id:
        source_baseline = db.scalars(
            select(LearningAssessment).where(
                LearningAssessment.student_id == student_id,
                LearningAssessment.skill_id == transfer.source_skill_id,
                LearningAssessment.phase.in_([
                    AssessmentPhase.POST_INSTRUCTION,
                    AssessmentPhase.BASELINE,
                ]),
                LearningAssessment.status == AssessmentStatus.COMPLETED,
            ).order_by(LearningAssessment.completed_at.desc())
        ).first()

    metrics = compute_effectiveness(
        baseline=source_baseline,
        comparison=transfer,
        measurement_type="TRANSFER",
        student_id=student_id,
        skill_id=skill_id,
    )
    save_snapshot(db, metrics, now=now)
    return metrics


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def skill_effectiveness_report(
    db: Session,
    *,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
) -> SkillEffectivenessReport:
    """Build a complete effectiveness report for a student-skill pair.

    Aggregates all assessment phases and computed metrics into a single
    report suitable for parent dashboard display.
    """
    from app.models import Skill

    skill = db.get(Skill, skill_id)
    if skill is None:
        raise ValueError(f"Skill {skill_id} not found")

    progress = db.get(StudentSkill, {
        "student_id": student_id, "skill_id": skill_id,
    })

    report = SkillEffectivenessReport(
        student_id=student_id,
        skill_id=skill_id,
        skill_code=skill.code,
        skill_name=skill.name,
    )

    if progress:
        report.current_mastery = progress.mastery_score
        report.current_confidence = progress.confidence_score
        report.attempt_count = progress.attempt_count
        report.independent_correct_count = progress.independent_correct_count

    # Load assessments by phase
    def _latest(phase: AssessmentPhase) -> LearningAssessment | None:
        return db.scalars(
            select(LearningAssessment).where(
                LearningAssessment.student_id == student_id,
                LearningAssessment.skill_id == skill_id,
                LearningAssessment.phase == phase,
            ).order_by(LearningAssessment.created_at.desc())
        ).first()

    report.baseline = _latest(AssessmentPhase.BASELINE)
    report.post_instruction = _latest(AssessmentPhase.POST_INSTRUCTION)
    report.retention = _latest(AssessmentPhase.RETENTION)
    report.transfer = _latest(AssessmentPhase.TRANSFER)

    report.has_baseline = (
        report.baseline is not None
        and report.baseline.status == AssessmentStatus.COMPLETED
    )
    report.has_post_instruction = (
        report.post_instruction is not None
        and report.post_instruction.status == AssessmentStatus.COMPLETED
    )
    report.has_retention = (
        report.retention is not None
        and report.retention.status == AssessmentStatus.COMPLETED
    )
    report.has_transfer = (
        report.transfer is not None
        and report.transfer.status == AssessmentStatus.COMPLETED
    )
    report.retention_scheduled = (
        report.retention is not None
        and report.retention.status == AssessmentStatus.SCHEDULED
    )

    # Load snapshots
    def _snapshot(measurement_type: str) -> EffectivenessSnapshot | None:
        return db.scalars(
            select(EffectivenessSnapshot).where(
                EffectivenessSnapshot.student_id == student_id,
                EffectivenessSnapshot.skill_id == skill_id,
                EffectivenessSnapshot.measurement_type == measurement_type,
            )
        ).first()

    growth_snap = _snapshot("GROWTH")
    retention_snap = _snapshot("RETENTION")
    transfer_snap = _snapshot("TRANSFER")

    if growth_snap:
        report.growth = _snapshot_to_metrics(growth_snap, student_id, skill_id)
    if retention_snap:
        report.retention_metrics = _snapshot_to_metrics(retention_snap, student_id, skill_id)
    if transfer_snap:
        report.transfer_metrics = _snapshot_to_metrics(transfer_snap, student_id, skill_id)

    return report


def _snapshot_to_metrics(
    snap: EffectivenessSnapshot,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
) -> EffectivenessMetrics:
    """Convert a persisted snapshot back to an EffectivenessMetrics."""
    return EffectivenessMetrics(
        student_id=student_id,
        skill_id=skill_id,
        measurement_type=snap.measurement_type,
        baseline_score=snap.baseline_score,
        baseline_independent_score=snap.baseline_independent_score,
        comparison_score=snap.comparison_score,
        comparison_independent_score=snap.comparison_independent_score,
        observed_improvement=snap.observed_improvement,
        independent_improvement=snap.independent_improvement,
        transfer_performance=snap.transfer_performance,
        baseline_difficulty_mean=snap.baseline_difficulty_mean,
        comparison_difficulty_mean=snap.comparison_difficulty_mean,
        difficulty_comparable=snap.difficulty_comparable,
        misconception_analysis=MisconceptionAnalysis(
            baseline=snap.baseline_misconceptions or [],
            comparison=snap.comparison_misconceptions or [],
            resolved=snap.misconceptions_resolved or [],
            persisting=snap.misconceptions_persisting or [],
            new=snap.misconceptions_new or [],
        ),
        evidence_count=snap.evidence_count,
        evidence_sufficient=snap.evidence_sufficient,
        confidence_level=snap.confidence_level,
        baseline_assessment_id=snap.baseline_assessment_id,
        comparison_assessment_id=snap.comparison_assessment_id,
    )


# ---------------------------------------------------------------------------
# Parent-friendly summaries
# ---------------------------------------------------------------------------

@dataclass
class ParentEffectivenessSummary:
    """Simplified effectiveness summary for parent dashboard display.

    Uses plain language and avoids jargon.  Does not claim causality.
    """
    skill_name: str
    understood_initially: str   # "Well", "Partially", "Not yet", "Not assessed"
    has_improved: str           # "Yes", "Somewhat", "Not yet", "Not assessed"
    can_solve_independently: str  # "Yes", "Sometimes", "Not yet", "Not assessed"
    remembers_after_days: str   # "Yes", "Partially", "Not yet", "Waiting", "Not assessed"
    applies_to_new_problems: str  # "Well", "Partially", "Not yet", "Not assessed"
    needs_attention: bool
    attention_reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "skill_name": self.skill_name,
            "understood_initially": self.understood_initially,
            "has_improved": self.has_improved,
            "can_solve_independently": self.can_solve_independently,
            "remembers_after_days": self.remembers_after_days,
            "applies_to_new_problems": self.applies_to_new_problems,
            "needs_attention": self.needs_attention,
            "attention_reason": self.attention_reason,
        }


def parent_summary(
    report: SkillEffectivenessReport,
) -> ParentEffectivenessSummary:
    """Generate a parent-friendly summary from an effectiveness report.

    This function avoids educational jargon and unsupported causal claims.
    """
    # What they understood initially
    if not report.has_baseline:
        initial = "Not assessed"
    elif (
        report.baseline
        and report.baseline.independent_score is not None
        and report.baseline.assessment_mode != "COMPROMISED"
        and report.baseline.coverage_sufficient is not False
    ):
        score = float(report.baseline.independent_score)
        if score >= 0.8:
            initial = "Well"
        elif score >= 0.4:
            initial = "Partially"
        else:
            initial = "Not yet"
    else:
        initial = "Not assessed"

    # Whether they've improved
    if report.growth and report.growth.evidence_sufficient:
        if report.growth.independent_improvement is None:
            # Evidence exists but independent score missing (compromised/insufficient)
            improved = "Not assessed"
        else:
            imp = float(report.growth.independent_improvement)
            if imp >= 0.2:
                improved = "Yes"
            elif imp > 0:
                improved = "Somewhat"
            else:
                improved = "Not yet"
    elif not report.has_post_instruction:
        improved = "Not assessed"
    else:
        improved = "Not enough evidence"

    # Can solve independently
    if report.has_post_instruction and report.post_instruction:
        if (
            report.post_instruction.independent_score is None
            or report.post_instruction.assessment_mode == "COMPROMISED"
            or report.post_instruction.coverage_sufficient is False
        ):
            independent = "Not assessed"
        else:
            ind = float(report.post_instruction.independent_score)
            if ind >= 0.8:
                independent = "Yes"
            elif ind >= 0.4:
                independent = "Sometimes"
            else:
                independent = "Not yet"
    else:
        # Guided/general mastery cannot establish independent performance.
        independent = "Not assessed"

    # Retention
    if report.has_retention and report.retention_metrics:
        if (
            not report.retention_metrics.evidence_sufficient
            or report.retention_metrics.independent_improvement is None
        ):
            remembers = "Not enough evidence"
        else:
            ret_imp = float(report.retention_metrics.observed_improvement)
            if ret_imp >= -0.1:
                remembers = "Yes"
            elif ret_imp >= -0.3:
                remembers = "Partially"
            else:
                remembers = "Not yet"
    elif report.retention_scheduled:
        remembers = "Waiting"
    else:
        remembers = "Not assessed"

    # Transfer — applying understanding to new problems
    if report.has_transfer and report.transfer_metrics:
        if (
            not report.transfer_metrics.evidence_sufficient
            or report.transfer_metrics.transfer_performance is None
        ):
            transfer_label = "Not enough evidence"
        else:
            tp = float(report.transfer_metrics.transfer_performance)
            if tp >= 0.7:
                transfer_label = "Well"
            elif tp >= 0.4:
                transfer_label = "Partially"
            else:
                transfer_label = "Not yet"
    else:
        transfer_label = "Not assessed"

    # Needs attention
    needs = False
    reason = None
    if report.has_post_instruction and improved == "Not yet":
        needs = True
        reason = "Practice hasn't led to improvement yet"
    elif report.has_retention and remembers == "Not yet":
        needs = True
        reason = "Previously learned material was not retained"
    elif report.growth and report.growth.misconception_analysis.persisting:
        needs = True
        reason = "Some misunderstandings persist after practice"

    return ParentEffectivenessSummary(
        skill_name=report.skill_name,
        understood_initially=initial,
        has_improved=improved,
        can_solve_independently=independent,
        remembers_after_days=remembers,
        applies_to_new_problems=transfer_label,
        needs_attention=needs,
        attention_reason=reason,
    )
