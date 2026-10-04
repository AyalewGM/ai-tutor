"""Staff (admin) API.

Access model:
- Non-staff callers get 404 on every route, so the surface isn't discoverable.
- Staff must pass a TOTP second factor on the current session before any
  data route; only /me and the /mfa/* bootstrap routes work without it.
- Every state-changing staff action is written to admin_audit_events.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.admin_models import AdminAuditEvent, AdminMfa
from app.auth import SESSION_COOKIE, resolve_session
from app.auth_models import AuthSession
from app.core.database import get_db
from app.identity import CurrentUser
from app.models import User
from app.parent_models import (
    APPROVAL_APPROVED,
    APPROVAL_REJECTED,
    ParentProfile,
    ParentStudentRelationship,
)
from app.plan_models import Plan
from app.services import totp
from app.services.admin_security import (
    MfaNotConfigured,
    clear_mfa_attempts,
    decrypt_secret,
    encrypt_secret,
    record_admin_action,
    register_mfa_attempt,
)
from app.services.email import family_approved_email, family_rejected_email, send_email
from app.services.permissions import Permission, has_permission, permissions_for

router = APIRouter(prefix="/admin", tags=["admin"])
DbSession = Annotated[Session, Depends(get_db)]

MFA_REQUIRED = "MFA_REQUIRED"


def _staff_user(user: CurrentUser) -> User:
    if not has_permission(user.role, Permission.ADMIN_ACCESS):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return user


StaffUser = Annotated[User, Depends(_staff_user)]


def _staff_session(request: Request, user: StaffUser, db: DbSession) -> AuthSession:
    token = request.cookies.get(SESSION_COOKIE)
    session = resolve_session(db, token) if token else None
    if session is None or session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return session


StaffSession = Annotated[AuthSession, Depends(_staff_session)]


def require_staff(permission: Permission) -> Callable[..., User]:
    """Dependency: staff user holding ``permission`` on an MFA-verified session."""

    def dependency(user: StaffUser, session: StaffSession) -> User:
        if session.mfa_verified_at is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MFA_REQUIRED)
        if not has_permission(user.role, permission):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return user

    return dependency


class StaffMeOut(BaseModel):
    email: str
    role: str
    permissions: list[str]
    mfa_enrolled: bool
    mfa_verified: bool


class MfaSetupOut(BaseModel):
    secret: str
    otpauth_uri: str


class MfaCodeIn(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class AuditEventOut(BaseModel):
    id: uuid.UUID
    actor_label: str
    action: str
    target_type: str | None
    target_id: str | None
    before: dict | None
    after: dict | None
    created_at: datetime


def _mfa_row(db: Session, user: User) -> AdminMfa | None:
    return db.get(AdminMfa, user.id)


def _mfa_unavailable(exc: MfaNotConfigured) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Two-factor authentication is not configured on this server",
    )


@router.get("/me", response_model=StaffMeOut)
def staff_me(user: StaffUser, session: StaffSession, db: DbSession) -> StaffMeOut:
    mfa = _mfa_row(db, user)
    return StaffMeOut(
        email=user.email,
        role=user.role,
        permissions=sorted(permissions_for(user.role)),
        mfa_enrolled=bool(mfa and mfa.enabled_at),
        mfa_verified=session.mfa_verified_at is not None,
    )


@router.post("/mfa/setup", response_model=MfaSetupOut)
def mfa_setup(user: StaffUser, db: DbSession) -> MfaSetupOut:
    """Begin (or restart) enrollment. Refused once a factor is active —
    resetting an active factor is an operator action (make_admin --reset-mfa)."""
    mfa = _mfa_row(db, user)
    if mfa is not None and mfa.enabled_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Two-factor already enabled"
        )
    secret = totp.generate_secret()
    try:
        encrypted = encrypt_secret(secret)
    except MfaNotConfigured as exc:
        raise _mfa_unavailable(exc) from exc
    if mfa is None:
        db.add(AdminMfa(user_id=user.id, secret_encrypted=encrypted))
    else:
        mfa.secret_encrypted = encrypted
        mfa.last_used_step = None
    record_admin_action(
        db,
        actor_user_id=user.id,
        actor_label=user.email,
        action="mfa.setup_started",
        target_type="user",
        target_id=str(user.id),
    )
    db.commit()
    return MfaSetupOut(secret=secret, otpauth_uri=totp.provisioning_uri(secret, user.email))


def _check_code(user: User, mfa: AdminMfa, code: str) -> int:
    register_mfa_attempt(user.id)
    try:
        secret = decrypt_secret(mfa.secret_encrypted)
    except MfaNotConfigured as exc:
        raise _mfa_unavailable(exc) from exc
    step = totp.verify(secret, code, last_used_step=mfa.last_used_step)
    if step is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid code")
    clear_mfa_attempts(user.id)
    return step


@router.post("/mfa/confirm", response_model=StaffMeOut)
def mfa_confirm(
    payload: MfaCodeIn, user: StaffUser, session: StaffSession, db: DbSession
) -> StaffMeOut:
    """Finish enrollment with a first valid code; verifies this session too."""
    mfa = _mfa_row(db, user)
    if mfa is None or mfa.enabled_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No pending enrollment")
    step = _check_code(user, mfa, payload.code)
    now = datetime.now(UTC)
    mfa.enabled_at = now
    mfa.last_used_step = step
    session.mfa_verified_at = now
    record_admin_action(
        db,
        actor_user_id=user.id,
        actor_label=user.email,
        action="mfa.enabled",
        target_type="user",
        target_id=str(user.id),
    )
    db.commit()
    return staff_me(user, session, db)


@router.post("/mfa/verify", response_model=StaffMeOut)
def mfa_verify(
    payload: MfaCodeIn, user: StaffUser, session: StaffSession, db: DbSession
) -> StaffMeOut:
    """Second factor for a fresh sign-in."""
    mfa = _mfa_row(db, user)
    if mfa is None or mfa.enabled_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Two-factor not enrolled")
    mfa.last_used_step = _check_code(user, mfa, payload.code)
    session.mfa_verified_at = datetime.now(UTC)
    record_admin_action(
        db,
        actor_user_id=user.id,
        actor_label=user.email,
        action="admin.signed_in",
        target_type="user",
        target_id=str(user.id),
    )
    db.commit()
    return staff_me(user, session, db)


@router.get("/audit-log", response_model=list[AuditEventOut])
def audit_log(
    db: DbSession,
    _user: Annotated[User, Depends(require_staff(Permission.AUDIT_READ))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before: datetime | None = None,
) -> list[AuditEventOut]:
    stmt = select(AdminAuditEvent).order_by(AdminAuditEvent.created_at.desc()).limit(limit)
    if before is not None:
        stmt = stmt.where(AdminAuditEvent.created_at < before)
    return [
        AuditEventOut(
            id=e.id,
            actor_label=e.actor_label,
            action=e.action,
            target_type=e.target_type,
            target_id=e.target_id,
            before=e.before_json,
            after=e.after_json,
            created_at=e.created_at,
        )
        for e in db.scalars(stmt)
    ]


# ---------------------------------------------------------------------------
# Families: pilot approval queue
# ---------------------------------------------------------------------------


class FamilyOut(BaseModel):
    parent_profile_id: uuid.UUID
    email: str
    display_name: str | None
    approval_status: str
    registered_at: datetime
    decided_at: datetime | None
    rejection_reason: str | None
    learner_count: int


class RejectIn(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class FamilyAiLimitIn(BaseModel):
    daily_limit: int | None = Field(default=None, ge=0)


class PlanOut(BaseModel):
    model_config = {"from_attributes": True}

    code: str
    name: str
    monthly_price_usd: Decimal
    monthly_price_cad: int
    max_students: int
    ai_daily_generations: int
    stripe_price_id_usd: str | None
    stripe_price_id_cad: str | None
    active: bool
    updated_at: datetime


class PlanUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    monthly_price_usd: Decimal | None = Field(default=None, ge=0)
    monthly_price_cad: int | None = Field(default=None, ge=0)
    max_students: int | None = Field(default=None, ge=1)
    ai_daily_generations: int | None = Field(default=None, ge=0)
    stripe_price_id_usd: str | None = None
    stripe_price_id_cad: str | None = None
    active: bool | None = None


def _family_out(parent: ParentProfile, user: User, learner_count: int) -> FamilyOut:
    return FamilyOut(
        parent_profile_id=parent.id,
        email=user.email,
        display_name=user.display_name,
        approval_status=parent.approval_status,
        registered_at=parent.created_at,
        decided_at=parent.approval_decided_at,
        rejection_reason=parent.rejection_reason,
        learner_count=learner_count,
    )


def _learner_count(db: Session, parent: ParentProfile) -> int:
    return int(
        db.scalar(
            select(func.count(ParentStudentRelationship.id)).where(
                ParentStudentRelationship.parent_profile_id == parent.id,
                ParentStudentRelationship.active.is_(True),
            )
        )
        or 0
    )


@router.get("/families", response_model=list[FamilyOut])
def list_families(
    db: DbSession,
    _user: Annotated[User, Depends(require_staff(Permission.FAMILIES_READ))],
    approval_status: Annotated[
        str | None, Query(alias="status", pattern="^(PENDING|APPROVED|REJECTED)$")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[FamilyOut]:
    learners = (
        select(
            ParentStudentRelationship.parent_profile_id,
            func.count(ParentStudentRelationship.id).label("n"),
        )
        .where(ParentStudentRelationship.active.is_(True))
        .group_by(ParentStudentRelationship.parent_profile_id)
        .subquery()
    )
    stmt = (
        select(ParentProfile, User, func.coalesce(learners.c.n, 0))
        .join(User, User.id == ParentProfile.user_id)
        .outerjoin(learners, learners.c.parent_profile_id == ParentProfile.id)
        .order_by(ParentProfile.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if approval_status:
        stmt = stmt.where(ParentProfile.approval_status == approval_status)
    return [_family_out(parent, user, int(n)) for parent, user, n in db.execute(stmt)]


def _decide(
    db: Session,
    staff: User,
    parent_profile_id: uuid.UUID,
    new_status: str,
    reason: str | None,
) -> tuple[ParentProfile, User]:
    parent = db.get(ParentProfile, parent_profile_id)
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")
    if parent.approval_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Family is already {new_status}"
        )
    family_user = db.get(User, parent.user_id)
    before = {"approval_status": parent.approval_status}
    parent.approval_status = new_status
    parent.approval_decided_at = datetime.now(UTC)
    parent.approval_decided_by_user_id = staff.id
    parent.rejection_reason = reason if new_status == APPROVAL_REJECTED else None
    after = {"approval_status": new_status}
    if parent.rejection_reason:
        after["rejection_reason"] = parent.rejection_reason
    record_admin_action(
        db,
        actor_user_id=staff.id,
        actor_label=staff.email,
        action="family.approved" if new_status == APPROVAL_APPROVED else "family.rejected",
        target_type="parent_profile",
        target_id=str(parent.id),
        before=before,
        after=after,
    )
    db.commit()
    return parent, family_user


@router.post("/families/{parent_profile_id}/approve", response_model=FamilyOut)
def approve_family(
    parent_profile_id: uuid.UUID,
    background: BackgroundTasks,
    db: DbSession,
    staff: Annotated[User, Depends(require_staff(Permission.FAMILIES_APPROVE))],
) -> FamilyOut:
    parent, family_user = _decide(db, staff, parent_profile_id, APPROVAL_APPROVED, None)
    background.add_task(
        send_email, family_approved_email(family_user.email, family_user.display_name)
    )
    return _family_out(parent, family_user, _learner_count(db, parent))


@router.post("/families/{parent_profile_id}/reject", response_model=FamilyOut)
def reject_family(
    parent_profile_id: uuid.UUID,
    payload: RejectIn,
    background: BackgroundTasks,
    db: DbSession,
    staff: Annotated[User, Depends(require_staff(Permission.FAMILIES_APPROVE))],
) -> FamilyOut:
    reason = (payload.reason or "").strip() or None
    parent, family_user = _decide(db, staff, parent_profile_id, APPROVAL_REJECTED, reason)
    background.add_task(
        send_email,
        family_rejected_email(family_user.email, family_user.display_name, reason),
    )
    return _family_out(parent, family_user, _learner_count(db, parent))


@router.get("/ai-usage/summary")
def ai_usage_summary(
    db: DbSession,
    _user: Annotated[User, Depends(require_staff(Permission.AI_USAGE_READ))],
) -> dict:
    """Month-to-date AI generations, denials, and estimated spend by family."""
    from app.services.usage_metering import usage_summary

    return usage_summary(db)


@router.patch("/families/{parent_profile_id}/ai-limit", response_model=FamilyOut)
def set_family_ai_limit(
    parent_profile_id: uuid.UUID,
    payload: FamilyAiLimitIn,
    db: DbSession,
    staff: Annotated[User, Depends(require_staff(Permission.AI_BUDGETS_MANAGE))],
) -> FamilyOut:
    parent = db.get(ParentProfile, parent_profile_id)
    family_user = db.get(User, parent.user_id) if parent is not None else None
    if parent is None or family_user is None:
        raise HTTPException(404, "Family not found")
    before = parent.ai_daily_limit
    parent.ai_daily_limit = payload.daily_limit
    db.flush()
    record_admin_action(
        db,
        actor_user_id=staff.id,
        actor_label=staff.email,
        action="FAMILY_AI_LIMIT_SET",
        target_type="parent_profile",
        target_id=str(parent.id),
        before={"ai_daily_limit": before},
        after={"ai_daily_limit": payload.daily_limit},
    )
    db.commit()
    return _family_out(parent, family_user, _learner_count(db, parent))


class PlansAdminOut(BaseModel):
    usd_to_cad_rate: Decimal
    plans: list[PlanOut]


@router.get("/plans", response_model=PlansAdminOut)
def list_plans(
    db: DbSession,
    _user: Annotated[User, Depends(require_staff(Permission.METRICS_READ))],
) -> PlansAdminOut:
    from app.services.plans import stored_fx_rate

    rate, _computed_at = stored_fx_rate(db)
    return PlansAdminOut(
        usd_to_cad_rate=rate,
        plans=[
            PlanOut.model_validate(plan)
            for plan in db.scalars(select(Plan).order_by(Plan.monthly_price_usd, Plan.code)).all()
        ],
    )


@router.patch("/plans/{code}", response_model=PlanOut)
def update_plan(
    code: str,
    payload: PlanUpdateIn,
    db: DbSession,
    staff: Annotated[User, Depends(require_staff(Permission.PLANS_MANAGE))],
) -> PlanOut:
    """Update a plan. If ``monthly_price_usd`` changes without an explicit
    ``monthly_price_cad``, CAD is re-derived from the stored 3-yr-average rate
    (cents dropped)."""
    from app.services.plans import cad_for_usd

    plan = db.get(Plan, code)
    if plan is None:
        raise HTTPException(404, "Plan not found")
    before = PlanOut.model_validate(plan).model_dump(mode="json")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(plan, field, value)
    if "monthly_price_usd" in updates and "monthly_price_cad" not in updates:
        plan.monthly_price_cad = cad_for_usd(db, plan.monthly_price_usd)
    plan.updated_at = datetime.now(UTC)
    db.flush()
    record_admin_action(
        db,
        actor_user_id=staff.id,
        actor_label=staff.email,
        action="PLAN_UPDATED",
        target_type="plan",
        target_id=plan.code,
        before=before,
        after=PlanOut.model_validate(plan).model_dump(mode="json"),
    )
    db.commit()
    return PlanOut.model_validate(plan)


@router.post("/plans/recalc-cad")
def recalc_cad_prices(
    db: DbSession,
    staff: Annotated[User, Depends(require_staff(Permission.PLANS_MANAGE))],
) -> dict:
    """Fetch the Bank of Canada 3-year-average USD→CAD rate, store it, and
    re-price every plan's fixed CAD amount (whole dollars, cents dropped)."""
    import httpx

    from app.services.plans import recalculate_cad_prices

    try:
        result = recalculate_cad_prices(db)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, f"Bank of Canada rate fetch failed: {exc}") from exc
    record_admin_action(
        db,
        actor_user_id=staff.id,
        actor_label=staff.email,
        action="PLAN_CAD_RECALCULATED",
        target_type="platform_setting",
        target_id="usd_to_cad_3yr_avg",
        before=None,
        after=result,
    )
    db.commit()
    return result


