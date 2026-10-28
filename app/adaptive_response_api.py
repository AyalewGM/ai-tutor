import uuid
from decimal import Decimal
from fractions import Fraction
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adaptive_api import _focus
from app.api import _problem_out, _student_skill, _tutor_context
from app.content_models import ProblemContentMetadata
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
from app.services.content_publishing import permitted
from app.services.curriculum_scope import (
    CurriculumScopeError,
    require_session_scope,
    require_skill_in_scope,
)
from app.services.focus_controller import apply_focus_policy
from app.services.fraction_assessment_registry import AssessmentMode
from app.services.hint_policy import assistance_level_for_hint, hint_constraint, select_hint
from app.services.learning_assessment import (
    ASSESSMENT_BLOCK_MESSAGE,
    check_assessment_guard,
)
from app.services.mastery_gate import evaluate_mastery_gate
from app.services.mastery_gate_evidence import load_mastery_gate_evidence
from app.services.problem_generation import regenerate_variant
from app.services.problem_selection import _eligibility_column, select_next_problem
from app.services.published_reasoning_probe import (
    PublishedProbeUnavailable,
    resolve_published_reasoning_probe,
    server_guided_retest,
    server_unhinted_transfer,
)
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


class PublishedReasoningIn(BaseModel):
    problem_id: uuid.UUID
    choice_id: str


@router.get("/sessions/{session_id}/published-reasoning")
def published_reasoning_probe(
    session_id: uuid.UUID,
    problem_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
) -> dict[str, object]:
    """Give a neutral probe derived from an authenticated, stored wrong answer."""
    session = require_learning_owns_session(db, access, db.get(TutorSession, session_id))
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise HTTPException(404, "Problem not found")
    try:
        probe = resolve_published_reasoning_probe(db, session=session, problem=problem)
    except PublishedProbeUnavailable as exc:
        raise HTTPException(409, str(exc)) from exc
    # Misconception codes and evidence-choice oracles are server-private.
    return {"problem_id": problem_id, "stage": "CONFIRM_REASONING",
            "prompt": probe.prompt, "choices": list(probe.choices),
            "independent_evidence_eligible": False}


@router.post("/sessions/{session_id}/published-reasoning")
def submit_published_reasoning(
    session_id: uuid.UUID,
    payload: PublishedReasoningIn,
    access: CurrentLearningAccess,
    db: DbSession,
) -> dict[str, object]:
    """Confirm a misconception with a second reasoning probe; no mastery credit."""
    session = require_learning_owns_session(db, access, db.get(TutorSession, session_id))
    db.refresh(session, with_for_update=True)
    problem = db.get(Problem, payload.problem_id)
    if problem is None:
        raise HTTPException(404, "Problem not found")
    try:
        probe = resolve_published_reasoning_probe(db, session=session, problem=problem)
    except PublishedProbeUnavailable as exc:
        raise HTTPException(409, str(exc)) from exc
    allowed = {choice["id"] for choice in probe.choices}
    if payload.choice_id not in allowed:
        raise HTTPException(422, "Choose one of the presented reasoning options")
    if payload.choice_id != probe.confirming_choice_id:
        # Consume the reasoning choice without attributing a misconception.
        # Otherwise a learner could brute-force the confirmation oracle.
        db.add(TutorTurn(
            session_id=session.id, role="STUDENT", problem_id=problem.id,
            attempt_id=probe.attempt_id, state=TutorState.GUIDED_PRACTICE,
            pedagogical_action="PUBLISHED_REASONING_SUBMITTED",
            message="Reasoning choice submitted",
            metadata_json={"response_attempt_id": str(probe.attempt_id),
                           "independent_evidence_eligible": False},
        ))
        db.commit()
        return {
            "stage": "PRACTICE_RETRY",
            "neutral_prompt": "Your answer and reasoning do not confirm a specific error. Try the same operation on both complete sides.",
            "independent_evidence_eligible": False,
        }
    try:
        retest = server_guided_retest(
            problem, misconception_code=probe.misconception_code,
        )
    except PublishedProbeUnavailable as exc:
        raise HTTPException(409, str(exc)) from exc
    db.add(TutorTurn(
        session_id=session.id, role="STUDENT", problem_id=problem.id,
        attempt_id=probe.attempt_id, state=TutorState.GUIDED_PRACTICE,
        pedagogical_action="PUBLISHED_REASONING_CONFIRMED",
        message="Reasoning choice submitted",
        metadata_json={
            "misconception_code": probe.misconception_code,
            "confirmation_choice_id": payload.choice_id,
            "response_attempt_id": str(probe.attempt_id),
            "task_fingerprint": problem.solution["task_fingerprint"],
            "independent_evidence_eligible": False,
        },
    ))
    db.commit()
    return {
        "stage": "SOCRATIC_REPAIR",
        "socratic_repair_questions": list(probe.repair_questions),
        "repair_check": _published_repair_prompt(problem, 0),
        "independent_evidence_eligible": False,
        "mastery_eligible": False,
    }


