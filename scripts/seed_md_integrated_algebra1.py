from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import (
    CanonicalSkill,
    CurriculumSkillMapping,
    EducationAuthority,
    Jurisdiction,
)
from app.models import Curriculum, Problem, Skill

CURRICULUM_CODE = "MD_INTEGRATED_ALGEBRA_1_2027_28"
CURRICULUM_VERSION = "MCCRS-2025-INTEGRATED-ALGEBRA-1-SY2027-28"
MSDE_SOURCE = (
    "https://www.marylandpublicschools.org/about/Documents/DCAA/Math/revised/"
    "Integrated-Algebra-1-Crosswalk-A.pdf"
)


def _authority(db):
    us = db.scalar(select(Jurisdiction).where(Jurisdiction.parent_id.is_(None), Jurisdiction.code == "US"))
    if us is None:
        us = Jurisdiction(code="US", name="United States", jurisdiction_type="COUNTRY")
        db.add(us); db.flush()
    md = db.scalar(select(Jurisdiction).where(Jurisdiction.parent_id == us.id, Jurisdiction.code == "MD"))
    if md is None:
        md = Jurisdiction(parent_id=us.id, code="MD", name="Maryland", jurisdiction_type="STATE_PROVINCE_TERRITORY", source_uri=MSDE_SOURCE)
        db.add(md); db.flush()
    authority = db.scalar(select(EducationAuthority).where(EducationAuthority.jurisdiction_id == md.id, EducationAuthority.code == "MSDE"))
    if authority is None:
        authority = EducationAuthority(jurisdiction_id=md.id, code="MSDE", name="Maryland State Department of Education", authority_type="STATE_AGENCY", source_uri=MSDE_SOURCE, provenance_json={"role": "Maryland mathematics standards authority"})
        db.add(authority); db.flush()
    return authority


def _skill(db, curriculum, code, name, description, level, canonical_code):
    skill = db.scalar(select(Skill).where(Skill.curriculum_id == curriculum.id, Skill.code == code))
    if skill is None:
        skill = Skill(curriculum_id=curriculum.id, code=code, name=name, description=description, difficulty_level=level, mastery_threshold=Decimal("0.850"))
        db.add(skill); db.flush()
    canonical = db.scalar(select(CanonicalSkill).where(CanonicalSkill.code == canonical_code))
    if canonical is None:
        canonical = CanonicalSkill(code=canonical_code, name=name, description=description, subject="MATHEMATICS")
        db.add(canonical); db.flush()
    mapping = db.scalar(select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id == skill.id))
    if mapping is None:
        db.add(CurriculumSkillMapping(canonical_skill_id=canonical.id, skill_id=skill.id, mapping_type="EQUIVALENT", provenance_json={"basis": "AI Tutor reviewed MSDE Integrated Algebra I mapping", "standards_authority": "Maryland State Department of Education", "standards_source": MSDE_SOURCE, "curriculum_code": curriculum.code, "curriculum_version": curriculum.version, "review_policy": "canonical grain equivalence required; no course-name inference"}))
        db.flush()
    return skill


def _problem(db, skill, prompt, answer, difficulty=1):
    existing = db.scalar(select(Problem).where(Problem.primary_skill_id == skill.id, Problem.prompt == prompt))
    if existing is None:
        db.add(Problem(primary_skill_id=skill.id, problem_type="WORD_PROBLEM", difficulty=difficulty, prompt=prompt, canonical_answer=answer, source_type="CURATED", solution={"answer": answer, "provenance": {"origin": "AUTHORED", "author": "AI Tutor curriculum team", "license": "proprietary", "standards_authority": "Maryland State Department of Education", "standards_source": MSDE_SOURCE}}))


def seed() -> None:
    """Seed reviewed IA1 skills without inferring prerequisite edges from standards order."""
    db = SessionLocal()
    try:
        authority = _authority(db)
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        if curriculum is None:
            curriculum = Curriculum(code=CURRICULUM_CODE, name="Maryland Integrated Algebra I — 2025 revised MCCRS", jurisdiction="Maryland", grade_level="Integrated Algebra I", authority_id=authority.id, version=CURRICULUM_VERSION, source_uri=MSDE_SOURCE)
            db.add(curriculum); db.flush()
        else:
            curriculum.name = "Maryland Integrated Algebra I — 2025 revised MCCRS"; curriculum.jurisdiction = "Maryland"; curriculum.grade_level = "Integrated Algebra I"; curriculum.authority_id = authority.id; curriculum.version = CURRICULUM_VERSION; curriculum.source_uri = MSDE_SOURCE

        specs = [
            ("IA1.AT.C.10", "Functions, Domain, and Range", "Identify, represent, and analyze functions using domain, range, tables, graphs, equations, and function notation.", 2, "MATH.IA1.AT.C.10"),
            ("IA1.GR.A.1", "Rigid Transformations and Congruence", "Apply rotations, reflections, and translations and use preserved distance and angle measure to justify congruence.", 2, "MATH.IA1.GR.A.1"),
            ("IA1.DS.A.1", "Correlation and Causation", "Distinguish correlation from causation when interpreting statistical relationships.", 2, "MATH.IA1.DS.A.1"),
            ("IA1.AT.B.8", "Linear-Inequality Optimization", "Model constraints with systems of linear inequalities, identify the feasible region, and justify an optimal solution in context.", 3, "MATH.IA1.AT.B.8"),
            ("IA1.AT.D.15", "Linear and Exponential Models", "Construct, compare, and interpret linear and exponential models in context, including rates of change and growth factors.", 3, "MATH.IA1.AT.D.15"),
            ("IA1.AT.D.17", "Inverse Linear Functions", "Find and interpret inverse linear functions and connect an inverse to reversing the input-output relationship.", 3, "MATH.IA1.AT.D.17"),
        ]
        skills = {code: _skill(db, curriculum, code, name, desc, level, canonical) for code, name, desc, level, canonical in specs}
        problems = [
            ("IA1.AT.C.10", "A function assigns 3, 7, and 11 to inputs 1, 2, and 3. What is its domain?", "{1, 2, 3}", 1),
            ("IA1.GR.A.1", "A triangle is translated 4 units right and 2 units up. Does the translation preserve its side lengths?", "Yes", 1),
            ("IA1.DS.A.1", "A study finds that students who carry umbrellas are more likely to wear raincoats. Does this correlation alone prove that umbrellas cause people to wear raincoats?", "No", 1),
            ("IA1.AT.B.8", "A club sells adult tickets x and student tickets y. Capacity gives x + y <= 100 and staffing gives x <= 60. If revenue is 10x + 6y, what quantity should be maximized?", "10x + 6y", 2),
            ("IA1.AT.D.15", "Plan A starts at 20 and increases by 5 each week. Plan B starts at 20 and multiplies by 1.10 each week. Which plan is exponential?", "Plan B", 2),
            ("IA1.AT.D.17", "A linear function is f(x) = 3x + 6. What is f inverse of x?", "(x - 6) / 3", 2),
        ]
        for code, prompt, answer, difficulty in problems:
            _problem(db, skills[code], prompt, answer, difficulty)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
