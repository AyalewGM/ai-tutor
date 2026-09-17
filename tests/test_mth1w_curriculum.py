from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_mth1w import AUTHORITY_CODE, CURRICULUM_CODE, seed
from scripts.seed_sprint1 import seed as seed_sprint1


def _seed_curricula():
    """Seed both jurisdictions so isolation tests do not depend on CI/test order."""
    seed_sprint1()
    seed()


def test_mth1w_seed_is_idempotent_and_jurisdiction_local():
    _seed_curricula()
    seed()

    db = SessionLocal()
    try:
        authority = db.scalar(
            select(EducationAuthority).where(EducationAuthority.code == AUTHORITY_CODE)
        )
        ontario = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        grade8 = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))

        assert authority is not None
        assert authority.name == "Ontario Ministry of Education"
        assert ontario is not None
        assert ontario.version == "2021"
        assert ontario.grade_level == "9"
        assert ontario.authority_id == authority.id
        assert grade8 is not None
        assert ontario.id != grade8.id

        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == ontario.id)))
        assert {skill.code for skill in skills} == {
            "MTH1W.B.NUM",
            "MTH1W.C.ALG",
            "MTH1W.C.REL",
            "MTH1W.F.FIN",
        }
        skill_ids = {skill.id for skill in skills}

        edges = list(
            db.scalars(
                select(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(skill_ids))
            )
        )
        assert len(edges) == 3
        assert all(edge.prerequisite_skill_id in skill_ids for edge in edges)

        problems = list(db.scalars(select(Problem).where(Problem.primary_skill_id.in_(skill_ids))))
        assert len(problems) == 9
        assert all(problem.primary_skill_id in skill_ids for problem in problems)

        maryland_skill_ids = set(
            db.scalars(select(Skill.id).where(Skill.curriculum_id == grade8.id))
        )
        assert skill_ids.isdisjoint(maryland_skill_ids)
    finally:
        db.close()


def test_mth1w_prerequisite_guard_rejects_cross_curriculum_edge():
    _seed_curricula()
    db = SessionLocal()
    try:
        ontario = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        grade8 = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        ontario_skill = db.scalar(select(Skill).where(Skill.curriculum_id == ontario.id))
        maryland_skill = db.scalar(select(Skill).where(Skill.curriculum_id == grade8.id))

        from scripts.seed_mth1w import _prerequisite

        try:
            _prerequisite(db, ontario_skill, maryland_skill)
        except ValueError as exc:
            assert "cannot cross curriculum boundaries" in str(exc)
        else:
            raise AssertionError("Cross-curriculum prerequisite edge was not rejected")
    finally:
        db.rollback()
        db.close()