def _published_repair_prompt(problem: Problem, step: int) -> str:
    """Two mathematical equalities checked server-side, never a mere text response."""
    coefficients = problem.solution.get("equation_coefficients", {})
    if set(("lhs_x", "lhs_constant", "rhs_x", "rhs_constant")) - coefficients.keys():
        raise HTTPException(409, "Published repair coefficients unavailable")
    if step == 0:
        return (
            "Subtract the right-side x term from both complete sides. "
            "What coefficient of x remains on the left? Enter an exact number."
        )
    return (
        "Subtract the original left-side constant from both complete sides. "
        "What constant remains on the right? Enter an exact number."
    )


class PublishedRepairIn(BaseModel):
    problem_id: uuid.UUID
    response: str


@router.post("/sessions/{session_id}/published-repair")
def submit_published_repair(
    session_id: uuid.UUID,
    payload: PublishedRepairIn,
    access: CurrentLearningAccess,
    db: DbSession,
) -> dict[str, object]:
    """Require two independently checked mathematical repair steps before retest."""
    if not 0 < len(payload.response) <= 64:
        raise HTTPException(422, "Enter an exact number")
    session = require_learning_owns_session(db, access, db.get(TutorSession, session_id))
    db.refresh(session, with_for_update=True)
    problem = db.get(Problem, payload.problem_id)
    if (
        session.status != "ACTIVE" or problem is None
        or problem.source_type != "PUBLISHED"
        or problem.primary_skill_id not in {session.primary_skill_id, session.active_skill_id}
    ):
        raise HTTPException(409, "Repair is unavailable")
    turns = list(db.scalars(select(TutorTurn).where(
        TutorTurn.session_id == session.id,
        TutorTurn.problem_id == problem.id,
        TutorTurn.pedagogical_action.in_((
            "PUBLISHED_REASONING_CONFIRMED",
            "PUBLISHED_REPAIR_RESULT",
            "PUBLISHED_GUIDED_RETEST_ISSUED",
        )),
    ).order_by(TutorTurn.created_at.asc(), TutorTurn.id.asc())))
    confirmed = [t for t in turns if t.pedagogical_action == "PUBLISHED_REASONING_CONFIRMED"]
    checks = [t for t in turns if t.pedagogical_action == "PUBLISHED_REPAIR_RESULT"]
    if len(confirmed) != 1 or any(
        t.pedagogical_action == "PUBLISHED_GUIDED_RETEST_ISSUED" for t in turns
    ) or len(checks) >= 4 or any(
        not isinstance(t.metadata_json, dict)
        or t.attempt_id != confirmed[0].attempt_id
        for t in checks
    ):
        raise HTTPException(409, "Repair stage is unavailable or complete")
    passed = [t for t in checks if t.metadata_json["correct"] is True]
    if len(passed) > 2 or any(
        t.metadata_json.get("step") != index for index, t in enumerate(passed)
    ):
        raise HTTPException(409, "Repair proof is inconsistent")
    step = len(passed)
    if step >= 2:
        raise HTTPException(409, "Repair already complete")
    coefficients = problem.solution.get("equation_coefficients", {})
    try:
        a = Fraction(coefficients["lhs_x"])
        b = Fraction(coefficients["lhs_constant"])
        c = Fraction(coefficients["rhs_x"])
        d = Fraction(coefficients["rhs_constant"])
        submitted = Fraction(payload.response.strip().replace(" ", ""))
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise HTTPException(422, "Enter a valid exact rational number") from exc
    expected = a - c if step == 0 else d - b
    correct = submitted == expected
    db.add(TutorTurn(
        session_id=session.id, role="STUDENT", problem_id=problem.id,
        attempt_id=confirmed[0].attempt_id, state=TutorState.GUIDED_PRACTICE,
        pedagogical_action="PUBLISHED_REPAIR_RESULT",
        message="Equality-preserving repair step answered",
        metadata_json={
            "step": step, "correct": correct, "independent_evidence_eligible": False,
        },
    ))
    if not correct:
        db.commit()
        return {
            "stage": "SOCRATIC_REPAIR_RETRY",
            "correct": False, "repair_check": _published_repair_prompt(problem, step),
            "independent_evidence_eligible": False, "mastery_eligible": False,
        }
    if step == 0:
        db.commit()
        return {
            "stage": "SOCRATIC_REPAIR",
            "correct": True, "repair_check": _published_repair_prompt(problem, 1),
            "independent_evidence_eligible": False, "mastery_eligible": False,
        }
    try:
        retest = server_guided_retest(
            problem, misconception_code=confirmed[0].metadata_json["misconception_code"],
        )
    except (PublishedProbeUnavailable, KeyError, TypeError) as exc:
        raise HTTPException(409, "Guided retest unavailable") from exc
    db.add(TutorTurn(
        session_id=session.id, role="SYSTEM", problem_id=problem.id,
        attempt_id=confirmed[0].attempt_id, state=TutorState.GUIDED_PRACTICE,
        pedagogical_action="PUBLISHED_GUIDED_RETEST_ISSUED",
        message="Fresh guided retest issued after verified repair",
        metadata_json={
            "variant_id": retest["variant_id"],
            "task_fingerprint": retest["task_fingerprint"],
            "source_fingerprint": problem.solution["task_fingerprint"],
            "independent_evidence_eligible": False,
        },
    ))
    db.commit()
    return {
        "stage": "GUIDED_RETEST",
        "correct": True,
        "guided_retest_task": {
            "variant_id": retest["variant_id"], "mode": "GUIDED",
            "prompt": retest["prompt"],
        },
        "independent_evidence_eligible": False, "mastery_eligible": False,
    }


