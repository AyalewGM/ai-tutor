import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ParentProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str | None = None
    email: str


class ParentProfileUpdateIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)


class ChildSummaryOut(BaseModel):
    id: uuid.UUID
    first_name: str
    grade_level: str
    school_system: str | None = None
    curriculum_name: str | None = None
    curriculum_code: str | None = None
    curriculum_version: str | None = None
    curriculum_authority_name: str | None = None
    jurisdiction: str | None = None
    jurisdiction_path: list[str] = Field(default_factory=list)
    local_authority_name: str | None = None


class LinkChildIn(BaseModel):
    claim_token: str = Field(min_length=16, max_length=512)


class LinkChildOut(BaseModel):
    child: ChildSummaryOut
    relationship_type: str


class SkillProgressOut(BaseModel):
    skill_id: uuid.UUID
    skill_code: str
    skill_name: str
    status: str
    attempt_count: int
    independent_attempt_count: int
    independent_correct_count: int
    hinted_correct_count: int
    evidence_status: str
    learning_state: str
    assistance_signal: str
    reason_code: str
    action_code: str


class RecentActivityOut(BaseModel):
    session_id: uuid.UUID
    skill_name: str
    state: str
    started_at: datetime
    ended_at: datetime | None = None


class SupportAreaOut(BaseModel):
    code: str
    name: str
    occurrence_count: int


class ReviewDueOut(BaseModel):
    skill_id: uuid.UUID
    skill_code: str
    skill_name: str
    status: str
    due_at: datetime
    interval_index: int
    mastery_score: float
    projected_mastery_score: float


class RecommendedSkillOut(BaseModel):
    skill_id: uuid.UUID
    skill_code: str
    skill_name: str
    reason: str


class ChildDashboardOut(BaseModel):
    child: ChildSummaryOut
    active_skill_name: str | None = None
    skills: list[SkillProgressOut]
    recent_activity: list[RecentActivityOut]
    support_areas: list[SupportAreaOut]
    reviews_due: list[ReviewDueOut] = Field(default_factory=list)
    recommended_next: RecommendedSkillOut | None = None
