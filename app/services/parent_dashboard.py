import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.curriculum_models import EducationAuthority, Jurisdiction, StudentCurriculumEnrollment
from app.models import (
    Attempt,
    Curriculum,
    LearnerAward,
    MasteryEvent,
    Misconception,
    Problem,
    Skill,
    SkillStatus,
    Student,
    StudentMisconception,
    StudentSkill,
    TutorSession,
    TutorState,
    TutorTurn,
)
from app.parent_models import (
    ChildLinkClaim,
    ParentProfile,
    ParentStudentRelationship,
    ParentStudentRelationshipEvent,
)
from app.parent_schemas import (
    ChildDashboardOut,
    ChildSummaryOut,
    DailyMetricOut,
    GradeLevelSummaryOut,
    LinkChildOut,
    RecentActivityOut,
    RecentPatternOut,
    RecommendedSkillOut,
    ReviewDueOut,
    SkillProgressOut,
    StepTrailOut,
    StrandSummaryOut,
    SupportAreaOut,
    WeeklyDigestOut,
    WorkStepLineOut,
)
from app.services.awards import BADGE_XP, attempt_xp
from app.services.curriculum_scope import CurriculumScopeError, resolve_student_curriculum_scope
from app.services.parent_intelligence import ParentSkillEvidence, classify_parent_skill_progress
from app.services.placement import recommend_next_skill
from app.services.plans import effective_seats
from app.services.review_schedule import RELEARNING, reviews_due


def hash_claim_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _parent_skill_status(progress: StudentSkill, *, mastery_check: bool) -> str:
    if mastery_check:
        return "Mastery Check"
    if progress.status == SkillStatus.MASTERED:
        return "Mastered"
    if progress.status == SkillStatus.REVIEW_DUE:
        return "Needs Practice"
    return "In Progress"


def _parent_session_state(state: TutorState) -> str:
    if state == TutorState.MASTERY_CHECK:
        return "Mastery Check"
    if state in {TutorState.REMEDIATION, TutorState.REVIEW}:
        return "Needs Practice"
    if state == TutorState.COMPLETE:
        return "Completed"
    return "In Progress"


def _skill_progress_out(
    progress: StudentSkill, skill: Skill, *, mastery_check: bool
) -> SkillProgressOut:
    insight = classify_parent_skill_progress(
        ParentSkillEvidence(
            attempt_count=progress.attempt_count,
            independent_attempt_count=progress.independent_attempt_count,
            independent_correct_count=progress.independent_correct_count,
            hinted_correct_count=progress.hinted_correct_count,
            status=progress.status,
        )
    )
    return SkillProgressOut(
        skill_id=skill.id,
        skill_code=skill.code,
        skill_name=skill.name,
        status=_parent_skill_status(progress, mastery_check=mastery_check),
        attempt_count=progress.attempt_count,
        independent_attempt_count=progress.independent_attempt_count,
        independent_correct_count=progress.independent_correct_count,
        hinted_correct_count=progress.hinted_correct_count,
        evidence_status=insight.evidence_status,
        learning_state=insight.learning_state,
        assistance_signal=insight.assistance_signal,
        reason_code=insight.reason_code,
        action_code=insight.action_code,
    )


def _active_relationship(
    db: Session, *, parent_id: uuid.UUID, student_id: uuid.UUID
) -> ParentStudentRelationship | None:
    return db.scalar(
        select(ParentStudentRelationship).where(
            ParentStudentRelationship.parent_profile_id == parent_id,
            ParentStudentRelationship.student_id == student_id,
            ParentStudentRelationship.active.is_(True),
        )
    )


def require_linked_child(
    db: Session, *, parent: ParentProfile, student_id: uuid.UUID
) -> Student:
    relationship = _active_relationship(db, parent_id=parent.id, student_id=student_id)
    if relationship is None:
        raise HTTPException(status_code=403, detail="Child is not linked to this parent")
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return student


def _jurisdiction_path(db: Session, jurisdiction_id: uuid.UUID | None) -> list[str]:
    path: list[str] = []
    seen: set[uuid.UUID] = set()
    current_id = jurisdiction_id
    while current_id is not None and current_id not in seen:
        seen.add(current_id)
        jurisdiction = db.get(Jurisdiction, current_id)
        if jurisdiction is None:
            break
        path.append(jurisdiction.name)
        current_id = jurisdiction.parent_id
    path.reverse()
    return path