class PublishedGuidedRetestIn(BaseModel):
    problem_id: uuid.UUID
    answer: str


@router.post("/sessions/{session_id}/published-guided-retest")
def submit_published_guided_retest(
    session_id: uuid.UUID,
    payload: PublishedGuidedRetestIn,
    access: CurrentLearningAccess,
    db: DbSession,
) -> dict[str, object]:
    """Verify the server-issued fresh guided task without mastery or rewards."""
    if not 0 < len(payload.answer) <= 64:
        raise HTTPException(422, "Enter one exact rational answer")
    session = require_learning_owns_session(db, access, db.get(TutorSession, session_id))
    db.refresh(session, with_for_update=True)
    problem = db.get(Problem, payload.problem_id)
    if (
        session.status != "ACTIVE"
        or problem is None
        or problem.source_type != "PUBLISHED"
        or problem.primary_skill_id not in {session.primary_skill_id, session.active_skill_id}
    ):
        raise HTTPException(409, "Guided retest is unavailable")
    turns = db.scalars(select(TutorTurn).where(
        TutorTurn.session_id == session.id,
        TutorTurn.problem_id == problem.id,
        TutorTurn.pedagogical_action.in_((
            "PUBLISHED_REASONING_CONFIRMED",
            "PUBLISHED_GUIDED_RETEST_ISSUED",
            "PUBLISHED_GUIDED_RETEST_RESULT",
        )),
    ).order_by(TutorTurn.created_at.asc(), TutorTurn.id.asc())).all()
    confirmed = [t for t in turns if t.pedagogical_action == "PUBLISHED_REASONING_CONFIRMED"]
    issued = [t for t in turns if t.pedagogical_action == "PUBLISHED_GUIDED_RETEST_ISSUED"]
    submitted = [t for t in turns if t.pedagogical_action == "PUBLISHED_GUIDED_RETEST_RESULT"]
    if (
        len(confirmed) != 1
        or len(issued) != len(submitted) + 1
        or len(issued) > 3
        or any(
            t.attempt_id != confirmed[0].attempt_id
            for t in (*issued, *submitted)
        )
        or any(
            not isinstance(t.metadata_json, dict)
            for t in (*confirmed, *issued, *submitted)
        )
        or any(
            t.metadata_json.get("correct") is not False
            for t in submitted
        )
    ):
        raise HTTPException(409, "Guided retest issuance or recovery proof is invalid")
    retry_index = len(submitted)
    try:
        retest = server_guided_retest(
            problem, misconception_code=confirmed[0].metadata_json["misconception_code"],
            retry_index=retry_index,
        )
    except (PublishedProbeUnavailable, KeyError, TypeError) as exc:
        raise HTTPException(409, "Guided retest proof unavailable") from exc
    if (
        issued[-1].metadata_json.get("variant_id") != retest["variant_id"]
        or issued[-1].metadata_json.get("task_fingerprint") != retest["task_fingerprint"]
        or issued[-1].metadata_json.get("source_fingerprint")
        != problem.solution["task_fingerprint"]
    ):
        raise HTTPException(409, "Guided retest identity mismatch")
    from app.services.fraction_assessment_registry import score_fraction

    correct = score_fraction(payload.answer, retest["canonical_answer"], variable="x")
    db.add(TutorTurn(
        session_id=session.id, role="STUDENT", problem_id=problem.id,
        attempt_id=issued[-1].attempt_id, state=TutorState.GUIDED_PRACTICE,
        pedagogical_action="PUBLISHED_GUIDED_RETEST_RESULT",
        message=payload.answer,
        metadata_json={
            "variant_id": retest["variant_id"],
            "task_fingerprint": retest["task_fingerprint"],
            "correct": correct,
            "assisted": True,
            "independent_evidence_eligible": False,
        },
    ))
    next_task = None
    if not correct and retry_index < 2:
        try:
            retry = server_guided_retest(
                problem, misconception_code=confirmed[0].metadata_json["misconception_code"],
                retry_index=retry_index + 1,
            )
        except PublishedProbeUnavailable as exc:
            raise HTTPException(409, str(exc)) from exc
        db.add(TutorTurn(
            session_id=session.id, role="SYSTEM", problem_id=problem.id,
            attempt_id=confirmed[0].attempt_id, state=TutorState.GUIDED_PRACTICE,
            pedagogical_action="PUBLISHED_GUIDED_RETEST_ISSUED",
            message="Fresh guided recovery task issued",
            metadata_json={
                "variant_id": retry["variant_id"],
                "task_fingerprint": retry["task_fingerprint"],
                "source_fingerprint": problem.solution["task_fingerprint"],
                "independent_evidence_eligible": False,
            },
        ))
        next_task = {
            "variant_id": retry["variant_id"], "mode": "GUIDED",
            "prompt": retry["prompt"],
        }
    db.commit()
    return {
        "stage": (
            "READY_FOR_TRANSFER_CONFIRMATION" if correct else
            "GUIDED_RETEST_RETRY" if next_task else "GUIDED_RETEST_EXHAUSTED"
        ),
        "correct": correct,
        "guided_retest_task": next_task,
        "independent_evidence_eligible": False,
        "mastery_eligible": False,
    }


