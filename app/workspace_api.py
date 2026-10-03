import uuid
from datetime import UTC, datetime, timedelta
from itertools import pairwise
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.identity import CurrentParent, require_parent_owns_session
from app.models import (
    Attempt,
    Curriculum,
    LearnerAward,
    Misconception,
    Problem,
    Skill,
    SkillStatus,
    Student,
    StudentSkill,
    TutorSession,
    TutorState,
    TutorTurn,
)
from app.schemas import ProblemChoiceOut, problem_choices_out
from app.services.awards import (
    BADGE_XP,
    attempt_xp,
    award_out,
    badge_collection,
    learner_progress,
)
from app.services.curriculum_scope import (
    CurriculumScopeError,
    require_session_scope,
    require_skill_in_scope,
)
from app.services.hint_policy import ASSESSMENT_STATES, select_hint
from app.services.placement import recommend_next_skill
from app.services.review_schedule import reviews_due
from app.services.stepwork import problem_supports_steps
from app.services.visualization import visualization_for

router = APIRouter(prefix="/learner-workspace", tags=["learner-workspace"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceAction = Literal["SUBMIT_ANSWER", "REQUEST_HINT", "I_DONT_UNDERSTAND"]


class LearnerIdentityOut(BaseModel):
    first_name: str
    grade_level: str
    avatar_id: str = "avatar-1"


class CurriculumContextOut(BaseModel):
    id: uuid.UUID
    name: str
    jurisdiction: str | None = None


class LearnExampleOut(BaseModel):
    title: str
    steps: list[str]
    answer: str | None = None


class LearnTermOut(BaseModel):
    term: str
    definition: str


class LearnContentOut(BaseModel):
    summary: str
    examples: list[LearnExampleOut] = Field(default_factory=list)
    key_terms: list[LearnTermOut] = Field(default_factory=list)
    watch_out: list[str] = Field(default_factory=list)


def build_learn_content(content: dict | None) -> LearnContentOut | None:
    """Wire-safe rendering of a skill's authored lesson. Shared by the workspace
    (state-gated) and the pre-session "learn this first" surface."""
    if not content or not isinstance(content, dict) or not content.get("summary"):
        return None
    examples = [
        LearnExampleOut(
            title=str(example.get("title", "")),
            steps=[str(step) for step in example.get("steps", [])],
            answer=str(example["answer"]) if example.get("answer") is not None else None,
        )
        for example in content.get("examples", [])
        if example.get("title") and example.get("steps")
    ]
    key_terms = [
        LearnTermOut(term=str(item.get("term", "")), definition=str(item.get("definition", "")))
        for item in content.get("key_terms", [])
        if item.get("term") and item.get("definition")
    ]
    watch_out = [str(item) for item in content.get("watch_out", []) if item]
    return LearnContentOut(
        summary=str(content["summary"]),
        examples=examples,
        key_terms=key_terms,
        watch_out=watch_out,
    )


class LearningFocusOut(BaseModel):
    primary_skill_id: uuid.UUID
    primary_skill_name: str
    active_skill_id: uuid.UUID
    skill_name: str
    in_remediation: bool
    remediation_reason: str | None = None
    learn: LearnContentOut | None = None


class WorkspaceProblemOut(BaseModel):
    id: uuid.UUID
    prompt: str
    difficulty: int
    visual: dict | None = None
    answer_kind: str = "FREE_TEXT"
    choices: list[ProblemChoiceOut] | None = None
    problem_type: str | None = None
    supports_steps: bool = False


class WorkspaceEvidenceOut(BaseModel):
    mastery_score: float
    confidence_score: float
    independent_attempt_count: int
    independent_correct_count: int
    hinted_correct_count: int
    smartscore: int = 0
    streak_count: int = 0
    mastery_level: str = "practicing"


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


class LearnerGrowthOut(BaseModel):
    xp: int
    level: int
    level_title: str
    xp_in_level: int
    xp_for_next: int
    xp_today: int = 0


class DailyGoalOut(BaseModel):
    target: int
    done: int
    reached: bool


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
    streak_days: int = 0
    growth: LearnerGrowthOut | None = None
    daily_goal: DailyGoalOut | None = None


def _allowed_actions(state: TutorState) -> list[WorkspaceAction]:
    if state == TutorState.COMPLETE:
        return []

    actions: list[WorkspaceAction] = ["SUBMIT_ANSWER"]
    hint = select_hint(state=state, explicit_request=True)
    if hint.allowed:
        actions.extend(["REQUEST_HINT", "I_DONT_UNDERSTAND"])
    return actions


def _learn_content(skill: Skill, *, state: TutorState) -> LearnContentOut | None:
    """Pre-practice instruction is hidden during assessment states, same as hints —
    a worked example during DIAGNOSE or MASTERY_CHECK would contaminate evidence."""
    if state in ASSESSMENT_STATES or state == TutorState.COMPLETE:
        return None
    return build_learn_content(skill.learn_content)


def _practice_streak_days(db: Session, student_id: uuid.UUID) -> int:
    """Consecutive calendar days with at least one session, counting back from
    today or yesterday (a streak isn't broken until a full day is missed)."""
    days = db.scalars(
        select(func.date(TutorSession.started_at))
        .where(TutorSession.student_id == student_id)
        .distinct()
        .order_by(func.date(TutorSession.started_at).desc())
    ).all()
    if not days:
        return 0
    today = datetime.now(UTC).date()
    if days[0] not in {today, today - timedelta(days=1)}:
        return 0
    streak = 1
    for previous, current in pairwise(days):
        if previous - current == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def _answer_streak(db: Session, student_id: uuid.UUID, skill_id: uuid.UUID) -> int:
    """Trailing run of correct answers on this skill — the SmartScore streak.

    Assisted successes still count (they are correct answers); only the
    evidence weight differs. Derived from Attempt rows — no new state.
    """
    rows = db.execute(
        select(Attempt.is_correct)
        .join(Problem, Problem.id == Attempt.problem_id)
        .where(
            Attempt.student_id == student_id,
            Problem.primary_skill_id == skill_id,
        )
        .order_by(Attempt.created_at.desc(), Attempt.id.desc())
        .limit(40)
    ).all()
    streak = 0
    for (correct,) in rows:
        if not correct:
            break
        streak += 1
    return streak


def _daily_goal(db: Session, student: Student) -> DailyGoalOut | None:
    """Questions answered today vs the learner-picked target, UTC day boundary.

    None when no target is set — no goal, no chip. `done` counts answer-level
    Attempt rows today across all of the learner's sessions.
    """
    if not student.daily_goal_questions:
        return None
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    done = db.scalar(
        select(func.count(Attempt.id)).where(
            Attempt.student_id == student.id,
            Attempt.is_correct.isnot(None),
            Attempt.created_at >= today_start,
        )
    ) or 0
    return DailyGoalOut(
        target=student.daily_goal_questions, done=done, reached=done >= student.daily_goal_questions
    )


def _mastery_level(progress: StudentSkill | None) -> str:
    """The three learner-facing labels; the state machine still owns truth."""
    if progress is None:
        return "practicing"
    if progress.status == SkillStatus.MASTERED:
        return "mastered"
    if float(progress.mastery_score) >= 0.7:
        return "proficient"
    return "practicing"


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
            avatar_id=learner.avatar_id,
        ),
        curriculum=CurriculumContextOut(
            id=curriculum.id,
            name=curriculum.name,
            jurisdiction=curriculum.jurisdiction,
        ),
        focus=LearningFocusOut(
            primary_skill_id=primary_skill.id,
            primary_skill_name=primary_skill.name,
            active_skill_id=active_skill.id,
            skill_name=active_skill.name,
            in_remediation=active_skill.id != primary_skill.id,
            remediation_reason=session.remediation_reason,
            learn=_learn_content(active_skill, state=session.current_state),
        ),
        problem=(
            WorkspaceProblemOut(
                id=problem.id,
                prompt=problem.prompt,
                difficulty=problem.difficulty,
                visual=visualization_for(problem),
                answer_kind=problem.answer_kind,
                choices=problem_choices_out(problem.choices),
                problem_type=problem.problem_type,
                supports_steps=problem_supports_steps(problem),
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
            smartscore=round(float(progress.mastery_score) * 100) if progress else 0,
            streak_count=_answer_streak(db, session.student_id, active_skill.id),
            mastery_level=_mastery_level(progress),
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
        streak_days=_practice_streak_days(db, session.student_id),
        growth=LearnerGrowthOut(**learner_progress(db, session.student_id)),
        daily_goal=_daily_goal(db, learner),
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


class DailyGoalPatchIn(BaseModel):
    questions_per_day: int | None = Field(default=None, ge=1, le=60)


@router.patch("/sessions/{session_id}/daily-goal", response_model=DailyGoalOut | None)
def patch_daily_goal(
    session_id: uuid.UUID, payload: DailyGoalPatchIn, parent: CurrentParent, db: DbSession
) -> DailyGoalOut | None:
    """Set (or clear) the learner's daily question target."""
    session = require_parent_owns_session(db, parent, db.get(TutorSession, session_id))
    learner = db.get(Student, session.student_id)
    if learner is None:
        raise HTTPException(409, "Session learner context is unavailable")
    learner.daily_goal_questions = payload.questions_per_day
    db.commit()
    return _daily_goal(db, learner)


class SessionMisconceptionOut(BaseModel):
    code: str
    name: str
    resolved: bool


class SessionSummaryOut(BaseModel):
    attempts: int
    correct: int
    independent_correct: int
    minutes: int
    xp_earned: int
    smartscore_start: int | None
    smartscore_now: int
    skills_practiced: list[str]
    misconceptions: list[SessionMisconceptionOut]
    awards: list[WorkspaceAwardOut]
    daily_goal: DailyGoalOut | None


@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryOut)
def get_session_summary(
    session_id: uuid.UUID, parent: CurrentParent, db: DbSession
) -> SessionSummaryOut:
    """End-of-session recap, derived entirely from persisted evidence."""
    session = require_parent_owns_session(db, parent, db.get(TutorSession, session_id))
    learner = db.get(Student, session.student_id)
    if learner is None:
        raise HTTPException(409, "Session learner context is unavailable")

    attempts = db.scalars(
        select(Attempt)
        .where(Attempt.session_id == session.id, Attempt.is_correct.isnot(None))
        .order_by(Attempt.created_at, Attempt.id)
    ).all()

    # A misconception counts as resolved when a correct answer came after it.
    misconception_rows: dict[uuid.UUID, int] = {}
    resolved_at: dict[uuid.UUID, int] = {}
    for index, attempt in enumerate(attempts):
        if attempt.misconception_id is not None:
            misconception_rows.setdefault(attempt.misconception_id, index)
        if attempt.is_correct:
            for mid, first_index in misconception_rows.items():
                if index > first_index:
                    resolved_at[mid] = index
    misconception_seen: list[SessionMisconceptionOut] = []
    if misconception_rows:
        names = {
            row.id: (row.code, row.name)
            for row in db.scalars(
                select(Misconception).where(Misconception.id.in_(misconception_rows))
            ).all()
        }
        misconception_seen = [
            SessionMisconceptionOut(
                code=names.get(mid, ("", ""))[0],
                name=names.get(mid, ("", ""))[1],
                resolved=mid in resolved_at,
            )
            for mid in misconception_rows
        ]

    skill_names = db.execute(
        select(Skill.name)
        .join(Problem, Problem.primary_skill_id == Skill.id)
        .where(Problem.id.in_({a.problem_id for a in attempts}))
        .distinct()
    ).all() if attempts else []
    skills_practiced = [name for (name,) in skill_names]

    session_awards = db.scalars(
        select(LearnerAward)
        .where(LearnerAward.session_id == session.id)
        .order_by(LearnerAward.created_at)
    ).all()

    problem_difficulty = {
        pid: diff
        for pid, diff in db.execute(
            select(Problem.id, Problem.difficulty).where(
                Problem.id.in_({a.problem_id for a in attempts})
            )
        ).all()
    } if attempts else {}
    xp = sum(
        attempt_xp(
            bool(a.is_correct), int(a.assistance_level or 0), int(problem_difficulty.get(a.problem_id, 1))
        )
        for a in attempts
    ) + sum(BADGE_XP.get(a.badge_code, 0) for a in session_awards)

    progress = db.get(
        StudentSkill, {"student_id": session.student_id, "skill_id": session.primary_skill_id}
    )
    smartscore_now = round(float(progress.mastery_score) * 100) if progress else 0
    smartscore_start = (
        round(float(session.starting_mastery) * 100)
        if session.starting_mastery is not None
        else None
    )

    minutes = 0
    if attempts:
        minutes = max(
            1, round((attempts[-1].created_at - session.started_at).total_seconds() / 60)
        )

    return SessionSummaryOut(
        attempts=len(attempts),
        correct=sum(1 for a in attempts if a.is_correct),
        independent_correct=sum(
            1 for a in attempts if a.is_correct and (a.assistance_level or 0) == 0
        ),
        minutes=minutes,
        xp_earned=xp,
        smartscore_start=smartscore_start,
        smartscore_now=smartscore_now,
        skills_practiced=skills_practiced,
        misconceptions=misconception_seen,
        awards=[WorkspaceAwardOut(**award_out(db, award)) for award in session_awards],
        daily_goal=_daily_goal(db, learner),
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
    return [BadgeOut(**entry) for entry in badge_collection(db, session.student_id)]


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

    skills = db.scalars(
        select(Skill)
        .where(Skill.curriculum_id == scope.curriculum_id)
        .order_by(Skill.difficulty_level, Skill.code)
    ).all()
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
            mastery_score=float(progress_rows[skill.id].mastery_score)
            if skill.id in progress_rows
            else 0.0,
            status=(
                progress_rows[skill.id].status.value if skill.id in progress_rows else "NOT_STARTED"
            ),
            is_active=skill.id == active_skill_id,
        )
        for skill in skills
    ]
