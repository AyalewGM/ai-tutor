import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HintEvent(Base):
    __tablename__ = "hint_events"
    __table_args__ = (CheckConstraint("level >= 1 AND level <= 4", name="ck_hint_events_level"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tutor_sessions.id"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"))
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"))
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id"), index=True)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("attempts.id"))
    tutor_turn_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tutor_turns.id"))
    level: Mapped[int] = mapped_column(Integer)
    trigger: Mapped[str] = mapped_column(String(50))
    generation_source: Mapped[str | None] = mapped_column(String(30))
    provider: Mapped[str | None] = mapped_column(String(50))
    llm_model: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
