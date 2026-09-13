import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.diagnostic_models import DiagnosticAttempt, DiagnosticSession
from app.diagnostic_schemas import (
    DiagnosticOut,
    DiagnosticRespondIn,
    DiagnosticResultOut,
    DiagnosticSkillEvidenceOut,
    DiagnosticStartIn,
)
from app.models import MasteryEvent, Problem, Skill, Student, StudentSkill, TutorState
from app.schemas import ProblemOut
from app.services.attempt_evidence import record_evidence
from app.services.curriculum_scope import (
    CurriculumScope,
    CurriculumScopeError,
    require_skill_in_scope,
    resolve_student_curriculum_scope,
)
from app.services.diagnostic_controller import decide_next_probe
from app.services.problem_selection import select_next_problem

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])
DbSession = Annotated[Session, Depends(get_db)]


def _student_skill(db: Session, student_id: uuid.UUID, skill_id: uuid.UUID) -> StudentSkill:
    row = db.get(StudentSkill, {"student_id": student_id, "skill_id": skill_id})
    if row is None:
        row = StudentSkill(student_id=student_id, skill_id=skill_id)
        db.add(row)
        db.flush()
    return row


def _next_problem(
    db: Session,
    student_id: uuid.UUID,
    skill_id: uuid.UUID,
    current_problem_id: uuid.UUID | None = None,
) -> Problem | None:
    progress = _student_skill(db, student_id, skill_id)
    return select_next_problem(
        db,
        skill_id=skill_id,
        current_problem_id=current_problem_id,
        current_difficulty=progress.current_difficulty,
        state=TutorState.DIAGNOSE,
    )


def _problem_out(problem: Problem | None) -> ProblemOut | None:
    if problem is None:
        return None
    return ProblemOut(id=problem.id, prompt=problem.prompt, difficulty=problem.difficulty)


