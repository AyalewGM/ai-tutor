from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import SESSION_COOKIE, create_session, revoke_session
from app.core.database import get_db
from app.core.settings import settings
from app.credential_models import UserCredential
from app.models import User
from app.parent_models import ParentProfile

router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]
_passwords = PasswordHasher()


class ParentRegistration(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class SessionUser(BaseModel):
    id: str
    role: str
    display_name: str | None


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
def register_parent(payload: ParentRegistration, response: Response, db: DbSession) -> SessionUser:
    email = payload.email.strip().lower()
    user = User(email=email, display_name=payload.display_name, role="PARENT")
    db.add(user)
    try:
        db.flush()
        db.add(UserCredential(user_id=user.id, password_hash=_passwords.hash(payload.password)))
        db.add(ParentProfile(user_id=user.id))
        token, _ = create_session(db, user.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Do not expose whether an account exists.
        raise HTTPException(status_code=400, detail="Unable to create account") from exc
    _set_session_cookie(response, token)
    return SessionUser(id=str(user.id), role=user.role, display_name=user.display_name)


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
    return SessionUser(id=str(user.id), role=user.role, display_name=user.display_name)


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
