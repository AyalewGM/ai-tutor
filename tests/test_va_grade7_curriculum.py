from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CurriculumSkillMapping
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_va_grade7 import CURRICULUM_CODE, VDOE_SOURCE, seed


def test_va_grade7_seed_is_idempotent_and_isolated():
    seed()
    seed()
    db = SessionLocal()
    try:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        assert curriculum is not None
        assert curriculum.jurisdiction == "Virginia"
        assert curriculum.grade_level == "7"
        assert curriculum.version == "SOL-2023-v1"
        assert curriculum.source_uri == VDOE_SOURCE

        skills = db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id)).all()
        assert len(skills) == 5
        skill_ids = {skill.id for skill in skills}
        mappings = db.scalars(select(CurriculumSkillMapping).where(
            CurriculumSkillMapping.skill_id.in_(skill_ids))).all()
        assert len(mappings) == 5
        assert all(mapping.provenance_json["standards_authority"] == "Virginia Department of Education"
                   for mapping in mappings)

        problems = db.scalars(select(Problem).where(Problem.primary_skill_id.in_(skill_ids))).all()
        assert len(problems) == 10
        assert all(problem.solution["provenance"]["origin"] == "AUTHORED" for problem in problems)
        assert all(problem.solution["provenance"]["standards_source"] == VDOE_SOURCE for problem in problems)

        edges = db.scalars(select(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(skill_ids))).all()
        assert edges
        assert all(edge.prerequisite_skill_id in skill_ids for edge in edges)

        other = db.scalars(select(Skill).where(Skill.curriculum_id != curriculum.id)).all()
        assert skill_ids.isdisjoint({skill.id for skill in other})
    finally:
        db.close()


def test_va_grade7_reuses_canonical_identity_without_cross_curriculum_mastery():
    seed()
    db = SessionLocal()
    try:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        va_skill = db.scalar(select(Skill).where(
            Skill.curriculum_id == curriculum.id, Skill.code == "VA7.PFA.EQUATION"))
        va_mapping = db.scalar(select(CurriculumSkillMapping).where(
            CurriculumSkillMapping.skill_id == va_skill.id))
        peer_mappings = db.scalars(select(CurriculumSkillMapping).where(
            CurriculumSkillMapping.canonical_skill_id == va_mapping.canonical_skill_id,
            CurriculumSkillMapping.skill_id != va_skill.id)).all()
        assert peer_mappings
        assert all(mapping.skill_id != va_skill.id for mapping in peer_mappings)
    finally:
        db.close()
