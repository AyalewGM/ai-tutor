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

CURRICULUM_CODE = "DC_MATH_7"
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
            curriculum = Curriculum(code=CURRICULUM_CODE, name="District of Columbia Grade 7 Mathematics",
                jurisdiction="District of Columbia", grade_level="7", authority_id=authority.id,
                version="CCSS-2010-v1", source_uri=OSSE_SOURCE)
            db.add(curriculum)
            db.flush()

        proportional = _skill(db, curriculum, "DC7.RP.PROPORTIONAL", "Proportional Relationships",
            "Recognize, represent, and solve proportional relationships.", 2, "MATH.RP.PROPORTIONAL_RELATIONSHIPS")
        percent = _skill(db, curriculum, "DC7.RP.PERCENT", "Percent Problems",
            "Solve multistep percent problems in context.", 2, "MATH.RP.PERCENT")
        rational = _skill(db, curriculum, "DC7.NS.RATIONAL", "Rational Number Arithmetic",
            "Add, subtract, multiply, and divide rational numbers.", 2, "MATH.NS.RATIONAL_ARITHMETIC")
        equation = _skill(db, curriculum, "DC7.EE.EQUATION", "Equations and Inequalities",
            "Solve real-world equations and inequalities.", 3, "MATH.EE.EQUATIONS_INEQUALITIES")
        probability = _skill(db, curriculum, "DC7.SP.PROBABILITY", "Probability and Sampling",
            "Use probability models and samples to reason about populations.", 3, "MATH.SP.PROBABILITY_SAMPLING")
        _edge(db, percent, proportional)
        _edge(db, equation, rational)

        for args in [
            (proportional, "A cyclist travels 18 miles in 1.5 hours at a constant rate. How many miles per hour is that?", "12", 1),
            (proportional, "Four notebooks cost $10. At the same rate, what do 10 notebooks cost?", "25", 2),
            (percent, "A $40 jacket is discounted by 25%. What is the sale price?", "30", 1),
            (percent, "A meal costs $24 before a 15% tip. How much is the tip?", "3.60", 2),
            (rational, "A temperature changes from -3 degrees to 5 degrees. What is the increase?", "8", 1),
            (rational, "Evaluate -3/4 + 1/2.", "-1/4", 2),
            (equation, "Three times a number plus 4 equals 19. What is the number?", "5", 1),
            (equation, "Solve 2x - 7 = 11.", "9", 2),
            (probability, "A bag has 3 red and 7 blue counters. What is the probability of drawing a red counter?", "3/10", 1),
            (probability, "In a random sample of 50 students, 20 prefer biking to school. What proportion of the sample prefers biking?", "2/5", 2),
        ]:
            _problem(db, *args)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
