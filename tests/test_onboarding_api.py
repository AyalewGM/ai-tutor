import uuid

import pytest
from fastapi import HTTPException

from app.curriculum_models import StudentCurriculumEnrollment
from app.models import Curriculum, Student
from app.onboarding_api import LearnerCreate, create_learner
from app.parent_models import ParentProfile


class OnboardingDb:
    def __init__(self, curriculum):
        self.curriculum = curriculum
        self.added = []
        self.committed = False

    def get(self, model, key):
        if model is Curriculum and self.curriculum is not None and self.curriculum.id == key:
            return self.curriculum
        return None

    def add(self, value):
        self.added.append(value)

    def flush(self):
        for value in self.added:
            if isinstance(value, Student) and value.id is None:
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
    db = OnboardingDb(curriculum)

    result = create_learner(
        LearnerCreate(first_name="Synthetic Learner", curriculum_id=curriculum.id), parent, db
    )

    student = next(value for value in db.added if isinstance(value, Student))
    enrollment = next(
        value for value in db.added if isinstance(value, StudentCurriculumEnrollment)
    )
    assert student.parent_id == parent_user_id
    assert student.curriculum_id == curriculum.id
    assert student.grade_level == curriculum.grade_level
    assert enrollment.student_id == student.id
    assert enrollment.curriculum_id == curriculum.id
    assert result.curriculum_id == curriculum.id
    assert result.curriculum_code == curriculum.code
    assert result.curriculum_version == curriculum.version
    assert result.jurisdiction == curriculum.jurisdiction
    assert db.committed


@pytest.mark.parametrize("curriculum", [None, _curriculum(active=False)])
def test_unknown_or_inactive_curriculum_is_rejected(curriculum):
    parent = ParentProfile(id=uuid.uuid4(), user_id=uuid.uuid4())
    requested_id = curriculum.id if curriculum is not None else uuid.uuid4()
    db = OnboardingDb(curriculum)

    with pytest.raises(HTTPException) as exc_info:
        create_learner(
            LearnerCreate(first_name="Synthetic Learner", curriculum_id=requested_id), parent, db
        )

    assert exc_info.value.status_code == 404
    assert db.added == []
    assert not db.committed
