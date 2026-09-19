import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.curriculum_models import StudentCurriculumEnrollment
from app.learner_deletion import erase_learner_transactional
from app.models import Curriculum, Skill, Student, StudentSkill, User
from app.parent_models import ChildLinkClaim, ParentProfile, ParentStudentRelationship


def test_postgres_learner_erase_isolated_and_preserves_shared_curriculum():
    """Exercise the deletion service against the migrated PostgreSQL schema.

    Uses only synthetic identities. A sibling in the same curriculum proves the
    erase is learner-scoped; shared curriculum/skill rows must survive.
    """
    db = SessionLocal()
    marker = uuid.uuid4().hex[:10]
    try:
        curriculum = db.scalar(select(Curriculum).limit(1))
        assert curriculum is not None
        skill = db.scalar(select(Skill).where(Skill.curriculum_id == curriculum.id).limit(1))
        assert skill is not None

        user = User(email=f"privacy-{marker}@example.invalid", role="PARENT")
        db.add(user)
        db.flush()
        parent = ParentProfile(user_id=user.id)
        db.add(parent)
        db.flush()

        target = Student(
            parent_id=user.id,
            curriculum_id=curriculum.id,
            first_name="SyntheticTarget",
            grade_level="8",
            school_system="SYNTHETIC",
        )
        sibling = Student(
            parent_id=user.id,
            curriculum_id=curriculum.id,
            first_name="SyntheticSibling",
            grade_level="8",
            school_system="SYNTHETIC",
        )
        db.add_all([target, sibling])
        db.flush()
        db.add_all(
            [
                ParentStudentRelationship(parent_profile_id=parent.id, student_id=target.id),
                ParentStudentRelationship(parent_profile_id=parent.id, student_id=sibling.id),
                StudentCurriculumEnrollment(student_id=target.id, curriculum_id=curriculum.id),
                StudentCurriculumEnrollment(student_id=sibling.id, curriculum_id=curriculum.id),
                StudentSkill(student_id=target.id, skill_id=skill.id),
                StudentSkill(student_id=sibling.id, skill_id=skill.id),
                ChildLinkClaim(
                    student_id=target.id,
                    token_hash=uuid.uuid4().hex + uuid.uuid4().hex,
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                ),
            ]
        )
        db.commit()

        target_id = target.id
        sibling_id = sibling.id
        curriculum_id = curriculum.id
        skill_id = skill.id

        erase_learner_transactional(db, parent=parent, learner_id=target_id)
        db.commit()

        assert db.get(Student, target_id) is None
        assert db.get(Student, sibling_id) is not None
        assert db.get(Curriculum, curriculum_id) is not None
        assert db.get(Skill, skill_id) is not None
        assert db.scalar(
            select(func.count(StudentCurriculumEnrollment.id)).where(
                StudentCurriculumEnrollment.student_id == target_id
            )
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(StudentSkill).where(StudentSkill.student_id == target_id)
        ) == 0
        assert db.scalar(
            select(func.count()).select_from(StudentSkill).where(StudentSkill.student_id == sibling_id)
        ) == 1
        assert db.scalar(
            select(func.count(ChildLinkClaim.id)).where(ChildLinkClaim.student_id == target_id)
        ) == 0
    finally:
        db.rollback()
        # The target is gone, but remove the synthetic sibling/family fixture.
        try:
            sibling_row = db.scalar(select(Student).where(Student.first_name == "SyntheticSibling", Student.parent_id == user.id))
            if sibling_row is not None:
                sibling_rel = db.scalar(
                    select(ParentStudentRelationship).where(
                        ParentStudentRelationship.parent_profile_id == parent.id,
                        ParentStudentRelationship.student_id == sibling_row.id,
                    )
                )
                if sibling_rel is not None:
                    erase_learner_transactional(db, parent=parent, learner_id=sibling_row.id)
            db.delete(parent)
            db.delete(user)
            db.commit()
        finally:
            db.close()
