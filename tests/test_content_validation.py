import uuid

import pytest

from app.content_validation import (
    ContentValidationError,
    CurriculumScopedRef,
    validate_active_skill_traceability,
    validate_expectation_skill_mapping,
    validate_fresh_problem_sets,
    validate_learning_mode_inventory,
    validate_prerequisite_edge,
    validate_problem_inventory,
    validate_problem_metadata,
    validate_problem_scope,
    validate_source_identity,
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


def test_problem_metadata_accepts_deterministic_mastery_problem():
    curriculum_id = uuid.uuid4()
    validate_problem_metadata(
        metadata_curriculum_id=curriculum_id,
        primary_skill=_ref(curriculum_id),
        objective="Solve a one-step linear equation",
        evaluation_type="EXACT_NUMERIC",
        diagnostic_eligible=False,
        guided_eligible=False,
        independent_eligible=True,
        mastery_eligible=True,
        llm_solution_required=False,
    )


def test_problem_metadata_rejects_cross_curriculum_or_orphan_mode():
    curriculum_id = uuid.uuid4()
    with pytest.raises(ContentValidationError, match="content-pack curriculum"):
        validate_problem_metadata(
            metadata_curriculum_id=curriculum_id,
            primary_skill=_ref(uuid.uuid4()),
            objective="Solve",
            evaluation_type="EXACT_NUMERIC",
            diagnostic_eligible=True,
            guided_eligible=False,
            independent_eligible=False,
            mastery_eligible=False,
            llm_solution_required=False,
        )

    with pytest.raises(ContentValidationError, match="at least one learning mode"):
        validate_problem_metadata(
            metadata_curriculum_id=curriculum_id,
            primary_skill=_ref(curriculum_id),
            objective="Solve",
            evaluation_type="EXACT_NUMERIC",
            diagnostic_eligible=False,
            guided_eligible=False,
            independent_eligible=False,
            mastery_eligible=False,
            llm_solution_required=False,
        )


def test_problem_metadata_rejects_llm_required_assessment_problem():
    curriculum_id = uuid.uuid4()
    with pytest.raises(ContentValidationError, match="cannot require an LLM"):
        validate_problem_metadata(
            metadata_curriculum_id=curriculum_id,
            primary_skill=_ref(curriculum_id),
            objective="Solve",
            evaluation_type="EXACT_NUMERIC",
            diagnostic_eligible=False,
            guided_eligible=False,
            independent_eligible=False,
            mastery_eligible=True,
            llm_solution_required=True,
        )


def test_active_skill_requires_source_traceability():
    with pytest.raises(ContentValidationError):
        validate_active_skill_traceability(
            skill=_ref(uuid.uuid4()),
            mapped_expectation_count=0,
        )


def test_problem_inventory_uses_explicit_accepted_threshold():
    skill = _ref(uuid.uuid4())
    validate_problem_inventory(skill=skill, problem_count=5, minimum_required=5)

    with pytest.raises(ContentValidationError):
        validate_problem_inventory(skill=skill, problem_count=4, minimum_required=5)


def test_source_identity_requires_version_identifier_and_absolute_uri():
    validate_source_identity(
        curriculum_version="2021",
        source_identifier="B1.1",
        source_uri="https://www.dcp.edu.gov.on.ca/example",
    )

    for kwargs in (
        {"curriculum_version": "", "source_identifier": "B1.1", "source_uri": "https://example.org"},
        {"curriculum_version": "2021", "source_identifier": "", "source_uri": "https://example.org"},
        {"curriculum_version": "2021", "source_identifier": "B1.1", "source_uri": "relative/path"},
    ):
        with pytest.raises(ContentValidationError):
            validate_source_identity(**kwargs)


def test_learning_mode_inventory_requires_each_deterministic_mode():
    skill = _ref(uuid.uuid4())
    validate_learning_mode_inventory(
        skill=skill,
        diagnostic_count=1,
        guided_count=1,
        independent_count=1,
        mastery_count=1,
    )

    with pytest.raises(ContentValidationError, match="mastery"):
        validate_learning_mode_inventory(
            skill=skill,
            diagnostic_count=1,
            guided_count=1,
            independent_count=1,
            mastery_count=0,
        )


def test_fresh_problem_sets_accept_distinct_mode_pools():
    validate_fresh_problem_sets(
        skill=_ref(uuid.uuid4()),
        diagnostic_problem_ids={"d1", "d2"},
        guided_problem_ids={"g1", "g2"},
        independent_problem_ids={"i1", "i2"},
        mastery_problem_ids={"m1", "m2"},
    )


def test_fresh_problem_sets_reject_reuse_between_independent_and_mastery():
    with pytest.raises(ContentValidationError, match="independent and mastery"):
        validate_fresh_problem_sets(
            skill=_ref(uuid.uuid4()),
            diagnostic_problem_ids={"d1"},
            guided_problem_ids={"g1"},
            independent_problem_ids={"fresh-1", "shared"},
            mastery_problem_ids={"shared", "fresh-2"},
        )


def test_fresh_problem_sets_reject_empty_mode_pool():
    with pytest.raises(ContentValidationError, match="diagnostic"):
        validate_fresh_problem_sets(
            skill=_ref(uuid.uuid4()),
            diagnostic_problem_ids=set(),
            guided_problem_ids={"g1"},
            independent_problem_ids={"i1"},
            mastery_problem_ids={"m1"},
        )
