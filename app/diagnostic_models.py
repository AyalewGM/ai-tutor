import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    target_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"))
    current_skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"))
    blocked_skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"))
    recommended_skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    placement_reason: Mapped[str | None] = mapped_column(String(120))
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    max_questions: Mapped[int] = mapped_column(Integer, default=8)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DiagnosticAttempt(Base):
    __tablename__ = "diagnostic_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diagnostic_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagnostic_sessions.id"), index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id"))
    student_answer: Mapped[str] = mapped_column(Text)
    normalized_answer: Mapped[str | None] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    misconception_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("misconceptions.id"))
    evaluation_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    sequence_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
