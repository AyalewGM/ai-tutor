import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.parent_models import ParentProfile

DbSession = Annotated[Session, Depends(get_db)]


def current_user(request: Request, db: DbSession) -> User:
    """Resolve identity established by trusted authentication middleware.

    Parent routes intentionally do not accept a caller-supplied user/parent UUID as
    authentication. Deployment-specific auth middleware must validate the external
    credential and set request.state.authenticated_user_id to the internal User UUID.
    Until such middleware is configured, protected routes fail closed with 401.
    """

    raw_user_id = getattr(request.state, "authenticated_user_id", None)
    if raw_user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        user_id = raw_user_id if isinstance(raw_user_id, uuid.UUID) else uuid.UUID(str(raw_user_id))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid authenticated identity") from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Authenticated user not found")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_parent_role(user: User) -> None:
    if user.role.upper() not in {"PARENT", "GUARDIAN"}:
        raise HTTPException(status_code=403, detail="Parent or guardian access required")


def current_parent(user: CurrentUser, db: DbSession) -> ParentProfile:
    require_parent_role(user)
    parent = db.scalar(select(ParentProfile).where(ParentProfile.user_id == user.id))
    if parent is None:
        raise HTTPException(status_code=404, detail="Parent profile not initialized")
    return parent


CurrentParent = Annotated[ParentProfile, Depends(current_parent)]
