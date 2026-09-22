from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import Curriculum, Skill, StudentSkill
from scripts.map_canonical_curricula import map_existing_skills
from scripts.seed_grade7 import seed as seed_grade7
from scripts.seed_mth1w import seed as seed_mth1w


def test_two_curricula_share_math_identity_without_sharing_evidence():
    seed_grade7()
    seed_mth1w()
    db = SessionLocal()
    try:
        map_existing_skills(db)
        map_existing_skills(db)
        db.commit()

        grade7 = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_7"))
        mth1w = db.scalar(
            select(Curriculum).where(
                Curriculum.code == "MTH1W", Curriculum.version == "2021"
            )
        )
        grade7_skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == grade7.id,
                Skill.code == "M7.EE.EXPR",
            )
        )
        mth1w_skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == mth1w.id,
                Skill.code == "MTH1W.C.ALG.EXPR",
            )
        )
        grade7_mapping = db.scalar(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.skill_id == grade7_skill.id
            )
        )
        mth1w_mapping = db.scalar(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.skill_id == mth1w_skill.id
            )
        )
        assert grade7_mapping.canonical_skill_id == mth1w_mapping.canonical_skill_id
        canonical = db.get(CanonicalSkill, grade7_mapping.canonical_skill_id)
        assert canonical.code == "MATH.EE.EXPR"
        assert grade7_skill.id != mth1w_skill.id

        # Reuse is metadata-only: learner evidence has no canonical-skill key
        # and therefore cannot silently transfer across curriculum versions.
        assert not hasattr(StudentSkill, "canonical_skill_id")
        assert not hasattr(CanonicalSkill, "student_id")
        assert not hasattr(CurriculumSkillMapping, "student_id")
    finally:
        db.close()
