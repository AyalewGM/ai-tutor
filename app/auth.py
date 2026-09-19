import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth_models import AuthSession
from app.core.database import SessionLocal

SESSION_COOKIE = "ai_tutor_session"
SESSION_TTL = timedelta(hours=8)


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user_id: uuid.UUID) -> tuple[str, AuthSession]:
    token = secrets.token_urlsafe(32)
    session = AuthSession(
        user_id=user_id,
        token_hash=_digest(token),
        expires_at=datetime.now(UTC) + SESSION_TTL,
    )
    db.add(session)
    db.flush()
    return token, session


def revoke_session(db: Session, token: str) -> None:
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == _digest(token)))
    if session is not None:
        db.delete(session)


def resolve_user_id(db: Session, token: str) -> uuid.UUID | None:
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == _digest(token)))
    if session is None or session.expires_at <= datetime.now(UTC):
        return None
    return session.user_id


async def session_identity_middleware(request: Request, call_next):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with SessionLocal() as db:
            user_id = resolve_user_id(db, token)
            if user_id is not None:
                request.state.authenticated_user_id = user_id
    return await call_next(request)
