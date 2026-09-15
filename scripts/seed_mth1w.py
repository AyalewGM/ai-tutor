from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority, Jurisdiction
from app.models import Curriculum, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "ON_MTH1W_2021"
AUTHORITY_CODE = "ON-MOE"
CANADA_CODE = "CA"
ONTARIO_CODE = "ON"
SOURCE_URI = "https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses-list"


def _skill(db, curriculum, code, name, description, level):
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
    return skill


def _prerequisite(db, skill, prerequisite):
    if skill.curriculum_id != prerequisite.curriculum_id:
        raise ValueError("Prerequisite edges cannot cross curriculum boundaries")
    key = {"skill_id": skill.id, "prerequisite_skill_id": prerequisite.id}
    if db.get(SkillPrerequisite, key) is None:
        db.add(SkillPrerequisite(**key, importance_weight=Decimal("1.000")))


def _problem(db, skill, difficulty, prompt, answer, problem_type):
    existing = db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == skill.id,
            Problem.prompt == prompt,
        )
    )
    if existing is None:
        db.add(
            Problem(
                primary_skill_id=skill.id,
                problem_type=problem_type,
                difficulty=difficulty,
                prompt=prompt,
                canonical_answer=answer,
                solution={"answer": answer},
                source_type="CURATED",
            )
        )


def _jurisdiction(db, *, parent_id, code, name, jurisdiction_type, source_uri=None):
    query = select(Jurisdiction).where(Jurisdiction.code == code)
    if parent_id is None:
        query = query.where(Jurisdiction.parent_id.is_(None))
    else:
        query = query.where(Jurisdiction.parent_id == parent_id)
    jurisdiction = db.scalar(query)
    if jurisdiction is None:
        jurisdiction = Jurisdiction(
            parent_id=parent_id,
            code=code,
            name=name,
            jurisdiction_type=jurisdiction_type,
            source_uri=source_uri,
            provenance_json={"source": "authoritative_public"} if source_uri else None,
        )
        db.add(jurisdiction)
        db.flush()
    return jurisdiction


def seed():
    db = SessionLocal()
    try:
        canada = _jurisdiction(
            db,
            parent_id=None,
            code=CANADA_CODE,
            name="Canada",
            jurisdiction_type="COUNTRY",
        )
        ontario_jurisdiction = _jurisdiction(
            db,
            parent_id=canada.id,
            code=ONTARIO_CODE,
            name="Ontario",
            jurisdiction_type="STATE_PROVINCE_TERRITORY",
            source_uri=SOURCE_URI,
        )

        authority = db.scalar(
            select(EducationAuthority).where(
                EducationAuthority.jurisdiction_id == ontario_jurisdiction.id,
                EducationAuthority.code == AUTHORITY_CODE,
            )
        )
        if authority is None:
            authority = EducationAuthority(
                jurisdiction_id=ontario_jurisdiction.id,
                code=AUTHORITY_CODE,
                name="Ontario Ministry of Education",
                authority_type="MINISTRY",
                source_uri=SOURCE_URI,
                provenance_json={"source": "authoritative_public", "curriculum": "MTH1W 2021"},
            )
            db.add(authority)
            db.flush()

        curriculum = db.scalar(
            select(Curriculum).where(
                Curriculum.authority_id == authority.id,
                Curriculum.code == CURRICULUM_CODE,
                Curriculum.version == "2021",
            )
        )
        if curriculum is None:
            curriculum = Curriculum(
                code=CURRICULUM_CODE,
                name="Ontario Grade 9 Mathematics (MTH1W)",
                jurisdiction="Ontario, Canada",
                grade_level="9",
                authority_id=authority.id,
                version="2021",
                source_uri=SOURCE_URI,
            )
            db.add(curriculum)
            db.flush()

        number = _skill(
            db,
            curriculum,
            "MTH1W.B.NUM",
            "Number Sense and Operations",
            "Represent and operate with numbers in Grade 9 mathematical contexts.",
            1,
        )
        algebra = _skill(
            db,
            curriculum,
            "MTH1W.C.ALG",
            "Algebraic Expressions and Equations",
            "Represent relationships algebraically and solve equations.",
            2,
        )
        relations = _skill(
            db,
            curriculum,
            "MTH1W.C.REL",
            "Linear Relations",
            "Represent and reason about linear relationships in multiple forms.",
            3,
        )
        financial = _skill(
            db,
            curriculum,
            "MTH1W.F.FIN",
            "Financial Literacy",
            "Apply mathematical reasoning to practical financial decisions.",
            2,
        )

        _prerequisite(db, algebra, number)
        _prerequisite(db, relations, algebra)
        _prerequisite(db, financial, number)

        problems = [
            (number, 1, "Evaluate -6 + 14.", "8", "ARITHMETIC"),
            (number, 2, "Evaluate 3/4 + 1/2.", "5/4", "ARITHMETIC"),
            (algebra, 1, "Simplify 4x + 3 + 2x - 5.", "6x-2", "SIMPLIFY_EXPRESSION"),
            (algebra, 2, "Solve 3x + 4 = 19.", "x=5", "SOLVE_EQUATION"),
            (relations, 2, "For y = 3x + 2, what is y when x = 4?", "14", "LINEAR_RELATION"),
            (relations, 3, "A line has slope 2 and y-intercept -1. Write its equation.", "y=2x-1", "LINEAR_RELATION"),
            (financial, 1, "A $80 purchase has 13% tax. What is the tax amount?", "10.40", "WORD_PROBLEM"),
            (financial, 2, "A $120 item is discounted by 25%. What is the sale price before tax?", "90", "WORD_PROBLEM"),
        ]
        for args in problems:
            _problem(db, *args)

        db.commit()
        print(f"MTH1W seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