def child_summary(db: Session, student: Student) -> ChildSummaryOut:
    try:
        scope = resolve_student_curriculum_scope(db, student)
    except CurriculumScopeError:
        return ChildSummaryOut(
            id=student.id,
            first_name=student.first_name,
            grade_level=student.grade_level,
            school_system=student.school_system,
        )

    curriculum = db.get(Curriculum, scope.curriculum_id)
    enrollment = (
        db.get(StudentCurriculumEnrollment, scope.enrollment_id)
        if scope.enrollment_id is not None
        else None
    )
    curriculum_authority = (
        db.get(EducationAuthority, curriculum.authority_id)
        if curriculum is not None and curriculum.authority_id is not None
        else None
    )
    local_authority_id = (
        enrollment.local_authority_id if enrollment is not None else scope.local_authority_id
    )
    local_authority = (
        db.get(EducationAuthority, local_authority_id) if local_authority_id is not None else None
    )
    jurisdiction_id = (
        curriculum_authority.jurisdiction_id
        if curriculum_authority is not None
        else (local_authority.jurisdiction_id if local_authority is not None else None)
    )
    return ChildSummaryOut(
        id=student.id,
        first_name=student.first_name,
        grade_level=student.grade_level,
        school_system=student.school_system,
        curriculum_name=curriculum.name if curriculum else None,
        curriculum_code=curriculum.code if curriculum else None,
        curriculum_version=curriculum.version if curriculum else None,
        curriculum_authority_name=(curriculum_authority.name if curriculum_authority else None),
        jurisdiction=curriculum.jurisdiction if curriculum else None,
        jurisdiction_path=_jurisdiction_path(db, jurisdiction_id),
        local_authority_name=local_authority.name if local_authority else None,
    )


def list_children(db: Session, *, parent: ParentProfile) -> list[ChildSummaryOut]:
    students = db.scalars(
        select(Student)
        .join(
            ParentStudentRelationship,
            ParentStudentRelationship.student_id == Student.id,
        )
        .where(
            ParentStudentRelationship.parent_profile_id == parent.id,
            ParentStudentRelationship.active.is_(True),
        )
        .order_by(Student.first_name, Student.id)
    ).all()
    return [child_summary(db, student) for student in students]


def link_child_with_claim(
    db: Session, *, parent: ParentProfile, claim_token: str
) -> LinkChildOut:
    now = datetime.now(UTC)
    claim = db.scalar(
        select(ChildLinkClaim).where(ChildLinkClaim.token_hash == hash_claim_token(claim_token))
    )
    if claim is None or claim.consumed_at is not None or claim.expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid or expired child link claim")

    student = db.get(Student, claim.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Child not found")

    relationship = db.scalar(
        select(ParentStudentRelationship).where(
            ParentStudentRelationship.parent_profile_id == parent.id,
            ParentStudentRelationship.student_id == student.id,
        )
    )
    if relationship is None or not relationship.active:
        locked_parent = db.scalar(
            select(ParentProfile).where(ParentProfile.id == parent.id).with_for_update()
        )
        if locked_parent is None:
            raise HTTPException(status_code=404, detail="Parent profile not found")
        active_relationships = int(
            db.scalar(
                select(func.count(ParentStudentRelationship.id)).where(
                    ParentStudentRelationship.parent_profile_id == parent.id,
                    ParentStudentRelationship.active.is_(True),
                )
            )
            or 0
        )
        seat_limit = effective_seats(db, locked_parent)
        if active_relationships >= seat_limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "STUDENT_SEAT_LIMIT_REACHED",
                    "subscription_tier": locked_parent.subscription_tier,
                    "current_students": active_relationships,
                    "max_students": seat_limit,
                    "upgrade": {"recommended_tier": "pro", "max_students": 5},
                },
            )

    action = "LINKED"
    if relationship is None:
        relationship = ParentStudentRelationship(
            parent_profile_id=parent.id,
            student_id=student.id,
            relationship_type="GUARDIAN",
            active=True,
        )
        db.add(relationship)
        db.flush()
    else:
        relationship.active = True
        relationship.unlinked_at = None
        action = "RELINKED"

    db.add(ParentStudentRelationshipEvent(relationship_id=relationship.id, action=action))
    claim.consumed_at = now
    db.flush()
    return LinkChildOut(
        child=child_summary(db, student),
        relationship_type=relationship.relationship_type,
    )


