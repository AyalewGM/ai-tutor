import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adaptive_api import _focus
from app.api import _problem_out, _student_skill, _tutor_context
from app.core.database import get_db
from app.models import (
    Attempt,
    MasteryEvent,
    Problem,
    Skill,
    Student,
    TutorSession,
    TutorTurn,
)
from app.schemas import EvaluationOut, MasteryOut, RespondIn, RespondOut, TutorOut
from app.services.attempt_evidence import record_evidence
from app.services.focus_controller import apply_focus_policy
from app.services.problem_selection import select_next_problem
from app.services.state_machine import TutorContext as StateContext
from app.services.state_machine import determine_next_action
from app.services.tutor_engine import tutor_engine

router = APIRouter(prefix="/adaptive-tutor", tags=["adaptive-tutor"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/sessions/{session_id}/respond", response_model=RespondOut)
def respond(session_id: uuid.UUID, payload: RespondIn, db: DbSession) -> RespondOut:
    session = db.get(TutorSession, session_id)
    if session is None or session.status != "ACTIVE":
        raise HTTPException(404, "Active tutor session not found")

    active_skill_id = session.active_skill_id or session.primary_skill_id
    problem = db.get(Problem, payload.problem_id)
    if problem is None or problem.primary_skill_id != active_skill_id:
        raise HTTPException(400, "Problem does not belong to active learning focus")

    student = db.get(Student, session.student_id)
    skill = db.get(Skill, active_skill_id)
    if student is None or skill is None:
        raise HTTPException(404, "Student or skill not found")

    progress = _student_skill(db, session.student_id, active_skill_id)
    evidence = record_evidence(
        db,
        progress=progress,
        prompt=problem.prompt,
        answer=payload.answer,
        canonical_answer=problem.canonical_answer or "",
        assistance_level=payload.assistance_level,
    )

    independent_successes = db.scalar(
        select(func.count(Attempt.id))
        .join(Problem, Problem.id == Attempt.problem_id)
        .where(
            Attempt.session_id == session.id,
            Problem.primary_skill_id == active_skill_id,
            Attempt.is_correct.is_(True),
            Attempt.assistance_level == 0,
        )
    ) or 0
    transition = determine_next_action(
        StateContext(
            state=session.current_state,
            correct=evidence.evaluation.correct,
            assistance_level=payload.assistance_level,
            misconception_count=evidence.misconception_count,
            consecutive_independent_successes=int(independent_successes),
        )
    )

    attempt_number = (
        db.scalar(
            select(func.count(Attempt.id)).where(
                Attempt.session_id == session.id,
                Attempt.problem_id == problem.id,
            )
        )
        or 0
    ) + 1
    attempt = Attempt(
        session_id=session.id,
        student_id=session.student_id,
        problem_id=problem.id,
        student_answer=payload.answer,
        normalized_answer=evidence.evaluation.normalized_answer,
        is_correct=evidence.evaluation.correct,
        attempt_number=attempt_number,
        assistance_level=payload.assistance_level,
        misconception_id=evidence.misconception.id if evidence.misconception else None,
        misconception_confidence=(
            Decimal(str(evidence.evaluation.misconception_confidence))
            if evidence.evaluation.misconception_confidence is not None
            else None
        ),
        evaluation_confidence=Decimal(str(evidence.evaluation.confidence)),
        state_at_attempt=session.current_state,
    )
    db.add(attempt)
    db.flush()
    db.add(
        MasteryEvent(
            student_id=session.student_id,
            skill_id=active_skill_id,
            attempt_id=attempt.id,
            previous_score=evidence.previous_score,
            new_score=progress.mastery_score,
            previous_confidence=evidence.previous_confidence,
            new_confidence=progress.confidence_score,
            reason="ATTEMPT_EVIDENCE",
            metadata_json={
                "correct": evidence.evaluation.correct,
                "assistance_level": payload.assistance_level,
            },
        )
    )

    transition = apply_focus_policy(
        db,
        session=session,
        progress=progress,
        transition=transition,
        correct=evidence.evaluation.correct,
        assistance_level=payload.assistance_level,
    )
    session.current_state = transition.state

    next_skill_id = session.active_skill_id or session.primary_skill_id
    next_skill = db.get(Skill, next_skill_id)
    next_progress = _student_skill(db, session.student_id, next_skill_id)
    if next_skill is None:
        raise HTTPException(404, "Active skill not found")
    next_problem = select_next_problem(
        db,
        skill_id=next_skill_id,
        current_problem_id=problem.id if problem.primary_skill_id == next_skill_id else None,
        current_difficulty=next_progress.current_difficulty,
        state=transition.state,
        correct=evidence.evaluation.correct,
    )

    generation = tutor_engine.generate(
        _tutor_context(
            db,
            student=student,
            skill=next_skill,
            state=transition.state,
            action=transition.action,
            hint_level=transition.hint_level,
            problem=problem,
            next_problem=next_problem,
            student_answer=payload.answer,
            misconception=evidence.misconception,
        )
    )
    db.add(
        TutorTurn(
            session_id=session.id,
            role="TUTOR",
            message=generation.message,
            state=transition.state,
            pedagogical_action=transition.action,
            problem_id=next_problem.id if next_problem else problem.id,
            attempt_id=attempt.id,
            llm_model=generation.model,
            metadata_json={
                "generation_source": generation.source,
                "target_skill_id": str(session.primary_skill_id),
                "active_skill_id": str(next_skill_id),
                "remediation_reason": session.remediation_reason,
            },
        )
    )
    db.commit()

    return RespondOut(
        session_id=session.id,
        state=transition.state,
        evaluation=EvaluationOut(
            correct=evidence.evaluation.correct,
            confidence=evidence.evaluation.confidence,
            misconception_code=evidence.evaluation.misconception_code,
            misconception_confidence=evidence.evaluation.misconception_confidence,
        ),
        tutor=TutorOut(
            action=transition.action,
            hint_level=transition.hint_level,
            message=generation.message,
        ),
        mastery=MasteryOut(
            score=next_progress.mastery_score,
            confidence=next_progress.confidence_score,
        ),
        focus=_focus(session),
        next_problem=_problem_out(next_problem),
    )
