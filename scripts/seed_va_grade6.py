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

CURRICULUM_CODE = "VA_MATH_6"
VDOE_SOURCE = "https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics"


def _authority(db):
    us = db.scalar(select(Jurisdiction).where(Jurisdiction.parent_id.is_(None), Jurisdiction.code == "US"))
    if us is None:
        us = Jurisdiction(code="US", name="United States", jurisdiction_type="COUNTRY")
        db.add(us)
        db.flush()
    va = db.scalar(select(Jurisdiction).where(Jurisdiction.parent_id == us.id, Jurisdiction.code == "VA"))
    if va is None:
        va = Jurisdiction(parent_id=us.id, code="VA", name="Virginia",
            jurisdiction_type="STATE_PROVINCE_TERRITORY", source_uri=VDOE_SOURCE)
        db.add(va)
        db.flush()
    authority = db.scalar(select(EducationAuthority).where(
        EducationAuthority.jurisdiction_id == va.id, EducationAuthority.code == "VDOE"))
    if authority is None:
        authority = EducationAuthority(jurisdiction_id=va.id, code="VDOE",
            name="Virginia Department of Education", authority_type="STATE_AGENCY",
            source_uri=VDOE_SOURCE, provenance_json={"role": "Virginia mathematics standards authority"})
        db.add(authority)
        db.flush()
    return authority


def _skill(db, curriculum, code, name, description, level, canonical_code):
    skill = db.scalar(select(Skill).where(Skill.curriculum_id == curriculum.id, Skill.code == code))
    if skill is None:
        skill = Skill(curriculum_id=curriculum.id, code=code, name=name, description=description,
            difficulty_level=level, mastery_threshold=Decimal("0.850"))
        db.add(skill)
        db.flush()
    canonical = db.scalar(select(CanonicalSkill).where(CanonicalSkill.code == canonical_code))
    if canonical is None:
        canonical = CanonicalSkill(code=canonical_code, name=name, description=description, subject="MATHEMATICS")
        db.add(canonical)
        db.flush()
    mapping = db.scalar(select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id == skill.id))
    if mapping is None:
        db.add(CurriculumSkillMapping(canonical_skill_id=canonical.id, skill_id=skill.id,
            mapping_type="EQUIVALENT", provenance_json={"basis": "AI Tutor reviewed 2023 SOL mapping",
            "standards_authority": "Virginia Department of Education", "standards_source": VDOE_SOURCE,
            "curriculum_code": curriculum.code, "curriculum_version": curriculum.version}))
        db.flush()
    return skill


def _edge(db, skill, prerequisite):
    if skill.curriculum_id != prerequisite.curriculum_id:
        raise ValueError("Prerequisite edges cannot cross curriculum boundaries")
    key = {"skill_id": skill.id, "prerequisite_skill_id": prerequisite.id}
    if db.get(SkillPrerequisite, key) is None:
        db.add(SkillPrerequisite(**key, importance_weight=Decimal("1.000")))


def _problem(db, skill, prompt, answer, difficulty=1):
    if db.scalar(select(Problem).where(Problem.primary_skill_id == skill.id, Problem.prompt == prompt)) is None:
        db.add(Problem(primary_skill_id=skill.id, problem_type="WORD_PROBLEM", difficulty=difficulty,
            prompt=prompt, canonical_answer=answer, source_type="CURATED",
            solution={"answer": answer, "provenance": {"origin": "AUTHORED",
            "author": "AI Tutor curriculum team", "license": "proprietary",
            "standards_authority": "Virginia Department of Education", "standards_source": VDOE_SOURCE}}))


def seed():
    db = SessionLocal()
    try:
        authority = _authority(db)
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        if curriculum is None:
            curriculum = Curriculum(code=CURRICULUM_CODE, name="Virginia Grade 6 Mathematics",
                jurisdiction="Virginia", grade_level="6", authority_id=authority.id,
                version="SOL-2023-v1", source_uri=VDOE_SOURCE)
            db.add(curriculum)
            db.flush()

        ratio = _skill(db, curriculum, "VA6.PFA.RATIO", "Ratio Reasoning",
            "Use ratios to compare quantities and represent proportional relationships.", 1, "MATH.RP.RATIO")
        rational = _skill(db, curriculum, "VA6.NS.RATIONAL", "Rational Number Equivalence",
            "Compare and represent fractions, decimals, and percents.", 2, "MATH.NS.RATIONAL_EQUIVALENCE")
        fraction = _skill(db, curriculum, "VA6.CE.FRACTION", "Fraction Operations",
            "Solve contextual problems involving positive rational numbers.", 2, "MATH.NS.FRACTION_DIVISION")
        expression = _skill(db, curriculum, "VA6.PFA.EXPR", "Expressions",
            "Use algebraic terminology and evaluate expressions.", 2, "MATH.EE.EXPRESSIONS")
        equation = _skill(db, curriculum, "VA6.PFA.EQUATION", "One-variable Equations",
            "Represent and solve linear equations in one variable.", 3, "MATH.EE.ONE_VARIABLE_EQUATIONS")
        _edge(db, equation, expression)

        for args in [
            (ratio, "A trail map uses 4 centimeters for 10 miles. What is the ratio of centimeters to miles in simplest form?", "2:5", 1),
            (ratio, "A recipe uses 3 cups of oats for every 2 cups of fruit. How many cups of oats are needed for 6 cups of fruit?", "9", 2),
            (rational, "Write 0.35 as a percent.", "35%", 1),
            (rational, "Which is greater: 3/5 or 55%?", "3/5", 2),
            (fraction, "Three-fourths of a gallon is shared equally among 3 containers. How much goes in each?", "1/4", 1),
            (fraction, "How many two-thirds-cup servings are in 4 cups?", "6", 2),
            (expression, "Evaluate 4x + 3 when x = 5.", "23", 1),
            (expression, "Find the value of 2(6 + 4).", "20", 1),
            (equation, "A number plus 11 equals 29. What is the number?", "18", 1),
            (equation, "Six times a number is 42. What is the number?", "7", 2),
        ]:
            _problem(db, *args)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
