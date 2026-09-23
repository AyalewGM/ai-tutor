from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CurriculumSkillMapping, EducationAuthority
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_md_algebra1 import CURRICULUM_CODE, LEGACY_CODE, MSDE_SOURCE, seed


def test_md_algebra1_seed_upgrades_pilot_idempotently_with_isolation():
    seed()
    seed()

    db = SessionLocal()
    try:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        assert curriculum is not None
        assert db.scalar(select(Curriculum).where(Curriculum.code == LEGACY_CODE)) is None
        assert curriculum.jurisdiction == "Maryland"
        assert curriculum.grade_level == "Algebra I"
        assert curriculum.version == "MCCRS-revised-SY2026-27"
        assert curriculum.source_uri == MSDE_SOURCE

        authority = db.get(EducationAuthority, curriculum.authority_id)
        assert authority is not None
        assert authority.code == "MSDE"

        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id)))
        assert len(skills) == 9
        skill_ids = {skill.id for skill in skills}
        mappings = list(
            db.scalars(select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id.in_(skill_ids)))
        )
        assert len(mappings) == len(skills)
        assert all(mapping.provenance_json["standards_authority"] == "Maryland State Department of Education" for mapping in mappings)

        edges = list(db.scalars(select(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(skill_ids))))
        assert len(edges) == 8
        assert all(edge.prerequisite_skill_id in skill_ids for edge in edges)

        problems = list(db.scalars(select(Problem).where(Problem.primary_skill_id.in_(skill_ids))))
        assert len(problems) == 21
        assert all(problem.solution["provenance"]["origin"] == "AUTHORED" for problem in problems)
        assert all(problem.solution["provenance"]["author"] == "AI Tutor curriculum team" for problem in problems)
        assert all(problem.solution["provenance"]["standards_source"] == MSDE_SOURCE for problem in problems)

        for other_code in ("MCPS_MATH_7", "MCPS_MATH_8", "MTH1W", "DC_MATH_7", "VA_MATH_7"):
            other = db.scalar(select(Curriculum).where(Curriculum.code == other_code))
            if other is not None:
                other_ids = set(db.scalars(select(Skill.id).where(Skill.curriculum_id == other.id)))
                assert skill_ids.isdisjoint(other_ids)
    finally:
        db.close()
