from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping, EducationAuthority, Jurisdiction
from app.models import Curriculum, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "DC_MATH_6"
OSSE_SOURCE = "https://osse.dc.gov/node/1210952"
DCPS_OVERLAY = "https://dcps.dc.gov/page/math"


def _authority(db):
    us = db.scalar(select(Jurisdiction).where(Jurisdiction.parent_id.is_(None), Jurisdiction.code == "US"))
    if us is None:
        us = Jurisdiction(code="US", name="United States", jurisdiction_type="COUNTRY")
        db.add(us)
        db.flush()
    dc = db.scalar(select(Jurisdiction).where(Jurisdiction.parent_id == us.id, Jurisdiction.code == "DC"))
    if dc is None:
        dc = Jurisdiction(parent_id=us.id, code="DC", name="District of Columbia",
                          jurisdiction_type="STATE_PROVINCE_TERRITORY", source_uri=OSSE_SOURCE)
        db.add(dc)
        db.flush()
    authority = db.scalar(select(EducationAuthority).where(
        EducationAuthority.jurisdiction_id == dc.id, EducationAuthority.code == "OSSE"))
    if authority is None:
        authority = EducationAuthority(jurisdiction_id=dc.id, code="OSSE",
            name="Office of the State Superintendent of Education", authority_type="STATE_AGENCY",
            source_uri=OSSE_SOURCE, provenance_json={"role": "DC mathematics standards authority"})
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
            mapping_type="EQUIVALENT", provenance_json={"basis": "AI Tutor reviewed standards mapping",
            "standards_authority": "District of Columbia State Board of Education / OSSE",
            "standards_source": OSSE_SOURCE, "local_overlay": DCPS_OVERLAY,
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
            solution={"answer": answer, "provenance": {"origin": "AUTHORED", "author": "AI Tutor curriculum team",
            "license": "proprietary", "standards_authority": "District of Columbia State Board of Education / OSSE",
            "standards_source": OSSE_SOURCE, "local_overlay": DCPS_OVERLAY}}))


def seed():
    db = SessionLocal()
    try:
        authority = _authority(db)
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        if curriculum is None:
            curriculum = Curriculum(code=CURRICULUM_CODE, name="District of Columbia Grade 6 Mathematics",
                jurisdiction="District of Columbia", grade_level="6", authority_id=authority.id,
                version="CCSS-2010-v1", source_uri=OSSE_SOURCE)
            db.add(curriculum)
            db.flush()

        ratio = _skill(db, curriculum, "DC6.RP.RATIO", "Ratio Reasoning", "Reason about ratios and equivalent ratios.", 1, "MATH.RP.RATIO")
        unit_rate = _skill(db, curriculum, "DC6.RP.UNIT_RATE", "Unit Rates", "Find and interpret unit rates.", 2, "MATH.RP.UNIT_RATE")
        fraction = _skill(db, curriculum, "DC6.NS.FRACTION", "Fraction Division", "Divide fractions in mathematical and contextual problems.", 2, "MATH.NS.FRACTION_DIVISION")
        expression = _skill(db, curriculum, "DC6.EE.EXPR", "Expressions", "Write and evaluate numerical and algebraic expressions.", 2, "MATH.EE.EXPRESSIONS")
        equation = _skill(db, curriculum, "DC6.EE.EQUATION", "One-variable Equations", "Represent and solve one-variable equations.", 3, "MATH.EE.ONE_VARIABLE_EQUATIONS")
        _edge(db, unit_rate, ratio)
        _edge(db, equation, expression)

        for args in [
            (ratio, "A garden has 15 tomato plants and 10 pepper plants. What is the ratio of tomato to pepper plants in simplest form?", "3:2", 1),
            (ratio, "A paint mix uses 3 cups of blue for every 2 cups of white. How many cups of blue are needed with 6 cups of white?", "9", 2),
            (unit_rate, "A train travels 120 miles in 4 hours. What is its unit rate in miles per hour?", "30", 1),
            (unit_rate, "Six folders cost $18. What is the cost per folder?", "3", 2),
            (fraction, "Two-thirds of a liter is shared equally among 4 bottles. How many liters go in each bottle?", "1/6", 1),
            (fraction, "How many three-fourths-cup servings are in 3 cups?", "4", 2),
            (expression, "Evaluate 5x + 2 when x = 4.", "22", 1),
            (expression, "Find the value of 3(5 + 2).", "21", 1),
            (equation, "A number plus 9 equals 24. What is the number?", "15", 1),
            (equation, "Five times a number is 35. What is the number?", "7", 2),
        ]:
            _problem(db, *args)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
