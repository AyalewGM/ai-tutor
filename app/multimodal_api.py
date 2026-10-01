import re
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.identity import CurrentParent, require_parent_owns_session
from app.models import Problem, Skill, TutorSession
from app.services.curriculum_scope import CurriculumScopeError, require_session_scope, require_skill_in_scope
from app.services.tutor_engine import fallback_message, TutorContext

router = APIRouter(prefix="/tutor", tags=["tutor-multimodal"])
DbSession = Annotated[Session, Depends(get_db)]

class CanvasPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float = Field(ge=0, le=4096)
    y: float = Field(ge=0, le=4096)
    pressure: float = Field(ge=0, le=1)

class CanvasStroke(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=80)
    tool: Literal["pen", "eraser"]
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    width: float = Field(gt=0, le=64)
    points: list[CanvasPoint] = Field(min_length=2, max_length=1000)

class CanvasDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1]
    strokes: list[CanvasStroke] = Field(max_length=250)

class MultimodalStepIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: uuid.UUID
    prompt: str = Field(default="", max_length=500)
    canvas: CanvasDocument
    # Snapshot is accepted only as a bounded data URL for explicit learner sync.
    snapshot_data_url: str = Field(max_length=750_000)

    @field_validator("snapshot_data_url")
    @classmethod
    def png_only(cls, value: str) -> str:
        if not value.startswith("data:image/png;base64,"):
            raise ValueError("Only PNG canvas snapshots are accepted")
        return value

class CanvasOverlay(BaseModel):
    kind: Literal["highlight", "label"]
    text: str = Field(max_length=120)
    x: float = Field(ge=0, le=4096)
    y: float = Field(ge=0, le=4096)

class MultimodalStepOut(BaseModel):
    message: str
    overlays: list[CanvasOverlay] = Field(default_factory=list)
    accepted_stroke_count: int

def _safe_overlay(problem_prompt: str) -> list[CanvasOverlay]:
    # Application-owned visual cue: never infer correctness from handwriting.
    match = re.search(r"([+-])\s*(\d+(?:\.\d+)?)", problem_prompt)
    if not match:
        return []
    operation, value = match.groups()
    inverse = "Subtract" if operation == "+" else "Add"
    return [CanvasOverlay(kind="label", text=f"{inverse} {value} on both sides", x=70, y=70)]

@router.post("/multimodal-step", response_model=MultimodalStepOut)
def multimodal_step(payload: MultimodalStepIn, parent: CurrentParent, db: DbSession) -> MultimodalStepOut:
    session = require_parent_owns_session(db, parent, db.get(TutorSession, payload.session_id))
    try:
        scope = require_session_scope(db, session)
        skill = require_skill_in_scope(db, skill_id=session.active_skill_id or session.primary_skill_id, scope=scope)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc

    # Deliberately do not persist or forward the PNG/strokes to a third party.
    # Until a reviewed vision provider exists, sync means "use scratchpad context
    # for a deterministic Socratic cue", not handwriting recognition.
    problem = None
    from sqlalchemy import select
    problem = db.scalar(
        select(Problem)
        .where(Problem.primary_skill_id == skill.id)
        .order_by(Problem.created_at.desc())
        .limit(1)
    )
    prompt = problem.prompt if problem is not None else skill.name
    context = TutorContext(
        grade_level="",
        curriculum_name="",
        state=session.current_state.value,
        skill_name=skill.name,
        action="GIVE_HINT",
        hint_level=1,
        problem_prompt=prompt,
        student_answer=None,
    )
    return MultimodalStepOut(
        message=fallback_message(context),
        overlays=_safe_overlay(prompt),
        accepted_stroke_count=len(payload.canvas.strokes),
    )
