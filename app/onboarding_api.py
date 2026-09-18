import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.curriculum_models import StudentCurriculumEnrollment
from app.identity import CurrentParent
from app.models import Curriculum, Student

router = APIRouter(prefix="/onboarding", tags=["onboarding"])
DbSession = Annotated[Session, Depends(get_db)]


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
    db.commit()

    return LearnerCreated(
        id=student.id,
        first_name=student.first_name,
        curriculum_id=curriculum.id,
        curriculum_code=curriculum.code,
        curriculum_version=curriculum.version,
        jurisdiction=curriculum.jurisdiction,
    )
