"""Safety boundary tests for inactive rational attempt recorder."""
import uuid
from unittest.mock import Mock

import app.services.atomic_rational_attempt as recorder
from app.services.atomic_rational_attempt import record_rational_attempt
from app.services.family_activation_adapter import DENIED, RegistrationDecision
from app.services.fraction_assessment_registry import AssessmentMode
from app.services.persisted_rational_resolution import TrustedAssessmentContext


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


def test_revoked_student_or_closed_session_denied_before_scoring(monkeypatch):
    scorer = Mock()
    monkeypatch.setattr(recorder, "score_persisted_rational", scorer)
    context = TrustedAssessmentContext(
        student_id=uuid.uuid4(), session_id=uuid.uuid4(),
        problem_id=uuid.uuid4(), mode=AssessmentMode.INDEPENDENT,
    )
    for student_active, session_status in ((False, "ACTIVE"), (True, "CLOSED")):
        db = Mock()
        db.bind.dialect.name = "postgresql"
        db.in_transaction.return_value = True
        db.connection.return_value.get_isolation_level.return_value = "READ COMMITTED"
        db.connection.return_value.connection.driver_connection.autocommit = False
        db.scalar.side_effect = [
            Mock(active=student_active), Mock(status=session_status), None,
        ]
        result = record_rational_attempt(
            db, context=context, submission="x=1/2",
            approval_source=Mock(), service_principal="synthetic",
        )
        assert result.decision == DENIED
        assert result.attempt_id is None
        db.add.assert_not_called()
        db.flush.assert_not_called()
        db.commit.assert_not_called()
    scorer.assert_not_called()


def test_replay_denied_without_scoring_or_writing(monkeypatch):

    db = Mock()
    db.bind.dialect.name = "postgresql"
    db.in_transaction.return_value = True
    db.connection.return_value.get_isolation_level.return_value = "READ COMMITTED"
    db.connection.return_value.connection.driver_connection.autocommit = False
    db.scalar.side_effect = [Mock(active=True), Mock(status="ACTIVE"), uuid.uuid4()]
    scorer = Mock()
    monkeypatch.setattr(recorder, "score_persisted_rational", scorer)
    context = TrustedAssessmentContext(
        student_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        problem_id=uuid.uuid4(),
        mode=AssessmentMode.INDEPENDENT,
    )
    result = record_rational_attempt(
        db, context=context, submission="x=1/2",
        approval_source=Mock(), service_principal="synthetic",
    )
    assert result.decision == DENIED
    assert result.attempt_id is None
    scorer.assert_not_called()
    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_denied_scoring_never_persists(monkeypatch):

    db = Mock()
    db.bind.dialect.name = "postgresql"
    db.in_transaction.return_value = True
    db.connection.return_value.get_isolation_level.return_value = "READ COMMITTED"
    db.connection.return_value.connection.driver_connection.autocommit = False
    db.scalar.side_effect = [Mock(active=True), Mock(status="ACTIVE"), None]
    monkeypatch.setattr(recorder, "score_persisted_rational", lambda *args, **kwargs: DENIED)
    context = TrustedAssessmentContext(
        student_id=uuid.uuid4(), session_id=uuid.uuid4(),
        problem_id=uuid.uuid4(), mode=AssessmentMode.INDEPENDENT,
    )
    result = record_rational_attempt(
        db, context=context, submission="x=1/2",
        approval_source=Mock(), service_principal="synthetic",
    )
    assert result.decision == DENIED
    assert result.attempt_id is None
    db.add.assert_not_called()
    db.flush.assert_not_called()


def test_eligible_correct_response_records_attempt_without_commit(monkeypatch):
    from app.models import TutorState

    db = Mock()
    db.bind.dialect.name = "postgresql"
    db.in_transaction.return_value = True
    db.connection.return_value.get_isolation_level.return_value = "READ COMMITTED"
    db.connection.return_value.connection.driver_connection.autocommit = False
    session = Mock(current_state=TutorState.INDEPENDENT_PRACTICE, status="ACTIVE")
    db.scalar.side_effect = [Mock(active=True), session, None]
    db.flush.side_effect = lambda: setattr(db.add.call_args.args[0], "id", uuid.uuid4())
    decision = RegistrationDecision(True, True, False)
    scorer = Mock(return_value=decision)
    monkeypatch.setattr(recorder, "score_persisted_rational", scorer)
    context = TrustedAssessmentContext(
        student_id=uuid.uuid4(), session_id=uuid.uuid4(),
        problem_id=uuid.uuid4(), mode=AssessmentMode.INDEPENDENT,
    )
    result = record_rational_attempt(
        db, context=context, submission="x=1/2",
        approval_source=Mock(), service_principal="synthetic",
    )
    attempt = db.add.call_args.args[0]
    assert result.decision == decision
    assert result.attempt_id == attempt.id
    assert attempt.is_correct is True
    assert attempt.student_id == context.student_id
    assert attempt.assistance_level == 0
    assert attempt.state_at_attempt == TutorState.INDEPENDENT_PRACTICE
    db.flush.assert_called_once()
    db.commit.assert_not_called()


