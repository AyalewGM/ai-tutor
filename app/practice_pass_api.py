import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.settings import settings
from app.identity import CurrentParent
from app.models import Student
from app.parent_models import (
    FamilyPracticePass,
    LearnerPassSession,
    ParentStudentRelationship,
)
from app.services.auth_security import (
    enforce_practice_link_activation_limit,
    enforce_practice_pass_activation_limit,
)
from app.services.parent_gate import require_parent_unlock

router = APIRouter(prefix="/practice-pass", tags=["practice-pass"])
DbSession = Annotated[Session, Depends(get_db)]
LEARNER_COOKIE = "ai_tutor_learner"
PASS_TTL = timedelta(days=7)
LEARNER_SESSION_TTL = timedelta(days=30)


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class GenerateIn(BaseModel):
    # Which child the link binds to. When omitted, the legacy single-child
    # rule applies: the family must have exactly one active learner.
    student_id: uuid.UUID | None = None


class PracticePassOut(BaseModel):
    url: str
    expires_at: datetime
    student_id: uuid.UUID


class PracticePassSummary(BaseModel):
    student_id: uuid.UUID
    expires_at: datetime
    created_at: datetime


class PracticePassListOut(BaseModel):
    passes: list[PracticePassSummary]


class ActivateIn(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    # Optional display name for the learner session only; never written to
    # the canonical parent-managed learner record.
    nickname: str | None = Field(
        default=None, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$"
    )


class ActivateOut(BaseModel):
    student_id: uuid.UUID
    nickname: str | None


def _set_learner_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        LEARNER_COOKIE, token, max_age=int(LEARNER_SESSION_TTL.total_seconds()),
        httponly=True, secure=settings.session_cookie_secure, samesite="lax", path="/",
    )


def _active_relationship(
    db: Session, *, parent_id: uuid.UUID, student_id: uuid.UUID
) -> ParentStudentRelationship | None:
    return db.scalar(
        select(ParentStudentRelationship).where(
            ParentStudentRelationship.parent_profile_id == parent_id,
            ParentStudentRelationship.student_id == student_id,
            ParentStudentRelationship.active.is_(True),
        )
    )


def _resolve_target_student(
    db: Session, *, parent_id: uuid.UUID, student_id: uuid.UUID | None
) -> uuid.UUID:
    """Child for the operation: explicit id must be an active relationship;
    omitted falls back to the legacy exactly-one-active-learner rule."""
    if student_id is not None:
        if _active_relationship(db, parent_id=parent_id, student_id=student_id) is None:
            raise HTTPException(status_code=404, detail="Child not found")
        return student_id
    student_ids = list(db.scalars(
        select(ParentStudentRelationship.student_id).where(
            ParentStudentRelationship.parent_profile_id == parent_id,
            ParentStudentRelationship.active.is_(True),
        )
    ))
    if len(student_ids) != 1:
        raise HTTPException(
            status_code=409,
            detail="Choose a child before generating a practice link",
        )
    return student_ids[0]


def revoke_child_pass(db: Session, *, parent_id: uuid.UUID, student_id: uuid.UUID) -> None:
    """Revoke the pass and invalidate live sessions for one child only."""
    now = datetime.now(UTC)
    practice_pass = db.scalar(
        select(FamilyPracticePass).where(
            FamilyPracticePass.parent_profile_id == parent_id,
            FamilyPracticePass.student_id == student_id,
        )
    )
    if practice_pass is None:
        return
    practice_pass.revoked_at = now
    db.execute(
        delete(LearnerPassSession).where(
            LearnerPassSession.practice_pass_id == practice_pass.id
        )
    )


@router.get("", response_model=PracticePassListOut)
def list_passes(parent: CurrentParent, db: DbSession) -> PracticePassListOut:
    """Active passes per child — metadata only, never the token."""
    now = datetime.now(UTC)
    rows = db.scalars(
        select(FamilyPracticePass).where(
            FamilyPracticePass.parent_profile_id == parent.id,
            FamilyPracticePass.revoked_at.is_(None),
            FamilyPracticePass.expires_at > now,
        )
    )
    return PracticePassListOut(
        passes=[
            PracticePassSummary(
                student_id=r.student_id, expires_at=r.expires_at, created_at=r.created_at
            )
            for r in rows
        ]
    )