class PublishedTransferIn(BaseModel):
    problem_id: uuid.UUID
    answer: str


def _published_transfer_proof(db: DbSession, session: TutorSession, problem: Problem):
    """Server-only proof of a successful, fresh guided retest."""
    if (
        session.status != "ACTIVE" or problem.source_type != "PUBLISHED"
        or problem.primary_skill_id not in {session.primary_skill_id, session.active_skill_id}
    ):
        raise HTTPException(409, "Transfer is unavailable")
    turns = list(db.scalars(select(TutorTurn).where(
        TutorTurn.session_id == session.id,
        TutorTurn.problem_id == problem.id,
        TutorTurn.pedagogical_action.in_((
            "PUBLISHED_REASONING_CONFIRMED",
            "PUBLISHED_GUIDED_RETEST_ISSUED",
            "PUBLISHED_GUIDED_RETEST_RESULT",
            "PUBLISHED_TRANSFER_ISSUED",
            "PUBLISHED_TRANSFER_RESULT",
        )),
    ).order_by(TutorTurn.created_at.asc(), TutorTurn.id.asc())))
    confirmed = [t for t in turns if t.pedagogical_action == "PUBLISHED_REASONING_CONFIRMED"]
    issued = [t for t in turns if t.pedagogical_action == "PUBLISHED_GUIDED_RETEST_ISSUED"]
    results = [t for t in turns if t.pedagogical_action == "PUBLISHED_GUIDED_RETEST_RESULT"]
    if (
        len(confirmed) != 1 or not issued or len(results) != len(issued)
        or not 1 <= len(issued) <= 3
        or any(t.attempt_id != confirmed[0].attempt_id for t in (*issued, *results))
        or any(not isinstance(t.metadata_json, dict) for t in (*confirmed, *issued, *results))
        or any(t.metadata_json.get("correct") is not False for t in results[:-1])
        or results[-1].metadata_json.get("correct") is not True
        or len([t for t in turns if t.pedagogical_action == "PUBLISHED_TRANSFER_RESULT"])
    ):
        raise HTTPException(409, "Verified guided success is required before transfer")
    try:
        transfer = server_unhinted_transfer(
            problem, misconception_code=confirmed[0].metadata_json["misconception_code"],
            guided_retry_index=len(results) - 1,
        )
    except (PublishedProbeUnavailable, KeyError, TypeError) as exc:
        raise HTTPException(409, "Transfer generation unavailable") from exc
    return transfer, confirmed[0], turns


