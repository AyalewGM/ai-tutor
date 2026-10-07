"""Canonical Grade 8–9 systems, polynomial, quadratic, and exponential families."""

from __future__ import annotations

import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(
    code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dims: str
) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dims))


FAMILIES = {
    "MATH.SYS.CHECK.SOLUTION": _spec("MATH.SYS.CHECK.SOLUTION", "Check a solution to a linear system", "MATH.EE.SYSTEMS", "SYSTEM_REASONING", 1, 3, "substitution", "reasoning"),
    "MATH.SYS.SOLVE.ELIMINATION": _spec("MATH.SYS.SOLVE.ELIMINATION", "Solve a system by elimination", "MATH.EE.SYSTEMS", "SOLVE_SYSTEM", 2, 4, "procedural_fluency", "reasoning"),
    "MATH.SYS.SOLVE.SUBSTITUTION": _spec("MATH.SYS.SOLVE.SUBSTITUTION", "Solve a system by substitution", "MATH.EE.SYSTEMS", "SOLVE_SYSTEM", 2, 4, "procedural_fluency", "reasoning"),
    "MATH.SYS.WORD.TOTAL": _spec("MATH.SYS.WORD.TOTAL", "Model a two-quantity total with a system", "MATH.EE.SYSTEMS", "WORD_PROBLEM", 2, 4, "modeling", "transfer"),
    "MATH.SYS.CLASSIFY": _spec("MATH.SYS.CLASSIFY", "Classify system solution count", "MATH.EE.SYSTEMS", "CLASSIFICATION", 2, 4, "conceptual_understanding", "representation"),
    "MATH.POLY.ADD": _spec("MATH.POLY.ADD", "Add linear polynomials", "MATH.EE.POLYNOMIAL_OPERATIONS", "POLYNOMIAL", 1, 3, "procedural_fluency", "structure_identification"),
    "MATH.POLY.SUB": _spec("MATH.POLY.SUB", "Subtract linear polynomials", "MATH.EE.POLYNOMIAL_OPERATIONS", "POLYNOMIAL", 1, 3, "procedural_fluency", "sign_reasoning"),
    "MATH.POLY.MULT.MONOMIAL": _spec("MATH.POLY.MULT.MONOMIAL", "Multiply a monomial and binomial", "MATH.EE.POLYNOMIAL_OPERATIONS", "POLYNOMIAL", 2, 4, "procedural_fluency", "distributive_property"),
    "MATH.POLY.MULT.BINOMIAL": _spec("MATH.POLY.MULT.BINOMIAL", "Multiply two binomials", "MATH.EE.POLYNOMIAL_OPERATIONS", "POLYNOMIAL", 2, 4, "procedural_fluency", "structure_identification"),
    "MATH.POLY.FACTOR.GCF": _spec("MATH.POLY.FACTOR.GCF", "Factor a greatest common factor", "MATH.EE.POLYNOMIAL_OPERATIONS", "FACTOR", 2, 4, "procedural_fluency", "structure_identification"),
    "MATH.POLY.ERROR.DISTRIBUTE": _spec("MATH.POLY.ERROR.DISTRIBUTE", "Diagnose incomplete polynomial distribution", "MATH.EE.POLYNOMIAL_OPERATIONS", "ERROR_ANALYSIS", 2, 4, "error_analysis", "misconception_probe"),
    "MATH.QUAD.EVALUATE": _spec("MATH.QUAD.EVALUATE", "Evaluate a quadratic function", "MATH.F.QUADRATIC.INTERPRET", "FUNCTION_EVALUATION", 1, 4, "procedural_fluency", "representation"),
    "MATH.QUAD.ROOTS.FACTORED": _spec("MATH.QUAD.ROOTS.FACTORED", "Find roots from factored form", "MATH.F.QUADRATIC.INTERPRET", "QUADRATIC", 2, 4, "inverse_operations", "structure_identification"),
    "MATH.QUAD.VERTEX.SYMMETRY": _spec("MATH.QUAD.VERTEX.SYMMETRY", "Interpret a quadratic vertex", "MATH.F.QUADRATIC.INTERPRET", "QUADRATIC_REASONING", 2, 4, "representation", "reasoning"),
    "MATH.QUAD.COMPARE.LINEAR": _spec("MATH.QUAD.COMPARE.LINEAR", "Distinguish quadratic and linear growth", "MATH.F.QUADRATIC.INTERPRET", "CLASSIFICATION", 2, 4, "conceptual_understanding", "pattern_reasoning"),
    "MATH.QUAD.ERROR.ROOT_SIGN": _spec("MATH.QUAD.ERROR.ROOT_SIGN", "Diagnose root-sign error", "MATH.F.QUADRATIC.INTERPRET", "ERROR_ANALYSIS", 2, 4, "error_analysis", "misconception_probe"),
    "MATH.EXPFUNC.EVALUATE": _spec("MATH.EXPFUNC.EVALUATE", "Evaluate an exponential function", "MATH.F.EXPONENTIAL", "FUNCTION_EVALUATION", 2, 4, "procedural_fluency", "representation"),
    "MATH.EXPFUNC.GROWTH.FACTOR": _spec("MATH.EXPFUNC.GROWTH.FACTOR", "Identify exponential growth factor", "MATH.F.EXPONENTIAL", "FUNCTION_REASONING", 2, 4, "conceptual_understanding", "pattern_reasoning"),
    "MATH.EXPFUNC.COMPARE.LINEAR": _spec("MATH.EXPFUNC.COMPARE.LINEAR", "Compare exponential and linear patterns", "MATH.F.EXPONENTIAL", "CLASSIFICATION", 2, 4, "conceptual_understanding", "pattern_reasoning"),
    "MATH.EXPFUNC.MODEL": _spec("MATH.EXPFUNC.MODEL", "Build an exponential growth model", "MATH.F.EXPONENTIAL", "MODEL_EQUATION", 3, 4, "modeling", "representation"),
}


