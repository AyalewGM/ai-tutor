"""Learning-effectiveness API endpoints.

Provides endpoints to create and manage learning assessments, record
responses, and retrieve effectiveness reports.  All endpoints are
parent-authenticated — a parent (or learner via pass) must own the student.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db

DbSession = Annotated[Session, Depends(get_db)]
from app.effectiveness_models import (
    AssessmentItem,
    AssessmentPhase,
    AssessmentStatus,
    LearningAssessment,
)
from app.identity import (
    CurrentLearningAccess,
    require_learning_owns_student,
)
from app.models import Student
from app.services.learning_assessment import (
    complete_assessment,
    create_baseline_assessment,
    create_post_instruction_assessment,
    create_transfer_assessment,
    expire_overdue_retention_assessments,
    find_due_retention_assessments,
    find_related_skills,
    record_item_response,
    schedule_retention_assessment,
    start_retention_assessment,
)
from app.services.learning_effectiveness import (
    measure_growth,
    measure_retention,
    measure_transfer,
    parent_summary,
    skill_effectiveness_report,
)

router = APIRouter(
    prefix="/effectiveness", tags=["learning-effectiveness"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CreateAssessmentRequest(BaseModel):
    student_id: uuid.UUID
    skill_id: uuid.UUID
    item_count: int = Field(default=5, ge=2, le=10)
    difficulty: int = Field(default=2, ge=1, le=5)


class TransferAssessmentRequest(BaseModel):
    student_id: uuid.UUID
    source_skill_id: uuid.UUID
    target_skill_id: uuid.UUID
    item_count: int = Field(default=5, ge=2, le=10)
    difficulty: int = Field(default=2, ge=1, le=5)


class ScheduleRetentionRequest(BaseModel):
    student_id: uuid.UUID
    skill_id: uuid.UUID
    delay_days: int = Field(default=7, ge=1, le=30)


class RecordResponseRequest(BaseModel):
    student_answer: str
    # assistance_level is NOT accepted from the client.
    # Assessments are controlled independent-only environments;
    # the server enforces assistance_level=0.


class AssessmentItemOut(BaseModel):
    id: uuid.UUID
    sequence_number: int
    family_code: str
    difficulty: int
    prompt: str
    student_answer: str | None = None
    is_correct: bool | None = None
    assistance_level: int = 0
    misconception_code: str | None = None

    model_config = {"from_attributes": True}


class AssessmentOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    skill_id: uuid.UUID
    phase: str
    status: str
    source_skill_id: uuid.UUID | None = None
    scheduled_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    items_total: int = 0
    items_answered: int = 0
    items_correct: int = 0
    items_independent_correct: int = 0
    score: float | None = None
    independent_score: float | None = None
    difficulty_mean: float | None = None
    misconceptions_detected: list[str] | None = None
    items: list[AssessmentItemOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class EffectivenessMetricsOut(BaseModel):
    measurement_type: str
    baseline_score: float | None = None
    baseline_independent_score: float | None = None
    comparison_score: float | None = None
    comparison_independent_score: float | None = None
    observed_improvement: float | None = None
    independent_improvement: float | None = None
    difficulty_comparable: bool = True
    evidence_sufficient: bool = False
    confidence_level: str = "INSUFFICIENT"
    misconceptions_resolved: list[str] = Field(default_factory=list)
    misconceptions_persisting: list[str] = Field(default_factory=list)
    misconceptions_new: list[str] = Field(default_factory=list)


class SkillReportOut(BaseModel):
    skill_code: str
    skill_name: str
    current_mastery: float | None = None
    current_confidence: float | None = None
    attempt_count: int = 0
    independent_correct_count: int = 0
    has_baseline: bool = False
    has_post_instruction: bool = False
    has_retention: bool = False
    has_transfer: bool = False
    retention_scheduled: bool = False
    growth: EffectivenessMetricsOut | None = None
    retention: EffectivenessMetricsOut | None = None
    transfer: EffectivenessMetricsOut | None = None


class ParentSummaryOut(BaseModel):
    skill_name: str
    understood_initially: str
    has_improved: str
    can_solve_independently: str
    remembers_after_days: str
    needs_attention: bool
    attention_reason: str | None = None


class RelatedSkillOut(BaseModel):
    skill_id: uuid.UUID
    skill_code: str
    skill_name: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_student(
    db: Session, access: CurrentLearningAccess, student_id: uuid.UUID,
) -> Student:
    student = db.get(Student, student_id)
    return require_learning_owns_student(access, student)


def _assessment_out(
    db: Session, assessment: LearningAssessment,
) -> AssessmentOut:
    from sqlalchemy import select as sa_select

    item_rows = db.scalars(
        sa_select(AssessmentItem).where(
            AssessmentItem.assessment_id == assessment.id,
        ).order_by(AssessmentItem.sequence_number)
    ).all()

    return AssessmentOut(
        id=assessment.id,
        student_id=assessment.student_id,
        skill_id=assessment.skill_id,
        phase=assessment.phase.value if isinstance(assessment.phase, AssessmentPhase) else assessment.phase,
        status=assessment.status.value if isinstance(assessment.status, AssessmentStatus) else assessment.status,
        source_skill_id=assessment.source_skill_id,
        scheduled_at=assessment.scheduled_at,
        started_at=assessment.started_at,
        completed_at=assessment.completed_at,
        items_total=assessment.items_total or 0,
        items_answered=assessment.items_answered or 0,
        items_correct=assessment.items_correct or 0,
        items_independent_correct=assessment.items_independent_correct or 0,
        score=float(assessment.score) if assessment.score is not None else None,
        independent_score=float(assessment.independent_score) if assessment.independent_score is not None else None,
        difficulty_mean=float(assessment.difficulty_mean) if assessment.difficulty_mean is not None else None,
        misconceptions_detected=assessment.misconceptions_detected,
        items=[
            AssessmentItemOut(
                id=item.id,
                sequence_number=item.sequence_number,
                family_code=item.family_code,
                difficulty=item.difficulty,
                prompt=item.prompt,
                student_answer=item.student_answer,
                is_correct=item.is_correct,
                assistance_level=item.assistance_level,
                misconception_code=item.misconception_code,
            )
            for item in item_rows
        ],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/assessments/baseline", response_model=AssessmentOut)
def create_baseline(
    body: CreateAssessmentRequest,
    access: CurrentLearningAccess,
    db: DbSession,
) -> AssessmentOut:
    """Create a baseline assessment before tutoring begins."""
    _load_student(db, access, body.student_id)
    assessment = create_baseline_assessment(
        db,
        student_id=body.student_id,
        skill_id=body.skill_id,
        item_count=body.item_count,
        difficulty=body.difficulty,
    )
    db.commit()
    return _assessment_out(db, assessment)


@router.post("/assessments/post-instruction", response_model=AssessmentOut)
def create_post_instruction(
    body: CreateAssessmentRequest,
    access: CurrentLearningAccess,
    db: DbSession,
) -> AssessmentOut:
    """Create a post-instruction assessment with fresh questions."""
    _load_student(db, access, body.student_id)
    assessment = create_post_instruction_assessment(
        db,
        student_id=body.student_id,
        skill_id=body.skill_id,
        item_count=body.item_count,
        difficulty=body.difficulty,
    )
    db.commit()
    return _assessment_out(db, assessment)


@router.post("/assessments/retention", response_model=AssessmentOut)
def schedule_retention(
    body: ScheduleRetentionRequest,
    access: CurrentLearningAccess,
    db: DbSession,
) -> AssessmentOut:
    """Schedule a retention assessment for a future date."""
    _load_student(db, access, body.student_id)
    assessment = schedule_retention_assessment(
        db,
        student_id=body.student_id,
        skill_id=body.skill_id,
        delay_days=body.delay_days,
    )
    db.commit()
    return _assessment_out(db, assessment)


@router.post("/assessments/transfer", response_model=AssessmentOut)
def create_transfer(
    body: TransferAssessmentRequest,
    access: CurrentLearningAccess,
    db: DbSession,
) -> AssessmentOut:
    """Create a transfer assessment on a related skill."""
    _load_student(db, access, body.student_id)
    assessment = create_transfer_assessment(
        db,
        student_id=body.student_id,
        source_skill_id=body.source_skill_id,
        target_skill_id=body.target_skill_id,
        item_count=body.item_count,
        difficulty=body.difficulty,
    )
    db.commit()
    return _assessment_out(db, assessment)


@router.post(
    "/assessments/{assessment_id}/start-retention",
    response_model=AssessmentOut,
)
def start_scheduled_retention(
    assessment_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
) -> AssessmentOut:
    """Start a scheduled retention assessment by generating fresh items."""
    assessment = db.get(LearningAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    _load_student(db, access, assessment.student_id)
    assessment = start_retention_assessment(db, assessment=assessment)
    db.commit()
    return _assessment_out(db, assessment)


@router.post(
    "/assessments/{assessment_id}/items/{item_id}/respond",
    response_model=AssessmentItemOut,
)
def respond_to_item(
    assessment_id: uuid.UUID,
    item_id: uuid.UUID,
    body: RecordResponseRequest,
    access: CurrentLearningAccess,
    db: DbSession,
) -> AssessmentItemOut:
    """Record a student's response to an assessment item."""
    assessment = db.get(LearningAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    _load_student(db, access, assessment.student_id)

    if assessment.status != AssessmentStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail=f"Assessment is {assessment.status.value}, not in progress",
        )

    item = db.get(AssessmentItem, item_id)
    if item is None or item.assessment_id != assessment.id:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.student_answer is not None:
        raise HTTPException(status_code=409, detail="Item already answered")

    item = record_item_response(
        db,
        item=item,
        student_answer=body.student_answer,
    )
    db.commit()
    return AssessmentItemOut(
        id=item.id,
        sequence_number=item.sequence_number,
        family_code=item.family_code,
        difficulty=item.difficulty,
        prompt=item.prompt,
        student_answer=item.student_answer,
        is_correct=item.is_correct,
        assistance_level=item.assistance_level,
        misconception_code=item.misconception_code,
    )


