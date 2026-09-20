import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    Attempt,
    Curriculum,
    MasteryEvent,
    Misconception,
    Problem,
    Skill,
    Student,
    StudentMisconception,
    StudentSkill,
    TutorSession,
    TutorState,
    TutorTurn,
)
from app.schemas import (
    EvaluationOut,
    MasteryOut,
    ProblemOut,
    RespondIn,
    RespondOut,
    SessionCreate,
    SessionOut,
    TutorOut,
)
from app.services.curriculum_scope import (
    CurriculumScopeError,
    require_session_scope,
    require_skill_in_scope,
    resolve_student_curriculum_scope,
)
from app.services.evaluation import evaluate_distributive_property
from app.services.mastery import update_mastery
from app.services.problem_selection import select_next_problem
from app.services.state_machine import TutorContext as StateContext
from app.services.state_machine import determine_next_action
from app.services.tutor_engine import TutorContext, tutor_engine

router = APIRouter(prefix="/tutor", tags=["tutor"])
DbSession = Annotated[Session, Depends(get_db)]


def _student_skill(db: Session, student_id: uuid.UUID, skill_id: uuid.UUID) -> StudentSkill:
    row = db.get(StudentSkill, {"student_id": student_id, "skill_id": skill_id})
    if row is None:
        row = StudentSkill(student_id=student_id, skill_id=skill_id)
        db.add(row)
        db.flush()
    return row


def _problem_out(problem: Problem | None) -> ProblemOut | None:
    if problem is None:
        return None
    return ProblemOut(id=problem.id, prompt=problem.prompt, difficulty=problem.difficulty)


def _tutor_context(
    db: Session,
    *,
    student: Student,
    skill: Skill,
    state: TutorState,
    action: str,
    hint_level: int | None,
    problem: Problem,
    next_problem: Problem | None = None,
    student_answer: str | None = None,
    misconception: Misconception | None = None,
) -> TutorContext:
    curriculum = db.get(Curriculum, skill.curriculum_id)
    return TutorContext(
        grade_level=student.grade_level,
        curriculum_name=curriculum.name if curriculum else "Unknown curriculum",
        state=state.value,
        skill_name=skill.name,
        action=action,
        hint_level=hint_level,
        problem_prompt=problem.prompt,
        student_answer=student_answer,
        misconception_description=misconception.description if misconception else None,
        remediation_strategy=misconception.remediation_strategy if misconception else None,
        next_problem_prompt=next_problem.prompt if next_problem else None,
    )


@router.post("/sessions", response_model=SessionOut)
def create_session(payload: SessionCreate, db: DbSession) -> SessionOut:
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    try:
        scope = resolve_student_curriculum_scope(db, student)
        skill = require_skill_in_scope(db, skill_id=payload.skill_id, scope=scope)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc

    progress = _student_skill(db, student.id, skill.id)
    problem = select_next_problem(
        db,
        skill_id=skill.id,
        current_problem_id=None,
        current_difficulty=progress.current_difficulty,
        state=TutorState.DIAGNOSE,
    )
    if problem is None:
        raise HTTPException(404, "No problem configured for this skill")

    session = TutorSession(
        student_id=student.id,
        primary_skill_id=skill.id,
        active_skill_id=skill.id,
        curriculum_id=scope.curriculum_id,
        curriculum_enrollment_id=scope.enrollment_id,
        current_state=TutorState.DIAGNOSE,
        starting_mastery=progress.mastery_score,
        session_goal=f"Diagnose and practice {skill.name}",
    )
    db.add(session)
    db.flush()

    generation = tutor_engine.generate(
        _tutor_context(
            db,
            student=student,
            skill=skill,
            state=TutorState.DIAGNOSE,
            action="ASK_DIAGNOSTIC",
            hint_level=None,
            problem=problem,
        )
    )
    db.add(
        TutorTurn(
            session_id=session.id,
            role="TUTOR",
            message=generation.message,
            state=TutorState.DIAGNOSE,
            pedagogical_action="ASK_DIAGNOSTIC",
            problem_id=problem.id,
            llm_model=generation.model,
            metadata_json={
                "generation_source": generation.source,
                "curriculum_id": str(scope.curriculum_id),
            },
        )
    )
    db.commit()
    db.refresh(session)

    return SessionOut(
        session_id=session.id,
        state=session.current_state,
        mastery=MasteryOut(score=progress.mastery_score, confidence=progress.confidence_score),
        problem=ProblemOut(id=problem.id, prompt=problem.prompt, difficulty=problem.difficulty),
        message=generation.message,
    )


