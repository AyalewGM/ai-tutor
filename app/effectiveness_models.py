"""Learning-effectiveness measurement models.

These tables record assessment evidence at specific points in the learning
lifecycle — baseline, post-instruction, retention, and transfer — so that
Mihur can deterministically measure whether a child's mathematical
understanding actually improved, persisted, and transferred.

Privacy: assessment rows reference student_id and skill_id only.  No free-text
child data is stored beyond what the existing Attempt model already holds.
"""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# ---------------------------------------------------------------------------
# Assessment phase enum
# ---------------------------------------------------------------------------

class AssessmentPhase(str, enum.Enum):
    """Which point in the learning lifecycle this assessment covers."""
    BASELINE = "BASELINE"
    POST_INSTRUCTION = "POST_INSTRUCTION"
    RETENTION = "RETENTION"
    TRANSFER = "TRANSFER"


class AssessmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"      # retention window lapsed without response
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# Learning Assessment — a coherent assessment event
# ---------------------------------------------------------------------------

class LearningAssessment(Base):
    """A single assessment event within the learning-effectiveness lifecycle.

    Each assessment targets one canonical skill, uses a specific phase, and
    records independent (unassisted) student responses to deterministically
    generated problems.  Multiple items per assessment are stored as
    AssessmentItem rows.

    The ``family_codes_used`` JSONB array ensures post-instruction and
    retention assessments select *different* problem families from baseline,
    preventing memorisation effects.
    """
    __tablename__ = "learning_assessments"
    __table_args__ = (
        Index("ix_learning_assessments_student_skill",
              "student_id", "skill_id"),
        Index("ix_learning_assessments_phase",
              "student_id", "phase"),
        Index("ix_learning_assessments_scheduled",
              "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False, index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id"), nullable=False, index=True,
    )
    phase: Mapped[AssessmentPhase] = mapped_column(
        Enum(AssessmentPhase), nullable=False,
    )
    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus), default=AssessmentStatus.SCHEDULED,
    )

    # For TRANSFER assessments, the *source* skill that was taught.
    source_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("skills.id"),
    )

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    # Problem selection provenance — which family codes were used, to
    # prevent reuse in later phases.
    family_codes_used: Mapped[list | None] = mapped_column(JSONB)

    # Server-enforced independent assessment mode.
    # Records that this assessment was administered without Mihur hints,
    # tutoring, or answer exposure within the platform's control.
    assessment_mode: Mapped[str] = mapped_column(
        String(30), default="INDEPENDENT",
    )  # "INDEPENDENT" — no platform assistance available during assessment
    # Set to "COMPROMISED" if platform assistance was detected
    compromised_reason: Mapped[str | None] = mapped_column(String(200))

    # Problem-family coverage — whether the assessment met its required
    # distinct-family count.  An assessment with insufficient coverage
    # cannot qualify as validated learning-effectiveness evidence.
    coverage_sufficient: Mapped[bool] = mapped_column(Boolean, default=True)
    requested_item_count: Mapped[int] = mapped_column(Integer, default=0)
    available_distinct_families: Mapped[int] = mapped_column(Integer, default=0)

    # Aggregate results (filled on completion)
    items_total: Mapped[int] = mapped_column(Integer, default=0)
    items_answered: Mapped[int] = mapped_column(Integer, default=0)
    items_correct: Mapped[int] = mapped_column(Integer, default=0)
    items_independent_correct: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    independent_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    difficulty_mean: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))

    # Misconceptions detected
    misconceptions_detected: Mapped[list | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Assessment Item — one question within an assessment
# ---------------------------------------------------------------------------

class AssessmentItem(Base):
    """A single question-response pair within a LearningAssessment.

    Every item records the family code, difficulty, student answer, and
    whether the answer was correct — all deterministically evaluated.
    """
    __tablename__ = "assessment_items"
    __table_args__ = (
        Index("ix_assessment_items_assessment", "assessment_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_assessments.id"), nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Problem provenance — sufficient to deterministically reconstruct
    # the exact generated problem (family_code + generation_seed + difficulty).
    family_code: Mapped[str] = mapped_column(String(100), nullable=False)
    variant_id: Mapped[str] = mapped_column(String(40), nullable=False)
    generation_seed: Mapped[str] = mapped_column(String(200), nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_answer: Mapped[str] = mapped_column(Text, nullable=False)

    # Student response
    student_answer: Mapped[str | None] = mapped_column(Text)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    assistance_level: Mapped[int] = mapped_column(Integer, default=0)
    misconception_code: Mapped[str | None] = mapped_column(String(100))

    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Effectiveness Snapshot — computed measurement at a point in time
# ---------------------------------------------------------------------------

class EffectivenessSnapshot(Base):
    """Deterministic per-skill effectiveness measurement.

    A snapshot is computed whenever a post-instruction, retention, or transfer
    assessment completes.  It compares the new assessment against the baseline
    to produce interpretable metrics.

    This is *not* a causal claim that tutoring caused improvement.  It is an
    observed measurement from deterministic assessment data.
    """
    __tablename__ = "effectiveness_snapshots"
    __table_args__ = (
        Index("ix_effectiveness_snapshots_student_skill",
              "student_id", "skill_id"),
        UniqueConstraint(
            "student_id", "skill_id", "measurement_type",
            name="uq_effectiveness_snapshot_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id"), nullable=False, index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id"), nullable=False, index=True,
    )
    measurement_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
    )  # "GROWTH", "RETENTION", "TRANSFER"

    # References to the assessments used
    baseline_assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("learning_assessments.id"),
    )
    comparison_assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("learning_assessments.id"),
    )

    # Scores
    baseline_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    baseline_independent_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    comparison_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    comparison_independent_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))

    # Computed metrics — GROWTH/RETENTION only
    observed_improvement: Mapped[Decimal | None] = mapped_column(Numeric(5, 3))
    independent_improvement: Mapped[Decimal | None] = mapped_column(Numeric(5, 3))
    # TRANSFER only — absolute performance on target skill
    transfer_performance: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))

    # Difficulty comparability
    baseline_difficulty_mean: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    comparison_difficulty_mean: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    difficulty_comparable: Mapped[bool] = mapped_column(Boolean, default=True)

    # Misconception resolution
    baseline_misconceptions: Mapped[list | None] = mapped_column(JSONB)
    comparison_misconceptions: Mapped[list | None] = mapped_column(JSONB)
    misconceptions_resolved: Mapped[list | None] = mapped_column(JSONB)
    misconceptions_persisting: Mapped[list | None] = mapped_column(JSONB)
    misconceptions_new: Mapped[list | None] = mapped_column(JSONB)

    # Evidence confidence
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    evidence_sufficient: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_level: Mapped[str] = mapped_column(
        String(20), default="INSUFFICIENT",
    )  # "INSUFFICIENT", "LOW", "MODERATE", "HIGH"

    # Metadata
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
