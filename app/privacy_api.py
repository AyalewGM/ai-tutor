import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.identity import CurrentUser, require_parent_role
from app.privacy_models import PrivacyNoticeAcknowledgement

router = APIRouter(prefix="/privacy", tags=["privacy"])
DbSession = Annotated[Session, Depends(get_db)]

CURRENT_NOTICE_VERSION = "pilot-privacy-v1"
CURRENT_NOTICE_TITLE = "Private pilot privacy notice"
CURRENT_NOTICE_SUMMARY = (
    "We use the minimum family and learning data needed to provide the private AI Tutor pilot, "
    "keep curriculum-specific progress, secure parent access, and operate the service. "
    "We do not use learner data for advertising or session replay. Tutoring decisions, mastery, "
    "and curriculum identity remain application-controlled. Acknowledging this notice records only "
    "your account, the notice version, and the acknowledgement time; it is not represented as "
    "verifiable parental consent."
)


class PrivacyNoticeOut(BaseModel):
    version: str
    title: str
    summary: str
    acknowledged: bool
    acknowledged_at: datetime | None = None


class PrivacyNoticeAcknowledgementIn(BaseModel):
    notice_version: str


def _existing_acknowledgement(
    db: Session, *, user_id: uuid.UUID
) -> PrivacyNoticeAcknowledgement | None:
    return db.scalar(
        select(PrivacyNoticeAcknowledgement).where(
            PrivacyNoticeAcknowledgement.user_id == user_id,
            PrivacyNoticeAcknowledgement.notice_version == CURRENT_NOTICE_VERSION,
        )
    )


def _notice_out(ack: PrivacyNoticeAcknowledgement | None) -> PrivacyNoticeOut:
    return PrivacyNoticeOut(
        version=CURRENT_NOTICE_VERSION,
        title=CURRENT_NOTICE_TITLE,
        summary=CURRENT_NOTICE_SUMMARY,
        acknowledged=ack is not None,
        acknowledged_at=ack.acknowledged_at if ack is not None else None,
    )


@router.get("/notice", response_model=PrivacyNoticeOut)
def get_current_notice(user: CurrentUser, db: DbSession) -> PrivacyNoticeOut:
    require_parent_role(user)
    return _notice_out(_existing_acknowledgement(db, user_id=user.id))


@router.post("/notice/acknowledge", response_model=PrivacyNoticeOut)
def acknowledge_current_notice(
    payload: PrivacyNoticeAcknowledgementIn,
    user: CurrentUser,
    db: DbSession,
) -> PrivacyNoticeOut:
    require_parent_role(user)
    if payload.notice_version != CURRENT_NOTICE_VERSION:
        raise HTTPException(status_code=409, detail="Privacy notice version is no longer current")

    acknowledgement = _existing_acknowledgement(db, user_id=user.id)
    if acknowledgement is None:
        acknowledgement = PrivacyNoticeAcknowledgement(
            user_id=user.id,
            notice_version=CURRENT_NOTICE_VERSION,
        )
        db.add(acknowledgement)
        db.commit()
        db.refresh(acknowledgement)
    return _notice_out(acknowledgement)
