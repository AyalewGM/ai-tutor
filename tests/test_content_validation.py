import uuid

import pytest

from app.content_validation import (
    ContentValidationError,
    CurriculumScopedRef,
    validate_active_skill_traceability,
    validate_expectation_skill_mapping,
    validate_prerequisite_edge,
    validate_problem_inventory,
    validate_problem_scope,
)


def _ref(curriculum_id: uuid.UUID, *, object_id: uuid.UUID | None = None) -> CurriculumScopedRef:
    return CurriculumScopedRef(id=object_id or uuid.uuid4(), curriculum_id=curriculum_id)


def test_expectation_skill_mapping_accepts_same_curriculum():
    curriculum_id = uuid.uuid4()
    validate_expectation_skill_mapping(
        mapping_curriculum_id=curriculum_id,
        expectation=_ref(curriculum_id),
        skill=_ref(curriculum_id),
    )


def test_expectation_skill_mapping_rejects_cross_curriculum():
    curriculum_id = uuid.uuid4()
    other_curriculum_id = uuid.uuid4()
    with pytest.raises(ContentValidationError):
        validate_expectation_skill_mapping(
            mapping_curriculum_id=curriculum_id,
            expectation=_ref(curriculum_id),
            skill=_ref(other_curriculum_id),
        )


def test_prerequisite_edge_rejects_cross_curriculum_and_self_reference():
    curriculum_id = uuid.uuid4()
    other_curriculum_id = uuid.uuid4()
    skill = _ref(curriculum_id)

    with pytest.raises(ContentValidationError):
        validate_prerequisite_edge(
            skill=skill,
            prerequisite=_ref(other_curriculum_id),
        )

    with pytest.raises(ContentValidationError):
        validate_prerequisite_edge(skill=skill, prerequisite=skill)


def test_problem_scope_rejects_skill_from_other_curriculum():
    with pytest.raises(ContentValidationError):
        validate_problem_scope(
            pack_curriculum_id=uuid.uuid4(),
            primary_skill=_ref(uuid.uuid4()),
        )


def test_active_skill_requires_source_traceability():
    with pytest.raises(ContentValidationError):
        validate_active_skill_traceability(
            skill=_ref(uuid.uuid4()),
            mapped_expectation_count=0,
        )


def test_problem_inventory_uses_explicit_accepted_threshold():
    skill = _ref(uuid.uuid4())
    validate_problem_inventory(
        skill=skill,
        problem_count=5,
        minimum_required=5,
    )

    with pytest.raises(ContentValidationError):
        validate_problem_inventory(
            skill=skill,
            problem_count=4,
            minimum_required=5,
        )
