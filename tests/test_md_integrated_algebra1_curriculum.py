from decimal import Decimal

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority
from app.models import Curriculum, Problem, Skill, Student, StudentSkill
from scripts.seed_md_algebra1 import CURRICULUM_CODE as TRADITIONAL_CURRICULUM_CODE, seed as seed_traditional
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
        assert len(integrated_skills) == 13
        skill_by_code = {skill.code: skill for skill in integrated_skills}
        assert "IA1.AT.A.1" in skill_by_code
        assert "IA1.AT.C.11" in skill_by_code
        assert "IA1.AT.C.12" in skill_by_code
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


def test_integrated_seed_preserves_existing_traditional_pathway_evidence():
    seed_traditional()

    db = SessionLocal()
    try:
        traditional = db.scalar(
            select(Curriculum).where(Curriculum.code == TRADITIONAL_CURRICULUM_CODE)
        )
        assert traditional is not None
        traditional_skill = db.scalar(
            select(Skill).where(Skill.curriculum_id == traditional.id).limit(1)
        )
        assert traditional_skill is not None
        student = Student(
            curriculum_id=traditional.id,
            first_name="Synthetic Historical Learner",
            grade_level="Algebra I",
            school_system="SYNTHETIC",
        )
        db.add(student)
        db.flush()
        evidence = StudentSkill(
            student_id=student.id,
            skill_id=traditional_skill.id,
            mastery_score=Decimal("0.875"),
            confidence_score=Decimal("0.900"),
            attempt_count=8,
            correct_count=7,
            independent_attempt_count=5,
            independent_correct_count=4,
            hinted_correct_count=1,
            current_difficulty=3,
        )
        db.add(evidence)
        db.commit()
        student_id = student.id
        skill_id = traditional_skill.id
    finally:
        db.close()

    seed()
    seed()

    db = SessionLocal()
    try:
        preserved = db.get(StudentSkill, (student_id, skill_id))
        assert preserved is not None
        assert preserved.mastery_score == Decimal("0.875")
        assert preserved.confidence_score == Decimal("0.900")
        assert preserved.attempt_count == 8
        assert preserved.correct_count == 7
        assert preserved.independent_attempt_count == 5
        assert preserved.independent_correct_count == 4
        assert preserved.hinted_correct_count == 1
        assert preserved.current_difficulty == 3

        integrated = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        assert integrated is not None
        assert integrated.id != traditional.id
    finally:
        db.close()