def _system(rng: random.Random) -> tuple[int, int, int, int]:
    x = rng.randint(-5, 8)
    y = rng.randint(-5, 8)
    a = rng.choice([1, 2, 3, 4])
    b = rng.choice([1, 2, 3, 4])
    return x, y, a, b


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.SYS.CHECK.SOLUTION":
        x, y, a, b = _system(rng)
        c1, c2 = a * x + y, x - b * y
        return (
            f"Does ({x},{y}) solve the system {a}x+y={c1} and x-{b}y={c2}? Answer yes or no.",
            "yes",
            ("Substitute the ordered pair into both equations.", "A system solution must satisfy both equations."),
            {"SYS.CHECK.ONE_EQUATION_ONLY": "no"},
        )
    if family_code in {"MATH.SYS.SOLVE.ELIMINATION", "MATH.SYS.SOLVE.SUBSTITUTION"}:
        x, y, a, b = _system(rng)
        if family_code == "MATH.SYS.SOLVE.ELIMINATION":
            c1, c2 = a * x + y, a * x - y
            return (
                f"Solve the system {a}x+y={c1} and {a}x-y={c2}. Give x,y.",
                f"{x},{y}",
                ("Add the equations to eliminate y.", "Solve for x, then substitute to find y."),
                {"SYS.ELIMINATION.ADD_COORDINATES": f"{x+y},{y}"},
            )
        c1, c2 = y - a * x, x + b * y
        return (
            f"Solve the system y={a}x+({c1}) and x+{b}y={c2}. Give x,y.",
            f"{x},{y}",
            ("Substitute the expression for y into the second equation.", "Solve for x, then evaluate y."),
            {"SYS.SUBSTITUTION.STOP_EARLY": str(x)},
        )
    if family_code == "MATH.SYS.WORD.TOTAL":
        adult = rng.randint(4, 12)
        child = rng.randint(3, 10)
        total = adult + child
        revenue = 10 * adult + 6 * child
        return (
            f"At an event, adult tickets cost 10 and child tickets cost 6. "
            f"There are {total} tickets totaling {revenue}. How many adult tickets were sold?",
            str(adult),
            (f"Let a+c={total}.", f"Use 10a+6c={revenue} as the second equation."),
            {"SYS.WORD.DIVIDE_REVENUE_BY_ADULT_PRICE": str(revenue // 10)},
        )
    if family_code == "MATH.SYS.CLASSIFY":
        case = rng.choice(["one", "none", "infinite"])
        m = rng.choice([2, 3, 4])
        b = rng.randint(1, 6)
        if case == "one":
            m2 = m + 1
            prompt = f"Classify the system y={m}x+{b} and y={m2}x+{b}: one, none, or infinite solutions."
        elif case == "none":
            prompt = f"Classify the system y={m}x+{b} and y={m}x+{b+2}: one, none, or infinite solutions."
        else:
            prompt = f"Classify the system y={m}x+{b} and 2y={2*m}x+{2*b}: one, none, or infinite solutions."
        return (
            prompt,
            case,
            ("Compare slopes and intercepts.", "Different slopes intersect once; equal slopes are parallel or identical."),
            {"SYS.CLASSIFY.PARALLEL_ALWAYS": "none" if case != "none" else "one"},
        )
    if family_code in {"MATH.POLY.ADD", "MATH.POLY.SUB"}:
        a, b, c, d = [rng.randint(1, 8) for _ in range(4)]
        if family_code == "MATH.POLY.ADD":
            return (
                f"Simplify ({a}x+{b})+({c}x+{d}).",
                f"{a+c}x+{b+d}",
                ("Combine x-terms with x-terms.", "Combine constants with constants."),
                {"POLY.ADD.ALL_COEFFICIENTS": f"{a+b+c+d}x"},
            )
        return (
            f"Simplify ({a}x+{b})-({c}x+{d}).",
            f"{a-c}x+{b-d}",
            ("Distribute the subtraction to both terms in the second polynomial.", "Then combine like terms."),
            {"POLY.SUB.FAIL_DISTRIBUTE": f"{a-c}x+{b+d}"},
        )
    if family_code == "MATH.POLY.MULT.MONOMIAL":
        k, a, b = rng.randint(2, 7), rng.randint(2, 8), rng.randint(1, 9)
        return (
            f"Expand {k}x({a}x+{b}).",
            f"{k*a}x^2+{k*b}x",
            ("Distribute the monomial to every term.", "Multiply coefficients and variable factors."),
            {"POLY.DISTRIBUTE.ONE_TERM": f"{k*a}x^2+{b}x"},
        )
    if family_code == "MATH.POLY.MULT.BINOMIAL":
        a, b = rng.randint(1, 7), rng.randint(1, 7)
        return (
            f"Expand (x+{a})(x+{b}).",
            f"x^2+{a+b}x+{a*b}",
            ("Multiply every term in the first binomial by every term in the second.", "Combine the two middle x-terms."),
            {"POLY.BINOMIAL.OMIT_MIDDLE": f"x^2+{a*b}"},
        )
    if family_code == "MATH.POLY.FACTOR.GCF":
        g, a, b = rng.randint(2, 8), rng.randint(2, 7), rng.randint(1, 9)
        return (
            f"Factor the greatest common factor from {g*a}x^2+{g*b}x.",
            f"{g}x({a}x+{b})",
            ("Both terms share a numerical factor and x.", "Divide each term by the common factor."),
            {"POLY.FACTOR.NUMERIC_ONLY": f"{g}({a}x^2+{b}x)"},
        )
    if family_code == "MATH.POLY.ERROR.DISTRIBUTE":
        k, a, b = rng.randint(2, 6), rng.randint(2, 7), rng.randint(1, 8)
        return (
            f"A student expands {k}x({a}x+{b}) as {k*a}x^2+{b}x. "
            f"Which response is correct? (A) The second term should be {k*b}x. "
            "(B) The student is correct. (C) The first term should lose x^2. (D) Only constants distribute.",
            "A",
            ("Distribution applies to every term inside the parentheses.", "The monomial multiplies the constant term too."),
            {"POLY.DISTRIBUTE.ONE_TERM": "B"},
        )
    if family_code == "MATH.QUAD.EVALUATE":
        a = rng.choice([1, 2, 3])
        b, c, x = rng.randint(-5, 5), rng.randint(-6, 6), rng.randint(-4, 4)
        value = a * x * x + b * x + c
        return (
            f"For f(x)={a}x^2+({b})x+({c}), find f({x}).",
            str(value),
            ("Substitute the input everywhere x appears.", "Square x before multiplying by the leading coefficient."),
            {"QUAD.EVAL.FORGET_SQUARE": str(a * x + b * x + c)},
        )
    if family_code == "MATH.QUAD.ROOTS.FACTORED":
        r1, r2 = rng.sample(range(-6, 7), 2)
        return (
            f"Find the roots of (x-({r1}))(x-({r2}))=0. Give smaller,larger.",
            f"{min(r1,r2)},{max(r1,r2)}",
            ("Use the zero-product property.", "Set each factor equal to zero."),
            {"QUAD.ROOT_SIGN": f"{min(-r1,-r2)},{max(-r1,-r2)}"},
        )
    if family_code == "MATH.QUAD.VERTEX.SYMMETRY":
        h, k = rng.randint(-5, 5), rng.randint(-5, 8)
        return (
            f"For y=(x-({h}))^2+({k}), give the vertex as x,y.",
            f"{h},{k}",
            ("Compare with vertex form y=(x-h)^2+k.", "The vertex is (h,k)."),
            {"QUAD.VERTEX.SIGN": f"{-h},{k}"},
        )
    if family_code == "MATH.QUAD.COMPARE.LINEAR":
        return (
            "Which table is quadratic? (A) x=0,1,2,3; y=1,4,9,16. "
            "(B) x=0,1,2,3; y=1,4,7,10.",
            "A",
            ("Linear tables have constant first differences.", "Quadratic tables have constant second differences."),
            {"QUAD.LINEAR.CONFUSION": "B"},
        )
    if family_code == "MATH.QUAD.ERROR.ROOT_SIGN":
        r = rng.randint(2, 8)
        return (
            f"A student says the root of x-{r}=0 is -{r}. Which response is correct? "
            f"(A) The root is {r}. (B) The student is correct. (C) The root is 0. (D) There is no root.",
            "A",
            ("Set the factor equal to zero.", f"Add {r} to both sides."),
            {"QUAD.ROOT_SIGN": "B"},
        )
    if family_code == "MATH.EXPFUNC.EVALUATE":
        initial = rng.randint(2, 8)
        factor = rng.randint(2, 4)
        x = rng.randint(2, 5)
        return (
            f"For f(x)={initial}({factor}^x), find f({x}).",
            str(initial * factor**x),
            ("Evaluate the power first.", "Then multiply by the initial value."),
            {"EXPFUNC.MULTIPLY_EXPONENT": str(initial * factor * x)},
        )
    if family_code == "MATH.EXPFUNC.GROWTH.FACTOR":
        start, factor = rng.randint(2, 7), rng.randint(2, 5)
        values = [start * factor**n for n in range(4)]
        return (
            f"The sequence is {values}. What is the constant multiplicative growth factor?",
            str(factor),
            ("Compare each term with the preceding term.", "Exponential growth has a constant ratio."),
            {"EXPFUNC.USE_DIFFERENCE": str(values[1] - values[0])},
        )
    if family_code == "MATH.EXPFUNC.COMPARE.LINEAR":
        return (
            "Which pattern is exponential? (A) 3,6,12,24 (B) 3,6,9,12.",
            "A",
            ("Exponential patterns have a constant multiplicative factor.", "Linear patterns have a constant additive difference."),
            {"EXPFUNC.CONFUSE_DIFFERENCE": "B"},
        )
    if family_code == "MATH.EXPFUNC.MODEL":
        initial, factor = rng.randint(2, 9), rng.randint(2, 4)
        return (
            f"A quantity starts at {initial} and is multiplied by {factor} each period. "
            "Which model gives the amount A after t periods?",
            f"A={initial}({factor}^t)",
            ("The initial value multiplies the growth factor.", "Repeated multiplication is represented by an exponent."),
            {"EXPFUNC.MODEL.LINEAR": f"A={initial}+{factor}t"},
        )
    raise ValueError(f"No Grade 8–9 algebra builder for family: {family_code}")
