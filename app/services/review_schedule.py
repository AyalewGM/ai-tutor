import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import (
    MasteryEvent,
    Skill,
    SkillReviewSchedule,
    SkillStatus,
    StudentSkill,
    TutorSession,
    TutorState,
)
from app.services.mastery import decayed_mastery
from app.services.state_machine import Transition

REVIEW_REASON = "SPACED_REVIEW"
REVIEW_INTERVALS_DAYS = (1, 3, 7, 14, 30)

SCHEDULED = "SCHEDULED"
DUE = "DUE"
RELEARNING = "RELEARNING"

REVIEW_PASSED = "REVIEW_PASSED"
REVIEW_FAILED = "REVIEW_FAILED"


@dataclass(frozen=True)
class DueReview:
    progress: StudentSkill
    schedule: SkillReviewSchedule
    decayed_score: float


@dataclass(frozen=True)
class ReviewVisibilityItem:
    progress: StudentSkill
    schedule: SkillReviewSchedule
    skill: Skill
    projected_mastery: float
    visibility_status: str  # DUE or RELEARNING


def _utcnow() -> datetime:
    return datetime.now(UTC)


def schedule_review(
    db: Session,
    *,
    progress: StudentSkill,
    now: datetime | None = None,
) -> SkillReviewSchedule:
    """Create or reset the spaced-review schedule for a freshly mastered skill."""
    now = now or _utcnow()
    schedule = db.get(
        SkillReviewSchedule,
        {"student_id": progress.student_id, "skill_id": progress.skill_id},
    )
    if schedule is None:
        schedule = SkillReviewSchedule(
            student_id=progress.student_id,
            skill_id=progress.skill_id,
        )
        db.add(schedule)
    schedule.interval_index = 0
    schedule.due_at = now + timedelta(days=REVIEW_INTERVALS_DAYS[0])
    schedule.status = SCHEDULED
    schedule.last_outcome = None
    db.add(
        MasteryEvent(
            student_id=progress.student_id,
            skill_id=progress.skill_id,
            previous_score=progress.mastery_score,
            new_score=progress.mastery_score,
            previous_confidence=progress.confidence_score,
            new_confidence=progress.confidence_score,
            reason="REVIEW_SCHEDULED",
            metadata_json={
                "due_at": schedule.due_at.isoformat(),
                "interval_index": schedule.interval_index,
            },
        )
    )
    return schedule


def due_review(
    db: Session,
    *,
    student_id: uuid.UUID,
    curriculum_id: uuid.UUID,
    now: datetime | None = None,
) -> DueReview | None:
    """Return the most overdue mastered skill, applying forgetting decay.

    Mastered skills whose scheduled review is due get their stored mastery
    decayed and are demoted to REVIEW_DUE so they surface before new work.
    """
    now = now or _utcnow()
    rows = db.execute(
        select(StudentSkill, SkillReviewSchedule)
        .join(
            SkillReviewSchedule,
            (SkillReviewSchedule.student_id == StudentSkill.student_id)
            & (SkillReviewSchedule.skill_id == StudentSkill.skill_id),
        )
        .join(Skill, Skill.id == StudentSkill.skill_id)
        .where(
            StudentSkill.student_id == student_id,
            StudentSkill.status == SkillStatus.MASTERED,
            Skill.curriculum_id == curriculum_id,
            SkillReviewSchedule.status == SCHEDULED,
            SkillReviewSchedule.due_at <= now,
        )
        .order_by(SkillReviewSchedule.due_at.asc())
    ).all()

    most_overdue: DueReview | None = None
    for progress, schedule in rows:
        anchor = (
            progress.last_independent_evidence_at
            or progress.last_attempt_at
            or schedule.created_at
        )
        if anchor.tzinfo is None:
            anchor = anchor.replace(tzinfo=UTC)
        days_since = max(0.0, (now - anchor).total_seconds() / 86400)
        decayed = decayed_mastery(
            float(progress.mastery_score),
            days_since_evidence=days_since,
            confidence=float(progress.confidence_score),
        )
        if decayed < float(progress.mastery_score):
            db.add(
                MasteryEvent(
                    student_id=progress.student_id,
                    skill_id=progress.skill_id,
                    previous_score=progress.mastery_score,
                    new_score=Decimal(str(decayed)),
                    previous_confidence=progress.confidence_score,
                    new_confidence=progress.confidence_score,
                    reason="MASTERY_DECAY",
                    metadata_json={
                        "days_since_evidence": round(days_since, 2),
                        "due_at": schedule.due_at.isoformat(),
                    },
                )
            )
            progress.mastery_score = Decimal(str(decayed))
        progress.status = SkillStatus.REVIEW_DUE
        schedule.status = DUE
        if most_overdue is None:
            most_overdue = DueReview(progress=progress, schedule=schedule, decayed_score=decayed)
    return most_overdue


