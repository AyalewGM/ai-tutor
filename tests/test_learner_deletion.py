import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.learner_deletion import erase_learner_transactional
from app.privacy_api import LearnerDeletionConfirmationIn, delete_learner_data


class ScalarRows:
    def __init__(self, values):
        self.values = values

    def __iter__(self):
        return iter(self.values)


class FakeDeletionDb:
    def __init__(self, *, learner, relationship, scalar_lists=None, fail_execute_at=None):
        self.learner = learner
        self.relationship = relationship
        self.scalar_lists = list(scalar_lists or [[], [], [], []])
        self.fail_execute_at = fail_execute_at
        self.execute_count = 0
        self.commits = 0
        self.rollbacks = 0

    def scalar(self, _query):
        return self.relationship

    def get(self, _model, learner_id):
        return self.learner if self.learner and self.learner.id == learner_id else None

    def scalars(self, _query):
        return ScalarRows(self.scalar_lists.pop(0))

    def execute(self, _statement):
        self.execute_count += 1
        if self.fail_execute_at == self.execute_count:
            raise RuntimeError("synthetic deletion failure")
        return SimpleNamespace(rowcount=1)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _family():
    user_id = uuid.uuid4()
    parent = SimpleNamespace(id=uuid.uuid4(), user_id=user_id)
    learner = SimpleNamespace(id=uuid.uuid4(), parent_id=user_id)
    relationship = SimpleNamespace(
        id=uuid.uuid4(),
        parent_profile_id=parent.id,
        student_id=learner.id,
        active=True,
    )
    return parent, learner, relationship


def test_cross_family_identifier_substitution_fails_before_mutation():
    parent, learner, _relationship = _family()
    unrelated_relationship = None
    db = FakeDeletionDb(learner=learner, relationship=unrelated_relationship)

    with pytest.raises(HTTPException) as exc:
        erase_learner_transactional(db, parent=parent, learner_id=learner.id)

    assert exc.value.status_code == 404
    assert db.execute_count == 0
    assert db.commits == 0


def test_transactional_service_does_not_commit_itself():
    parent, learner, relationship = _family()
    db = FakeDeletionDb(
        learner=learner,
        relationship=relationship,
        scalar_lists=[[relationship.id], [], [], []],
    )

    result = erase_learner_transactional(db, parent=parent, learner_id=learner.id)

    assert result.learner_id == learner.id
    assert db.execute_count > 0
    assert db.commits == 0
    assert db.rollbacks == 0


def test_api_requires_explicit_confirmation_before_mutation():
    parent, learner, relationship = _family()
    db = FakeDeletionDb(learner=learner, relationship=relationship)

    with pytest.raises(HTTPException) as exc:
        delete_learner_data(
            learner.id,
            LearnerDeletionConfirmationIn(confirmation="delete"),
            parent,
            db,
        )

    assert exc.value.status_code == 400
    assert db.execute_count == 0
    assert db.commits == 0


def test_api_commits_only_after_complete_service():
    parent, learner, relationship = _family()
    db = FakeDeletionDb(
        learner=learner,
        relationship=relationship,
        scalar_lists=[[relationship.id], [], [], []],
    )

    result = delete_learner_data(
        learner.id,
        LearnerDeletionConfirmationIn(confirmation="DELETE"),
        parent,
        db,
    )

    assert result.status == "DELETED"
    assert result.learner_id == learner.id
    assert db.commits == 1
    assert db.rollbacks == 0


def test_failure_rolls_back_and_never_commits():
    parent, learner, relationship = _family()
    db = FakeDeletionDb(
        learner=learner,
        relationship=relationship,
        scalar_lists=[[relationship.id], [], [], []],
        fail_execute_at=4,
    )

    with pytest.raises(RuntimeError, match="synthetic deletion failure"):
        delete_learner_data(
            learner.id,
            LearnerDeletionConfirmationIn(confirmation="DELETE"),
            parent,
            db,
        )

    assert db.commits == 0
    assert db.rollbacks == 1
