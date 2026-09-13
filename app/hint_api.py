import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api import _tutor_context
from app.core.database import get_db
from app.hint_models import HintEvent
from app.models import Problem, Skill, Student, TutorSession, TutorTurn
from app.services.hint_policy import hint_constraint, select_hint
from app.services.tutor_engine import tutor_engine

router = APIRouter(prefix="/adaptive-tutor", tags=["adaptive-tutor"])
DbSession = Annotated[Session, Depends(get_db)]


class HintRequest(BaseModel):
    problem_id: uuid.UUID


class HintResponse(BaseModel):
    allowed: bool
    level: int
    trigger: str
    message: str


@router.post("/sessions/{session_id}/hint", response_model=HintResponse)
def request_hint(session_id: uuid.UUID, payload: HintRequest, db: DbSession) -> HintResponse:
    session = db.get(TutorSession, session_id)
    if session is None or session.status != "ACTIVE":
        raise HTTPException(404, "Active tutor session not found")
    active_skill_id = session.active_skill_id or session.primary_skill_id
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
    if not decision.allowed:
        return HintResponse(
            allowed=False,
            level=0,
            trigger=decision.trigger,
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
            "hint_trigger": decision.trigger,
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
            trigger=decision.trigger,
            generation_source=generation.source,
            provider=generation.provider,
            llm_model=generation.model,
        )
    )
    db.commit()
    return HintResponse(
        allowed=True,
        level=decision.level,
        trigger=decision.trigger,
        message=generation.message,
    )
