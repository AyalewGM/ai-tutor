import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum_models import StudentCurriculumEnrollment
from app.models import Skill, Student, TutorSession


class CurriculumScopeError(ValueError):
    """Raised when learning data crosses the learner/session curriculum boundary."""


@dataclass(frozen=True)
class CurriculumScope:
    curriculum_id: uuid.UUID
    enrollment_id: uuid.UUID | None
    local_authority_id: uuid.UUID | None


def resolve_student_curriculum_scope(db: Session, student: Student) -> CurriculumScope:
    enrollments = db.scalars(
        select(StudentCurriculumEnrollment)
        .where(
            StudentCurriculumEnrollment.student_id == student.id,
            StudentCurriculumEnrollment.active.is_(True),
        )
        .order_by(StudentCurriculumEnrollment.effective_from.desc())
    ).all()
    if len(enrollments) > 1:
        raise CurriculumScopeError("Student has multiple active curriculum enrollments")
    if enrollments:
        enrollment = enrollments[0]
        return CurriculumScope(
            curriculum_id=enrollment.curriculum_id,
            enrollment_id=enrollment.id,
            local_authority_id=enrollment.local_authority_id,
        )

    # Compatibility path for tests/legacy rows created without migration 0006.
    # Migrated production rows are backfilled into student_curriculum_enrollments.
    if student.curriculum_id is not None:
        return CurriculumScope(
            curriculum_id=student.curriculum_id,
            enrollment_id=None,
            local_authority_id=None,
        )
    raise CurriculumScopeError("Student has no active curriculum enrollment")


def require_skill_in_scope(db: Session, *, skill_id: uuid.UUID, scope: CurriculumScope) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise CurriculumScopeError("Skill not found")
    if skill.curriculum_id != scope.curriculum_id:
        raise CurriculumScopeError("Skill does not belong to the student's active curriculum")
    return skill


def require_session_scope(db: Session, session: TutorSession) -> CurriculumScope:
    student = db.get(Student, session.student_id)
    if student is None:
        raise CurriculumScopeError("Session student not found")
    current = resolve_student_curriculum_scope(db, student)

    # Sessions snapshot their curriculum. Legacy sessions may have null snapshot
    # fields until migration 0006 backfills them.
    session_curriculum_id = session.curriculum_id or current.curriculum_id
    if session_curriculum_id != current.curriculum_id:
        raise CurriculumScopeError("Session curriculum no longer matches active learner scope")
    if (
        session.curriculum_enrollment_id is not None
        and current.enrollment_id is not None
        and session.curriculum_enrollment_id != current.enrollment_id
    ):
        raise CurriculumScopeError("Session enrollment does not match active learner scope")
    return CurriculumScope(
        curriculum_id=session_curriculum_id,
        enrollment_id=session.curriculum_enrollment_id or current.enrollment_id,
        local_authority_id=current.local_authority_id,
    )


def require_prerequisite_same_curriculum(
    db: Session,
    *,
    target_skill_id: uuid.UUID,
    prerequisite_skill_id: uuid.UUID,
) -> None:
    target = db.get(Skill, target_skill_id)
    prerequisite = db.get(Skill, prerequisite_skill_id)
    if target is None or prerequisite is None:
        raise CurriculumScopeError("Prerequisite graph references a missing skill")
    if target.curriculum_id != prerequisite.curriculum_id:
        raise CurriculumScopeError("Prerequisite edge crosses curriculum boundaries")