@router.post("/sessions/{session_id}/published-transfer/start")
def start_published_transfer(
    session_id: uuid.UUID,
    problem_id: uuid.UUID,
    access: CurrentLearningAccess,
    db: DbSession,
) -> dict[str, object]:
    """Issue a single new-family, unhinted transfer in the owned learner session."""
    session = require_learning_owns_session(db, access, db.get(TutorSession, session_id))
    db.refresh(session, with_for_update=True)
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise HTTPException(404, "Problem not found")
    transfer, confirmed, turns = _published_transfer_proof(db, session, problem)
    if any(t.pedagogical_action == "PUBLISHED_TRANSFER_ISSUED" for t in turns):
        raise HTTPException(409, "Independent transfer already issued")
    db.add(TutorTurn(
        session_id=session.id, role="SYSTEM", problem_id=problem.id,
        attempt_id=confirmed.attempt_id, state=TutorState.INDEPENDENT_PRACTICE,
        pedagogical_action="PUBLISHED_TRANSFER_ISSUED",
        message="Unhinted alternate-family task issued",
        metadata_json={
            "variant_id": transfer["learner_task"]["variant_id"],
            "target_fingerprint": transfer["private_target_fingerprint_for_review"],
            "source_fingerprint": problem.solution["task_fingerprint"],
            "target_family": transfer["target_family"],
            "hints_allowed": False,
            "independent_evidence_eligible": False,
        },
    ))
    db.commit()
    return {
        "stage": "INDEPENDENT_EXIT",
        "independent_task": transfer["learner_task"],
        "hints_allowed": False,
        "independent_evidence_eligible": False,
        "mastery_eligible": False,
    }


