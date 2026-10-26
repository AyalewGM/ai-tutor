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
