import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import billing_api
from app.core.database import SessionLocal
from app.core.settings import settings
from app.main import app
from app.models import User
from app.parent_models import ParentProfile
from app.plan_models import Plan
from app.services import billing
from app.services.plans import FREE_PLAN

client = TestClient(app)


@pytest.fixture(autouse=True)
def _approved(monkeypatch):
    monkeypatch.setattr(settings, "require_family_approval", False)
    yield
    client.cookies.clear()


def _register(email: str | None = None) -> str:
    email = email or f"fam-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/v1/auth/register-parent",
        json={
            "email": email,
            "password": "correct-horse-battery",
            "display_name": "P",
            "parent_pin": "1234",
            "terms_accepted": True,
            "coppa_consent_given": True,
        },
    )
    assert response.status_code == 201, response.text
    return email


def _profile(email: str) -> ParentProfile:
    with SessionLocal() as db:
        return db.scalar(
            select(ParentProfile).join(User, User.id == ParentProfile.user_id).where(
                User.email == email
            )
        )


def test_subscription_defaults() -> None:
    _register()
    response = client.get("/api/v1/billing/subscription")
    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == FREE_PLAN
    assert body["status"] is None
    assert body["can_manage"] is False


def test_checkout_503_when_stripe_unconfigured(monkeypatch) -> None:
    _register()
    monkeypatch.setattr(settings, "stripe_secret_key", None)
    response = client.post("/api/v1/billing/checkout", json={"plan_code": "pro"})
    assert response.status_code == 503


def test_checkout_rejects_free_and_unknown_plans(monkeypatch) -> None:
    _register()
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_x")
    assert client.post("/api/v1/billing/checkout", json={"plan_code": FREE_PLAN}).status_code == 404
    assert client.post("/api/v1/billing/checkout", json={"plan_code": "nope"}).status_code == 404


def test_checkout_returns_url_and_picks_cad_price(monkeypatch) -> None:
    email = _register()
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_x")
    with SessionLocal() as db:
        profile = db.scalar(
            select(ParentProfile).join(User, User.id == ParentProfile.user_id).where(
                User.email == email
            )
        )
        profile.country_code = "CA"
        plan = db.get(Plan, "pro")
        plan.stripe_price_id_usd = "price_usd_1"
        plan.stripe_price_id_cad = "price_cad_1"
        db.commit()

    captured = {}

    def fake_checkout(profile, *, plan, price_id, email):
        captured["price_id"] = price_id
        captured["plan_code"] = plan.code
        return "https://checkout.stripe.com/session/1"

    monkeypatch.setattr(billing_api, "create_checkout_session", fake_checkout)
    response = client.post("/api/v1/billing/checkout", json={"plan_code": "pro"})
    assert response.status_code == 200
    assert response.json()["url"].startswith("https://checkout.stripe.com/")
    assert captured == {"price_id": "price_cad_1", "plan_code": "pro"}

    with SessionLocal() as db:
        plan = db.get(Plan, "pro")
        plan.stripe_price_id_usd = None
        plan.stripe_price_id_cad = None
        db.commit()


def test_portal_requires_existing_customer(monkeypatch) -> None:
    email = _register()
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_x")
    assert client.post("/api/v1/billing/portal").status_code == 404
    with SessionLocal() as db:
        profile = db.scalar(
            select(ParentProfile).join(User, User.id == ParentProfile.user_id).where(
                User.email == email
            )
        )
        profile.stripe_customer_id = f"cus_{uuid.uuid4().hex[:8]}"
        db.commit()
    monkeypatch.setattr(billing_api, "create_portal_session", lambda p: "https://portal")
    assert client.post("/api/v1/billing/portal").json()["url"] == "https://portal"


def test_webhook_rejects_bad_signature(monkeypatch) -> None:
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_x")
    monkeypatch.setattr(
        billing_api,
        "construct_webhook_event",
        lambda payload, sig: (_ for _ in ()).throw(ValueError("bad sig")),
    )
    assert client.post("/api/v1/billing/webhook", content=b"{}").status_code == 400


def test_webhook_checkout_and_subscription_lifecycle(monkeypatch) -> None:
    email = _register()
    profile = _profile(email)
    customer_id = f"cus_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_x")

    events = iter(
        [
            {
                "type": "checkout.session.completed",
                "data": {"object": {
                    "client_reference_id": str(profile.user_id),
                    "customer": customer_id,
                    "subscription": "sub_9",
                }},
            },
            {
                "type": "customer.subscription.updated",
                "data": {"object": {
                    "id": "sub_9",
                    "customer": customer_id,
                    "status": "trialing",
                    "trial_end": 1_900_000_000,
                    "metadata": {"plan_code": "pro"},
                }},
            },
            {
                "type": "customer.subscription.deleted",
                "data": {"object": {
                    "id": "sub_9",
                    "customer": customer_id,
                    "status": "canceled",
                }},
            },
        ]
    )
    monkeypatch.setattr(billing_api, "construct_webhook_event", lambda p, s: next(events))

    assert client.post("/api/v1/billing/webhook", content=b"{}").json()["applied"] is True
    refreshed = _profile(email)
    assert refreshed.stripe_customer_id == customer_id
    assert refreshed.stripe_subscription_id == "sub_9"

    assert client.post("/api/v1/billing/webhook", content=b"{}").json()["applied"] is True
    refreshed = _profile(email)
    assert refreshed.subscription_tier == "pro"
    assert refreshed.subscription_status == "trialing"
    assert refreshed.trial_ends_at is not None

    assert client.post("/api/v1/billing/webhook", content=b"{}").json()["applied"] is True
    refreshed = _profile(email)
    assert refreshed.subscription_tier == FREE_PLAN
    assert refreshed.subscription_status == "canceled"


def test_webhook_ignores_unknown_event_and_customer(monkeypatch) -> None:
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_x")
    events = iter(
        [
            {"type": "invoice.paid", "data": {"object": {}}},
            {
                "type": "customer.subscription.updated",
                "data": {"object": {"id": "sub_x", "customer": "cus_unknown", "status": "active"}},
            },
        ]
    )
    monkeypatch.setattr(billing_api, "construct_webhook_event", lambda p, s: next(events))
    assert client.post("/api/v1/billing/webhook", content=b"{}").json() == {
        "received": True, "applied": False,
    }
    assert client.post("/api/v1/billing/webhook", content=b"{}").json() == {
        "received": True, "applied": False,
    }


def test_price_for_plan_prefers_cad_for_canada() -> None:
    plan = Plan(
        code="x", name="X", monthly_price_usd="9.99", monthly_price_cad=13,
        max_students=5, ai_daily_generations=300,
        stripe_price_id_usd="p_us", stripe_price_id_cad="p_ca",
    )
    assert billing.price_for_plan(plan, "CA") == "p_ca"
    assert billing.price_for_plan(plan, "US") == "p_us"
    plan.stripe_price_id_cad = None
    assert billing.price_for_plan(plan, "CA") == "p_us"
