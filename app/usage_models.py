"""AI usage ledger and per-model cost rates.

The ledger records every billable tutor generation (and budget denials) so
spend can be capped per family and globally, and so the admin dashboard can
report families by AI cost. Tokens and cost are application-recorded —
never trusted from the client.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AiUsageEvent(Base):
    """One row per tutor generation attempt that reached (or was denied
    before reaching) the AI provider."""

    __tablename__ = "ai_usage_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # The family account (users.id). NULL for unattributed calls (e.g. a
    # learner with no linked parent) — they still count toward the global cap.
    family_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("students.id"), index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tutor_sessions.id"), index=True
    )
    action: Mapped[str] = mapped_column(String(40))
    provider: Mapped[str | None] = mapped_column(String(40))
    model: Mapped[str | None] = mapped_column(String(80))
    # "llm" = provider answered; "fallback" = provider unavailable (no billable
    # call); "budget_denied" = refused before the call (no spend).
    source: Mapped[str] = mapped_column(String(20))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    # True when token counts were estimated because the provider did not
    # report usage (the internal gateway may not).
    tokens_estimated: Mapped[bool] = mapped_column(default=False, nullable=False)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), default=Decimal(0), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )


class AiModelRate(Base):
    """USD cost per million tokens, editable from the admin dashboard.

    Missing models fall back to DEFAULT_RATES in usage_metering, then to a
    conservative built-in estimate.
    """

    __tablename__ = "ai_model_rates"

    provider: Mapped[str] = mapped_column(String(40), primary_key=True)
    model: Mapped[str] = mapped_column(String(80), primary_key=True)
    input_usd_per_1m: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    output_usd_per_1m: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
