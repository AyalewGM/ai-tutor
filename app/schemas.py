import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import TutorState


class SessionCreate(BaseModel):
    student_id: uuid.UUID
    skill_id: uuid.UUID


class ProblemChoiceOut(BaseModel):
    id: str
    text: str


def problem_choices_out(choices: list | None) -> list[ProblemChoiceOut] | None:
    """Serialize choices for the wire; distractor misconception codes stay server-side."""
    if not choices:
        return None
    return [
        ProblemChoiceOut(id=str(choice.get("id", "")), text=str(choice.get("text", "")))
        for choice in choices
    ]


class ProblemOut(BaseModel):
    id: uuid.UUID
    prompt: str
    difficulty: int
    answer_kind: str = "FREE_TEXT"
    choices: list[ProblemChoiceOut] | None = None
    problem_type: str | None = None
    supports_steps: bool = False


class WorkStepIn(BaseModel):
    problem_id: uuid.UUID
    line: str = Field(min_length=1, max_length=200)


class ReverseChallengeOut(BaseModel):
    line: str
    prompt: str


class WorkStepOut(BaseModel):
    status: Literal["solved", "valid", "invalid", "unparseable", "duplicate"]
    feedback: str | None = None
    misconception_code: str | None = None
    revealed_line: str | None = None
    normalized_line: str | None = None
    invalid_count: int = 0
    cpa_level: str | None = None
    step_visual: dict | None = None
    reverse_challenge: ReverseChallengeOut | None = None
    challenge_outcome: Literal["spotted", "missed", "unresolved"] | None = None


class PhotoLineOut(BaseModel):
    text: str
    needs_review: bool = False


class PhotoScanOut(BaseModel):
    problem_id: uuid.UUID
    lines: list[PhotoLineOut]
    engine: str


class MasteryOut(BaseModel):
    score: float
    confidence: float


class LearningFocusOut(BaseModel):
    target_skill_id: uuid.UUID
    active_skill_id: uuid.UUID
    in_remediation: bool
    remediation_reason: str | None = None


class SessionOut(BaseModel):
    session_id: uuid.UUID
    state: TutorState
    mastery: MasteryOut
    focus: LearningFocusOut | None = None
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


class AwardOut(BaseModel):
    code: str
    name: str
    description: str
    skill_name: str | None = None
    awarded_at: datetime


class GrowthOut(BaseModel):
    xp: int
    level: int
    level_title: str
    xp_in_level: int
    xp_for_next: int
    xp_today: int = 0
    leveled_up: bool = False


class RespondOut(BaseModel):
    session_id: uuid.UUID
    state: TutorState
    evaluation: EvaluationOut
    tutor: TutorOut
    mastery: MasteryOut
    focus: LearningFocusOut | None = None
    next_problem: ProblemOut | None = None
    new_awards: list[AwardOut] = Field(default_factory=list)
    xp_earned: int = 0
    growth: GrowthOut | None = None



class ParentRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    parent_pin: str = Field(pattern=r"^\d{4}$")
    terms_accepted: Literal[True]
    coppa_consent_given: Literal[True]


class StudentCreateSchema(BaseModel):
    display_name: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    grade_level: str | None = Field(default=None, min_length=1, max_length=30)
    avatar_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")

    @field_validator("display_name")
    @classmethod
    def reject_contact_like_display_names(cls, value: str) -> str:
        normalized = value.strip()
        if "@" in normalized or "." in normalized:
            raise ValueError("Use a short nickname, not contact information")
        return normalized


class PINVerifySchema(BaseModel):
    parent_pin: str = Field(pattern=r"^\d{4}$")


class PasswordReauthSchema(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class StudentProfileOut(BaseModel):
    id: uuid.UUID
    display_name: str
    grade_level: str | None
    avatar_id: str


class PINVerifyOut(BaseModel):
    verified: bool
    unlock_token: str
    expires_in_seconds: int


class ProgressStudentSummary(BaseModel):
    student_id: uuid.UUID
    display_name: str
    sessions_started: int
    sessions_completed: int
    attempts: int
    correct_attempts: int
    average_mastery: float


class ProgressSummaryOut(BaseModel):
    window_days: int
    students: list[ProgressStudentSummary]
