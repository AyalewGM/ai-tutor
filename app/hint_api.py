import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api import _tutor_context
from app.core.database import get_db
from app.hint_models import HintEvent
from app.identity import CurrentParent, require_parent_owns_session
from app.models import Problem, Skill, Student, TutorSession, TutorTurn
from app.services.curriculum_scope import (
    CurriculumScopeError,
    require_session_scope,
    require_skill_in_scope,
)
from app.services.hint_policy import hint_constraint, select_hint
from app.services.tutor_engine import tutor_engine

router = APIRouter(prefix="/adaptive-tutor", tags=["adaptive-tutor"])
DbSession = Annotated[Session, Depends(get_db)]


class HintRequest(BaseModel):
    problem_id: uuid.UUID
    reason: Literal["HINT", "I_DONT_UNDERSTAND"] = "HINT"


class HintResponse(BaseModel):
    allowed: bool
    level: int
    trigger: str
    message: str


@router.post("/sessions/{session_id}/hint", response_model=HintResponse)
def request_hint(
    session_id: uuid.UUID, payload: HintRequest, parent: CurrentParent, db: DbSession
) -> HintResponse:
    session = require_parent_owns_session(db, parent, db.get(TutorSession, session_id))
    active_skill_id = session.active_skill_id or session.primary_skill_id
    try:
        scope = require_session_scope(db, session)
        require_skill_in_scope(db, skill_id=active_skill_id, scope=scope)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc

    problem = db.get(Problem, payload.problem_id)
    if problem is None or problem.primary_skill_id != active_skill_id:
        raise HTTPException(400, "Problem does not belong to active learning focus")

    highest = db.scalar(
        select(func.max(HintEvent.level)).where(
            HintEvent.session_id == session.id,
            HintEvent.problem_id == problem.id,
        )
    ) or 0
    decision = select_hint(
        state=session.current_state,
        highest_level_used=int(highest),
        explicit_request=True,
    )
    request_trigger = (
        "I_DONT_UNDERSTAND"
        if payload.reason == "I_DONT_UNDERSTAND"
        else decision.trigger
    )
    if not decision.allowed:
        return HintResponse(
            allowed=False,
            level=0,
            trigger=request_trigger,
            message=decision.reason or "Hints are not available right now.",
        )

    student = db.get(Student, session.student_id)
    skill = db.get(Skill, active_skill_id)
    if student is None or skill is None:
        raise HTTPException(404, "Student or skill not found")
    generation = tutor_engine.generate(
        _tutor_context(
            db,
            student=student,
            skill=skill,
            state=session.current_state,
            action="GIVE_HINT",
            hint_level=decision.level,
            problem=problem,
        )
    )
    turn = TutorTurn(
        session_id=session.id,
        role="TUTOR",
        message=generation.message,
        state=session.current_state,
        pedagogical_action="GIVE_HINT",
        problem_id=problem.id,
        llm_model=generation.model,
        metadata_json={
            "generation_source": generation.source,
            "provider": generation.provider,
            "hint_level": decision.level,
            "hint_trigger": request_trigger,
            "hint_constraint": hint_constraint(decision.level),
        },
    )
    db.add(turn)
    db.flush()
    db.add(
        HintEvent(
            session_id=session.id,
            student_id=session.student_id,
            skill_id=active_skill_id,
            problem_id=problem.id,
            tutor_turn_id=turn.id,
            level=decision.level,
            trigger=request_trigger,
            generation_source=generation.source,
            provider=generation.provider,
            llm_model=generation.model,
        )
    )
    db.commit()
    return HintResponse(
        allowed=True,
        level=decision.level,
        trigger=request_trigger,
        message=generation.message,
    )
