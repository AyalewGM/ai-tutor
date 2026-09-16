from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority
from app.models import Curriculum, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "MCPS_ALGEBRA_1_2026_27"


def _skill(db, curriculum: Curriculum, code: str, name: str, description: str, level: int) -> Skill:
    skill = db.scalar(select(Skill).where(Skill.curriculum_id == curriculum.id, Skill.code == code))
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


def _problem(db, skill: Skill, difficulty: int, prompt: str, answer: str, problem_type: str) -> None:
    if db.scalar(select(Problem).where(Problem.primary_skill_id == skill.id, Problem.prompt == prompt)) is None:
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
        authority = db.scalar(select(EducationAuthority).where(EducationAuthority.code == "MCPS"))
        if authority is None:
            raise RuntimeError("MCPS education authority must be seeded before Algebra I content")

        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        if curriculum is None:
            curriculum = Curriculum(
                code=CURRICULUM_CODE,
                name="MCPS Algebra 1 — SY 2026-27 Pilot",
                jurisdiction="Montgomery County, Maryland",
                grade_level="Algebra 1",
                authority_id=authority.id,
                version="SY2026-27",
                source_uri="https://www.montgomeryschoolsmd.org/curriculum/math/",
            )
            db.add(curriculum)
            db.flush()

        expressions = _skill(db, curriculum, "A1.EXPR", "Algebraic Expressions", "Interpret and simplify algebraic expressions.", 1)
        linear_equations = _skill(db, curriculum, "A1.LINEAR.EQ", "Linear Equations", "Solve one-variable linear equations and justify equivalent steps.", 2)
        linear_functions = _skill(db, curriculum, "A1.LINEAR.FN", "Linear Functions", "Represent and reason about linear relationships using equations, tables, and rates of change.", 3)

        _prerequisite(db, linear_equations, expressions)
        _prerequisite(db, linear_functions, linear_equations)

        problems = [
            (expressions, 1, "Simplify 4(x + 3).", "4x+12", "SIMPLIFY_EXPRESSION"),
            (expressions, 2, "Simplify 3x + 7 + 2x - 4.", "5x+3", "SIMPLIFY_EXPRESSION"),
            (linear_equations, 1, "Solve x + 9 = 21.", "x=12", "SOLVE_EQUATION"),
            (linear_equations, 2, "Solve 3x - 5 = 16.", "x=7", "SOLVE_EQUATION"),
            (linear_equations, 3, "Solve 2(x + 4) = 18.", "x=5", "SOLVE_EQUATION"),
            (linear_functions, 1, "A line has slope 3 and y-intercept 2. Write its equation in slope-intercept form.", "y=3x+2", "LINEAR_FUNCTION"),
            (linear_functions, 2, "For y = 4x - 1, what is y when x = 3?", "11", "LINEAR_FUNCTION"),
            (linear_functions, 3, "A taxi charges $4 plus $2 per mile. Write an equation for total cost y after x miles.", "y=2x+4", "WORD_PROBLEM"),
        ]
        for skill, difficulty, prompt, answer, problem_type in problems:
            _problem(db, skill, difficulty, prompt, answer, problem_type)

        db.commit()
        print(f"Algebra I pilot seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
