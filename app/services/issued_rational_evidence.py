"""Read-only proof of a fresh, unassisted, server-issued rational item.

No route, token issuance, attempt write or mastery award. The issuing API must
create its own trusted TutorTurn with these exact fields transactionally.
Legacy and ambiguous records deny independent/mastery scoring.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.diagnostic_models import DiagnosticAttempt, DiagnosticSession
from app.hint_models import HintEvent
from app.models import Attempt, Problem, TutorState, TutorTurn
from app.services.fraction_assessment_registry import AssessmentMode

ISSUANCE_VERSION = "MIHUR_ASSESSMENT_ISSUANCE_V1"


def verify_fresh_issuance(
    db: Session, *,
    student_id: object,
    session_id: object,
    problem: Problem,
    mode: AssessmentMode,
) -> bool:
    """Proof for scoring admission, NOT sufficient to award mastery evidence."""
    if mode not in {AssessmentMode.INDEPENDENT, AssessmentMode.MASTERY}:
        return False
    solution = problem.solution
    if not isinstance(solution, dict):
        return False
    variant = solution.get("variant_id")
    fingerprint = solution.get("task_fingerprint")
    if not isinstance(variant, str) or not variant or not isinstance(fingerprint, str) or not fingerprint:
        return False
    # A previously submitted problem must never be accepted as a fresh task,
    # including another session or a diagnostic attempt for the same learner.
    if db.scalar(select(Attempt.id).where(
        Attempt.student_id == student_id, Attempt.problem_id == problem.id,
    ).limit(1)) is not None:
        return False
    if db.scalar(select(DiagnosticAttempt.id).join(
        DiagnosticSession, DiagnosticSession.id == DiagnosticAttempt.diagnostic_session_id,
    ).where(
        DiagnosticSession.student_id == student_id,
        DiagnosticAttempt.problem_id == problem.id,
    ).limit(1)) is not None:
        return False
    # HintEvent is authoritative assistance evidence even when no TutorTurn
    # was written for the hint. A previously assisted item cannot be fresh
    # independent work in a new session either.
    if db.scalar(select(HintEvent.id).where(
        HintEvent.student_id == student_id,
        HintEvent.problem_id == problem.id,
    ).limit(1)) is not None:
        return False
    turns = db.scalars(select(TutorTurn).where(
        TutorTurn.session_id == session_id, TutorTurn.problem_id == problem.id,
    )).all()
    # Fail closed on any unrecognized interaction: unknown assistant actions
    # must not silently become unassisted evidence. A plain learner input is
    # allowed, but is not itself proof of issuance or mastery.
    issuance = [
        turn for turn in turns
        if turn.role == "SYSTEM" and turn.pedagogical_action == "ISSUE_ASSESSMENT"
    ]
    if any(
        turn not in issuance
        and not (
            turn.role == "STUDENT"
            and turn.pedagogical_action == "ANSWER_INPUT"
            and turn.state == (
                TutorState.INDEPENDENT_PRACTICE
                if mode == AssessmentMode.INDEPENDENT else TutorState.MASTERY_CHECK
            )
        )
        for turn in turns
    ):
        return False
    if len(issuance) != 1:
        return False
    issued = issuance[0]
    expected = {
        "issuance_contract": ISSUANCE_VERSION,
        "student_id": str(student_id),
        "problem_id": str(problem.id),
        "variant_id": variant,
        "task_fingerprint": fingerprint,
        "mode": mode.value,
    }
    return (
        issued.role == "SYSTEM"
        and issued.pedagogical_action == "ISSUE_ASSESSMENT"
        and issued.state == (
            TutorState.INDEPENDENT_PRACTICE if mode == AssessmentMode.INDEPENDENT
            else TutorState.MASTERY_CHECK
        )
        and isinstance(issued.metadata_json, dict)
        and issued.metadata_json == expected
    )
