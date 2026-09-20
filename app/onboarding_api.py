import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.curriculum_models import StudentCurriculumEnrollment
from app.identity import CurrentParent, require_parent_owns_student
from app.models import Curriculum, Skill, Student
from app.parent_models import ParentStudentRelationship, ParentStudentRelationshipEvent
from app.services.problem_generation import content_readiness

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
DbSession = Annotated[Session, Depends(get_db)]


class CurriculumChoice(BaseModel):
    id: uuid.UUID
    code: str
    version: str
    jurisdiction: str | None
    grade_level: str | None


class LearnerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
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


@router.post("/learners", response_model=LearnerCreated, status_code=status.HTTP_201_CREATED)
def create_learner(payload: LearnerCreate, parent: CurrentParent, db: DbSession) -> LearnerCreated:
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
