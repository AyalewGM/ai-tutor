import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    target_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    recommended_skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"))
    recommended_difficulty: Mapped[int | None] = mapped_column(Integer)
    placement_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    result_json: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DiagnosticSkillState(Base):
    __tablename__ = "diagnostic_skill_states"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagnostic_sessions.id"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    mastery_estimate: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=Decimal("0.500"))
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=Decimal("0.000"))
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    independent_correct_count: Mapped[int] = mapped_column(Integer, default=0)
    attempted: Mapped[bool] = mapped_column(Boolean, default=False)


class DiagnosticAttempt(Base):
    __tablename__ = "diagnostic_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("diagnostic_sessions.id"), index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id"))
    answer: Mapped[str] = mapped_column(String(500))
    correct: Mapped[bool] = mapped_column(Boolean)
    assistance_level: Mapped[int] = mapped_column(Integer, default=0)
    evidence_weight: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