@router.post("/sessions/{session_id}/published-transfer/respond")
def submit_published_transfer(
    session_id: uuid.UUID,
    payload: PublishedTransferIn,
    access: CurrentLearningAccess,
    db: DbSession,
) -> dict[str, object]:
    """Exact-oracle transfer feedback, strictly separate from mastery credit."""
    if not 0 < len(payload.answer) <= 64:
        raise HTTPException(422, "Enter one exact rational answer")
    session = require_learning_owns_session(db, access, db.get(TutorSession, session_id))
    db.refresh(session, with_for_update=True)
    problem = db.get(Problem, payload.problem_id)
    if problem is None:
        raise HTTPException(404, "Problem not found")
    transfer, confirmed, turns = _published_transfer_proof(db, session, problem)
    issued = [t for t in turns if t.pedagogical_action == "PUBLISHED_TRANSFER_ISSUED"]
    if (
        len(issued) != 1 or issued[0].attempt_id != confirmed.attempt_id
        or not isinstance(issued[0].metadata_json, dict)
        or issued[0].metadata_json.get("target_fingerprint")
        != transfer["private_target_fingerprint_for_review"]
        or issued[0].metadata_json.get("variant_id")
        != transfer["learner_task"]["variant_id"]
        or issued[0].metadata_json.get("target_family") != transfer["target_family"]
        or issued[0].metadata_json.get("hints_allowed") is not False
    ):
        raise HTTPException(409, "Unhinted transfer issuance proof is invalid")
    from app.services.fraction_assessment_registry import score_fraction

    correct = score_fraction(
        payload.answer, transfer["private_exact_oracle_for_review"], variable="x",
    )
    db.add(TutorTurn(
        session_id=session.id, role="STUDENT", problem_id=problem.id,
        attempt_id=confirmed.attempt_id, state=TutorState.INDEPENDENT_PRACTICE,
        pedagogical_action="PUBLISHED_TRANSFER_RESULT",
        message="Independent task answered",
        metadata_json={
            "target_fingerprint": transfer["private_target_fingerprint_for_review"],
            "correct": correct,
            "hints_allowed": False,
            "independent_evidence_eligible": False,
        },
    ))
    db.commit()
    return {
        "stage": "TRANSFER_FEEDBACK_ONLY",
        "correct": correct,
        "independent_evidence_eligible": False,
        "mastery_eligible": False,
        "xp_earned": 0,
    }


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

    if problem.source_type == "PUBLISHED":
        db.refresh(session, with_for_update=True)
        issued_id = db.scalar(select(TutorTurn.problem_id).where(
            TutorTurn.session_id == session.id, TutorTurn.role == "TUTOR",
            TutorTurn.pedagogical_action != "WORK_STEP",
        ).order_by(TutorTurn.created_at.desc(), TutorTurn.id.desc()).limit(1))
        already_answered = db.scalar(select(Attempt.id).where(
            Attempt.session_id == session.id, Attempt.problem_id == problem.id,
        ).limit(1))
        if issued_id != problem.id or already_answered is not None:
            raise HTTPException(409, "Published item was not issued or has already been answered")

    mode_column = _eligibility_column(session.current_state)
    if problem.source_type == "PUBLISHED" and (
        mode_column is None or not permitted(db, problem, mode_column.key.removesuffix("_eligible"))
    ):
        raise HTTPException(409, "Published package unavailable for this learning mode")

    student = db.get(Student, session.student_id)
    skill = db.get(Skill, active_skill_id)
    if student is None or skill is None:
        raise HTTPException(404, "Student or skill not found")

    state_at_attempt = session.current_state
    content_meta = db.scalar(
        select(ProblemContentMetadata).where(
            ProblemContentMetadata.problem_id == problem.id
        )
    )
    is_extension = bool(content_meta and content_meta.extension_eligible)
    if is_extension:
        # Optional stretch tier: tagged EXTENSION so mastery gating, progress
        # counters, and evidence queries exclude it.
        state_at_attempt = TutorState.EXTENSION
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
        published_problem=problem,
        assessment_mode=AssessmentMode(mode_column.key.removesuffix("_eligible")) if mode_column is not None else None,
        step_misconception_code=step_misconception_code,
        count_evidence=not is_extension,
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
                # Published answers remain feedback-only even when correct.
                Problem.source_type != "PUBLISHED",
                Attempt.is_correct.is_(True),
                Attempt.assistance_level == 0,
                Attempt.state_at_attempt != TutorState.EXTENSION,
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

    if not is_extension:
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

    if not is_extension:
        # Extension attempts never move the session state machine or the
        # difficulty ladder — the optional tier is progression-neutral.
        session.current_state = transition.state
        if engine_action == "INCREASE_DIFFICULTY":
            progress.current_difficulty = min(10, progress.current_difficulty + 1)
        elif engine_action == "REMEDIATE":
            progress.current_difficulty = max(1, progress.current_difficulty - 1)

    # --- Independent-assessment guard: block ALL tutoring assistance ---
    assessment_guard = check_assessment_guard(
        db, student_id=session.student_id,
    )

    jit_decision = select_hint(
        state=state_at_attempt,
        highest_level_used=int(highest_hint_level),
        misconception_confidence=evidence.evaluation.misconception_confidence,
        repeated_unsuccessful_attempts=(attempt_number if not evidence.evaluation.correct else 0),
        independent_assessment_active=assessment_guard.blocked,
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
        if (
            not is_extension
            and evidence.evaluation.correct is False
            and problem.primary_skill_id == next_skill_id
        ):
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
                correct=None if is_extension else evidence.evaluation.correct,
                session_id=session.id,
                offer_extension=is_extension,
            )
        tutor_action = transition.action
        tutor_hint_level = transition.hint_level
        tutor_skill = next_skill
        generation_state = transition.state

    # When an independent assessment is active, skip the LLM tutoring
    # call entirely.  The student's answer has already been graded and
    # recorded (grading is not assistance), but no explanatory feedback,
    # hints, misconception guidance, or solution steps are delivered.
    if assessment_guard.blocked:
        message = ASSESSMENT_BLOCK_MESSAGE
        answer_leak_blocked = False
        generation_source = "assessment_blocked"
        generation_model: str | None = None
    else:
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
        generation_source = generation.source
        generation_model = generation.model
        answer_leak_blocked = True
    if not assessment_guard.blocked and not evidence.evaluation.correct:
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
        llm_model=generation_model,
        metadata_json={
            "generation_source": generation_source,
            "answer_leak_blocked": answer_leak_blocked,
            "assessment_blocked": assessment_guard.blocked,
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

    if issue_jit_hint and not assessment_guard.blocked:
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
                generation_source=generation_source,
                provider=None,
                llm_model=generation_model,
            )
        )

    # Until the published learner journey is independently verified, correct
    # published responses are feedback, not reward or mastery evidence.
    new_awards = [] if problem.source_type == "PUBLISHED" else evaluate_awards(
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

    xp_earned = 0 if problem.source_type == "PUBLISHED" else (
        attempt_xp(
            bool(evidence.evaluation.correct),
            effective_assistance_level,
            problem.difficulty,
        ) + sum(BADGE_XP.get(award.badge_code, 0) for award in new_awards)
    )
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
    if not assessment_guard.blocked:
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

    # Block step-by-step assistance during independent assessment.
    # Work-step feedback reveals solution lines and misconception
    # guidance, which compromises assessment independence.
    ws_guard = check_assessment_guard(db, student_id=session.student_id)
    if ws_guard.blocked:
        return WorkStepOut(
            status="blocked",
            feedback=ASSESSMENT_BLOCK_MESSAGE,
        )
    problem = db.get(Problem, payload.problem_id)
    active_skill_id = session.active_skill_id or session.primary_skill_id
    if problem is None or problem.primary_skill_id != active_skill_id:
        raise HTTPException(400, "Problem does not support step-by-step work")
    if problem.source_type == "PUBLISHED":
        raise HTTPException(409, "Published step assistance is not yet authorized")
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
    # Published content must not accept OCR-derived work suggestions until the
    # signed learning-journey and evidence-isolation contract is reviewed.
    # This denial precedes image intake and does not modify learner history.
    if problem.source_type == "PUBLISHED":
        raise HTTPException(409, "Published step assistance is not yet authorized")
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