class WindowCounts(BaseModel):
    d1: int = Field(alias="1d")
    d7: int = Field(alias="7d")
    d30: int = Field(alias="30d")


class SignupCounts(BaseModel):
    d1: int = Field(alias="1d")
    d7: int = Field(alias="7d")
    d30: int = Field(alias="30d")
    total: int


class SignupDay(BaseModel):
    date: str
    count: int


class MetricsOverviewOut(BaseModel):
    as_of: datetime
    active_learners: WindowCounts
    active_families: WindowCounts
    attempts: WindowCounts
    tutor_sessions: WindowCounts
    signups: SignupCounts
    signups_daily: list[SignupDay]
    learners_total: int


class RegionActivityOut(BaseModel):
    country_code: str
    region_code: str
    families: int
    active_learners: int
    attempts: int


class CurriculumActivityOut(BaseModel):
    code: str
    name: str
    learners_total: int
    active_learners: int
    attempts: int


@router.get("/metrics/overview", response_model=MetricsOverviewOut)
def metrics_overview(
    db: DbSession,
    _user: Annotated[User, Depends(require_staff(Permission.METRICS_READ))],
) -> MetricsOverviewOut:
    """DAU/WAU/MAU (learners and their families), sign-ups, and activity totals."""
    from app.services.metrics import overview

    return MetricsOverviewOut.model_validate(overview(db))


@router.get("/metrics/by-region", response_model=list[RegionActivityOut])
def metrics_by_region(
    db: DbSession,
    _user: Annotated[User, Depends(require_staff(Permission.METRICS_READ))],
) -> list[RegionActivityOut]:
    """30-day learning activity per family country/state (UNSET when unsaved)."""
    from app.services.metrics import activity_by_region

    return [RegionActivityOut.model_validate(row) for row in activity_by_region(db)]


@router.get("/metrics/by-curriculum", response_model=list[CurriculumActivityOut])
def metrics_by_curriculum(
    db: DbSession,
    _user: Annotated[User, Depends(require_staff(Permission.METRICS_READ))],
) -> list[CurriculumActivityOut]:
    """30-day attempts and active learners per practiced curriculum."""
    from app.services.metrics import activity_by_curriculum

    return [CurriculumActivityOut.model_validate(row) for row in activity_by_curriculum(db)]
