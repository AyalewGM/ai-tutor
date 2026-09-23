from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import (
    CanonicalSkill,
    CurriculumSkillMapping,
    EducationAuthority,
    Jurisdiction,
)
from app.models import Curriculum, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "VA_ALGEBRA_1_SOL_2023"
VDOE_SOURCE = "https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics"
VERSION = "SOL-2023-v1"


def _authority(db):
    us = db.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id.is_(None), Jurisdiction.code == "US"
        )
    )
    if us is None:
        us = Jurisdiction(code="US", name="United States", jurisdiction_type="COUNTRY")
        db.add(us)
        db.flush()
    va = db.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id == us.id, Jurisdiction.code == "VA"
        )
    )
    if va is None:
        va = Jurisdiction(
            parent_id=us.id,
            code="VA",
            name="Virginia",
            jurisdiction_type="STATE_PROVINCE_TERRITORY",
            source_uri=VDOE_SOURCE,
        )
        db.add(va)
        db.flush()
    authority = db.scalar(
        select(EducationAuthority).where(
            EducationAuthority.jurisdiction_id == va.id,
            EducationAuthority.code == "VDOE",
        )
    )
    if authority is None:
        authority = EducationAuthority(
            jurisdiction_id=va.id,
            code="VDOE",
            name="Virginia Department of Education",
            authority_type="STATE_AGENCY",
            source_uri=VDOE_SOURCE,
            provenance_json={"role": "Virginia mathematics standards authority"},
        )
        db.add(authority)
        db.flush()
    return authority


def _skill(db, curriculum, code, name, description, level, canonical_code):
    skill = db.scalar(
        select(Skill).where(
            Skill.curriculum_id == curriculum.id, Skill.code == code
        )
    )
    if skill is None:
        skill = Skill(
            curriculum_id=curriculum.id,
            code=code,
            name=name,
            description=description,
            difficulty_level=level,
            mastery_threshold=Decimal("0.850"),
        )
        db.add(skill)
        db.flush()
    canonical = db.scalar(
        select(CanonicalSkill).where(CanonicalSkill.code == canonical_code)
    )
    if canonical is None:
        canonical = CanonicalSkill(
            code=canonical_code,
            name=name,
            description=description,
            subject="MATHEMATICS",
        )
        db.add(canonical)
        db.flush()
    mapping = db.scalar(
        select(CurriculumSkillMapping).where(
            CurriculumSkillMapping.skill_id == skill.id
        )
    )
    if mapping is None:
        db.add(
            CurriculumSkillMapping(
                canonical_skill_id=canonical.id,
                skill_id=skill.id,
                mapping_type="EQUIVALENT",
                provenance_json={
                    "basis": "AI Tutor reviewed Virginia Algebra I 2023 SOL mapping",
                    "standards_authority": "Virginia Department of Education",
                    "standards_source": VDOE_SOURCE,
                    "curriculum_code": curriculum.code,
                    "curriculum_version": curriculum.version,
                },
            )
        )
        db.flush()
    return skill


def _edge(db, skill, prerequisite):
    if skill.curriculum_id != prerequisite.curriculum_id:
        raise ValueError("Prerequisite edges cannot cross curriculum boundaries")
    key = {"skill_id": skill.id, "prerequisite_skill_id": prerequisite.id}
    if db.get(SkillPrerequisite, key) is None:
        db.add(SkillPrerequisite(**key, importance_weight=Decimal("1.000")))


def _problem(db, skill, prompt, answer, difficulty=1):
    existing = db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == skill.id, Problem.prompt == prompt
        )
    )
    if existing is None:
        db.add(
            Problem(
                primary_skill_id=skill.id,
                problem_type="WORD_PROBLEM",
                difficulty=difficulty,
                prompt=prompt,
                canonical_answer=answer,
                source_type="CURATED",
                solution={
                    "answer": answer,
                    "provenance": {
                        "origin": "AUTHORED",
                        "author": "AI Tutor curriculum team",
                        "license": "proprietary",
                        "standards_authority": "Virginia Department of Education",
                        "standards_source": VDOE_SOURCE,
                    },
                },
            )
        )


def seed():
    db = SessionLocal()
    try:
        authority = _authority(db)
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        if curriculum is None:
            curriculum = Curriculum(
                code=CURRICULUM_CODE,
                name="Virginia Algebra I — 2023 SOL",
                jurisdiction="Virginia",
                grade_level="Algebra I",
                authority_id=authority.id,
                version=VERSION,
                source_uri=VDOE_SOURCE,
            )
            db.add(curriculum)
            db.flush()

        expr = _skill(
            db, curriculum, "VAA1.EXPR", "Algebraic Expressions",
            "Interpret, simplify, and transform algebraic expressions.", 1,
            "MATH.ALGEBRA1.EXPR",
        )
        eq = _skill(
            db, curriculum, "VAA1.LINEAR.EQ", "Linear Equations",
            "Solve and justify one-variable linear equations.", 2,
            "MATH.ALGEBRA1.LINEAR_EQ",
        )
        fn = _skill(
            db, curriculum, "VAA1.LINEAR.FN", "Linear Functions",
            "Represent and analyze linear relationships using multiple representations.", 3,
            "MATH.ALGEBRA1.LINEAR_FN",
        )
        slope = _skill(
            db, curriculum, "VAA1.LINEAR.FN.SLOPE", "Slope-Intercept Form",
            "Write and interpret linear equations in slope-intercept form.", 3,
            "MATH.ALGEBRA1.LINEAR_FN_SLOPE",
        )
        eval_fn = _skill(
            db, curriculum, "VAA1.LINEAR.FN.EVAL", "Evaluating Linear Functions",
            "Evaluate linear functions for specified inputs.", 3,
            "MATH.ALGEBRA1.LINEAR_FN_EVAL",
        )
        _edge(db, eq, expr)
        _edge(db, fn, eq)
        _edge(db, slope, fn)
        _edge(db, eval_fn, slope)

        for args in [
            (expr, "Simplify 6x - 2x + 9.", "4x + 9", 1),
            (expr, "Expand 4(x - 3).", "4x - 12", 1),
            (eq, "Solve 6x + 4 = 34.", "5", 1),
            (eq, "Solve 3(x + 2) = 21.", "5", 2),
            (fn, "A line rises 15 units while running 5 units. What is its slope?", "3", 1),
            (fn, "A service charges $6 plus $3 per hour. Write the cost function for x hours.", "3x + 6", 2),
            (slope, "Write the equation of a line with slope 2 and y-intercept -4.", "y = 2x - 4", 1),
            (slope, "For y = -3x + 8, identify the slope.", "-3", 1),
            (eval_fn, "If f(x) = 2x + 5, find f(4).", "13", 1),
            (eval_fn, "If g(x) = -3x + 2, find g(-2).", "8", 2),
        ]:
            _problem(db, *args)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
