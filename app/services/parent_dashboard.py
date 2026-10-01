import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.curriculum_models import EducationAuthority, Jurisdiction, StudentCurriculumEnrollment
from app.models import (
    Curriculum,
    Misconception,
    Skill,
    SkillStatus,
    Student,
    StudentMisconception,
    StudentSkill,
    TutorSession,
    TutorState,
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
    GradeLevelSummaryOut,
    LinkChildOut,
    RecentActivityOut,
    RecommendedSkillOut,
    ReviewDueOut,
    SkillProgressOut,
    StrandSummaryOut,
    SupportAreaOut,
)
from app.services.curriculum_scope import CurriculumScopeError, resolve_student_curriculum_scope
from app.services.parent_intelligence import ParentSkillEvidence, classify_parent_skill_progress
from app.services.placement import recommend_next_skill
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
        seat_limit = locked_parent.max_students or 1
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
    )


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