def reviews_due(
    db: Session,
    *,
    student_id: uuid.UUID,
    curriculum_id: uuid.UUID,
    now: datetime | None = None,
) -> list[ReviewVisibilityItem]:
    """Read-only projection of skills needing review for parent/learner surfaces.

    Unlike due_review(), this never mutates progress or schedules — decayed
    mastery is reported as a projection only.
    """
    now = now or _utcnow()
    rows = db.execute(
        select(StudentSkill, SkillReviewSchedule, Skill)
        .join(
            SkillReviewSchedule,
            (SkillReviewSchedule.student_id == StudentSkill.student_id)
            & (SkillReviewSchedule.skill_id == StudentSkill.skill_id),
        )
        .join(Skill, Skill.id == StudentSkill.skill_id)
        .where(
            StudentSkill.student_id == student_id,
            Skill.curriculum_id == curriculum_id,
            or_(
                SkillReviewSchedule.status == RELEARNING,
                SkillReviewSchedule.due_at <= now,
            ),
        )
        .order_by(SkillReviewSchedule.due_at.asc())
    ).all()

    items: list[ReviewVisibilityItem] = []
    for progress, schedule, skill in rows:
        anchor = (
            progress.last_independent_evidence_at
            or progress.last_attempt_at
            or schedule.created_at
        )
        if anchor.tzinfo is None:
            anchor = anchor.replace(tzinfo=UTC)
        days_since = max(0.0, (now - anchor).total_seconds() / 86400)
        projected = decayed_mastery(
            float(progress.mastery_score),
            days_since_evidence=days_since,
            confidence=float(progress.confidence_score),
        )
        items.append(
            ReviewVisibilityItem(
                progress=progress,
                schedule=schedule,
                skill=skill,
                projected_mastery=projected,
                visibility_status=(
                    RELEARNING if schedule.status == RELEARNING else DUE
                ),
            )
        )
    return items


def record_review_outcome(
    db: Session,
    *,
    progress: StudentSkill,
    schedule: SkillReviewSchedule,
    correct: bool,
    assistance_level: int,
    now: datetime | None = None,
) -> str:
    """Advance the schedule on independent success; demote mastery on failure."""
    now = now or _utcnow()
    passed = correct and assistance_level == 0
    schedule.last_reviewed_at = now

    if passed:
        schedule.interval_index = min(
            schedule.interval_index + 1, len(REVIEW_INTERVALS_DAYS) - 1
        )
        schedule.due_at = now + timedelta(
            days=REVIEW_INTERVALS_DAYS[schedule.interval_index]
        )
        schedule.status = SCHEDULED
        schedule.last_outcome = REVIEW_PASSED
        progress.status = SkillStatus.MASTERED
        progress.last_independent_evidence_at = now
    else:
        schedule.status = RELEARNING
        schedule.last_outcome = REVIEW_FAILED
        progress.status = SkillStatus.PRACTICING

    db.add(
        MasteryEvent(
            student_id=progress.student_id,
            skill_id=progress.skill_id,
            previous_score=progress.mastery_score,
            new_score=progress.mastery_score,
            previous_confidence=progress.confidence_score,
            new_confidence=progress.confidence_score,
            reason="REVIEW_OUTCOME",
            metadata_json={
                "passed": passed,
                "correct": correct,
                "assistance_level": assistance_level,
                "interval_index": schedule.interval_index,
                "next_due_at": (
                    schedule.due_at.isoformat() if schedule.status == SCHEDULED else None
                ),
            },
        )
    )
    return REVIEW_PASSED if passed else REVIEW_FAILED


def apply_review_policy(
    db: Session,
    *,
    session: TutorSession,
    progress: StudentSkill,
    transition: Transition,
    correct: bool,
    assistance_level: int,
    now: datetime | None = None,
) -> tuple[Transition, str | None]:
    """Decide the transition for a spaced-review attempt.

    Returns the transition and the review outcome (None when the attempt was
    not decisive for the review, e.g. continued relearning after a failure).
    """
    outcome = None
    if progress.status == SkillStatus.REVIEW_DUE:
        schedule = db.get(
            SkillReviewSchedule,
            {"student_id": progress.student_id, "skill_id": progress.skill_id},
        )
        if schedule is not None:
            outcome = record_review_outcome(
                db,
                progress=progress,
                schedule=schedule,
                correct=correct,
                assistance_level=assistance_level,
                now=now,
            )

    if outcome == REVIEW_PASSED:
        if session.active_skill_id and session.active_skill_id != session.primary_skill_id:
            session.active_skill_id = session.primary_skill_id
            session.remediation_reason = None
            return Transition(TutorState.GUIDED_PRACTICE, "RESUME_TARGET"), outcome
        return Transition(TutorState.COMPLETE, "MARK_MASTERED"), outcome
    if outcome == REVIEW_FAILED:
        return Transition(TutorState.REMEDIATION, "REMEDIATE", hint_level=2), outcome
    return transition, outcome
