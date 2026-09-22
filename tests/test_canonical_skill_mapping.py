from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import Curriculum, Skill, StudentSkill
from scripts.seed_grade7 import CURRICULUM_CODE, seed


def test_grade7_canonical_mappings_are_idempotent_and_local_evidence_stays_local():
    seed()
    seed()
    db = SessionLocal()
    try:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id)))
        mappings = list(
            db.scalars(
                select(CurriculumSkillMapping).where(
                    CurriculumSkillMapping.skill_id.in_([skill.id for skill in skills])
                )
            )
        )
        assert len(mappings) == len(skills)
        canonical_ids = {mapping.canonical_skill_id for mapping in mappings}
        canonical = list(
            db.scalars(select(CanonicalSkill).where(CanonicalSkill.id.in_(canonical_ids)))
        )
        assert len(canonical) == len(skills)
        assert all(item.code.startswith("MATH.") for item in canonical)

        # The reusable layer contains no learner/mastery foreign key. Evidence
        # remains attached to curriculum-local Skill rows.
        assert not hasattr(CanonicalSkill, "student_id")
        assert not hasattr(CurriculumSkillMapping, "student_id")
        assert StudentSkill.skill_id.property.columns[0].foreign_keys
    finally:
        db.close()
