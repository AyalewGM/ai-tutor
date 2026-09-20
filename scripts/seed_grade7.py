from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority
from app.models import Curriculum, Misconception, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "MCPS_MATH_7"


def _skill(
    db,
    curriculum: Curriculum,
    code: str,
    name: str,
    description: str,
    level: int,
) -> Skill:
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


def _prerequisite(db, skill: Skill, prerequisite: Skill) -> None:
    if skill.curriculum_id != prerequisite.curriculum_id:
        raise ValueError("Prerequisite edges cannot cross curriculum boundaries")
    key = {"skill_id": skill.id, "prerequisite_skill_id": prerequisite.id}
    if db.get(SkillPrerequisite, key) is None:
        db.add(SkillPrerequisite(**key, importance_weight=Decimal("1.000")))


def _problem(
    db,
    skill: Skill,
    difficulty: int,
    prompt: str,
    answer: str,
    problem_type: str,
) -> None:
    if db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == skill.id,
            Problem.prompt == prompt,
        )
    ) is None:
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


def seed() -> None:
    db = SessionLocal()
    try:
        authority = db.scalar(
            select(EducationAuthority).where(EducationAuthority.code == "MCPS")
        )
        if authority is None:
            raise RuntimeError("MCPS education authority must be seeded before Grade 7 content")

        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        if curriculum is None:
            curriculum = Curriculum(
                code=CURRICULUM_CODE,
                name="MCPS Grade 7 Mathematics",
                jurisdiction="Montgomery County, Maryland",
                grade_level="7",
                authority_id=authority.id,
                version="1",
                source_uri="https://www.montgomeryschoolsmd.org/curriculum/math/ms/",
            )
            db.add(curriculum)
            db.flush()

        proportional = _skill(
            db,
            curriculum,
            "M7.RP.PROP",
            "Proportional Relationships",
            "Recognize and reason about proportional relationships.",
            1,
        )
        percent = _skill(
            db,
            curriculum,
            "M7.RP.PERCENT",
            "Percent Problems",
            "Use proportional reasoning to solve percent problems.",
            2,
        )
        expressions = _skill(
            db,
            curriculum,
            "M7.EE.EXPR",
            "Equivalent Expressions",
            "Use properties of operations to generate equivalent expressions.",
            2,
        )
        equations = _skill(
            db,
            curriculum,
            "M7.EE.EQUATION",
            "Equations and Inequalities",
            "Solve contextual equations and inequalities using rational numbers.",
            3,
        )

        _prerequisite(db, percent, proportional)
        _prerequisite(db, equations, expressions)

        def _misconception(skill, code, name, description, strategy):
            if db.scalar(
                select(Misconception).where(
                    Misconception.skill_id == skill.id,
                    Misconception.code == code,
                )
            ) is None:
                db.add(
                    Misconception(
                        skill_id=skill.id,
                        code=code,
                        name=name,
                        description=description,
                        remediation_strategy=strategy,
                    )
                )

        _misconception(
            percent,
            "FIN_001",
            "Percent treated as a whole-number amount",
            "The learner uses the percent as a dollar amount or forgets to "
            "divide by 100.",
            "Convert the percent to a decimal by dividing by 100 before "
            "multiplying by the amount.",
        )
        _misconception(
            expressions,
            "DIST_001",
            "Partial distribution",
            "The learner multiplies the outside factor by only one term "
            "inside parentheses.",
            "Represent the outside factor as multiplying each term separately "
            "before simplifying.",
        )
        _misconception(
            expressions,
            "ALG_001",
            "Unlike terms combined",
            "The learner merges constants into the variable term instead of "
            "combining like terms separately.",
            "Group variable terms with variable terms and constants with "
            "constants before simplifying.",
        )
        _misconception(
            expressions,
            "ALG_002",
            "Constant sign dropped",
            "The learner combines constants but drops the sign of a negative "
            "term.",
            "Attach each constant's sign to the term and combine signed "
            "constants carefully.",
        )
        _misconception(
            equations,
            "EQ_003",
            "Multiplies instead of dividing",
            "The learner multiplies both sides by the coefficient instead of "
            "dividing to isolate the variable.",
            "Undo multiplication with division: divide both sides by the "
            "coefficient of the variable.",
        )

        problems = [
            (
                proportional,
                1,
                "A recipe uses 2 cups of flour for 3 batches. How many cups are needed for 6 batches?",
                "4",
                "WORD_PROBLEM",
            ),
            (
                proportional,
                2,
                "A car travels 150 miles in 3 hours at a constant rate. What is the unit rate in miles per hour?",
                "50",
                "WORD_PROBLEM",
            ),
            (percent, 1, "What is 20% of 60?", "12", "WORD_PROBLEM"),
            (
                percent,
                2,
                "A $40 item is discounted by 25%. What is the discount amount?",
                "10",
                "WORD_PROBLEM",
            ),
            (expressions, 1, "Simplify 3(x + 2).", "3x+6", "SIMPLIFY_EXPRESSION"),
            (
                expressions,
                2,
                "Simplify 2x + 5 + 3x - 1.",
                "5x+4",
                "SIMPLIFY_EXPRESSION",
            ),
            (equations, 1, "Solve 4x = 20", "x=5", "SOLVE_EQUATION"),
            (equations, 2, "x + 7 = 19", "x=12", "SOLVE_EQUATION"),
            (equations, 3, "3x - 4 = 17", "x=7", "SOLVE_EQUATION"),
        ]
        for skill, difficulty, prompt, answer, problem_type in problems:
            _problem(db, skill, difficulty, prompt, answer, problem_type)

        db.commit()
        print(f"Grade 7 seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