def _diagnostic_scope(db: Session, session: DiagnosticSession) -> CurriculumScope:
    if session.curriculum_id is not None:
        return CurriculumScope(
            curriculum_id=session.curriculum_id,
            enrollment_id=session.curriculum_enrollment_id,
            local_authority_id=None,
        )
    student = db.get(Student, session.student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    try:
        return resolve_student_curriculum_scope(db, student)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc


def _require_session_skill_scope(
    db: Session, *, session: DiagnosticSession, skill_id: uuid.UUID
) -> Skill:
    try:
        return require_skill_in_scope(db, skill_id=skill_id, scope=_diagnostic_scope(db, session))
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/sessions", response_model=DiagnosticOut)
def start_diagnostic(payload: DiagnosticStartIn, db: DbSession) -> DiagnosticOut:
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    try:
        scope = resolve_student_curriculum_scope(db, student)
        target = require_skill_in_scope(db, skill_id=payload.target_skill_id, scope=scope)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc

    problem = _next_problem(db, student.id, target.id)
    if problem is None:
        raise HTTPException(404, "No diagnostic problem configured for target skill")

    session = DiagnosticSession(
        student_id=student.id,
        target_skill_id=target.id,
        current_skill_id=target.id,
        curriculum_id=scope.curriculum_id,
        curriculum_enrollment_id=scope.enrollment_id,
        status="ACTIVE",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return DiagnosticOut(
        session_id=session.id,
        status=session.status,
        target_skill_id=session.target_skill_id,
        current_skill_id=session.current_skill_id,
        question_count=session.question_count,
        max_questions=session.max_questions,
        problem=_problem_out(problem),
        message="Answer this diagnostic question independently. No hints are used during placement.",
    )


@router.post("/sessions/{session_id}/respond", response_model=DiagnosticOut)
def respond_to_diagnostic(
    session_id: uuid.UUID,
    payload: DiagnosticRespondIn,
    db: DbSession,
) -> DiagnosticOut:
    session = db.get(DiagnosticSession, session_id)
    if session is None or session.status != "ACTIVE":
        raise HTTPException(404, "Active diagnostic session not found")

    scope = _diagnostic_scope(db, session)
    _require_session_skill_scope(db, session=session, skill_id=session.current_skill_id)
    problem = db.get(Problem, payload.problem_id)
    if problem is None or problem.primary_skill_id != session.current_skill_id:
        raise HTTPException(400, "Problem does not belong to the current diagnostic skill")

    progress = _student_skill(db, session.student_id, session.current_skill_id)
    evidence = record_evidence(
        db,
        progress=progress,
        prompt=problem.prompt,
        answer=payload.answer,
        canonical_answer=problem.canonical_answer or "",
        assistance_level=0,
    )

    session.question_count += 1
    diagnostic_attempt = DiagnosticAttempt(
        diagnostic_session_id=session.id,
        skill_id=session.current_skill_id,
        problem_id=problem.id,
        student_answer=payload.answer,
        normalized_answer=evidence.evaluation.normalized_answer,
        is_correct=evidence.evaluation.correct,
        misconception_id=evidence.misconception.id if evidence.misconception else None,
        evaluation_confidence=Decimal(str(evidence.evaluation.confidence)),
        sequence_number=session.question_count,
    )
    db.add(diagnostic_attempt)
    db.flush()

    db.add(
        MasteryEvent(
            student_id=session.student_id,
            skill_id=session.current_skill_id,
            attempt_id=None,
            previous_score=evidence.previous_score,
            new_score=progress.mastery_score,
            previous_confidence=evidence.previous_confidence,
            new_confidence=progress.confidence_score,
            reason="DIAGNOSTIC_EVIDENCE",
            metadata_json={
                "diagnostic_session_id": str(session.id),
                "diagnostic_attempt_id": str(diagnostic_attempt.id),
                "correct": evidence.evaluation.correct,
                "curriculum_id": str(scope.curriculum_id),
                "curriculum_enrollment_id": (
                    str(scope.enrollment_id) if scope.enrollment_id else None
                ),
            },
        )
    )

    decision = decide_next_probe(
        db,
        session=session,
        misconception=evidence.misconception,
    )

    next_problem = None
    if decision.complete:
        session.status = "COMPLETED"
        session.recommended_skill_id = decision.recommended_skill_id
        session.placement_reason = decision.reason
        session.completed_at = datetime.now(UTC)
        message = "Diagnostic complete. A recommended starting skill is now available."
    else:
        previous_skill_id = session.current_skill_id
        next_skill_id = decision.next_skill_id or previous_skill_id
        _require_session_skill_scope(db, session=session, skill_id=next_skill_id)
        if next_skill_id != previous_skill_id:
            session.blocked_skill_id = previous_skill_id
            session.current_skill_id = next_skill_id
        exclude_problem_id = problem.id if session.current_skill_id == previous_skill_id else None
        next_problem = _next_problem(
            db,
            session.student_id,
            session.current_skill_id,
            current_problem_id=exclude_problem_id,
        )
        if next_problem is None:
            raise HTTPException(404, "No diagnostic problem configured for next probe skill")
        message = "Response recorded. Continue with the next diagnostic question."

    db.commit()
    return DiagnosticOut(
        session_id=session.id,
        status=session.status,
        target_skill_id=session.target_skill_id,
        current_skill_id=session.current_skill_id,
        question_count=session.question_count,
        max_questions=session.max_questions,
        problem=_problem_out(next_problem),
        last_answer_correct=evidence.evaluation.correct,
        recommended_skill_id=session.recommended_skill_id,
        placement_reason=session.placement_reason,
        message=message,
    )


@router.get("/sessions/{session_id}/result", response_model=DiagnosticResultOut)
def diagnostic_result(session_id: uuid.UUID, db: DbSession) -> DiagnosticResultOut:
    session = db.get(DiagnosticSession, session_id)
    if session is None:
        raise HTTPException(404, "Diagnostic session not found")

    _require_session_skill_scope(db, session=session, skill_id=session.target_skill_id)
    attempts = list(
        db.scalars(
            select(DiagnosticAttempt)
            .where(DiagnosticAttempt.diagnostic_session_id == session.id)
            .order_by(DiagnosticAttempt.sequence_number)
        ).all()
    )
    by_skill: dict[uuid.UUID, tuple[int, int]] = {}
    for attempt in attempts:
        _require_session_skill_scope(db, session=session, skill_id=attempt.skill_id)
        correct, incorrect = by_skill.get(attempt.skill_id, (0, 0))
        if attempt.is_correct:
            correct += 1
        else:
            incorrect += 1
        by_skill[attempt.skill_id] = (correct, incorrect)

    evidence_rows: list[DiagnosticSkillEvidenceOut] = []
    for skill_id, (correct, incorrect) in by_skill.items():
        progress = _student_skill(db, session.student_id, skill_id)
        evidence_rows.append(
            DiagnosticSkillEvidenceOut(
                skill_id=skill_id,
                correct_count=correct,
                incorrect_count=incorrect,
                mastery_score=progress.mastery_score,
                confidence_score=progress.confidence_score,
            )
        )

    return DiagnosticResultOut(
        session_id=session.id,
        status=session.status,
        target_skill_id=session.target_skill_id,
        recommended_skill_id=session.recommended_skill_id,
        placement_reason=session.placement_reason,
        question_count=session.question_count,
        evidence=evidence_rows,
    )
