import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    Attempt,
    Curriculum,
    LearnerAward,
    MasteryEvent,
    Problem,
    Skill,
    SkillStatus,
    Student,
    StudentSkill,
    TutorSession,
    User,
)
from app.parent_models import ParentProfile, ParentStudentRelationship
from app.services.parent_dashboard import dashboard


def _persist_scope_fixture(db: Session) -> tuple[ParentProfile, Student, Skill, Skill]:
    suffix = uuid.uuid4().hex[:8]
    parent_user = User(
        email=f"parent-f009-{suffix}@example.test",
        display_name="F009 Isolation Parent",
        role="PARENT",
    )
    in_scope_curriculum = Curriculum(
        code=f"F009_SCOPE_A_{suffix}",
        name="F009 Scope A",
        jurisdiction="Scope A",
        grade_level="8",
        version="1",
    )
    other_curriculum = Curriculum(
        code=f"F009_SCOPE_B_{suffix}",
        name="F009 Scope B",
        jurisdiction="Scope B",
        grade_level="9",
        version="1",
    )
    db.add_all([parent_user, in_scope_curriculum, other_curriculum])
    db.flush()

    student = Student(
        curriculum_id=in_scope_curriculum.id,
        first_name="Scoped Learner",
        grade_level="8",
        school_system="Pilot",
    )
    in_scope_skill = Skill(
        curriculum_id=in_scope_curriculum.id,
        code=f"F009.A.1.{suffix}",
        name="In-scope skill",
        difficulty_level=1,
    )
    other_skill = Skill(
        curriculum_id=other_curriculum.id,
        code=f"F009.B.1.{suffix}",
        name="Cross-curriculum skill that must not leak",
        difficulty_level=1,
    )
    db.add_all([student, in_scope_skill, other_skill])
    db.flush()

    parent = ParentProfile(user_id=parent_user.id)
    db.add(parent)
    db.flush()
    db.add(
        ParentStudentRelationship(
            parent_profile_id=parent.id,
            student_id=student.id,
            relationship_type="GUARDIAN",
            active=True,
        )
    )
    db.add_all(
        [
            StudentSkill(
                student_id=student.id,
                skill_id=in_scope_skill.id,
                attempt_count=2,
                independent_attempt_count=2,
                independent_correct_count=1,
                status=SkillStatus.PRACTICING,
            ),
            StudentSkill(
                student_id=student.id,
                skill_id=other_skill.id,
                attempt_count=99,
                independent_attempt_count=99,
                independent_correct_count=99,
                hinted_correct_count=99,
                status=SkillStatus.MASTERED,
            ),
        ]
    )
    db.commit()
    db.refresh(parent)
    db.refresh(student)
    db.refresh(in_scope_skill)
    db.refresh(other_skill)
    return parent, student, in_scope_skill, other_skill


def test_parent_dashboard_excludes_cross_curriculum_learning_evidence() -> None:
    with SessionLocal() as db:
        parent, student, in_scope_skill, other_skill = _persist_scope_fixture(db)

        result = dashboard(db, parent=parent, student_id=student.id)

        visible_skill_ids = {row.skill_id for row in result.skills}
        assert in_scope_skill.id in visible_skill_ids
        assert other_skill.id not in visible_skill_ids
        assert all(row.skill_name != other_skill.name for row in result.skills)

        projected = next(row for row in result.skills if row.skill_id == in_scope_skill.id)
        assert projected.learning_state == "INDEPENDENT_PROGRESS"
        assert projected.independent_correct_count == 1


def test_parent_dashboard_reports_learning_trends() -> None:
    with SessionLocal() as db:
        parent, student, skill, _ = _persist_scope_fixture(db)
        now = datetime.now(UTC)

        today_session = TutorSession(
            student_id=student.id,
            primary_skill_id=skill.id,
            active_skill_id=skill.id,
            curriculum_id=skill.curriculum_id,
            started_at=now - timedelta(minutes=20),
            ended_at=now,
        )
        prev_session = TutorSession(
            student_id=student.id,
            primary_skill_id=skill.id,
            active_skill_id=skill.id,
            curriculum_id=skill.curriculum_id,
            started_at=now - timedelta(days=8, minutes=40),
            ended_at=now - timedelta(days=8),
        )
        problem = Problem(
            primary_skill_id=skill.id,
            problem_type="SOLVE_EQUATION",
            difficulty=3,
            prompt=f"trend-test {uuid.uuid4()}",
            canonical_answer="x=1",
            source_type="TEST",
        )
        db.add_all([today_session, prev_session, problem])
        db.flush()
        db.add(
            Attempt(
                session_id=today_session.id,
                student_id=student.id,
                problem_id=problem.id,
                student_answer="x=1",
                is_correct=True,
                assistance_level=0,
            )
        )
        db.add_all(
            [
                MasteryEvent(
                    student_id=student.id,
                    skill_id=skill.id,
                    previous_score=0.4,
                    new_score=0.5,
                    previous_confidence=0.3,
                    new_confidence=0.4,
                    reason="ATTEMPT",
                    created_at=now - timedelta(days=8),
                ),
                MasteryEvent(
                    student_id=student.id,
                    skill_id=skill.id,
                    previous_score=0.5,
                    new_score=0.7,
                    previous_confidence=0.4,
                    new_confidence=0.6,
                    reason="ATTEMPT",
                ),
                LearnerAward(
                    student_id=student.id,
                    badge_code="SKILL_MASTERED",
                    skill_id=skill.id,
                    session_id=today_session.id,
                ),
            ]
        )
        db.commit()

        result = dashboard(db, parent=parent, student_id=student.id)

        metrics = result.daily_metrics
        assert len(metrics) == 14
        by_date = {m.date: m for m in metrics}
        today_key = now.date().isoformat()
        # Minutes are attributed to the session's start day.
        session_start_key = (now - timedelta(minutes=20)).date().isoformat()
        prev_session_key = (now - timedelta(days=8, minutes=40)).date().isoformat()
        prev_key = (now - timedelta(days=8)).date().isoformat()
        assert by_date[session_start_key].minutes == 20
        assert by_date[prev_session_key].minutes == 40
        # Mastery line carries the last recorded score forward.
        assert by_date[today_key].mastery_score == 70.0
        assert by_date[prev_key].mastery_score == 50.0

        digest = result.weekly_digest
        assert digest is not None
        assert digest.sessions == 1
        assert digest.minutes == 20
        assert digest.prev_sessions == 1
        assert digest.prev_minutes == 40
        assert digest.minutes_delta == -20
        # 14 XP for the independent d=3 correct + 50 for SKILL_MASTERED.
        assert digest.xp_earned == 64
        assert digest.skills_mastered == 1
        assert digest.badges_earned == 1
        assert digest.mastery_delta == 20.0
        assert digest.days_since_practice == 0
        assert digest.stall is False