@router.post(
    "/assessments/{assessment_id}/complete",
    response_model=AssessmentOut,
)
def complete(
    assessment_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
) -> AssessmentOut:
    """Complete an assessment and compute aggregate scores."""
    assessment = db.get(LearningAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    _load_student(db, access, assessment.student_id)

    if assessment.status != AssessmentStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=409,
            detail=f"Assessment is {assessment.status.value}, not in progress",
        )

    assessment = complete_assessment(db, assessment=assessment)

    # Auto-compute effectiveness metrics for completed assessments
    if assessment.phase == AssessmentPhase.POST_INSTRUCTION:
        measure_growth(
            db,
            student_id=assessment.student_id,
            skill_id=assessment.skill_id,
        )
    elif assessment.phase == AssessmentPhase.RETENTION:
        measure_retention(
            db,
            student_id=assessment.student_id,
            skill_id=assessment.skill_id,
        )
    elif assessment.phase == AssessmentPhase.TRANSFER:
        measure_transfer(
            db,
            student_id=assessment.student_id,
            skill_id=assessment.skill_id,
        )

    db.commit()
    return _assessment_out(db, assessment)


@router.get(
    "/assessments/{assessment_id}",
    response_model=AssessmentOut,
)
def get_assessment(
    assessment_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
) -> AssessmentOut:
    """Retrieve an assessment with its items."""
    assessment = db.get(LearningAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    _load_student(db, access, assessment.student_id)
    return _assessment_out(db, assessment)


@router.get(
    "/students/{student_id}/skills/{skill_id}/report",
    response_model=SkillReportOut,
)
def get_skill_report(
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
) -> SkillReportOut:
    """Get the full effectiveness report for a student-skill pair."""
    _load_student(db, access, student_id)
    report = skill_effectiveness_report(db, student_id=student_id, skill_id=skill_id)
    return SkillReportOut(**report.to_dict())


@router.get(
    "/students/{student_id}/skills/{skill_id}/parent-summary",
    response_model=ParentSummaryOut,
)
def get_parent_summary(
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
) -> ParentSummaryOut:
    """Get a parent-friendly effectiveness summary.

    Avoids educational jargon.  Explains what the child understood initially,
    what has improved, what they can solve independently, and whether they
    remember after several days.
    """
    _load_student(db, access, student_id)
    report = skill_effectiveness_report(db, student_id=student_id, skill_id=skill_id)
    summary = parent_summary(report)
    return ParentSummaryOut(**summary.to_dict())


@router.get(
    "/students/{student_id}/skills/{skill_id}/related",
    response_model=list[RelatedSkillOut],
)
def get_related_skills(
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
) -> list[RelatedSkillOut]:
    """Get skills related to the given one for transfer assessment."""
    _load_student(db, access, student_id)
    related = find_related_skills(db, skill_id=skill_id)
    return [
        RelatedSkillOut(
            skill_id=s.id, skill_code=s.code, skill_name=s.name,
        )
        for s in related
    ]


@router.get(
    "/students/{student_id}/retention-due",
    response_model=list[AssessmentOut],
)
def get_retention_due(
    student_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
) -> list[AssessmentOut]:
    """Get retention assessments that are scheduled and due."""
    _load_student(db, access, student_id)
    # Expire any that are too old
    expire_overdue_retention_assessments(db, student_id=student_id)
    due = find_due_retention_assessments(db, student_id=student_id)
    db.commit()
    return [_assessment_out(db, a) for a in due]
