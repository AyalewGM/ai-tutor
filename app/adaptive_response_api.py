import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adaptive_api import _focus
from app.api import _problem_out, _student_skill, _tutor_context
from app.core.database import get_db
from app.hint_models import HintEvent
from app.models import (
    Attempt,
    MasteryEvent,
    Problem,
    Skill,
    SkillStatus,
    Student,
    TutorSession,
    TutorState,
    TutorTurn,
)
from app.schemas import EvaluationOut, MasteryOut, RespondIn, RespondOut, TutorOut
from app.services.attempt_evidence import record_evidence
from app.services.curriculum_scope import (
    CurriculumScopeError,
    require_session_scope,
    require_skill_in_scope,
)
from app.services.focus_controller import apply_focus_policy
from app.services.hint_policy import assistance_level_for_hint, hint_constraint, select_hint
from app.services.mastery_gate import evaluate_mastery_gate
from app.services.mastery_gate_evidence import load_mastery_gate_evidence
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
    try:
        scope = require_session_scope(db, session)
        require_skill_in_scope(db, skill_id=active_skill_id, scope=scope)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc

    problem = db.get(Problem, payload.problem_id)
    if problem is None or problem.primary_skill_id != active_skill_id:
        raise HTTPException(400, "Problem does not belong to active learning focus")

    student = db.get(Student, session.student_id)
    skill = db.get(Skill, active_skill_id)
    if student is None or skill is None:
        raise HTTPException(404, "Student or skill not found")

    state_at_attempt = session.current_state
    highest_hint_level = db.scalar(
        select(func.max(HintEvent.level)).where(
            HintEvent.session_id == session.id,
            HintEvent.problem_id == problem.id,
        )
    ) or 0
    effective_assistance_level = max(
        payload.assistance_level,
        assistance_level_for_hint(int(highest_hint_level)),
    )

    progress = _student_skill(db, session.student_id, active_skill_id)
    evidence = record_evidence(
        db,
        progress=progress,
        prompt=problem.prompt,
        answer=payload.answer,
        canonical_answer=problem.canonical_answer or "",
        assistance_level=effective_assistance_level,
    )

    prior_attempt_count = db.scalar(
        select(func.count(Attempt.id)).where(
            Attempt.session_id == session.id,
            Attempt.problem_id == problem.id,
        )
    ) or 0
    attempt_number = int(prior_attempt_count) + 1
    attempt = Attempt(
        session_id=session.id,
        student_id=session.student_id,
        problem_id=problem.id,
        student_answer=payload.answer,
        normalized_answer=evidence.evaluation.normalized_answer,
        is_correct=evidence.evaluation.correct,
        attempt_number=attempt_number,
        assistance_level=effective_assistance_level,
        misconception_id=evidence.misconception.id if evidence.misconception else None,
        misconception_confidence=(
            Decimal(str(evidence.evaluation.misconception_confidence))
            if evidence.evaluation.misconception_confidence is not None
            else None
        ),
        evaluation_confidence=Decimal(str(evidence.evaluation.confidence)),
        state_at_attempt=state_at_attempt,
    )
    db.add(attempt)
    db.flush()

    gate_evidence = load_mastery_gate_evidence(
        db,
        student_id=session.student_id,
        skill_id=active_skill_id,
    )
    gate_decision = evaluate_mastery_gate(
        mastery_score=progress.mastery_score,
        mastery_threshold=skill.mastery_threshold,
        independent_correct_count=gate_evidence.independent_correct_count,
        strong_help_seen=gate_evidence.strong_help_seen,
        independent_successes_after_strong_help=(
            gate_evidence.independent_successes_after_strong_help
        ),
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
            state=state_at_attempt,
            correct=evidence.evaluation.correct,
            assistance_level=effective_assistance_level,
            misconception_count=evidence.misconception_count,
            consecutive_independent_successes=int(independent_successes),
            mastery_gate_eligible=gate_decision.eligible,
        )
    )

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
                "assistance_level": effective_assistance_level,
                "reported_assistance_level": payload.assistance_level,
                "highest_hint_level": int(highest_hint_level),
                "curriculum_id": str(scope.curriculum_id),
                "curriculum_enrollment_id": (
                    str(scope.enrollment_id) if scope.enrollment_id else None
                ),
            },
        )
    )

    if state_at_attempt in {TutorState.INDEPENDENT_PRACTICE, TutorState.MASTERY_CHECK}:
        db.add(
            MasteryEvent(
                student_id=session.student_id,
                skill_id=active_skill_id,
                attempt_id=attempt.id,
                previous_score=progress.mastery_score,
                new_score=progress.mastery_score,
                previous_confidence=progress.confidence_score,
                new_confidence=progress.confidence_score,
                reason="MASTERY_GATE_DECISION",
                metadata_json={
                    "eligible": gate_decision.eligible,
                    "reason": gate_decision.reason,
                    "mastery_score": str(progress.mastery_score),
                    "mastery_threshold": str(skill.mastery_threshold),
                    "independent_correct_count": gate_evidence.independent_correct_count,
                    "strong_help_seen": gate_evidence.strong_help_seen,
                    "independent_successes_after_strong_help": (
                        gate_evidence.independent_successes_after_strong_help
                    ),
                    "curriculum_id": str(scope.curriculum_id),
                },
            )
        )

    transition = apply_focus_policy(
        db,
        session=session,
        progress=progress,
        transition=transition,
        correct=evidence.evaluation.correct,
        assistance_level=effective_assistance_level,
    )

    if state_at_attempt == TutorState.MASTERY_CHECK:
        passed_mastery_check = (
            transition.action == "MARK_MASTERED"
            and evidence.evaluation.correct
            and effective_assistance_level == 0
        )
        db.add(
            MasteryEvent(
                student_id=session.student_id,
                skill_id=active_skill_id,
                attempt_id=attempt.id,
                previous_score=progress.mastery_score,
                new_score=progress.mastery_score,
                previous_confidence=progress.confidence_score,
                new_confidence=progress.confidence_score,
                reason="MASTERY_CHECK_RESULT",
                metadata_json={
                    "passed": passed_mastery_check,
                    "correct": evidence.evaluation.correct,
                    "assistance_level": effective_assistance_level,
                    "curriculum_id": str(scope.curriculum_id),
                },
            )
        )
        if passed_mastery_check:
            progress.status = SkillStatus.MASTERED
            session.ending_mastery = progress.mastery_score

    session.current_state = transition.state

    jit_decision = select_hint(
        state=state_at_attempt,
        highest_level_used=int(highest_hint_level),
        misconception_confidence=evidence.evaluation.misconception_confidence,
        repeated_unsuccessful_attempts=(
            attempt_number if not evidence.evaluation.correct else 0
        ),
    )
    issue_jit_hint = (
        not evidence.evaluation.correct
        and evidence.misconception is not None
        and jit_decision.allowed
        and (session.active_skill_id or session.primary_skill_id) == active_skill_id
    )

    next_skill_id = session.active_skill_id or session.primary_skill_id
    try:
        next_skill = require_skill_in_scope(db, skill_id=next_skill_id, scope=scope)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc
    next_progress = _student_skill(db, session.student_id, next_skill_id)

    if issue_jit_hint:
        next_problem = problem
        tutor_action = "GIVE_HINT"
        tutor_hint_level = jit_decision.level
        tutor_skill = skill
        generation_state = transition.state
    else:
        next_problem = select_next_problem(
            db,
            skill_id=next_skill_id,
            current_problem_id=problem.id if problem.primary_skill_id == next_skill_id else None,
            current_difficulty=next_progress.current_difficulty,
            state=transition.state,
            correct=evidence.evaluation.correct,
        )
        tutor_action = transition.action
        tutor_hint_level = transition.hint_level
        tutor_skill = next_skill
        generation_state = transition.state

    generation = tutor_engine.generate(
        _tutor_context(
            db,
            student=student,
            skill=tutor_skill,
            state=generation_state,
            action=tutor_action,
            hint_level=tutor_hint_level,
            problem=problem,
            next_problem=next_problem,
            student_answer=payload.answer,
            misconception=evidence.misconception,
        )
    )
    turn = TutorTurn(
        session_id=session.id,
        role="TUTOR",
        message=generation.message,
        state=generation_state,
        pedagogical_action=tutor_action,
        problem_id=next_problem.id if next_problem else problem.id,
        attempt_id=attempt.id,
        llm_model=generation.model,
        metadata_json={
            "generation_source": generation.source,
            "target_skill_id": str(session.primary_skill_id),
            "active_skill_id": str(next_skill_id),
            "remediation_reason": session.remediation_reason,
            "hint_level": tutor_hint_level,
            "hint_trigger": jit_decision.trigger if issue_jit_hint else None,
            "hint_constraint": (
                hint_constraint(tutor_hint_level)
                if issue_jit_hint and tutor_hint_level is not None
                else None
            ),
            "effective_assistance_level": effective_assistance_level,
            "mastery_gate_eligible": gate_decision.eligible,
            "mastery_gate_reason": gate_decision.reason,
            "curriculum_id": str(scope.curriculum_id),
            "curriculum_enrollment_id": (
                str(scope.enrollment_id) if scope.enrollment_id else None
            ),
        },
    )
    db.add(turn)
    db.flush()

    if issue_jit_hint:
        db.add(
            HintEvent(
                session_id=session.id,
                student_id=session.student_id,
                skill_id=active_skill_id,
                problem_id=problem.id,
                attempt_id=attempt.id,
                tutor_turn_id=turn.id,
                level=jit_decision.level,
                trigger=jit_decision.trigger,
                generation_source=generation.source,
                provider=generation.provider,
                llm_model=generation.model,
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
            action=tutor_action,
            hint_level=tutor_hint_level,
            message=generation.message,
        ),
        mastery=MasteryOut(
            score=next_progress.mastery_score,
            confidence=next_progress.confidence_score,
        ),
        focus=_focus(session),
        next_problem=_problem_out(next_problem),
    )
