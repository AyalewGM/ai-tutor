import uuid

import pytest
from fastapi import HTTPException, Response

from app.identity import LearningAccess, require_learning_owns_student
from app.models import Student
from app.parent_models import ParentProfile
from app.practice_pass_api import _digest, _set_learner_cookie


def test_practice_pass_digest_does_not_store_bearer_token():
    raw = "synthetic-practice-pass-token-never-store-this"
    digest = _digest(raw)
    assert raw not in digest
    assert len(digest) == 64
    assert digest == _digest(raw)


def test_learner_cookie_is_http_only_and_scoped(monkeypatch):
    from app import practice_pass_api

    monkeypatch.setattr(practice_pass_api.settings, "session_cookie_secure", True)
    response = Response()
    _set_learner_cookie(response, "synthetic-learner-session")
    cookie = response.headers["set-cookie"]
    assert "ai_tutor_learner=" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=lax" in cookie


def test_learner_access_cannot_cross_to_sibling():
    parent_user_id = uuid.uuid4()
    parent = ParentProfile(id=uuid.uuid4(), user_id=parent_user_id)
    allowed = Student(
        id=uuid.uuid4(), parent_id=parent_user_id, first_name="PilotKid",
        grade_level="9", avatar_id="avatar-1", active=True,
    )
    sibling = Student(
        id=uuid.uuid4(), parent_id=parent_user_id, first_name="OtherKid",
        grade_level="8", avatar_id="avatar-1", active=True,
    )
    access = LearningAccess(parent=parent, learner_id=allowed.id)
    assert require_learning_owns_student(access, allowed).id == allowed.id
    with pytest.raises(HTTPException) as exc:
        require_learning_owns_student(access, sibling)
    assert exc.value.status_code == 404


@pytest.mark.parametrize("case", ["missing", "foreign", "inactive", "ended", "sibling"])
def test_session_denials_do_not_disclose_session_existence(case):
    from types import SimpleNamespace

    from app.identity import require_learning_owns_session
    from app.models import TutorSession

    owner = uuid.uuid4()
    parent = ParentProfile(id=uuid.uuid4(), user_id=owner)
    own = Student(id=uuid.uuid4(), parent_id=owner, first_name="SyntheticQA", grade_level="9", active=True)
    target = Student(id=uuid.uuid4(), parent_id=owner, first_name="SyntheticQA2", grade_level="9", active=True)
    if case == "foreign":
        target.parent_id = uuid.uuid4()
    if case == "inactive":
        target.active = False
    session = TutorSession(id=uuid.uuid4(), student_id=target.id, status="ENDED" if case == "ended" else "ACTIVE")
    db = SimpleNamespace(get=lambda _model, _identifier: target)
    access = LearningAccess(parent=parent, learner_id=own.id if case == "sibling" else None)
    with pytest.raises(HTTPException) as exc:
        require_learning_owns_session(db, access, None if case == "missing" else session)
    assert exc.value.status_code == 404
    assert exc.value.detail == "Active tutor session not found"


def test_session_owner_and_bound_learner_retain_access():
    from types import SimpleNamespace

    from app.identity import require_learning_owns_session
    from app.models import TutorSession

    owner = uuid.uuid4()
    parent = ParentProfile(id=uuid.uuid4(), user_id=owner)
    student = Student(id=uuid.uuid4(), parent_id=owner, first_name="SyntheticQA", grade_level="9", active=True)
    session = TutorSession(id=uuid.uuid4(), student_id=student.id, status="ACTIVE")
    db = SimpleNamespace(get=lambda _model, _identifier: student)
    for learner_id in (None, student.id):
        access = LearningAccess(parent=parent, learner_id=learner_id)
        assert require_learning_owns_session(db, access, session) is session
