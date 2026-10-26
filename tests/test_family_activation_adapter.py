"""Synthetic-only tests of the versioned family registration and scoring adapter."""
from dataclasses import replace

import pytest

from app.answer_contracts import AnswerKind
from app.services.family_activation_adapter import (
    DENIED,
    SCHEMA_VERSION,
    FamilyRegistration,
    compile_registration,
    score_registered_rational,
)
from app.services.fraction_assessment_registry import (
    AUTHORIZED_FAMILIES,
    AssessmentMode,
    ReviewedFamily,
)
from app.services.question_package_release import PackageReleaseEvidence

_SHA = "a" * 40


def evidence(**changes):
    defaults = {
        "package_sha":_SHA, "math_accepted_sha":_SHA, "pedagogy_accepted_sha":_SHA,
        "backend_scoring_sha":_SHA, "frontend_integration_sha":_SHA,
        "muse_qa_sha":_SHA, "engineering_authorized_sha":_SHA,
        "canonical_mapping_approved":True, "exact_scorer_verified":True,
        "response_schema_verified":True, "history_preservation_verified":True,
        "runtime_activation_approved":True,
    }
    defaults.update(changes)
    return PackageReleaseEvidence(**defaults)


def registration():
    return FamilyRegistration(
        family=ReviewedFamily(
            "SYNTHETIC.EQUATION.FRACTION", "MATH.EE.EQUATION.TWO", _SHA,
            frozenset({AssessmentMode.GUIDED, AssessmentMode.INDEPENDENT}),
            AnswerKind.VARIABLE_VALUE,
        ),
        evidence=evidence(),
        scorer_revision="b" * 40,
        source_mapping_revision="c" * 40,
        answer_variable="x", standards_manifest_sha="d" * 40,
        jurisdiction_code="CA.ON", curriculum_code="MTH1W",
        mapping_disposition="ACCEPTED", coverage_credit=True,
    )


def test_manifest_is_immutable_and_never_populates_runtime_registry():
    assert not AUTHORIZED_FAMILIES
    result = compile_registration(SCHEMA_VERSION, (registration(),))
    assert set(result) == {"SYNTHETIC.EQUATION.FRACTION"}
    with pytest.raises(TypeError):
        result["DRAFT"] = registration().family
    assert not AUTHORIZED_FAMILIES


@pytest.mark.parametrize("changed", [
    {"math_accepted_sha": None},
    {"runtime_activation_approved": False},
    {"canonical_mapping_approved": False},
    {"history_preservation_verified": False},
    {"muse_qa_sha": "d" * 40},
])
def test_incomplete_or_stale_release_gate_fails_closed(changed):
    record = replace(registration(), evidence=evidence(**changed))
    with pytest.raises(ValueError):
        compile_registration(SCHEMA_VERSION, (record,))


def test_schema_revision_and_duplicate_family_fail_closed():
    item = registration()
    with pytest.raises(ValueError):
        compile_registration("mihur.family-registration.v2", (item,))
    with pytest.raises(ValueError):
        compile_registration(SCHEMA_VERSION, (item, item))
    with pytest.raises(ValueError):
        compile_registration(SCHEMA_VERSION, (
            replace(item, scorer_revision="invalid"),))


def test_positive_negative_mode_assistance_and_identity():
    reg = compile_registration(SCHEMA_VERSION, (registration(),))
    args = {
        "registry":reg, "family_id":"SYNTHETIC.EQUATION.FRACTION",
        "canonical_skill_code":"MATH.EE.EQUATION.TWO",
        "content_sha":_SHA, "canonical_answer":"x=-3/4", "variable":"x",
        "source_mapping_revision": "c" * 40, "standards_manifest_sha": "d" * 40,
        "jurisdiction_code": "CA.ON", "curriculum_code": "MTH1W",
    }
    positive = score_registered_rational(
        **args, submitted_answer="X=6/-8", mode=AssessmentMode.INDEPENDENT
    )
    assert positive.eligible and positive.correct
    assert not positive.independent_evidence_eligible
    assert score_registered_rational(
        **args, submitted_answer="x=-3/4", mode=AssessmentMode.GUIDED
    ).independent_evidence_eligible is False
    assert score_registered_rational(
        **args, submitted_answer="x=-3/4",
        mode=AssessmentMode.INDEPENDENT, assisted=True
    ).independent_evidence_eligible is False
    assert score_registered_rational(
        **args, submitted_answer="x=3/4", mode=AssessmentMode.INDEPENDENT
    ).correct is False
    for change in (
        {"family_id": "DRAFT.489"},
        {"canonical_skill_code": "MATH.WRONG"},
        {"content_sha": "d" * 40},
        {"mode": AssessmentMode.MASTERY},
        {"assisted": "false"},
    ):
        current = dict(args, submitted_answer="x=-3/4", mode=AssessmentMode.INDEPENDENT)
        current.update(change)
        assert score_registered_rational(**current) == DENIED
    assert not hasattr(positive, "canonical_answer")


