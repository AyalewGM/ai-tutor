from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Curriculum, Skill, SkillStatus, Student, StudentSkill, User
from app.parent_models import ParentProfile, ParentStudentRelationship
from app.services.parent_dashboard import dashboard


def _persist_scope_fixture(db: Session) -> tuple[ParentProfile, Student, Skill, Skill]:
    parent_user = User(
        email="parent-f009-isolation@example.test",
        display_name="F009 Isolation Parent",
        role="PARENT",
    )
    in_scope_curriculum = Curriculum(
        code="F009_SCOPE_A",
        name="F009 Scope A",
        jurisdiction="Scope A",
        grade_level="8",
        version="1",
    )
    other_curriculum = Curriculum(
        code="F009_SCOPE_B",
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
        code="F009.A.1",
        name="In-scope skill",
        difficulty_level=1,
    )
    other_skill = Skill(
        curriculum_id=other_curriculum.id,
        code="F009.B.1",
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
