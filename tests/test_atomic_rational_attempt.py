"""Safety boundary tests for inactive rational attempt recorder."""
from unittest.mock import Mock

from app.services.atomic_rational_attempt import record_rational_attempt
from app.services.family_activation_adapter import DENIED


def test_rejects_non_postgres_without_writing():
    db = Mock()
    db.bind.dialect.name = "sqlite"
    result = record_rational_attempt(
        db,
        context=object(),
        submission="x=1/2",
        approval_source=Mock(),
        service_principal="synthetic",
    )
    assert result.decision == DENIED
    assert result.attempt_id is None
    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_rejects_missing_database_bind():
    db = Mock()
    db.bind = None
    result = record_rational_attempt(
        db,
        context=object(),
        submission="x=1/2",
        approval_source=Mock(),
        service_principal="synthetic",
    )
    assert result.decision == DENIED
    assert result.attempt_id is None
    db.add.assert_not_called()


def test_requires_existing_transaction_before_any_database_query():
    from app.services.persisted_rational_resolution import TrustedAssessmentContext
    from app.services.fraction_assessment_registry import AssessmentMode
    import uuid

    db = Mock()
    db.bind.dialect.name = "postgresql"
    db.in_transaction.return_value = False
    context = TrustedAssessmentContext(
        student_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        problem_id=uuid.uuid4(),
        mode=AssessmentMode.INDEPENDENT,
    )
    result = record_rational_attempt(
        db,
        context=context,
        submission="x=1/2",
        approval_source=Mock(),
        service_principal="synthetic",
    )
    assert result.decision == DENIED
    assert result.attempt_id is None
    db.scalar.assert_not_called()
    db.add.assert_not_called()
