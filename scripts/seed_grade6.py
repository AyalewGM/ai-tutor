from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping, EducationAuthority
from app.models import Curriculum, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "MCPS_MATH_6"
MSDE_SOURCE = "https://marylandpublicschools.org/about/Pages/DCAA/Math/revised-standards.aspx"
MCPS_OVERLAY = "https://www.montgomeryschoolsmd.org/curriculum/math/ms/"


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
            "standards_authority": "Maryland State Department of Education", "standards_source": MSDE_SOURCE,
            "local_overlay": MCPS_OVERLAY, "curriculum_code": curriculum.code, "curriculum_version": curriculum.version}))
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
            "license": "proprietary", "standards_authority": "Maryland State Department of Education",
            "standards_source": MSDE_SOURCE, "local_overlay": MCPS_OVERLAY}}))


def seed():
    db = SessionLocal()
    try:
        authority = db.scalar(select(EducationAuthority).where(EducationAuthority.code == "MCPS"))
        if authority is None:
            raise RuntimeError("MCPS education authority must be seeded before Grade 6 content")
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        if curriculum is None:
            curriculum = Curriculum(code=CURRICULUM_CODE, name="MCPS Grade 6 Mathematics",
                jurisdiction="Montgomery County, Maryland", grade_level="6", authority_id=authority.id,
                version="MSDE-2026-27-v1", source_uri=MSDE_SOURCE)
            db.add(curriculum)
            db.flush()

        ratio = _skill(db, curriculum, "M6.RP.RATIO", "Ratio Reasoning", "Reason about ratios and equivalent ratios.", 1, "MATH.RP.RATIO")
        unit_rate = _skill(db, curriculum, "M6.RP.UNIT_RATE", "Unit Rates", "Find and interpret unit rates.", 2, "MATH.RP.UNIT_RATE")
        fraction = _skill(db, curriculum, "M6.NS.FRACTION", "Fraction Division", "Divide fractions in mathematical and contextual problems.", 2, "MATH.NS.FRACTION_DIVISION")
        expression = _skill(db, curriculum, "M6.EE.EXPR", "Expressions", "Write and evaluate numerical and algebraic expressions.", 2, "MATH.EE.EXPRESSIONS")
        equation = _skill(db, curriculum, "M6.EE.EQUATION", "One-variable Equations", "Represent and solve one-variable equations.", 3, "MATH.EE.ONE_VARIABLE_EQUATIONS")
        _edge(db, unit_rate, ratio)
        _edge(db, equation, expression)

        for args in [
            (ratio, "A class has 12 red markers and 8 blue markers. What is the ratio of red to blue in simplest form?", "3:2", 1),
            (ratio, "A drink uses 2 cups of juice for every 3 cups of water. How many cups of juice are needed with 9 cups of water?", "6", 2),
            (unit_rate, "A cyclist travels 36 miles in 3 hours. What is the unit rate in miles per hour?", "12", 1),
            (unit_rate, "Five notebooks cost $15. What is the cost per notebook?", "3", 2),
            (fraction, "Three-fourths of a gallon is shared equally among 3 containers. How many gallons go in each container?", "1/4", 1),
            (fraction, "How many one-half-cup servings are in 3 cups?", "6", 2),
            (expression, "Evaluate 4x + 3 when x = 5.", "23", 1),
            (expression, "Write the value of 2(6 + 4).", "20", 1),
            (equation, "A number plus 7 equals 19. What is the number?", "12", 1),
            (equation, "Four times a number is 28. What is the number?", "7", 2),
        ]:
            _problem(db, *args)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
