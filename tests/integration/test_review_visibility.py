import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Curriculum,
    Skill,
    SkillReviewSchedule,
    SkillStatus,
    Student,
    StudentSkill,
    User,
)
from app.parent_models import ParentProfile, ParentStudentRelationship
from app.services.parent_dashboard import dashboard
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _persist_review_fixture(db: Session) -> tuple[ParentProfile, Student, Skill, Skill]:
    parent_user = User(
        email=f"parent-review-visibility-{uuid.uuid4().hex[:8]}@example.test",
        display_name="Review Visibility Parent",
        role="PARENT",
    )
    curriculum = Curriculum(
        code=f"REVIEW_SCOPE_{uuid.uuid4().hex[:8]}",
        name="Review Scope Curriculum",
        jurisdiction="Scope",
        grade_level="8",
        version="1",
    )
    db.add_all([parent_user, curriculum])
    db.flush()

    student = Student(
        curriculum_id=curriculum.id,
        first_name="Review Visibility Learner",
        grade_level="8",
        school_system="Pilot",
    )
    due_skill = Skill(
        curriculum_id=curriculum.id,
        code=f"RV.DUE.{uuid.uuid4().hex[:6]}",
        name="Due for review skill",
        difficulty_level=1,
    )
    relearning_skill = Skill(
        curriculum_id=curriculum.id,
        code=f"RV.RELEARN.{uuid.uuid4().hex[:6]}",
        name="Relearning skill",
        difficulty_level=1,
    )
    db.add_all([student, due_skill, relearning_skill])
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

    now = datetime.now(UTC)
    db.add_all(
        [
            StudentSkill(
                student_id=student.id,
                skill_id=due_skill.id,
                mastery_score=Decimal("0.900"),
                confidence_score=Decimal("0.500"),
                status=SkillStatus.MASTERED,
                last_independent_evidence_at=now - timedelta(days=30),
            ),
            StudentSkill(
                student_id=student.id,
                skill_id=relearning_skill.id,
                mastery_score=Decimal("0.600"),
                confidence_score=Decimal("0.400"),
                status=SkillStatus.PRACTICING,
                last_independent_evidence_at=now - timedelta(days=5),
            ),
            SkillReviewSchedule(
                student_id=student.id,
                skill_id=due_skill.id,
                interval_index=0,
                due_at=now - timedelta(hours=2),
                status="SCHEDULED",
            ),
            SkillReviewSchedule(
                student_id=student.id,
                skill_id=relearning_skill.id,
                interval_index=2,
                due_at=now + timedelta(days=7),
                status="RELEARNING",
                last_outcome="REVIEW_FAILED",
            ),
        ]
    )
    db.commit()
    db.refresh(parent)
    db.refresh(student)
    return parent, student, due_skill, relearning_skill


def test_dashboard_surfaces_due_and_relearning_reviews() -> None:
    with SessionLocal() as db:
        parent, student, due_skill, relearning_skill = _persist_review_fixture(db)

        result = dashboard(db, parent=parent, student_id=student.id)

        reviews = {row.skill_id: row for row in result.reviews_due}
        assert set(reviews) == {due_skill.id, relearning_skill.id}

        due = reviews[due_skill.id]
        assert due.status == "Due"
        assert due.skill_name == due_skill.name
        assert due.mastery_score == 0.9
        assert due.projected_mastery_score < due.mastery_score
        assert due.interval_index == 0

        relearning = reviews[relearning_skill.id]
        assert relearning.status == "Relearning"
        assert relearning.interval_index == 2

        # Visibility is read-only: no decay or demotion is persisted.
        db.expire_all()
        progress = db.get(
            StudentSkill, {"student_id": student.id, "skill_id": due_skill.id}
        )
        assert progress is not None
        assert progress.status == SkillStatus.MASTERED
        assert float(progress.mastery_score) == 0.9
        schedule = db.get(
            SkillReviewSchedule,
            {"student_id": student.id, "skill_id": due_skill.id},
        )
        assert schedule is not None
        assert schedule.status == "SCHEDULED"


def test_dashboard_omits_healthy_schedules_and_cross_curriculum_reviews() -> None:
    with SessionLocal() as db:
        parent, student, due_skill, _ = _persist_review_fixture(db)
        other_curriculum = Curriculum(
            code=f"OTHER_{uuid.uuid4().hex[:8]}",
            name="Other Curriculum",
            jurisdiction="Other",
            grade_level="9",
            version="1",
        )
        db.add(other_curriculum)
        db.flush()
        other_skill = Skill(
            curriculum_id=other_curriculum.id,
            code=f"RV.OTHER.{uuid.uuid4().hex[:6]}",
            name="Cross-curriculum review must not leak",
            difficulty_level=1,
        )
        healthy_skill = Skill(
            curriculum_id=db.get(Skill, due_skill.id).curriculum_id,
            code=f"RV.OK.{uuid.uuid4().hex[:6]}",
            name="Not-yet-due skill",
            difficulty_level=1,
        )
        db.add_all([other_skill, healthy_skill])
        db.flush()
        now = datetime.now(UTC)
        db.add_all(
            [
                StudentSkill(
                    student_id=student.id,
                    skill_id=other_skill.id,
                    mastery_score=Decimal("0.900"),
                    status=SkillStatus.MASTERED,
                ),
                StudentSkill(
                    student_id=student.id,
                    skill_id=healthy_skill.id,
                    mastery_score=Decimal("0.950"),
                    status=SkillStatus.MASTERED,
                ),
                SkillReviewSchedule(
                    student_id=student.id,
                    skill_id=other_skill.id,
                    due_at=now - timedelta(hours=5),
                    status="SCHEDULED",
                ),
                SkillReviewSchedule(
                    student_id=student.id,
                    skill_id=healthy_skill.id,
                    due_at=now + timedelta(days=10),
                    status="SCHEDULED",
                ),
            ]
        )
        db.commit()

        result = dashboard(db, parent=parent, student_id=student.id)
        visible_ids = {row.skill_id for row in result.reviews_due}
        assert due_skill.id in visible_ids
        assert other_skill.id not in visible_ids
        assert healthy_skill.id not in visible_ids


def test_workspace_surfaces_reviews_due() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_MATH_8")
        )
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None and skill is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Workspace Review Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)

        now = datetime.now(UTC)
        db.add_all(
            [
                StudentSkill(
                    student_id=student.id,
                    skill_id=skill.id,
                    mastery_score=Decimal("0.900"),
                    status=SkillStatus.MASTERED,
                    last_independent_evidence_at=now - timedelta(days=20),
                ),
                SkillReviewSchedule(
                    student_id=student.id,
                    skill_id=skill.id,
                    due_at=now - timedelta(hours=1),
                    status="SCHEDULED",
                ),
            ]
        )
        db.commit()
        student_id, skill_id = student.id, skill.id

    session = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert session.status_code == 200
    session_id = session.json()["session_id"]

    workspace = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")
    assert workspace.status_code == 200
    reviews = workspace.json()["reviews_due"]
    assert any(row["skill_id"] == str(skill_id) for row in reviews)
    assert all(row["skill_name"] and row["due_at"] for row in reviews)
