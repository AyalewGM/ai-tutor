import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adaptive_api import _focus
from app.api import _problem_out, _student_skill, _tutor_context
from app.core.database import SessionLocal, get_db
from app.hint_models import HintEvent
from app.identity import CurrentLearningAccess, require_learning_owns_session
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
from app.schemas import (
    AwardOut,
    EvaluationOut,
    GrowthOut,
    MasteryOut,
    PhotoLineOut,
    PhotoScanOut,
    RespondIn,
    RespondOut,
    TutorOut,
    WorkStepIn,
    WorkStepOut,
)
from app.services import chat_cpa, pedagogy_engine, photo_ocr, stepwork, visualization
from app.services.attempt_evidence import record_evidence
from app.services.awards import (
    BADGE_XP,
    attempt_xp,
    award_out,
    evaluate_awards,
    learner_progress,
    level_for_xp,
)
from app.services.curriculum_scope import (
    CurriculumScopeError,
    require_session_scope,
    require_skill_in_scope,
)
from app.services.focus_controller import apply_focus_policy
from app.services.hint_policy import assistance_level_for_hint, hint_constraint, select_hint
from app.services.learning_assessment import has_active_assessment
from app.services.mastery_gate import evaluate_mastery_gate
from app.services.mastery_gate_evidence import load_mastery_gate_evidence
from app.services.problem_generation import regenerate_variant
from app.services.problem_selection import select_next_problem
from app.services.review_schedule import (
    REVIEW_PASSED,
    REVIEW_REASON,
    apply_review_policy,
    schedule_review,
)
from app.services.state_machine import Transition, determine_next_action
from app.services.state_machine import TutorContext as StateContext
from app.services.tutor_engine import fallback_message
from app.services.usage_metering import ai_generate
from app.telemetry import TelemetryEnvelope, publish_telemetry_fail_open

router = APIRouter(prefix="/adaptive-tutor", tags=["adaptive-tutor"])
DbSession = Annotated[Session, Depends(get_db)]


def _publish_adaptive_event(
    *,
    event_type: str,
    session: TutorSession,
    curriculum_id: uuid.UUID,
    skill_id: uuid.UUID,
    payload: dict[str, object],
) -> None:
    """Publish metadata only after authoritative tutoring state commits."""
    publish_telemetry_fail_open(
        SessionLocal,
        TelemetryEnvelope(
            event_type=event_type,
            learner_pseudonymous_id=str(session.student_id),
            curriculum_id=curriculum_id,
            session_id=session.id,
            skill_id=skill_id,
            payload=payload,
        ),
    )


