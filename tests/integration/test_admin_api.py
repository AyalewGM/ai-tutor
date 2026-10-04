import uuid
from datetime import UTC, datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import admin_api
from app.admin_models import AdminAuditEvent, AdminMfa
from app.auth import SESSION_COOKIE, create_session
from app.core.database import SessionLocal
from app.core.settings import settings
from app.main import app
from app.models import User
from app.parent_models import ParentProfile
from app.services import totp

client = TestClient(app)


@pytest.fixture(autouse=True)
def _mfa_env(monkeypatch):
    monkeypatch.setattr(settings, "mfa_encryption_key", Fernet.generate_key().decode())
    # No Redis in CI; the limiter is exercised separately.
    monkeypatch.setattr(admin_api, "register_mfa_attempt", lambda _user_id: None)
    monkeypatch.setattr(admin_api, "clear_mfa_attempts", lambda _user_id: None)
    yield
    client.cookies.clear()


def _user(role: str, *, parent: bool = False) -> str:
    """Create a user and return a fresh session token."""
    with SessionLocal() as db:
        user = User(email=f"{role.lower()}-{uuid.uuid4().hex[:8]}@example.test", role=role)
        db.add(user)
        db.flush()
        if parent:
            db.add(ParentProfile(user_id=user.id))
        token, _ = create_session(db, user.id)
        db.commit()
        return token


def _new_session_for(email: str) -> str:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        token, _ = create_session(db, user.id)
        db.commit()
        return token


def _secret_for(email: str) -> str:
    from app.services.admin_security import decrypt_secret

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        return decrypt_secret(db.get(AdminMfa, user.id).secret_encrypted)


def test_admin_routes_are_hidden_from_families_and_anonymous() -> None:
    assert client.get("/api/v1/admin/me").status_code == 401
    client.cookies.set(SESSION_COOKIE, _user("PARENT", parent=True))
    for method, path in [
        ("get", "/api/v1/admin/me"),
        ("get", "/api/v1/admin/audit-log"),
        ("post", "/api/v1/admin/mfa/setup"),
    ]:
        assert getattr(client, method)(path).status_code == 404, path


def test_full_enrollment_then_mfa_gates_data_routes() -> None:
    client.cookies.set(SESSION_COOKIE, _user("ADMIN"))
    me = client.get("/api/v1/admin/me").json()
    assert me["mfa_enrolled"] is False and me["mfa_verified"] is False
    assert "admin.audit.read" in me["permissions"]

    # Data routes refuse an unverified session.
    blocked = client.get("/api/v1/admin/audit-log")
    assert blocked.status_code == 403 and blocked.json()["detail"] == "MFA_REQUIRED"

    setup = client.post("/api/v1/admin/mfa/setup")
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    assert setup.json()["otpauth_uri"].startswith("otpauth://totp/")
    # Stored encrypted, never as the plain secret.
    email = me["email"]
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert secret not in db.get(AdminMfa, user.id).secret_encrypted

    assert client.post("/api/v1/admin/mfa/confirm", json={"code": "000000"}).status_code == 401
    code = totp._code_at(secret, totp.current_step())
    confirmed = client.post("/api/v1/admin/mfa/confirm", json={"code": code})
    assert confirmed.status_code == 200 and confirmed.json()["mfa_verified"] is True

    log = client.get("/api/v1/admin/audit-log")
    assert log.status_code == 200
    assert {"mfa.setup_started", "mfa.enabled"} <= {e["action"] for e in log.json()}

    # An active factor can't be silently replaced through the API.
    assert client.post("/api/v1/admin/mfa/setup").status_code == 409

    # A new sign-in starts unverified and the used code can't be replayed.
    client.cookies.set(SESSION_COOKIE, _new_session_for(email))
    assert client.get("/api/v1/admin/audit-log").status_code == 403
    assert client.post("/api/v1/admin/mfa/verify", json={"code": code}).status_code == 401
    next_code = totp._code_at(_secret_for(email), totp.current_step() + 1)
    verified = client.post("/api/v1/admin/mfa/verify", json={"code": next_code})
    assert verified.status_code == 200
    assert client.get("/api/v1/admin/audit-log").status_code == 200


