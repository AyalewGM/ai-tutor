"""Stripe billing: checkout, portal, and webhook-applied subscription state.

Application-owned state lives on ParentProfile (subscription_tier is the
effective plan code; subscription_status mirrors Stripe). Stripe owns the
money. All Stripe calls are thin functions so tests can monkeypatch them —
no Stripe objects cross into the rest of the app.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin_models import AdminAuditEvent
from app.core.settings import settings
from app.parent_models import ParentProfile
from app.plan_models import Plan
from app.services.plans import FREE_PLAN

logger = logging.getLogger("ai_tutor.billing")

# Statuses that keep the paid plan's benefits. Anything else resolves to free.
_PAID_STATUSES = {"trialing", "active", "past_due"}


def stripe_configured() -> bool:
    return bool(settings.stripe_secret_key)


def _client():
    if not settings.stripe_secret_key:
        raise RuntimeError("Stripe is not configured")
    import stripe

    stripe.api_key = settings.stripe_secret_key
    return stripe


def price_for_plan(plan: Plan, country_code: str | None) -> str | None:
    """Canadian families pay the fixed CAD price when one is configured."""
    if country_code == "CA" and plan.stripe_price_id_cad:
        return plan.stripe_price_id_cad
    return plan.stripe_price_id_usd


def create_checkout_session(
    profile: ParentProfile, *, plan: Plan, price_id: str, email: str
) -> str:
    stripe = _client()
    base = settings.public_base_url.rstrip("/")
    session = stripe.checkout.Session.create(
        mode="subscription",
        client_reference_id=str(profile.user_id),
        customer=profile.stripe_customer_id,
        customer_email=None if profile.stripe_customer_id else email,
        line_items=[{"price": price_id, "quantity": 1}],
        # Card-required trial: Stripe collects a payment method up front and
        # only charges when the trial lapses.
        payment_method_collection="always",
        subscription_data={
            "trial_period_days": settings.stripe_trial_days,
            "metadata": {"plan_code": plan.code, "family_user_id": str(profile.user_id)},
        },
        success_url=f"{base}/billing?status=success",
        cancel_url=f"{base}/billing?status=cancel",
    )
    return session.url


def create_portal_session(profile: ParentProfile) -> str:
    stripe = _client()
    session = stripe.billing_portal.Session.create(
        customer=profile.stripe_customer_id,
        return_url=f"{settings.public_base_url.rstrip('/')}/billing",
    )
    return session.url


def construct_webhook_event(payload: bytes, signature: str) -> Any:
    stripe = _client()
    return stripe.Webhook.construct_event(
        payload, signature, settings.stripe_webhook_secret
    )


def _profile_by_customer(db: Session, customer_id: str | None) -> ParentProfile | None:
    if not customer_id:
        return None
    return db.scalar(
        select(ParentProfile).where(ParentProfile.stripe_customer_id == customer_id)
    )


def _profile_by_user_id(db: Session, user_id: str | None) -> ParentProfile | None:
    if not user_id:
        return None
    try:
        import uuid

        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        return None
    return db.scalar(select(ParentProfile).where(ParentProfile.user_id == uid))


def _audit(db: Session, profile: ParentProfile, action: str, before: dict, after: dict) -> None:
    db.add(
        AdminAuditEvent(
            actor_user_id=None,
            actor_label="stripe-webhook",
            action=action,
            target_type="subscription",
            target_id=str(profile.user_id),
            before_json=before,
            after_json=after,
        )
    )


def _trial_end(value: int | None) -> datetime | None:
    return datetime.fromtimestamp(value, UTC) if value else None


def apply_webhook_event(db: Session, event: Any) -> bool:
    """Apply one Stripe event to the local subscription mirror. Returns True
    when the event mutated state; unknown event types are ignored so Stripe
    stops retrying them."""
    etype = event.get("type") if isinstance(event, dict) else getattr(event, "type", None)
    obj = (
        event.get("data", {}).get("object", {})
        if isinstance(event, dict)
        else getattr(event.data, "object", {})
    )
    get = obj.get if isinstance(obj, dict) else lambda k, d=None: getattr(obj, k, d)

    if etype == "checkout.session.completed":
        profile = _profile_by_user_id(db, get("client_reference_id"))
        if profile is None:
            logger.warning("checkout.session.completed for unknown user %s", get("client_reference_id"))
            return False
        profile.stripe_customer_id = get("customer") or profile.stripe_customer_id
        profile.stripe_subscription_id = get("subscription") or profile.stripe_subscription_id
        return True

    if etype in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
        profile = _profile_by_customer(db, get("customer"))
        if profile is None:
            metadata = get("metadata") or {}
            profile = _profile_by_user_id(db, metadata.get("family_user_id"))
        if profile is None:
            logger.warning("subscription event for unknown customer %s", get("customer"))
            return False
        before = {
            "tier": profile.subscription_tier,
            "status": profile.subscription_status,
        }
        metadata = get("metadata") or {}
        plan_code = metadata.get("plan_code")
        status = get("status")
        profile.stripe_subscription_id = get("id") or profile.stripe_subscription_id
        profile.subscription_status = status
        profile.trial_ends_at = _trial_end(get("trial_end"))
        if etype == "customer.subscription.deleted" or status not in _PAID_STATUSES:
            profile.subscription_tier = FREE_PLAN
        elif plan_code:
            profile.subscription_tier = plan_code
        _audit(
            db,
            profile,
            etype.upper().replace(".", "_"),
            before=before,
            after={"tier": profile.subscription_tier, "status": status},
        )
        return True

    return False
