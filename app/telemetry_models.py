from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TelemetryEventRecord(Base):
    __tablename__ = "telemetry_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    schema_version: Mapped[str] = mapped_column(String(40))
    learner_pseudonymous_id: Mapped[str] = mapped_column(String(100), index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tutor_sessions.id"), index=True
    )
    curriculum_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curricula.id"), index=True)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id"), index=True)
    policy_version: Mapped[str | None] = mapped_column(String(80))
    purpose: Mapped[str] = mapped_column(String(100))
    retention_class: Mapped[str] = mapped_column(String(40), index=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    deletion_audit_note: Mapped[str | None] = mapped_column(Text)
