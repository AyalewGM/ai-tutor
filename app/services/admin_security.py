"""Staff second-factor plumbing: secret encryption, attempt limiting, audit."""

import uuid

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.admin_models import AdminAuditEvent
from app.core.settings import settings


class MfaNotConfigured(RuntimeError):
    """MFA_ENCRYPTION_KEY is missing — fail closed rather than store plaintext."""


def _fernet() -> Fernet:
    if not settings.mfa_encryption_key:
        raise MfaNotConfigured("MFA_ENCRYPTION_KEY is not configured")
    return Fernet(settings.mfa_encryption_key.encode("ascii"))


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("ascii")
    except InvalidToken as exc:
        raise MfaNotConfigured("MFA secret cannot be decrypted with the current key") from exc


def register_mfa_attempt(user_id: uuid.UUID) -> None:
    """Throttle code guessing. Fails closed: if the limiter is down, deny."""
    key = f"admin-mfa-attempts:{user_id}"
    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        attempts = client.incr(key)
        if attempts == 1:
            client.expire(key, settings.admin_mfa_window_seconds)
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verification is temporarily unavailable",
        ) from exc
    if attempts > settings.admin_mfa_max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification attempts. Try again later.",
        )


def clear_mfa_attempts(user_id: uuid.UUID) -> None:
    try:
        Redis.from_url(settings.redis_url, decode_responses=True).delete(
            f"admin-mfa-attempts:{user_id}"
        )
    except RedisError:
        return


def record_admin_action(
    db: Session,
    *,
    actor_user_id: uuid.UUID | None,
    actor_label: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
) -> AdminAuditEvent:
    event = AdminAuditEvent(
        actor_user_id=actor_user_id,
        actor_label=actor_label,
        action=action,
        target_type=target_type,
        target_id=target_id,
        before_json=before,
        after_json=after,
    )
    db.add(event)
    return event
