from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Misconception, Problem, Skill
from scripts.seed_grade8 import CURRICULUM_CODE, seed


def test_grade8_seed_is_idempotent_and_curriculum_local():
    seed()
    seed()

    db = SessionLocal()
    try:
        grade8 = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        assert grade8 is not None
        assert grade8.grade_level == "8"

        skills = {
            skill.code: skill
            for skill in db.scalars(
                select(Skill).where(Skill.curriculum_id == grade8.id)
            )
        }
        assert "M8.G.TRANS" in skills
        assert "M8.G.SIM" in skills

        problems = list(
            db.scalars(
                select(Problem).where(
                    Problem.primary_skill_id.in_(
                        {skills["M8.G.TRANS"].id, skills["M8.G.SIM"].id}
                    )
                )
            )
        )
        assert len(problems) == 8

        misconceptions = list(
            db.scalars(
                select(Misconception).where(
                    Misconception.skill_id.in_(
                        {skills["M8.G.TRANS"].id, skills["M8.G.SIM"].id}
                    )
                )
            )
        )
        assert {m.code for m in misconceptions} == {
            "TR_001", "TR_002", "TR_003", "TR_004", "TR_005",
            "SIM_001", "SIM_002", "SIM_003", "SIM_004",
        }
    finally:
        db.close()