def test_setup_fails_closed_without_encryption_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "mfa_encryption_key", None)
    client.cookies.set(SESSION_COOKIE, _user("ADMIN"))
    assert client.post("/api/v1/admin/mfa/setup").status_code == 503


def test_revoked_staff_lose_access() -> None:
    client.cookies.set(SESSION_COOKIE, _user("STAFF_REVOKED"))
    assert client.get("/api/v1/admin/me").status_code == 404


def test_make_admin_refuses_family_accounts_and_audits_grants(monkeypatch) -> None:
    from scripts.ops import make_admin

    with SessionLocal() as db:
        parent = User(email=f"family-{uuid.uuid4().hex[:8]}@example.test", role="PARENT")
        db.add(parent)
        db.flush()
        db.add(ParentProfile(user_id=parent.id))
        staff = User(email=f"staff-{uuid.uuid4().hex[:8]}@example.test", role="PARENT")
        db.add(staff)
        db.commit()
        parent_email, staff_email, staff_id = parent.email, staff.email, staff.id

    with pytest.raises(SystemExit):
        make_admin.grant(parent_email)

    make_admin.grant(staff_email)
    with SessionLocal() as db:
        assert db.get(User, staff_id).role == "ADMIN"
        event = db.scalar(
            select(AdminAuditEvent).where(
                AdminAuditEvent.target_id == str(staff_id),
                AdminAuditEvent.action == "staff.role_granted",
            )
        )
        assert event is not None and event.actor_label == "operator-cli"

    make_admin.revoke(staff_email)
    with SessionLocal() as db:
        assert db.get(User, staff_id).role == "STAFF_REVOKED"


def _mfa_verified_staff(role: str) -> str:
    with SessionLocal() as db:
        user = User(email=f"{role.lower()}-{uuid.uuid4().hex[:8]}@example.test", role=role)
        db.add(user)
        db.flush()
        token, session = create_session(db, user.id)
        session.mfa_verified_at = datetime.now(UTC)
        db.commit()
        return token


def test_support_role_scoped_to_family_approval() -> None:
    client.cookies.set(SESSION_COOKIE, _mfa_verified_staff("SUPPORT"))
    me = client.get("/api/v1/admin/me")
    assert me.status_code == 200 and me.json()["role"] == "SUPPORT"
    assert set(me.json()["permissions"]) == {
        "admin.access", "admin.families.read", "admin.families.approve",
    }
    assert client.get("/api/v1/admin/families").status_code == 200
    # Every other surface is a 404 (undiscoverable), not a 403.
    assert client.get("/api/v1/admin/metrics/overview").status_code == 404
    assert client.get("/api/v1/admin/ai-usage/summary").status_code == 404
    assert client.get("/api/v1/admin/plans").status_code == 404
    assert client.get("/api/v1/admin/audit-log").status_code == 404


def test_analyst_role_read_only_reporting() -> None:
    client.cookies.set(SESSION_COOKIE, _mfa_verified_staff("ANALYST"))
    me = client.get("/api/v1/admin/me")
    assert me.status_code == 200 and me.json()["role"] == "ANALYST"
    assert set(me.json()["permissions"]) == {
        "admin.access", "admin.metrics.read", "admin.ai_usage.read",
    }
    assert client.get("/api/v1/admin/metrics/overview").status_code == 200
    assert client.get("/api/v1/admin/metrics/conversion").status_code == 200
    assert client.get("/api/v1/admin/ai-usage/summary").status_code == 200
    # GET /plans is METRICS_READ (read-only catalog), but writes need PLANS_MANAGE.
    assert client.get("/api/v1/admin/plans").status_code == 200
    assert client.patch("/api/v1/admin/plans/pro", json={"name": "X"}).status_code == 404
    assert client.get("/api/v1/admin/families").status_code == 404
    assert client.get("/api/v1/admin/audit-log").status_code == 404
