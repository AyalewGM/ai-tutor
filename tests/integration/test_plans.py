"""Plan catalog, plan-driven seat/AI limits, and fixed CAD pricing."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.admin_models import AdminAuditEvent
from app.auth import SESSION_COOKIE, create_session
from app.core.database import SessionLocal
from app.main import app
from app.models import Student, User
from app.parent_models import ParentProfile
from app.plan_models import Plan, PlatformSetting
from app.services import plans as plan_service
from app.services.tutor_engine import TutorContext, tutor_engine
from app.services.usage_metering import check_ai_budget

client = TestClient(app)


class _OkProvider:
    model_name = "metered-model"
    provider_name = "metered"

    def generate(self, context: TutorContext) -> dict[str, object]:
        return {"message": "ok", "input_tokens": 10, "output_tokens": 5}


@pytest.fixture(autouse=True)
def _provider(monkeypatch):
    monkeypatch.setattr(tutor_engine, "provider", _OkProvider())
    yield
    client.cookies.clear()


def _family(
    *,
    tier: str = "free",
    max_students: int | None = None,
    ai_daily_limit: int | None = None,
    country_code: str | None = None,
) -> tuple[User, ParentProfile]:
    with SessionLocal() as db:
        user = User(email=f"fam-{uuid.uuid4().hex[:8]}@example.com", role="PARENT")
        db.add(user)
        db.flush()
        profile = ParentProfile(
            user_id=user.id,
            subscription_tier=tier,
            max_students=max_students,
            ai_daily_limit=ai_daily_limit,
            country_code=country_code,
        )
        db.add(profile)
        db.commit()
        db.refresh(user)
        db.refresh(profile)
        return user, profile


def _cleanup_users(*users: User) -> None:
    with SessionLocal() as db:
        for user in users:
            db.query(ParentProfile).filter(ParentProfile.user_id == user.id).delete()
            db.query(Student).filter(Student.parent_id == user.id).delete()
            db.query(User).filter(User.id == user.id).delete()
        db.commit()


def _staff_cookie() -> None:
    with SessionLocal() as db:
        user = User(email=f"admin-{uuid.uuid4().hex[:8]}@example.com", role="ADMIN")
        db.add(user)
        db.flush()
        token, session = create_session(db, user.id)
        session.mfa_verified_at = datetime.now(UTC)
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)


def test_seeded_plan_catalog():
    with SessionLocal() as db:
        plans = {p.code: p for p in db.scalars(select(Plan)).all()}
    assert {"free", "pro"} <= set(plans)
    free, pro = plans["free"], plans["pro"]
    assert (free.monthly_price_usd, free.monthly_price_cad, free.max_students) == (
        Decimal("0.00"),
        0,
        1,
    )
    assert (pro.monthly_price_usd, pro.monthly_price_cad, pro.max_students) == (
        Decimal("9.99"),
        13,
        5,
    )
    assert pro.ai_daily_generations > free.ai_daily_generations


def test_cad_price_is_whole_dollars_with_cents_dropped():
    # Stored fallback rate is 1.36: 9.99 * 1.36 = 13.5864 -> 13.
    with SessionLocal() as db:
        assert plan_service.cad_for_usd(db, Decimal("9.99")) == 13
        assert plan_service.cad_for_usd(db, Decimal("0.73")) == 0
        row = db.get(PlatformSetting, "usd_to_cad_3yr_avg")
        row.value = "1.5"
        db.flush()
        assert plan_service.cad_for_usd(db, Decimal("10.00")) == 15
        db.rollback()


def test_effective_seats_plan_default_and_override():
    user, profile = _family(tier="free", max_students=None)
    with SessionLocal() as db:
        assert plan_service.effective_seats(db, profile) == 1
        assert plan_service.upgrade_target(db, profile).code == "pro"
        profile.max_students = 3
        assert plan_service.effective_seats(db, profile) == 3
        assert plan_service.upgrade_target(db, profile) is not None
    _cleanup_users(user)


def test_effective_seats_override_larger_than_any_plan_has_no_upgrade():
    user, profile = _family(tier="pro", max_students=99)
    with SessionLocal() as db:
        assert plan_service.effective_seats(db, profile) == 99
        assert plan_service.upgrade_target(db, profile) is None
    _cleanup_users(user)


def test_plan_ai_limit_replaces_global_default_when_no_override():
    user, profile = _family(tier="free", ai_daily_limit=None)
    with SessionLocal() as db:
        # free plan's 50 differs from the global fallback; the plan wins.
        assert plan_service.effective_ai_daily_limit(db, profile) == 50
        profile.ai_daily_limit = 7
        assert plan_service.effective_ai_daily_limit(db, profile) == 7
    _cleanup_users(user)


def test_check_ai_budget_uses_plan_limit():
    with SessionLocal() as db:
        db.add(
            Plan(
                code="tiny-plan",
                name="Tiny",
                monthly_price_usd=Decimal("0.00"),
                monthly_price_cad=0,
                max_students=1,
                ai_daily_generations=0,
                active=True,
            )
        )
        db.commit()
    try:
        user, _profile = _family(tier="tiny-plan")
        with SessionLocal() as db:
            assert check_ai_budget(db, user.id) is False
        _cleanup_users(user)
    finally:
        with SessionLocal() as db:
            db.execute(delete(Plan).where(Plan.code == "tiny-plan"))
            db.commit()


def test_onboarding_plans_localizes_by_family_country():
    us_user, _p = _family(country_code="US")
    ca_user, _p2 = _family(country_code="CA")
    for user, currency, price in ((us_user, "USD", "9.99"), (ca_user, "CAD", "13")):
        with SessionLocal() as db:
            token, _session = create_session(db, user.id)
            db.commit()
        client.cookies.set(SESSION_COOKIE, token)
        resp = client.get("/api/v1/onboarding/plans")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["currency"] == currency
        pro = next(p for p in data["plans"] if p["code"] == "pro")
        assert pro["price"]["amount"] == price
        assert pro["price"]["currency"] == currency
        assert pro["max_students"] == 5
        client.cookies.clear()
    _cleanup_users(us_user, ca_user)


def test_admin_plans_requires_staff():
    assert client.get("/api/v1/admin/plans").status_code == 401
    _staff_cookie()
    resp = client.get("/api/v1/admin/plans")
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["usd_to_cad_rate"]) == Decimal("1.36")
    codes = {p["code"] for p in data["plans"]}
    assert {"free", "pro"} <= codes


def test_admin_plan_patch_rederives_cad_and_audits():
    _staff_cookie()
    before = client.get("/api/v1/admin/plans").json()
    pro_before = next(p for p in before["plans"] if p["code"] == "pro")
    try:
        resp = client.patch("/api/v1/admin/plans/pro", json={"monthly_price_usd": "20.00"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # 20.00 * 1.36 = 27.20 -> 27 whole CAD, no explicit CAD given.
        assert body["monthly_price_cad"] == 27
        with SessionLocal() as db:
            audit = db.scalar(
                select(AdminAuditEvent).where(
                    AdminAuditEvent.action == "PLAN_UPDATED",
                    AdminAuditEvent.target_id == "pro",
                )
            )
            assert audit is not None
            db.query(AdminAuditEvent).filter(AdminAuditEvent.id == audit.id).delete()
            db.commit()
        # Explicit CAD wins over derivation.
        resp = client.patch(
            "/api/v1/admin/plans/pro",
            json={"monthly_price_usd": "20.00", "monthly_price_cad": 31},
        )
        assert resp.json()["monthly_price_cad"] == 31
    finally:
        client.patch(
            "/api/v1/admin/plans/pro",
            json={
                "monthly_price_usd": pro_before["monthly_price_usd"],
                "monthly_price_cad": pro_before["monthly_price_cad"],
            },
        )
        client.cookies.clear()


def test_admin_recalc_cad_stores_rate_and_reprices(monkeypatch):
    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "observations": [
                    {"FXUSDCAD": {"v": "1.40"}},
                    {"FXUSDCAD": {"v": "1.30"}},
                    {"FXUSDCAD": {"v": None}},
                ]
            }

    monkeypatch.setattr(plan_service.httpx, "get", lambda *a, **k: _Resp())
    _staff_cookie()
    try:
        resp = client.post("/api/v1/admin/plans/recalc-cad")
        assert resp.status_code == 200, resp.text
        result = resp.json()
        # mean(1.40, 1.30) = 1.3500 -> pro CAD floor(9.99 * 1.35) = 13.
        assert Decimal(result["rate"]) == Decimal("1.3500")
        with SessionLocal() as db:
            row = db.get(PlatformSetting, "usd_to_cad_3yr_avg")
            assert row is not None and row.value == "1.3500"
            pro = db.get(Plan, "pro")
            assert pro.monthly_price_cad == 13
            audit = db.scalar(
                select(AdminAuditEvent).where(AdminAuditEvent.action == "PLAN_CAD_RECALCULATED")
            )
            assert audit is not None
    finally:
        with SessionLocal() as db:
            db.execute(
                delete(AdminAuditEvent).where(AdminAuditEvent.action == "PLAN_CAD_RECALCULATED")
            )
            row = db.get(PlatformSetting, "usd_to_cad_3yr_avg")
            if row is not None:
                row.value = "1.36"
            pro = db.get(Plan, "pro")
            if pro is not None:
                pro.monthly_price_cad = 13
            db.commit()
        client.cookies.clear()
