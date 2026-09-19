from decimal import Decimal

from sqlalchemy import select

from app.content_ingestion import (
    ContentPackInput,
    ExpectationInput,
    ExpectationSkillMappingInput,
    persist_expectation_pack,
)
from app.core.database import SessionLocal
from app.models import Curriculum, Misconception, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "MTH1W"
AUTHORITY_CODE = "ON_MIN_ED"
SOURCE_URI = "https://www.dcp.edu.gov.on.ca/en/curriculum/secondary-mathematics/courses/mth1w"


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


def _expectation_pack() -> ContentPackInput:
    expectations = (
        ExpectationInput(
            source_identifier="MTH1W.B",
            title="Number",
            strand="B. Number",
            source_uri=SOURCE_URI,
        ),
        ExpectationInput(
            source_identifier="MTH1W.C",
            title="Algebra",
            strand="C. Algebra",
            source_uri=SOURCE_URI,
        ),
        ExpectationInput(
            source_identifier="MTH1W.F",
            title="Financial Literacy",
            strand="F. Financial Literacy",
            source_uri=SOURCE_URI,
        ),
    )
    mappings = (
        ExpectationSkillMappingInput("MTH1W.B", "MTH1W.B.NUM"),
        ExpectationSkillMappingInput("MTH1W.C", "MTH1W.C.ALG"),
        ExpectationSkillMappingInput("MTH1W.C", "MTH1W.C.REL"),
        ExpectationSkillMappingInput("MTH1W.F", "MTH1W.F.FIN"),
    )
    return ContentPackInput(
        curriculum_code=CURRICULUM_CODE,
        curriculum_version="2021",
        expectations=expectations,
        mappings=mappings,
    )


def seed():
    db = SessionLocal()
    try:
        curriculum = db.scalar(
            select(Curriculum).where(
                Curriculum.code == CURRICULUM_CODE,
                Curriculum.version == "2021",
                Curriculum.active.is_(True),
            )
        )
        if curriculum is None:
            raise RuntimeError(
                "Active MTH1W 2021 curriculum registry entry is required; run migrations first"
            )

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

        misconception = db.scalar(
            select(Misconception).where(
                Misconception.skill_id == number.id,
                Misconception.code == "DIST_001",
            )
        )
        if misconception is None:
            db.add(
                Misconception(
                    skill_id=number.id,
                    code="DIST_001",
                    name="Partial distribution",
                    description=(
                        "The learner multiplies the outside factor by only one term "
                        "inside parentheses."
                    ),
                    remediation_strategy=(
                        "Represent the outside factor as multiplying each term separately "
                        "before simplifying."
                    ),
                )
            )

        problems = [
            (number, 1, "Evaluate -6 + 14.", "8", "ARITHMETIC"),
            (number, 2, "Evaluate 3/4 + 1/2.", "5/4", "ARITHMETIC"),
            (algebra, 1, "Simplify 4x + 3 + 2x - 5.", "6x-2", "SIMPLIFY_EXPRESSION"),
            (algebra, 2, "Solve 3x + 4 = 19.", "x=5", "SOLVE_EQUATION"),
            (algebra, 2, "Simplify 4(x + 3).", "4x+12", "SIMPLIFY_EXPRESSION"),
            (relations, 2, "For y = 3x + 2, what is y when x = 4?", "14", "LINEAR_RELATION"),
            (relations, 3, "A line has slope 2 and y-intercept -1. Write its equation.", "y=2x-1", "LINEAR_RELATION"),
            (financial, 1, "A $80 purchase has 13% tax. What is the tax amount?", "10.40", "WORD_PROBLEM"),
            (financial, 2, "A $120 item is discounted by 25%. What is the sale price before tax?", "90", "WORD_PROBLEM"),
        ]
        for args in problems:
            _problem(db, *args)

        persist_expectation_pack(db, _expectation_pack())

        db.commit()
        print(f"MTH1W seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
