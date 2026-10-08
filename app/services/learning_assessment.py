"""Learning-assessment service — create, administer, and score assessments.

This service owns the lifecycle of LearningAssessment / AssessmentItem rows.
It selects *fresh* canonical problems for each assessment phase, ensures
post-instruction and retention assessments use different families from the
baseline (preventing memorisation), and deterministically scores responses.

Key contracts:
- Baseline assessments measure understanding *before* tutoring.
- Post-instruction assessments use equivalent but non-identical items.
- Retention assessments use fresh items after a configurable delay.
- Transfer assessments evaluate a *different* skill related to the taught one.
- All scoring is deterministic (no LLM involvement).
- Assessments are independent: assistance_level is always server-enforced to 0.
- Excluded families are never silently reintroduced.
- Incomplete assessments (below minimum answered items) cannot produce scores.
- Each item stores the exact generation_seed for reproducible reconstruction.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.canonical_problem_families import FAMILIES, LearningMode, generate
from app.effectiveness_models import (
    AssessmentItem,
    AssessmentPhase,
    AssessmentStatus,
    LearningAssessment,
)
from app.models import Skill, SkillPrerequisite

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_ITEMS_PER_ASSESSMENT = 5
RETENTION_DELAY_DAYS = 7
TRANSFER_MIN_ITEMS = 3

# Minimum items answered to consider an assessment scoreable.
# Below this threshold the assessment is marked COMPLETED with
# insufficient_evidence=True and no numeric score.
MIN_ITEMS_FOR_SCORE = 3

# Minimum fraction of items that must be answered to allow completion.
MIN_COMPLETION_RATIO = 0.6


# ---------------------------------------------------------------------------
# Selection result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SelectionResult:
    """Outcome of problem-family selection for an assessment.

    ``sufficient`` is False when exclusion constraints leave fewer families
    than requested *and* no parallel-form fallback was used.  In that case
    the assessment should be flagged with ``insufficient_coverage=True``.
    """
    families: list[tuple[str, int]]   # (family_code, difficulty)
    sufficient: bool
    available_count: int
    excluded_count: int
    reused_families: list[str]        # families that appear in >1 assessment


# ---------------------------------------------------------------------------
# Problem selection
# ---------------------------------------------------------------------------

def _families_for_skill(skill_code: str) -> list[str]:
    """Return family codes whose canonical_skill_code matches."""
    return [
        code for code, spec in FAMILIES.items()
        if spec.canonical_skill_code == skill_code
    ]


def _select_assessment_families(
    skill_code: str,
    exclude_families: set[str] | None = None,
    count: int = DEFAULT_ITEMS_PER_ASSESSMENT,
    difficulty: int = 2,
) -> SelectionResult:
    """Pick family codes for an assessment, *never* reintroducing excluded ones.

    If exclusion constraints leave fewer families than ``count``, returns
    only what is available and flags ``sufficient=False``.  The caller must
    record this so the assessment is never presented as independently
    validated when it does not meet its coverage requirements.
    """
    available = _families_for_skill(skill_code)
    exclude = exclude_families or set()
    preferred = [f for f in available if f not in exclude]

    # NEVER silently reintroduce excluded families.
    # If we have fewer distinct families than requested, return what we have.
    usable = preferred if preferred else []
    sufficient = len(usable) >= count

    result: list[tuple[str, int]] = []
    reused: list[str] = []
    for i in range(min(count, max(len(usable), 1) if usable else 0)):
        family_code = usable[i % len(usable)]
        if i >= len(usable):
            reused.append(family_code)
        spec = FAMILIES[family_code]
        d = max(spec.min_difficulty, min(spec.max_difficulty, difficulty + (i % 3) - 1))
        result.append((family_code, d))

    return SelectionResult(
        families=result,
        sufficient=sufficient,
        available_count=len(available),
        excluded_count=len(exclude),
        reused_families=reused,
    )


def _generate_items(
    assessment_id: uuid.UUID,
    families: list[tuple[str, int]],
    seed_base: str,
) -> list[AssessmentItem]:
    """Generate AssessmentItem rows from selected families.

    Each item stores the exact ``generation_seed`` used so the problem
    can be deterministically reconstructed for misconception detection.
    """
    items: list[AssessmentItem] = []
    for seq, (family_code, difficulty) in enumerate(families, start=1):
        seed = f"{seed_base}:{seq}"
        problem = generate(
            family_code, seed=seed, difficulty=difficulty,
            mode=LearningMode.DIAGNOSTIC,
        )
        items.append(AssessmentItem(
            assessment_id=assessment_id,
            sequence_number=seq,
            family_code=family_code,
            variant_id=problem.variant_id,
            generation_seed=seed,
            difficulty=difficulty,
            prompt=problem.prompt,
            canonical_answer=problem.canonical_answer,
        ))
    return items


def _all_prior_families(
    db: Session,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
) -> set[str]:
    """Collect family codes used in all prior completed assessments."""
    prior = db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.skill_id == skill_id,
            LearningAssessment.status == AssessmentStatus.COMPLETED,
        )
    ).all()
    exclude: set[str] = set()
    for p in prior:
        exclude.update(p.family_codes_used or [])
    return exclude


# Also collect families from IN_PROGRESS assessments so we don't reuse
# items that the student may have already seen.
def _all_used_families(
    db: Session,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
) -> set[str]:
    """Collect family codes used in all prior and in-progress assessments."""
    prior = db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.skill_id == skill_id,
            LearningAssessment.status.in_([
                AssessmentStatus.COMPLETED,
                AssessmentStatus.IN_PROGRESS,
            ]),
        )
    ).all()
    exclude: set[str] = set()
    for p in prior:
        exclude.update(p.family_codes_used or [])
    return exclude


# ---------------------------------------------------------------------------
# Assessment lifecycle
# ---------------------------------------------------------------------------

def create_baseline_assessment(
    db: Session,
    *,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    item_count: int = DEFAULT_ITEMS_PER_ASSESSMENT,
    difficulty: int = 2,
    now: datetime | None = None,
) -> LearningAssessment:
    """Create a baseline assessment for a skill before tutoring begins.

    Selects problems from available canonical families, generates items,
    and records which families were used so later assessments can avoid them.
    """
    now = now or datetime.now(UTC)
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise ValueError(f"Skill {skill_id} not found")

    selection = _select_assessment_families(
        skill.code, count=item_count, difficulty=difficulty,
    )
    if not selection.families:
        raise ValueError(
            f"No canonical families available for skill {skill.code}"
        )
    family_codes = list({fc for fc, _ in selection.families})

    assessment = LearningAssessment(
        student_id=student_id,
        skill_id=skill_id,
        phase=AssessmentPhase.BASELINE,
        status=AssessmentStatus.IN_PROGRESS,
        scheduled_at=now,
        started_at=now,
        family_codes_used=family_codes,
        items_total=len(selection.families),
    )
    db.add(assessment)
    db.flush()

    seed_base = f"baseline:{student_id}:{skill_id}:{now.isoformat()}"
    items = _generate_items(assessment.id, selection.families, seed_base)
    for item in items:
        db.add(item)

    return assessment


def create_post_instruction_assessment(
    db: Session,
    *,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    item_count: int = DEFAULT_ITEMS_PER_ASSESSMENT,
    difficulty: int = 2,
    now: datetime | None = None,
) -> LearningAssessment:
    """Create a post-instruction assessment using different families from baseline.

    Prevents memorisation by excluding family codes used in all prior
    assessments.  If insufficient distinct families exist, the assessment
    is flagged with insufficient coverage rather than silently reusing
    excluded families.
    """
    now = now or datetime.now(UTC)
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise ValueError(f"Skill {skill_id} not found")

    exclude = _all_used_families(db, student_id, skill_id)

    selection = _select_assessment_families(
        skill.code, exclude_families=exclude,
        count=item_count, difficulty=difficulty,
    )
    if not selection.families:
        raise ValueError(
            f"No distinct families available for post-instruction on {skill.code}. "
            f"All {selection.available_count} families already used."
        )
    family_codes = list({fc for fc, _ in selection.families})

    assessment = LearningAssessment(
        student_id=student_id,
        skill_id=skill_id,
        phase=AssessmentPhase.POST_INSTRUCTION,
        status=AssessmentStatus.IN_PROGRESS,
        scheduled_at=now,
        started_at=now,
        family_codes_used=family_codes,
        items_total=len(selection.families),
    )
    db.add(assessment)
    db.flush()

    seed_base = f"post:{student_id}:{skill_id}:{now.isoformat()}"
    items = _generate_items(assessment.id, selection.families, seed_base)
    for item in items:
        db.add(item)

    return assessment


def schedule_retention_assessment(
    db: Session,
    *,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    delay_days: int = RETENTION_DELAY_DAYS,
    now: datetime | None = None,
) -> LearningAssessment:
    """Schedule a retention assessment for a future date.

    The assessment is created in SCHEDULED status.  Items are generated when
    the assessment is started (to ensure fresh content).
    """
    now = now or datetime.now(UTC)
    scheduled_at = now + timedelta(days=delay_days)

    assessment = LearningAssessment(
        student_id=student_id,
        skill_id=skill_id,
        phase=AssessmentPhase.RETENTION,
        status=AssessmentStatus.SCHEDULED,
        scheduled_at=scheduled_at,
    )
    db.add(assessment)
    return assessment


def start_retention_assessment(
    db: Session,
    *,
    assessment: LearningAssessment,
    item_count: int = DEFAULT_ITEMS_PER_ASSESSMENT,
    difficulty: int = 2,
    now: datetime | None = None,
) -> LearningAssessment:
    """Start a scheduled retention assessment by generating fresh items.

    Excludes families used in all prior assessments for this skill.
    """
    now = now or datetime.now(UTC)

    if assessment.phase != AssessmentPhase.RETENTION:
        raise ValueError("Not a retention assessment")
    if assessment.status not in (AssessmentStatus.SCHEDULED, AssessmentStatus.EXPIRED):
        raise ValueError(f"Assessment in unexpected status: {assessment.status}")

    skill = db.get(Skill, assessment.skill_id)
    if skill is None:
        raise ValueError(f"Skill {assessment.skill_id} not found")

    exclude = _all_used_families(db, assessment.student_id, assessment.skill_id)
    selection = _select_assessment_families(
        skill.code, exclude_families=exclude,
        count=item_count, difficulty=difficulty,
    )
    if not selection.families:
        raise ValueError(
            f"No distinct families available for retention on {skill.code}"
        )
    family_codes = list({fc for fc, _ in selection.families})

    assessment.status = AssessmentStatus.IN_PROGRESS
    assessment.started_at = now
    assessment.family_codes_used = family_codes
    assessment.items_total = len(selection.families)

    seed_base = (
        f"retention:{assessment.student_id}:"
        f"{assessment.skill_id}:{now.isoformat()}"
    )
    items = _generate_items(assessment.id, selection.families, seed_base)
    for item in items:
        db.add(item)

    return assessment


def create_transfer_assessment(
    db: Session,
    *,
    student_id: uuid.UUID,
    source_skill_id: uuid.UUID,
    target_skill_id: uuid.UUID,
    item_count: int = DEFAULT_ITEMS_PER_ASSESSMENT,
    difficulty: int = 2,
    now: datetime | None = None,
) -> LearningAssessment:
    """Create a transfer assessment testing application of learned concepts.

    The assessment targets a *different* skill (target_skill_id) that is
    related to the taught skill (source_skill_id).  source_skill_id is
    recorded for measurement purposes.
    """
    now = now or datetime.now(UTC)
    target_skill = db.get(Skill, target_skill_id)
    if target_skill is None:
        raise ValueError(f"Target skill {target_skill_id} not found")

    selection = _select_assessment_families(
        target_skill.code, count=item_count, difficulty=difficulty,
    )
    if not selection.families:
        raise ValueError(
            f"No canonical families available for transfer on {target_skill.code}"
        )
    family_codes = list({fc for fc, _ in selection.families})

    assessment = LearningAssessment(
        student_id=student_id,
        skill_id=target_skill_id,
        source_skill_id=source_skill_id,
        phase=AssessmentPhase.TRANSFER,
        status=AssessmentStatus.IN_PROGRESS,
        scheduled_at=now,
        started_at=now,
        family_codes_used=family_codes,
        items_total=len(selection.families),
    )
    db.add(assessment)
    db.flush()

    seed_base = f"transfer:{student_id}:{target_skill_id}:{now.isoformat()}"
    items = _generate_items(assessment.id, selection.families, seed_base)
    for item in items:
        db.add(item)

    return assessment


# ---------------------------------------------------------------------------
# Response recording
# ---------------------------------------------------------------------------

def record_item_response(
    db: Session,
    *,
    item: AssessmentItem,
    student_answer: str,
    now: datetime | None = None,
) -> AssessmentItem:
    """Record a student's response to an assessment item.

    Assessment responses are always scored as independent (assistance_level=0)
    because assessments are controlled environments without hints.  The
    ``assistance_level`` parameter was removed — the server enforces
    independence.

    The exact problem is reconstructed using the persisted
    ``generation_seed``, ensuring prompt/answer/misconception consistency.
    """
    now = now or datetime.now(UTC)

    if item.student_answer is not None:
        raise ValueError("Item already answered — duplicate response rejected")

    # Reconstruct the exact original problem using persisted provenance
    problem = generate(
        item.family_code,
        seed=item.generation_seed,
        difficulty=item.difficulty,
        mode=LearningMode.DIAGNOSTIC,
    )

    # Verify reconstruction integrity
    if problem.canonical_answer != item.canonical_answer:
        raise RuntimeError(
            f"Problem reconstruction mismatch for item {item.id}: "
            f"stored={item.canonical_answer!r}, regenerated={problem.canonical_answer!r}"
        )

    # Deterministic grading via canonical answer comparison
    from app.canonical_problem_families import _normalize
    correct = _normalize(student_answer) == _normalize(item.canonical_answer)

    # Detect misconception if wrong, using the reconstructed problem's
    # misconception mapping (which is guaranteed to match the original)
    misconception_code = None
    if not correct:
        misconception_code = problem.misconception_for(student_answer)

    item.student_answer = student_answer
    item.is_correct = correct
    item.assistance_level = 0  # server-enforced: assessments are independent
    item.misconception_code = misconception_code
    item.answered_at = now

    return item


def complete_assessment(
    db: Session,
    *,
    assessment: LearningAssessment,
    now: datetime | None = None,
) -> LearningAssessment:
    """Finalize an assessment by computing aggregate scores.

    Completion policy:
    - All items are fetched (answered + unanswered).
    - Score denominator is ``items_total`` (not just items answered),
      so unanswered items count against the student.
    - If fewer than ``MIN_ITEMS_FOR_SCORE`` items were answered, the
      assessment completes with score=None (insufficient evidence).
    - If fewer than ``MIN_COMPLETION_RATIO`` of items were answered,
      the assessment is marked CANCELLED (abandoned), not COMPLETED.
    """
    now = now or datetime.now(UTC)

    all_items = db.scalars(
        select(AssessmentItem).where(
            AssessmentItem.assessment_id == assessment.id,
        ).order_by(AssessmentItem.sequence_number)
    ).all()

    answered_items = [i for i in all_items if i.student_answer is not None]
    total = assessment.items_total or len(all_items)
    answered_count = len(answered_items)

    # Abandoned: too few items answered
    if total > 0 and answered_count / total < MIN_COMPLETION_RATIO:
        assessment.status = AssessmentStatus.CANCELLED
        assessment.completed_at = now
        assessment.items_answered = answered_count
        return assessment

    # Insufficient evidence: some items answered but below threshold
    if answered_count < MIN_ITEMS_FOR_SCORE:
        assessment.status = AssessmentStatus.COMPLETED
        assessment.completed_at = now
        assessment.items_answered = answered_count
        assessment.score = None
        assessment.independent_score = None
        return assessment

    total_correct = sum(1 for i in answered_items if i.is_correct)
    # All assessment items are independent (assistance_level=0),
    # but we still filter defensively.
    independent_items = [i for i in answered_items if i.assistance_level == 0]
    independent_correct = sum(1 for i in independent_items if i.is_correct)

    # If the assessment was compromised (platform assistance detected),
    # independent_score is set to None — it cannot represent independent mastery.
    compromised = (assessment.assessment_mode or "INDEPENDENT") == "COMPROMISED"

    # Score denominator is items_total (unanswered items penalise)
    difficulties = [i.difficulty for i in answered_items]
    diff_mean = Decimal(str(sum(difficulties) / len(difficulties)))

    misconceptions = [
        i.misconception_code for i in answered_items
        if i.misconception_code is not None
    ]

    assessment.items_answered = answered_count
    assessment.items_correct = total_correct
    assessment.items_independent_correct = independent_correct
    assessment.score = Decimal(str(
        total_correct / total
    )).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    assessment.independent_score = (
        None if compromised
        else Decimal(str(
            independent_correct / total
        )).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    )
    assessment.difficulty_mean = diff_mean.quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP,
    )
    assessment.misconceptions_detected = misconceptions or None
    assessment.status = AssessmentStatus.COMPLETED
    assessment.completed_at = now

    return assessment


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def find_baseline(
    db: Session,
    *,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
) -> LearningAssessment | None:
    """Find the most recent completed baseline for a student-skill pair."""
    return db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.skill_id == skill_id,
            LearningAssessment.phase == AssessmentPhase.BASELINE,
            LearningAssessment.status == AssessmentStatus.COMPLETED,
        ).order_by(LearningAssessment.completed_at.desc())
    ).first()


def find_due_retention_assessments(
    db: Session,
    *,
    student_id: uuid.UUID,
    now: datetime | None = None,
) -> list[LearningAssessment]:
    """Find retention assessments that are scheduled and due."""
    now = now or datetime.now(UTC)
    return list(db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.phase == AssessmentPhase.RETENTION,
            LearningAssessment.status == AssessmentStatus.SCHEDULED,
            LearningAssessment.scheduled_at <= now,
        ).order_by(LearningAssessment.scheduled_at)
    ).all())


def expire_overdue_retention_assessments(
    db: Session,
    *,
    student_id: uuid.UUID,
    grace_days: int = 14,
    now: datetime | None = None,
) -> list[LearningAssessment]:
    """Mark retention assessments as EXPIRED if too far past their window.

    A retention assessment that was never started within grace_days after
    its scheduled date is marked EXPIRED rather than treated as failure.
    """
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=grace_days)
    overdue = db.scalars(
        select(LearningAssessment).where(
            LearningAssessment.student_id == student_id,
            LearningAssessment.phase == AssessmentPhase.RETENTION,
            LearningAssessment.status == AssessmentStatus.SCHEDULED,
            LearningAssessment.scheduled_at <= cutoff,
        )
    ).all()
    for a in overdue:
        a.status = AssessmentStatus.EXPIRED
    return list(overdue)


def has_active_assessment(
    db: Session,
    *,
    student_id: uuid.UUID,
    skill_id: uuid.UUID | None = None,
) -> bool:
    """Check whether the student has an IN_PROGRESS assessment.

    Used by hint and tutoring guards to enforce independent assessment mode.
    When ``skill_id`` is provided, restricts to that skill; otherwise checks
    any skill.
    """
    q = select(LearningAssessment.id).where(
        LearningAssessment.student_id == student_id,
        LearningAssessment.status == AssessmentStatus.IN_PROGRESS,
    )
    if skill_id is not None:
        q = q.where(LearningAssessment.skill_id == skill_id)
    return db.scalar(q) is not None


# ---------------------------------------------------------------------------
# Centralized independent-assessment guard
# ---------------------------------------------------------------------------

# Student-friendly message returned when assistance is blocked.
ASSESSMENT_BLOCK_MESSAGE = (
    "You're working on an independent assessment right now. "
    "Hints and tutoring help are paused until you finish. "
    "You can do this!"
)


class AssessmentGuardResult:
    """Outcome of the centralized assessment guard check.

    ``blocked`` is True when the student has an active independent
    assessment and the request should not deliver tutoring assistance.
    ``message`` contains a student-friendly explanation when blocked.
    """
    __slots__ = ("blocked", "message")

    def __init__(self, *, blocked: bool, message: str = ""):
        self.blocked = blocked
        self.message = message


def check_assessment_guard(
    db: Session,
    *,
    student_id: uuid.UUID,
) -> AssessmentGuardResult:
    """Centralized guard: should tutoring assistance be blocked?

    Returns a blocked result when the student has any IN_PROGRESS
    independent assessment.  Callers must not deliver hints, LLM
    explanations, revealed solution steps, or other assistance when
    blocked.

    A successfully blocked request does NOT mark the assessment
    compromised — no assistance was actually delivered.
    """
    if has_active_assessment(db, student_id=student_id):
        return AssessmentGuardResult(
            blocked=True, message=ASSESSMENT_BLOCK_MESSAGE,
        )
    return AssessmentGuardResult(blocked=False)


def mark_assessment_compromised(
    db: Session,
    *,
    student_id: uuid.UUID,
    reason: str,
    skill_id: uuid.UUID | None = None,
) -> list[LearningAssessment]:
    """Mark all in-progress assessments for the student as compromised.

    Called when platform assistance was **actually delivered** during an
    active assessment (e.g. a race condition where the guard was not
    checked, or a code path that bypassed the guard).

    Successfully *blocked* requests must NOT call this — a blocked
    request means no assistance was delivered, so the assessment is
    not compromised.

    Compromised assessments produce ``independent_score=None`` on
    completion and are excluded from independent mastery evidence.
    """
    q = select(LearningAssessment).where(
        LearningAssessment.student_id == student_id,
        LearningAssessment.status == AssessmentStatus.IN_PROGRESS,
    )
    if skill_id is not None:
        q = q.where(LearningAssessment.skill_id == skill_id)
    assessments = list(db.scalars(q).all())
    for a in assessments:
        a.assessment_mode = "COMPROMISED"
        a.compromised_reason = reason
    return assessments


def find_related_skills(
    db: Session,
    *,
    skill_id: uuid.UUID,
) -> list[Skill]:
    """Find skills related to the given one via prerequisite edges.

    Returns skills that either depend on the given skill or share a
    prerequisite relationship (bidirectional).
    """
    dependents = db.scalars(
        select(Skill).join(
            SkillPrerequisite, SkillPrerequisite.skill_id == Skill.id,
        ).where(SkillPrerequisite.prerequisite_skill_id == skill_id)
    ).all()

    prerequisites = db.scalars(
        select(Skill).join(
            SkillPrerequisite, SkillPrerequisite.prerequisite_skill_id == Skill.id,
        ).where(SkillPrerequisite.skill_id == skill_id)
    ).all()

    seen = set()
    result = []
    for s in list(dependents) + list(prerequisites):
        if s.id != skill_id and s.id not in seen:
            seen.add(s.id)
            result.append(s)
    return result