@router.post("/sessions/{session_id}/respond", response_model=RespondOut)
def respond(
    session_id: uuid.UUID, payload: RespondIn, access: CurrentLearningAccess, db: DbSession
) -> RespondOut:
    session = require_learning_owns_session(db, access, db.get(TutorSession, session_id))

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
    highest_hint_level = (
        db.scalar(
            select(func.max(HintEvent.level)).where(
                HintEvent.session_id == session.id,
                HintEvent.problem_id == problem.id,
            )
        )
        or 0
    )
    # Step errors and revealed work lines count as assistance — derived from
    # server-side records, not the client payload.
    step_errors = (
        db.scalar(
            select(func.count(TutorTurn.id)).where(
                TutorTurn.session_id == session.id,
                TutorTurn.problem_id == problem.id,
                TutorTurn.pedagogical_action == "WORK_STEP",
                TutorTurn.metadata_json["step_status"].as_string() == "invalid",
            )
        )
        or 0
    )
    step_revealed = (
        db.scalar(
            select(func.count(TutorTurn.id)).where(
                TutorTurn.session_id == session.id,
                TutorTurn.problem_id == problem.id,
                TutorTurn.pedagogical_action == "WORK_STEP",
                TutorTurn.metadata_json["revealed"].as_boolean(),
            )
        )
        or 0
    )
    step_assistance = (1 if step_errors else 0) + (1 if step_revealed else 0)
    effective_assistance_level = max(
        payload.assistance_level,
        assistance_level_for_hint(int(highest_hint_level)),
        min(step_assistance, 4),
    )

    progress = _student_skill(db, session.student_id, active_skill_id)
    # A misconception observed during graded work steps is evidence even when
    # the final answer recovered; the final-answer classification still wins
    # when both fire.
    step_misconception_code = db.scalar(
        select(TutorTurn.metadata_json["misconception_code"].as_string())
        .where(
            TutorTurn.session_id == session.id,
            TutorTurn.problem_id == problem.id,
            TutorTurn.pedagogical_action == "WORK_STEP",
            TutorTurn.metadata_json["step_status"].as_string() == "invalid",
            TutorTurn.metadata_json["misconception_code"].as_string().is_not(None),
        )
        .order_by(TutorTurn.created_at.desc(), TutorTurn.id.desc())
    )
    evidence = record_evidence(
        db,
        progress=progress,
        prompt=problem.prompt,
        answer=payload.answer,
        canonical_answer=problem.canonical_answer or "",
        assistance_level=effective_assistance_level,
        problem_difficulty=problem.difficulty,
        answer_kind=problem.answer_kind,
        choices=problem.choices,
        step_misconception_code=step_misconception_code,
    )

    prior_attempt_count = (
        db.scalar(
            select(func.count(Attempt.id)).where(
                Attempt.session_id == session.id,
                Attempt.problem_id == problem.id,
            )
        )
        or 0
    )
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

    independent_successes = (
        db.scalar(
            select(func.count(Attempt.id))
            .join(Problem, Problem.id == Attempt.problem_id)
            .where(
                Attempt.session_id == session.id,
                Problem.primary_skill_id == active_skill_id,
                Attempt.is_correct.is_(True),
                Attempt.assistance_level == 0,
            )
        )
        or 0
    )
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
    engine_action = transition.action

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

    review_outcome = None
    if session.remediation_reason == REVIEW_REASON:
        transition, review_outcome = apply_review_policy(
            db,
            session=session,
            progress=progress,
            transition=transition,
            correct=evidence.evaluation.correct,
            assistance_level=effective_assistance_level,
        )
    else:
        transition = apply_focus_policy(
            db,
            session=session,
            progress=progress,
            transition=transition,
            correct=evidence.evaluation.correct,
            assistance_level=effective_assistance_level,
        )

    review_scheduled_payload: dict[str, object] | None = None
    passed_mastery_check = False
    gap_fixed = False
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
            review_schedule = schedule_review(db, progress=progress)
            review_scheduled_payload = {
                "due_at": review_schedule.due_at.isoformat(),
                "interval_index": review_schedule.interval_index,
            }
            if (
                session.remediation_reason == REVIEW_REASON
                and session.active_skill_id
                and session.active_skill_id != session.primary_skill_id
            ):
                session.active_skill_id = session.primary_skill_id
                session.remediation_reason = None
                gap_fixed = True
                transition = Transition(TutorState.GUIDED_PRACTICE, "RESUME_TARGET")

    session.current_state = transition.state
    if engine_action == "INCREASE_DIFFICULTY":
        progress.current_difficulty = min(10, progress.current_difficulty + 1)
    elif engine_action == "REMEDIATE":
        progress.current_difficulty = max(1, progress.current_difficulty - 1)

    jit_decision = select_hint(
        state=state_at_attempt,
        highest_level_used=int(highest_hint_level),
        misconception_confidence=evidence.evaluation.misconception_confidence,
        repeated_unsuccessful_attempts=(attempt_number if not evidence.evaluation.correct else 0),
        independent_assessment_active=has_active_assessment(
            db, student_id=session.student_id,
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
        next_problem = None
        if evidence.evaluation.correct is False and problem.primary_skill_id == next_skill_id:
            next_problem = regenerate_variant(
                db, source_problem=problem, session_id=session.id
            )
        if next_problem is None:
            next_problem = select_next_problem(
                db,
                skill_id=next_skill_id,
                current_problem_id=problem.id
                if problem.primary_skill_id == next_skill_id
                else None,
                current_difficulty=next_progress.current_difficulty,
                state=transition.state,
                correct=evidence.evaluation.correct,
                session_id=session.id,
            )
        tutor_action = transition.action
        tutor_hint_level = transition.hint_level
        tutor_skill = next_skill
        generation_state = transition.state

    tutor_context = _tutor_context(
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
        session_id=session.id,
    )
    generation = ai_generate(
        db,
        tutor_context,
        student=student,
        session_id=session.id,
        action=tutor_action,
        # Correct-answer feedback needs no model call; the deterministic
        # fallback covers it. The LLM only engages where language adds
        # pedagogical value: misses, hints, misconceptions.
        use_llm=not evidence.evaluation.correct,
    )
    message = chat_cpa.sanitize_cpa_blocks(
        generation.message, canonical_answer=problem.canonical_answer
    )
    answer_leak_blocked = False
    if generation.source == "llm" and chat_cpa.text_reveals_answer(
        message, problem.canonical_answer
    ):
        # The model stated the solved form in prose. Swap in the
        # deterministic voice — Socratic integrity is not negotiable.
        message = fallback_message(tutor_context)
        answer_leak_blocked = True
    if not evidence.evaluation.correct:
        block = visualization.chat_cpa_block(visualization.visualization_for(problem))
        if block and "```json:cpa" not in message:
            message = f"{message}\n\n{block}"
    turn = TutorTurn(
        session_id=session.id,
        role="TUTOR",
        message=message,
        state=generation_state,
        pedagogical_action=tutor_action,
        problem_id=next_problem.id if next_problem else problem.id,
        attempt_id=attempt.id,
        llm_model=generation.model,
        metadata_json={
            "generation_source": generation.source,
            "answer_leak_blocked": answer_leak_blocked,
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
            "curriculum_enrollment_id": (str(scope.enrollment_id) if scope.enrollment_id else None),
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

    new_awards = evaluate_awards(
        db,
        student_id=session.student_id,
        session_id=session.id,
        active_skill_id=active_skill_id,
        correct=bool(evidence.evaluation.correct),
        engine_action=engine_action,
        mastery_passed=passed_mastery_check,
        review_passed=review_outcome == REVIEW_PASSED,
        gap_fixed=gap_fixed,
    )
    db.flush()

    xp_earned = attempt_xp(
        bool(evidence.evaluation.correct),
        effective_assistance_level,
        problem.difficulty,
    ) + sum(BADGE_XP.get(award.badge_code, 0) for award in new_awards)
    progress = learner_progress(db, session.student_id)
    level_now, _ = level_for_xp(progress["xp"])
    level_before, _ = level_for_xp(progress["xp"] - xp_earned)
    growth_out = {
        **progress,
        "leveled_up": level_now > level_before,
    }

    db.commit()

    _publish_adaptive_event(
        event_type="mastery.evidence_recorded",
        session=session,
        curriculum_id=scope.curriculum_id,
        skill_id=active_skill_id,
        payload={
            "correct": evidence.evaluation.correct,
            "assistance_level": effective_assistance_level,
            "state": state_at_attempt.value,
            "mastery_gate_eligible": gate_decision.eligible,
        },
    )
    if review_outcome is not None:
        _publish_adaptive_event(
            event_type="review.outcome_recorded",
            session=session,
            curriculum_id=scope.curriculum_id,
            skill_id=active_skill_id,
            payload={
                "passed": review_outcome == REVIEW_PASSED,
                "correct": evidence.evaluation.correct,
                "assistance_level": effective_assistance_level,
            },
        )
    if review_scheduled_payload is not None:
        _publish_adaptive_event(
            event_type="review.scheduled",
            session=session,
            curriculum_id=scope.curriculum_id,
            skill_id=active_skill_id,
            payload=review_scheduled_payload,
        )
    _publish_adaptive_event(
        event_type="model.generation_completed",
        session=session,
        curriculum_id=scope.curriculum_id,
        skill_id=next_skill_id,
        payload={
            "request_id": generation.request_id,
            "source": generation.source,
            "provider": generation.provider,
            "model": generation.model,
            "latency_ms": generation.latency_ms,
            "success": generation.source == "llm",
        },
    )

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
            message=message,
        ),
        mastery=MasteryOut(
            score=next_progress.mastery_score,
            confidence=next_progress.confidence_score,
        ),
        focus=_focus(session),
        next_problem=_problem_out(next_problem),
        new_awards=[AwardOut(**award_out(db, award)) for award in new_awards],
        xp_earned=xp_earned,
        growth=GrowthOut(**growth_out),
    )


@router.post("/sessions/{session_id}/work-step", response_model=WorkStepOut)
def work_step(
    session_id: uuid.UUID, payload: WorkStepIn, access: CurrentLearningAccess, db: DbSession
) -> WorkStepOut:
    """Grade one intermediate work line for a step-supporting problem.

    Accepted lines and the invalid streak are reconstructed from recorded
    WORK_STEP turns, so the escalation policy is server-derived and cannot be
    reset by the client.
    """
    session = require_learning_owns_session(db, access, db.get(TutorSession, session_id))
    problem = db.get(Problem, payload.problem_id)
    active_skill_id = session.active_skill_id or session.primary_skill_id
    if problem is None or problem.primary_skill_id != active_skill_id:
        raise HTTPException(400, "Problem does not support step-by-step work")
    if not stepwork.problem_supports_steps(problem):
        raise HTTPException(400, "Problem does not support step-by-step work")
    start = stepwork.starting_point(problem)
    word_model = stepwork.word_canonical_value(problem)

    turns = db.scalars(
        select(TutorTurn)
        .where(
            TutorTurn.session_id == session.id,
            TutorTurn.problem_id == problem.id,
            TutorTurn.pedagogical_action == "WORK_STEP",
        )
        .order_by(TutorTurn.created_at, TutorTurn.id)
    ).all()
    accepted: list[str] = []
    invalid_count = 0
    for turn in turns:
        meta = turn.metadata_json or {}
        status = meta.get("step_status")
        if status in {"valid", "solved"}:
            accepted.append(meta.get("normalized_line") or meta.get("line") or "")
            invalid_count = 0
        elif status == "invalid":
            invalid_count += 1

    if problem.problem_type == "ALGEBRA_WORD_PROBLEM":
        result = stepwork.check_algebra_word_step(
            problem.canonical_answer, word_model, accepted, payload.line, invalid_count
        )
    elif word_model is not None:
        result = stepwork.check_word_step(
            problem.canonical_answer, word_model, accepted, payload.line, invalid_count
        )
    else:
        result = stepwork.check_step(start, accepted, payload.line, invalid_count)

    new_meta: dict = {
        "step_status": result.status,
        "line": payload.line[:200],
        "normalized_line": result.normalized_line,
        "misconception_code": result.misconception_code,
        "revealed": bool(result.revealed_line),
    }

    # --- Pedagogy layer: reverse-Socratic challenge resolution, CPA level ---
    challenge_turn = db.scalars(
        select(TutorTurn)
        .where(
            TutorTurn.session_id == session.id,
            TutorTurn.problem_id == problem.id,
            TutorTurn.pedagogical_action == "REVERSE_CHALLENGE",
        )
        .order_by(TutorTurn.created_at.desc(), TutorTurn.id.desc())
        .limit(1)
    ).first()
    challenge_pending = challenge_turn is not None and "resolved_outcome" not in (
        challenge_turn.metadata_json or {}
    )
    challenge_outcome: str | None = None
    feedback = result.feedback
    if challenge_pending:
        presented = (challenge_turn.metadata_json or {}).get("presented_line")
        if pedagogy_engine.line_matches(payload.line, presented):
            challenge_outcome = "missed"
            feedback = (
                "Careful — that repeats the slip in my attempt. "
                "What should happen to keep both sides balanced?"
            )
        elif result.status in {"valid", "solved"}:
            challenge_outcome = "spotted"
            feedback = f"Nice catch — you spotted my mistake. {result.feedback or 'That step works.'}"
        else:
            challenge_outcome = "unresolved"
        new_meta["challenge_outcome"] = challenge_outcome
        challenge_turn.metadata_json = {
            **(challenge_turn.metadata_json or {}),
            "resolved_outcome": challenge_outcome,
        }

    state = pedagogy_engine.evaluate_pedagogical_state(
        [*(t.metadata_json or {} for t in turns), new_meta],
        prior_cpa=session.cpa_level or "ABSTRACT",
        challenge_pending=challenge_pending,
    )
    if state.cpa_level != session.cpa_level:
        db.add(
            TutorTurn(
                session_id=session.id,
                role="TUTOR",
                message="",
                state=session.current_state,
                pedagogical_action="CPA_TRANSITION",
                problem_id=problem.id,
                metadata_json={"from": session.cpa_level, "to": state.cpa_level},
            )
        )
        session.cpa_level = state.cpa_level

    # The line just graded becomes the newest accepted line when it lands.
    latest_accepted = (
        (result.normalized_line or payload.line)
        if result.status in {"valid", "solved"}
        else (accepted[-1] if accepted else None)
    )
    step_visual = None
    if state.cpa_level != "ABSTRACT":
        step_visual = visualization.step_visual(problem, latest_accepted)

    reverse_challenge = None
    if state.trigger_reverse_socratic:
        anchor = latest_accepted or (start or "")
        crafted = pedagogy_engine.craft_flawed_step(anchor)
        if crafted is not None:
            flawed_line, planted_code = crafted
            db.add(
                TutorTurn(
                    session_id=session.id,
                    role="TUTOR",
                    message=f"I tried this next step: {flawed_line}",
                    state=session.current_state,
                    pedagogical_action="REVERSE_CHALLENGE",
                    problem_id=problem.id,
                    metadata_json={
                        "presented_line": flawed_line,
                        "planted_code": planted_code,
                    },
                )
            )
            reverse_challenge = {
                "line": flawed_line,
                "prompt": "I tried this next step, but something feels off. Can you spot my mistake?",
            }

    db.add(
        TutorTurn(
            session_id=session.id,
            role="STUDENT",
            message=payload.line[:200],
            state=session.current_state,
            pedagogical_action="WORK_STEP",
            problem_id=problem.id,
            metadata_json=new_meta,
        )
    )
    db.commit()
    return WorkStepOut(
        status=result.status,
        feedback=feedback,
        misconception_code=result.misconception_code,
        revealed_line=result.revealed_line,
        normalized_line=result.normalized_line,
        invalid_count=(invalid_count + 1 if result.status == "invalid" else 0),
        cpa_level=state.cpa_level,
        step_visual=step_visual,
        reverse_challenge=reverse_challenge,
        challenge_outcome=challenge_outcome,
    )


OcrProvider = Annotated[photo_ocr.PhotoOcrProvider, Depends(photo_ocr.get_ocr_provider)]


@router.post("/sessions/{session_id}/work-photo/scan", response_model=PhotoScanOut)
async def work_photo_scan(
    session_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
    ocr: OcrProvider,
    file: Annotated[UploadFile, File()],
    problem_id: Annotated[uuid.UUID, Form()],
) -> PhotoScanOut:
    """Read photographed written work into editable lines.

    The image is processed in memory and never persisted. OCR output is a
    *suggestion*: the learner confirms or edits each line client-side, and
    only confirmed lines are submitted to ``work-step`` — so a misread can
    never be graded as a learner misconception.
    """
    session = require_learning_owns_session(db, access, db.get(TutorSession, session_id))
    problem = db.get(Problem, problem_id)
    active_skill_id = session.active_skill_id or session.primary_skill_id
    if problem is None or problem.primary_skill_id != active_skill_id:
        raise HTTPException(400, "Problem does not support step-by-step work")
    if not stepwork.problem_supports_steps(problem):
        raise HTTPException(400, "Problem does not support step-by-step work")
    if file.content_type not in photo_ocr.ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, "Upload a JPEG, PNG, or WebP photo")
    image = await file.read()
    if len(image) > photo_ocr.MAX_PHOTO_BYTES:
        raise HTTPException(413, "Photo is too large — keep it under 8 MB")
    try:
        result = ocr.scan(image, file.content_type)
    except photo_ocr.PhotoOcrUnavailable as exc:
        raise HTTPException(503, "Photo intake is not enabled") from exc
    except photo_ocr.PhotoOcrError as exc:
        raise HTTPException(502, "Could not read the photo — try a clearer shot") from exc
    if not result.lines:
        raise HTTPException(
            422, "No work lines found — photograph the written steps up close"
        )
    return PhotoScanOut(
        problem_id=problem.id,
        lines=[PhotoLineOut(text=l.text, needs_review=l.needs_review) for l in result.lines],
        engine=result.engine,
    )