def unlink_child(db: Session, *, parent: ParentProfile, student_id: uuid.UUID) -> None:
    relationship = _active_relationship(db, parent_id=parent.id, student_id=student_id)
    if relationship is None:
        raise HTTPException(status_code=404, detail="Active child relationship not found")
    relationship.active = False
    relationship.unlinked_at = datetime.now(UTC)
    db.add(ParentStudentRelationshipEvent(relationship_id=relationship.id, action="UNLINKED"))
    db.flush()


def dashboard(db: Session, *, parent: ParentProfile, student_id: uuid.UUID) -> ChildDashboardOut:
    student = require_linked_child(db, parent=parent, student_id=student_id)
    try:
        scope = resolve_student_curriculum_scope(db, student)
    except CurriculumScopeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    active_session = db.scalar(
        select(TutorSession)
        .where(
            TutorSession.student_id == student.id,
            TutorSession.status == "ACTIVE",
            or_(
                TutorSession.curriculum_id == scope.curriculum_id,
                TutorSession.curriculum_id.is_(None),
            ),
        )
        .order_by(desc(TutorSession.started_at))
        .limit(1)
    )
    mastery_check_skill_id = None
    active_skill_name = None
    if active_session and active_session.active_skill_id:
        active_skill = db.get(Skill, active_session.active_skill_id)
        if active_skill and active_skill.curriculum_id == scope.curriculum_id:
            active_skill_name = active_skill.name
            if active_session.current_state == TutorState.MASTERY_CHECK:
                mastery_check_skill_id = active_session.active_skill_id

    progress_rows = db.execute(
        select(StudentSkill, Skill)
        .join(Skill, Skill.id == StudentSkill.skill_id)
        .where(
            StudentSkill.student_id == student.id,
            Skill.curriculum_id == scope.curriculum_id,
        )
        .order_by(Skill.name)
    ).all()
    skills = [
        _skill_progress_out(
            progress,
            skill,
            mastery_check=skill.id == mastery_check_skill_id,
        )
        for progress, skill in progress_rows
    ]

    sessions = db.execute(
        select(TutorSession, Skill)
        .join(Skill, Skill.id == TutorSession.primary_skill_id)
        .where(
            TutorSession.student_id == student.id,
            Skill.curriculum_id == scope.curriculum_id,
            or_(
                TutorSession.curriculum_id == scope.curriculum_id,
                TutorSession.curriculum_id.is_(None),
            ),
        )
        .order_by(desc(TutorSession.started_at))
        .limit(10)
    ).all()
    recent_activity = [
        RecentActivityOut(
            session_id=session.id,
            skill_name=skill.name,
            state=_parent_session_state(session.current_state),
            started_at=session.started_at,
            ended_at=session.ended_at,
        )
        for session, skill in sessions
    ]

    support_rows = db.execute(
        select(StudentMisconception, Misconception, Skill.name)
        .join(Misconception, Misconception.id == StudentMisconception.misconception_id)
        .join(Skill, Skill.id == Misconception.skill_id)
        .where(
            StudentMisconception.student_id == student.id,
            StudentMisconception.status == "ACTIVE",
            Skill.curriculum_id == scope.curriculum_id,
        )
        .order_by(desc(StudentMisconception.occurrence_count))
        .limit(10)
    ).all()
    support_areas = [
        SupportAreaOut(
            code=misconception.code,
            name=misconception.name,
            occurrence_count=student_misconception.occurrence_count,
        )
        for student_misconception, misconception, _skill_name in support_rows
    ]
    support_skill_names = [skill_name for *_rest, skill_name in support_rows]

    review_items = reviews_due(
        db, student_id=student.id, curriculum_id=scope.curriculum_id
    )
    reviews_due_out = [
        ReviewDueOut(
            skill_id=item.skill.id,
            skill_code=item.skill.code,
            skill_name=item.skill.name,
            status="Relearning" if item.visibility_status == RELEARNING else "Due",
            due_at=item.schedule.due_at,
            interval_index=item.schedule.interval_index,
            mastery_score=float(item.progress.mastery_score),
            projected_mastery_score=item.projected_mastery,
        )
        for item in review_items
    ]

    recommendation = recommend_next_skill(
        db, student_id=student.id, curriculum_id=scope.curriculum_id
    )

    summary = _grade_level_summary(
        db,
        student_id=student.id,
        scope=scope,
        progress_rows=progress_rows,
        support_skill_names=support_skill_names,
    )

    daily_metrics, weekly_digest = _learning_trends(
        db, student_id=student.id, scope=scope
    )

    step_trails = _step_trails(db, student_id=student.id, scope=scope)
    recent_patterns = _recent_patterns(db, student_id=student.id, scope=scope)

    return ChildDashboardOut(
        child=child_summary(db, student),
        active_skill_name=active_skill_name,
        skills=skills,
        recent_activity=recent_activity,
        support_areas=support_areas,
        reviews_due=reviews_due_out,
        recommended_next=(
            RecommendedSkillOut(
                skill_id=recommendation.skill.id,
                skill_code=recommendation.skill.code,
                skill_name=recommendation.skill.name,
                reason=recommendation.reason,
            )
            if recommendation
            else None
        ),
        grade_level_summary=summary,
        daily_metrics=daily_metrics,
        weekly_digest=weekly_digest,
        step_trails=step_trails,
        recent_patterns=recent_patterns,
    )


