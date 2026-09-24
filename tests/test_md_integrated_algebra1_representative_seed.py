from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_md_integrated_algebra1 import CURRICULUM_CODE, MSDE_SOURCE, seed


def test_integrated_algebra1_representative_seed_is_idempotent_and_isolated():
    seed()
    seed()
    db = SessionLocal()
    try:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        assert curriculum is not None
        assert curriculum.grade_level == "Integrated Algebra I"
        assert curriculum.source_uri == MSDE_SOURCE
        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id)))
        expected_codes = {
            "IA1.AT.C.10",
            "IA1.GR.A.1",
            "IA1.DS.A.1",
            "IA1.AT.B.8",
            "IA1.AT.D.13",
            "IA1.AT.D.14",
            "IA1.AT.D.15",
            "IA1.AT.D.16",
            "IA1.AT.D.17",
            "IA1.DS.B.6",
        }
        assert {skill.code for skill in skills} == expected_codes
        skill_ids = {skill.id for skill in skills}
        mappings = list(db.scalars(select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id.in_(skill_ids))))
        assert len(mappings) == 10
        assert all(mapping.provenance_json["standards_source"] == MSDE_SOURCE for mapping in mappings)
        canonical_ids = {mapping.canonical_skill_id for mapping in mappings}
        canonical_codes = set(db.scalars(select(CanonicalSkill.code).where(CanonicalSkill.id.in_(canonical_ids))))
        assert canonical_codes == {f"MATH.{code}" for code in expected_codes}
        # Standards order is not prerequisite topology; no edge is introduced
        # until application-owned pedagogy review establishes a true dependency.
        edges = list(db.scalars(select(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(skill_ids))))
        assert edges == []
        problems = list(db.scalars(select(Problem).where(Problem.primary_skill_id.in_(skill_ids))))
        assert len(problems) == 10
        assert all(problem.solution["provenance"]["origin"] == "AUTHORED" for problem in problems)
        assert all(problem.solution["provenance"]["author"] == "AI Tutor curriculum team" for problem in problems)
        traditional = db.scalar(select(Curriculum).where(Curriculum.code == "MD_ALGEBRA_1_2026_27"))
        if traditional is not None:
            traditional_ids = set(db.scalars(select(Skill.id).where(Skill.curriculum_id == traditional.id)))
            assert skill_ids.isdisjoint(traditional_ids)
            traditional_canonical_ids = set(db.scalars(select(CurriculumSkillMapping.canonical_skill_id).where(CurriculumSkillMapping.skill_id.in_(traditional_ids))))
            assert canonical_ids.isdisjoint(traditional_canonical_ids)
    finally:
        db.close()
