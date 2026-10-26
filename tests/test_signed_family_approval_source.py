"""Ephemeral-key signature evidence; never stores production signing keys."""
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.answer_contracts import AnswerKind
from app.services.family_activation_adapter import FamilyRegistration
from app.services.fraction_assessment_registry import AssessmentMode, ReviewedFamily
from app.services.question_package_release import PackageReleaseEvidence
from app.services.signed_family_approval_source import (
    PinnedPublicKeyApprovalSource,
    SignedReleaseDeclaration,
    canonical_release_payload,
)

_SHA = "a" * 40


def _approved():
    evidence = PackageReleaseEvidence(
        package_sha=_SHA, math_accepted_sha=_SHA, pedagogy_accepted_sha=_SHA,
        backend_scoring_sha=_SHA, frontend_integration_sha=_SHA,
        muse_qa_sha=_SHA, engineering_authorized_sha=_SHA,
        canonical_mapping_approved=True, exact_scorer_verified=True,
        response_schema_verified=True, history_preservation_verified=True,
        runtime_activation_approved=True,
    )
    return FamilyRegistration(
        family=ReviewedFamily(
            family_id="SYNTHETIC.SIGNED.RATIONAL",
            canonical_skill_code="MATH.EE.EQUATION.TWO",
            content_sha=_SHA,
            modes=frozenset({AssessmentMode.GUIDED, AssessmentMode.INDEPENDENT}),
            answer_kind=AnswerKind.VARIABLE_VALUE,
        ),
        evidence=evidence, scorer_revision="b" * 40, source_mapping_revision="c" * 40,
        answer_variable="x", standards_manifest_sha="d" * 40,
        jurisdiction_code="CA.ON", curriculum_code="MTH1W", local_skill_code="MTH1W.C.ALG.EQ2",
        mapping_disposition="ACCEPTED", coverage_credit=True,
    )


def _sign():
    private = Ed25519PrivateKey.generate()
    records = (_approved(),)
    declaration = SignedReleaseDeclaration(
        key_id="synthetic-review-key-v1", registrations=records,
        signature=private.sign(canonical_release_payload(
            key_id="synthetic-review-key-v1", registrations=records,
        )),
    )
    source = PinnedPublicKeyApprovalSource(
        trusted_key_id="synthetic-review-key-v1",
        public_key_bytes=private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw),
        trusted_service_principal="synthetic-service-only",
        declaration=declaration,
    )
    return source, private, declaration


def test_signed_release_positive_and_principal_denial():
    source, _private, declaration = _sign()
    assert source.approved_records(
        service_principal="synthetic-service-only"
    ) == declaration.registrations
    with pytest.raises(PermissionError):
        source.approved_records(service_principal="web-client")


def test_tampered_modes_family_and_evidence_are_rejected():
    _source, private, original = _sign()
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    family = original.registrations[0].family
    for tampered in (
        replace(
            original.registrations[0],
            family=replace(family, modes=frozenset({AssessmentMode.MASTERY})),
        ),
        replace(
            original.registrations[0],
            family=replace(family, canonical_skill_code="MATH.WRONG"),
        ),
        replace(
            original.registrations[0],
            source_mapping_revision="f" * 40,
        ),
        replace(
            original.registrations[0],
            evidence=replace(
                original.registrations[0].evidence,
                engineering_authorized_sha="d" * 40,
            ),
        ),
    ):
        source = PinnedPublicKeyApprovalSource(
            trusted_key_id=original.key_id, public_key_bytes=public,
            trusted_service_principal="synthetic-service-only",
            declaration=replace(original, registrations=(tampered,)),
        )
        with pytest.raises((ValueError, PermissionError)):
            source.approved_records(service_principal="synthetic-service-only")


def test_other_signer_and_unrecognized_key_denied():
    source, _private, declaration = _sign()
    foreign = Ed25519PrivateKey.generate()
    signed_by_foreign = replace(
        declaration,
        signature=foreign.sign(canonical_release_payload(
            key_id=declaration.key_id, registrations=declaration.registrations,
        )),
    )
    trusted_pub = _private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    other = PinnedPublicKeyApprovalSource(
        trusted_key_id=declaration.key_id, public_key_bytes=trusted_pub,
        trusted_service_principal="synthetic-service-only",
        declaration=signed_by_foreign,
    )
    with pytest.raises(PermissionError):
        other.approved_records(service_principal="synthetic-service-only")
    with pytest.raises(ValueError):
        PinnedPublicKeyApprovalSource(
            trusted_key_id="unexpected-key", public_key_bytes=trusted_pub,
            trusted_service_principal="synthetic-service-only",
            declaration=declaration,
        )
    assert len(source.approved_records(service_principal="synthetic-service-only")) == 1
