import uuid

from pydantic import BaseModel, Field


class DiagnosticStartIn(BaseModel):
    student_id: uuid.UUID
    target_skill_id: uuid.UUID


class DiagnosticProblemOut(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    prompt: str
    difficulty: int


class DiagnosticStartOut(BaseModel):
    diagnostic_session_id: uuid.UUID
    problem: DiagnosticProblemOut


class DiagnosticRespondIn(BaseModel):
    problem_id: uuid.UUID
    answer: str = Field(min_length=1, max_length=500)
    assistance_level: int = Field(default=0, ge=0, le=4)


class PlacementOut(BaseModel):
    recommended_skill_id: uuid.UUID
    recommended_difficulty: int
    confidence: float
    tutor_session_id: uuid.UUID | None = None


class DiagnosticRespondOut(BaseModel):
    diagnostic_session_id: uuid.UUID
    correct: bool
    complete: bool
    next_problem: DiagnosticProblemOut | None = None
    placement: PlacementOut | None = None
