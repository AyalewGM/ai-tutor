"""Stripe billing endpoints: checkout, customer portal, subscription state,
and the signature-verified webhook that applies Stripe events locally."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.settings import settings
from app.identity import CurrentParent, DbSession
from app.models import User
from app.services.billing import (
    apply_webhook_event,
    construct_webhook_event,
    create_checkout_session,
    create_portal_session,
    price_for_plan,
    stripe_configured,
)
from app.services.plans import FREE_PLAN, get_plan

logger = logging.getLogger("ai_tutor.billing")

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutIn(BaseModel):
    plan_code: str


class UrlOut(BaseModel):
    url: str


class SubscriptionOut(BaseModel):
    tier: str
    status: str | None
    trial_ends_at: str | None
    can_manage: bool
    billing_enabled: bool


@router.get("/subscription", response_model=SubscriptionOut)
def subscription(parent: CurrentParent) -> SubscriptionOut:
    return SubscriptionOut(
        tier=parent.subscription_tier,
        status=parent.subscription_status,
        trial_ends_at=parent.trial_ends_at.isoformat() if parent.trial_ends_at else None,
        can_manage=bool(parent.stripe_customer_id),
        billing_enabled=stripe_configured(),
    )


@router.post("/checkout", response_model=UrlOut)
def checkout(payload: CheckoutIn, parent: CurrentParent, db: DbSession) -> UrlOut:
    if not stripe_configured():
        raise HTTPException(503, "Billing is not configured")
    plan = get_plan(db, payload.plan_code)
    if plan is None or not plan.active or plan.code == FREE_PLAN:
        raise HTTPException(404, "Plan not found")
    price_id = price_for_plan(plan, parent.country_code)
    if not price_id:
        raise HTTPException(503, "Plan is not configured for checkout")
    user = db.get(User, parent.user_id)
    url = create_checkout_session(parent, plan=plan, price_id=price_id, email=user.email)
    db.commit()
    return UrlOut(url=url)


@router.post("/portal", response_model=UrlOut)
def portal(parent: CurrentParent) -> UrlOut:
    if not stripe_configured():
        raise HTTPException(503, "Billing is not configured")
    if not parent.stripe_customer_id:
        raise HTTPException(404, "No billing account")
    return UrlOut(url=create_portal_session(parent))


@router.post("/webhook")
async def webhook(request: Request, db: DbSession) -> dict:
    if not settings.stripe_webhook_secret:
        raise HTTPException(503, "Billing is not configured")
    signature = request.headers.get("Stripe-Signature", "")
    payload = await request.body()
    try:
        event = construct_webhook_event(payload, signature)
    except Exception:  # noqa: BLE001 — any verification failure means unsigned
        raise HTTPException(400, "Invalid webhook signature") from None
    applied = apply_webhook_event(db, event)
    db.commit()
    return {"received": True, "applied": applied}