def _mint_pass(
    db: Session, *, parent_id: uuid.UUID, student_id: uuid.UUID, now: datetime
) -> PracticePassOut:
    """Regenerate a child pass: prior link and its live sessions die atomically."""
    existing = db.scalar(
        select(FamilyPracticePass).where(
            FamilyPracticePass.parent_profile_id == parent_id,
            FamilyPracticePass.student_id == student_id,
        )
    )
    if existing is not None:
        existing.revoked_at = now
        db.execute(
            delete(LearnerPassSession).where(
                LearnerPassSession.practice_pass_id == existing.id
            )
        )
        db.delete(existing)
        db.flush()
    raw = secrets.token_urlsafe(32)
    practice_pass = FamilyPracticePass(
        parent_profile_id=parent_id, student_id=student_id,
        token_hash=_digest(raw), expires_at=now + PASS_TTL,
    )
    db.add(practice_pass)
    db.flush()
    return PracticePassOut(
        url=f"/practice/{raw}",
        expires_at=practice_pass.expires_at,
        student_id=practice_pass.student_id,
    )


@router.post("", response_model=PracticePassOut)
def generate_pass(
    request: Request,
    parent: CurrentParent,
    db: DbSession,
    payload: GenerateIn | None = None,
) -> PracticePassOut:
    require_parent_unlock(request, parent.user_id)
    student_id = _resolve_target_student(
        db, parent_id=parent.id, student_id=(payload.student_id if payload else None)
    )
    out = _mint_pass(db, parent_id=parent.id, student_id=student_id, now=datetime.now(UTC))
    db.commit()
    return out


@router.post("/all", response_model=list[PracticePassOut])
def generate_all_passes(
    request: Request,
    parent: CurrentParent,
    db: DbSession,
) -> list[PracticePassOut]:
    """One link per active child — for sending each kid their own link at once.
    Regenerating semantics apply to every child at once."""
    require_parent_unlock(request, parent.user_id)
    student_ids = list(
        db.scalars(
            select(ParentStudentRelationship.student_id).where(
                ParentStudentRelationship.parent_profile_id == parent.id,
                ParentStudentRelationship.active.is_(True),
            )
        )
    )
    if not student_ids:
        raise HTTPException(status_code=409, detail="No active learners to link")
    now = datetime.now(UTC)
    out = [
        _mint_pass(db, parent_id=parent.id, student_id=student_id, now=now)
        for student_id in student_ids
    ]
    db.commit()
    return out


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def revoke_pass(
    request: Request,
    parent: CurrentParent,
    db: DbSession,
    student_id: Annotated[uuid.UUID | None, Query()] = None,
) -> Response:
    require_parent_unlock(request, parent.user_id)
    target = _resolve_target_student(db, parent_id=parent.id, student_id=student_id)
    revoke_child_pass(db, parent_id=parent.id, student_id=target)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/activate", response_model=ActivateOut)
def activate(
    payload: ActivateIn, request: Request, response: Response, db: DbSession
) -> ActivateOut:
    enforce_practice_link_activation_limit(request)
    now = datetime.now(UTC)
    practice_pass = db.scalar(select(FamilyPracticePass).where(FamilyPracticePass.token_hash == _digest(payload.token)))
    if practice_pass is None or practice_pass.revoked_at is not None or practice_pass.expires_at <= now:
        raise HTTPException(status_code=401, detail="Practice pass is invalid or expired")
    student = db.get(Student, practice_pass.student_id)
    if (
        student is None
        or not student.active
        or _active_relationship(
            db,
            parent_id=practice_pass.parent_profile_id,
            student_id=practice_pass.student_id,
        )
        is None
    ):
        raise HTTPException(status_code=401, detail="Practice pass is invalid or expired")
    enforce_practice_pass_activation_limit(practice_pass.token_hash)
    # One live session per link: a second activation (same device re-login or
    # a shared link) invalidates the previous session, so two people can never
    # use the same link concurrently — the newest activation wins.
    db.execute(
        delete(LearnerPassSession).where(
            LearnerPassSession.practice_pass_id == practice_pass.id
        )
    )
    raw_session = secrets.token_urlsafe(32)
    learner_session = LearnerPassSession(
        practice_pass_id=practice_pass.id, student_id=student.id,
        token_hash=_digest(raw_session), expires_at=now + LEARNER_SESSION_TTL,
        display_name=(payload.nickname.strip() if payload.nickname else None),
    )
    db.add(learner_session)
    db.commit()
    _set_learner_cookie(response, raw_session)
    # The bearer token lives in the URL until the SPA strips it; make sure
    # it can never leak to third parties via Referer on the way out.
    response.headers["Referrer-Policy"] = "no-referrer"
    return ActivateOut(
        student_id=student.id,
        nickname=learner_session.display_name or student.first_name,
    )
