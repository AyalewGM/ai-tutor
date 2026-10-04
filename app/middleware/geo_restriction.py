"""Country restriction behind Cloudflare.

When GEO_ENFORCEMENT_ENABLED is on, every request must arrive with a country
Cloudflare attached (CF-IPCountry) that is in ALLOWED_COUNTRIES. Missing,
"XX" (unknown) and "T1" (Tor) are all blocked — the check fails closed.

Two deliberate exceptions:
- Sign-in, auth config and health endpoints stay reachable so approved
  families can sign in while travelling; credential attacks on sign-in are
  handled by the rate limit, account lockout and Turnstile.
- Requests carrying a valid session for an APPROVED family (or staff) are
  allowed from anywhere — families travel.
"""

import logging
import uuid

from fastapi import Request, status
from sqlalchemy import select
from starlette.responses import JSONResponse

from app.core.database import SessionLocal
from app.core.settings import settings
from app.models import Student, User
from app.parent_models import ParentProfile

logger = logging.getLogger(__name__)

REGION_BLOCKED = "REGION_NOT_SUPPORTED"

# Cloudflare country codes that mean "don't know" or anonymized traffic.
_UNKNOWN_COUNTRIES = {"", "XX", "T1"}


def _exempt_paths() -> set[str]:
    prefix = settings.api_prefix
    return {
        "/health",
        "/ready",
        # Sign-in stays reachable worldwide: the credential is the password /
        # practice-pass token itself, guarded by throttles, lockout, Turnstile.
        f"{prefix}/auth/login",
        f"{prefix}/auth/config",
        f"{prefix}/practice-pass/activate",
    }


def _request_country(request: Request) -> str:
    """Country code Cloudflare asserted, or '' when headers aren't trusted."""
    if not settings.cloudflare_trusted:
        return ""
    return request.headers.get("cf-ipcountry", "").strip().upper()


def _has_approved_session(request: Request) -> bool:
    """Valid session for staff or a registered family (parent or learner pass)."""
    user_id = getattr(request.state, "authenticated_user_id", None)
    learner_id = getattr(request.state, "authenticated_learner_id", None)
    if user_id is None and learner_id is None:
        return False
    with SessionLocal() as db:
        if isinstance(user_id, uuid.UUID):
            user = db.get(User, user_id)
            if user is not None:
                if user.role != "PARENT":
                    return True  # staff accounts are not region-restricted
                parent = db.scalar(
                    select(ParentProfile).where(ParentProfile.user_id == user.id)
                )
                if parent is not None:
                    return True
        if isinstance(learner_id, uuid.UUID):
            student = db.get(Student, learner_id)
            if student is not None and student.parent_id is not None:
                parent = db.scalar(
                    select(ParentProfile).where(
                        ParentProfile.user_id == student.parent_id
                    )
                )
                if parent is not None:
                    return True
    return False


def _deny(request: Request, country: str) -> JSONResponse:
    logger.warning(
        "geo block: path=%s country=%s", request.url.path, country or "none"
    )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": REGION_BLOCKED},
    )


async def geo_restriction_middleware(request: Request, call_next):
    if not settings.geo_enforcement_enabled:
        return await call_next(request)
    path = request.url.path
    if path in _exempt_paths():
        return await call_next(request)
    country = _request_country(request)
    if country in settings.allowed_country_set:
        return await call_next(request)
    # New-family registration is never allowed from outside the allowlist —
    # the travel exemption is only for already-approved sessions.
    if path == f"{settings.api_prefix}/auth/register-parent":
        return _deny(request, country)
    # Travel exemption: an approved session may continue from a foreign but
    # known country. Unknown/anonymized countries are blocked for everyone.
    if country not in _UNKNOWN_COUNTRIES and _has_approved_session(request):
        return await call_next(request)
    return _deny(request, country)
