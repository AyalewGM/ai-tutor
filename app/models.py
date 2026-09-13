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


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    grade_level: Mapped[str | None] = mapped_column(String(30))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("curriculum_id", "code", name="uq_skills_curriculum_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curriculum_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curricula.id"))
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    grade_level: Mapped[str | None] = mapped_column(String(30))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    prerequisites_json: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    answer_type: Mapped[str] = mapped_column(String(50), default="numeric")
    correct_answer: Mapped[str] = mapped_column(String(255))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    is_diagnostic: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class StudentSkillState(Base):
    __tablename__ = "student_skill_state"
    __table_args__ = (UniqueConstraint("student_id", "skill_id", name="uq_student_skill_state"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    mastery_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0)
    independent_correct_streak: Mapped[int] = mapped_column(Integer, default=0)
    independent_attempts: Mapped[int] = mapped_column(Integer, default=0)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_hint_level: Mapped[int] = mapped_column(Integer, default=0)
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id"), index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tutor_sessions.id"), index=True)
    answer: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    hint_level: Mapped[int] = mapped_column(Integer, default=0)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class TutorSession(Base):
    __tablename__ = "tutor_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    primary_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"))
    active_skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"))
    curriculum_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("curricula.id"), index=True)
    curriculum_enrollment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("student_curriculum_enrollments.id"), index=True)
    remediation_reason: Mapped[str | None] = mapped_column(String(120))
    session_goal: Mapped[str | None] = mapped_column(String(500))
    current_state: Mapped[TutorState] = mapped_column(Enum(TutorState), default=TutorState.DIAGNOSE)
    hint_level: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
