import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import (
    Curriculum,
    Misconception,
    Skill,
    Student,
    StudentMisconception,
    StudentSkill,
    TutorSession,
)
from app.parent_models import ChildLinkClaim, ParentProfile, ParentStudentRelationship
from app.parent_schemas import (
    ChildDashboardOut,
    ChildSummaryOut,
    LinkChildOut,
    RecentActivityOut,
    SkillProgressOut,
    SupportAreaOut,
)


def hash_claim_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _active_relationship(
    db: Session, *, parent_id: uuid.UUID, student_id: uuid.UUID
) -> ParentStudentRelationship | None:
    return db.scalar(
        select(ParentStudentRelationship).where(
            ParentStudentRelationship.parent_profile_id == parent_id,
            ParentStudentRelationship.student_id == student_id,
            ParentStudentRelationship.active.is_(True),
        )
    )


def require_linked_child(
    db: Session, *, parent: ParentProfile, student_id: uuid.UUID
) -> Student:
    relationship = _active_relationship(db, parent_id=parent.id, student_id=student_id)
    if relationship is None:
        raise HTTPException(status_code=403, detail="Child is not linked to this parent")
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return student


def child_summary(db: Session, student: Student) -> ChildSummaryOut:
    curriculum = db.get(Curriculum, student.curriculum_id) if student.curriculum_id else None
    return ChildSummaryOut(
        id=student.id,
        first_name=student.first_name,
        grade_level=student.grade_level,
        school_system=student.school_system,
        curriculum_name=curriculum.name if curriculum else None,
        jurisdiction=curriculum.jurisdiction if curriculum else None,
    )


def list_children(db: Session, *, parent: ParentProfile) -> list[ChildSummaryOut]:
    students = db.scalars(
        select(Student)
        .join(
            ParentStudentRelationship,
            ParentStudentRelationship.student_id == Student.id,
        )
        .where(
            ParentStudentRelationship.parent_profile_id == parent.id,
            ParentStudentRelationship.active.is_(True),
        )
        .order_by(Student.first_name, Student.id)
    ).all()
    return [child_summary(db, student) for student in students]


def link_child_with_claim(
    db: Session, *, parent: ParentProfile, claim_token: str
) -> LinkChildOut:
    now = datetime.now(timezone.utc)
    claim = db.scalar(
        select(ChildLinkClaim).where(ChildLinkClaim.token_hash == hash_claim_token(claim_token))
    )
    if claim is None or claim.consumed_at is not None or claim.expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid or expired child link claim")

    student = db.get(Student, claim.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Child not found")

    relationship = db.scalar(
        select(ParentStudentRelationship).where(
            ParentStudentRelationship.parent_profile_id == parent.id,
            ParentStudentRelationship.student_id == student.id,
        )
    )
    if relationship is None:
        relationship = ParentStudentRelationship(
            parent_profile_id=parent.id,
            student_id=student.id,
            relationship_type="GUARDIAN",
            active=True,
        )
        db.add(relationship)
    else:
        relationship.active = True
        relationship.unlinked_at = None

    claim.consumed_at = now
    db.flush()
    return LinkChildOut(
        child=child_summary(db, student),
        relationship_type=relationship.relationship_type,
    )


def unlink_child(db: Session, *, parent: ParentProfile, student_id: uuid.UUID) -> None:
    relationship = _active_relationship(db, parent_id=parent.id, student_id=student_id)
    if relationship is None:
        raise HTTPException(status_code=404, detail="Active child relationship not found")
    relationship.active = False
    relationship.unlinked_at = datetime.now(timezone.utc)
    db.flush()


def dashboard(db: Session, *, parent: ParentProfile, student_id: uuid.UUID) -> ChildDashboardOut:
    student = require_linked_child(db, parent=parent, student_id=student_id)

    progress_rows = db.execute(
        select(StudentSkill, Skill)
        .join(Skill, Skill.id == StudentSkill.skill_id)
        .where(StudentSkill.student_id == student.id)
        .order_by(Skill.name)
    ).all()
    skills = [
        SkillProgressOut(
            skill_id=skill.id,
            skill_code=skill.code,
            skill_name=skill.name,
            status=progress.status.value,
            attempt_count=progress.attempt_count,
            independent_attempt_count=progress.independent_attempt_count,
            independent_correct_count=progress.independent_correct_count,
            hinted_correct_count=progress.hinted_correct_count,
        )
        for progress, skill in progress_rows
    ]

    sessions = db.execute(
        select(TutorSession, Skill)
        .join(Skill, Skill.id == TutorSession.primary_skill_id)
        .where(TutorSession.student_id == student.id)
        .order_by(desc(TutorSession.started_at))
        .limit(10)
    ).all()
    recent_activity = [
        RecentActivityOut(
            session_id=session.id,
            skill_name=skill.name,
            state=session.current_state.value,
            started_at=session.started_at,
            ended_at=session.ended_at,
        )
        for session, skill in sessions
    ]

    support_rows = db.execute(
        select(StudentMisconception, Misconception)
        .join(Misconception, Misconception.id == StudentMisconception.misconception_id)
        .where(
            StudentMisconception.student_id == student.id,
            StudentMisconception.status == "ACTIVE",
        )
        .order_by(desc(StudentMisconception.occurrence_count))
        .limit(10)
    ).all()
    support_areas = [
        SupportAreaOut(
            code=misconception.code,
            name=misconception.name,
            occurrence_count=student_misconception.occurrence_count,
        )
        for student_misconception, misconception in support_rows
    ]

    active_session = db.scalar(
        select(TutorSession)
        .where(TutorSession.student_id == student.id, TutorSession.status == "ACTIVE")
        .order_by(desc(TutorSession.started_at))
        .limit(1)
    )
    active_skill_name = None
    if active_session and active_session.active_skill_id:
        active_skill = db.get(Skill, active_session.active_skill_id)
        active_skill_name = active_skill.name if active_skill else None

    return ChildDashboardOut(
        child=child_summary(db, student),
        active_skill_name=active_skill_name,
        skills=skills,
        recent_activity=recent_activity,
        support_areas=support_areas,
    )