def _recent_patterns(
    db: Session,
    *,
    student_id: uuid.UUID,
    scope,
    days: int = 7,
    limit: int = 3,
) -> list[RecentPatternOut]:
    """Top misconception patterns over the last week.

    Combines answer-level classifications (Attempt.misconception_id) and
    step-level transition classifications (WORK_STEP turns) — aggregated
    counts only, no raw learner text is read.
    """
    since = datetime.now(UTC) - timedelta(days=days)

    answer_rows = db.execute(
        select(Misconception.code, Misconception.name, func.count())
        .join(Attempt, Attempt.misconception_id == Misconception.id)
        .join(TutorSession, TutorSession.id == Attempt.session_id)
        .join(Skill, Skill.id == Misconception.skill_id)
        .where(
            TutorSession.student_id == student_id,
            Attempt.created_at >= since,
            Skill.curriculum_id == scope.curriculum_id,
        )
        .group_by(Misconception.code, Misconception.name)
        .limit(500)
    ).all()

    # JSONB extraction can't be grouped by label portably — count in Python
    # over a bounded window of rows.
    step_rows = db.execute(
        select(
            TutorTurn.metadata_json["misconception_code"].as_string(),
            Problem.primary_skill_id,
        )
        .join(TutorSession, TutorSession.id == TutorTurn.session_id)
        .join(Problem, Problem.id == TutorTurn.problem_id)
        .join(Skill, Skill.id == Problem.primary_skill_id)
        .where(
            TutorSession.student_id == student_id,
            TutorTurn.pedagogical_action == "WORK_STEP",
            TutorTurn.metadata_json["step_status"].as_string() == "invalid",
            TutorTurn.metadata_json["misconception_code"].as_string().is_not(None),
            TutorTurn.created_at >= since,
            Skill.curriculum_id == scope.curriculum_id,
        )
        .limit(2000)
    ).all()
    step_counts: dict[tuple[uuid.UUID, str], int] = {}
    for code, skill_id in step_rows:
        key = (skill_id, code)
        step_counts[key] = step_counts.get(key, 0) + 1

    # Resolve step-level codes to names within their owning skill.
    step_keys = set(step_counts)
    step_names: dict[tuple[uuid.UUID, str], str] = {}
    if step_keys:
        for skill_id, code, name in db.execute(
            select(Misconception.skill_id, Misconception.code, Misconception.name).where(
                Misconception.skill_id.in_({s for s, _ in step_keys}),
                Misconception.code.in_({c for _, c in step_keys}),
            )
        ):
            step_names[(skill_id, code)] = name

    counts: dict[str, dict] = {}
    for code, name, n in answer_rows:
        entry = counts.setdefault(code, {"name": name, "n": 0, "answer": 0, "steps": 0})
        entry["n"] += n
        entry["answer"] += n
    for (skill_id, code), n in step_counts.items():
        name = step_names.get((skill_id, code))
        if name is None:
            continue
        entry = counts.setdefault(code, {"name": name, "n": 0, "answer": 0, "steps": 0})
        entry["n"] += n
        entry["steps"] += n

    top = sorted(counts.items(), key=lambda kv: -kv[1]["n"])[:limit]
    return [
        RecentPatternOut(
            code=code,
            name=data["name"],
            count=data["n"],
            source=(
                "both"
                if data["answer"] and data["steps"]
                else ("answer" if data["answer"] else "steps")
            ),
        )
        for code, data in top
    ]


