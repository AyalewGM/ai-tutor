"""Synthetic regression coverage for the read-only persisted scoring boundary."""
from unittest.mock import Mock
from uuid import uuid4

from app.services.family_activation_adapter import DENIED
from app.services.fraction_assessment_registry import AssessmentMode
from app.services.persisted_rational_resolution import (
    TrustedAssessmentContext,
    score_persisted_rational,
)


def _context():
    return TrustedAssessmentContext(uuid4(), uuid4(), uuid4(), AssessmentMode.INDEPENDENT)


def test_never_accesses_database_without_authenticated_approval_source():
    db = Mock()
    assert score_persisted_rational(
        db, context=_context(), submission="x=3/4"
    ) == DENIED
    db.scalar.assert_not_called()


def test_denies_without_release_authority_before_database_lookup():
    db = Mock()
    ctx = _context()
    assert score_persisted_rational(
        db, context=ctx, submission="3/4",
        approval_source=Mock(), service_principal="",
    ) == DENIED
    db.scalar.assert_not_called()


def test_rejects_client_style_assistance_and_mode_values():
    db = Mock()
    ctx = _context()
    for altered in (
        TrustedAssessmentContext(ctx.student_id, ctx.session_id, ctx.problem_id, "independent"),
        TrustedAssessmentContext(ctx.student_id, ctx.session_id, ctx.problem_id, AssessmentMode.INDEPENDENT, "false"),
    ):
        assert score_persisted_rational(
            db, context=altered, submission="x=3/4",
            approval_source=Mock(), service_principal="trusted-service",
        ) == DENIED
    db.scalar.assert_not_called()
