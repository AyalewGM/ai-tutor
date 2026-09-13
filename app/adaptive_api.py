from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import _student_skill, _tutor_context
from app.core.database import get_db
from app.models import Skill, Student, TutorSession, TutorState, TutorTurn
from app.schemas import LearningFocusOut, MasteryOut, ProblemOut, SessionCreate, SessionOut
from app.services.problem_selection import select_next_problem
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
def create_session(payload: SessionCreate, db: DbSession) -> SessionOut:
    student = db.get(Student, payload.student_id)
    skill = db.get(Skill, payload.skill_id)
    if student is None or skill is None:
        raise HTTPException(404, "Student or skill not found")

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
            metadata_json={"generation_source": generation.source},
        )
    )
    db.commit()

    return SessionOut(
        session_id=session.id,
        state=session.current_state,
        mastery=MasteryOut(score=progress.mastery_score, confidence=progress.confidence_score),
        focus=_focus(session),
        problem=ProblemOut(id=problem.id, prompt=problem.prompt, difficulty=problem.difficulty),
        message=generation.message,
    )
