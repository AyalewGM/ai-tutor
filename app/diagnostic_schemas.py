import uuid

from pydantic import BaseModel, Field

from app.schemas import ProblemOut


class DiagnosticStartIn(BaseModel):
    student_id: uuid.UUID
    target_skill_id: uuid.UUID


class DiagnosticRespondIn(BaseModel):
    problem_id: uuid.UUID
    answer: str = Field(min_length=1)


class DiagnosticSkillEvidenceOut(BaseModel):
    skill_id: uuid.UUID
    correct_count: int
    incorrect_count: int
    mastery_score: float
    confidence_score: float


class DiagnosticOut(BaseModel):
    session_id: uuid.UUID
    status: str
    target_skill_id: uuid.UUID
    current_skill_id: uuid.UUID
    question_count: int
    max_questions: int
    problem: ProblemOut | None = None
    last_answer_correct: bool | None = None
    recommended_skill_id: uuid.UUID | None = None
    placement_reason: str | None = None
    message: str


class DiagnosticResultOut(BaseModel):
    session_id: uuid.UUID
    status: str
    target_skill_id: uuid.UUID
    recommended_skill_id: uuid.UUID | None
    placement_reason: str | None
    question_count: int
    evidence: list[DiagnosticSkillEvidenceOut]