def _step_trails(
    db: Session,
    *,
    student_id: uuid.UUID,
    scope,
    limit_problems: int = 5,
) -> list[StepTrailOut]:
    """Recent step-worked problems so parents can see where the work stumbled."""
    rows = db.execute(
        select(TutorTurn, Problem, Skill)
        .join(TutorSession, TutorSession.id == TutorTurn.session_id)
        .join(Problem, Problem.id == TutorTurn.problem_id)
        .join(Skill, Skill.id == Problem.primary_skill_id)
        .where(
            TutorSession.student_id == student_id,
            TutorTurn.pedagogical_action == "WORK_STEP",
            Skill.curriculum_id == scope.curriculum_id,
            # "Recent" must stay a bounded window so the scan rides the
            # (session_id, created_at) index instead of the full table.
            TutorTurn.created_at >= datetime.now(UTC) - timedelta(days=90),
        )
        .order_by(desc(TutorTurn.created_at), desc(TutorTurn.id))
        .limit(400)
    ).all()

    grouped: dict[uuid.UUID, dict] = {}
    order: list[uuid.UUID] = []
    for turn, problem, skill in rows:
        entry = grouped.get(problem.id)
        if entry is None:
            if len(order) >= limit_problems:
                continue
            entry = {
                "problem": problem,
                "skill": skill,
                "turns": [],
                "updated_at": turn.created_at,
            }
            grouped[problem.id] = entry
            order.append(problem.id)
        entry["turns"].append(turn)

    code_pairs = {
        (entry["problem"].primary_skill_id, (t.metadata_json or {}).get("misconception_code"))
        for entry in grouped.values()
        for t in entry["turns"]
        if (t.metadata_json or {}).get("misconception_code")
    }
    name_lookup: dict[tuple[uuid.UUID, str], str] = {}
    if code_pairs:
        skill_ids = {skill_id for skill_id, _ in code_pairs}
        codes = {code for _, code in code_pairs}
        for skill_id, code, name in db.execute(
            select(Misconception.skill_id, Misconception.code, Misconception.name).where(
                Misconception.skill_id.in_(skill_ids),
                Misconception.code.in_(codes),
            )
        ):
            name_lookup[(skill_id, code)] = name

    trails: list[StepTrailOut] = []
    for problem_id in order:
        entry = grouped[problem_id]
        problem = entry["problem"]
        turns = list(reversed(entry["turns"]))  # chronological within the trail
        lines = [
            WorkStepLineOut(
                line=(t.metadata_json or {}).get("normalized_line")
                or (t.metadata_json or {}).get("line")
                or t.message,
                status=(t.metadata_json or {}).get("step_status") or "invalid",
                misconception_code=(t.metadata_json or {}).get("misconception_code"),
                revealed=bool((t.metadata_json or {}).get("revealed")),
            )
            for t in turns
        ]
        statuses = {line.status for line in lines}
        if "solved" in statuses:
            status = "SOLVED"
        elif statuses & {"invalid", "unparseable"} or any(line.revealed for line in lines):
            status = "STRUGGLED"
        else:
            status = "IN_PROGRESS"
        misconception_names = sorted(
            {
                name_lookup[(problem.primary_skill_id, line.misconception_code)]
                for line in lines
                if line.misconception_code
                and (problem.primary_skill_id, line.misconception_code) in name_lookup
            }
        )
        trails.append(
            StepTrailOut(
                problem_id=problem.id,
                prompt=problem.prompt,
                skill_name=entry["skill"].name,
                updated_at=entry["updated_at"],
                status=status,
                lines=lines,
                misconception_names=misconception_names,
            )
        )
    return trails


