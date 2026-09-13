import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HintEvent(Base):
    __tablename__ = "hint_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tutor_sessions.id"), index=True)
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id"), index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("attempts.id"))
    tutor_turn_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tutor_turns.id"))
    level: Mapped[int] = mapped_column(Integer)
    trigger: Mapped[str] = mapped_column(String(30))
    misconception_code: Mapped[str | None] = mapped_column(String(100))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
