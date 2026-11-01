"""Authorization regression for published recovery after learner deactivation.

The backend must deny an old ACTIVE tutor session if the learner is deactivated.
"""
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.identity import require_learning_owns_session


@pytest.mark.parametrize("inactive", [True, False])
def test_revoked_or_unowned_learner_cannot_resume_active_session(inactive):
    owner, outsider = uuid4(), uuid4()
    student_id, session_id = uuid4(), uuid4()
    student = SimpleNamespace(
        id=student_id,
        parent_id=owner if inactive else outsider,
        active=not inactive,
    )
    session = SimpleNamespace(
        id=session_id, student_id=student_id, status="ACTIVE",
    )
    db = SimpleNamespace(get=lambda model, key: student)
    parent = SimpleNamespace(user_id=owner)
    with pytest.raises(HTTPException) as error:
        require_learning_owns_session(db, SimpleNamespace(
            parent=parent, learner_id=None,
        ), session)
    assert error.value.status_code == 404


def test_owned_active_learner_can_resume_owned_active_session():
    owner, student_id, session_id = uuid4(), uuid4(), uuid4()
    student = SimpleNamespace(id=student_id, parent_id=owner, active=True)
    session = SimpleNamespace(
        id=session_id, student_id=student_id, status="ACTIVE",
    )
    db = SimpleNamespace(get=lambda model, key: student)
    parent = SimpleNamespace(user_id=owner)
    assert require_learning_owns_session(db, SimpleNamespace(
        parent=parent, learner_id=student_id,
    ), session) is session


def test_revoked_session_denied_even_for_active_owned_learner():
    owner, student_id = uuid4(), uuid4()
    student = SimpleNamespace(id=student_id, parent_id=owner, active=True)
    db = SimpleNamespace(get=lambda model, key: student)
    session = SimpleNamespace(student_id=student_id, status="CLOSED")
    with pytest.raises(HTTPException) as error:
        require_learning_owns_session(db, SimpleNamespace(
            parent=SimpleNamespace(user_id=owner), learner_id=student_id,
        ), session)
    assert error.value.status_code == 404
