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


class CampaignStartIn(BaseModel):
    student_id: uuid.UUID


class CampaignSkillRef(BaseModel):
    id: uuid.UUID
    code: str
    name: str


class CampaignOut(BaseModel):
    campaign_id: uuid.UUID
    status: str
    question_count: int
    max_questions: int
    targets_planned: int
    targets_probed: int
    problem: ProblemOut | None = None
    current_skill: CampaignSkillRef | None = None
    last_answer_correct: bool | None = None
    message: str


class CampaignStrandOut(BaseModel):
    name: str
    readiness: str  # STRONG | DEVELOPING | EMERGING | NOT_PROBED
    skills_probed: int
    skills_ready: int
    skills_total: int
    deepest_gap: CampaignSkillRef | None = None


class CampaignSkillResultOut(BaseModel):
    skill: CampaignSkillRef
    strand: str
    verdict: str  # READY | PARTIAL | NOT_READY
    correct_count: int
    incorrect_count: int


class CampaignReportOut(BaseModel):
    campaign_id: uuid.UUID
    status: str
    question_count: int
    recommended: CampaignSkillRef | None
    strands: list[CampaignStrandOut]
    skills: list[CampaignSkillResultOut]