@router.post("/sessions/{session_id}/respond", response_model=RespondOut)
def respond(session_id: uuid.UUID, payload: RespondIn, db: DbSession) -> RespondOut:
    session = db.get(TutorSession, session_id)
    if session is None or session.status != "ACTIVE":
        raise HTTPException(404, "Active tutor session not found")
    try:
        scope = require_session_scope(db, session)
        skill = require_skill_in_scope(db, skill_id=session.primary_skill_id, scope=scope)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc

    problem = db.get(Problem, payload.problem_id)
    if problem is None or problem.primary_skill_id != session.primary_skill_id:
        raise HTTPException(400, "Problem does not belong to the active skill")

    student = db.get(Student, session.student_id)
    if student is None:
        raise HTTPException(404, "Student not found")

    progress = _student_skill(db, session.student_id, session.primary_skill_id)
    previous_score = progress.mastery_score
    previous_confidence = progress.confidence_score
    evaluation = evaluate_distributive_property(
        problem.prompt,
        payload.answer,
        problem.canonical_answer or "",
    )

    misconception = None
    misconception_count = 0
    if evaluation.misconception_code:
        misconception = db.scalar(
            select(Misconception).where(
                Misconception.skill_id == skill.id,
                Misconception.code == evaluation.misconception_code,
            )
        )
        if misconception:
            key = {
                "student_id": session.student_id,
                "misconception_id": misconception.id,
            }
            student_misconception = db.get(StudentMisconception, key)
            if student_misconception is None:
                student_misconception = StudentMisconception(
                    student_id=session.student_id,
                    misconception_id=misconception.id,
                    occurrence_count=1,
                    confidence=Decimal(str(evaluation.misconception_confidence or 0)),
                )
                db.add(student_misconception)
            else:
                student_misconception.occurrence_count += 1
                student_misconception.confidence = Decimal(
                    str(evaluation.misconception_confidence or 0)
                )
            misconception_count = student_misconception.occurrence_count

    mastery = update_mastery(
        float(progress.mastery_score),
        progress.attempt_count,
        evaluation.correct,
        payload.assistance_level,
    )
    progress.attempt_count += 1
    if evaluation.correct:
        progress.correct_count += 1
        if payload.assistance_level == 0:
            progress.independent_attempt_count += 1
            progress.independent_correct_count += 1
        else:
            progress.hinted_correct_count += 1
    elif payload.assistance_level == 0:
        progress.independent_attempt_count += 1
    progress.mastery_score = Decimal(str(mastery.mastery))
    progress.confidence_score = Decimal(str(mastery.confidence))

    consecutive_successes = db.scalar(
        select(func.count(Attempt.id)).where(
            Attempt.session_id == session.id,
            Attempt.is_correct.is_(True),
            Attempt.assistance_level == 0,
        )
    ) or 0

    transition = determine_next_action(
        StateContext(
            state=session.current_state,
            correct=evaluation.correct,
            assistance_level=payload.assistance_level,
            misconception_count=misconception_count,
            consecutive_independent_successes=int(consecutive_successes),
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
        normalized_answer=evaluation.normalized_answer,
        is_correct=evaluation.correct,
        attempt_number=attempt_number,
        assistance_level=payload.assistance_level,
        misconception_id=misconception.id if misconception else None,
        misconception_confidence=(
            Decimal(str(evaluation.misconception_confidence))
            if evaluation.misconception_confidence is not None
            else None
        ),
        evaluation_confidence=Decimal(str(evaluation.confidence)),
        state_at_attempt=session.current_state,
    )
    db.add(attempt)
    db.flush()

    db.add(
        TutorTurn(
            session_id=session.id,
            role="STUDENT",
            message=payload.answer,
            state=session.current_state,
            pedagogical_action="ANSWER",
            problem_id=problem.id,
            attempt_id=attempt.id,
        )
    )
    db.add(
        MasteryEvent(
            student_id=session.student_id,
            skill_id=session.primary_skill_id,
            attempt_id=attempt.id,
            previous_score=previous_score,
            new_score=progress.mastery_score,
            previous_confidence=previous_confidence,
            new_confidence=progress.confidence_score,
            reason="ATTEMPT_EVIDENCE",
            metadata_json={
                "correct": evaluation.correct,
                "assistance_level": payload.assistance_level,
                "evidence": mastery.evidence,
                "curriculum_id": str(scope.curriculum_id),
            },
        )
    )

    session.current_state = transition.state
    if transition.action == "INCREASE_DIFFICULTY":
        progress.current_difficulty = min(10, progress.current_difficulty + 1)
    elif transition.action == "REMEDIATE":
        progress.current_difficulty = max(1, progress.current_difficulty - 1)

    next_problem = select_next_problem(
        db,
        skill_id=session.primary_skill_id,
        current_problem_id=problem.id,
        current_difficulty=progress.current_difficulty,
        state=transition.state,
        correct=evaluation.correct,
    )
    generation = tutor_engine.generate(
        _tutor_context(
            db,
            student=student,
            skill=skill,
            state=transition.state,
            action=transition.action,
            hint_level=transition.hint_level,
            problem=problem,
            next_problem=next_problem,
            student_answer=payload.answer,
            misconception=misconception,
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
                "hint_level": transition.hint_level,
                "generation_source": generation.source,
                "curriculum_id": str(scope.curriculum_id),
            },
        )
    )
    db.commit()

    return RespondOut(
        session_id=session.id,
        state=transition.state,
        evaluation=EvaluationOut(
            correct=evaluation.correct,
            confidence=evaluation.confidence,
            misconception_code=evaluation.misconception_code,
            misconception_confidence=evaluation.misconception_confidence,
        ),
        tutor=TutorOut(
            action=transition.action,
            hint_level=transition.hint_level,
            message=generation.message,
        ),
        mastery=MasteryOut(score=progress.mastery_score, confidence=progress.confidence_score),
        next_problem=_problem_out(next_problem),
    )
