"""Cloudflare Turnstile bot check for sign-in and registration.

Enabled when TURNSTILE_SECRET_KEY is set. Fails closed: a missing token, a
failed verification, or an unreachable Cloudflare all deny the request. The
token is never logged or persisted.
"""

import logging

import httpx
from fastapi import HTTPException, status

from app.core.settings import settings

logger = logging.getLogger(__name__)

_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
_MAX_TOKEN_LENGTH = 2048


def turnstile_enabled() -> bool:
    return bool(settings.turnstile_secret_key)


def verify_turnstile(token: str | None, remote_ip: str | None = None) -> None:
    """Raise HTTPException unless the token verifies. No-op when disabled."""
    if not turnstile_enabled():
        return
    if not token or len(token) > _MAX_TOKEN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security check required. Please try again.",
        )
    try:
        response = httpx.post(
            _SITEVERIFY_URL,
            data={
                "secret": settings.turnstile_secret_key,
                "response": token,
                **({"remoteip": remote_ip} if remote_ip else {}),
            },
            timeout=settings.turnstile_timeout_seconds,
        )
        outcome = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.error("turnstile siteverify unreachable: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security check is temporarily unavailable. Please try again.",
        ) from exc
    if outcome.get("success") is not True:
        # Cloudflare error codes are non-sensitive; the token itself is never logged.
        logger.warning(
            "turnstile verification failed: %s", outcome.get("error-codes", [])
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security check failed. Please try again.",
        )
