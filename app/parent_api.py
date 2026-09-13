import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.identity import CurrentParent, CurrentUser, require_parent_role
from app.parent_models import ParentProfile
from app.parent_schemas import (
    ChildDashboardOut,
    ChildSummaryOut,
    LinkChildIn,
    LinkChildOut,
    ParentProfileOut,
)
from app.services.parent_dashboard import (
    dashboard,
    link_child_with_claim,
    list_children,
    unlink_child,
)

router = APIRouter(prefix="/parents", tags=["parents"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/profile", response_model=ParentProfileOut)
def create_or_load_profile(user: CurrentUser, db: DbSession) -> ParentProfileOut:
    require_parent_role(user)
    parent = db.scalar(select(ParentProfile).where(ParentProfile.user_id == user.id))
    if parent is None:
        parent = ParentProfile(user_id=user.id)
        db.add(parent)
        db.commit()
        db.refresh(parent)
    return ParentProfileOut(
        id=parent.id,
        user_id=user.id,
        display_name=user.display_name,
        email=user.email,
    )


@router.get("/profile", response_model=ParentProfileOut)
def get_profile(user: CurrentUser, parent: CurrentParent) -> ParentProfileOut:
    return ParentProfileOut(
        id=parent.id,
        user_id=user.id,
        display_name=user.display_name,
        email=user.email,
    )


@router.get("/children", response_model=list[ChildSummaryOut])
def get_children(parent: CurrentParent, db: DbSession) -> list[ChildSummaryOut]:
    return list_children(db, parent=parent)


@router.post("/children/link", response_model=LinkChildOut)
def link_child(payload: LinkChildIn, parent: CurrentParent, db: DbSession) -> LinkChildOut:
    result = link_child_with_claim(db, parent=parent, claim_token=payload.claim_token)
    db.commit()
    return result


@router.delete("/children/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_child(student_id: uuid.UUID, parent: CurrentParent, db: DbSession) -> Response:
    unlink_child(db, parent=parent, student_id=student_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/children/{student_id}/dashboard", response_model=ChildDashboardOut)
def child_dashboard(
    student_id: uuid.UUID, parent: CurrentParent, db: DbSession
) -> ChildDashboardOut:
    return dashboard(db, parent=parent, student_id=student_id)
