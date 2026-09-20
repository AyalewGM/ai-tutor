from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_sprint1 import seed


def test_grade8_fine_grained_subskills_and_chains():
    seed()

    db = SessionLocal()
    try:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_MATH_8")
        )
        skills = {
            skill.code: skill
            for skill in db.scalars(
                select(Skill).where(Skill.curriculum_id == curriculum.id)
            )
        }
        subskills = {
            "M8.ALG.INVERSE.ADD",
            "M8.ALG.INVERSE.MULT",
            "M8.ALG.DIST.POS",
            "M8.ALG.DIST.NEG",
            "M8.ALG.MULTI_STEP.COMBINE",
        }
        assert subskills <= skills.keys()

        edges = set(
            db.execute(
                select(
                    SkillPrerequisite.skill_id,
                    SkillPrerequisite.prerequisite_skill_id,
                )
            ).all()
        )

        def edge(child: str, parent: str) -> bool:
            return (skills[child].id, skills[parent].id) in edges

        assert edge("M8.ALG.INVERSE.ADD", "M8.ALG.INVERSE")
        assert edge("M8.ALG.INVERSE.MULT", "M8.ALG.INVERSE.ADD")
        assert edge("M8.ALG.DIST.POS", "M8.ALG.DIST")
        assert edge("M8.ALG.DIST.NEG", "M8.ALG.DIST.POS")
        assert edge("M8.ALG.MULTI_STEP.COMBINE", "M8.ALG.MULTI_STEP")

        for code in subskills:
            types = {
                row[0]
                for row in db.execute(
                    select(Problem.problem_type).where(
                        Problem.primary_skill_id == skills[code].id
                    )
                )
            }
            assert types, code
    finally:
        db.close()
