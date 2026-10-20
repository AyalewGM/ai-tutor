from dataclasses import replace

from app.services import question_package_release as release

SHA = "a" * 40


def complete_evidence() -> release.PackageReleaseEvidence:
    return release.PackageReleaseEvidence(
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
    assert release.release_preflight_passes(release.PackageReleaseEvidence(package_sha=SHA)) is False


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
        assert release.release_preflight_passes(replace(complete, **{field: None})) is False
        assert release.release_preflight_passes(replace(complete, **{field: "b" * 40})) is False
    for field in (
        "canonical_mapping_approved",
        "exact_scorer_verified",
        "response_schema_verified",
        "history_preservation_verified",
        "runtime_activation_approved",
    ):
        assert release.release_preflight_passes(replace(complete, **{field: False})) is False


def test_eligible_mode_permissions_require_all_gates() -> None:
    # Full preflight is not a diagnostic/independent/mastery mode grant.
    assert release.release_preflight_passes(complete_evidence()) is True
    assert release.release_preflight_passes(replace(complete_evidence(), package_sha="invalid")) is False


def test_gate_is_side_effect_free() -> None:
    evidence = complete_evidence()
    before = repr(evidence)
    assert release.release_preflight_passes(evidence)
    assert repr(evidence) == before
