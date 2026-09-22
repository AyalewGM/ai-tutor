import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.identity import CurrentParent, require_parent_owns_session
from app.models import (
    Curriculum,
    LearnerAward,
    Problem,
    Skill,
    Student,
    StudentSkill,
    TutorSession,
    TutorState,
    TutorTurn,
)
from app.services.awards import award_out, badge_collection
from app.services.curriculum_scope import (
    CurriculumScopeError,
    require_session_scope,
    require_skill_in_scope,
)
from app.services.hint_policy import select_hint
from app.services.placement import recommend_next_skill
from app.services.review_schedule import reviews_due
from app.services.visualization import visualization_for

router = APIRouter(prefix="/learner-workspace", tags=["learner-workspace"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceAction = Literal["SUBMIT_ANSWER", "REQUEST_HINT", "I_DONT_UNDERSTAND"]


class LearnerIdentityOut(BaseModel):
    first_name: str
    grade_level: str


class CurriculumContextOut(BaseModel):
    id: uuid.UUID
    name: str
    jurisdiction: str | None = None


class LearningFocusOut(BaseModel):
    primary_skill_id: uuid.UUID
    active_skill_id: uuid.UUID
    skill_name: str
    in_remediation: bool
    remediation_reason: str | None = None


class WorkspaceProblemOut(BaseModel):
    id: uuid.UUID
    prompt: str
    difficulty: int
    visual: dict | None = None


class WorkspaceEvidenceOut(BaseModel):
    mastery_score: float
    confidence_score: float
    independent_attempt_count: int
    independent_correct_count: int
    hinted_correct_count: int


class WorkspaceReviewDueOut(BaseModel):
    skill_id: uuid.UUID
    skill_name: str
    due_at: datetime
    status: str


class WorkspaceRecommendedSkillOut(BaseModel):
    skill_id: uuid.UUID
    skill_name: str
    reason: str


class WorkspaceAwardOut(BaseModel):
    code: str
    name: str
    description: str
    skill_name: str | None = None
    awarded_at: datetime


class LearnerWorkspaceOut(BaseModel):
    session_id: uuid.UUID
    state: TutorState
    learner: LearnerIdentityOut
    curriculum: CurriculumContextOut
    focus: LearningFocusOut
    problem: WorkspaceProblemOut | None
    coaching_message: str | None
    allowed_actions: list[WorkspaceAction]
    evidence: WorkspaceEvidenceOut
    reviews_due: list[WorkspaceReviewDueOut] = Field(default_factory=list)
    awards: list[WorkspaceAwardOut] = Field(default_factory=list)
    recommended_next: WorkspaceRecommendedSkillOut | None = None


def _allowed_actions(state: TutorState) -> list[WorkspaceAction]:
    if state == TutorState.COMPLETE:
        return []

    actions: list[WorkspaceAction] = ["SUBMIT_ANSWER"]
    hint = select_hint(state=state, explicit_request=True)
    if hint.allowed:
        actions.extend(["REQUEST_HINT", "I_DONT_UNDERSTAND"])
    return actions


def _current_tutor_turn(db: Session, session_id: uuid.UUID) -> TutorTurn | None:
    return db.scalar(
        select(TutorTurn)
        .where(TutorTurn.session_id == session_id, TutorTurn.role == "TUTOR")
        .order_by(TutorTurn.created_at.desc(), TutorTurn.id.desc())
        .limit(1)
    )


@router.get("/sessions/{session_id}", response_model=LearnerWorkspaceOut)
def get_learner_workspace(
    session_id: uuid.UUID, parent: CurrentParent, db: DbSession
) -> LearnerWorkspaceOut:
    """Reconstruct only an authorized family's learner-visible state."""
    session = require_parent_owns_session(db, parent, db.get(TutorSession, session_id))

    try:
        scope = require_session_scope(db, session)
        primary_skill = require_skill_in_scope(db, skill_id=session.primary_skill_id, scope=scope)
        active_skill_id = session.active_skill_id or session.primary_skill_id
        active_skill = require_skill_in_scope(db, skill_id=active_skill_id, scope=scope)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc

    learner = db.get(Student, session.student_id)
    curriculum = db.get(Curriculum, scope.curriculum_id)
    if learner is None or curriculum is None:
        raise HTTPException(409, "Session curriculum or learner context is unavailable")

    turn = _current_tutor_turn(db, session.id)
    problem = db.get(Problem, turn.problem_id) if turn and turn.problem_id else None
    if problem is not None and problem.primary_skill_id != active_skill.id:
        raise HTTPException(409, "Persisted problem falls outside the active learning focus")

    progress = db.get(
        StudentSkill,
        {"student_id": session.student_id, "skill_id": active_skill.id},
    )

    return LearnerWorkspaceOut(
        session_id=session.id,
        state=session.current_state,
        learner=LearnerIdentityOut(
            first_name=learner.first_name,
            grade_level=learner.grade_level,
        ),
        curriculum=CurriculumContextOut(
            id=curriculum.id,
            name=curriculum.name,
            jurisdiction=curriculum.jurisdiction,
        ),
        focus=LearningFocusOut(
            primary_skill_id=primary_skill.id,
            active_skill_id=active_skill.id,
            skill_name=active_skill.name,
            in_remediation=active_skill.id != primary_skill.id,
            remediation_reason=session.remediation_reason,
        ),
        problem=(
            WorkspaceProblemOut(
                id=problem.id,
                prompt=problem.prompt,
                difficulty=problem.difficulty,
                visual=visualization_for(problem),
            )
            if problem
            else None
        ),
        coaching_message=turn.message if turn else None,
        allowed_actions=_allowed_actions(session.current_state),
        evidence=WorkspaceEvidenceOut(
            mastery_score=float(progress.mastery_score) if progress else 0.0,
            confidence_score=float(progress.confidence_score) if progress else 0.0,
            independent_attempt_count=progress.independent_attempt_count if progress else 0,
            independent_correct_count=progress.independent_correct_count if progress else 0,
            hinted_correct_count=progress.hinted_correct_count if progress else 0,
        ),
        reviews_due=[
            WorkspaceReviewDueOut(
                skill_id=item.skill.id,
                skill_name=item.skill.name,
                due_at=item.schedule.due_at,
                status=item.visibility_status,
            )
            for item in reviews_due(
                db,
                student_id=session.student_id,
                curriculum_id=scope.curriculum_id,
            )
        ],
        awards=[
            WorkspaceAwardOut(**award_out(db, award))
            for award in db.scalars(
                select(LearnerAward)
                .where(LearnerAward.student_id == session.student_id)
                .order_by(LearnerAward.created_at.desc())
                .limit(50)
            ).all()
        ],
        recommended_next=(
            WorkspaceRecommendedSkillOut(
                skill_id=recommendation.skill.id,
                skill_name=recommendation.skill.name,
                reason=recommendation.reason,
            )
            if (
                recommendation := recommend_next_skill(
                    db,
                    student_id=session.student_id,
                    curriculum_id=scope.curriculum_id,
                )
            )
            else None
        ),
    )


class BadgeProgressOut(BaseModel):
    current: int
    target: int


class BadgeOut(BaseModel):
    code: str
    name: str
    description: str
    earned: bool
    times_earned: int
    skill_names: list[str] = Field(default_factory=list)
    progress: BadgeProgressOut | None = None


@router.get("/sessions/{session_id}/badges", response_model=list[BadgeOut])
def get_badge_collection(
    session_id: uuid.UUID, parent: CurrentParent, db: DbSession
) -> list[BadgeOut]:
    """Full badge catalog for the learner owning this session."""
    session = require_parent_owns_session(db, parent, db.get(TutorSession, session_id))
    return [
        BadgeOut(**entry)
        for entry in badge_collection(db, session.student_id)
    ]


class SkillMapEntryOut(BaseModel):
    skill_id: uuid.UUID
    code: str
    name: str
    difficulty_level: int
    mastery_score: float
    status: str
    is_active: bool


@router.get("/sessions/{session_id}/skill-map", response_model=list[SkillMapEntryOut])
def get_skill_map(
    session_id: uuid.UUID, parent: CurrentParent, db: DbSession
) -> list[SkillMapEntryOut]:
    """All curriculum skills with the learner's mastery, ordered for display."""
    session = require_parent_owns_session(db, parent, db.get(TutorSession, session_id))
    try:
        scope = require_session_scope(db, session)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc

    # Group by strand (code prefix up to the last segment), then difficulty —
    # strands like NUM and ALG should render as contiguous groups, not
    # interleaved by difficulty_level.
    skills = sorted(
        db.scalars(
            select(Skill).where(Skill.curriculum_id == scope.curriculum_id)
        ).all(),
        key=lambda s: (s.code.rsplit(".", 1)[0], s.difficulty_level, s.code),
    )
    progress_rows = {
        row.skill_id: row
        for row in db.scalars(
            select(StudentSkill).where(StudentSkill.student_id == session.student_id)
        ).all()
    }
    active_skill_id = session.active_skill_id or session.primary_skill_id

    return [
        SkillMapEntryOut(
            skill_id=skill.id,
            code=skill.code,
            name=skill.name,
            difficulty_level=skill.difficulty_level,
            mastery_score=float(
                progress_rows[skill.id].mastery_score
            )
            if skill.id in progress_rows
            else 0.0,
            status=(
                progress_rows[skill.id].status.value
                if skill.id in progress_rows
                else "NOT_STARTED"
            ),
            is_active=skill.id == active_skill_id,
        )
        for skill in skills
    ]
