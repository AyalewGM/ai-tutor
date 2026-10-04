import uuid

import pytest
from fastapi import HTTPException

from app.curriculum_models import StudentCurriculumEnrollment
from app.models import Curriculum, Student
from app.onboarding_api import LearnerCreate, create_learner
from app.parent_models import (
    ParentProfile,
    ParentStudentRelationship,
    ParentStudentRelationshipEvent,
)


class OnboardingDb:
    def __init__(self, curriculum, parent, active_relationships=0):
        self.curriculum = curriculum
        self.parent = parent
        self.added = []
        self.committed = False
        self.scalar_calls = 0
        self.active_relationships = active_relationships

    def scalar(self, _query):
        self.scalar_calls += 1
        return self.parent if self.scalar_calls == 1 else self.active_relationships

    def scalars(self, _query):
        # No plans visible to this mock: upgrade_target resolves None.
        class _Result:
            def first(self):
                return None

            def all(self):
                return []

        return _Result()

    def get(self, model, key):
        if model is Curriculum and self.curriculum is not None and self.curriculum.id == key:
            return self.curriculum
        return None

    def add(self, value):
        self.added.append(value)

    def flush(self):
        for value in self.added:
            if isinstance(value, (Student, ParentStudentRelationship)) and value.id is None:
                value.id = uuid.uuid4()

    def commit(self):
        self.committed = True


def _curriculum(*, active=True):
    return Curriculum(
        id=uuid.uuid4(),
        code="SYNTH-G9-MATH",
        name="Synthetic Grade 9 Math",
        jurisdiction="SYNTHETIC",
        grade_level="9",
        version="2026-test",
        active=active,
    )


def test_parent_owned_learner_preserves_exact_curriculum_identity():
    parent_user_id = uuid.uuid4()
    parent = ParentProfile(id=uuid.uuid4(), user_id=parent_user_id)
    curriculum = _curriculum()
    db = OnboardingDb(curriculum, parent)

    result = create_learner(
        LearnerCreate(first_name="SyntheticLearner", curriculum_id=curriculum.id), parent, db
    )

    student = next(value for value in db.added if isinstance(value, Student))
    enrollment = next(value for value in db.added if isinstance(value, StudentCurriculumEnrollment))
    relationship = next(value for value in db.added if isinstance(value, ParentStudentRelationship))
    relationship_event = next(
        value for value in db.added if isinstance(value, ParentStudentRelationshipEvent)
    )
    assert student.parent_id == parent_user_id
    assert student.curriculum_id == curriculum.id
    assert student.grade_level == curriculum.grade_level
    assert enrollment.student_id == student.id
    assert enrollment.curriculum_id == curriculum.id
    assert relationship.parent_profile_id == parent.id
    assert relationship.student_id == student.id
    assert relationship.relationship_type == "GUARDIAN"
    assert relationship.active is True
    assert relationship_event.relationship_id == relationship.id
    assert relationship_event.action == "LINKED"
    assert result.curriculum_id == curriculum.id
    assert result.curriculum_code == curriculum.code
    assert result.curriculum_version == curriculum.version
    assert result.jurisdiction == curriculum.jurisdiction
    assert db.committed


@pytest.mark.parametrize("curriculum", [None, _curriculum(active=False)])
def test_unknown_or_inactive_curriculum_is_rejected(curriculum):
    parent = ParentProfile(id=uuid.uuid4(), user_id=uuid.uuid4())
    requested_id = curriculum.id if curriculum is not None else uuid.uuid4()
    db = OnboardingDb(curriculum, parent)

    with pytest.raises(HTTPException) as exc_info:
        create_learner(
            LearnerCreate(first_name="SyntheticLearner", curriculum_id=requested_id), parent, db
        )

    assert exc_info.value.status_code == 404
    assert db.added == []
    assert not db.committed


def test_learner_avatar_choice_is_persisted():
    parent = ParentProfile(id=uuid.uuid4(), user_id=uuid.uuid4())
    curriculum = _curriculum()
    db = OnboardingDb(curriculum, parent)

    result = create_learner(
        LearnerCreate(
            first_name="AvatarKid",
            curriculum_id=curriculum.id,
            avatar_id="avatar-5",
        ),
        parent,
        db,
    )

    student = next(value for value in db.added if isinstance(value, Student))
    assert student.avatar_id == "avatar-5"
    assert result.avatar_id == "avatar-5"


def test_unknown_avatar_is_rejected():
    parent = ParentProfile(id=uuid.uuid4(), user_id=uuid.uuid4())
    curriculum = _curriculum()
    db = OnboardingDb(curriculum, parent)

    with pytest.raises(HTTPException) as exc_info:
        create_learner(
            LearnerCreate(
                first_name="AvatarKid",
                curriculum_id=curriculum.id,
                avatar_id="avatar-999",
            ),
            parent,
            db,
        )

    assert exc_info.value.status_code == 422
    assert db.added == []
    assert not db.committed


def test_free_parent_cannot_create_second_learner() -> None:
    parent = ParentProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        subscription_tier="free",
        max_students=1,
    )
    curriculum = _curriculum()
    db = OnboardingDb(curriculum, parent, active_relationships=1)

    with pytest.raises(HTTPException) as exc_info:
        create_learner(
            LearnerCreate(first_name="SecondLearner", curriculum_id=curriculum.id),
            parent,
            db,
        )

    assert exc_info.value.status_code == 402
    assert exc_info.value.detail["code"] == "STUDENT_SEAT_LIMIT_REACHED"
    assert exc_info.value.detail["max_students"] == 1
    assert db.added == []