def test_eligible_incorrect_assisted_response_records_without_mastery(monkeypatch):
    from app.models import TutorState

    db = Mock()
    db.bind.dialect.name = "postgresql"
    db.in_transaction.return_value = True
    db.connection.return_value.get_isolation_level.return_value = "READ COMMITTED"
    db.connection.return_value.connection.driver_connection.autocommit = False
    db.scalar.side_effect = [Mock(active=True), Mock(current_state=TutorState.GUIDED_PRACTICE, status="ACTIVE"), None]
    db.flush.side_effect = lambda: setattr(db.add.call_args.args[0], "id", uuid.uuid4())
    monkeypatch.setattr(
        recorder, "score_persisted_rational",
        Mock(return_value=RegistrationDecision(True, False, False)),
    )
    context = TrustedAssessmentContext(
        student_id=uuid.uuid4(), session_id=uuid.uuid4(),
        problem_id=uuid.uuid4(), mode=AssessmentMode.GUIDED, assisted=True,
    )
    result = record_rational_attempt(
        db, context=context, submission="x=999",
        approval_source=Mock(), service_principal="synthetic",
    )
    attempt = db.add.call_args.args[0]
    assert result.decision.eligible is True
    assert result.decision.correct is False
    assert result.decision.independent_evidence_eligible is False
    assert attempt.is_correct is False
    assert attempt.assistance_level == 1
    assert attempt.state_at_attempt == TutorState.GUIDED_PRACTICE
    db.commit.assert_not_called()


def test_unsupported_or_unavailable_isolation_denied_before_queries(monkeypatch):
    from sqlalchemy.exc import InvalidRequestError

    scorer = Mock()
    monkeypatch.setattr(recorder, "score_persisted_rational", scorer)
    context = TrustedAssessmentContext(
        student_id=uuid.uuid4(), session_id=uuid.uuid4(),
        problem_id=uuid.uuid4(), mode=AssessmentMode.INDEPENDENT,
    )
    for isolation in ("REPEATABLE READ", "SERIALIZABLE", "READ UNCOMMITTED", None):
        db = Mock()
        db.bind.dialect.name = "postgresql"
        db.in_transaction.return_value = True
        db.connection.return_value.get_isolation_level.return_value = isolation
        result = record_rational_attempt(
            db, context=context, submission="x=1/2",
            approval_source=Mock(), service_principal="synthetic",
        )
        assert result.decision == DENIED and result.attempt_id is None
        db.scalar.assert_not_called()
        db.add.assert_not_called()
        db.flush.assert_not_called()
    for error in (InvalidRequestError("Unavailable"), NotImplementedError(), AttributeError()):
        db = Mock()
        db.bind.dialect.name = "postgresql"
        db.in_transaction.return_value = True
        db.connection.return_value.get_isolation_level.side_effect = error
        result = record_rational_attempt(
            db, context=context, submission="x=1/2",
            approval_source=Mock(), service_principal="synthetic",
        )
        assert result.decision == DENIED and result.attempt_id is None
        db.scalar.assert_not_called()
        db.add.assert_not_called()
        db.flush.assert_not_called()
    scorer.assert_not_called()


def test_actual_driver_autocommit_must_be_explicitly_false(monkeypatch):
    from unittest.mock import PropertyMock

    scorer = Mock()
    monkeypatch.setattr(recorder, "score_persisted_rational", scorer)
    context = TrustedAssessmentContext(
        student_id=uuid.uuid4(), session_id=uuid.uuid4(),
        problem_id=uuid.uuid4(), mode=AssessmentMode.INDEPENDENT,
    )
    for state in (True, None, 0, "False", Mock(), "missing", "error"):
        db = Mock()
        db.bind.dialect.name = "postgresql"
        db.in_transaction.return_value = True
        connection = db.connection.return_value
        connection.get_isolation_level.return_value = "READ COMMITTED"
        if state == "missing":
            connection.connection.driver_connection = object()
        elif state == "error":
            driver = Mock()
            type(driver).autocommit = PropertyMock(side_effect=RuntimeError("Unavailable"))
            connection.connection.driver_connection = driver
        else:
            connection.connection.driver_connection.autocommit = state
        result = record_rational_attempt(
            db, context=context, submission="x=1/2",
            approval_source=Mock(), service_principal="synthetic",
        )
        assert result.decision == DENIED and result.attempt_id is None
        db.scalar.assert_not_called()
        db.add.assert_not_called()
        db.flush.assert_not_called()
    scorer.assert_not_called()
