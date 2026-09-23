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

CURRICULUM_CODE = "VA_MATH_7"
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
            curriculum = Curriculum(code=CURRICULUM_CODE, name="Virginia Grade 7 Mathematics",
                jurisdiction="Virginia", grade_level="7", authority_id=authority.id,
                version="SOL-2023-v1", source_uri=VDOE_SOURCE)
            db.add(curriculum)
            db.flush()

        rational = _skill(db, curriculum, "VA7.CE.RATIONAL", "Rational Number Operations",
            "Use rational-number operations accurately in mathematical and contextual problems.", 2,
            "MATH.NS.RATIONAL_OPERATIONS")
        proportional = _skill(db, curriculum, "VA7.PFA.PROPORTIONAL", "Proportional Relationships",
            "Represent and solve proportional relationships, including percent applications.", 2,
            "MATH.RP.PROPORTIONAL_RELATIONSHIPS")
        equation = _skill(db, curriculum, "VA7.PFA.EQUATION", "Equations and Inequalities",
            "Represent and solve one-variable equations and inequalities.", 3,
            "MATH.EE.ONE_VARIABLE_EQUATIONS")
        geometry = _skill(db, curriculum, "VA7.MG.GEOMETRY", "Geometry Applications",
            "Solve measurement and geometry problems using properties of figures.", 2,
            "MATH.G.GEOMETRY_APPLICATIONS")
        probability = _skill(db, curriculum, "VA7.PS.PROBABILITY", "Probability and Data",
            "Reason about probability and interpret data from samples and displays.", 2,
            "MATH.SP.PROBABILITY")
        _edge(db, equation, rational)
        _edge(db, proportional, rational)

        for args in [
            (rational, "Evaluate -6 + 9.", "3", 1),
            (rational, "A temperature changes from 4 degrees to -3 degrees. What is the change?", "-7", 2),
            (proportional, "Five notebooks cost $15. At the same rate, what do 8 notebooks cost?", "$24", 1),
            (proportional, "A $60 item is discounted by 25%. What is the sale price?", "$45", 2),
            (equation, "Solve 3x + 5 = 20.", "5", 1),
            (equation, "Solve x - 4 < 9.", "x < 13", 2),
            (geometry, "A rectangle is 8 cm long and 5 cm wide. What is its area?", "40 square centimeters", 1),
            (geometry, "A triangle has base 10 cm and height 6 cm. What is its area?", "30 square centimeters", 2),
            (probability, "A bag has 3 red and 7 blue tiles. What is the probability of choosing red?", "3/10", 1),
            (probability, "In a sample of 50 students, 20 prefer biking. What percent prefer biking?", "40%", 2),
        ]:
            _problem(db, *args)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
