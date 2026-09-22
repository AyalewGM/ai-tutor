from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CurriculumSkillMapping
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_grade6 import CURRICULUM_CODE, MSDE_SOURCE, seed


def test_grade6_seed_is_idempotent_provenanced_and_isolated():
    seed()
    seed()
    db = SessionLocal()
    try:
        grade6 = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        assert grade6 is not None
        assert grade6.grade_level == "6"
        assert grade6.source_uri == MSDE_SOURCE
        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == grade6.id)))
        assert {s.code for s in skills} == {"M6.RP.RATIO", "M6.RP.UNIT_RATE", "M6.NS.FRACTION", "M6.EE.EXPR", "M6.EE.EQUATION"}
        ids = {s.id for s in skills}
        assert len(list(db.scalars(select(Problem).where(Problem.primary_skill_id.in_(ids))))) == 10
        edges = list(db.scalars(select(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(ids))))
        assert len(edges) == 2
        assert all(e.prerequisite_skill_id in ids for e in edges)
        mappings = list(db.scalars(select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id.in_(ids))))
        assert len(mappings) == len(skills)
        for other_code in ("MCPS_MATH_7", "MCPS_MATH_8", "ON_MTH1W_2021"):
            other = db.scalar(select(Curriculum).where(Curriculum.code == other_code))
            if other is not None:
                other_ids = set(db.scalars(select(Skill.id).where(Skill.curriculum_id == other.id)))
                assert ids.isdisjoint(other_ids)
    finally:
        db.close()
