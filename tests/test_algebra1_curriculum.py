from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_algebra1 import CURRICULUM_CODE, seed


def test_algebra1_seed_is_idempotent_versioned_and_curriculum_local():
    seed()
    seed()

    db = SessionLocal()
    try:
        algebra1 = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        grade8 = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        ontario = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))

        assert algebra1 is not None
        assert algebra1.grade_level == "Algebra 1"
        assert algebra1.version == "SY2026-27"
        assert grade8 is not None
        assert algebra1.id != grade8.id
        if ontario is not None:
            assert algebra1.id != ontario.id

        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == algebra1.id)))
        assert {skill.code for skill in skills} == {
            "A1.EXPR",
            "A1.LINEAR.EQ",
            "A1.LINEAR.FN",
        }
        skill_ids = {skill.id for skill in skills}

        edges = list(
            db.scalars(
                select(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(skill_ids))
            )
        )
        assert len(edges) == 2
        assert all(edge.prerequisite_skill_id in skill_ids for edge in edges)

        problems = list(
            db.scalars(select(Problem).where(Problem.primary_skill_id.in_(skill_ids)))
        )
        assert len(problems) == 8
        assert all(problem.primary_skill_id in skill_ids for problem in problems)

        grade8_skill_ids = set(
            db.scalars(select(Skill.id).where(Skill.curriculum_id == grade8.id))
        )
        assert skill_ids.isdisjoint(grade8_skill_ids)

        if ontario is not None:
            ontario_skill_ids = set(
                db.scalars(select(Skill.id).where(Skill.curriculum_id == ontario.id))
            )
            assert skill_ids.isdisjoint(ontario_skill_ids)
    finally:
        db.close()
