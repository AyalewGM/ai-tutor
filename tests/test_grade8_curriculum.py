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
        assert "M8.SP.STAT" in skills
        assert "M8.G.PYTH" in skills
        assert "M8.NS.RAD" in skills
        assert "M8.F.FN" in skills

        skill_ids = {
            skills[code].id
            for code in (
                "M8.G.TRANS", "M8.G.SIM", "M8.SP.STAT", "M8.G.PYTH", "M8.NS.RAD",
                "M8.F.FN",
            )
        }
        problems = list(
            db.scalars(
                select(Problem).where(Problem.primary_skill_id.in_(skill_ids))
            )
        )
        assert len(problems) == 27

        misconceptions = list(
            db.scalars(
                select(Misconception).where(Misconception.skill_id.in_(skill_ids))
            )
        )
        assert {m.code for m in misconceptions} == {
            "TR_001", "TR_002", "TR_003", "TR_004", "TR_005",
            "SIM_001", "SIM_002", "SIM_003", "SIM_004",
            "STAT_001", "STAT_002", "STAT_003", "STAT_004", "STAT_005",
            "STAT_006", "STAT_007", "STAT_008",
            "PYTH_001", "PYTH_002", "PYTH_003",
            "RAD_001", "RAD_002", "RAD_003", "RAD_004",
            "FUNC_001", "FUNC_002", "FUNC_003", "FUNC_004",
        }
    finally:
        db.close()
