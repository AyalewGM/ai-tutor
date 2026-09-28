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

CURRICULUM_CODE = "MD_MATH_3_2026_27"
CURRICULUM_VERSION = "MCCRS-revised-SY2026-27"
MSDE_SOURCE = "https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx"
GRADE3_CROSSWALK = "https://marylandpublicschools.org/about/Documents/DCAA/Math/revised/Grade-3-MCCRS-Math-Crosswalk-A.pdf"
GRADE3_COMPANION = "https://marylandpublicschools.org/about/Documents/DCAA/Math/revised/Grade-3-MCCRS-Math-Standard-Companion-Guide-A.pdf"


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
    maryland = db.scalar(
        select(Jurisdiction).where(
            Jurisdiction.parent_id == us.id, Jurisdiction.code == "MD"
        )
    )
    if maryland is None:
        maryland = Jurisdiction(
            parent_id=us.id,
            code="MD",
            name="Maryland",
            jurisdiction_type="STATE_PROVINCE_TERRITORY",
            source_uri=MSDE_SOURCE,
        )
        db.add(maryland)
        db.flush()
    authority = db.scalar(
        select(EducationAuthority).where(
            EducationAuthority.jurisdiction_id == maryland.id,
            EducationAuthority.code == "MSDE",
        )
    )
    if authority is None:
        authority = EducationAuthority(
            jurisdiction_id=maryland.id,
            code="MSDE",
            name="Maryland State Department of Education",
            authority_type="STATE_AGENCY",
            source_uri=MSDE_SOURCE,
            provenance_json={"role": "Maryland mathematics standards authority"},
        )
        db.add(authority)
        db.flush()
    return authority


