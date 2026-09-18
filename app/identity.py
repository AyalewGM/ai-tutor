import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Student, TutorSession, User
from app.parent_models import ParentProfile

DbSession = Annotated[Session, Depends(get_db)]


def current_user(request: Request, db: DbSession) -> User:
    """Resolve identity established by trusted authentication middleware."""
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


def require_parent_owns_student(parent: ParentProfile, student: Student | None) -> Student:
    """Fail closed without disclosing whether another family's learner exists."""
    if student is None or student.parent_id != parent.user_id:
        raise HTTPException(status_code=404, detail="Learner not found")
    return student


def require_parent_owns_session(
    db: Session, parent: ParentProfile, session: TutorSession | None
) -> TutorSession:
    """Authorize a tutor session through its server-side learner relationship."""
    if session is None or session.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Active tutor session not found")
    require_parent_owns_student(parent, db.get(Student, session.student_id))
    return session
