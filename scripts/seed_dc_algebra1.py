from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping, EducationAuthority, Jurisdiction
from app.models import Curriculum, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "DC_ALGEBRA_1_CCSS_M"
OSSE_SOURCE = "https://osse.dc.gov/page/common-core-state-standards-mathematics"
DCPS_CONTEXT = "https://dcps.dc.gov/graduation"
VERSION = "CCSS-M-2010"


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
            mapping_type="EQUIVALENT", provenance_json={"basis": "AI Tutor reviewed DC Algebra I mapping",
            "standards_authority": "Office of the State Superintendent of Education",
            "standards_source": OSSE_SOURCE, "local_implementation_context": DCPS_CONTEXT,
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
            "standards_authority": "Office of the State Superintendent of Education",
            "standards_source": OSSE_SOURCE, "local_implementation_context": DCPS_CONTEXT}}))


def seed():
    db = SessionLocal()
    try:
        authority = _authority(db)
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        if curriculum is None:
            curriculum = Curriculum(code=CURRICULUM_CODE, name="District of Columbia Algebra I — CCSS-M",
                jurisdiction="District of Columbia", grade_level="Algebra I", authority_id=authority.id,
                version=VERSION, source_uri=OSSE_SOURCE)
            db.add(curriculum)
            db.flush()

        expr = _skill(db, curriculum, "DCA1.EXPR", "Algebraic Expressions",
            "Interpret and simplify algebraic expressions.", 1, "MATH.ALGEBRA1.EXPR")
        eq = _skill(db, curriculum, "DCA1.LINEAR.EQ", "Linear Equations",
            "Solve one-variable linear equations and justify equivalent steps.", 2, "MATH.ALGEBRA1.LINEAR_EQ")
        fn = _skill(db, curriculum, "DCA1.LINEAR.FN", "Linear Functions",
            "Represent linear relationships using equations, tables, and rates of change.", 3, "MATH.ALGEBRA1.LINEAR_FN")
        slope = _skill(db, curriculum, "DCA1.LINEAR.FN.SLOPE", "Slope-Intercept Form",
            "Write linear equations in y = mx + b form.", 3, "MATH.ALGEBRA1.LINEAR_FN_SLOPE")
        eval_fn = _skill(db, curriculum, "DCA1.LINEAR.FN.EVAL", "Evaluating Linear Functions",
            "Evaluate a linear function for a given input.", 3, "MATH.ALGEBRA1.LINEAR_FN_EVAL")
        _edge(db, eq, expr)
        _edge(db, fn, eq)
        _edge(db, slope, fn)
        _edge(db, eval_fn, slope)

        for args in [
            (expr, "Simplify 4x + 3x - 5.", "7x - 5", 1),
            (expr, "Expand 3(x + 4).", "3x + 12", 1),
            (eq, "Solve 5x + 7 = 32.", "5", 1),
            (eq, "Solve 4(x - 2) = 20.", "7", 2),
            (fn, "A line rises 12 units while running 4 units. What is its slope?", "3", 1),
            (fn, "A taxi charges $4 plus $2 per mile. Write the cost function for x miles.", "2x + 4", 2),
            (slope, "Write the equation of a line with slope 3 and y-intercept -2.", "y = 3x - 2", 1),
            (slope, "For y = -2x + 5, identify the slope.", "-2", 1),
            (eval_fn, "If f(x) = 3x + 1, find f(4).", "13", 1),
            (eval_fn, "If g(x) = -2x + 7, find g(-3).", "13", 2),
        ]:
            _problem(db, *args)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