def _skill(db, curriculum, *, code, name, description, level, canonical_code, standard):
    skill = db.scalar(
        select(Skill).where(Skill.curriculum_id == curriculum.id, Skill.code == code)
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
        select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id == skill.id)
    )
    if mapping is None:
        db.add(
            CurriculumSkillMapping(
                canonical_skill_id=canonical.id,
                skill_id=skill.id,
                mapping_type="EQUIVALENT",
                provenance_json={
                    "basis": "AI Tutor reviewed standards mapping",
                    "standard": standard,
                    "standards_authority": "Maryland State Department of Education",
                    "standards_source": GRADE3_CROSSWALK,
                    "companion_source": GRADE3_COMPANION,
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


def _problem(db, skill, *, problem_type, prompt, answer, parameters, difficulty):
    existing = db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == skill.id, Problem.prompt == prompt
        )
    )
    if existing is not None:
        return
    db.add(
        Problem(
            primary_skill_id=skill.id,
            problem_type=problem_type,
            difficulty=difficulty,
            prompt=prompt,
            canonical_answer=answer,
            source_type="CURATED",
            solution={
                "answer": answer,
                "parameters": parameters,
                "provenance": {
                    "origin": "AUTHORED",
                    "author": "AI Tutor curriculum team",
                    "license": "proprietary",
                    "standards_authority": "Maryland State Department of Education",
                    "standards_source": GRADE3_CROSSWALK,
                    "curriculum_version": CURRICULUM_VERSION,
                },
            },
        )
    )


def seed():
    db = SessionLocal()
    try:
        authority = _authority(db)
        curriculum = db.scalar(
            select(Curriculum).where(
                Curriculum.authority_id == authority.id,
                Curriculum.code == CURRICULUM_CODE,
                Curriculum.version == CURRICULUM_VERSION,
            )
        )
        if curriculum is None:
            curriculum = Curriculum(
                authority_id=authority.id,
                code=CURRICULUM_CODE,
                name="Maryland Grade 3 Mathematics — revised MCCRS",
                jurisdiction="Maryland",
                grade_level="3",
                version=CURRICULUM_VERSION,
                source_uri=GRADE3_CROSSWALK,
            )
            db.add(curriculum)
            db.flush()

        multiply = _skill(
            db,
            curriculum,
            code="MD3.NOS.EQUAL_GROUPS",
            name="Multiplication as Equal Groups",
            description="Interpret products as equal groups and arrays.",
            level=1,
            canonical_code="MATH.ELEMENTARY.MULTIPLICATION.EQUAL_GROUPS",
            standard="3.NOS.B",
        )
        divide = _skill(
            db,
            curriculum,
            code="MD3.NOS.EQUAL_SHARING",
            name="Division as Equal Sharing",
            description="Interpret quotients through fair sharing and groups of a known size.",
            level=2,
            canonical_code="MATH.ELEMENTARY.DIVISION.EQUAL_SHARING",
            standard="3.NOS.B",
        )
        fraction = _skill(
            db,
            curriculum,
            code="MD3.NOS.UNIT_FRACTION",
            name="Unit Fractions as Numbers",
            description="Understand 1/b as one equal part of a whole and build fractions from it.",
            level=3,
            canonical_code="MATH.ELEMENTARY.FRACTION.UNIT",
            standard="3.NOS.F",
        )
        area = _skill(
            db,
            curriculum,
            code="MD3.GR.RECTANGLE_AREA",
            name="Rectangle Area with Unit Squares",
            description="Relate rectangular arrays, unit squares, and multiplication to area.",
            level=3,
            canonical_code="MATH.ELEMENTARY.MEASUREMENT.RECTANGLE_AREA",
            standard="3.GR.C",
        )
        _edge(db, divide, multiply)
        _edge(db, fraction, divide)
        _edge(db, area, multiply)

        problems = [
            (multiply, "EQUAL_GROUPS", "There are 3 rows with 4 counters in each row. How many counters are there?", "12", {"rows": 3, "columns": 4, "representation": "counters"}, 1),
            (multiply, "EQUAL_GROUPS", "Five bags each hold 2 marbles. How many marbles are in all?", "10", {"rows": 5, "columns": 2, "representation": "groups"}, 1),
            (multiply, "EQUAL_GROUPS", "What product is represented by 4 equal groups of 6?", "24", {"rows": 4, "columns": 6, "representation": "groups"}, 2),
            (multiply, "EQUAL_GROUPS", "A garden has 7 short rows with 3 plants in each row. How many plants are there?", "21", {"rows": 7, "columns": 3, "representation": "array"}, 2),
            (divide, "EQUAL_SHARING", "Twelve counters are shared equally among 3 children. How many counters does each child get?", "4", {"total": 12, "groups": 3, "group_size": 4}, 1),
            (divide, "EQUAL_SHARING", "Eighteen shells are placed into groups of 6. How many groups are made?", "3", {"total": 18, "groups": 3, "group_size": 6}, 1),
            (divide, "EQUAL_SHARING", "Twenty-four pencils are packed equally into 4 boxes. How many pencils go in each box?", "6", {"total": 24, "groups": 4, "group_size": 6}, 2),
            (divide, "EQUAL_SHARING", "A coach places 28 cones in rows of 7. How many rows are made?", "4", {"total": 28, "groups": 4, "group_size": 7}, 2),
            (fraction, "UNIT_FRACTION", "A strip is divided into 4 equal parts. What fraction is one part?", "1/4", {"numerator": 1, "denominator": 4}, 1),
            (fraction, "UNIT_FRACTION", "One equal part of a whole is 1/6. How many equal parts make the whole?", "6", {"numerator": 1, "denominator": 6}, 1),
            (fraction, "UNIT_FRACTION", "A number line from 0 to 1 is split into 8 equal spaces. What fraction names the first mark after 0?", "1/8", {"numerator": 1, "denominator": 8}, 2),
            (fraction, "UNIT_FRACTION", "Mina uses 3 pieces of size 1/5. What fraction of the whole does she have?", "3/5", {"numerator": 3, "denominator": 5}, 2),
            (area, "RECTANGLE_AREA", "A rectangle has 3 rows of 5 unit squares. What is its area in square units?", "15", {"rows": 3, "columns": 5, "unit": "square units"}, 1),
            (area, "RECTANGLE_AREA", "A rectangular mat is 4 units long and 2 units wide. What is its area?", "8", {"rows": 2, "columns": 4, "unit": "square units"}, 1),
            (area, "RECTANGLE_AREA", "A rectangle covers 6 rows with 3 unit squares in each row. What area does it cover?", "18", {"rows": 6, "columns": 3, "unit": "square units"}, 2),
            (area, "RECTANGLE_AREA", "A board is 7 units by 4 units. Find its area in square units.", "28", {"rows": 4, "columns": 7, "unit": "square units"}, 2),
        ]
        for skill, problem_type, prompt, answer, parameters, difficulty in problems:
            _problem(
                db,
                skill,
                problem_type=problem_type,
                prompt=prompt,
                answer=answer,
                parameters=parameters,
                difficulty=difficulty,
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
