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


def _problem(
    db,
    skill: Skill,
    difficulty: int,
    prompt: str,
    answer: str,
    problem_type: str,
    *,
    answer_kind: str = "FREE_TEXT",
    parameters: dict | None = None,
    choices: list | None = None,
) -> None:
    provenance = {
        "origin": "AUTHORED",
        "author": "AI Tutor curriculum team",
        "license": "proprietary",
        "source_uri": "https://www.montgomeryschoolsmd.org/curriculum/math/",
    }
    existing = db.scalar(select(Problem).where(Problem.primary_skill_id == skill.id, Problem.prompt == prompt))
    solution = {"answer": answer, "provenance": provenance}
    if parameters is not None:
        solution["problem_family"] = problem_type
        solution["parameters"] = parameters
    if existing is None:
        db.add(
            Problem(
                primary_skill_id=skill.id,
                problem_type=problem_type,
                difficulty=difficulty,
                prompt=prompt,
                canonical_answer=answer,
                answer_kind=answer_kind,
                choices=choices,
                solution=solution,
                source_type="CURATED",
            )
        )
    elif parameters is not None and "parameters" not in (existing.solution or {}):
        existing.solution = {**(existing.solution or {}), **{k: v for k, v in solution.items() if k != "answer"}}
    elif "provenance" not in (existing.solution or {}):
        existing.solution = {**(existing.solution or {}), "provenance": provenance}


