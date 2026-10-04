import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.settings import settings
from app.identity import CurrentParent
from app.models import Student
from app.parent_models import FamilyPracticePass, LearnerPassSession, ParentStudentRelationship
from app.services.parent_gate import require_parent_unlock

# These models live here (rather than parent_models) so legacy test/bootstrap code
# that creates Base.metadata before Alembic does not pre-create the new tables.
# Alembic owns their lifecycle in deployed environments.
router = APIRouter(prefix="/practice-pass", tags=["practice-pass"])
DbSession = Annotated[Session, Depends(get_db)]
LEARNER_COOKIE = "ai_tutor_learner"
PASS_TTL = timedelta(days=7)
LEARNER_SESSION_TTL = timedelta(days=30)

def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

class PracticePassOut(BaseModel):
    url: str
    expires_at: datetime
    student_id: uuid.UUID

class ActivateIn(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    nickname: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")

class ActivateOut(BaseModel):
    student_id: uuid.UUID
    nickname: str

def _set_learner_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        LEARNER_COOKIE, token, max_age=int(LEARNER_SESSION_TTL.total_seconds()),
        httponly=True, secure=settings.session_cookie_secure, samesite="lax", path="/",
    )

@router.post("", response_model=PracticePassOut)
def generate_pass(request: Request, parent: CurrentParent, db: DbSession) -> PracticePassOut:
    require_parent_unlock(request, parent.user_id)
    student_ids = list(db.scalars(
        select(ParentStudentRelationship.student_id).where(
            ParentStudentRelationship.parent_profile_id == parent.id,
            ParentStudentRelationship.active.is_(True),
        )
    ))
    if len(student_ids) != 1:
        raise HTTPException(status_code=409, detail="Pilot practice pass requires exactly one active learner")
    now = datetime.now(UTC)
    existing = db.scalar(select(FamilyPracticePass).where(FamilyPracticePass.parent_profile_id == parent.id))
    if existing is not None:
        existing.revoked_at = now
        db.execute(delete(LearnerPassSession).where(LearnerPassSession.practice_pass_id == existing.id))
        db.delete(existing)
        db.flush()
    raw = secrets.token_urlsafe(32)
    practice_pass = FamilyPracticePass(
        parent_profile_id=parent.id, student_id=student_ids[0],
        token_hash=_digest(raw), expires_at=now + PASS_TTL,
    )
    db.add(practice_pass)
    db.commit()
    return PracticePassOut(url=f"/practice/{raw}", expires_at=practice_pass.expires_at, student_id=practice_pass.student_id)

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def revoke_pass(request: Request, parent: CurrentParent, db: DbSession) -> Response:
    require_parent_unlock(request, parent.user_id)
    practice_pass = db.scalar(select(FamilyPracticePass).where(FamilyPracticePass.parent_profile_id == parent.id))
    if practice_pass is not None:
        practice_pass.revoked_at = datetime.now(UTC)
        db.execute(delete(LearnerPassSession).where(LearnerPassSession.practice_pass_id == practice_pass.id))
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/activate", response_model=ActivateOut)
def activate(payload: ActivateIn, response: Response, db: DbSession) -> ActivateOut:
    now = datetime.now(UTC)
    practice_pass = db.scalar(select(FamilyPracticePass).where(FamilyPracticePass.token_hash == _digest(payload.token)))
    if practice_pass is None or practice_pass.revoked_at is not None or practice_pass.expires_at <= now:
        raise HTTPException(status_code=401, detail="Practice pass is invalid or expired")
    student = db.get(Student, practice_pass.student_id)
    if student is None or not student.active:
        raise HTTPException(status_code=401, detail="Practice pass is invalid or expired")
    # Nickname is deliberately minimized display data; never ask for a legal name.
    student.first_name = payload.nickname.strip()
    raw_session = secrets.token_urlsafe(32)
    learner_session = LearnerPassSession(
        practice_pass_id=practice_pass.id, student_id=student.id,
        token_hash=_digest(raw_session), expires_at=now + LEARNER_SESSION_TTL,
    )
    db.add(learner_session)
    db.commit()
    _set_learner_cookie(response, raw_session)
    return ActivateOut(student_id=student.id, nickname=student.first_name)
