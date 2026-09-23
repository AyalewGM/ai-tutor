from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CurriculumSkillMapping, EducationAuthority
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_dc_grade7 import CURRICULUM_CODE, OSSE_SOURCE, seed


def test_dc_grade7_seed_is_idempotent_provenanced_and_isolated():
    seed()
    seed()
    db = SessionLocal()
    try:
        grade7 = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        assert grade7 is not None
        assert grade7.grade_level == "7"
        assert grade7.source_uri == OSSE_SOURCE
        authority = db.get(EducationAuthority, grade7.authority_id)
        assert authority is not None
        assert authority.code == "OSSE"
        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == grade7.id)))
        assert {s.code for s in skills} == {
            "DC7.RP.PROPORTIONAL", "DC7.RP.PERCENT", "DC7.NS.RATIONAL",
            "DC7.EE.EQUATION", "DC7.SP.PROBABILITY"
        }
        ids = {s.id for s in skills}
        problems = list(db.scalars(select(Problem).where(Problem.primary_skill_id.in_(ids))))
        assert len(problems) == 10
        assert all(p.solution["provenance"]["origin"] == "AUTHORED" for p in problems)
        edges = list(db.scalars(select(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(ids))))
        assert len(edges) == 2
        assert all(e.prerequisite_skill_id in ids for e in edges)
        mappings = list(db.scalars(select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id.in_(ids))))
        assert len(mappings) == len(skills)
        for other_code in ("DC_MATH_6", "MCPS_MATH_6", "MCPS_MATH_7", "MCPS_MATH_8", "ON_MTH1W_2021", "VA_MATH_6"):
            other = db.scalar(select(Curriculum).where(Curriculum.code == other_code))
            if other is not None:
                other_ids = set(db.scalars(select(Skill.id).where(Skill.curriculum_id == other.id)))
                assert ids.isdisjoint(other_ids)
    finally:
        db.close()
