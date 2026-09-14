import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

import app.content_models
import app.curriculum_models  # noqa: F401
from app.core.database import Base


class TutorState(str, enum.Enum):
    DIAGNOSE = "DIAGNOSE"
    INTRODUCE = "INTRODUCE"
    MODEL = "MODEL"
    GUIDED_PRACTICE = "GUIDED_PRACTICE"
    INDEPENDENT_PRACTICE = "INDEPENDENT_PRACTICE"
    MASTERY_CHECK = "MASTERY_CHECK"
    REMEDIATION = "REMEDIATION"
    REVIEW = "REVIEW"
    COMPLETE = "COMPLETE"


class SkillStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    INTRODUCED = "INTRODUCED"
    LEARNING = "LEARNING"
    PRACTICING = "PRACTICING"
    MASTERED = "MASTERED"
    REVIEW_DUE = "REVIEW_DUE"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(30), default="PARENT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Curriculum(Base):
    __tablename__ = "curricula"
    __table_args__ = (
        UniqueConstraint("authority_id", "code", "version", name="uq_curricula_authority_code_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255))
    jurisdiction: Mapped[str | None] = mapped_column(String(255))
    grade_level: Mapped[str | None] = mapped_column(String(30))
    authority_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("education_authorities.id"), index=True
    )
    version: Mapped[str] = mapped_column(String(80), default="1")
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_uri: Mapped[str | None] = mapped_column(Text)
    provenance_json: Mapped[dict | None] = mapped_column(JSONB)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Student(Base):
    __tablename__ = "students"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    curriculum_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("curricula.id"))
    first_name: Mapped[str] = mapped_column(String(100))
    grade_level: Mapped[str] = mapped_column(String(30))
    school_system: Mapped[str | None] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        UniqueConstraint("curriculum_id", "code", name="uq_skills_curriculum_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curriculum_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curricula.id"))
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=1)
    mastery_threshold: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=Decimal("0.850"))


class SkillPrerequisite(Base):
    __tablename__ = "skill_prerequisites"
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    prerequisite_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    importance_weight: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=Decimal("1.0"))


class StudentSkill(Base):
    __tablename__ = "student_skills"
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    mastery_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=Decimal(0))
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=Decimal(0))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    independent_attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    independent_correct_count: Mapped[int] = mapped_column(Integer, default=0)
    hinted_correct_count: Mapped[int] = mapped_column(Integer, default=0)
    current_difficulty: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[SkillStatus] = mapped_column(Enum(SkillStatus), default=SkillStatus.NOT_STARTED)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Misconception(Base):
    __tablename__ = "misconceptions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"))
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    remediation_strategy: Mapped[str | None] = mapped_column(Text)


class StudentMisconception(Base):
    __tablename__ = "student_misconceptions"
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), primary_key=True)
    misconception_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("misconceptions.id"), primary_key=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")


class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primary_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    problem_type: Mapped[str] = mapped_column(String(50))
    difficulty: Mapped[int] = mapped_column(Integer)
    prompt: Mapped[str] = mapped_column(Text)
    canonical_answer: Mapped[str | None] = mapped_column(Text)
    solution: Mapped[dict | None] = mapped_column(JSONB)
    source_type: Mapped[str] = mapped_column(String(30), default="CURATED")


class TutorSession(Base):
    __tablename__ = "tutor_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    primary_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"))
    active_skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"))
    curriculum_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("curricula.id"), index=True)
    curriculum_enrollment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("student_curriculum_enrollments.id"), index=True
    )
    remediation_reason: Mapped[str | None] = mapped_column(String(120))
    session_goal: Mapped[str | None] = mapped_column(String(500))
    current_state: Mapped[TutorState] = mapped_column(Enum(TutorState), default=TutorState.DIAGNOSE)
    starting_mastery: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    ending_mastery: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (UniqueConstraint("session_id", "problem_id", "attempt_number"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tutor_sessions.id"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id"))
    student_answer: Mapped[str] = mapped_column(Text)
    normalized_answer: Mapped[str | None] = mapped_column(Text)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    assistance_level: Mapped[int] = mapped_column(Integer, default=0)
    misconception_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("misconceptions.id"))
    misconception_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    evaluation_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    state_at_attempt: Mapped[TutorState | None] = mapped_column(Enum(TutorState))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class TutorTurn(Base):
    __tablename__ = "tutor_turns"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tutor_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    state: Mapped[TutorState | None] = mapped_column(Enum(TutorState))
    pedagogical_action: Mapped[str | None] = mapped_column(String(50))
    problem_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("problems.id"))
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("attempts.id"))
    llm_model: Mapped[str | None] = mapped_column(String(100))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MasteryEvent(Base):
    __tablename__ = "mastery_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("attempts.id"))
    previous_score: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    new_score: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    previous_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    new_confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    reason: Mapped[str] = mapped_column(String(100))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class InterventionRecord(Base):
    __tablename__ = "intervention_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    curriculum_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curricula.id"), index=True)
    target_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    prerequisite_skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"), index=True)
    policy_version: Mapped[str] = mapped_column(String(80), index=True)
    state: Mapped[str] = mapped_column(String(50), index=True)
    reason_code: Mapped[str] = mapped_column(String(120))
    evidence_ids_json: Mapped[list] = mapped_column(JSONB, default=list)
    return_condition: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(30), default="RECOMMENDED", index=True)
    outcome_code: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
