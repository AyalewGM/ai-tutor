from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority
from app.models import Curriculum, Problem, Skill
from scripts.seed_md_integrated_algebra1 import (
    CURRICULUM_CODE,
    CURRICULUM_VERSION,
    MSDE_SOURCE,
    seed,
)


def test_integrated_algebra1_registers_idempotently_without_mutating_traditional_course():
    seed()
    seed()

    db = SessionLocal()
    try:
        curricula = list(
            db.scalars(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        )
        assert len(curricula) == 1
        curriculum = curricula[0]
        assert curriculum.jurisdiction == "Maryland"
        assert curriculum.grade_level == "Integrated Algebra I"
        assert curriculum.version == CURRICULUM_VERSION
        assert curriculum.source_uri == MSDE_SOURCE

        authority = db.get(EducationAuthority, curriculum.authority_id)
        assert authority is not None
        assert authority.code == "MSDE"

        integrated_skills = list(
            db.scalars(select(Skill).where(Skill.curriculum_id == curriculum.id))
        )
        assert len(integrated_skills) == 11
        skill_by_code = {skill.code: skill for skill in integrated_skills}
        assert "IA1.AT.C.11" in skill_by_code
        assert "IA1.AT.D.13" in skill_by_code
        assert "IA1.AT.D.14" in skill_by_code
        d14 = skill_by_code["IA1.AT.D.14"]
        assert "piecewise" in d14.description.lower()
        assert "absolute-value" in d14.description.lower()
        assert db.scalar(
            select(func.count(Problem.id)).where(Problem.primary_skill_id == d14.id)
        ) == 1

        traditional = db.scalar(
            select(Curriculum).where(Curriculum.code == "MD_ALGEBRA_1_2026_27")
        )
        if traditional is not None:
            assert traditional.id != curriculum.id
            assert traditional.version != curriculum.version
            traditional_skill_ids = set(
                db.scalars(
                    select(Skill.id).where(Skill.curriculum_id == traditional.id)
                )
            )
            integrated_skill_ids = {skill.id for skill in integrated_skills}
            assert traditional_skill_ids.isdisjoint(integrated_skill_ids)
    finally:
        db.close()
