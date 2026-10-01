import hashlib
import secrets
import uuid

from fastapi import HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError

from app.core.settings import settings

PARENT_UNLOCK_HEADER = "X-Parent-Unlock"


def _redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def register_pin_attempt(parent_user_id: uuid.UUID) -> None:
    key = f"parent-pin-attempts:{parent_user_id}"
    try:
        client = _redis()
        attempts = client.incr(key)
        if attempts == 1:
            client.expire(key, settings.parent_pin_window_seconds)
        if attempts > settings.parent_pin_max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many PIN attempts. Try again later or re-authenticate with the account password.",
            )
    except HTTPException:
        raise
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Adult-access verification is temporarily unavailable",
        ) from exc


def clear_pin_attempts(parent_user_id: uuid.UUID) -> None:
    try:
        _redis().delete(f"parent-pin-attempts:{parent_user_id}")
    except RedisError:
        # Verification already succeeded. Failure to clear only makes the limiter
        # stricter on the next attempt; never weaken the gate because Redis failed.
        return


def issue_parent_unlock(parent_user_id: uuid.UUID) -> str:
    token = secrets.token_urlsafe(32)
    key = f"parent-unlock:{_digest(token)}"
    try:
        _redis().setex(key, settings.parent_unlock_ttl_seconds, str(parent_user_id))
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Adult-access verification is temporarily unavailable",
        ) from exc
    return token


def require_parent_unlock(request: Request, parent_user_id: uuid.UUID) -> None:
    token = request.headers.get(PARENT_UNLOCK_HEADER)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent PIN or password re-authentication required",
        )
    try:
        owner = _redis().get(f"parent-unlock:{_digest(token)}")
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Adult-access verification is temporarily unavailable",
        ) from exc
    if owner != str(parent_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent unlock is invalid or expired",
        )
