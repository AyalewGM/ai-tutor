from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import EducationAuthority
from app.models import Curriculum, Misconception, Problem, Skill, SkillPrerequisite

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

        # Fine-grained subskills gated by their strand anchors.
        expr_dist = _skill(db, curriculum, "A1.EXPR.DIST", "Distribution in Expressions", "Expand a(x + b) forms using the distributive property.", 1)
        expr_combine = _skill(db, curriculum, "A1.EXPR.COMBINE", "Combining Like Terms", "Combine like terms to simplify multi-term expressions.", 2)
        eq_one = _skill(db, curriculum, "A1.LINEAR.EQ.ONE", "One-Step Linear Equations", "Solve x + a = b and ax = b with a single inverse operation.", 2)
        eq_two = _skill(db, curriculum, "A1.LINEAR.EQ.TWO", "Two-Step and Multi-Step Linear Equations", "Solve ax + b = c and a(x + b) = c forms.", 3)
        fn_slope = _skill(db, curriculum, "A1.LINEAR.FN.SLOPE", "Slope-Intercept Form", "Write linear equations in y = mx + b from slope and intercept.", 3)
        fn_eval = _skill(db, curriculum, "A1.LINEAR.FN.EVAL", "Evaluating Linear Functions", "Evaluate a linear function for a given input.", 3)

        _prerequisite(db, expr_dist, expressions)
        _prerequisite(db, expr_combine, expr_dist)
        _prerequisite(db, eq_one, linear_equations)
        _prerequisite(db, eq_two, eq_one)
        _prerequisite(db, fn_slope, linear_functions)
        _prerequisite(db, fn_eval, fn_slope)

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
            linear_equations,
            "EQ_003",
            "Multiplies instead of dividing",
            "The learner multiplies both sides by the coefficient instead of "
            "dividing to isolate the variable.",
            "Undo multiplication with division: divide both sides by the "
            "coefficient of the variable.",
        )
        _misconception(
            linear_functions,
            "REL_002",
            "Coefficient added to variable",
            "The learner evaluates mx as m + x instead of multiplying the "
            "slope by the input value.",
            "Substitute the input into mx as multiplication: m times x, "
            "then add b.",
        )
        _misconception(
            expr_dist,
            "DIST_001",
            "Partial distribution",
            "The learner multiplies the outside factor by only one term "
            "inside parentheses.",
            "Represent the outside factor as multiplying each term separately "
            "before simplifying.",
        )
        _misconception(
            expr_combine,
            "ALG_001",
            "Unlike terms combined",
            "The learner merges constants into the variable term instead of "
            "combining like terms separately.",
            "Group variable terms with variable terms and constants with "
            "constants before simplifying.",
        )
        _misconception(
            eq_one,
            "EQ_003",
            "Multiplies instead of dividing",
            "The learner multiplies both sides by the coefficient instead of "
            "dividing to isolate the variable.",
            "Undo multiplication with division: divide both sides by the "
            "coefficient of the variable.",
        )
        _misconception(
            eq_two,
            "EQ_002",
            "Skipped or missequenced inverse step",
            "The learner undoes one operation but skips or reorders the other "
            "inverse step, such as forgetting to divide by the coefficient.",
            "Undo operations in reverse order: remove the added constant first, "
            "then divide by the coefficient.",
        )
        _misconception(
            fn_slope,
            "REL_001",
            "Slope and intercept swapped",
            "The learner writes the linear equation with the slope and "
            "y-intercept exchanged.",
            "Anchor the equation as y = mx + b and check which given value "
            "multiplies x and which stands alone.",
        )
        _misconception(
            fn_eval,
            "REL_002",
            "Coefficient added to variable",
            "The learner evaluates mx as m + x instead of multiplying the "
            "slope by the input value.",
            "Substitute the input into mx as multiplication: m times x, "
            "then add b.",
        )

        problems = [
            (expressions, 1, "Simplify 4(x + 3).", "4x+12", "SIMPLIFY_EXPRESSION"),
            (expressions, 2, "Simplify 3x + 7 + 2x - 4.", "5x+3", "SIMPLIFY_EXPRESSION"),
            (linear_equations, 1, "Solve x + 9 = 21.", "x=12", "SOLVE_EQUATION"),
            (linear_equations, 1, "Solve 5x = 30.", "x=6", "SOLVE_EQUATION"),
            (linear_equations, 2, "Solve 3x - 5 = 16.", "x=7", "SOLVE_EQUATION"),
            (linear_equations, 3, "Solve 2(x + 4) = 18.", "x=5", "SOLVE_EQUATION"),
            (linear_functions, 1, "A line has slope 3 and y-intercept 2. Write its equation in slope-intercept form.", "y=3x+2", "LINEAR_FUNCTION"),
            (linear_functions, 2, "For y = 4x - 1, what is y when x = 3?", "11", "LINEAR_FUNCTION"),
            (linear_functions, 3, "A taxi charges $4 plus $2 per mile. Write an equation for total cost y after x miles.", "y=2x+4", "WORD_PROBLEM"),
            (expr_dist, 1, "Simplify 5(x + 2).", "5x+10", "SIMPLIFY_EXPRESSION"),
            (expr_dist, 2, "Simplify 3(x - 4).", "3x-12", "SIMPLIFY_EXPRESSION"),
            (expr_combine, 2, "Simplify 6x + 1 - 2x + 5.", "4x+6", "SIMPLIFY_EXPRESSION"),
            (expr_combine, 3, "Simplify 8x - 4 - 3x + 2.", "5x-2", "SIMPLIFY_EXPRESSION"),
            (eq_one, 1, "Solve x + 5 = 14.", "x=9", "SOLVE_EQUATION"),
            (eq_one, 1, "Solve 7x = 49.", "x=7", "SOLVE_EQUATION"),
            (eq_two, 2, "Solve 4x + 1 = 21.", "x=5", "SOLVE_EQUATION"),
            (eq_two, 3, "Solve 3(x - 1) = 15.", "x=6", "SOLVE_EQUATION"),
            (fn_slope, 2, "A line has slope 5 and y-intercept -2. Write its equation.", "y=5x-2", "LINEAR_FUNCTION"),
            (fn_slope, 3, "A line has slope -3 and y-intercept 6. Write its equation.", "y=-3x+6", "LINEAR_FUNCTION"),
            (fn_eval, 2, "For y = 3x + 5, what is y when x = 4?", "17", "LINEAR_FUNCTION"),
            (fn_eval, 3, "For y = -2x + 7, what is y when x = 3?", "1", "LINEAR_FUNCTION"),
        ]
        for skill, difficulty, prompt, answer, problem_type in problems:
            _problem(db, skill, difficulty, prompt, answer, problem_type)

        db.commit()
        print(f"Algebra I pilot seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
