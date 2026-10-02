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


class StrandSummaryOut(BaseModel):
    strand: str
    total: int
    mastered: int
    in_progress: int


class GradeLevelSummaryOut(BaseModel):
    curriculum_code: str | None
    curriculum_name: str | None
    skills_total: int
    skills_mastered: int
    skills_in_progress: int
    skills_not_started: int
    mastery_percent: float
    strands: list[StrandSummaryOut]
    sessions_last_7_days: int
    minutes_last_7_days: int
    trouble_spots: list[str]


class DailyMetricOut(BaseModel):
    date: str
    label: str
    minutes: int
    mastery_score: float


class WeeklyDigestOut(BaseModel):
    sessions: int
    minutes: int
    xp_earned: int
    skills_mastered: int
    badges_earned: int
    prev_sessions: int
    prev_minutes: int
    minutes_delta: int
    mastery_delta: float | None = None
    days_since_practice: int | None = None
    stall: bool = False


class ChildDashboardOut(BaseModel):
    child: ChildSummaryOut
    active_skill_name: str | None = None
    skills: list[SkillProgressOut]
    recent_activity: list[RecentActivityOut]
    support_areas: list[SupportAreaOut]
    reviews_due: list[ReviewDueOut] = Field(default_factory=list)
    recommended_next: RecommendedSkillOut | None = None
    grade_level_summary: GradeLevelSummaryOut | None = None
    daily_metrics: list[DailyMetricOut] = Field(default_factory=list)
    weekly_digest: WeeklyDigestOut | None = None
