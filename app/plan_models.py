"""Subscription plans and platform-wide settings.

Plans are the source of truth for seat limits, AI generation caps, and
pricing. USD is the base currency; the CAD price is computed once from the
3-year-average USD→CAD rate (cents dropped) and only recalculated when an
admin triggers it — never converted per request.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    monthly_price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # Whole Canadian dollars — USD price x the stored 3-year-average rate,
    # cents dropped. Recalculated only via the admin recalc action.
    monthly_price_cad: Mapped[int] = mapped_column(Integer, nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_daily_generations: Mapped[int] = mapped_column(Integer, nullable=False)
    # Stripe Price ids for checkout — NULL until the operator creates the
    # prices in Stripe and writes them here (via PATCH /admin/plans).
    stripe_price_id_usd: Mapped[str | None] = mapped_column(String(255))
    stripe_price_id_cad: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class PlatformSetting(Base):
    """Small key/value store for operator-managed values (e.g. the stored
    USD→CAD average rate and when it was computed)."""

    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
