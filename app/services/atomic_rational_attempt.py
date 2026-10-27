"""Inactive, transaction-scoped rational attempt recorder.

This helper is not wired to a learner route. Caller owns authentication, the
transaction and commit/rollback. It never awards independent mastery credit.
PostgreSQL row locks serialize submissions for the same learner across sessions.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attempt, Student, TutorSession
from app.services.family_activation_adapter import DENIED, RegistrationDecision
from app.services.persisted_rational_resolution import (
    AuthenticatedApprovalSource,
    TrustedAssessmentContext,
    score_persisted_rational,
)


@dataclass(frozen=True)
class RecordedRationalAttempt:
    decision: RegistrationDecision
    attempt_id: object | None


def record_rational_attempt(
    db: Session,
    *,
    context: TrustedAssessmentContext,
    submission: str,
    approval_source: AuthenticatedApprovalSource,
    service_principal: str,
) -> RecordedRationalAttempt:
    """Record at most one submission per student/problem, without committing.

    Must run inside a PostgreSQL transaction. Never call on SQLite or before
    independently authorized package activation. Rejected/replayed requests
    create no Attempt. Incorrect eligible answers are recorded as incorrect.
    """
    if db.bind is None or db.bind.dialect.name != "postgresql":
        return RecordedRationalAttempt(DENIED, None)
    if not isinstance(context, TrustedAssessmentContext):
        return RecordedRationalAttempt(DENIED, None)
    if not db.in_transaction():
        return RecordedRationalAttempt(DENIED, None)
    # The student row is the serialization point across concurrent sessions.
    student = db.scalar(
        select(Student).where(Student.id == context.student_id).with_for_update()
    )
    if student is None:
        return RecordedRationalAttempt(DENIED, None)
    session = db.scalar(
        select(TutorSession).where(
            TutorSession.id == context.session_id,
            TutorSession.student_id == context.student_id,
        ).with_for_update()
    )
    if session is None:
        return RecordedRationalAttempt(DENIED, None)
    previous = db.scalar(
        select(Attempt.id).where(
            Attempt.student_id == context.student_id,
            Attempt.problem_id == context.problem_id,
        ).limit(1)
    )
    if previous is not None:
        return RecordedRationalAttempt(DENIED, None)
    decision = score_persisted_rational(
        db,
        context=context,
        submission=submission,
        approval_source=approval_source,
        service_principal=service_principal,
    )
    if not decision.eligible:
        return RecordedRationalAttempt(DENIED, None)
    # Do not promote a scoring result into independent/mastery evidence.
    # Existing mastery policy must be separately integrated and reviewed.
    if decision.independent_evidence_eligible:
        return RecordedRationalAttempt(DENIED, None)
    attempt = Attempt(
        session_id=context.session_id,
        student_id=context.student_id,
        problem_id=context.problem_id,
        student_answer=submission,
        is_correct=decision.correct,
        attempt_number=1,
        assistance_level=1 if context.assisted else 0,
        state_at_attempt=session.current_state,
    )
    db.add(attempt)
    db.flush()
    return RecordedRationalAttempt(decision, attempt.id)
