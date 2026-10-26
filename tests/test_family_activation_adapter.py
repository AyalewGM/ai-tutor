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
    defaults = dict(
        package_sha=_SHA, math_accepted_sha=_SHA, pedagogy_accepted_sha=_SHA,
        backend_scoring_sha=_SHA, frontend_integration_sha=_SHA,
        muse_qa_sha=_SHA, engineering_authorized_sha=_SHA,
        canonical_mapping_approved=True, exact_scorer_verified=True,
        response_schema_verified=True, history_preservation_verified=True,
        runtime_activation_approved=True,
    )
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
    args = dict(
        registry=reg, family_id="SYNTHETIC.EQUATION.FRACTION",
        canonical_skill_code="MATH.EE.EQUATION.TWO",
        content_sha=_SHA, canonical_answer="x=-3/4", variable="x",
    )
    positive = score_registered_rational(
        **args, submitted_answer="X=6/-8", mode=AssessmentMode.INDEPENDENT
    )
    assert positive.eligible and positive.correct and positive.independent_evidence_eligible
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
    kwargs = dict(
        registry=registry, family_id="SYNTHETIC.EQUATION.FRACTION",
        canonical_skill_code="MATH.EE.EQUATION.TWO", content_sha=_SHA,
        mode=AssessmentMode.INDEPENDENT, canonical_answer="x=-3/4",
        submitted_answer="x=-6/8", variable="x",
    )
    initial = score_registered_rational(**kwargs)
    assert all(score_registered_rational(**kwargs) == initial for _ in range(15))
    assert not AUTHORIZED_FAMILIES
