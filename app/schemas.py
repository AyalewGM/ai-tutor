import uuid

from pydantic import BaseModel, Field

from app.models import TutorState


class SessionCreate(BaseModel):
    student_id: uuid.UUID
    skill_id: uuid.UUID


class ProblemOut(BaseModel):
    id: uuid.UUID
    prompt: str
    difficulty: int


class MasteryOut(BaseModel):
    score: float
    confidence: float


class SessionOut(BaseModel):
    session_id: uuid.UUID
    state: TutorState
    mastery: MasteryOut
    problem: ProblemOut
    message: str


class RespondIn(BaseModel):
    problem_id: uuid.UUID
    answer: str = Field(min_length=1)
    assistance_level: int = Field(default=0, ge=0, le=4)


class EvaluationOut(BaseModel):
    correct: bool
    confidence: float
    misconception_code: str | None = None
    misconception_confidence: float | None = None


class TutorOut(BaseModel):
    action: str
    hint_level: int | None = None
    message: str


class RespondOut(BaseModel):
    session_id: uuid.UUID
    state: TutorState
    evaluation: EvaluationOut
    tutor: TutorOut
    mastery: MasteryOut
    next_problem: ProblemOut | None = None
