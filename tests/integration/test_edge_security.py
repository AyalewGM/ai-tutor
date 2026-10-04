"""PR 3 edge security: geo restriction, auth throttles, lockout, Turnstile."""

import uuid
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from redis.exceptions import RedisError

from app.auth import SESSION_COOKIE, create_session
from app.core.database import SessionLocal
from app.core.settings import settings
from app.main import app
from app.models import User
from app.parent_models import APPROVAL_APPROVED, APPROVAL_PENDING, ParentProfile
from app.services import auth_security

client = TestClient(app)


class FakeRedis:
    """Minimal in-memory stand-in for the limiter's Redis commands."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def incr(self, key):
        self.store[key] = str(int(self.store.get(key, "0")) + 1)
        return int(self.store[key])

    def expire(self, key, seconds):
        return True

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, seconds, value):
        self.store[key] = str(value)
        return True

    def delete(self, *keys):
        removed = 0
        for key in keys:
            removed += self.store.pop(key, None) is not None
        return removed


def _register_payload(email: str) -> dict:
    return {
        "email": email,
        "password": "a-very-long-password",
        "parent_pin": "1234",
        "terms_accepted": True,
        "coppa_consent_given": True,
    }


def _approved_parent(email: str | None = None) -> tuple[User, str]:
    """Approved family + live session cookie token."""
    with SessionLocal() as db:
        user = User(
            email=email or f"travel-{uuid.uuid4()}@example.com",
            display_name="Travel Parent",
            role="PARENT",
        )
        db.add(user)
        db.flush()
        db.add(ParentProfile(user_id=user.id, approval_status=APPROVAL_APPROVED))
        token, _ = create_session(db, user.id)
        db.commit()
        db.refresh(user)
        return user, token


@pytest.fixture
def geo_on(monkeypatch):
    monkeypatch.setattr(settings, "geo_enforcement_enabled", True)
    monkeypatch.setattr(settings, "cloudflare_trusted", True)
    yield
    client.cookies.clear()


@pytest.fixture
def throttled(monkeypatch):
    """Throttles on with an isolated FakeRedis per test."""
    fake = FakeRedis()
    monkeypatch.setattr(settings, "auth_throttles_enabled", True)
    monkeypatch.setattr(auth_security, "_redis", lambda: fake)
    yield fake
    client.cookies.clear()


# --- Geo restriction --------------------------------------------------------


def test_geo_allows_us_and_ca(geo_on):
    for country in ("US", "CA"):
        response = client.get("/api/v1/auth/me", headers={"CF-IPCountry": country})
        assert response.status_code == 401  # unauthenticated, but not geo-blocked


def test_geo_blocks_foreign_and_unknown(geo_on):
    for country in ("FR", "CN", "XX", "T1"):
        response = client.get("/api/v1/auth/me", headers={"CF-IPCountry": country})
        assert response.status_code == 403, country
        assert response.json()["detail"] == "REGION_NOT_SUPPORTED"
    # Missing header is also blocked (fail closed).
    assert client.get("/api/v1/auth/me").status_code == 403


def test_geo_blocks_everything_when_cf_not_trusted(monkeypatch):
    monkeypatch.setattr(settings, "geo_enforcement_enabled", True)
    monkeypatch.setattr(settings, "cloudflare_trusted", False)
    response = client.get("/api/v1/auth/me", headers={"CF-IPCountry": "US"})
    assert response.status_code == 403  # spoofable headers are ignored


def test_geo_off_by_default_ignores_headers():
    # Suite default: enforcement off — no 403 even from a blocked country.
    response = client.get("/api/v1/auth/me", headers={"CF-IPCountry": "FR"})
    assert response.status_code == 401


def test_geo_exempts_health_login_and_config(geo_on):
    assert client.get("/health", headers={"CF-IPCountry": "FR"}).status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "x"},
        headers={"CF-IPCountry": "FR"},
    )
    assert login.status_code == 401  # reachable: traveling families can sign in
    assert client.get("/api/v1/auth/config", headers={"CF-IPCountry": "FR"}).status_code == 200


def test_geo_travel_exemption_for_approved_family(geo_on):
    _, token = _approved_parent()
    client.cookies.set(SESSION_COOKIE, token)
    response = client.get("/api/v1/auth/me", headers={"CF-IPCountry": "FR"})
    assert response.status_code == 200


def test_geo_travel_exemption_denied_when_unknown(geo_on):
    _, token = _approved_parent()
    client.cookies.set(SESSION_COOKIE, token)
    # Unknown/anonymized countries block even approved sessions.
    assert client.get("/api/v1/auth/me", headers={"CF-IPCountry": "XX"}).status_code == 403
    assert client.get("/api/v1/auth/me").status_code == 403


def test_geo_nonapproved_family_still_gets_travel_exemption(geo_on):
    # approval_status is informational since the gate was removed — any
    # registered family session is exempt.
    with SessionLocal() as db:
        user = User(email=f"pending-{uuid.uuid4()}@example.com", role="PARENT")
        db.add(user)
        db.flush()
        db.add(ParentProfile(user_id=user.id, approval_status=APPROVAL_PENDING))
        token, _ = create_session(db, user.id)
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get("/api/v1/auth/me", headers={"CF-IPCountry": "FR"}).status_code == 200


def test_geo_registration_never_exempt(geo_on):
    _, token = _approved_parent()
    client.cookies.set(SESSION_COOKIE, token)
    response = client.post(
        "/api/v1/auth/register-parent",
        json=_register_payload(f"blocked-{uuid.uuid4()}@example.com"),
        headers={"CF-IPCountry": "FR"},
    )
    assert response.status_code == 403


# --- Auth throttles + lockout -----------------------------------------------


def test_register_rate_limit(throttled, monkeypatch):
    monkeypatch.setattr(settings, "register_rate_limit_per_ip", 2)
    for _ in range(2):
        client.post(
            "/api/v1/auth/register-parent",
            json=_register_payload(f"fam-{uuid.uuid4()}@example.com"),
        )
    response = client.post(
        "/api/v1/auth/register-parent",
        json=_register_payload(f"fam-{uuid.uuid4()}@example.com"),
    )
    assert response.status_code == 429


def test_login_rate_limit(throttled, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_per_ip", 2)
    for _ in range(2):
        client.post(
            "/api/v1/auth/login",
            json={"email": "a@example.com", "password": "wrong"},
        )
    response = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": "wrong"}
    )
    assert response.status_code == 429


def test_lockout_after_repeated_failures(throttled, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_per_ip", 100)
    monkeypatch.setattr(settings, "login_max_failed_attempts", 3)
    client.post("/api/v1/auth/register-parent", json=_register_payload("lock@example.com"))
    for _ in range(3):
        response = client.post(
            "/api/v1/auth/login", json={"email": "lock@example.com", "password": "wrong"}
        )
        assert response.status_code == 401
    # 4th attempt is locked out even with the correct password.
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "lock@example.com", "password": "a-very-long-password"},
    )
    assert response.status_code == 429
    # The lockout is per-account: a different account still signs in.
    client.post("/api/v1/auth/register-parent", json=_register_payload("other@example.com"))
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "a-very-long-password"},
    )
    assert response.status_code == 200


def test_successful_login_clears_failures(throttled, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_per_ip", 100)
    monkeypatch.setattr(settings, "login_max_failed_attempts", 3)
    client.post("/api/v1/auth/register-parent", json=_register_payload("reset@example.com"))
    for _ in range(2):
        client.post(
            "/api/v1/auth/login", json={"email": "reset@example.com", "password": "wrong"}
        )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "reset@example.com", "password": "a-very-long-password"},
    )
    assert response.status_code == 200
    # Counter was cleared: two more failures don't lock the account.
    for _ in range(2):
        response = client.post(
            "/api/v1/auth/login", json={"email": "reset@example.com", "password": "wrong"}
        )
        assert response.status_code == 401


def test_lockout_expires(throttled, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit_per_ip", 100)
    monkeypatch.setattr(settings, "login_max_failed_attempts", 1)
    monkeypatch.setattr(settings, "login_lockout_seconds", 0)  # immediate expiry
    client.post("/api/v1/auth/register-parent", json=_register_payload("exp@example.com"))
    client.post(
        "/api/v1/auth/login", json={"email": "exp@example.com", "password": "wrong"}
    )
    # Simulate expiry: FakeRedis honors no TTLs, so clear it like Redis would.
    throttled.store.clear()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "exp@example.com", "password": "a-very-long-password"},
    )
    assert response.status_code == 200


def test_throttles_fail_closed_when_redis_down(throttled, monkeypatch):
    def _boom():
        raise RedisError("down")

    monkeypatch.setattr(auth_security, "_redis", _boom)
    response = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": "x"}
    )
    assert response.status_code == 503


def test_throttles_disabled_never_touch_redis(monkeypatch):
    def _boom():
        raise RedisError("down")

    monkeypatch.setattr(auth_security, "_redis", _boom)
    # autouse fixture already set auth_throttles_enabled=False
    response = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": "x"}
    )
    assert response.status_code == 401


# --- Turnstile ---------------------------------------------------------------


@pytest.fixture
def turnstile_on(monkeypatch):
    monkeypatch.setattr(settings, "turnstile_secret_key", "test-secret")
    monkeypatch.setattr(settings, "turnstile_site_key", "test-site-key")
    yield
    client.cookies.clear()


def test_auth_config_exposes_site_key_only(turnstile_on):
    response = client.get("/api/v1/auth/config")
    assert response.status_code == 200
    assert response.json() == {"turnstile_site_key": "test-site-key"}


def test_turnstile_missing_token_rejected(turnstile_on):
    response = client.post(
        "/api/v1/auth/register-parent",
        json=_register_payload(f"no-token-{uuid.uuid4()}@example.com"),
    )
    assert response.status_code == 400


def test_turnstile_failed_verification_rejected(turnstile_on, monkeypatch):
    def _fake_post(*args, **kwargs):
        return SimpleNamespace(json=lambda: {"success": False, "error-codes": ["bad"]})

    monkeypatch.setattr(httpx, "post", _fake_post)
    response = client.post(
        "/api/v1/auth/register-parent",
        json={**_register_payload(f"bad-{uuid.uuid4()}@example.com"), "turnstile_token": "t"},
    )
    assert response.status_code == 400


def test_turnstile_success_allows_request(turnstile_on, monkeypatch):
    captured: dict = {}

    def _fake_post(url, data, timeout):
        captured.update(data)
        return SimpleNamespace(json=lambda: {"success": True})

    monkeypatch.setattr(httpx, "post", _fake_post)
    email = f"ok-{uuid.uuid4()}@example.com"
    response = client.post(
        "/api/v1/auth/register-parent",
        json={**_register_payload(email), "turnstile_token": "valid-token"},
    )
    assert response.status_code == 201
    assert captured["secret"] == "test-secret"
    assert captured["response"] == "valid-token"


def test_turnstile_outage_fails_closed(turnstile_on, monkeypatch):
    def _boom(*args, **kwargs):
        raise httpx.ConnectError("unreachable")

    monkeypatch.setattr(httpx, "post", _boom)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "a@example.com",
            "password": "x",
            "turnstile_token": "t",
        },
    )
    assert response.status_code == 503


def test_turnstile_also_guards_login(turnstile_on):
    response = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": "x"}
    )
    assert response.status_code == 400  # no token → rejected before credentials
