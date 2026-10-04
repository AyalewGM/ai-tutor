"""Sign-in/registration throttling and account lockout.

Redis-backed fixed-window counters, namespaced per control. Fails closed like
the admin MFA limiter: if Redis is unavailable the endpoint returns 503 rather
than allowing unbounded credential guessing.
"""

import hashlib
import logging

from fastapi import HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError

from app.core.settings import settings

logger = logging.getLogger(__name__)


def _redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def client_ip(request: Request) -> str:
    """Caller IP for throttling. CF-Connecting-IP is trusted only when the app
    is configured to sit behind a locked-down Cloudflare zone."""
    if settings.cloudflare_trusted:
        cf_ip = request.headers.get("cf-connecting-ip", "").strip()
        if cf_ip:
            return cf_ip
    return request.client.host if request.client else "unknown"


def _increment(key: str, window_seconds: int) -> int | None:
    """Increment the windowed counter; None when Redis is unavailable."""
    try:
        client = _redis()
        count = client.incr(key)
        if count == 1:
            client.expire(key, window_seconds)
        return count
    except RedisError:
        return None


def _deny_unavailable() -> None:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Service is temporarily unavailable. Please try again shortly.",
    )


def _deny_rate_limited() -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many attempts. Please try again later.",
    )


def enforce_login_rate_limit(request: Request) -> None:
    if not settings.auth_throttles_enabled:
        return
    count = _increment(
        f"rl:login-ip:{client_ip(request)}", settings.login_rate_window_seconds
    )
    if count is None:
        logger.error("login rate limiter unavailable (redis)")
        _deny_unavailable()
    if count > settings.login_rate_limit_per_ip:
        logger.warning("login rate limit exceeded for client IP")
        _deny_rate_limited()


def enforce_register_rate_limit(request: Request) -> None:
    if not settings.auth_throttles_enabled:
        return
    count = _increment(
        f"rl:register-ip:{client_ip(request)}", settings.register_rate_window_seconds
    )
    if count is None:
        logger.error("register rate limiter unavailable (redis)")
        _deny_unavailable()
    if count > settings.register_rate_limit_per_ip:
        logger.warning("registration rate limit exceeded for client IP")
        _deny_rate_limited()


def _lockout_key(email: str) -> str:
    # SHA-256 so raw account emails never appear in Redis keys or dumps.
    return f"rl:login-fail:{hashlib.sha256(email.encode('utf-8')).hexdigest()}"


def ensure_not_locked_out(email: str) -> None:
    """Deny while the account's failed-attempt lockout is active."""
    if not settings.auth_throttles_enabled:
        return
    try:
        failures = _redis().get(_lockout_key(email))
    except RedisError:
        logger.error("login lockout check unavailable (redis)")
        _deny_unavailable()
    if failures is not None and int(failures) >= settings.login_max_failed_attempts:
        logger.warning("login blocked: account locked after repeated failures")
        _deny_rate_limited()


def record_login_failure(email: str) -> None:
    """Best-effort: the request already failed authentication; never raise."""
    if not settings.auth_throttles_enabled:
        return
    if _increment(_lockout_key(email), settings.login_lockout_seconds) is None:
        logger.error("could not record login failure (redis)")


def clear_login_failures(email: str) -> None:
    if not settings.auth_throttles_enabled:
        return
    try:
        _redis().delete(_lockout_key(email))
    except RedisError:
        logger.error("could not clear login failures (redis)")
