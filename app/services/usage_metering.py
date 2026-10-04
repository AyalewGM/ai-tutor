"""AI usage metering: ledger writes, cost rates, and budget enforcement.

Application-owned decisions: the engine is asked for language only after the
budget check passes. A denied call silently falls back to the built-in
deterministic messages, so learning continues and only AI wording stops.

Windows are UTC calendar day (family limits) and UTC calendar month (the
global spend cap) — documented so families and ops read the same clock.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admin_models import AdminAuditEvent
from app.core.settings import settings
from app.parent_models import ParentProfile
from app.usage_models import AiModelRate, AiUsageEvent

if TYPE_CHECKING:
    from app.models import Student
    from app.services.tutor_engine import TutorEngineResult

logger = logging.getLogger("ai_tutor.usage")

# USD per million tokens (input, output). Published-list approximations for
# the models this deployment can select; ai_model_rates rows override, and
# _FALLBACK_RATE covers unknown models so a missing price never means free.
DEFAULT_RATES: dict[tuple[str, str], tuple[Decimal, Decimal]] = {
    ("openai", "gpt-5"): (Decimal("1.25"), Decimal("10.00")),
    ("openai", "gpt-5-mini"): (Decimal("0.25"), Decimal("2.00")),
    ("openai", "gpt-4o-mini"): (Decimal("0.15"), Decimal("0.60")),
    ("gemini", "gemini-3.8-flash"): (Decimal("0.30"), Decimal("2.50")),
    ("gemini", "gemini-2.5-flash"): (Decimal("0.30"), Decimal("2.50")),
}
_FALLBACK_RATE = (Decimal("1.00"), Decimal("4.00"))

# Conservative estimate when a provider omits token counts (the gateway's
# /v1/render may not report usage): ~a tutor prompt plus a short message.
_ESTIMATED_TOKENS = (1_500, 300)


def _month_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _day_start(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def rate_for(db: Session, provider: str | None, model: str | None) -> tuple[Decimal, Decimal]:
    if provider and model:
        row = db.get(AiModelRate, (provider, model))
        if row is not None:
            return row.input_usd_per_1m, row.output_usd_per_1m
    return DEFAULT_RATES.get((provider or "", model or ""), _FALLBACK_RATE)


def estimate_cost(
    db: Session,
    *,
    provider: str | None,
    model: str | None,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    in_rate, out_rate = rate_for(db, provider, model)
    cost = (Decimal(input_tokens) * in_rate + Decimal(output_tokens) * out_rate) / Decimal(1_000_000)
    return cost.quantize(Decimal("0.000001"))


def monthly_spend_usd(db: Session, now: datetime | None = None) -> Decimal:
    now = now or datetime.now(UTC)
    return db.scalar(
        select(func.coalesce(func.sum(AiUsageEvent.estimated_cost_usd), 0)).where(
            AiUsageEvent.created_at >= _month_start(now)
        )
    ) or Decimal(0)


def _family_daily_count(db: Session, family_user_id, now: datetime) -> int:
    return db.scalar(
        select(func.count(AiUsageEvent.id)).where(
            AiUsageEvent.family_user_id == family_user_id,
            AiUsageEvent.created_at >= _day_start(now),
            AiUsageEvent.source == "llm",
        )
    ) or 0


def _family_limit(db: Session, family_user_id) -> int | None:
    profile = db.scalar(
        select(ParentProfile).where(ParentProfile.user_id == family_user_id)
    )
    if profile is not None:
        from app.services.plans import effective_ai_daily_limit

        return effective_ai_daily_limit(db, profile)
    return settings.family_ai_daily_generations


def check_ai_budget(db: Session, family_user_id, *, now: datetime | None = None) -> bool:
    """True when another AI generation may be billed."""
    if not settings.ai_budgets_enabled:
        return True
    now = now or datetime.now(UTC)
    if monthly_spend_usd(db, now) >= settings.ai_monthly_cost_cap_usd:
        return False
    if family_user_id is not None:
        limit = _family_limit(db, family_user_id)
        if limit is not None and _family_daily_count(db, family_user_id, now) >= limit:
            return False
    return True


def _maybe_send_budget_alert(db: Session, before: Decimal, after: Decimal) -> None:
    cap = settings.ai_monthly_cost_cap_usd
    threshold = cap * Decimal(str(settings.ai_budget_alert_pct))
    if cap <= 0 or not (before < threshold <= after):
        return
    now = datetime.now(UTC)
    month_key = now.strftime("%Y-%m")
    already = db.scalar(
        select(AdminAuditEvent.id).where(
            AdminAuditEvent.action == "AI_BUDGET_ALERT",
            AdminAuditEvent.target_id == month_key,
        )
    )
    if already is not None:
        return
    db.add(
        AdminAuditEvent(
            actor_user_id=None,
            actor_label="usage-metering",
            action="AI_BUDGET_ALERT",
            target_type="ai_budget",
            target_id=month_key,
            after_json={"spend_usd": str(after), "cap_usd": str(cap), "threshold_pct": settings.ai_budget_alert_pct},
        )
    )
    if settings.admin_notification_email:
        from app.services.email import OutboundEmail, send_email

        send_email(
            OutboundEmail(
                to=settings.admin_notification_email,
                subject=f"Mihur AI spend at {settings.ai_budget_alert_pct:.0%} of monthly cap",
                body=(
                    f"Estimated AI spend for {month_key} reached ${after:.4f} of the "
                    f"${cap:.2f} monthly cap. Beyond ${cap:.2f}, tutor messages fall "
                    "back to built-in text until next month."
                ),
            )
        )


def record_ai_usage(
    db: Session,
    *,
    family_user_id,
    student_id,
    session_id,
    action: str,
    result: TutorEngineResult,
) -> AiUsageEvent:
    """Ledger row for one generation, plus the 80%-of-cap admin alert."""
    if result.source == "llm":
        estimated = result.input_tokens is None
        in_toks = result.input_tokens if not estimated else _ESTIMATED_TOKENS[0]
        out_toks = result.output_tokens if not estimated else _ESTIMATED_TOKENS[1]
        cost = estimate_cost(
            db, provider=result.provider, model=result.model,
            input_tokens=in_toks, output_tokens=out_toks,
        )
    else:
        estimated = False
        in_toks = out_toks = None
        cost = Decimal(0)

    before = monthly_spend_usd(db)
    event = AiUsageEvent(
        family_user_id=family_user_id,
        student_id=student_id,
        session_id=session_id,
        action=action,
        provider=result.provider,
        model=result.model,
        source=result.source,
        input_tokens=in_toks,
        output_tokens=out_toks,
        tokens_estimated=estimated,
        estimated_cost_usd=cost,
    )
    db.add(event)
    db.flush()
    if event.source == "llm":
        _maybe_send_budget_alert(db, before, before + cost)
    return event


def record_budget_denial(
    db: Session, *, family_user_id, student_id, session_id, action: str
) -> AiUsageEvent:
    """Ledger row marking a refused call — feeds 'families hitting limits'."""
    event = AiUsageEvent(
        family_user_id=family_user_id,
        student_id=student_id,
        session_id=session_id,
        action=action,
        source="budget_denied",
        estimated_cost_usd=Decimal(0),
    )
    db.add(event)
    db.flush()
    return event


def ai_generate(
    db: Session,
    context,
    *,
    student: Student | None,
    session_id=None,
    action: str = "",
    use_llm: bool = True,
) -> TutorEngineResult:
    """One entry point for every tutor generation: budget check, call, ledger.

    ``use_llm`` keeps each call site's own rule (e.g. no model call for
    correct-answer feedback); the budget check only ever *narrows* it.
    """
    from app.services.tutor_engine import tutor_engine

    family_user_id = student.parent_id if student is not None else None
    allowed = use_llm and check_ai_budget(db, family_user_id)
    if use_llm and not allowed:
        record_budget_denial(
            db, family_user_id=family_user_id, student_id=getattr(student, "id", None),
            session_id=session_id, action=action,
        )
    result = tutor_engine.generate(context, use_llm=allowed)
    if result.source == "llm":
        record_ai_usage(
            db,
            family_user_id=family_user_id,
            student_id=getattr(student, "id", None),
            session_id=session_id,
            action=action,
            result=result,
        )
    return result


@dataclass(frozen=True)
class FamilyUsage:
    family_user_id: object
    generations: int
    denied: int
    spend_usd: Decimal


def usage_summary(db: Session, now: datetime | None = None) -> dict:
    """Month-to-date totals for the admin AI-usage tab."""
    now = now or datetime.now(UTC)
    month = _month_start(now)
    totals = db.execute(
        select(
            func.count(AiUsageEvent.id).filter(AiUsageEvent.source == "llm"),
            func.count(AiUsageEvent.id).filter(AiUsageEvent.source == "budget_denied"),
            func.coalesce(func.sum(AiUsageEvent.estimated_cost_usd), 0),
        ).where(AiUsageEvent.created_at >= month)
    ).one()
    families = db.execute(
        select(
            AiUsageEvent.family_user_id,
            func.count(AiUsageEvent.id).filter(AiUsageEvent.source == "llm"),
            func.count(AiUsageEvent.id).filter(AiUsageEvent.source == "budget_denied"),
            func.coalesce(func.sum(AiUsageEvent.estimated_cost_usd), 0),
        )
        .where(AiUsageEvent.created_at >= month)
        .group_by(AiUsageEvent.family_user_id)
        .order_by(func.coalesce(func.sum(AiUsageEvent.estimated_cost_usd), 0).desc())
        .limit(50)
    ).all()
    return {
        "month": month.strftime("%Y-%m"),
        "generations": int(totals[0]),
        "denied": int(totals[1]),
        "spend_usd": str(totals[2]),
        "cap_usd": str(settings.ai_monthly_cost_cap_usd),
        "families": [
            {
                "family_user_id": str(row[0]) if row[0] else None,
                "generations": int(row[1]),
                "denied": int(row[2]),
                "spend_usd": str(row[3]),
            }
            for row in families
        ],
    }