def test_repeat_scoring_is_pure_no_attempt_or_mastery_state():
    registry = compile_registration(SCHEMA_VERSION, (registration(),))
    kwargs = {
        "registry":registry, "family_id":"SYNTHETIC.EQUATION.FRACTION",
        "canonical_skill_code":"MATH.EE.EQUATION.TWO", "content_sha":_SHA,
        "mode":AssessmentMode.INDEPENDENT, "canonical_answer":"x=-3/4",
        "submitted_answer":"x=-6/8", "variable":"x",
        "source_mapping_revision": "c" * 40, "standards_manifest_sha": "d" * 40,
        "jurisdiction_code": "CA.ON", "curriculum_code": "MTH1W",
    }
    initial = score_registered_rational(**kwargs)
    assert all(score_registered_rational(**kwargs) == initial for _ in range(15))
    assert not AUTHORIZED_FAMILIES


def test_reviewed_answer_kind_and_variable_cannot_be_switched_by_caller():
    registry = compile_registration(SCHEMA_VERSION, (registration(),))
    common = {
        "registry": registry, "family_id": "SYNTHETIC.EQUATION.FRACTION",
        "canonical_skill_code": "MATH.EE.EQUATION.TWO", "content_sha": _SHA,
        "source_mapping_revision": "c" * 40, "standards_manifest_sha": "d" * 40,
        "jurisdiction_code": "CA.ON", "curriculum_code": "MTH1W",
        "mode": AssessmentMode.INDEPENDENT,
    }
    for wrong in (
        {"canonical_answer": "-3/4", "submitted_answer": "6/-8", "variable": None},
        {"canonical_answer": "y=-3/4", "submitted_answer": "y=6/-8", "variable": "y"},
        {"canonical_answer": "x=-3/4", "submitted_answer": "y=6/-8", "variable": "x"},
    ):
        result = score_registered_rational(**common, **wrong)
        assert not result.independent_evidence_eligible
        assert result == DENIED or not result.correct


def test_invalid_mapping_evidence_and_contract_are_denied():
    base = registration()
    for modified in (
        replace(base, mapping_disposition="PROVISIONAL"),
        replace(base, coverage_credit=False),
        replace(base, standards_manifest_sha=""),
        replace(base, jurisdiction_code=""),
        replace(base, answer_variable=None),
    ):
        with pytest.raises(ValueError):
            compile_registration(SCHEMA_VERSION, (modified,))
    registry = compile_registration(SCHEMA_VERSION, (base,))
    for override in (
        {"source_mapping_revision": "f" * 40},
        {"standards_manifest_sha": "e" * 40},
        {"jurisdiction_code": "US.MD"},
        {"curriculum_code": "MTH1W.FUTURE"},
    ):
        values = {
            "registry": registry, "family_id": base.family.family_id,
            "canonical_skill_code": base.family.canonical_skill_code,
            "content_sha": _SHA, "mode": AssessmentMode.INDEPENDENT,
            "canonical_answer": "x=-3/4", "submitted_answer": "x=-6/8", "variable": "x",
            "source_mapping_revision": "c" * 40, "standards_manifest_sha": "d" * 40,
            "jurisdiction_code": "CA.ON", "curriculum_code": "MTH1W",
        }
        values.update(override)
        assert score_registered_rational(**values) == DENIED


def test_bare_rational_family_cannot_accept_equation_form():
    original = registration()
    bare = replace(
        original,
        family=replace(original.family, answer_kind=AnswerKind.RATIONAL),
        answer_variable=None,
    )
    registry = compile_registration(SCHEMA_VERSION, (bare,))
    values = {
        "registry": registry, "family_id": bare.family.family_id,
        "canonical_skill_code": bare.family.canonical_skill_code,
        "content_sha": _SHA, "mode": AssessmentMode.INDEPENDENT,
        "source_mapping_revision": "c" * 40, "standards_manifest_sha": "d" * 40,
        "jurisdiction_code": "CA.ON", "curriculum_code": "MTH1W",
        "canonical_answer": "-3/4", "variable": None,
    }
    valid = score_registered_rational(**values, submitted_answer="6/-8")
    assert valid.eligible and valid.correct and not valid.independent_evidence_eligible
    wrong_shape = score_registered_rational(**values, submitted_answer="x=6/-8")
    assert wrong_shape.eligible and not wrong_shape.correct
    assert score_registered_rational(
        **{**values, "variable": "x"}, submitted_answer="x=6/-8"
    ) == DENIED
