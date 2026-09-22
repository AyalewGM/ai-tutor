from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import _student_skill, _tutor_context
from app.core.database import get_db
from app.identity import CurrentParent, require_parent_owns_student
from app.models import (
    Problem,
    Skill,
    SkillStatus,
    Student,
    TutorSession,
    TutorState,
    TutorTurn,
)
from app.schemas import LearningFocusOut, MasteryOut, ProblemOut, SessionCreate, SessionOut
from app.services.curriculum_scope import (
    CurriculumScopeError,
    require_skill_in_scope,
    resolve_student_curriculum_scope,
)
from app.services.problem_selection import select_next_problem
from app.services.review_schedule import REVIEW_REASON, due_review
from app.services.tutor_engine import tutor_engine

router = APIRouter(prefix="/adaptive-tutor", tags=["adaptive-tutor"])
DbSession = Annotated[Session, Depends(get_db)]


def _focus(session: TutorSession) -> LearningFocusOut:
    active = session.active_skill_id or session.primary_skill_id
    return LearningFocusOut(
        target_skill_id=session.primary_skill_id,
        active_skill_id=active,
        in_remediation=active != session.primary_skill_id,
        remediation_reason=session.remediation_reason,
    )


@router.post("/sessions", response_model=SessionOut)
def create_session(payload: SessionCreate, parent: CurrentParent, db: DbSession) -> SessionOut:
    student = require_parent_owns_student(parent, db.get(Student, payload.student_id))

    try:
        scope = resolve_student_curriculum_scope(db, student)
        skill = require_skill_in_scope(db, skill_id=payload.skill_id, scope=scope)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc

    progress = _student_skill(db, student.id, skill.id)

    existing = db.scalar(
        select(TutorSession)
        .where(
            TutorSession.student_id == student.id,
            TutorSession.primary_skill_id == skill.id,
            TutorSession.status == "ACTIVE",
        )
        .order_by(TutorSession.started_at.desc(), TutorSession.id.desc())
    )
    if existing is not None:
        turn = db.scalar(
            select(TutorTurn)
            .where(TutorTurn.session_id == existing.id, TutorTurn.role == "TUTOR")
            .order_by(TutorTurn.created_at.desc(), TutorTurn.id.desc())
        )
        problem = db.get(Problem, turn.problem_id) if turn and turn.problem_id else None
        if problem is None:
            focus_id = existing.active_skill_id or skill.id
            problem = select_next_problem(
                db,
                skill_id=focus_id,
                current_problem_id=None,
                current_difficulty=progress.current_difficulty,
                state=existing.current_state,
            )
        if problem is None:
            raise HTTPException(404, "No problem configured for this skill")
        return SessionOut(
            session_id=existing.id,
            state=existing.current_state,
            mastery=MasteryOut(
                score=progress.mastery_score,
                confidence=progress.confidence_score,
            ),
            focus=_focus(existing),
            problem=ProblemOut(
                id=problem.id, prompt=problem.prompt, difficulty=problem.difficulty
            ),
            message=turn.message
            if turn
            else "Welcome back — pick up where you left off.",
        )

    review = None
    if scope.curriculum_id is not None:
        review = due_review(
            db,
            student_id=student.id,
            curriculum_id=scope.curriculum_id,
        )
    focus_skill = skill
    focus_progress = progress
    if review is not None:
        focus_progress = review.progress
        focus_skill = db.get(Skill, review.progress.skill_id) or skill

    if review is not None:
        opening_state = TutorState.REVIEW
        opening_action = "START_REVIEW"
    else:
        opening_state = {
            SkillStatus.MASTERED: TutorState.MASTERY_CHECK,
            SkillStatus.REVIEW_DUE: TutorState.MASTERY_CHECK,
            SkillStatus.PRACTICING: TutorState.INDEPENDENT_PRACTICE,
            SkillStatus.LEARNING: TutorState.GUIDED_PRACTICE,
            SkillStatus.INTRODUCED: TutorState.GUIDED_PRACTICE,
        }.get(progress.status, TutorState.DIAGNOSE)
        opening_action = {
            TutorState.MASTERY_CHECK: "START_MASTERY_CHECK",
            TutorState.INDEPENDENT_PRACTICE: "RESUME_TARGET",
            TutorState.GUIDED_PRACTICE: "RESUME_TARGET",
        }.get(opening_state, "ASK_DIAGNOSTIC")

    problem = select_next_problem(
        db,
        skill_id=focus_skill.id,
        current_problem_id=None,
        current_difficulty=focus_progress.current_difficulty,
        state=opening_state,
    )
    if problem is None:
        raise HTTPException(404, "No problem configured for this skill")

    session = TutorSession(
        student_id=student.id,
        primary_skill_id=skill.id,
        active_skill_id=focus_skill.id,
        curriculum_id=scope.curriculum_id,
        curriculum_enrollment_id=scope.enrollment_id,
        current_state=opening_state,
        remediation_reason=REVIEW_REASON if review is not None else None,
        starting_mastery=progress.mastery_score,
        session_goal=(
            f"Review {focus_skill.name} before continuing"
            if review is not None
            else f"Diagnose and practice {skill.name}"
        ),
    )
    db.add(session)
    db.flush()

    generation = tutor_engine.generate(
        _tutor_context(
            db,
            student=student,
            skill=focus_skill,
            state=opening_state,
            action=opening_action,
            hint_level=None,
            problem=problem,
        )
    )
    db.add(
        TutorTurn(
            session_id=session.id,
            role="TUTOR",
            message=generation.message,
            state=opening_state,
            pedagogical_action=opening_action,
            problem_id=problem.id,
            llm_model=generation.model,
            metadata_json={"generation_source": generation.source},
        )
    )
    db.commit()

    return SessionOut(
        session_id=session.id,
        state=session.current_state,
        mastery=MasteryOut(
            score=focus_progress.mastery_score,
            confidence=focus_progress.confidence_score,
        ),
        focus=_focus(session),
        problem=ProblemOut(id=problem.id, prompt=problem.prompt, difficulty=problem.difficulty),
        message=generation.message,
    )
