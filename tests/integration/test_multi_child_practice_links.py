"""Issue #426 — per-child practice links, invite-only registration, pilot seats.

Synthetic fixtures only; never touches real family records. Each test builds
its own parent profile + learners so the suite is order-independent.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import practice_pass_api
from app.core.database import SessionLocal
from app.core.settings import settings
from app.identity import current_user
from app.main import app
from app.models import Curriculum, Student, User
from app.parent_models import (
    FamilyPracticePass,
    LearnerPassSession,
    ParentInvitation,
    ParentProfile,
    ParentStudentRelationship,
    PilotEntitlement,
)
from app.services.parent_dashboard import unlink_child
from app.services.plans import effective_seats

client = TestClient(app)


@pytest.fixture(autouse=True)
def _adult_unlock(monkeypatch):
    monkeypatch.setattr(practice_pass_api, "require_parent_unlock", lambda *_args: None)


def _override_user(user: User) -> None:
    app.dependency_overrides[current_user] = lambda: user


def _clear_override() -> None:
    app.dependency_overrides.pop(current_user, None)


def _make_family(children: int = 2) -> tuple[uuid.UUID, list[uuid.UUID]]:
    """Synthetic parent + children with active relationships."""
    suffix = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        user = User(
            email=f"pilot-parent-{suffix}@example.com",
            display_name="Pilot Parent",
            role="PARENT",
        )
        db.add(user)
        db.flush()
        parent = ParentProfile(user_id=user.id, subscription_tier="free")
        db.add(parent)
        db.flush()
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_MATH_8")
        )
        student_ids = []
        for i in range(children):
            student = Student(
                first_name=f"PilotChild{i}",
                grade_level="8",
                curriculum_id=curriculum.id if curriculum else None,
                active=True,
            )
            db.add(student)
            db.flush()
            db.add(
                ParentStudentRelationship(
                    parent_profile_id=parent.id, student_id=student.id
                )
            )
            student_ids.append(student.id)
        db.commit()
        return parent.id, student_ids


def _parent_user(parent_id: uuid.UUID) -> User:
    with SessionLocal() as db:
        parent = db.get(ParentProfile, parent_id)
        return db.get(User, parent.user_id)


def _extract_token(url: str) -> str:
    return url.rsplit("/", 1)[-1]


def test_per_child_links_have_independent_lifecycles():
    parent_id, (child_a, child_b) = _make_family(children=2)
    try:
        _override_user(_parent_user(parent_id))

        resp_a = client.post("/api/v1/practice-pass", json={"student_id": str(child_a)})
        resp_b = client.post("/api/v1/practice-pass", json={"student_id": str(child_b)})
        assert resp_a.status_code == 200 and resp_b.status_code == 200
        token_a = _extract_token(resp_a.json()["url"])
        token_b = _extract_token(resp_b.json()["url"])
        assert token_a != token_b
        assert resp_a.json()["student_id"] == str(child_a)
        assert resp_b.json()["student_id"] == str(child_b)

        listed = client.get("/api/v1/practice-pass")
        assert listed.status_code == 200
        assert {p["student_id"] for p in listed.json()["passes"]} == {
            str(child_a), str(child_b)
        }
        # Token never round-trips through the list endpoint.
        assert token_a not in listed.text and token_b not in listed.text

        # Activate child A: optional nickname becomes the session display
        # name; the canonical learner record is never mutated.
        before_name = None
        with SessionLocal() as db:
            before_name = db.get(Student, child_a).first_name
        act = client.post(
            "/api/v1/practice-pass/activate",
            json={"token": token_a, "nickname": "kid-a"},
        )
        assert act.status_code == 200
        assert act.json()["student_id"] == str(child_a)
        assert act.headers.get("Referrer-Policy") == "no-referrer"
        with SessionLocal() as db:
            assert db.get(Student, child_a).first_name == before_name
            session = db.scalar(
                select(LearnerPassSession).where(
                    LearnerPassSession.student_id == child_a
                )
            )
            assert session.display_name == "kid-a"

        # Regenerate A: old A token dies, sibling B unaffected.
        regen = client.post("/api/v1/practice-pass", json={"student_id": str(child_a)})
        assert regen.status_code == 200
        token_a2 = _extract_token(regen.json()["url"])
        assert token_a2 != token_a
        stale = client.post(
            "/api/v1/practice-pass/activate",
            json={"token": token_a},
        )
        assert stale.status_code == 401
        act_b = client.post(
            "/api/v1/practice-pass/activate",
            json={"token": token_b},
        )
        assert act_b.status_code == 200

        # Revoke A only: A dies, B's existing session + token stay live.
        revoked = client.delete(
            "/api/v1/practice-pass", params={"student_id": str(child_a)}
        )
        assert revoked.status_code == 204
        assert (
            client.post(
                "/api/v1/practice-pass/activate", json={"token": token_a2}
            ).status_code
            == 401
        )
        with SessionLocal() as db:
            a_sessions = db.scalars(
                select(LearnerPassSession).where(
                    LearnerPassSession.student_id == child_a
                )
            ).all()
            assert a_sessions == []
            b_sessions = db.scalars(
                select(LearnerPassSession).where(
                    LearnerPassSession.student_id == child_b
                )
            ).all()
            assert len(b_sessions) == 1

        # Unlink B: its pass and sessions die with the relationship.
        with SessionLocal() as db:
            parent = db.get(ParentProfile, parent_id)
            unlink_child(db, parent=parent, student_id=child_b)
            db.commit()
        assert (
            client.post(
                "/api/v1/practice-pass/activate", json={"token": token_b}
            ).status_code
            == 401
        )
        with SessionLocal() as db:
            assert (
                db.scalars(
                    select(LearnerPassSession).where(
                        LearnerPassSession.student_id == child_b
                    )
                ).all()
                == []
            )
    finally:
        _clear_override()


def test_multi_child_family_must_choose_child():
    parent_id, _children = _make_family(children=2)
    try:
        _override_user(_parent_user(parent_id))
        resp = client.post("/api/v1/practice-pass", json={})
        assert resp.status_code == 409
    finally:
        _clear_override()


def test_pass_operations_reject_unrelated_child():
    parent_id, (mine,) = _make_family(children=1)
    _other_id, (foreign,) = _make_family(children=1)
    try:
        _override_user(_parent_user(parent_id))
        resp = client.post("/api/v1/practice-pass", json={"student_id": str(foreign)})
        assert resp.status_code == 404
        # Own child still works.
        ok = client.post("/api/v1/practice-pass", json={"student_id": str(mine)})
        assert ok.status_code == 200
    finally:
        _clear_override()


def test_single_child_legacy_path_still_works():
    parent_id, (child,) = _make_family(children=1)
    try:
        _override_user(_parent_user(parent_id))
        resp = client.post("/api/v1/practice-pass", json={})
        assert resp.status_code == 200
        assert resp.json()["student_id"] == str(child)
    finally:
        _clear_override()


def _register(email: str, token: str | None):
    payload = {
        "email": email,
        "password": "synthetic-password-12+",
        "display_name": "Synthetic Parent",
        "parent_pin": "1234",
        "country_code": "US",
        "region_code": "MD",
        "terms_accepted": True,
        "coppa_consent_given": True,
    }
    if token is not None:
        payload["invitation_token"] = token
    return client.post("/api/v1/auth/register-parent", json=payload)


def _issue_invitation(email: str | None = None, seats: int | None = None,
                      status: str = "PENDING") -> tuple[str, uuid.UUID]:
    import hashlib
    import secrets

    raw = secrets.token_urlsafe(32)
    with SessionLocal() as db:
        inv = ParentInvitation(
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            email=email,
            seats=seats,
            status=status,
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return raw, inv.id


def test_invite_only_registration_lifecycle(monkeypatch):
    monkeypatch.setattr(settings, "pilot_invite_only", True)
    suffix = uuid.uuid4().hex[:8]

    # No token -> denied generically.
    denied = _register(f"no-invite-{suffix}@example.com", None)
    assert denied.status_code == 403

    # Garbage token -> same denial.
    bad = _register(f"bad-token-{suffix}@example.com", "x" * 43)
    assert bad.status_code == 403

    # Valid scoped invitation -> account + consumed invite + entitlement.
    token, invitation_id = _issue_invitation(
        email=f"invited-{suffix}@example.com", seats=3
    )
    ok = _register(f"invited-{suffix}@example.com", token)
    assert ok.status_code == 201
    with SessionLocal() as db:
        inv = db.get(ParentInvitation, invitation_id)
        assert inv.status == "ACCEPTED"
        assert inv.accepted_parent_profile_id is not None
        grant = db.scalar(
            select(PilotEntitlement).where(
                PilotEntitlement.parent_profile_id == inv.accepted_parent_profile_id
            )
        )
        assert grant is not None
        assert grant.seats == 3
        assert grant.source == "INVITATION"
        assert grant.ends_at > datetime.now(UTC)

    # Single-use: the same token can never mint a second family.
    replay = _register(f"replay-{suffix}@example.com", token)
    assert replay.status_code == 403

    # Disabled invitations cannot self-register.
    dtoken, _ = _issue_invitation(
        email=f"disabled-{suffix}@example.com", status="DISABLED"
    )
    assert _register(f"disabled-{suffix}@example.com", dtoken).status_code == 403

    # Email-scoped invitations reject a different email.
    scoped, _ = _issue_invitation(email=f"scoped-{suffix}@example.com")
    assert (
        _register(f"impostor-{suffix}@example.com", scoped).status_code == 403
    )


def test_open_registration_ignores_invitation_gate(monkeypatch):
    # Default (non-pilot) deployments keep self-serve registration.
    monkeypatch.setattr(settings, "pilot_invite_only", False)
    suffix = uuid.uuid4().hex[:8]
    resp = _register(f"open-{suffix}@example.com", None)
    assert resp.status_code == 201


def test_pilot_entitlement_drives_seats_with_time_bound():
    parent_id, _ = _make_family(children=2)
    with SessionLocal() as db:
        parent = db.get(ParentProfile, parent_id)
        plan_seats = effective_seats(db, parent)
        db.add(
            PilotEntitlement(
                parent_profile_id=parent.id,
                seats=3,
                source="ADMIN",
                starts_at=datetime.now(UTC) - timedelta(days=1),
                ends_at=datetime.now(UTC) + timedelta(days=30),
            )
        )
        db.commit()
        assert effective_seats(db, parent) == 3
    with SessionLocal() as db:
        parent = db.get(ParentProfile, parent_id)
        grant = db.scalar(
            select(PilotEntitlement).where(
                PilotEntitlement.parent_profile_id == parent_id
            )
        )
        grant.ends_at = datetime.now(UTC) - timedelta(hours=1)
        db.commit()
        assert effective_seats(db, parent) == plan_seats


def test_expired_and_revoked_passes_cannot_activate():
    parent_id, (child,) = _make_family(children=1)
    try:
        _override_user(_parent_user(parent_id))
        resp = client.post("/api/v1/practice-pass", json={"student_id": str(child)})
        token = _extract_token(resp.json()["url"])
        with SessionLocal() as db:
            row = db.scalar(
                select(FamilyPracticePass).where(
                    FamilyPracticePass.student_id == child
                )
            )
            row.expires_at = datetime.now(UTC) - timedelta(hours=1)
            db.commit()
        assert (
            client.post(
                "/api/v1/practice-pass/activate", json={"token": token}
            ).status_code
            == 401
        )
        # Unknown token is the same generic denial — no existence signal.
        assert (
            client.post(
                "/api/v1/practice-pass/activate", json={"token": "z" * 43}
            ).status_code
            == 401
        )
    finally:
        _clear_override()


def test_bulk_generate_returns_one_link_per_child_and_all_activate():
    parent_id, children = _make_family(children=3)
    try:
        _override_user(_parent_user(parent_id))
        resp = client.post("/api/v1/practice-pass/all")
        assert resp.status_code == 200
        links = resp.json()
        assert {row["student_id"] for row in links} == {str(c) for c in children}
        # Every link activates and lands on its own child.
        for row, child in zip(links, children, strict=True):
            activated = client.post(
                "/api/v1/practice-pass/activate",
                json={"token": _extract_token(row["url"])},
            )
            assert activated.status_code == 200
            assert activated.json()["student_id"] == str(child)
    finally:
        _clear_override()


def test_second_activation_is_rejected_while_session_is_live():
    parent_id, (child,) = _make_family(children=1)
    try:
        _override_user(_parent_user(parent_id))
        url = client.post(
            "/api/v1/practice-pass", json={"student_id": str(child)}
        ).json()["url"]
        token = _extract_token(url)
        assert (
            client.post("/api/v1/practice-pass/activate", json={"token": token}).status_code
            == 200
        )
        # The same browser re-visiting its own link is idempotent — never
        # self-rejected.
        assert (
            client.post("/api/v1/practice-pass/activate", json={"token": token}).status_code
            == 200
        )
        # A second holder of the same link (different browser, no cookie) is
        # refused while the first session is in use — the live session is
        # untouched.
        client.cookies.delete("ai_tutor_learner")
        assert (
            client.post("/api/v1/practice-pass/activate", json={"token": token}).status_code
            == 409
        )
        with SessionLocal() as db:
            live = db.scalars(
                select(LearnerPassSession).where(
                    LearnerPassSession.student_id == child
                )
            ).all()
            assert len(live) == 1
    finally:
        _clear_override()


def test_stale_session_does_not_block_reactivation():
    """A crashed/idle session must not lock the child out: once last_seen_at
    is older than the live window, activation succeeds and cleans up."""
    parent_id, (child,) = _make_family(children=1)
    try:
        _override_user(_parent_user(parent_id))
        url = client.post(
            "/api/v1/practice-pass", json={"student_id": str(child)}
        ).json()["url"]
        token = _extract_token(url)
        client.post("/api/v1/practice-pass/activate", json={"token": token})
        with SessionLocal() as db:
            stale = db.scalar(
                select(LearnerPassSession).where(
                    LearnerPassSession.student_id == child
                )
            )
            stale.last_seen_at = datetime.now(UTC) - timedelta(
                seconds=settings.practice_link_live_session_window_seconds + 60
            )
            db.commit()
            stale_id = stale.id
        # Re-enter from a browser without the old session cookie — the stale
        # session is cleaned and activation succeeds.
        client.cookies.delete("ai_tutor_learner")
        resp = client.post("/api/v1/practice-pass/activate", json={"token": token})
        assert resp.status_code == 200
        with SessionLocal() as db:
            live = db.scalars(
                select(LearnerPassSession).where(
                    LearnerPassSession.student_id == child
                )
            ).all()
            assert len(live) == 1
            assert live[0].id != stale_id
    finally:
        _clear_override()


def test_parent_regeneration_reclaims_a_live_link():
    """If a live link is genuinely shared, the parent retakes it by
    regenerating — the new link activates despite an in-use session."""
    parent_id, (child,) = _make_family(children=1)
    try:
        _override_user(_parent_user(parent_id))
        url = client.post(
            "/api/v1/practice-pass", json={"student_id": str(child)}
        ).json()["url"]
        client.post(
            "/api/v1/practice-pass/activate", json={"token": _extract_token(url)}
        )
        # Confirm the in-use block fires for a different holder of the link.
        client.cookies.delete("ai_tutor_learner")
        assert (
            client.post(
                "/api/v1/practice-pass/activate",
                json={"token": _extract_token(url)},
            ).status_code
            == 409
        )
        # Regeneration deletes the live session; the fresh link activates.
        fresh = client.post(
            "/api/v1/practice-pass", json={"student_id": str(child)}
        ).json()["url"]
        resp = client.post(
            "/api/v1/practice-pass/activate", json={"token": _extract_token(fresh)}
        )
        assert resp.status_code == 200
        with SessionLocal() as db:
            assert (
                len(
                    db.scalars(
                        select(LearnerPassSession).where(
                            LearnerPassSession.student_id == child
                        )
                    ).all()
                )
                == 1
            )
    finally:
        _clear_override()


def test_registration_requires_and_stores_family_state():
    email = f"state-{uuid.uuid4().hex[:8]}@example.com"
    base = {
        "email": email,
        "password": "synthetic-password-12+",
        "parent_pin": "1234",
        "terms_accepted": True,
        "coppa_consent_given": True,
    }
    # Missing state entirely → 422 (schema requires it).
    assert (
        client.post("/api/v1/auth/register-parent", json=base).status_code == 422
    )
    # Unknown region pair → 422.
    bad = dict(base, country_code="US", region_code="XX")
    assert (
        client.post("/api/v1/auth/register-parent", json=bad).status_code == 422
    )
    # Valid pair registers and persists the family region.
    ok = dict(base, country_code="US", region_code="NY")
    resp = client.post("/api/v1/auth/register-parent", json=ok)
    assert resp.status_code == 201, resp.text
    with SessionLocal() as db:
        parent = db.scalar(
            select(ParentProfile).where(
                ParentProfile.user_id == db.scalar(
                    select(User.id).where(User.email == email)
                )
            )
        )
        assert parent.country_code == "US"
        assert parent.region_code == "NY"


def test_public_regions_endpoint_serves_registration_cascade():
    resp = client.get("/api/v1/auth/regions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["family"] is None
    countries = {c["code"]: c for c in body["countries"]}
    assert set(countries) == {"US", "CA"}
    us = {r["code"]: r for r in countries["US"]["regions"]}
    assert len(us) == 51  # 50 states + DC
    assert us["NY"]["name"] == "New York"


def test_uncovered_region_falls_back_to_country_catalog():
    """A state with no seeded curriculum still sees the US catalog —
    choosing a state is required, never a dead end."""
    email = f"ny-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/v1/auth/register-parent",
        json={
            "email": email,
            "password": "synthetic-password-12+",
            "parent_pin": "1234",
            "country_code": "US",
            "region_code": "NY",
            "terms_accepted": True,
            "coppa_consent_given": True,
        },
    )
    assert resp.status_code == 201, resp.text
    # A freshly registered family has no learner session — the shared test
    # client may carry a sibling test's ai_tutor_learner cookie.
    client.cookies.delete("ai_tutor_learner")
    resp = client.get("/api/v1/onboarding/curricula")
    assert resp.status_code == 200
    curricula = resp.json()
    assert curricula  # fell back to the country list, not an empty catalog
    # Nothing is labeled as belonging to a different covered region.
    assert all(
        c["region_code"] in {"DC", "MD", "VA", "NY", None} for c in curricula
    )


@pytest.fixture
def outbox(monkeypatch):
    from app import admin_api, auth_api

    sent = []
    monkeypatch.setattr(auth_api, "send_email", sent.append)
    monkeypatch.setattr(admin_api, "send_email", sent.append)
    monkeypatch.setattr(settings, "admin_notification_email", "owner@example.com")
    yield sent
    client.cookies.clear()


def _staff_cookie() -> None:
    """ADMIN session with MFA verified — mirrors the staff gate in admin_api."""
    from app.auth import SESSION_COOKIE, create_session

    with SessionLocal() as db:
        staff = User(email=f"staff-{uuid.uuid4().hex[:8]}@example.com", role="ADMIN")
        db.add(staff)
        db.flush()
        token, session = create_session(db, staff.id)
        session.mfa_verified_at = datetime.now(UTC)
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)


def test_registration_emails_welcome_to_parent_and_notice_to_owner(outbox):
    email = f"welcome-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/v1/auth/register-parent",
        json={
            "email": email,
            "password": "synthetic-password-12+",
            "parent_pin": "1234",
            "country_code": "US",
            "region_code": "NY",
            "terms_accepted": True,
            "coppa_consent_given": True,
        },
    )
    assert resp.status_code == 201, resp.text
    recipients = [m.to for m in outbox]
    assert email in recipients  # welcome email to the registering parent
    assert "owner@example.com" in recipients  # admin notification preserved
    welcome = next(m for m in outbox if m.to == email)
    assert "New York" in welcome.body
    assert "one link per child" in welcome.body.lower() or "each child" in welcome.body


def test_invitation_send_flag_emails_the_link(outbox):
    _staff_cookie()
    # send=true without an email has nowhere to go.
    assert (
        client.post(
            "/api/v1/admin/family-invitations", json={"send": True}
        ).status_code
        == 422
    )
    target = f"invited-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/v1/admin/family-invitations",
        json={"email": target, "seats": 2, "send": True},
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["token"]
    invite = next(m for m in outbox if m.to == target)
    assert f"/register?invite={token}" in invite.body
    assert "2 learners" in invite.body
    # The same link can be handed off manually when send is false.
    quiet = client.post(
        "/api/v1/admin/family-invitations",
        json={"email": f"quiet-{uuid.uuid4().hex[:8]}@example.com"},
    )
    assert quiet.status_code == 201
    assert not any("register?invite" in m.body for m in outbox if m.to == quiet.json()["email"])


def test_pilot_approval_gate_blocks_pending_family(monkeypatch):
    """With pilot_require_approval, a registering family is PENDING and every
    parent-scoped surface denies access until staff approval."""
    monkeypatch.setattr(settings, "pilot_require_approval", True)
    email = f"pending-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/v1/auth/register-parent",
        json={
            "email": email,
            "password": "synthetic-password-12+",
            "parent_pin": "1234",
            "country_code": "US",
            "region_code": "MD",
            "terms_accepted": True,
            "coppa_consent_given": True,
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["approval_status"] == "PENDING"
    # Session exists (login works) but parent surfaces deny.
    assert client.get("/api/v1/onboarding/learners").status_code == 403
    assert client.post("/api/v1/practice-pass", json={}).status_code == 403


def test_pilot_approval_gate_allows_family_after_approval(monkeypatch):
    monkeypatch.setattr(settings, "pilot_require_approval", True)
    email = f"approved-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/v1/auth/register-parent",
        json={
            "email": email,
            "password": "synthetic-password-12+",
            "parent_pin": "1234",
            "country_code": "US",
            "region_code": "MD",
            "terms_accepted": True,
            "coppa_consent_given": True,
        },
    )
    assert resp.status_code == 201, resp.text
    assert client.get("/api/v1/onboarding/learners").status_code == 403
    with SessionLocal() as db:
        parent = db.scalar(
            select(ParentProfile).where(
                ParentProfile.user_id
                == db.scalar(select(User.id).where(User.email == email))
            )
        )
        parent.approval_status = "APPROVED"
        db.commit()
    assert client.get("/api/v1/onboarding/learners").status_code == 200


def test_pilot_approval_gate_off_leaves_register_approved(monkeypatch):
    """Flag off = existing behavior: self-registered families proceed."""
    monkeypatch.setattr(settings, "pilot_require_approval", False)
    resp = _register(f"gate-off-{uuid.uuid4().hex[:8]}@example.com", None)
    assert resp.status_code == 201, resp.text
    assert resp.json()["approval_status"] == "APPROVED"
