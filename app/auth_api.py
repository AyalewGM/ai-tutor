from datetime import UTC, datetime
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import SESSION_COOKIE, create_session, revoke_session
from app.core.database import get_db
from app.core.settings import settings
from app.credential_models import UserCredential
from app.identity import CurrentUser, initial_approval_status
from app.models import User
from app.parent_models import ParentProfile
from app.schemas import ParentRegisterSchema
from app.services.email import new_family_notification, send_email

router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]
_passwords = PasswordHasher()


ParentRegistration = ParentRegisterSchema

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class SessionUser(BaseModel):
    id: str
    role: str
    display_name: str | None
    # PENDING / APPROVED / REJECTED for families; None for staff accounts.
    approval_status: str | None = None
    rejection_reason: str | None = None


def _session_user(db: Session, user: User) -> SessionUser:
    parent = db.scalar(select(ParentProfile).where(ParentProfile.user_id == user.id))
    return SessionUser(
        id=str(user.id),
        role=user.role,
        display_name=user.display_name,
        approval_status=parent.approval_status if parent else None,
        rejection_reason=parent.rejection_reason if parent else None,
    )


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=8 * 60 * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/register-parent", response_model=SessionUser, status_code=status.HTTP_201_CREATED)
def register_parent(
    payload: ParentRegistration,
    response: Response,
    background: BackgroundTasks,
    db: DbSession,
) -> SessionUser:
    email = payload.email.strip().lower()
    user = User(email=email, display_name=payload.display_name, role="PARENT")
    db.add(user)
    try:
        db.flush()
        db.add(UserCredential(user_id=user.id, password_hash=_passwords.hash(payload.password)))
        accepted_at = datetime.now(UTC)
        db.add(
            ParentProfile(
                user_id=user.id,
                subscription_tier="free",
                max_students=1,
                parent_pin_hash=_passwords.hash(payload.parent_pin),
                coppa_consent_given=True,
                consent_timestamp=accepted_at,
                terms_accepted_at=accepted_at,
                approval_status=initial_approval_status(),
            )
        )
        token, _ = create_session(db, user.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Do not expose whether an account exists.
        raise HTTPException(status_code=400, detail="Unable to create account") from exc
    _set_session_cookie(response, token)
    if settings.require_family_approval:
        notification = new_family_notification(user.email, user.display_name)
        if notification is not None:
            background.add_task(send_email, notification)
    return _session_user(db, user)


@router.post("/login", response_model=SessionUser)
def login(payload: LoginRequest, response: Response, db: DbSession) -> SessionUser:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    credential = db.get(UserCredential, user.id) if user is not None else None
    if credential is None:
        # Perform an Argon2 operation on the unknown-account path to reduce timing leakage.
        _passwords.hash(payload.password)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    try:
        valid = _passwords.verify(credential.password_hash, payload.password)
    except VerificationError:
        valid = False
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token, _ = create_session(db, user.id)
    db.commit()
    _set_session_cookie(response, token)
    return _session_user(db, user)


@router.get("/me", response_model=SessionUser)
def me(user: CurrentUser, db: DbSession) -> SessionUser:
    """Who is signed in — deliberately ungated so pending families can see their status."""
    return _session_user(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: DbSession) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        revoke_session(db, token)
        db.commit()
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )
