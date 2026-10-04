import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import admin_api, auth_api
from app.admin_models import AdminAuditEvent
from app.auth import SESSION_COOKIE, create_session
from app.core.database import SessionLocal
from app.core.settings import settings
from app.main import app
from app.models import User
from app.parent_models import ParentProfile

client = TestClient(app)


@pytest.fixture
def outbox(monkeypatch):
    sent = []
    monkeypatch.setattr(auth_api, "send_email", sent.append)
    monkeypatch.setattr(admin_api, "send_email", sent.append)
    monkeypatch.setattr(settings, "require_family_approval", True)
    monkeypatch.setattr(settings, "admin_notification_email", "owner@mihur.test")
    yield sent
    client.cookies.clear()


def _register(email: str | None = None) -> tuple[str, dict]:
    email = email or f"family-{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/v1/auth/register-parent",
        json={
            "email": email,
            "password": "correct-horse-battery",
            "display_name": "Pilot Parent",
            "parent_pin": "1234",
            "terms_accepted": True,
            "coppa_consent_given": True,
        },
    )
    assert response.status_code == 201, response.text
    return email, response.json()


def _admin_token() -> str:
    """An ADMIN session that has already passed two-factor."""
    with SessionLocal() as db:
        user = User(email=f"staff-{uuid.uuid4().hex[:8]}@example.test", role="ADMIN")
        db.add(user)
        db.flush()
        token, session = create_session(db, user.id)
        session.mfa_verified_at = datetime.now(UTC)
        db.commit()
        return token


def _profile_id(email: str) -> uuid.UUID:
    with SessionLocal() as db:
        return db.scalar(
            select(ParentProfile.id).join(User, User.id == ParentProfile.user_id).where(
                User.email == email
            )
        )


def test_new_family_is_pending_blocked_and_admin_is_notified(outbox) -> None:
    email, body = _register()
    assert body["approval_status"] == "PENDING"
    assert [m.to for m in outbox] == ["owner@mihur.test"]
    assert email in outbox[0].body and "/admin" in outbox[0].body

    blocked = client.get("/api/v1/onboarding/learners")
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "FAMILY_PENDING_APPROVAL"
    # Status stays readable so the pending page can explain what's happening.
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200 and me.json()["approval_status"] == "PENDING"


def test_admin_approves_family_who_then_gets_access(outbox) -> None:
    family_email, _ = _register()
    family_cookie = client.cookies.get(SESSION_COOKIE)
    profile_id = _profile_id(family_email)

    client.cookies.set(SESSION_COOKIE, _admin_token())
    pending = client.get("/api/v1/admin/families", params={"status": "PENDING"})
    assert pending.status_code == 200
    assert str(profile_id) in {f["parent_profile_id"] for f in pending.json()}

    approved = client.post(f"/api/v1/admin/families/{profile_id}/approve")
    assert approved.status_code == 200 and approved.json()["approval_status"] == "APPROVED"
    assert client.post(f"/api/v1/admin/families/{profile_id}/approve").status_code == 409
    assert outbox[-1].to == family_email and "approved" in outbox[-1].subject

    with SessionLocal() as db:
        event = db.scalar(
            select(AdminAuditEvent).where(
                AdminAuditEvent.target_id == str(profile_id),
                AdminAuditEvent.action == "family.approved",
            )
        )
        assert event is not None
        assert event.before_json == {"approval_status": "PENDING"}

    client.cookies.set(SESSION_COOKIE, family_cookie)
    assert client.get("/api/v1/onboarding/learners").status_code == 200


def test_rejected_family_sees_reason_and_stays_blocked(outbox) -> None:
    family_email, _ = _register()
    family_cookie = client.cookies.get(SESSION_COOKIE)
    profile_id = _profile_id(family_email)

    client.cookies.set(SESSION_COOKIE, _admin_token())
    rejected = client.post(
        f"/api/v1/admin/families/{profile_id}/reject",
        json={"reason": "The pilot is limited to Maryland families right now."},
    )
    assert rejected.status_code == 200
    assert "Maryland" in outbox[-1].body and outbox[-1].to == family_email

    client.cookies.set(SESSION_COOKIE, family_cookie)
    blocked = client.get("/api/v1/onboarding/learners")
    assert blocked.status_code == 403 and blocked.json()["detail"] == "FAMILY_REJECTED"
    me = client.get("/api/v1/auth/me").json()
    assert me["approval_status"] == "REJECTED" and "Maryland" in me["rejection_reason"]


def test_family_routes_require_staff_with_mfa(outbox) -> None:
    _register()
    for method, path in [
        ("get", "/api/v1/admin/families"),
        ("post", f"/api/v1/admin/families/{uuid.uuid4()}/approve"),
    ]:
        assert getattr(client, method)(path).status_code == 404, path

    with SessionLocal() as db:
        staff = User(email=f"staff-{uuid.uuid4().hex[:8]}@example.test", role="ADMIN")
        db.add(staff)
        db.flush()
        token, _ = create_session(db, staff.id)  # not MFA-verified
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get("/api/v1/admin/families").status_code == 403


def test_gate_off_approves_immediately(outbox, monkeypatch) -> None:
    monkeypatch.setattr(settings, "require_family_approval", False)
    _, body = _register()
    assert body["approval_status"] == "APPROVED"
    assert outbox == []
    assert client.get("/api/v1/onboarding/learners").status_code == 200


def test_self_created_profile_cannot_bypass_the_gate(outbox) -> None:
    with SessionLocal() as db:
        user = User(email=f"bare-{uuid.uuid4().hex[:8]}@example.test", role="PARENT")
        db.add(user)
        db.flush()
        token, _ = create_session(db, user.id)
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)
    assert client.post("/api/v1/parents/profile").status_code == 200
    assert client.get("/api/v1/onboarding/learners").json()["detail"] == "FAMILY_PENDING_APPROVAL"
