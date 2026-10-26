"""Synthetic resolver tests; PostgreSQL end-to-end remains a separate release gate."""
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.answer_contracts import AnswerKind
from app.models import TutorState
from app.services.family_activation_adapter import DENIED, FamilyRegistration
from app.services.fraction_assessment_registry import AssessmentMode, ReviewedFamily
from app.services.persisted_rational_resolution import (
    TrustedAssessmentContext,
    score_persisted_rational,
)
from app.services.question_package_release import PackageReleaseEvidence

_SHA = "a" * 40
_FAMILY = "SYNTHETIC.ONTARIO.RATIONAL"
_SKILL = "MATH.EE.EQUATION.TWO"


def _release():
    return PackageReleaseEvidence(
        package_sha=_SHA, math_accepted_sha=_SHA, pedagogy_accepted_sha=_SHA,
        backend_scoring_sha=_SHA, frontend_integration_sha=_SHA,
        muse_qa_sha=_SHA, engineering_authorized_sha=_SHA,
        canonical_mapping_approved=True, exact_scorer_verified=True,
        response_schema_verified=True, history_preservation_verified=True,
        runtime_activation_approved=True,
    )


def _fixture(*, eligible=True, owner=True, provenance=None, state=TutorState.INDEPENDENT_PRACTICE):
    student_id, session_id, problem_id, skill_id, curriculum_id = (uuid4() for _ in range(5))
    context = TrustedAssessmentContext(student_id, session_id, problem_id, AssessmentMode.INDEPENDENT)
    session = SimpleNamespace(
        id=session_id, student_id=student_id if owner else uuid4(),
        status="ACTIVE", current_state=state,
        primary_skill_id=skill_id, active_skill_id=skill_id, curriculum_id=curriculum_id,
    )
    problem = SimpleNamespace(id=problem_id, primary_skill_id=skill_id, canonical_answer="x=-3/4", answer_kind="VARIABLE_VALUE")
    skill = SimpleNamespace(id=skill_id, code="MTH1W.C.ALG.EQ2", curriculum_id=curriculum_id)
    mapping = SimpleNamespace(canonical_skill_id=uuid4())
    canonical = SimpleNamespace(id=mapping.canonical_skill_id, code=_SKILL)
    metadata = SimpleNamespace(
        problem_id=problem_id, curriculum_id=curriculum_id,
        diagnostic_eligible=False, guided_eligible=False,
        independent_eligible=eligible, mastery_eligible=False,
        provenance_json=provenance if provenance is not None else {
            "family_id": _FAMILY, "content_sha": _SHA,
        },
    )
    db = Mock()
    db.scalar.side_effect = [session if owner else None, problem, skill, metadata, mapping, canonical]
    record = FamilyRegistration(
        family=ReviewedFamily(
            _FAMILY, _SKILL, _SHA, frozenset({AssessmentMode.INDEPENDENT}),
            AnswerKind.VARIABLE_VALUE,
        ),
        evidence=_release(), scorer_revision="b" * 40, source_mapping_revision="c" * 40,
    )
    provider = Mock()
    provider.approved_records.return_value = (record,)
    return db, context, provider


def test_server_stored_provenance_and_mode_permit_pure_scoring():
    db, context, provider = _fixture()
    result = score_persisted_rational(
        db, context=context, submission="X=6/-8",
        approval_source=provider, service_principal="release-service",
    )
    assert result.eligible and result.correct and result.independent_evidence_eligible
    provider.approved_records.assert_called_once_with(service_principal="release-service")
    assert db.scalar.call_count == 6
    assert not hasattr(result, "canonical_answer")


def test_cross_learner_session_denied_before_problem_lookup():
    db, context, provider = _fixture(owner=False)
    assert score_persisted_rational(
        db, context=context, submission="x=-3/4",
        approval_source=provider, service_principal="release-service",
    ) == DENIED
    assert db.scalar.call_count == 1
    provider.approved_records.assert_not_called()


def test_missing_mode_and_mismatched_tutor_state_denied():
    for params in ({"eligible": False}, {"state": TutorState.GUIDED_PRACTICE}):
        db, context, provider = _fixture(**params)
        assert score_persisted_rational(
            db, context=context, submission="x=-3/4",
            approval_source=provider, service_principal="release-service",
        ) == DENIED
        provider.approved_records.assert_not_called()


def test_provenance_from_persisted_metadata_must_be_complete():
    for values in (
        {"family_id": _FAMILY, "content_sha": "c" * 40},
        {"family_id": _FAMILY, "content_sha": _SHA, "extra": "spoof"},
        {"family_id": _FAMILY},
    ):
        db, context, provider = _fixture(provenance=values)
        result = score_persisted_rational(
            db, context=context, submission="x=-3/4",
            approval_source=provider, service_principal="release-service",
        )
        assert result == DENIED
