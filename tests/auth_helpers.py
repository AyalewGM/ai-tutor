from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import SESSION_COOKIE, create_session
from app.models import Student, User
from app.parent_models import ParentProfile


def authenticate_parent_for_student(client: TestClient, db: Session, student: Student) -> User:
    """Create a synthetic parent/session and bind the learner to that parent."""
    user = User(
        email=f"synthetic-parent-{student.id}@example.com",
        display_name="Synthetic Test Parent",
        role="PARENT",
    )
    db.add(user)
    db.flush()
    db.add(ParentProfile(user_id=user.id))
    student.parent_id = user.id
    token, _ = create_session(db, user.id)
    db.commit()
    client.cookies.set(SESSION_COOKIE, token)
    return user
