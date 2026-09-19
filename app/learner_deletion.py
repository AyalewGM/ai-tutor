import uuid
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.curriculum_models import StudentCurriculumEnrollment
from app.diagnostic_models import DiagnosticAttempt, DiagnosticSession
from app.hint_models import HintEvent
from app.models import (
    Attempt,
    InterventionRecord,
    MasteryEvent,
    Student,
    StudentMisconception,
    StudentSkill,
    TutorSession,
    TutorTurn,
)
from app.parent_models import (
    ChildLinkClaim,
    ParentProfile,
    ParentStudentRelationship,
    ParentStudentRelationshipEvent,
)
from app.telemetry_models import TelemetryEventRecord

DELETION_POLICY_VERSION = "pilot-learner-deletion-v1"


@dataclass(frozen=True)
class LearnerDeletionResult:
    learner_id: uuid.UUID
    policy_version: str = DELETION_POLICY_VERSION


def _authorized_relationship(
    db: Session, *, parent: ParentProfile, learner_id: uuid.UUID
) -> ParentStudentRelationship:
    relationship = db.scalar(
        select(ParentStudentRelationship).where(
            ParentStudentRelationship.parent_profile_id == parent.id,
            ParentStudentRelationship.student_id == learner_id,
            ParentStudentRelationship.active.is_(True),
        )
    )
    learner = db.get(Student, learner_id)
    # Preserve the pilot's legacy parent_id ownership check while relationship
    # records are the family authorization source. Fail closed/non-enumerating.
    if relationship is None or learner is None or learner.parent_id != parent.user_id:
        raise HTTPException(status_code=404, detail="Learner not found")
    return relationship


def erase_learner_transactional(
    db: Session, *, parent: ParentProfile, learner_id: uuid.UUID
) -> LearnerDeletionResult:
    """Erase one authorized learner and learner-scoped evidence atomically.

    The caller owns the SQLAlchemy transaction. This function deliberately does
    not commit: API/service boundaries commit only after every dependency has
    been handled, so any exception rolls the entire operation back.
    """
    relationship = _authorized_relationship(db, parent=parent, learner_id=learner_id)

    relationship_ids = list(
        db.scalars(
            select(ParentStudentRelationship.id).where(
                ParentStudentRelationship.student_id == learner_id
            )
        )
    )
    session_ids = list(
        db.scalars(select(TutorSession.id).where(TutorSession.student_id == learner_id))
    )
    diagnostic_session_ids = list(
        db.scalars(
            select(DiagnosticSession.id).where(DiagnosticSession.student_id == learner_id)
        )
    )
    attempt_ids = list(
        db.scalars(select(Attempt.id).where(Attempt.student_id == learner_id))
    )

    # Disposable telemetry can reference tutor sessions. Remove it before the
    # authoritative session rows; it never owns mastery or intervention state.
    if session_ids:
        db.execute(
            delete(TelemetryEventRecord).where(
                TelemetryEventRecord.session_id.in_(session_ids)
            )
        )

    # Leaf records that reference attempts/turns/sessions must go first.
    db.execute(delete(HintEvent).where(HintEvent.student_id == learner_id))
    db.execute(delete(MasteryEvent).where(MasteryEvent.student_id == learner_id))
    if session_ids:
        db.execute(delete(TutorTurn).where(TutorTurn.session_id.in_(session_ids)))
    if attempt_ids:
        # Defensive: turns can also reference an attempt from the learner.
        db.execute(delete(TutorTurn).where(TutorTurn.attempt_id.in_(attempt_ids)))
    db.execute(delete(Attempt).where(Attempt.student_id == learner_id))

    if diagnostic_session_ids:
        db.execute(
            delete(DiagnosticAttempt).where(
                DiagnosticAttempt.diagnostic_session_id.in_(diagnostic_session_ids)
            )
        )
    db.execute(delete(DiagnosticSession).where(DiagnosticSession.student_id == learner_id))

    db.execute(delete(InterventionRecord).where(InterventionRecord.student_id == learner_id))
    db.execute(delete(StudentMisconception).where(StudentMisconception.student_id == learner_id))
    db.execute(delete(StudentSkill).where(StudentSkill.student_id == learner_id))
    db.execute(
        delete(StudentCurriculumEnrollment).where(
            StudentCurriculumEnrollment.student_id == learner_id
        )
    )
    db.execute(delete(ChildLinkClaim).where(ChildLinkClaim.student_id == learner_id))
    db.execute(delete(TutorSession).where(TutorSession.student_id == learner_id))

    if relationship_ids:
        db.execute(
            delete(ParentStudentRelationshipEvent).where(
                ParentStudentRelationshipEvent.relationship_id.in_(relationship_ids)
            )
        )
    db.execute(
        delete(ParentStudentRelationship).where(
            ParentStudentRelationship.student_id == learner_id
        )
    )

    deleted = db.execute(
        delete(Student).where(
            Student.id == learner_id,
            Student.parent_id == parent.user_id,
        )
    )
    if int(deleted.rowcount or 0) != 1:
        # This should be unreachable after authorization. Raising here keeps
        # unknown/concurrent ownership changes from producing a partial erase.
        raise RuntimeError("learner deletion lost authorization before completion")

    # Keep a local reference so static analysis/tests make it explicit that
    # authorization was established before the first mutation.
    assert relationship.student_id == learner_id
    return LearnerDeletionResult(learner_id=learner_id)
