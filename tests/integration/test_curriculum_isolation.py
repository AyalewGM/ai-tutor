import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority, StudentCurriculumEnrollment
from app.main import app
from app.models import Curriculum, Skill, SkillPrerequisite, Student
from app.services.curriculum_scope import CurriculumScopeError
from app.services.prerequisite_readiness import find_unready_prerequisite

client = TestClient(app)


def test_ontario_mth1w_is_owned_by_ministry_not_ocdsb() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(
                Curriculum.code == "MTH1W",
                Curriculum.version == "2021",
            )
        )
        assert curriculum is not None
        authority = db.get(EducationAuthority, curriculum.authority_id)
        assert authority is not None
        assert authority.code == "ON_MIN_ED"
        assert authority.name == "Ontario Ministry of Education"

        ocdsb = db.scalar(
            select(EducationAuthority).where(EducationAuthority.code == "OCDSB")
        )
        assert ocdsb is not None
        assert curriculum.authority_id != ocdsb.id


def test_same_skill_code_can_exist_in_separate_curricula() -> None:
    with SessionLocal() as db:
        mcps = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        mth1w = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        existing = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == mcps.id,
                Skill.code == "M8.ALG.DIST",
            )
        )
        assert mcps is not None
        assert mth1w is not None
        assert existing is not None

        duplicate_code_other_curriculum = Skill(
            curriculum_id=mth1w.id,
            code=existing.code,
            name="Different Curriculum Concept",
            description="Test-only duplicate code under another curriculum.",
            difficulty_level=1,
        )
        db.add(duplicate_code_other_curriculum)
        db.flush()
        assert duplicate_code_other_curriculum.id is not None
        db.rollback()


def test_adaptive_session_rejects_skill_from_another_curriculum() -> None:
    with SessionLocal() as db:
        mcps = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        mth1w = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        mcps_authority = db.get(EducationAuthority, mcps.authority_id)
        assert mcps is not None
        assert mth1w is not None
        assert mcps_authority is not None

        student = Student(
            curriculum_id=mcps.id,
            first_name="Isolation Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        enrollment = StudentCurriculumEnrollment(
            student_id=student.id,
            curriculum_id=mcps.id,
            local_authority_id=mcps_authority.id,
            active=True,
            source_uri="test",
        )
        foreign_skill = Skill(
            curriculum_id=mth1w.id,
            code="TEST.MTH1W.FOREIGN",
            name="Foreign Skill",
            description="Must not be accessible from MCPS enrollment.",
            difficulty_level=1,
        )
        db.add_all([enrollment, foreign_skill])
        db.commit()
        student_id = student.id
        foreign_skill_id = foreign_skill.id

    response = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(foreign_skill_id)},
    )
    assert response.status_code == 409
    assert "active curriculum" in response.json()["detail"]


def test_prerequisite_graph_fails_closed_on_cross_curriculum_edge() -> None:
    with SessionLocal() as db:
        mcps = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        mth1w = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        target = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == mcps.id,
                Skill.code == "M8.ALG.MULTI_STEP",
            )
        )
        assert mcps is not None
        assert mth1w is not None
        assert target is not None

        foreign_prerequisite = Skill(
            curriculum_id=mth1w.id,
            code="TEST.MTH1W.PREREQ",
            name="Foreign prerequisite",
            description="Test-only cross-curriculum prerequisite.",
            difficulty_level=1,
        )
        student = Student(
            curriculum_id=mcps.id,
            first_name="Graph Isolation Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add_all([foreign_prerequisite, student])
        db.flush()
        edge = SkillPrerequisite(
            skill_id=target.id,
            prerequisite_skill_id=foreign_prerequisite.id,
        )
        db.add(edge)
        db.flush()

        with pytest.raises(CurriculumScopeError, match="crosses curriculum boundaries"):
            find_unready_prerequisite(
                db,
                student_id=student.id,
                target_skill_id=target.id,
            )
        db.rollback()
