from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import Curriculum, Skill, SkillStatus, Student, StudentSkill
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

        # Use only synthetic learner data. Mastery on the Maryland-local skill
        # must not create evidence on the equivalent Ontario-local skill.
        learner = Student(
            curriculum_id=grade7.id,
            first_name="Synthetic",
            grade_level="7",
            school_system="TEST",
        )
        db.add(learner)
        db.flush()
        db.add(
            StudentSkill(
                student_id=learner.id,
                skill_id=grade7_skill.id,
                mastery_score=Decimal("0.900"),
                confidence_score=Decimal("0.900"),
                attempt_count=5,
                correct_count=5,
                independent_attempt_count=5,
                independent_correct_count=5,
                status=SkillStatus.MASTERED,
            )
        )
        db.flush()

        grade7_evidence = db.get(StudentSkill, (learner.id, grade7_skill.id))
        ontario_evidence = db.get(StudentSkill, (learner.id, mth1w_skill.id))
        assert grade7_evidence is not None
        assert grade7_evidence.status == SkillStatus.MASTERED
        assert ontario_evidence is None

        # Reuse is metadata-only: learner evidence has no canonical-skill key.
        assert not hasattr(StudentSkill, "canonical_skill_id")
        assert not hasattr(CanonicalSkill, "student_id")
        assert not hasattr(CurriculumSkillMapping, "student_id")
    finally:
        db.rollback()
        db.close()


def test_ontario_mapping_is_broad_and_never_creates_canonical_learner_evidence():
    seed_mth1w()
    db = SessionLocal()
    try:
        map_existing_skills(db)
        db.commit()
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MTH1W", Curriculum.version == "2021")
        )
        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id)))
        mapped = list(
            db.scalars(
                select(CurriculumSkillMapping).where(
                    CurriculumSkillMapping.skill_id.in_([skill.id for skill in skills])
                )
            )
        )
        mapped_codes = {
            db.get(CanonicalSkill, mapping.canonical_skill_id).code for mapping in mapped
        }
        assert "MATH.EE.EXPR" in mapped_codes
        assert "MATH.EE.EQUATION.MULTISTEP" in mapped_codes
        assert "MATH.F.LINEAR.SLOPE_INTERCEPT" in mapped_codes
        assert "MATH.RP.PERCENT.APPLICATIONS" in mapped_codes
        assert not hasattr(CanonicalSkill, "mastery_score")
        assert not hasattr(CurriculumSkillMapping, "mastery_score")
    finally:
        db.close()
