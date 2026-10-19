from dataclasses import replace

from app.services.question_package_release import (
    PackageReleaseEvidence,
    QuestionMode,
    permitted_question_modes,
)


SHA = "a" * 40


def complete_evidence() -> PackageReleaseEvidence:
    return PackageReleaseEvidence(
        package_sha=SHA,
        math_accepted_sha=SHA,
        pedagogy_accepted_sha=SHA,
        backend_scoring_sha=SHA,
        frontend_integration_sha=SHA,
        muse_qa_sha=SHA,
        engineering_authorized_sha=SHA,
        canonical_mapping_approved=True,
        exact_scorer_verified=True,
        response_schema_verified=True,
        history_preservation_verified=True,
        runtime_activation_approved=True,
    )


def test_unreviewed_package_cannot_activate() -> None:
    assert permitted_question_modes(PackageReleaseEvidence(package_sha=SHA)) == frozenset()


def test_every_review_and_release_gate_is_required() -> None:
    complete = complete_evidence()
    for field in (
        "math_accepted_sha",
        "pedagogy_accepted_sha",
        "backend_scoring_sha",
        "frontend_integration_sha",
        "muse_qa_sha",
        "engineering_authorized_sha",
    ):
        assert permitted_question_modes(replace(complete, **{field: None})) == frozenset()
        assert permitted_question_modes(replace(complete, **{field: "b" * 40})) == frozenset()
    for field in (
        "canonical_mapping_approved",
        "exact_scorer_verified",
        "response_schema_verified",
        "history_preservation_verified",
        "runtime_activation_approved",
    ):
        assert permitted_question_modes(replace(complete, **{field: False})) == frozenset()


def test_eligible_mode_permissions_require_all_gates() -> None:
    assert permitted_question_modes(complete_evidence()) == frozenset(QuestionMode)
    assert permitted_question_modes(replace(complete_evidence(), package_sha="invalid")) == frozenset()


def test_gate_is_side_effect_free() -> None:
    evidence = complete_evidence()
    before = repr(evidence)
    assert permitted_question_modes(evidence)
    assert repr(evidence) == before
