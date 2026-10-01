import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.curriculum_models import StudentCurriculumEnrollment
from app.identity import CurrentParent, require_parent_owns_student
from app.models import (
    Curriculum,
    LearnerAward,
    Skill,
    SkillStatus,
    Student,
    StudentSkill,
    TutorSession,
)
from app.parent_models import ParentProfile, ParentStudentRelationship, ParentStudentRelationshipEvent
from app.services.placement import recommend_next_skill
from app.services.problem_generation import content_readiness
from app.services.review_schedule import reviews_due

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
DbSession = Annotated[Session, Depends(get_db)]


class CurriculumChoice(BaseModel):
    id: uuid.UUID
    code: str
    version: str
    jurisdiction: str | None
    grade_level: str | None


class LearnerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    curriculum_id: uuid.UUID


class LearnerCreated(BaseModel):
    id: uuid.UUID
    first_name: str
    curriculum_id: uuid.UUID
    curriculum_code: str
    curriculum_version: str
    jurisdiction: str | None


class LearnerChoice(BaseModel):
    id: uuid.UUID
    first_name: str
    curriculum_id: uuid.UUID
    curriculum_code: str
    curriculum_version: str
    jurisdiction: str | None


class SkillChoice(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    content_ready: bool = True


class LaunchpadSkill(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    reason: str
    mastery_score: float
    session_id: uuid.UUID | None = None


class LaunchpadReview(BaseModel):
    skill_id: uuid.UUID
    skill_name: str


class LearnerLaunchpad(BaseModel):
    recommended: LaunchpadSkill | None
    reviews_due: list[LaunchpadReview]
    mastered_count: int
    learning_count: int
    ready_skill_count: int
    award_count: int


@router.get("/curricula", response_model=list[CurriculumChoice])
def list_active_curricula(parent: CurrentParent, db: DbSession) -> list[CurriculumChoice]:
    curricula = db.scalars(
        select(Curriculum)
        .where(Curriculum.active.is_(True))
        .order_by(Curriculum.jurisdiction, Curriculum.grade_level, Curriculum.code, Curriculum.version)
    ).all()
    return [
        CurriculumChoice(
            id=curriculum.id,
            code=curriculum.code,
            version=curriculum.version,
            jurisdiction=curriculum.jurisdiction,
            grade_level=curriculum.grade_level,
        )
        for curriculum in curricula
    ]


@router.get("/learners", response_model=list[LearnerChoice])
def list_learners(parent: CurrentParent, db: DbSession) -> list[LearnerChoice]:
    rows = db.execute(
        select(Student, Curriculum)
        .join(Curriculum, Curriculum.id == Student.curriculum_id)
        .where(Student.parent_id == parent.user_id, Student.active.is_(True))
        .order_by(Student.first_name, Student.id)
    ).all()
    return [
        LearnerChoice(
            id=student.id,
            first_name=student.first_name,
            curriculum_id=curriculum.id,
            curriculum_code=curriculum.code,
            curriculum_version=curriculum.version,
            jurisdiction=curriculum.jurisdiction,
        )
        for student, curriculum in rows
    ]


@router.get("/learners/{student_id}/skills", response_model=list[SkillChoice])
def list_learner_skills(
    student_id: uuid.UUID, parent: CurrentParent, db: DbSession
) -> list[SkillChoice]:
    student = require_parent_owns_student(parent, db.get(Student, student_id))
    if student.curriculum_id is None:
        raise HTTPException(status_code=409, detail="Learner curriculum is unavailable")
    skills = db.scalars(
        select(Skill)
        .where(Skill.curriculum_id == student.curriculum_id)
        .order_by(Skill.difficulty_level, Skill.code)
    ).all()
    return [
        SkillChoice(
            id=skill.id,
            code=skill.code,
            name=skill.name,
            content_ready=content_readiness(db, skill_id=skill.id).ready,
        )
        for skill in skills
    ]


@router.get("/learners/{student_id}/launchpad", response_model=LearnerLaunchpad)
def get_learner_launchpad(
    student_id: uuid.UUID, parent: CurrentParent, db: DbSession
) -> LearnerLaunchpad:
    student = require_parent_owns_student(parent, db.get(Student, student_id))
    if student.curriculum_id is None:
        raise HTTPException(status_code=409, detail="Learner curriculum is unavailable")

    skills = db.scalars(
        select(Skill).where(Skill.curriculum_id == student.curriculum_id)
    ).all()
    skill_ids = [skill.id for skill in skills]
    progress_rows = db.scalars(
        select(StudentSkill).where(
            StudentSkill.student_id == student.id,
            StudentSkill.skill_id.in_(skill_ids),
        )
    ).all() if skill_ids else []
    progress_by_skill = {row.skill_id: row for row in progress_rows}

    active_session = db.scalar(
        select(TutorSession)
        .where(
            TutorSession.student_id == student.id,
            TutorSession.curriculum_id == student.curriculum_id,
            TutorSession.status == "ACTIVE",
        )
        .order_by(TutorSession.started_at.desc(), TutorSession.id.desc())
    )
    recommended = None
    if active_session is not None:
        active_skill = db.get(
            Skill, active_session.active_skill_id or active_session.primary_skill_id
        )
        if active_skill is not None and active_skill.curriculum_id == student.curriculum_id:
            progress = progress_by_skill.get(active_skill.id)
            recommended = LaunchpadSkill(
                id=active_skill.id,
                code=active_skill.code,
                name=active_skill.name,
                reason="CONTINUE_SESSION",
                mastery_score=float(progress.mastery_score) if progress else 0.0,
                session_id=active_session.id,
            )
    if recommended is None:
        placement = recommend_next_skill(
            db, student_id=student.id, curriculum_id=student.curriculum_id
        )
        if placement is not None and content_readiness(
            db, skill_id=placement.skill.id
        ).ready:
            progress = progress_by_skill.get(placement.skill.id)
            recommended = LaunchpadSkill(
                id=placement.skill.id,
                code=placement.skill.code,
                name=placement.skill.name,
                reason=placement.reason,
                mastery_score=float(progress.mastery_score) if progress else 0.0,
            )

    review_items = reviews_due(
        db, student_id=student.id, curriculum_id=student.curriculum_id
    )
    mastered_count = sum(row.status == SkillStatus.MASTERED for row in progress_rows)
    learning_count = sum(
        row.status not in {SkillStatus.NOT_STARTED, SkillStatus.MASTERED}
        for row in progress_rows
    )
    ready_skill_count = sum(
        content_readiness(db, skill_id=skill.id).ready for skill in skills
    )
    award_count = db.scalar(
        select(func.count(LearnerAward.id)).where(LearnerAward.student_id == student.id)
    ) or 0
    return LearnerLaunchpad(
        recommended=recommended,
        reviews_due=[
            LaunchpadReview(skill_id=item.skill.id, skill_name=item.skill.name)
            for item in review_items
        ],
        mastered_count=mastered_count,
        learning_count=learning_count,
        ready_skill_count=ready_skill_count,
        award_count=award_count,
    )


@router.post("/learners", response_model=LearnerCreated, status_code=status.HTTP_201_CREATED)
def create_learner(payload: LearnerCreate, parent: CurrentParent, db: DbSession) -> LearnerCreated:
    locked_parent = db.scalar(
        select(ParentProfile).where(ParentProfile.id == parent.id).with_for_update()
    )
    if locked_parent is None:
        raise HTTPException(status_code=404, detail="Parent profile not found")
    current_count = int(
        db.scalar(
            select(func.count(ParentStudentRelationship.id)).where(
                ParentStudentRelationship.parent_profile_id == parent.id,
                ParentStudentRelationship.active.is_(True),
            )
        )
        or 0
    )
    if current_count >= locked_parent.max_students:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "STUDENT_SEAT_LIMIT_REACHED",
                "subscription_tier": locked_parent.subscription_tier,
                "current_students": current_count,
                "max_students": locked_parent.max_students,
                "upgrade": {"recommended_tier": "pro", "max_students": 5},
            },
        )

    curriculum = db.get(Curriculum, payload.curriculum_id)
    if curriculum is None or not curriculum.active:
        raise HTTPException(status_code=404, detail="Active curriculum not found")

    first_name = payload.first_name.strip()
    if not first_name:
        raise HTTPException(status_code=422, detail="Learner first name is required")

    student = Student(
        parent_id=parent.user_id,
        curriculum_id=curriculum.id,
        first_name=first_name,
        grade_level=curriculum.grade_level or "UNSPECIFIED",
        school_system=None,
        avatar_id="avatar-1",
    )
    db.add(student)
    db.flush()
    db.add(
        StudentCurriculumEnrollment(
            student_id=student.id,
            curriculum_id=curriculum.id,
            provenance_json={"source": "parent_onboarding"},
        )
    )
    relationship = ParentStudentRelationship(
        parent_profile_id=parent.id,
        student_id=student.id,
        relationship_type="GUARDIAN",
        active=True,
    )
    db.add(relationship)
    db.flush()
    db.add(ParentStudentRelationshipEvent(relationship_id=relationship.id, action="LINKED"))
    db.commit()

    return LearnerCreated(
        id=student.id,
        first_name=student.first_name,
        curriculum_id=curriculum.id,
        curriculum_code=curriculum.code,
        curriculum_version=curriculum.version,
        jurisdiction=curriculum.jurisdiction,
    )
