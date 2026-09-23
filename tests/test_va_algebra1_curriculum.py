from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping, EducationAuthority
from app.models import Curriculum, Problem, Skill, SkillPrerequisite
from scripts.seed_va_algebra1 import CURRICULUM_CODE, VDOE_SOURCE, VERSION, seed


def test_va_algebra1_seed_is_idempotent_provenanced_and_isolated():
    seed()
    seed()
    db = SessionLocal()
    try:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        assert curriculum is not None
        assert curriculum.grade_level == "Algebra I"
        assert curriculum.version == VERSION
        assert curriculum.source_uri == VDOE_SOURCE
        authority = db.get(EducationAuthority, curriculum.authority_id)
        assert authority is not None
        assert authority.code == "VDOE"

        skills = list(db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id)))
        assert len(skills) == 5
        ids = {skill.id for skill in skills}
        mappings = list(
            db.scalars(
                select(CurriculumSkillMapping).where(
                    CurriculumSkillMapping.skill_id.in_(ids)
                )
            )
        )
        assert len(mappings) == 5
        canonical_codes = set(
            db.scalars(
                select(CanonicalSkill.code).where(
                    CanonicalSkill.id.in_(
                        {mapping.canonical_skill_id for mapping in mappings}
                    )
                )
            )
        )
        assert "MATH.ALGEBRA1.LINEAR_EQ" in canonical_codes
        assert "MATH.ALGEBRA1.LINEAR_FN" in canonical_codes

        problems = list(
            db.scalars(select(Problem).where(Problem.primary_skill_id.in_(ids)))
        )
        assert len(problems) == 10
        assert all(
            problem.solution["provenance"]["origin"] == "AUTHORED"
            for problem in problems
        )
        edges = list(
            db.scalars(
                select(SkillPrerequisite).where(SkillPrerequisite.skill_id.in_(ids))
            )
        )
        assert len(edges) == 4
        assert all(edge.prerequisite_skill_id in ids for edge in edges)

        for other_code in (
            "MD_ALGEBRA_1_2026_27",
            "DC_ALGEBRA_1_CCSS_M",
            "VA_MATH_6",
            "VA_MATH_7",
            "ON_MTH1W_2021",
        ):
            other = db.scalar(select(Curriculum).where(Curriculum.code == other_code))
            if other is not None:
                other_ids = set(
                    db.scalars(select(Skill.id).where(Skill.curriculum_id == other.id))
                )
                assert ids.isdisjoint(other_ids)

        dc = db.scalar(
            select(Curriculum).where(Curriculum.code == "DC_ALGEBRA_1_CCSS_M")
        )
        if dc is not None:
            dc_ids = set(
                db.scalars(select(Skill.id).where(Skill.curriculum_id == dc.id))
            )
            dc_mappings = list(
                db.scalars(
                    select(CurriculumSkillMapping).where(
                        CurriculumSkillMapping.skill_id.in_(dc_ids)
                    )
                )
            )
            assert {m.canonical_skill_id for m in mappings} & {
                m.canonical_skill_id for m in dc_mappings
            }
    finally:
        db.close()