def _learning_trends(
    db: Session,
    *,
    student_id: uuid.UUID,
    scope,
) -> tuple[list[DailyMetricOut], WeeklyDigestOut]:
    """14-day daily activity + week-over-week digest from authoritative rows."""
    now = datetime.now(UTC)
    window_start = (now - timedelta(days=13)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_start = (now - timedelta(days=6)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    sessions = db.scalars(
        select(TutorSession).where(
            TutorSession.student_id == student_id,
            TutorSession.started_at >= window_start,
            or_(
                TutorSession.curriculum_id == scope.curriculum_id,
                TutorSession.curriculum_id.is_(None),
            ),
        )
    ).all()

    # Daily minutes — same duration convention as the grade-level summary.
    minutes_by_day: dict[str, int] = {}
    for session in sessions:
        day = session.started_at.date().isoformat()
        minutes = int(
            ((session.ended_at or session.started_at) - session.started_at).total_seconds() // 60
        )
        minutes_by_day[day] = minutes_by_day.get(day, 0) + max(minutes, 0)

    # Mastery line — last recorded score per day, carried forward across
    # quiet days. Baseline is the earliest event's previous_score.
    events = db.scalars(
        select(MasteryEvent)
        .where(
            MasteryEvent.student_id == student_id,
            MasteryEvent.created_at >= window_start,
        )
        .order_by(MasteryEvent.created_at)
    ).all()
    score_by_day: dict[str, float] = {}
    baseline = 0.0
    for event in events:
        if not score_by_day:
            baseline = float(event.previous_score)
        score_by_day[event.created_at.date().isoformat()] = float(event.new_score)
    # Carry the pre-window score forward if earlier events exist.
    prior_event = db.scalar(
        select(MasteryEvent)
        .where(
            MasteryEvent.student_id == student_id,
            MasteryEvent.created_at < window_start,
        )
        .order_by(desc(MasteryEvent.created_at))
        .limit(1)
    )
    running = float(prior_event.new_score) if prior_event else baseline

    day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    daily_metrics: list[DailyMetricOut] = []
    week_mastery_start = running
    for offset in range(14):
        day = (window_start + timedelta(days=offset)).date()
        key = day.isoformat()
        running = score_by_day.get(key, running)
        if day < week_start.date():
            week_mastery_start = running
        daily_metrics.append(
            DailyMetricOut(
                date=key,
                label=day_labels[(day.weekday() + 1) % 7],
                minutes=minutes_by_day.get(key, 0),
                mastery_score=round(running * 100, 1),
            )
        )

    def _week_bounds(days_ago_start: int, days_ago_end: int) -> tuple[datetime, datetime]:
        start = (now - timedelta(days=days_ago_start)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = (now - timedelta(days=days_ago_end)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return start, end

    this_lo, this_hi = _week_bounds(6, -1)
    prev_lo, prev_hi = _week_bounds(13, 6)

    def _sessions_between(lo: datetime, hi: datetime) -> list[TutorSession]:
        return [
            s for s in sessions if lo <= s.started_at < hi
        ]

    this_sessions = _sessions_between(this_lo, this_hi)
    prev_sessions = _sessions_between(prev_lo, prev_hi)

    def _minutes(items: list[TutorSession]) -> int:
        return sum(
            max(
                int(((s.ended_at or s.started_at) - s.started_at).total_seconds() // 60),
                0,
            )
            for s in items
        )

    week_attempts = db.execute(
        select(Attempt.is_correct, Attempt.assistance_level, Problem.difficulty)
        .join(Problem, Attempt.problem_id == Problem.id)
        .where(
            Attempt.student_id == student_id,
            Attempt.is_correct.isnot(None),
            Attempt.created_at >= this_lo,
        )
    ).all()
    xp_earned = sum(
        attempt_xp(bool(ok), int(assistance or 0), int(diff or 1))
        for ok, assistance, diff in week_attempts
    )
    week_awards = db.scalars(
        select(LearnerAward).where(
            LearnerAward.student_id == student_id,
            LearnerAward.created_at >= this_lo,
        )
    ).all()
    xp_earned += sum(BADGE_XP.get(a.badge_code, 0) for a in week_awards)

    last_attempt_at = db.scalar(
        select(func.max(Attempt.created_at)).where(Attempt.student_id == student_id)
    )
    days_since = (
        (now.date() - last_attempt_at.date()).days if last_attempt_at else None
    )

    digest = WeeklyDigestOut(
        sessions=len(this_sessions),
        minutes=_minutes(this_sessions),
        xp_earned=xp_earned,
        skills_mastered=sum(1 for a in week_awards if a.badge_code == "SKILL_MASTERED"),
        badges_earned=len(week_awards),
        prev_sessions=len(prev_sessions),
        prev_minutes=_minutes(prev_sessions),
        minutes_delta=_minutes(this_sessions) - _minutes(prev_sessions),
        mastery_delta=(
            round((running - week_mastery_start) * 100, 1)
            if events or prior_event
            else None
        ),
        days_since_practice=days_since,
        stall=days_since is not None and days_since >= 3,
    )
    return daily_metrics, digest


def _strand_for(code: str, name: str) -> str:
    """Mirror the learner Explore Topics grouping so parent and learner views
    use the same strand vocabulary."""
    text = f"{code} {name}".lower()
    if "fraction" in text or "decimal" in text:
        return "Fractions & decimals"
    if any(
        term in text
        for term in ("geometr", "shape", "angle", "coordinate", "area", "perimeter", "volume", "line")
    ):
        return "Geometry"
    if any(term in text for term in ("measure", "length", "time", "money", "clock")):
        return "Measurement & time"
    if any(term in text for term in ("graph", "data", "plot", "table")):
        return "Data & graphs"
    if any(
        term in text
        for term in ("pattern", "equation", "algebra", "expression", "distribut", "linear", "variable")
    ):
        return "Patterns & algebra"
    if "percent" in text or "financial" in text or "discount" in text or "tax" in text:
        return "Percent & financial"
    if "proportion" in text or "rate" in text or "ratio" in text:
        return "Ratios & proportions"
    return "Numbers & operations"


def _grade_level_summary(
    db: Session,
    *,
    student_id: uuid.UUID,
    scope,
    progress_rows,
    support_skill_names: list[str],
) -> GradeLevelSummaryOut | None:
    curriculum = db.get(Curriculum, scope.curriculum_id)
    curriculum_skills = db.scalars(
        select(Skill).where(Skill.curriculum_id == scope.curriculum_id)
    ).all()
    if not curriculum_skills:
        return None

    progress_by_skill = {progress.skill_id: progress for progress, _skill in progress_rows}

    mastered = in_progress = 0
    strands: dict[str, StrandSummaryOut] = {}
    trouble: list[str] = list(support_skill_names)
    for skill in curriculum_skills:
        progress = progress_by_skill.get(skill.id)
        if progress is None:
            bucket = "not_started"
        elif progress.status == SkillStatus.MASTERED:
            mastered += 1
            bucket = "mastered"
        else:
            in_progress += 1
            bucket = "in_progress"
            if (
                progress.independent_attempt_count >= 3
                and progress.independent_correct_count == 0
                and skill.name not in trouble
            ):
                trouble.append(skill.name)

        strand = _strand_for(skill.code, skill.name)
        entry = strands.setdefault(
            strand, StrandSummaryOut(strand=strand, total=0, mastered=0, in_progress=0)
        )
        entry.total += 1
        if bucket == "mastered":
            entry.mastered += 1
        elif bucket == "in_progress":
            entry.in_progress += 1

    week_ago = datetime.now(UTC) - timedelta(days=7)
    week_sessions = db.scalars(
        select(TutorSession).where(
            TutorSession.student_id == student_id,
            TutorSession.started_at >= week_ago,
            or_(
                TutorSession.curriculum_id == scope.curriculum_id,
                TutorSession.curriculum_id.is_(None),
            ),
        )
    ).all()
    minutes = sum(
        int(
            ((session.ended_at or session.started_at) - session.started_at).total_seconds() // 60
        )
        for session in week_sessions
    )

    total = len(curriculum_skills)
    return GradeLevelSummaryOut(
        curriculum_code=curriculum.code if curriculum else None,
        curriculum_name=curriculum.name if curriculum else None,
        skills_total=total,
        skills_mastered=mastered,
        skills_in_progress=in_progress,
        skills_not_started=total - mastered - in_progress,
        mastery_percent=round(100.0 * mastered / total, 1),
        strands=sorted(strands.values(), key=lambda s: s.strand),
        sessions_last_7_days=len(week_sessions),
        minutes_last_7_days=int(minutes),
        trouble_spots=trouble[:5],
    )
