from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_grade7 import CURRICULUM_CODE, seed


def test_grade7_seed_is_idempotent_and_curriculum_local():
    seed()
    seed()

    db = SessionLocal()
    try:
        grade7 = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        grade8 = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        assert grade7 is not None
        assert grade7.grade_level == "7"
        assert grade7.version == "1"
        assert grade8 is not None
        assert grade7.id != grade8.id

        grade7_skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == grade7.id)))
        assert {skill.code for skill in grade7_skills} == {
            "M7.RP.PROP",
            "M7.RP.PERCENT",
            "M7.EE.EXPR",
            "M7.EE.EQUATION",
            "M7.RP.PROP.RATE",
            "M7.RP.PERCENT.OF",
            "M7.EE.EXPR.DIST",
            "M7.EE.EXPR.COMBINE",
            "M7.EE.EQUATION.ONE",
            "M7.EE.EQUATION.TWO",
        }
        skill_ids = {skill.id for skill in grade7_skills}

        edges = list(
            db.scalars(
                select(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(skill_ids))
            )
        )
        assert len(edges) == 8
        assert all(edge.prerequisite_skill_id in skill_ids for edge in edges)

        problems = list(db.scalars(select(Problem).where(Problem.primary_skill_id.in_(skill_ids))))
        assert len(problems) == 21
        assert all(problem.primary_skill_id in skill_ids for problem in problems)

        grade8_skill_ids = set(
            db.scalars(select(Skill.id).where(Skill.curriculum_id == grade8.id))
        )
        assert skill_ids.isdisjoint(grade8_skill_ids)
    finally:
        db.close()
