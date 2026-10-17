import hashlib
from datetime import UTC, datetime, timedelta
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
from app.identity import CurrentUser
from app.models import User
from app.onboarding_api import regions_catalog
from app.parent_models import (
    APPROVAL_APPROVED,
    ParentInvitation,
    ParentProfile,
    PilotEntitlement,
)
from app.parent_schemas import RegionsOut
from app.schemas import ParentRegisterSchema
from app.services.auth_security import (
    clear_login_failures,
    client_ip,
    enforce_login_rate_limit,
    enforce_register_rate_limit,
    ensure_not_locked_out,
    record_login_failure,
)
from app.services.email import new_family_notification, send_email
from app.services.regions import valid_region
from app.services.turnstile import verify_turnstile

router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]
_passwords = PasswordHasher()


ParentRegistration = ParentRegisterSchema


def _invitation_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _resolve_invitation(db: Session, payload: ParentRegistration) -> ParentInvitation:
    """Invite-only gate: resolve a pending, unexpired, email-scoped
    invitation or deny generically — no existence/scope disclosure."""
    generic = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Registration requires a valid invitation",
    )
    if not payload.invitation_token:
        raise generic
    invitation = db.scalar(
        select(ParentInvitation).where(
            ParentInvitation.token_hash == _invitation_digest(payload.invitation_token)
        )
    )
    if (
        invitation is None
        or invitation.status != "PENDING"
        or invitation.expires_at <= datetime.now(UTC)
        or (invitation.email is not None
            and invitation.email.lower() != payload.email.strip().lower())
    ):
        raise generic
    return invitation


def _consume_invitation(
    db: Session, *, invitation: ParentInvitation, parent: ParentProfile, now: datetime
) -> None:
    """Single-use consumption + pilot seat grant, inside the registration
    transaction so a disabled invite can never mint an account."""
    invitation.status = "ACCEPTED"
    invitation.accepted_parent_profile_id = parent.id
    invitation.responded_at = now
    db.add(
        PilotEntitlement(
            parent_profile_id=parent.id,
            seats=invitation.seats or settings.pilot_invite_default_seats,
            source="INVITATION",
            invitation_id=invitation.id,
            starts_at=now,
            ends_at=now + timedelta(days=settings.pilot_entitlement_days),
        )
    )
    db.flush()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    turnstile_token: str | None = Field(default=None, max_length=2048)


class AuthConfigOut(BaseModel):
    # Public so the sign-in page can render the bot check before submit.
    turnstile_site_key: str | None = None


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
    request: Request,
    response: Response,
    background: BackgroundTasks,
    db: DbSession,
) -> SessionUser:
    enforce_register_rate_limit(request)
    verify_turnstile(payload.turnstile_token, client_ip(request))
    email = payload.email.strip().lower()
    country_code = payload.country_code.upper()
    region_code = payload.region_code.upper()
    if not valid_region(country_code, region_code):
        raise HTTPException(status_code=422, detail="Unknown country or region")
    invitation = _resolve_invitation(db, payload) if settings.pilot_invite_only else None
    user = User(email=email, display_name=payload.display_name, role="PARENT")
    db.add(user)
    try:
        db.flush()
        db.add(UserCredential(user_id=user.id, password_hash=_passwords.hash(payload.password)))
        accepted_at = datetime.now(UTC)
        parent = ParentProfile(
            user_id=user.id,
            subscription_tier="free",
            parent_pin_hash=_passwords.hash(payload.parent_pin),
            country_code=country_code,
            region_code=region_code,
            coppa_consent_given=True,
            consent_timestamp=accepted_at,
            terms_accepted_at=accepted_at,
            approval_status=APPROVAL_APPROVED,
        )
        db.add(parent)
        db.flush()
        if invitation is not None:
            _consume_invitation(db, invitation=invitation, parent=parent, now=accepted_at)
        token, _ = create_session(db, user.id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Do not expose whether an account exists.
        raise HTTPException(status_code=400, detail="Unable to create account") from exc
    _set_session_cookie(response, token)
    notification = new_family_notification(user.email, user.display_name)
    if notification is not None:
        background.add_task(send_email, notification)
    return _session_user(db, user)


@router.post("/login", response_model=SessionUser)
def login(
    payload: LoginRequest, request: Request, response: Response, db: DbSession
) -> SessionUser:
    enforce_login_rate_limit(request)
    verify_turnstile(payload.turnstile_token, client_ip(request))
    email = payload.email.strip().lower()
    # Generic 429 whether or not the account exists — no enumeration signal.
    ensure_not_locked_out(email)
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    credential = db.get(UserCredential, user.id) if user is not None else None
    if credential is None:
        # Perform an Argon2 operation on the unknown-account path to reduce timing leakage.
        _passwords.hash(payload.password)
        record_login_failure(email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    try:
        valid = _passwords.verify(credential.password_hash, payload.password)
    except VerificationError:
        valid = False
    if not valid:
        record_login_failure(email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    clear_login_failures(email)
    token, _ = create_session(db, user.id)
    db.commit()
    _set_session_cookie(response, token)
    return _session_user(db, user)


@router.get("/config", response_model=AuthConfigOut)
def auth_config() -> AuthConfigOut:
    """Public auth-page config — only ever the site key, never the secret."""
    return AuthConfigOut(turnstile_site_key=settings.turnstile_site_key)


@router.get("/regions", response_model=RegionsOut)
def public_regions(db: DbSession) -> RegionsOut:
    """Country → state/province cascade for the registration form.

    Public because registration happens pre-auth; contains only static
    geography plus per-region curriculum coverage flags — no family data.
    """
    return RegionsOut(countries=regions_catalog(db), family=None)


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
