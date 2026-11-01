"""Synthetic current-recovery discovery tests; never access learner data."""
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app import adaptive_response_api as api


class FakeDB:
    def __init__(self, session, ids):
        self.session = session
        self.ids = ids

    def get(self, _model, _key):
        return self.session

    def scalars(self, _query):
        return self.ids


@pytest.fixture
def context(monkeypatch):
    session = SimpleNamespace(
        id=uuid4(), student_id=uuid4(), active_skill_id=uuid4(),
        primary_skill_id=uuid4(),
    )
    monkeypatch.setattr(api, "require_learning_owns_session", lambda db, access, s: s)
    monkeypatch.setattr(api, "require_session_scope", lambda db, s: object())
    monkeypatch.setattr(api, "require_skill_in_scope", lambda *args, **kwargs: None)
    return session


def test_completed_old_journey_does_not_block_new_recovery(monkeypatch, context):
    old, new = uuid4(), uuid4()
    monkeypatch.setattr(api, "published_recovery_state", lambda **kwargs: {
        "stage": "COMPLETE_FEEDBACK_ONLY" if kwargs["problem_id"] == old else "GUIDED_RETEST",
        "independent_evidence_eligible": False, "mastery_eligible": False,
    })
    result = api.discover_published_recovery(
        context.id, access=object(), db=FakeDB(context, [old, new])
    )
    assert result["problem_id"] == new
    assert result["stage"] == "GUIDED_RETEST"


def test_two_unfinished_journeys_fail_closed(monkeypatch, context):
    monkeypatch.setattr(api, "published_recovery_state", lambda **kwargs: {
        "stage": "GUIDED_RETEST", "independent_evidence_eligible": False,
    })
    with pytest.raises(HTTPException) as error:
        api.discover_published_recovery(
            context.id, access=object(), db=FakeDB(context, [uuid4(), uuid4()])
        )
    assert error.value.status_code == 409


def test_no_candidate_is_no_credit(monkeypatch, context):
    result = api.discover_published_recovery(context.id, access=object(), db=FakeDB(context, []))
    assert result == {
        "stage": "NONE", "independent_evidence_eligible": False, "mastery_eligible": False
    }


def test_revoked_candidate_denial_is_not_suppressed(monkeypatch, context):
    def revoked(**kwargs):
        raise HTTPException(409, "Publication revoked")
    monkeypatch.setattr(api, "published_recovery_state", revoked)
    with pytest.raises(HTTPException) as error:
        api.discover_published_recovery(
            context.id, access=object(), db=FakeDB(context, [uuid4()])
        )
    assert error.value.status_code == 409
