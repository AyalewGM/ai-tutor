from fastapi import HTTPException, Response

import app.auth_api as auth_api
from app.auth_api import LoginRequest, _set_session_cookie, login


class MissingUserDb:
    def scalar(self, _query):
        return None

    def get(self, _model, _key):
        return None


def test_session_cookie_is_http_only_and_same_site(monkeypatch):
    monkeypatch.setattr(auth_api.settings, "session_cookie_secure", True)
    response = Response()

    _set_session_cookie(response, "synthetic-session-token")

    cookie = response.headers["set-cookie"]
    assert "ai_tutor_session=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Secure" in cookie
    assert "Max-Age=28800" in cookie


def test_unknown_parent_login_returns_generic_failure():
    payload = LoginRequest(email="synthetic.parent@example.test", password="not-a-real-password")

    try:
        login(payload, Response(), MissingUserDb())
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid email or password"
    else:
        raise AssertionError("unknown account must not authenticate")
