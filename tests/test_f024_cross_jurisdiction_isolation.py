from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import Curriculum, Skill, SkillStatus, Student, StudentSkill
from scripts.seed_dc_grade3 import seed as seed_dc
from scripts.seed_md_grade3 import seed as seed_md


def test_md_and_dc_grade3_share_canonical_concepts_but_not_evidence():
    seed_md()
    seed_dc()
    with SessionLocal() as db:
        md_curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MD_MATH_3_2026_27")
        )
        dc_curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "DC_MATH_3_2024_25")
        )
        assert md_curriculum is not None
        assert dc_curriculum is not None
        assert md_curriculum.id != dc_curriculum.id
        assert md_curriculum.jurisdiction == "Maryland"
        assert dc_curriculum.jurisdiction == "District of Columbia"

        md_skills = list(
            db.scalars(
                select(Skill).where(Skill.curriculum_id == md_curriculum.id)
            )
        )
        dc_skills = list(
            db.scalars(
                select(Skill).where(Skill.curriculum_id == dc_curriculum.id)
            )
        )
        assert len(md_skills) == 4
        assert len(dc_skills) == 4
        md_skill_ids = {skill.id for skill in md_skills}
        dc_skill_ids = {skill.id for skill in dc_skills}
        assert md_skill_ids.isdisjoint(dc_skill_ids)

        md_mappings = list(
            db.scalars(
                select(CurriculumSkillMapping).where(
                    CurriculumSkillMapping.skill_id.in_(md_skill_ids)
                )
            )
        )
        dc_mappings = list(
            db.scalars(
                select(CurriculumSkillMapping).where(
                    CurriculumSkillMapping.skill_id.in_(dc_skill_ids)
                )
            )
        )
        assert len(md_mappings) == 4
        assert len(dc_mappings) == 4

        md_canonical_codes = {
            db.get(CanonicalSkill, mapping.canonical_skill_id).code
            for mapping in md_mappings
        }
        dc_canonical_codes = {
            db.get(CanonicalSkill, mapping.canonical_skill_id).code
            for mapping in dc_mappings
        }
        assert md_canonical_codes == dc_canonical_codes

        md_equal_groups = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == md_curriculum.id,
                Skill.code == "MD3.NOS.EQUAL_GROUPS",
            )
        )
        dc_equal_groups = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == dc_curriculum.id,
                Skill.code == "DC3.OA.EQUAL_GROUPS",
            )
        )
        learner = Student(
            curriculum_id=md_curriculum.id,
            first_name="Cross-Jurisdiction Isolation Learner",
            grade_level="3",
            school_system="TEST",
        )
        db.add(learner)
        db.flush()
        db.add(
            StudentSkill(
                student_id=learner.id,
                skill_id=md_equal_groups.id,
                mastery_score=Decimal("0.900"),
                confidence_score=Decimal("0.900"),
                independent_attempt_count=4,
                independent_correct_count=4,
                status=SkillStatus.MASTERED,
            )
        )
        db.flush()

        assert (
            db.get(StudentSkill, (learner.id, md_equal_groups.id)) is not None
        )
        assert db.get(StudentSkill, (learner.id, dc_equal_groups.id)) is None
        assert not hasattr(StudentSkill, "canonical_skill_id")
        db.rollback()


def test_md_and_dc_prerequisite_edges_are_curriculum_isolated():
    seed_md()
    seed_dc()
    with SessionLocal() as db:
        md_curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MD_MATH_3_2026_27")
        )
        dc_curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "DC_MATH_3_2024_25")
        )
        md_skill_ids = {
            skill.id
            for skill in db.scalars(
                select(Skill).where(Skill.curriculum_id == md_curriculum.id)
            )
        }
        dc_skill_ids = {
            skill.id
            for skill in db.scalars(
                select(Skill).where(Skill.curriculum_id == dc_curriculum.id)
            )
        }
        from app.models import SkillPrerequisite

        md_edges = list(
            db.scalars(
                select(SkillPrerequisite).where(
                    SkillPrerequisite.skill_id.in_(md_skill_ids)
                )
            )
        )
        dc_edges = list(
            db.scalars(
                select(SkillPrerequisite).where(
                    SkillPrerequisite.skill_id.in_(dc_skill_ids)
                )
            )
        )
        assert len(md_edges) == 3
        assert len(dc_edges) == 3
        assert all(
            edge.prerequisite_skill_id in md_skill_ids for edge in md_edges
        )
        assert all(
            edge.prerequisite_skill_id in dc_skill_ids for edge in dc_edges
        )
        db.rollback()