def seed_content(db, curriculum: Curriculum) -> None:
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
        quad_functions = _skill(db, curriculum, "A1.QUAD.FN", "Quadratic Functions", "Interpret and reason about quadratic relationships using equations and graphs.", 4)
        poly_functions = _skill(db, curriculum, "A1.POLY.FN", "Polynomial Functions", "Interpret polynomial functions: degree, zeros, end behavior, and graphs of factored forms.", 5)

        _prerequisite(db, expr_dist, expressions)
        _prerequisite(db, expr_combine, expr_dist)
        _prerequisite(db, eq_one, linear_equations)
        _prerequisite(db, eq_two, eq_one)
        _prerequisite(db, fn_slope, linear_functions)
        _prerequisite(db, fn_eval, fn_slope)
        _prerequisite(db, quad_functions, linear_functions)
        _prerequisite(db, poly_functions, quad_functions)

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
            eq_two,
            "EQ_001",
            "Inverse operation in wrong direction",
            "The learner applies the inverse operation in the wrong direction, "
            "for example adding the constant instead of subtracting it.",
            "Identify the operation applied to the variable and undo it with "
            "the opposite operation on both sides.",
        )
        _misconception(
            eq_two,
            "ARITH_001",
            "Arithmetic slip in isolation",
            "The learner applies the correct inverse operation but computes "
            "the result on the other side incorrectly.",
            "After applying an inverse operation, recompute the unaffected "
            "side carefully before moving on.",
        )
        _misconception(
            eq_one,
            "EQ_004",
            "Coefficient treated as addend",
            "The learner subtracts the coefficient from the constant as if "
            "3x meant x + 3 instead of 3 times x.",
            "Name the operation binding the variable: a coefficient multiplies "
            "the variable, so undo it with division.",
        )
        _misconception(
            expr_dist,
            "DIST_002",
            "Distribution sign error",
            "The learner distributes the factor but flips the sign of the "
            "constant term.",
            "Rewrite the product as a signed multiplication for each term, "
            "tracking the sign of both factors before simplifying.",
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
            fn_slope,
            "GR_001",
            "Slope inverted on a graph",
            "The learner reads run over rise instead of rise over run when "
            "measuring the slope of a graphed line.",
            "Trace one lattice step: count the vertical change first, then "
            "divide by the horizontal change.",
        )
        _misconception(
            fn_slope,
            "GR_002",
            "Slope sign misread",
            "The learner reports a positive slope for a line falling left to "
            "right, or a negative slope for a line rising.",
            "Read the line left to right: rising means positive slope, "
            "falling means negative.",
        )
        _misconception(
            fn_slope,
            "GR_003",
            "x-intercept mistaken for y-intercept",
            "The learner reports where the line crosses the x-axis when asked "
            "for the y-intercept.",
            "The y-intercept is the y-value where the line crosses the "
            "vertical axis — where x = 0.",
        )
        _misconception(
            fn_slope,
            "COORDINATE_ORDER_SWAP",
            "Coordinates listed in reverse order",
            "The learner reads a plotted point as (y, x) instead of (x, y).",
            "Run before you climb: the x-coordinate always comes first, "
            "then the y-coordinate.",
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
        _misconception(
            quad_functions,
            "QUAD_001",
            "Vertex x-coordinate sign error",
            "The learner reports or writes the vertex's x-coordinate with the "
            "opposite sign, treating y = a(x - h)^2 + k as if the shift were h "
            "rather than -h inside the parentheses.",
            "In y = a(x - h)^2 + k the vertex is (h, k): the minus inside the "
            "parentheses means h itself is the x-shift.",
        )
        _misconception(
            quad_functions,
            "QUAD_002",
            "Opening direction misread",
            "The learner reads an upward-opening parabola as downward or vice "
            "versa, usually by misreading the sign of the leading coefficient.",
            "Check the sign of a: positive opens upward, negative opens "
            "downward — or look at whether the arms rise or fall.",
        )
        _misconception(
            quad_functions,
            "QUAD_003",
            "Vertex coordinates swapped",
            "The learner interchanges the vertex's x- and y-coordinates, "
            "writing (k, h) instead of (h, k) or x = k for the axis.",
            "The axis of symmetry runs through the vertex's x-coordinate: "
            "x = h, and the vertex sits at (h, k).",
        )
        _misconception(
            poly_functions,
            "POLY_001",
            "Zero sign error",
            "The learner reads a factor (x - r) as giving the zero x = -r, "
            "keeping the sign shown inside the parentheses instead of solving "
            "x - r = 0.",
            "Set each factor equal to zero and solve: (x - r) = 0 gives "
            "x = r, so the zero has the opposite sign of what appears inside.",
        )
        _misconception(
            poly_functions,
            "POLY_002",
            "End-behavior parity confusion",
            "The learner describes end behavior without accounting for "
            "whether the degree is even or odd, or ignores the sign of the "
            "leading coefficient.",
            "Check two things: even degree means both ends go the same way, "
            "odd means opposite ways; then a positive leading coefficient "
            "rises to the right, negative falls.",
        )
        _misconception(
            poly_functions,
            "POLY_003",
            "Degree confused with term count",
            "The learner reports the number of terms or the leading "
            "coefficient as the degree instead of the greatest exponent.",
            "The degree is the largest exponent on the variable — count "
            "exponents, not terms.",
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

        # Graph-first items — parameters feed the coordinate-plane visual.
        graph_problems = [
            (
                fn_slope, 2, "What is the slope of the line shown?", "2",
                "LINEAR_GRAPH", "FRACTION",
                {"tier": "read_slope", "m_num": 2, "m_den": 1, "b": 3},
                None,
            ),
            (
                fn_slope, 3, "What is the y-intercept of the line shown?", "-2",
                "LINEAR_GRAPH", "INTEGER",
                {"tier": "read_intercept", "m_num": 1, "m_den": 2, "b": -2},
                None,
            ),
            (
                fn_eval, 3, "According to the graph, what is y when x = 2?", "5",
                "LINEAR_GRAPH", "INTEGER",
                {"tier": "read_value", "m_num": 2, "m_den": 1, "b": 1, "x": 2},
                None,
            ),
            (
                linear_functions, 3, "What is the slope of the line shown?", "-3/2",
                "LINEAR_GRAPH", "FRACTION",
                {"tier": "read_slope", "m_num": -3, "m_den": 2, "b": 4},
                None,
            ),
            (
                quad_functions, 3,
                "What are the coordinates of the vertex of the parabola shown?",
                "(2, -1)", "QUADRATIC_FUNCTION", "FREE_TEXT",
                {"tier": "vertex", "a_num": 1, "a_den": 1, "h": 2, "k": -1},
                None,
            ),
            (
                quad_functions, 2, "For f(x) = x^2 - 4x + 3, what is f(5)?", "8",
                "QUADRATIC_FUNCTION", "INTEGER",
                {"tier": "evaluate", "a_num": 1, "a_den": 1, "h": 2, "k": -1},
                None,
            ),
            (
                poly_functions, 2, "For p(x) = x^3 - 2x + 1, what is p(2)?", "5",
                "POLYNOMIAL_FUNCTION", "INTEGER",
                {"tier": "evaluate", "a": 0, "roots": [], "coeffs": [1, 0, -2, 1], "x": 2},
                None,
            ),
            (
                poly_functions, 3,
                "What are the zeros of f(x) = (x-1)(x+2)(x-3)?", "a",
                "POLYNOMIAL_FUNCTION", "MULTIPLE_CHOICE",
                {"tier": "zeros_from_factors", "a": 1, "roots": [-2, 1, 3], "coeffs": [1, 0, -7, 6]},
                [
                    {"id": "a", "text": "x = -2, x = 1, x = 3"},
                    {"id": "b", "text": "x = 2, x = -1, x = -3", "misconception_code": "POLY_001"},
                    {"id": "c", "text": "x = -2, x = 1"},
                    {"id": "d", "text": "x = -1, x = 2, x = 4"},
                ],
            ),
            (
                poly_functions, 4,
                "How many times does the graph cross the x-axis?", "b",
                "POLYNOMIAL_FUNCTION", "MULTIPLE_CHOICE",
                {"tier": "count_roots", "a": 1, "roots": [-2, 1, 3], "coeffs": [1, 0, -7, 6]},
                [
                    {"id": "a", "text": "2"},
                    {"id": "b", "text": "3"},
                    {"id": "c", "text": "1"},
                    {"id": "d", "text": "0"},
                ],
            ),
        ]
        for skill, difficulty, prompt, answer, ptype, answer_kind, parameters, choices in graph_problems:
            _problem(
                db, skill, difficulty, prompt, answer, ptype,
                answer_kind=answer_kind, parameters=parameters, choices=choices,
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

        seed_content(db, curriculum)

        db.commit()
        print(f"Algebra I pilot seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
