"""Plan resolution and CAD pricing.

Seat limits and AI caps come from the plans table; the per-family columns
(``max_students``, ``ai_daily_limit``) are explicit overrides only — NULL
means "follow the plan". CAD prices are stored on the plan and recomputed
only when an admin recalculates against the Bank of Canada 3-year average.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import ROUND_FLOOR, Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.parent_models import ParentProfile
from app.plan_models import Plan, PlatformSetting

logger = logging.getLogger("ai_tutor.plans")

FX_RATE_KEY = "usd_to_cad_3yr_avg"
FX_COMPUTED_KEY = "usd_to_cad_3yr_avg_computed_at"
BOC_URL = "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?recent=780"
FREE_PLAN = "free"


def get_plan(db: Session, code: str | None) -> Plan | None:
    return db.get(Plan, code) if code else None


def effective_plan(db: Session, parent: ParentProfile) -> Plan | None:
    return get_plan(db, parent.subscription_tier) or get_plan(db, FREE_PLAN)


def effective_seats(db: Session, parent: ParentProfile) -> int:
    if parent.max_students is not None:
        return parent.max_students
    plan = effective_plan(db, parent)
    return plan.max_students if plan is not None else 1


def effective_ai_daily_limit(db: Session, parent: ParentProfile) -> int | None:
    """Per-family override, then plan cap, then the global default."""
    if parent.ai_daily_limit is not None:
        return parent.ai_daily_limit
    plan = effective_plan(db, parent)
    if plan is not None:
        return plan.ai_daily_generations
    return settings.family_ai_daily_generations


def upgrade_target(db: Session, parent: ParentProfile) -> Plan | None:
    """Cheapest active plan with more seats than the family's effective limit."""
    seats = effective_seats(db, parent)
    return db.scalars(
        select(Plan)
        .where(Plan.active.is_(True), Plan.max_students > seats)
        .order_by(Plan.monthly_price_usd, Plan.max_students)
    ).first()


def cad_for_usd(db: Session, usd: Decimal) -> int:
    """Whole-dollar CAD at the stored 3-yr-average rate (cents dropped)."""
    rate, _computed_at = stored_fx_rate(db)
    return int((usd * rate).quantize(Decimal(1), rounding=ROUND_FLOOR))


def currency_for(country_code: str | None) -> str:
    return "CAD" if country_code == "CA" else "USD"


def localized_price(plan: Plan, country_code: str | None) -> dict:
    if currency_for(country_code) == "CAD":
        return {"currency": "CAD", "amount": str(plan.monthly_price_cad)}
    return {"currency": "USD", "amount": str(plan.monthly_price_usd)}


def stored_fx_rate(db: Session) -> tuple[Decimal, datetime | None]:
    rate_row = db.get(PlatformSetting, FX_RATE_KEY)
    computed_row = db.get(PlatformSetting, FX_COMPUTED_KEY)
    rate = Decimal(rate_row.value) if rate_row else settings.usd_to_cad_fallback
    computed_at = None
    if computed_row is not None:
        try:
            computed_at = datetime.fromisoformat(computed_row.value)
        except ValueError:
            computed_at = None
    return rate, computed_at


def fetch_boc_3yr_average() -> Decimal:
    """Average USD→CAD over ~3 years of business days from the Bank of
    Canada Valet API (free, no key)."""
    response = httpx.get(BOC_URL, timeout=settings.fx_fetch_timeout_seconds)
    response.raise_for_status()
    observations = response.json().get("observations") or []
    rates = [
        Decimal(obs["FXUSDCAD"]["v"])
        for obs in observations
        if obs.get("FXUSDCAD", {}).get("v") is not None
    ]
    if not rates:
        raise ValueError("Bank of Canada returned no USD/CAD observations")
    return (sum(rates) / Decimal(len(rates))).quantize(Decimal("0.0001"))


def recalculate_cad_prices(db: Session) -> dict:
    """Fetch the 3-year average, store it, and re-price every plan's CAD
    amount (cents dropped). Returns what changed for the audit log."""
    rate = fetch_boc_3yr_average()
    now = datetime.now(UTC)
    for key, value in ((FX_RATE_KEY, str(rate)), (FX_COMPUTED_KEY, now.isoformat())):
        row = db.get(PlatformSetting, key)
        if row is None:
            db.add(PlatformSetting(key=key, value=value, updated_at=now))
        else:
            row.value = value
            row.updated_at = now
    changed = []
    for plan in db.scalars(select(Plan)).all():
        cad = int((plan.monthly_price_usd * rate).quantize(Decimal(1), rounding=ROUND_FLOOR))
        if plan.monthly_price_cad != cad:
            changed.append({"code": plan.code, "before": plan.monthly_price_cad, "after": cad})
            plan.monthly_price_cad = cad
            plan.updated_at = now
    db.flush()
    return {"rate": str(rate), "computed_at": now.isoformat(), "plans": changed}
