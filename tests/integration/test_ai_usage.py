"""AI usage ledger, rate lookup, and budget enforcement."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.admin_models import AdminAuditEvent
from app.auth import SESSION_COOKIE, create_session
from app.core.database import SessionLocal
from app.core.settings import settings
from app.main import app
from app.models import Student, User
from app.parent_models import ParentProfile
from app.services.tutor_engine import TutorContext, tutor_engine
from app.services.usage_metering import (
    ai_generate,
    check_ai_budget,
    estimate_cost,
)
from app.usage_models import AiModelRate, AiUsageEvent

client = TestClient(app)


class TokenProvider:
    model_name = "metered-model"
    provider_name = "metered"

    def __init__(self, in_toks=1000, out_toks=200):
        self._usage = (in_toks, out_toks)

    def generate(self, context: TutorContext) -> dict[str, object]:
        return {
            "message": "Metered tutor message.",
            "input_tokens": self._usage[0],
            "output_tokens": self._usage[1],
        }


class SilentProvider:
    model_name = "silent-model"
    provider_name = "silent"

    def generate(self, context: TutorContext) -> dict[str, object]:
        return {"message": "No usage reported."}


@pytest.fixture(autouse=True)
def _provider(monkeypatch):
    monkeypatch.setattr(tutor_engine, "provider", TokenProvider())
    yield
    client.cookies.clear()


def _ctx() -> TutorContext:
    return TutorContext(
        grade_level="8",
        curriculum_name="Test Curriculum",
        state="GUIDED_PRACTICE",
        skill_name="Test Skill",
        action="GIVE_HINT",
        hint_level=2,
        problem_prompt="3(x+4)",
    )


def _family() -> tuple[User, Student]:
    with SessionLocal() as db:
        user = User(email=f"fam-{uuid.uuid4().hex[:8]}@example.com", role="PARENT")
        db.add(user)
        db.flush()
        db.add(ParentProfile(user_id=user.id))
        student = Student(parent_id=user.id, first_name="L", grade_level="8")
        db.add(student)
        db.commit()
        db.refresh(user)
        db.refresh(student)
        return user, student


def _cleanup(*families):
    with SessionLocal() as db:
        for user, student in families:
            db.query(AiUsageEvent).filter(AiUsageEvent.family_user_id == user.id).delete()
            db.query(Student).filter(Student.id == student.id).delete()
            db.query(ParentProfile).filter(ParentProfile.user_id == user.id).delete()
            db.query(User).filter(User.id == user.id).delete()
        db.commit()


def test_generation_writes_ledger_row_with_reported_tokens():
    user, student = _family()
    with SessionLocal() as db:
        result = ai_generate(db, _ctx(), student=student, session_id=None, action="GIVE_HINT")
        db.commit()
    assert result.source == "llm"
    with SessionLocal() as db:
        event = db.scalar(
            select(AiUsageEvent).where(AiUsageEvent.family_user_id == user.id)
        )
        assert event is not None
        assert event.source == "llm"
        assert event.provider == "metered" and event.model == "metered-model"
        assert event.input_tokens == 1000 and event.output_tokens == 200
        assert event.tokens_estimated is False
        assert event.estimated_cost_usd > 0
    _cleanup((user, student))


def test_missing_token_usage_is_estimated_and_flagged():
    user, student = _family()
    tutor_engine.provider = SilentProvider()
    with SessionLocal() as db:
        result = ai_generate(db, _ctx(), student=student, session_id=None, action="GIVE_HINT")
        db.commit()
    assert result.source == "llm" and result.input_tokens is None
    with SessionLocal() as db:
        event = db.scalar(
            select(AiUsageEvent).where(AiUsageEvent.family_user_id == user.id)
        )
        assert event.tokens_estimated is True
        assert event.input_tokens == 1500 and event.output_tokens == 300
    tutor_engine.provider = TokenProvider()
    _cleanup((user, student))


def test_db_rate_row_overrides_default_and_unknown_models_fallback():
    with SessionLocal() as db:
        db.add(
            AiModelRate(
                provider="metered",
                model="metered-model",
                input_usd_per_1m=Decimal("2.00"),
                output_usd_per_1m=Decimal("6.00"),
            )
        )
        db.commit()
        cost = estimate_cost(
            db, provider="metered", model="metered-model",
            input_tokens=1_000_000, output_tokens=1_000_000,
        )
        assert cost == Decimal("8.000000")
        unknown = estimate_cost(
            db, provider="x", model="y", input_tokens=1_000_000, output_tokens=1_000_000
        )
        assert unknown == Decimal("5.000000")  # fallback 1.00 + 4.00
        db.query(AiModelRate).filter(
            AiModelRate.provider == "metered", AiModelRate.model == "metered-model"
        ).delete()
        db.commit()


def test_family_daily_limit_denies_and_ledgers_denial(monkeypatch):
    user, student = _family()
    monkeypatch.setattr(settings, "family_ai_daily_generations", 2)
    db = SessionLocal()
    ai_generate(db, _ctx(), student=student, action="GIVE_HINT")
    ai_generate(db, _ctx(), student=student, action="GIVE_HINT")
    denied = ai_generate(db, _ctx(), student=student, action="GIVE_HINT")
    db.commit()
    assert denied.source == "fallback"
    with SessionLocal() as check:
        assert check.scalar(
            select(func.count(AiUsageEvent.id)).where(
                AiUsageEvent.family_user_id == user.id,
                AiUsageEvent.source == "llm",
            )
        ) == 2
        assert check.scalar(
            select(func.count(AiUsageEvent.id)).where(
                AiUsageEvent.family_user_id == user.id,
                AiUsageEvent.source == "budget_denied",
            )
        ) == 1
    db.close()
    _cleanup((user, student))


def test_per_family_override_wins_over_default(monkeypatch):
    user, student = _family()
    monkeypatch.setattr(settings, "family_ai_daily_generations", 1)
    with SessionLocal() as db:
        profile = db.scalar(select(ParentProfile).where(ParentProfile.user_id == user.id))
        profile.ai_daily_limit = 5
        db.commit()
        assert check_ai_budget(db, user.id) is True
    with SessionLocal() as db:
        profile = db.scalar(select(ParentProfile).where(ParentProfile.user_id == user.id))
        profile.ai_daily_limit = 0
        db.commit()
        assert check_ai_budget(db, user.id) is False
    _cleanup((user, student))


def test_global_monthly_cap_denies_everyone(monkeypatch):
    user, student = _family()
    monkeypatch.setattr(settings, "ai_monthly_cost_cap_usd", Decimal(0))
    with SessionLocal() as db:
        assert check_ai_budget(db, user.id) is False
        assert check_ai_budget(db, None) is False
    _cleanup((user, student))


def test_disabled_budgets_allow_everything(monkeypatch):
    monkeypatch.setattr(settings, "ai_budgets_enabled", False)
    monkeypatch.setattr(settings, "ai_monthly_cost_cap_usd", Decimal(0))
    with SessionLocal() as db:
        assert check_ai_budget(db, uuid.uuid4()) is True


def test_eighty_percent_alert_emails_and_audits_once(monkeypatch):
    user, student = _family()
    sent: list = []
    tutor_engine.provider = TokenProvider(in_toks=100_000, out_toks=10_000)
    monkeypatch.setattr(settings, "admin_notification_email", "admin@example.com")
    monkeypatch.setattr(settings, "ai_monthly_cost_cap_usd", Decimal("0.01"))
    monkeypatch.setattr(settings, "ai_budget_alert_pct", 0.5)
    from app.services.email import OutboundEmail

    def capture(msg: OutboundEmail) -> bool:
        sent.append(msg.subject)
        return True

    monkeypatch.setattr("app.services.email.send_email", capture)
    db = SessionLocal()
    ai_generate(db, _ctx(), student=student, action="GIVE_HINT")
    db.commit()
    month_key = datetime.now(UTC).strftime("%Y-%m")
    assert sent, "expected a budget alert email"
    with SessionLocal() as check:
        alerts = check.scalars(
            select(AdminAuditEvent).where(
                AdminAuditEvent.action == "AI_BUDGET_ALERT",
                AdminAuditEvent.target_id == month_key,
            )
        ).all()
        assert len(alerts) == 1
    # A second generation must not re-alert.
    ai_generate(db, _ctx(), student=student, action="GIVE_HINT")
    db.commit()
    assert len(sent) == 1
    db.close()
    with SessionLocal() as db2:
        db2.query(AdminAuditEvent).filter(
            AdminAuditEvent.action == "AI_BUDGET_ALERT",
            AdminAuditEvent.target_id == month_key,
        ).delete()
        db2.commit()
    _cleanup((user, student))


def _staff_cookie() -> None:
    with SessionLocal() as db:
        user = User(email=f"admin-{uuid.uuid4().hex[:8]}@example.com", role="ADMIN")
        db.add(user)
        db.flush()
        token, session = create_session(db, user.id)
        session.mfa_verified_at = datetime.now(UTC)
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)


def test_ai_usage_summary_requires_staff(monkeypatch):
    assert client.get("/api/v1/admin/ai-usage/summary").status_code == 401
    with SessionLocal() as db:
        user = User(email=f"par-{uuid.uuid4().hex[:8]}@example.com", role="PARENT")
        db.add(user)
        db.flush()
        token, _ = create_session(db, user.id)
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get("/api/v1/admin/ai-usage/summary").status_code == 404


def test_ai_usage_summary_and_family_limit_admin_flow():
    user, student = _family()
    with SessionLocal() as db:
        ai_generate(db, _ctx(), student=student, action="GIVE_HINT")
        db.commit()
    _staff_cookie()
    resp = client.get("/api/v1/admin/ai-usage/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["generations"] >= 1
    fam = next(f for f in data["families"] if f["family_user_id"] == str(user.id))
    assert fam["generations"] == 1 and Decimal(fam["spend_usd"]) > 0
    with SessionLocal() as db:
        profile = db.scalar(select(ParentProfile).where(ParentProfile.user_id == user.id))
        pid = str(profile.id)
    patch = client.patch(
        f"/api/v1/admin/families/{pid}/ai-limit", json={"daily_limit": 25}
    )
    assert patch.status_code == 200
    with SessionLocal() as db:
        profile = db.scalar(select(ParentProfile).where(ParentProfile.user_id == user.id))
        assert profile.ai_daily_limit == 25
        audit = db.scalar(
            select(AdminAuditEvent).where(
                AdminAuditEvent.action == "FAMILY_AI_LIMIT_SET",
                AdminAuditEvent.target_id == pid,
            )
        )
        assert audit is not None
        db.query(AdminAuditEvent).filter(AdminAuditEvent.id == audit.id).delete()
        db.commit()
    _cleanup((user, student))
