import random
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Problem


def _module_contextualizer():
    from app.services import problem_contextualizer

    return problem_contextualizer.contextualizer


def _metered_contextualize(
    db: Session,
    contextualizer,
    *,
    template: str,
    parameters: dict,
    canonical_answer: str,
    student_id: uuid.UUID | None,
    session_id: uuid.UUID | None,
):
    """Contextualizer call through the same budget gate + ledger as tutor
    generations. Denied calls fall back to the template prompt, and a
    successful narrative is billed with estimated tokens (the gateway does
    not report usage). Returns the narrative result or None."""
    from app.models import Student, TutorSession
    from app.services.tutor_engine import TutorEngineResult
    from app.services.usage_metering import (
        check_ai_budget,
        record_ai_usage,
        record_budget_denial,
    )

    resolved_student_id = student_id
    if resolved_student_id is None and session_id is not None:
        tut_session = db.get(TutorSession, session_id)
        resolved_student_id = tut_session.student_id if tut_session else None
    family_user_id = None
    if resolved_student_id is not None:
        student = db.get(Student, resolved_student_id)
        family_user_id = student.parent_id if student else None

    if not check_ai_budget(db, family_user_id):
        record_budget_denial(
            db,
            family_user_id=family_user_id,
            student_id=resolved_student_id,
            session_id=session_id,
            action="contextualize",
        )
        return None
    narrative = contextualizer.contextualize(
        template=template,
        parameters=parameters,
        canonical_answer=canonical_answer,
    )
    if narrative is not None:
        record_ai_usage(
            db,
            family_user_id=family_user_id,
            student_id=resolved_student_id,
            session_id=session_id,
            action="contextualize",
            result=TutorEngineResult(
                message=narrative.prompt,
                source="llm",
                provider=narrative.provider,
                model=narrative.model,
            ),
        )
    return narrative


@dataclass(frozen=True)
class GeneratedProblem:
    prompt: str
    canonical_answer: str
    difficulty: int
    problem_type: str
    context: dict | None = None
    parameters: dict | None = None
    answer_kind: str = "FREE_TEXT"
    choices: list | None = None


def _fmt_term(coefficient: int, variable: str) -> str:
    if coefficient == 1:
        return variable
    if coefficient == -1:
        return f"-{variable}"
    return f"{coefficient}{variable}"


def _fmt_expr(coefficient: int, constant: int, variable: str = "x") -> str:
    lead = _fmt_term(coefficient, variable)
    if constant == 0:
        return lead
    return f"{lead}{constant:+d}"


def _generate_simplify_expression(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 3:
        a = rng.randint(2, 9)
        b = rng.randint(1, 12)
        sign = "+" if difficulty <= 2 or rng.random() < 0.5 else "-"
        prompt = f"{a}(x{sign}{b})"
        answer = _fmt_expr(a, a * b if sign == "+" else -a * b)
        parameters = {"a": a, "b": b, "sign": sign}
    else:
        a, c = rng.randint(2, 9), rng.randint(2, 9)
        b = rng.randint(-9, 9)
        d = rng.randint(-9, 9)
        prompt = f"{_fmt_expr(a, b)} + {_fmt_expr(c, d)}"
        prompt = prompt.replace("+ -", "- ")
        answer = _fmt_expr(a + c, b + d)
        parameters = {"a": a, "b": b, "c": c, "d": d}
    return GeneratedProblem(
        prompt, answer, difficulty, "SIMPLIFY_EXPRESSION", parameters=parameters
    )


def _generate_combine_like_terms(rng: random.Random, difficulty: int) -> GeneratedProblem:
    variable = rng.choice(["x", "y", "n"])
    a = rng.randint(-9, 9)
    b = rng.randint(-9, 9)
    while a == 0 or b == 0:
        a = rng.randint(-9, 9)
        b = rng.randint(-9, 9)
    constant = rng.randint(-9, 9) if difficulty >= 3 else 0
    terms = [f"{_fmt_term(a, variable)}", f"{_fmt_term(b, variable)}"]
    if constant:
        terms.append(str(constant))
    prompt = "Simplify " + " + ".join(terms).replace("+ -", "- ") + "."
    answer = _fmt_expr(a + b, constant, variable)
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "COMBINE_LIKE_TERMS",
        parameters={"a": a, "b": b, "constant": constant, "variable": variable},
    )


def _generate_polynomial_add_subtract(rng: random.Random, difficulty: int) -> GeneratedProblem:
    variable = rng.choice(["x", "y"])
    a, b = rng.randint(-6, 6), rng.randint(-9, 9)
    c, d = rng.randint(-6, 6), rng.randint(-9, 9)
    while a == 0 or c == 0:
        a, c = rng.randint(-6, 6), rng.randint(-6, 6)
    operation = "-" if difficulty >= 3 and rng.random() < 0.6 else "+"
    left = _fmt_expr(a, b, variable)
    right = _fmt_expr(c, d, variable)
    prompt = f"Simplify ({left}) {operation} ({right})."
    if operation == "+":
        coefficient, constant = a + c, b + d
    else:
        coefficient, constant = a - c, b - d
    answer = _fmt_expr(coefficient, constant, variable)
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "POLYNOMIAL_ADD_SUBTRACT",
        parameters={
            "a": a,
            "b": b,
            "c": c,
            "d": d,
            "operation": operation,
            "variable": variable,
        },
    )


def _generate_solve_equation(rng: random.Random, difficulty: int) -> GeneratedProblem:
    x = rng.randint(-12, 12) if difficulty >= 4 else rng.randint(1, 12)
    if difficulty <= 1:
        b = rng.randint(1, 20)
        prompt = f"x + {b} = {x + b}"
        parameters = {"tier": "add_inverse", "b": b, "x": x}
    elif difficulty == 2:
        a = rng.randint(2, 9)
        prompt = f"{a}x = {a * x}"
        parameters = {"tier": "coefficient", "a": a, "x": x}
    elif difficulty <= 4:
        a, b = rng.randint(2, 9), rng.randint(1, 15)
        prompt = f"{_fmt_expr(a, b)} = {a * x + b}"
        parameters = {"tier": "two_step", "a": a, "b": b, "x": x}
    elif difficulty == 5:
        a, b = rng.randint(2, 6), rng.randint(-9, 9)
        prompt = f"{a}({_fmt_expr(1, b)}) = {a * (x + b)}"
        parameters = {"tier": "distribute_equation", "a": a, "b": b, "x": x}
    else:
        # Ontario MTH1W classroom progression: simplify first, then collect
        # variable terms on one side and constants on the other.  Generate an
        # equation with variables on both sides and, at the highest tier,
        # a bracket that must be distributed before solving.
        a = rng.randint(2, 7)
        c = rng.randint(1, a - 1)
        b = rng.randint(-9, 12)
        d = (a - c) * x + b
        if difficulty >= 7:
            k = rng.randint(2, 4)
            inner_b = rng.randint(-5, 6)
            left_constant = k * inner_b + b
            d = (k - c) * x + left_constant
            while k == c:
                c = rng.randint(1, 6)
                d = (k - c) * x + left_constant
            prompt = f"{k}(x {'+' if inner_b >= 0 else '-'} {abs(inner_b)}) {'+' if b >= 0 else '-'} {abs(b)} = {_fmt_expr(c, d)}"
            parameters = {
                "tier": "brackets_both_sides",
                "k": k,
                "inner_b": inner_b,
                "b": b,
                "c": c,
                "x": x,
            }
        else:
            prompt = f"{_fmt_expr(a, b)} = {_fmt_expr(c, d)}"
            parameters = {"tier": "variables_both_sides", "a": a, "b": b, "c": c, "d": d, "x": x}
    return GeneratedProblem(prompt, f"x={x}", difficulty, "SOLVE_EQUATION", parameters=parameters)


def _generate_linear_function(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        m = rng.randint(1, 8)
        b = rng.randint(-8, 8) if difficulty == 2 else rng.randint(0, 8)
        prompt = (
            f"A line has slope {m} and y-intercept {b}. Write its equation in slope-intercept form."
        )
        answer = f"y={_fmt_expr(m, b)}"
        parameters = {"tier": "write_slope_intercept", "m": m, "b": b}
    else:
        m = rng.randint(-8, 8)
        b = rng.randint(-9, 9)
        x = rng.randint(-6, 6)
        prompt = f"For y = {_fmt_expr(m, b)}, what is y when x = {x}?"
        answer = str(m * x + b)
        parameters = {"tier": "evaluate", "m": m, "b": b, "x": x}
    return GeneratedProblem(prompt, answer, difficulty, "LINEAR_FUNCTION", parameters=parameters)


def _linear_graph_params(
    rng: random.Random, difficulty: int, *, integer_slope: bool = False
) -> tuple[int, int, int]:
    """(m_num, m_den, b) for a line y = (m_num/m_den)x + b.

    The slope is a reduced fraction and the intercept is integer; parameters are
    constrained so the lattice points one slope-step each side of the
    y-intercept stay on the ±9 grid the visual renders.
    """
    denominators = [1] if difficulty <= 2 or integer_slope else [1, 1, 2, 3]
    while True:
        den = rng.choice(denominators)
        num = rng.randint(-5, 5)
        if num == 0 or Fraction(num, den).denominator != den:
            continue
        b = rng.randint(-6, 6)
        if -9 <= b - num <= 9 and -9 <= b + num <= 9:
            return num, den, b


def _slope_text(num: int, den: int) -> str:
    return str(num) if den == 1 else f"{num}/{den}"


def _equation_text(m: int, b: int) -> str:
    return f"y={_fmt_expr(m, b)}"


def _mc_choices(
    rng: random.Random, correct: str, distractors: list[tuple[str, str | None]]
) -> tuple[list[dict], str]:
    """Build the four-option choice list; returns (choices, correct_id)."""
    seen = {correct}
    unique: list[tuple[str, str | None]] = []
    for text, code in distractors:
        if text not in seen:
            seen.add(text)
            unique.append((text, code))
    options = unique[:3] + [(correct, None)]
    rng.shuffle(options)
    choices = [
        {
            "id": chr(ord("a") + i),
            "text": text,
            **({"misconception_code": code} if code else {}),
        }
        for i, (text, code) in enumerate(options)
    ]
    return choices, next(c["id"] for c in choices if c["text"] == correct)


def _generate_linear_graph(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Graph-first linear-function items: read slope/intercept/values off a
    plotted line, pick the point on the line, or match the line's equation.

    The m_num/m_den/b parameters drive the coordinate-plane visual, so the
    prompt is always answered from the rendered graph — never from the text.
    """
    tiers = ["read_intercept", "read_slope"]
    if difficulty >= 3:
        tiers += ["read_value", "point_on_line"]
    if difficulty >= 5:
        tiers.append("write_equation")
    tier = rng.choice(tiers)
    num, den, b = _linear_graph_params(
        rng, difficulty, integer_slope=(tier == "write_equation")
    )
    params: dict = {"tier": tier, "m_num": num, "m_den": den, "b": b}
    prompt: str
    answer: str
    kind = "FREE_TEXT"
    choices = None

    if tier == "read_slope":
        prompt = "What is the slope of the line shown?"
        answer = _slope_text(num, den)
        kind = "FRACTION"
    elif tier == "read_intercept":
        prompt = "What is the y-intercept of the line shown?"
        answer = str(b)
        kind = "INTEGER"
    elif tier == "read_value":
        ks = [k for k in (-3, -2, -1, 1, 2, 3) if abs(k * den) <= 9 and abs(b + k * num) <= 9]
        if not ks:
            return _generate_linear_graph(rng, difficulty)
        k = rng.choice(ks)
        x = k * den
        y = b + k * num
        params["x"] = x
        prompt = f"According to the graph, what is y when x = {x}?"
        answer = str(y)
        kind = "INTEGER"
    elif tier == "point_on_line":
        ks = [k for k in (-3, -2, -1, 1, 2, 3) if abs(k * den) <= 9 and abs(b + k * num) <= 9]
        if not ks:
            return _generate_linear_graph(rng, difficulty)
        k = rng.choice(ks)
        x = k * den
        y = b + k * num
        params["x"] = x
        correct_text = f"({x}, {y})"
        distractors = [
            (f"({y}, {x})", "COORDINATE_ORDER_SWAP"),
            (f"({x}, {b - k * num})", "GR_002"),  # stepped the wrong direction
            (f"({x + den}, {y})", None),
        ]
        prompt = "Which ordered pair is a point on this line?"
        choices, answer = _mc_choices(rng, correct_text, distractors)
        kind = "MULTIPLE_CHOICE"
    else:  # write_equation — integer slopes only
        correct_text = _equation_text(num, b)
        distractors = [
            (f"y={_fmt_expr(-num, b)}", "GR_002"),
            (_equation_text(num + 1, b), None),
            (_equation_text(num, b + 1 if b < 6 else b - 1), None),
        ]
        if b != 0 and b != num:
            distractors.insert(0, (_equation_text(b, num), "REL_001"))
        if b % num == 0 and b != 0:
            distractors.insert(0, (_equation_text(num, -b // num), "GR_003"))
        prompt = "Which equation describes the line shown?"
        choices, answer = _mc_choices(rng, correct_text, distractors)
        kind = "MULTIPLE_CHOICE"

    return GeneratedProblem(
        prompt, answer, difficulty, "LINEAR_GRAPH",
        parameters=params, answer_kind=kind, choices=choices,
    )


def _quad_params(rng: random.Random, *, integer_a: bool = False) -> tuple[int, int, int, int]:
    """(a_num, a_den, h, k) for y = (a_num/a_den)(x - h)^2 + k.

    The points one horizontal step either side of the vertex must stay inside
    the ±9 grid the visual renders so the curve is never asked about off-screen.
    """
    while True:
        if integer_a:
            num, den = rng.choice([-2, -1, 1, 2]), 1
        else:
            num, den = rng.choice([(-2, 1), (-1, 1), (1, 1), (2, 1), (-1, 2), (1, 2)])
        h = rng.randint(-5, 5)
        k = rng.randint(-6, 6)
        if abs(k + num / den) <= 9:
            return num, den, h, k


def _vertex_form_text(a: int, h: int, k: int) -> str:
    coeff = "" if a == 1 else "-" if a == -1 else str(a)
    inner = "x^2" if h == 0 else f"(x{'+' if h < 0 else '-'}{abs(h)})^2"
    if k == 0:
        return f"y={coeff}{inner}"
    return f"y={coeff}{inner}{'+' if k > 0 else '-'}{abs(k)}"


def _generate_quadratic_function(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Graph-first quadratic items: open direction, vertex, x-intercept count,
    axis of symmetry, equation-from-graph — plus text-only evaluation.

    a_num/a_den/h/k drive the parabola visual; graph tiers are always read
    from the rendered curve, never from the prompt.
    """
    tiers = ["evaluate", "opens_direction"]
    if difficulty >= 3:
        tiers += ["vertex", "count_roots"]
    if difficulty >= 4:
        tiers.append("axis_of_symmetry")
    if difficulty >= 5:
        tiers.append("write_equation")
    tier = rng.choice(tiers)
    num, den, h, k = _quad_params(
        rng, integer_a=tier in {"evaluate", "write_equation"}
    )
    a = num / den
    params: dict = {"tier": tier, "a_num": num, "a_den": den, "h": h, "k": k}
    kind = "FREE_TEXT"
    choices = None

    if tier == "evaluate":
        b_std = -2 * num * h
        c_std = num * h * h + k
        x_val = rng.randint(-4, 4)
        answer_val = num * x_val * x_val + b_std * x_val + c_std
        a_txt = "" if num == 1 else "-" if num == -1 else str(num)
        terms = f"{a_txt}x^2"
        if b_std:
            terms += f"{'+' if b_std > 0 else '-'}{abs(b_std) if abs(b_std) != 1 else ''}x"
        if c_std:
            terms += f"{'+' if c_std > 0 else '-'}{abs(c_std)}"
        prompt = f"For f(x) = {terms}, what is f({x_val})?"
        answer = str(answer_val)
        kind = "INTEGER"
    elif tier == "opens_direction":
        correct = "Upward" if a > 0 else "Downward"
        distractors = [
            ("Downward" if a > 0 else "Upward", "QUAD_002"),
            ("To the left", None),
            ("To the right", None),
        ]
        prompt = "The parabola shown opens in which direction?"
        choices, answer = _mc_choices(rng, correct, distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "vertex":
        prompt = "What are the coordinates of the vertex of the parabola shown?"
        answer = f"({h}, {k})"
    elif tier == "count_roots":
        roots = 1 if k == 0 else (2 if (a > 0) == (k < 0) else 0)
        choices, answer = _mc_choices(
            rng, str(roots), [(str(n), None) for n in range(4) if n != roots]
        )
        prompt = "How many times does the parabola cross the x-axis?"
        kind = "MULTIPLE_CHOICE"
    elif tier == "axis_of_symmetry":
        distractors = [
            (f"x={k}" if k != h else f"x={k + 1}", "QUAD_003"),
            (f"y={k}", None),
        ]
        if h != 0:
            distractors.insert(0, (f"x={-h}", "QUAD_001"))
        else:
            distractors.append(("x=1", None))
        prompt = "What is the equation of the parabola's axis of symmetry?"
        choices, answer = _mc_choices(rng, f"x={h}", distractors)
        kind = "MULTIPLE_CHOICE"
    else:  # write_equation — integer a only
        correct_text = _vertex_form_text(num, h, k)
        distractors = [
            (_vertex_form_text(-num, h, k), "QUAD_002"),
            (_vertex_form_text(num, -h, k), "QUAD_001"),
        ]
        if h != k:
            distractors.append((_vertex_form_text(num, k, h), "QUAD_003"))
        prompt = "Which equation describes the parabola shown?"
        choices, answer = _mc_choices(rng, correct_text, distractors)
        kind = "MULTIPLE_CHOICE"

    return GeneratedProblem(
        prompt, answer, difficulty, "QUADRATIC_FUNCTION",
        parameters=params, answer_kind=kind, choices=choices,
    )


def _poly_expand(a: int, roots: list[int]) -> list[int]:
    """Coefficients of a·∏(x - r), highest degree first."""
    coeffs = [a]
    for r in roots:
        out = [0] * (len(coeffs) + 1)
        for i, c in enumerate(coeffs):
            out[i] += c
            out[i + 1] -= c * r
        coeffs = out
    return coeffs


def _poly_val(coeffs: list[int], x: float) -> float:
    total = 0.0
    for c in coeffs:
        total = total * x + c
    return total


def _poly_text(coeffs: list[int]) -> str:
    degree = len(coeffs) - 1
    parts: list[str] = []
    for i, c in enumerate(coeffs):
        if c == 0:
            continue
        power = degree - i
        var = "" if power == 0 else "x" if power == 1 else f"x^{power}"
        mag = var if var and abs(c) == 1 else f"{abs(c)}{var}"
        if not parts:
            parts.append(f"-{mag}" if c < 0 else mag)
        else:
            parts.append(f"{'+' if c > 0 else '-'}{mag}")
    return "".join(parts) or "0"


def _factor_text(r: int) -> str:
    return "x" if r == 0 else f"(x{'+' if r < 0 else '-'}{abs(r)})"


def _poly_graph_params(rng: random.Random, n_roots: int) -> tuple[int, list[int], list[int]]:
    """(a, roots, coeffs) for a graphed polynomial in factored form.

    Roots are distinct integers inside the window and every local extremum
    between them stays within ±9 so the curve's turning points and crossings
    are all readable on the rendered graph.
    """
    while True:
        roots = sorted(rng.sample(range(-4, 5), n_roots))
        a = rng.choice([-1, 1])
        coeffs = _poly_expand(a, roots)
        lo, hi = roots[0] - 1.2, roots[-1] + 1.2
        if all(abs(_poly_val(coeffs, lo + i * 0.02)) <= 9 for i in range(int((hi - lo) / 0.02) + 1)):
            return a, roots, coeffs


_END_BEHAVIOR = {
    (True, 1): "Rises to the left and rises to the right",
    (True, -1): "Falls to the left and falls to the right",
    (False, 1): "Falls to the left and rises to the right",
    (False, -1): "Rises to the left and falls to the right",
}


def _generate_polynomial_function(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Polynomial items: evaluate/degree on text, zeros from factored form,
    graph reads (crossing count, equation match) and end behavior.

    roots + a own the truth; coeffs are the expanded coefficients the
    renderer samples — the frontend never computes roots itself.
    """
    tiers = ["evaluate", "degree"]
    if difficulty >= 3:
        tiers += ["zeros_from_factors", "count_roots"]
    if difficulty >= 4:
        tiers.append("end_behavior")
    if difficulty >= 5:
        tiers.append("write_equation")
    tier = rng.choice(tiers)
    params: dict = {"tier": tier}
    choices = None

    if tier == "evaluate":
        degree = rng.choice([2, 3])
        coeffs = [rng.choice([-2, -1, 1, 2])] + [rng.randint(-4, 4) for _ in range(degree)]
        x_val = rng.randint(-3, 3)
        params.update(coeffs=coeffs, roots=[], a=0, x=x_val)
        prompt = f"For p(x) = {_poly_text(coeffs)}, what is p({x_val})?"
        answer = str(int(_poly_val(coeffs, x_val)))
        kind = "INTEGER"
    elif tier == "degree":
        degree = rng.randint(2, 5)
        # Guarantee at least two zero coefficients so the term-count
        # distractor genuinely differs from the degree.
        while True:
            coeffs = [rng.choice([-3, -2, -1, 1, 2, 3])]
            coeffs += [rng.randint(-5, 5) for _ in range(degree)]
            coeffs[rng.randint(1, degree - 1)] = 0
            terms = sum(1 for c in coeffs if c != 0)
            if terms != degree:
                break
        distractors = [
            (str(terms), "POLY_003"),
            (str(abs(coeffs[0])), "POLY_003"),
            (str(degree + 1), None),
            (str(degree - 1), None),
        ]
        params.update(coeffs=coeffs, roots=[], a=0)
        prompt = f"What is the degree of p(x) = {_poly_text(coeffs)}?"
        choices, answer = _mc_choices(rng, str(degree), distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "zeros_from_factors":
        n = rng.choice([2, 3])
        roots = sorted(rng.sample(range(-4, 5), n))
        params.update(a=1, roots=roots, coeffs=_poly_expand(1, roots))
        def fmt(rs: list[int]) -> str:
            return ", ".join(f"x = {r}" for r in rs)

        distractors = [
            (fmt([-r for r in roots]), "POLY_001"),
            (fmt(roots[:-1]), None),
            (fmt([r + 1 for r in roots]), None),
        ]
        factors = "".join(_factor_text(r) for r in roots)
        prompt = f"What are the zeros of f(x) = {factors}?"
        choices, answer = _mc_choices(rng, fmt(roots), distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "count_roots":
        a, roots, coeffs = _poly_graph_params(rng, rng.choice([2, 3]))
        params.update(a=a, roots=roots, coeffs=coeffs)
        correct = str(len(roots))
        choices, answer = _mc_choices(
            rng, correct, [(str(n), None) for n in range(4) if str(n) != correct]
        )
        prompt = "How many times does the graph cross the x-axis?"
        kind = "MULTIPLE_CHOICE"
    elif tier == "end_behavior":
        degree = rng.randint(2, 4)
        lead = rng.choice([-2, -1, 1, 2])
        coeffs = [lead] + [rng.randint(-4, 4) for _ in range(degree)]
        params.update(coeffs=coeffs, roots=[], a=lead)
        even = degree % 2 == 0
        correct = _END_BEHAVIOR[(even, 1 if lead > 0 else -1)]
        distractors = [
            (_END_BEHAVIOR[(not even, 1 if lead > 0 else -1)], "POLY_002"),
            (_END_BEHAVIOR[(even, -1 if lead > 0 else 1)], "POLY_002"),
            (_END_BEHAVIOR[(not even, -1 if lead > 0 else 1)], None),
        ]
        prompt = f"For p(x) = {_poly_text(coeffs)}, which describes the end behavior?"
        choices, answer = _mc_choices(rng, correct, distractors)
        kind = "MULTIPLE_CHOICE"
    else:  # write_equation — read the factored form off a marked graph
        a, roots, coeffs = _poly_graph_params(rng, 3)
        params.update(a=a, roots=roots, coeffs=coeffs)
        def eq(aa: int, rs: list[int]) -> str:
            lead = "" if aa == 1 else "-" if aa == -1 else str(aa)
            return f"y={lead}{''.join(_factor_text(r) for r in rs)}"

        distractors = [
            (eq(a, [-r for r in roots]), "POLY_001"),
            (eq(-a, roots), None),
            (eq(a, roots[:-1]), None),
        ]
        prompt = "Which equation describes the graph shown?"
        choices, answer = _mc_choices(rng, eq(a, roots), distractors)
        kind = "MULTIPLE_CHOICE"

    return GeneratedProblem(
        prompt, answer, difficulty, "POLYNOMIAL_FUNCTION",
        parameters=params, answer_kind=kind, choices=choices,
    )


def _generate_integer_sum(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        a, b = rng.randint(1, 20), rng.randint(1, 20)
    elif difficulty <= 4:
        a, b = rng.randint(-15, 15), rng.randint(1, 15)
    else:
        a, b = rng.randint(-20, 20), rng.randint(-20, 20)
    prompt = f"Evaluate {a} + {b}." if b >= 0 else f"Evaluate {a} - {abs(b)}."
    return GeneratedProblem(
        prompt,
        str(a + b),
        difficulty,
        "INTEGER_OPERATIONS",
        parameters={"a": a, "b": b},
    )


def _generate_integer_compare(rng: random.Random, difficulty: int) -> GeneratedProblem:
    bound = 10 if difficulty <= 2 else 20
    a = rng.randint(-bound, bound)
    b = rng.randint(-bound, bound)
    while b == a:
        b = rng.randint(-bound, bound)
    prompt = f"Which is greater, {a} or {b}?"
    return GeneratedProblem(
        prompt,
        str(max(a, b)),
        difficulty,
        "INTEGER_COMPARE",
        parameters={"a": a, "b": b},
    )


def _generate_fraction_add(rng: random.Random, difficulty: int) -> GeneratedProblem:
    d1 = rng.choice([2, 3, 4, 5])
    d2 = rng.choice([2, 3, 4, 5, 6, 8])
    n1, n2 = rng.randint(1, d1 - 1), rng.randint(1, d2 - 1)
    result = Fraction(n1, d1) + Fraction(n2, d2)
    prompt = f"Evaluate {n1}/{d1} + {n2}/{d2}."
    answer = (
        str(result.numerator)
        if result.denominator == 1
        else f"{result.numerator}/{result.denominator}"
    )
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "FRACTION_OPERATIONS",
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )


def _generate_fraction_subtract(rng: random.Random, difficulty: int) -> GeneratedProblem:
    f1 = Fraction(rng.randint(1, 4), rng.choice([2, 3, 4, 5]))
    f2 = Fraction(rng.randint(1, 7), rng.choice([2, 3, 4, 5, 6, 8]))
    while f2 >= f1:
        f2 = Fraction(rng.randint(1, 7), rng.choice([2, 3, 4, 5, 6, 8]))
    result = f1 - f2
    answer = (
        str(result.numerator)
        if result.denominator == 1
        else f"{result.numerator}/{result.denominator}"
    )
    prompt = f"Evaluate {f1.numerator}/{f1.denominator} - {f2.numerator}/{f2.denominator}."
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "FRACTION_SUBTRACT",
        parameters={
            "n1": f1.numerator,
            "d1": f1.denominator,
            "n2": f2.numerator,
            "d2": f2.denominator,
        },
    )


def _generate_word_problem(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        percent = rng.choice([10, 20, 25, 50])
        amount = rng.choice([40, 60, 80, 100, 120, 200])
        prompt = f"What is {percent}% of {amount}?"
        answer = str(percent * amount // 100)
        context = {
            "template": "percent_of",
            "parameters": {"percent": percent, "amount": amount},
        }
        parameters = dict(context["parameters"])
    else:
        total = rng.choice([60, 90, 120, 150, 240, 300])
        hours = rng.choice([2, 3, 4, 5, 6])
        prompt = (
            f"A car travels {total} miles in {hours} hours at a constant rate. "
            "What is the unit rate in miles per hour?"
        )
        answer = str(total // hours) if total % hours == 0 else f"{total}/{hours}"
        context = {
            "template": "unit_rate",
            "parameters": {"distance": total, "hours": hours},
        }
        parameters = dict(context["parameters"])
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "WORD_PROBLEM",
        context=context,
        parameters=parameters,
    )


def _generate_algebra_word_problem(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Word problems that require defining a variable and building an equation.

    Every template yields a linear ax + b = c model with an integer answer,
    so the step checker can verify the setup by its solution value.
    """
    if difficulty <= 2:
        template = rng.choice(["number_trick", "shared_total"])
    else:
        template = rng.choice(["flat_fee", "savings"])
    if template == "number_trick":
        a, b, x = rng.randint(2, 9), rng.randint(1, 15), rng.randint(2, 12)
        prompt = (
            f"When a number is multiplied by {a} and then increased by {b}, "
            f"the result is {a * x + b}. Find the number."
        )
        answer = str(x)
        parameters = {"multiplier": a, "added": b, "value": x}
    elif template == "shared_total":
        k, x = rng.randint(2, 5), rng.randint(3, 12)
        prompt = (
            f"Mia scored {k} times as many points as Leo. Together they scored "
            f"{(k + 1) * x} points. How many points did Leo score?"
        )
        answer = str(x)
        parameters = {"ratio": k, "leo": x}
    elif template == "flat_fee":
        fee, rate, miles = rng.randint(2, 8), rng.randint(2, 9), rng.randint(4, 15)
        prompt = (
            f"A taxi charges a ${fee} pickup fee plus ${rate} per mile. "
            f"A ride costs ${fee + rate * miles} total. How many miles was the ride?"
        )
        answer = str(miles)
        parameters = {"fee": fee, "rate": rate, "miles": miles}
    else:
        saved, weekly, weeks = rng.randint(5, 30), rng.randint(3, 10), rng.randint(4, 12)
        prompt = (
            f"You already have ${saved} saved and add ${weekly} every week. "
            f"In how many weeks will you have ${saved + weekly * weeks}?"
        )
        answer = str(weeks)
        parameters = {"saved": saved, "weekly": weekly, "weeks": weeks}
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "ALGEBRA_WORD_PROBLEM",
        context={"template": template, "parameters": parameters},
        parameters=parameters,
    )


def _generate_equal_groups(rng: random.Random, difficulty: int) -> GeneratedProblem:
    limit = 5 if difficulty <= 1 else 10
    rows, columns = rng.randint(2, limit), rng.randint(2, limit)
    return GeneratedProblem(
        prompt=(
            f"An array has {rows} rows with {columns} counters in each row. "
            "How many counters are there?"
        ),
        canonical_answer=str(rows * columns),
        difficulty=difficulty,
        problem_type="EQUAL_GROUPS",
        parameters={"rows": rows, "columns": columns, "representation": "array"},
    )


def _generate_equal_sharing(rng: random.Random, difficulty: int) -> GeneratedProblem:
    limit = 5 if difficulty <= 1 else 10
    groups, group_size = rng.randint(2, limit), rng.randint(2, limit)
    total = groups * group_size
    return GeneratedProblem(
        prompt=(
            f"{total} counters are shared equally among {groups} groups. "
            "How many counters are in each group?"
        ),
        canonical_answer=str(group_size),
        difficulty=difficulty,
        problem_type="EQUAL_SHARING",
        parameters={"total": total, "groups": groups, "group_size": group_size},
    )


def _generate_unit_fraction(rng: random.Random, difficulty: int) -> GeneratedProblem:
    denominator = rng.randint(2, 6 if difficulty <= 1 else 10)
    numerator = 1 if difficulty <= 1 else rng.randint(1, denominator - 1)
    answer = f"{numerator}/{denominator}"
    prompt = (
        f"A whole is divided into {denominator} equal parts. "
        f"What fraction is {numerator} of those parts?"
    )
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "UNIT_FRACTION",
        parameters={"numerator": numerator, "denominator": denominator},
    )


def _generate_rectangle_area(rng: random.Random, difficulty: int) -> GeneratedProblem:
    limit = 6 if difficulty <= 1 else 10
    rows, columns = rng.randint(2, limit), rng.randint(2, limit)
    return GeneratedProblem(
        prompt=(
            f"A rectangle has {rows} rows of {columns} unit squares. "
            "What is its area in square units?"
        ),
        canonical_answer=str(rows * columns),
        difficulty=difficulty,
        problem_type="RECTANGLE_AREA",
        parameters={"rows": rows, "columns": columns, "unit": "square units"},
    )


def _generate_addition_within_20(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(2, 9)
    b = rng.randint(2, min(9, 18 - a))
    return GeneratedProblem(
        prompt=f"What is {a} + {b}?",
        canonical_answer=str(a + b),
        difficulty=difficulty,
        problem_type="ADDITION_WITHIN_20",
        parameters={"a": a, "b": b, "operation": "+"},
    )


def _generate_subtraction_within_20(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(5, 18)
    b = rng.randint(2, min(a - 1, 9))
    return GeneratedProblem(
        prompt=f"What is {a} - {b}?",
        canonical_answer=str(a - b),
        difficulty=difficulty,
        problem_type="SUBTRACTION_WITHIN_20",
        parameters={"a": a, "b": b, "operation": "-"},
    )


def _generate_addition_within_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(10, 89)
    b = rng.randint(10, 99 - a)
    return GeneratedProblem(
        prompt=f"What is {a} + {b}?",
        canonical_answer=str(a + b),
        difficulty=difficulty,
        problem_type="ADDITION_WITHIN_100",
        parameters={"a": a, "b": b, "operation": "+"},
    )


def _generate_subtraction_within_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(20, 99)
    b = rng.randint(10, a - 1)
    return GeneratedProblem(
        prompt=f"What is {a} - {b}?",
        canonical_answer=str(a - b),
        difficulty=difficulty,
        problem_type="SUBTRACTION_WITHIN_100",
        parameters={"a": a, "b": b, "operation": "-"},
    )


def _generate_place_value_base_ten(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        tens = rng.randint(1, 9)
        ones = rng.randint(0, 9)
        number = tens * 10 + ones
        prompt = f"How many tens and ones make {number}?"
        answer = f"{tens} tens and {ones} ones"
        params = {"number": number, "tens": tens, "ones": ones, "place": "tens_and_ones"}
    else:
        hundreds = rng.randint(1, 9)
        tens = rng.randint(0, 9)
        ones = rng.randint(0, 9)
        number = hundreds * 100 + tens * 10 + ones
        prompt = f"How many hundreds, tens, and ones make {number}?"
        answer = f"{hundreds} hundreds, {tens} tens, and {ones} ones"
        params = {
            "number": number,
            "hundreds": hundreds,
            "tens": tens,
            "ones": ones,
            "place": "hundreds_tens_ones",
        }
    return GeneratedProblem(prompt, answer, difficulty, "PLACE_VALUE_BASE_TEN", parameters=params)


def _generate_money_count(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        q, d, n, p = rng.randint(0, 2), rng.randint(0, 2), rng.randint(0, 2), rng.randint(0, 4)
    else:
        q, d, n, p = rng.randint(0, 4), rng.randint(0, 5), rng.randint(0, 5), rng.randint(0, 9)
    total = q * 25 + d * 10 + n * 5 + p
    parts = []
    if q:
        parts.append(f"{q} quarter{'s' if q != 1 else ''}")
    if d:
        parts.append(f"{d} dime{'s' if d != 1 else ''}")
    if n:
        parts.append(f"{n} nickel{'s' if n != 1 else ''}")
    if p:
        parts.append(f"{p} penny{'s' if p != 1 else ''}")
    prompt = "What is the total value of " + ", ".join(parts) + "?"
    dollars = total // 100
    cents = total % 100
    if dollars:
        answer = f"${dollars}.{cents:02d}"
    else:
        answer = f"${cents / 100:.2f}"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "MONEY_COUNT",
        parameters={"quarters": q, "dimes": d, "nickels": n, "pennies": p, "total_cents": total},
    )


def _generate_time_to_hour_half_hour(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        hour = rng.randint(1, 12)
        minute = rng.choice([0, 30])
    else:
        hour = rng.randint(1, 12)
        minute = rng.choice([0, 15, 30, 45])
    if minute == 0:
        answer = f"{hour}:00"
        prompt = f"What time is shown when the hour hand points to {hour} and the minute hand points to 12?"
    elif minute == 30:
        answer = f"{hour}:30"
        prompt = f"What time is shown when the hour hand is between {hour} and {(hour % 12) + 1} and the minute hand points to 6?"
    else:
        answer = f"{hour}:{minute:02d}"
        prompt = f"What time is shown when the minute hand points to {minute // 5} and the hour hand is near {hour}?"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "TIME_TO_HOUR_HALF_HOUR",
        parameters={"hour": hour, "minute": minute},
    )


def _generate_multi_digit_multiplication(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        a, b = rng.randint(10, 99), rng.randint(2, 9)
    else:
        a, b = rng.randint(100, 999), rng.randint(10, 99)
    return GeneratedProblem(
        prompt=f"What is {a} × {b}?",
        canonical_answer=str(a * b),
        difficulty=difficulty,
        problem_type="MULTI_DIGIT_MULTIPLICATION",
        parameters={"a": a, "b": b, "operation": "×"},
    )


def _generate_long_division(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        divisor = rng.randint(2, 9)
        quotient = rng.randint(10, 99)
    else:
        divisor = rng.randint(2, 12)
        quotient = rng.randint(10, 99)
    dividend = divisor * quotient
    return GeneratedProblem(
        prompt=f"What is {dividend} ÷ {divisor}?",
        canonical_answer=str(quotient),
        difficulty=difficulty,
        problem_type="LONG_DIVISION",
        parameters={
            "dividend": dividend,
            "divisor": divisor,
            "quotient": quotient,
            "operation": "÷",
        },
    )


def _generate_fraction_equivalence(rng: random.Random, difficulty: int) -> GeneratedProblem:
    target = Fraction(rng.randint(1, 3), rng.choice([2, 3, 4, 5, 6, 8]))
    multiplier = rng.randint(2, 4)
    equivalent = Fraction(target.numerator * multiplier, target.denominator * multiplier)
    prompt = f"What fraction is equivalent to {target.numerator}/{target.denominator} with denominator {equivalent.denominator}?"
    return GeneratedProblem(
        prompt,
        f"{equivalent.numerator}/{equivalent.denominator}",
        difficulty,
        "FRACTION_EQUIVALENCE",
        parameters={
            "original_numerator": target.numerator,
            "original_denominator": target.denominator,
            "multiplier": multiplier,
            "target_numerator": equivalent.numerator,
            "target_denominator": equivalent.denominator,
        },
    )


def _generate_fraction_add_subtract_like(rng: random.Random, difficulty: int) -> GeneratedProblem:
    denominator = rng.choice([2, 3, 4, 5, 6, 8])
    n1 = rng.randint(1, denominator - 1)
    n2 = rng.randint(1, denominator - 1)
    if rng.random() < 0.5:
        result = Fraction(n1, denominator) + Fraction(n2, denominator)
        op = "+"
        prompt = f"What is {n1}/{denominator} + {n2}/{denominator}?"
    else:
        if n1 < n2:
            n1, n2 = n2, n1
        result = Fraction(n1, denominator) - Fraction(n2, denominator)
        op = "-"
        prompt = f"What is {n1}/{denominator} - {n2}/{denominator}?"
    answer = (
        str(result.numerator)
        if result.denominator == 1
        else f"{result.numerator}/{result.denominator}"
    )
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "FRACTION_ADD_SUBTRACT_LIKE",
        parameters={"n1": n1, "n2": n2, "denominator": denominator, "operation": op},
    )


def _generate_fraction_multiply(rng: random.Random, difficulty: int) -> GeneratedProblem:
    n1 = rng.randint(1, 5)
    d1 = rng.randint(2, 6)
    n2 = rng.randint(1, 5)
    d2 = rng.randint(2, 6)
    result = Fraction(n1, d1) * Fraction(n2, d2)
    prompt = f"What is {n1}/{d1} × {n2}/{d2}?"
    answer = (
        str(result.numerator)
        if result.denominator == 1
        else f"{result.numerator}/{result.denominator}"
    )
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "FRACTION_MULTIPLY",
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )


def _generate_decimal_place_value(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 1:
        value = round(rng.randint(1, 99) / 10, 1)
        prompt = f"What is the value of the digit in the tenths place of {value}?"
        answer = str(int((value * 10) % 10))
        params = {"number": value, "place": "tenths", "digit": int(answer)}
    else:
        value = round(rng.randint(1, 999) / 100, 2)
        prompt = f"What is the value of the digit in the hundredths place of {value}?"
        answer = str(int((value * 100) % 10))
        params = {"number": value, "place": "hundredths", "digit": int(answer)}
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "DECIMAL_PLACE_VALUE",
        parameters=params,
    )


def _generate_angle_measurement(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Classify a rendered angle — the degree label stays hidden in the
    visual, so this is a real read rather than a number echo."""
    angle = rng.choice([20, 30, 45, 60, 75, 80, 90, 100, 120, 135, 150, 160, 180])
    cls = (
        "acute" if angle < 90
        else "right" if angle == 90
        else "straight" if angle == 180
        else "obtuse"
    )
    others = [c for c in ("acute", "right", "obtuse", "straight") if c != cls]
    distractors: list[tuple[str, str | None]] = []
    # The mirrored class (acute↔obtuse) is the diagnosable error.
    mirror = "obtuse" if cls == "acute" else "acute" if cls == "obtuse" else None
    for c in others:
        distractors.append((c, "GEO_007" if c == mirror else None))
    choices, answer = _mc_choices(rng, cls, distractors)
    return GeneratedProblem(
        "What kind of angle is shown?",
        answer,
        difficulty,
        "ANGLE_MEASUREMENT",
        parameters={"tier": "classify", "angle": angle, "labeled": False},
        answer_kind="MULTIPLE_CHOICE",
        choices=choices,
    )


def _generate_coordinate_plane(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        x = rng.randint(0, 10)
        y = rng.randint(0, 10)
    else:
        x = rng.choice([n for n in range(-8, 9) if n != 0])
        y = rng.choice([n for n in range(-8, 9) if n != 0])
    if difficulty >= 3 and rng.random() < 0.4:
        quadrant = ("I" if x > 0 and y > 0 else
                    "II" if x < 0 and y > 0 else
                    "III" if x < 0 and y < 0 else "IV")
        choices, answer = _mc_choices(
            rng,
            f"Quadrant {quadrant}",
            [(f"Quadrant {q}", None) for q in ("I", "II", "III", "IV")],
        )
        return GeneratedProblem(
            f"The point ({x}, {y}) is plotted on the coordinate plane. In which quadrant is it?",
            answer,
            difficulty,
            "COORDINATE_PLANE",
            parameters={"tier": "quadrant", "x": x, "y": y, "labeled": True},
            answer_kind="MULTIPLE_CHOICE",
            choices=choices,
        )
    return GeneratedProblem(
        "What are the coordinates of the point shown?",
        f"({x}, {y})",
        difficulty,
        "COORDINATE_PLANE",
        parameters={"tier": "read_point", "x": x, "y": y, "labeled": False},
    )


_SOLID_PROPERTIES = {
    # (faces, vertices, edges) — cylinders and cones are excluded because
    # curved-surface counting is genuinely ambiguous at this level.
    "rectangular_prism": (6, 8, 12),
    "square_pyramid": (5, 5, 8),
}


def _generate_solid_volume(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """3D solids: prism/pyramid volumes, surface area, cylinder/cone volumes
    in terms of π, and faces/edges counting — all rendered isometrically.

    The solid spec carries only dimensions; the backend owns every formula.
    """
    tiers = ["prism_volume", "count_faces"]
    if difficulty >= 3:
        tiers += ["pyramid_volume", "surface_area"]
    if difficulty >= 4:
        tiers += ["cylinder_volume", "cone_volume", "count_edges"]
    tier = rng.choice(tiers)
    choices = None

    if tier == "prism_volume":
        l, w, h = (rng.randint(2, 8) for _ in range(3))
        params = {"tier": tier, "solid": "rectangular_prism", "l": l, "w": w, "h": h}
        prompt = (
            f"The rectangular prism shown has length {l}, width {w}, and "
            f"height {h}. What is its volume in cubic units?"
        )
        answer = str(l * w * h)
        kind = "INTEGER"
    elif tier == "count_faces":
        solid = rng.choice(list(_SOLID_PROPERTIES))
        faces, vertices, _ = _SOLID_PROPERTIES[solid]
        params = {"tier": tier, "solid": solid}
        distractors = [
            (str(vertices), "SOLID_003"),
            (str(faces - 1), "SOLID_003"),
            (str(faces + 1), None),
        ]
        prompt = "How many faces does the solid shown have?"
        choices, answer = _mc_choices(rng, str(faces), distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "pyramid_volume":
        b = rng.randint(3, 6)
        h = rng.randint(3, 9)
        while (b * b * h) % 3 != 0:
            h = rng.randint(3, 9)
        params = {"tier": tier, "solid": "square_pyramid", "b": b, "h": h}
        prompt = (
            f"The square pyramid shown has a base with side length {b} and "
            f"height {h}. What is its volume in cubic units?"
        )
        answer = str(b * b * h // 3)
        kind = "INTEGER"
    elif tier == "surface_area":
        l, w, h = (rng.randint(2, 7) for _ in range(3))
        sa = 2 * (l * w + l * h + w * h)
        params = {"tier": tier, "solid": "rectangular_prism", "l": l, "w": w, "h": h}
        distractors = [
            (str(l * w * h), "SOLID_002"),
            (str(l * w + l * h + w * h), "SOLID_003"),
            (str(sa - 2 * min(l * w, l * h, w * h)), "SOLID_003"),
        ]
        prompt = "What is the total surface area of the rectangular prism shown?"
        choices, answer = _mc_choices(rng, str(sa), distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "cylinder_volume":
        r = rng.randint(2, 5)
        h = rng.choice([3, 6, 9])  # divisible by 3 keeps the cone distractor clean
        params = {"tier": tier, "solid": "cylinder", "r": r, "h": h}
        distractors = [
            (f"{2 * r * h}π", "SOLID_002"),
            (f"{r * r * h // 3}π", "SOLID_001"),
            (f"{r * h}π", None),
            (f"{r * r * h + h}π", None),
        ]
        prompt = (
            f"The cylinder shown has radius {r} and height {h}. "
            "Which expression gives its volume?"
        )
        choices, answer = _mc_choices(rng, f"{r * r * h}π", distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "cone_volume":
        r = rng.randint(2, 4)
        h = rng.choice([3, 6, 9])
        params = {"tier": tier, "solid": "cone", "r": r, "h": h}
        distractors = [
            (f"{r * r * h}π", "SOLID_001"),
            (f"{2 * r * h}π", "SOLID_002"),
            (f"{r * h}π", None),
            (f"{r * r * h // 3 + 2}π", None),
        ]
        prompt = (
            f"The cone shown has radius {r} and height {h}. "
            "Which expression gives its volume?"
        )
        choices, answer = _mc_choices(rng, f"{r * r * h // 3}π", distractors)
        kind = "MULTIPLE_CHOICE"
    else:  # count_edges
        solid = rng.choice(list(_SOLID_PROPERTIES))
        faces, vertices, edges = _SOLID_PROPERTIES[solid]
        params = {"tier": tier, "solid": solid}
        distractors = [
            (str(vertices), "SOLID_003"),
            (str(faces), "SOLID_003"),
            (str(edges - 2), None),
        ]
        prompt = "How many edges does the solid shown have?"
        choices, answer = _mc_choices(rng, str(edges), distractors)
        kind = "MULTIPLE_CHOICE"

    return GeneratedProblem(
        prompt, answer, difficulty, "SOLID_VOLUME",
        parameters=params, answer_kind=kind, choices=choices,
    )


def _generate_geometry_2d(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Plane geometry: angle relationships (complementary, supplementary,
    linear pairs, vertical), triangle angle sums, circle measures in terms
    of π, and composite-figure area — each with a dedicated diagram spec.
    """
    tiers = ["complementary", "supplementary"]
    if difficulty >= 3:
        tiers += ["linear_pair", "vertical_angles", "triangle_angle"]
    if difficulty >= 4:
        tiers += ["circle_area", "circle_circumference", "composite_area"]
    tier = rng.choice(tiers)
    choices = None

    if tier == "complementary":
        angle = rng.choice([15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75])
        params = {"tier": tier, "angle": angle}
        prompt = "The two angles shown are complementary. What is the measure of the missing angle?"
        answer = str(90 - angle)
        kind = "INTEGER"
    elif tier == "supplementary":
        angle = rng.choice([20, 30, 40, 45, 50, 60, 65, 70, 80, 100, 110, 120, 130, 140, 150])
        params = {"tier": tier, "angle": angle}
        prompt = "The two angles shown are supplementary. What is the measure of the missing angle?"
        answer = str(180 - angle)
        kind = "INTEGER"
    elif tier == "linear_pair":
        angle = rng.choice([30, 40, 45, 50, 60, 65, 70, 80, 100, 110, 120, 130, 140, 150])
        params = {"tier": tier, "angle": angle, "mark": "adjacent"}
        prompt = "The marked angle and the angle labeled ? form a linear pair. What is the measure of ?"
        answer = str(180 - angle)
        kind = "INTEGER"
    elif tier == "vertical_angles":
        angle = rng.choice([30, 40, 45, 50, 60, 65, 70, 80, 100, 110, 120, 130, 140, 150])
        params = {"tier": tier, "angle": angle, "mark": "vertical"}
        distractors = [
            (str(180 - angle), "GEO_004"),
            (str(90 - angle) if angle < 90 else str(angle - 10), None),
            (str(angle + 10) if angle <= 170 else str(angle - 20), None),
        ]
        prompt = "The two lines shown intersect. What is the measure of the angle labeled ?"
        choices, answer = _mc_choices(rng, str(angle), distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "triangle_angle":
        a = rng.randint(25, 90)
        b = rng.randint(25, 90)
        while not (60 <= a + b <= 150):
            a = rng.randint(25, 90)
            b = rng.randint(25, 90)
        params = {"tier": tier, "a": a, "b": b}
        prompt = "What is the measure of the triangle's third angle, labeled ?"
        answer = str(180 - a - b)
        kind = "INTEGER"
    elif tier == "circle_area":
        r = rng.randint(2, 7)
        params = {"tier": tier, "r": r}
        distractors = [
            (f"{2 * r}π", "GEO_001"),
            (f"{4 * r * r}π", "GEO_006"),
            (f"{2 * r * r}π", None),
        ]
        prompt = f"The circle shown has radius {r}. Which expression gives its area?"
        choices, answer = _mc_choices(rng, f"{r * r}π", distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "circle_circumference":
        r = rng.randint(2, 7)
        params = {"tier": tier, "r": r}
        distractors = [
            (f"{r * r}π", "GEO_001"),
            (f"{r}π", "GEO_006"),
            (f"{4 * r}π", None),
        ]
        prompt = f"The circle shown has radius {r}. Which expression gives its circumference?"
        choices, answer = _mc_choices(rng, f"{2 * r}π", distractors)
        kind = "MULTIPLE_CHOICE"
    else:  # composite_area — L-shape: outer W×H minus an a×b notch
        w = rng.randint(5, 9)
        h = rng.randint(5, 9)
        a = rng.randint(2, w - 3)
        b = rng.randint(2, h - 3)
        params = {"tier": tier, "w": w, "h": h, "a": a, "b": b}
        area = w * h - a * b
        distractors = [
            (str(w * h), "GEO_005"),
            (str(w * h + a * b), "GEO_005"),
            (str(a * b), None),
        ]
        prompt = "What is the area of the shaded L-shaped figure shown?"
        choices, answer = _mc_choices(rng, str(area), distractors)
        kind = "MULTIPLE_CHOICE"

    return GeneratedProblem(
        prompt, answer, difficulty, "GEOMETRY_2D",
        parameters=params, answer_kind=kind, choices=choices,
    )


_TRANSFORM_BOUND = 8


def _random_point(rng: random.Random, lo: int, hi: int) -> list[int]:
    return [rng.randint(lo, hi), rng.randint(lo, hi)]


def _random_triangle(rng: random.Random, region) -> list[list[int]]:
    for _ in range(80):
        tri = [region() for _ in range(3)]
        (x1, y1), (x2, y2), (x3, y3) = tri
        if (x2 - x1) * (y3 - y1) != (y2 - y1) * (x3 - x1):
            return tri
    raise AssertionError("could not build a non-collinear triangle")


def _generate_transformation(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Rigid motions and dilations on the coordinate plane: translate,
    reflect, rotate, or dilate a rendered point — or name the motion that
    maps a rendered preimage triangle onto its image."""
    tiers = ["translate"]
    if difficulty >= 2:
        tiers.append("reflect")
    if difficulty >= 3:
        tiers += ["rotate", "identify"]
    if difficulty >= 4:
        tiers.append("dilate")
    tier = rng.choice(tiers)

    if tier == "translate":
        dx = rng.choice([d for d in range(-5, 6) if d != 0])
        dy = rng.choice([d for d in range(-5, 6) if d != 0])
        for _ in range(60):
            x, y = _random_point(rng, -5, 5)
            if abs(x + dx) <= _TRANSFORM_BOUND and abs(y + dy) <= _TRANSFORM_BOUND:
                break
        nx, ny = x + dx, y + dy
        horizontal = f"{abs(dx)} units {'right' if dx > 0 else 'left'}"
        vertical = f"{abs(dy)} units {'up' if dy > 0 else 'down'}"
        prompt = (
            f"Point P is shown on the grid. Translate it {horizontal} and "
            f"{vertical}. What are the coordinates of P'?"
        )
        params = {"tier": tier, "x": x, "y": y, "dx": dx, "dy": dy,
                  "preimage": [[x, y]], "labels": ["P"]}
        answer = f"({nx}, {ny})"
        kind = "FREE_TEXT"
        choices = None
    elif tier == "reflect":
        axis = rng.choice(["x-axis", "y-axis"])
        for _ in range(60):
            x, y = _random_point(rng, -7, 7)
            if x != 0 and y != 0:
                break
        nx, ny = (x, -y) if axis == "x-axis" else (-x, y)
        prompt = (
            f"Point P is shown on the grid. Reflect it over the {axis}. "
            "What are the coordinates of P'?"
        )
        params = {"tier": tier, "x": x, "y": y, "axis": axis,
                  "preimage": [[x, y]], "labels": ["P"]}
        answer = f"({nx}, {ny})"
        kind = "FREE_TEXT"
        choices = None
    elif tier == "rotate":
        direction = rng.choice(["90° clockwise", "90° counterclockwise", "180°"])
        for _ in range(60):
            x, y = _random_point(rng, -7, 7)
            if x != 0 and y != 0:
                break
        if direction == "90° clockwise":
            nx, ny = y, -x
        elif direction == "90° counterclockwise":
            nx, ny = -y, x
        else:
            nx, ny = -x, -y
        prompt = (
            f"Point P is shown on the grid. Rotate it {direction} about the "
            "origin. What are the coordinates of P'?"
        )
        params = {"tier": tier, "x": x, "y": y, "direction": direction,
                  "preimage": [[x, y]], "labels": ["P"]}
        answer = f"({nx}, {ny})"
        kind = "FREE_TEXT"
        choices = None
    elif tier == "dilate":
        k = rng.choice([2, 3])
        for _ in range(60):
            x, y = _random_point(rng, -3, 3)
            if x != 0 and y != 0 and abs(k * x) <= _TRANSFORM_BOUND and abs(k * y) <= _TRANSFORM_BOUND:
                break
        prompt = (
            f"Point P is shown on the grid. Dilate it by a scale factor of {k} "
            "centred at the origin. What are the coordinates of P'?"
        )
        params = {"tier": tier, "x": x, "y": y, "k": k,
                  "preimage": [[x, y]], "labels": ["P"]}
        answer = f"({k * x}, {k * y})"
        kind = "FREE_TEXT"
        choices = None
    else:  # identify — name the motion mapping the preimage onto the image
        motion = rng.choice(
            ["translate", "reflect_x", "reflect_y", "rotate_180", "rotate_90cw"]
        )
        if motion == "reflect_x":
            tri = _random_triangle(rng, lambda: [rng.randint(-6, 6), rng.randint(1, 6)])
            image = [[x, -y] for x, y in tri]
            description = "a reflection over the x-axis"
        elif motion == "reflect_y":
            tri = _random_triangle(rng, lambda: [rng.randint(1, 6), rng.randint(-6, 6)])
            image = [[-x, y] for x, y in tri]
            description = "a reflection over the y-axis"
        elif motion == "rotate_180":
            tri = _random_triangle(rng, lambda: [rng.randint(1, 5), rng.randint(1, 5)])
            image = [[-x, -y] for x, y in tri]
            description = "a rotation of 180° about the origin"
        elif motion == "rotate_90cw":
            tri = _random_triangle(rng, lambda: [rng.randint(-5, -1), rng.randint(1, 5)])
            image = [[y, -x] for x, y in tri]
            description = "a rotation of 90° clockwise about the origin"
        else:
            dx = rng.choice([d for d in range(-4, 5) if d != 0])
            dy = rng.choice([d for d in range(-4, 5) if d != 0])

            def region():
                return [rng.randint(-4, 4), rng.randint(-4, 4)]

            tri = _random_triangle(rng, region)
            while not all(
                abs(x + dx) <= _TRANSFORM_BOUND and abs(y + dy) <= _TRANSFORM_BOUND
                for x, y in tri
            ):
                tri = _random_triangle(rng, region)
            image = [[x + dx, y + dy] for x, y in tri]
            description = (
                f"a translation {abs(dx)} units {'right' if dx > 0 else 'left'} "
                f"and {abs(dy)} units {'up' if dy > 0 else 'down'}"
            )
        distractor_pool = [
            "a reflection over the x-axis",
            "a reflection over the y-axis",
            "a rotation of 180° about the origin",
            "a rotation of 90° clockwise about the origin",
            "a translation 2 units right and 3 units up",
        ]
        distractors = [
            (text, "TR_004") for text in distractor_pool if text != description
        ]
        rng.shuffle(distractors)
        prompt = (
            "Triangle ABC is mapped onto triangle A'B'C' as shown. "
            "Which transformation maps the preimage onto the image?"
        )
        choices, answer = _mc_choices(rng, description, distractors[:3])
        params = {"tier": tier, "motion": motion, "preimage": tri,
                  "image": image, "labels": ["A", "B", "C"],
                  "image_labels": ["A'", "B'", "C'"]}
        kind = "MULTIPLE_CHOICE"

    return GeneratedProblem(
        prompt, answer, difficulty, "TRANSFORMATION",
        parameters=params, answer_kind=kind, choices=choices,
    )


_SIMILARITY_SHAPES = {
    "triangle": [[0, 0], [6, 0], [2, 5]],
    "wide": [[0, 0], [7, 0], [4, 3]],
    "tall": [[0, 0], [3, 0], [1, 6]],
}


def _scale_verts(verts: list[list[float]], scale: float) -> list[list[float]]:
    return [[round(vx * scale, 2), round(vy * scale, 2)] for vx, vy in verts]


def _generate_similarity(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Similar and congruent figures: scale factors, proportional sides,
    the k versus k² perimeter/area trap, and congruence classification.
    Diagrams are always proportional — the drawn image is the preimage
    scaled by k."""
    tiers = ["scale_factor", "missing_side"]
    if difficulty >= 3:
        tiers += ["perimeter_area_effect", "classify"]
    tier = rng.choice(tiers)

    shape = _SIMILARITY_SHAPES["triangle"]
    base_len = 6.0  # the base edge of the reference shape

    if tier == "scale_factor":
        a, k_num, k_den = rng.choice(
            [(2, 2, 1), (3, 2, 1), (4, 2, 1), (4, 3, 2), (6, 3, 2), (2, 3, 1)]
        )
        image_a = a * k_num // k_den
        s = a / base_len
        preimage = _scale_verts(shape, s)
        image = _scale_verts(shape, s * k_num / k_den)
        correct = str(k_num) if k_den == 1 else f"{k_num}/{k_den}"
        distractors = [
            (f"{k_den}/{k_num}", "SIM_003"),
            (str(k_num + 1), None),
            (str(image_a - a), None),
            (str(image_a), None),
        ]
        prompt = (
            "The two triangles shown are similar. What is the scale factor "
            "from the smaller triangle to the larger one?"
        )
        choices, answer = _mc_choices(rng, correct, distractors)
        params = {
            "tier": tier, "preimage": preimage, "image": image,
            "pre_edge_labels": [str(a), None, None],
            "image_edge_labels": [str(image_a), None, None],
            "k_num": k_num, "k_den": k_den,
        }
        kind = "MULTIPLE_CHOICE"
    elif tier == "missing_side":
        a = rng.choice([3, 4, 5, 6])
        k = rng.choice([2, 3])
        b = rng.choice([4, 5, 7])
        s = a / base_len
        preimage = _scale_verts(shape, s)
        image = _scale_verts(shape, s * k)
        correct = b * k
        distractors = [
            (str(b + a * (k - 1)), "SIM_001"),
            (str(a + b), None),
            (str(b * k + a), None),
            (str(a * k), None),
        ]
        prompt = (
            "The two triangles shown are similar. What is the length of "
            "the side labeled ?"
        )
        choices, answer = _mc_choices(rng, str(correct), distractors)
        params = {
            "tier": tier, "preimage": preimage, "image": image,
            "pre_edge_labels": [str(a), str(b), None],
            "image_edge_labels": [str(a * k), "?", None],
        }
        kind = "MULTIPLE_CHOICE"
    elif tier == "perimeter_area_effect":
        k = rng.choice([2, 3, 4])
        measure = rng.choice(["perimeter", "area"])
        s = 3 / base_len
        preimage = _scale_verts(shape, s)
        image = _scale_verts(shape, s * k)
        correct_exp = k if measure == "perimeter" else k * k
        wrong_exp = k * k if measure == "perimeter" else k
        distractors = [
            (f"multiplied by {wrong_exp}", "SIM_002"),
            (f"multiplied by {k * 2}", None),
            ("stays the same", None),
        ]
        prompt = (
            f"The smaller triangle is scaled by a factor of {k} to produce "
            f"the larger one shown. By what factor does its {measure} change?"
        )
        choices, answer = _mc_choices(
            rng, f"multiplied by {correct_exp}", distractors
        )
        params = {
            "tier": tier, "preimage": preimage, "image": image,
            "measure": measure, "k": k,
        }
        kind = "MULTIPLE_CHOICE"
    else:  # classify — congruent, similar, or neither
        relation = rng.choice(["congruent", "similar", "neither"])
        s = rng.choice([2, 3]) / base_len
        preimage = _scale_verts(shape, s)
        if relation == "congruent":
            image = list(preimage)
            correct = "congruent"
        elif relation == "similar":
            image = _scale_verts(shape, s * rng.choice([1.5, 2]))
            correct = "similar but not congruent"
        else:
            image = _scale_verts(rng.choice([_SIMILARITY_SHAPES["wide"], _SIMILARITY_SHAPES["tall"]]), s)
            correct = "neither congruent nor similar"
        distractors = [
            (text, "SIM_004")
            for text in ("congruent", "similar but not congruent",
                         "neither congruent nor similar")
            if text != correct
        ]
        prompt = (
            "How are the two triangles shown related?"
        )
        choices, answer = _mc_choices(rng, correct, distractors)
        params = {"tier": tier, "preimage": preimage, "image": image}
        kind = "MULTIPLE_CHOICE"

    return GeneratedProblem(
        prompt, answer, difficulty, "SIMILARITY",
        parameters=params, answer_kind=kind, choices=choices,
    )


_SYSTEM_SLOPES = [(1, 1), (-1, 1), (2, 1), (-2, 1), (1, 2), (-1, 2)]


def _generate_system(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Systems of two linear equations: read the intersection off a
    graphed pair of lines, count solutions (parallel versus coincident),
    or solve a standard-form pair algebraically."""
    tiers = ["graphical_solution"]
    if difficulty >= 2:
        tiers.append("count_solutions")
    if difficulty >= 3:
        tiers.append("solve")
    tier = rng.choice(tiers)
    choices = None

    if tier == "count_solutions":
        case = rng.choice(["one", "none", "infinite"])
        m_num, m_den = rng.choice(_SYSTEM_SLOPES)
        b1 = rng.randint(-4, 4)
        if case == "one":
            for _ in range(40):
                m2_num, m2_den = rng.choice(_SYSTEM_SLOPES)
                if (m2_num, m2_den) != (m_num, m_den):
                    break
            b2 = rng.randint(-4, 4)
            correct = "one solution"
        elif case == "none":
            m2_num, m2_den = m_num, m_den
            b2 = b1 + rng.choice([-3, -2, 2, 3])
            while abs(b2) > 7:
                b2 = b1 + rng.choice([-3, -2, 2, 3])
            correct = "no solution"
        else:
            m2_num, m2_den, b2 = m_num, m_den, b1
            correct = "infinitely many solutions"
        options = ["one solution", "no solution",
                   "infinitely many solutions", "two solutions"]
        distractors = [
            (text, "SYS_002" if text != "two solutions" else None)
            for text in options if text != correct
        ]
        prompt = (
            "The two equations of a system are graphed. How many "
            "solutions does the system have?"
        )
        choices, answer = _mc_choices(rng, correct, distractors)
        params = {"tier": tier, "case": case,
                  "lines": [{"m_num": m_num, "m_den": m_den, "i_num": b1, "i_den": 1},
                            {"m_num": m2_num, "m_den": m2_den, "i_num": b2, "i_den": 1}]}
        kind = "MULTIPLE_CHOICE"
    elif tier == "graphical_solution":
        for _ in range(80):
            sx, sy = _random_point(rng, -4, 4)
            (m1n, m1d), (m2n, m2d) = rng.sample(_SYSTEM_SLOPES, 2)
            b1 = sy * m1d - m1n * sx
            b2 = sy * m2d - m2n * sx
            if b1 % m1d == 0 and b2 % m2d == 0:
                b1 //= m1d
                b2 //= m2d
                if abs(b1) <= 7 and abs(b2) <= 7 and b1 != b2:
                    break
        prompt = (
            "The system of equations shown has exactly one solution. "
            "What are its coordinates?"
        )
        answer = f"({sx}, {sy})"
        params = {"tier": tier,
                  "lines": [{"m_num": m1n, "m_den": m1d, "i_num": b1, "i_den": 1},
                            {"m_num": m2n, "m_den": m2d, "i_num": b2, "i_den": 1}]}
        kind = "FREE_TEXT"
    else:  # solve — standard-form pair with an integer intersection
        for _ in range(80):
            sx, sy = _random_point(rng, -4, 4)
            a1, b1 = rng.sample([1, 2, 3], 2)
            a2, b2 = rng.sample([1, 2, 3], 2)
            if a1 * b2 != a2 * b1:
                break
        c1 = a1 * sx + b1 * sy
        c2 = a2 * sx + b2 * sy
        prompt = (
            f"Solve the system: {a1}x + {b1}y = {c1} and "
            f"{a2}x + {b2}y = {c2}. Write the solution as (x, y)."
        )
        answer = f"({sx}, {sy})"
        # No diagram: the lines would give the intersection away. The
        # visual tiers above are where graph-reading is the skill.
        params = {"tier": tier, "a1": a1, "b1": b1, "c1": c1,
                  "a2": a2, "b2": b2, "c2": c2}
        kind = "FREE_TEXT"

    return GeneratedProblem(
        prompt, answer, difficulty, "SYSTEM_OF_EQUATIONS",
        parameters=params, answer_kind=kind, choices=choices,
    )


# (slope, intercept) pairs whose line stays meaningfully on the 0..10 grid.
_SCATTER_FITS = {
    "positive": (
        [(Fraction(1), b) for b in (1, 2, 3, 4)]
        + [(Fraction(2), b) for b in (1, 2)]
        + [(Fraction(3), b) for b in (0, 1)]
        + [(Fraction(1, 2), b) for b in (2, 3, 4)]
        + [(Fraction(3, 2), b) for b in (1, 2)]
    ),
    "negative": (
        [(Fraction(-1), b) for b in (8, 9, 10)]
        + [(Fraction(-2), 10)]
        + [(Fraction(-1, 2), b) for b in (6, 7, 8)]
        + [(Fraction(-3, 2), b) for b in (9, 10)]
    ),
}


def _scatter_cloud(
    rng: random.Random, direction: str, *, integer_slope: bool = False
) -> tuple[list[list[int]], Fraction | None, int | None]:
    """An integer-coordinate cloud on a 0..10 grid trending along
    y = m x + b, or scattered for 'none'. Returns (points, m, b);
    m and b are None when there is no trend."""
    if direction == "none":
        xs = sorted(rng.sample(range(1, 10), 7))
        return [[x, rng.randint(1, 9)] for x in xs], None, None
    fits = [(m, b) for m, b in _SCATTER_FITS[direction]
            if not integer_slope or m.denominator == 1]
    m, b = rng.choice(fits)
    xs = sorted(rng.sample(range(1, 10), 7))
    points = []
    for x in xs:
        jitter = rng.choices([-1, 0, 1], weights=[1, 4, 1])[0]
        y = int(m * x + b) + jitter
        points.append([x, min(10, max(0, y))])
    return points, m, b


def _fit_equation_text(m: Fraction, b: int) -> str:
    if m == 1:
        coeff = ""
    elif m == -1:
        coeff = "-"
    elif m.denominator == 1:
        coeff = str(m.numerator)
    else:
        coeff = f"{m.numerator}/{m.denominator}"
    equation = f"y = {coeff}x"
    if b > 0:
        equation += f" + {b}"
    elif b < 0:
        equation += f" - {abs(b)}"
    return equation


_CORRELATION_CONTEXTS = [
    ("ice cream sales", "the number of swimmers at local pools", "positive"),
    ("the number of firefighters at a fire", "the damage the fire causes", "positive"),
    ("a student's shoe size", "their score on a spelling test", "positive"),
    ("the outdoor temperature", "sales of hot drinks", "negative"),
]


def _generate_statistics(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Scatterplot items: read the association, find the outlier, predict
    from a rendered line of best fit, match a cloud to its best-fit
    equation, or separate association from causation.

    The fit line renders only for the predict tier — drawing it for
    best_fit_line would state the answer, and the other tiers have no
    line to show."""
    tiers = ["association"]
    if difficulty >= 2:
        tiers.append("outlier")
    if difficulty >= 3:
        tiers += ["predict", "best_fit_line"]
    if difficulty >= 4:
        tiers.append("correlation_causation")
    tier = rng.choice(tiers)
    choices = None
    params: dict = {"tier": tier}

    if tier == "association":
        direction = rng.choice(["positive", "negative", "none"])
        points, m, b = _scatter_cloud(rng, direction)
        params["points"] = points
        prompt = (
            "What type of association does the scatterplot show between "
            "the two variables?"
        )
        options = ["a positive association", "a negative association",
                   "no association", "a curved (nonlinear) association"]
        correct = f"a {direction} association" if direction != "none" else "no association"
        distractors = [(text, "STAT_001") for text in options if text != correct]
        choices, answer = _mc_choices(rng, correct, distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "outlier":
        direction = rng.choice(["positive", "negative"])
        points, m, b = _scatter_cloud(rng, direction, integer_slope=True)
        # Candidates stay on-grid and at least 4 off the trend line, and
        # never collide with a cloud point — a clamped or overlapping
        # "outlier" would make the item ambiguous.
        candidates = []
        for x_out in (2, 5, 8):
            line_y = int(m * x_out + b)
            for step in (4, 5, 6):
                y_out = line_y + step * (1 if line_y <= 5 else -1)
                if 0 <= y_out <= 10 and [x_out, y_out] not in points:
                    candidates.append([x_out, y_out])
        if not candidates:
            return _generate_statistics(rng, difficulty)
        outlier = rng.choice(candidates)
        points.append(outlier)
        rng.shuffle(points)
        params["points"] = points
        prompt = "Which point is the outlier in the scatterplot?"
        on_pattern = [p for p in points if p != outlier]
        # The most extreme on-pattern point is the diagnostic distractor:
        # picking it means "outlier = biggest value", not "breaks the pattern".
        extreme = max(on_pattern, key=lambda p: abs(p[0] - 5) + abs(p[1] - 5))
        others = [p for p in on_pattern if p != extreme]
        rng.shuffle(others)
        distractors = (
            [(f"({extreme[0]}, {extreme[1]})", "STAT_003")]
            + [(f"({p[0]}, {p[1]})", None) for p in others[:2]]
        )
        correct_text = f"({outlier[0]}, {outlier[1]})"
        choices, answer = _mc_choices(rng, correct_text, distractors)
        kind = "MULTIPLE_CHOICE"
    elif tier == "predict":
        points, m, b = _scatter_cloud(rng, "positive", integer_slope=True)
        params["points"] = points
        params["fit"] = {"m_num": m.numerator, "m_den": m.denominator,
                         "i_num": b, "i_den": 1}
        candidates = [x for x in range(2, 9) if 1 <= m * x + b <= 9]
        x_q = rng.choice(candidates)
        equation = _fit_equation_text(m, b)
        prompt = (
            f"The scatterplot shows data with the line of best fit "
            f"{equation}. Use it to predict y when x = {x_q}."
        )
        answer = str(int(m * x_q + b))
        kind = "INTEGER"
    elif tier == "best_fit_line":
        direction = rng.choice(["positive", "negative"])
        points, m, b = _scatter_cloud(rng, direction, integer_slope=True)
        params["points"] = points
        prompt = "Which equation best fits the data shown in the scatterplot?"
        correct = _fit_equation_text(m, b)
        distractors = [
            (_fit_equation_text(-m, b), "STAT_001"),
            (_fit_equation_text(Fraction(b), m.numerator), "STAT_005"),
            (_fit_equation_text(m, b + 2), None),
            (_fit_equation_text(m + 1, b), None),
            (_fit_equation_text(m, b - 2), None),
        ]
        choices, answer = _mc_choices(rng, correct, distractors)
        kind = "MULTIPLE_CHOICE"
    else:  # correlation_causation — text only, no diagram
        x_var, y_var, direction = rng.choice(_CORRELATION_CONTEXTS)
        # The context rides in params so prompt dedupe can tell the
        # four contexts apart (points-less params would all collapse
        # to one fingerprint).
        params["x_var"] = x_var
        params["y_var"] = y_var
        params["direction"] = direction
        prompt = (
            f"A scatterplot shows a strong {direction} association between "
            f"{x_var} and {y_var}. Which conclusion is most reasonable?"
        )
        correct = (
            "The variables are associated, but one does not necessarily "
            "cause the other"
        )
        distractors = [
            (f"Changes in {x_var} directly cause changes in {y_var}", "STAT_002"),
            (f"Changes in {y_var} directly cause changes in {x_var}", "STAT_002"),
            ("There is no relationship between the two variables", "STAT_001"),
        ]
        choices, answer = _mc_choices(rng, correct, distractors)
        kind = "MULTIPLE_CHOICE"

    return GeneratedProblem(
        prompt, answer, difficulty, "STATISTICS",
        parameters=params, answer_kind=kind, choices=choices,
    )


def _generate_volume(rng: random.Random, difficulty: int) -> GeneratedProblem:
    l = rng.randint(2, 6)
    w = rng.randint(2, 6)
    h = rng.randint(2, 6)
    prompt = f"A rectangular prism has length {l}, width {w}, and height {h}. What is its volume?"
    return GeneratedProblem(
        prompt,
        str(l * w * h),
        difficulty,
        "VOLUME",
        parameters={"length": l, "width": w, "height": h},
    )


def _generate_number_sequence(rng: random.Random, difficulty: int) -> GeneratedProblem:
    start = rng.randint(1, 100)
    step = rng.choice([1, 2, 5, 10])
    missing_index = rng.randint(1, 4)
    sequence = [start + step * i for i in range(5)]
    answer = sequence[missing_index]
    sequence[missing_index] = None
    prompt = (
        "What number completes the sequence: "
        + ", ".join("?" if x is None else str(x) for x in sequence)
        + "?"
    )
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "NUMBER_SEQUENCE",
        parameters={"start": start, "step": step, "missing_index": missing_index, "answer": answer},
    )


def _generate_compare_numbers(rng: random.Random, difficulty: int) -> GeneratedProblem:
    limit = 50 if difficulty <= 1 else 120
    a = rng.randint(1, limit)
    b = rng.randint(1, limit)
    if a == b:
        b = (b % limit) + 1
    if a > b:
        answer = ">"
    elif a < b:
        answer = "<"
    else:
        answer = "="
    prompt = f"Compare: {a} ___ {b}. Use >, <, or =."
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "COMPARE_NUMBERS",
        parameters={"a": a, "b": b, "operation": "compare"},
    )


def _generate_word_problem_add_sub_20(rng: random.Random, difficulty: int) -> GeneratedProblem:
    contexts = [
        ("add", "{a} crayons are on the table. {b} more are added. How many crayons are there?"),
        ("subtract", "{a} birds are on a branch. {b} fly away. How many birds are left?"),
        ("add", "There are {a} red blocks and {b} blue blocks. How many blocks are there in all?"),
        ("subtract", "A basket has {a} apples. {b} are eaten. How many apples remain?"),
    ]
    op, template = rng.choice(contexts)
    if op == "add":
        a = rng.randint(2, 12)
        b = rng.randint(2, min(9, 18 - a))
        answer = a + b
    else:
        a = rng.randint(5, 18)
        b = rng.randint(2, min(a - 1, 9))
        answer = a - b
    prompt = template.format(a=a, b=b)
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "WORD_PROBLEM_ADD_SUB_20",
        parameters={"a": a, "b": b, "operation": op, "answer": answer},
    )


def _generate_word_problem_add_sub_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    contexts = [
        (
            "add",
            "A library has {a} fiction books and {b} nonfiction books. How many books are there?",
        ),
        ("subtract", "There are {a} sheets of paper. {b} are used. How many are left?"),
        (
            "add",
            "A box has {a} red marbles and {b} blue marbles. How many marbles are there in all?",
        ),
        ("subtract", "A school has {a} students. {b} leave for a field trip. How many remain?"),
    ]
    op, template = rng.choice(contexts)
    if op == "add":
        a = rng.randint(10, 80)
        b = rng.randint(10, 99 - a)
        answer = a + b
    else:
        a = rng.randint(20, 99)
        b = rng.randint(10, a - 1)
        answer = a - b
    prompt = template.format(a=a, b=b)
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "WORD_PROBLEM_ADD_SUB_100",
        parameters={"a": a, "b": b, "operation": op, "answer": answer},
    )


def _generate_number_pattern(rng: random.Random, difficulty: int) -> GeneratedProblem:
    start = rng.randint(1, 50)
    step = rng.choice([2, 5, 10])
    length = 5
    index = rng.randint(0, length - 1)
    pattern = [start + step * i for i in range(length)]
    answer = pattern[index]
    pattern[index] = None
    prompt = (
        "What number completes the pattern: "
        + ", ".join("?" if x is None else str(x) for x in pattern)
        + "?"
    )
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "NUMBER_PATTERN",
        parameters={"start": start, "step": step, "missing_index": index, "answer": answer},
    )


def _generate_equation_balance(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(1, 10)
    b = rng.randint(1, 10)
    c = a + b
    unknown = rng.choice(["a", "b", "c"])
    if unknown == "a":
        prompt = f"___ + {b} = {c}"
        answer = a
    elif unknown == "b":
        prompt = f"{a} + ___ = {c}"
        answer = b
    else:
        prompt = f"{a} + {b} = ___"
        answer = c
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "EQUATION_BALANCE",
        parameters={"a": a, "b": b, "c": c, "unknown": unknown},
    )


def _generate_compare_length(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(1, 20)
    b = rng.randint(1, 20)
    if a > b:
        answer = a - b
        prompt = f"One ribbon is {a} inches long. Another is {b} inches long. How much longer is the first ribbon?"
    else:
        answer = b - a
        prompt = f"One ribbon is {a} inches long. Another is {b} inches long. How much longer is the second ribbon?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "COMPARE_LENGTH",
        parameters={"a": a, "b": b, "difference": answer},
    )


def _generate_time_to_5_minutes(rng: random.Random, difficulty: int) -> GeneratedProblem:
    hour = rng.randint(1, 12)
    minute = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    prompt = f"What time is shown when the hour hand is near {hour} and the minute hand points to {minute // 5}?"
    answer = f"{hour}:{minute:02d}"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "TIME_TO_5_MINUTES",
        parameters={"hour": hour, "minute": minute},
    )


def _generate_geometry_shapes(rng: random.Random, difficulty: int) -> GeneratedProblem:
    shapes = ["triangle", "square", "rectangle", "circle", "hexagon"]
    shape = rng.choice(shapes)
    prompt = f"How many sides does a {shape} have?"
    sides = {"triangle": 3, "square": 4, "rectangle": 4, "circle": 0, "hexagon": 6}
    return GeneratedProblem(
        prompt,
        str(sides[shape]),
        difficulty,
        "GEOMETRY_SHAPES",
        parameters={"shape": shape, "sides": sides[shape]},
    )


def _generate_fraction_halves_thirds_fourths(
    rng: random.Random, difficulty: int
) -> GeneratedProblem:
    denominator = rng.choice([2, 3, 4])
    numerator = rng.randint(1, denominator)
    prompt = f"A shape is divided into {denominator} equal parts. {numerator} part{'s' if numerator != 1 else ''} are shaded. What fraction is shaded?"
    answer = f"{numerator}/{denominator}"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "FRACTION_HALVES_THIRDS_FOURTHS",
        parameters={"numerator": numerator, "denominator": denominator},
    )


def _generate_bar_graph_read(rng: random.Random, difficulty: int) -> GeneratedProblem:
    categories = ["red", "blue", "green", "yellow"]
    values = [rng.randint(1, 10) for _ in categories]
    category = rng.choice(categories)
    answer = values[categories.index(category)]
    data = dict(zip(categories, values))
    prompt = f"A bar graph shows votes for favorite colors: {data}. How many votes did {category} receive?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "BAR_GRAPH_READ",
        parameters={"category": category, "value": answer, "total": sum(values)},
    )


def _generate_picture_graph_read(rng: random.Random, difficulty: int) -> GeneratedProblem:
    categories = ["dog", "cat", "bird", "fish"]
    values = [rng.randint(1, 8) for _ in categories]
    category = rng.choice(categories)
    answer = values[categories.index(category)]
    data = dict(zip(categories, values))
    prompt = f"A picture graph shows pets: {data}. How many {category}s are there?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "PICTURE_GRAPH_READ",
        parameters={"category": category, "value": answer, "total": sum(values)},
    )


def _generate_multiplication_within_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(2, 9) if difficulty <= 2 else rng.randint(2, 12)
    b = rng.randint(2, 9) if difficulty <= 2 else rng.randint(2, 12)
    return GeneratedProblem(
        prompt=f"What is {a} × {b}?",
        canonical_answer=str(a * b),
        difficulty=difficulty,
        problem_type="MULTIPLICATION_WITHIN_100",
        parameters={"a": a, "b": b, "operation": "×"},
    )


def _generate_division_within_100(rng: random.Random, difficulty: int) -> GeneratedProblem:
    b = rng.randint(2, 9)
    answer = rng.randint(2, 12 if difficulty <= 2 else 9)
    a = b * answer
    return GeneratedProblem(
        prompt=f"What is {a} ÷ {b}?",
        canonical_answer=str(answer),
        difficulty=difficulty,
        problem_type="DIVISION_WITHIN_100",
        parameters={"a": a, "b": b, "operation": "÷"},
    )


def _generate_word_problem_multiply_divide_100(
    rng: random.Random, difficulty: int
) -> GeneratedProblem:
    templates = [
        (
            "multiply",
            "There are {a} boxes with {b} pencils in each box. How many pencils are there in all?",
        ),
        (
            "divide",
            "{a} stickers are shared equally among {b} students. How many stickers does each student get?",
        ),
    ]
    op, template = rng.choice(templates)
    if op == "multiply":
        a = rng.randint(2, 9)
        b = rng.randint(2, 12 if difficulty <= 2 else 9)
        answer = a * b
    else:
        b = rng.randint(2, 9)
        answer = rng.randint(2, 12 if difficulty <= 2 else 9)
        a = b * answer
    prompt = template.format(a=a, b=b)
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "WORD_PROBLEM_MULTIPLY_DIVIDE_100",
        parameters={"a": a, "b": b, "operation": op, "answer": answer},
    )


def _generate_rounding(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        number = rng.randint(10, 99)
        place = 10
        place_name = "ten"
    else:
        number = rng.randint(100, 999)
        place = 100
        place_name = "hundred"
    rounded = round(number / place) * place
    return GeneratedProblem(
        prompt=f"Round {number} to the nearest {place_name}.",
        canonical_answer=str(rounded),
        difficulty=difficulty,
        problem_type="ROUNDING",
        parameters={"number": number, "place": place_name, "rounded": rounded},
    )


def _generate_fraction_compare(rng: random.Random, difficulty: int) -> GeneratedProblem:
    denominators = [2, 3, 4, 6, 8]
    d1, d2 = rng.sample(denominators, 2)
    n1 = rng.randint(1, d1 - 1)
    n2 = rng.randint(1, d2 - 1)
    from fractions import Fraction

    f1 = Fraction(n1, d1)
    f2 = Fraction(n2, d2)
    if f1 > f2:
        answer = ">"
    elif f1 < f2:
        answer = "<"
    else:
        answer = "="
    return GeneratedProblem(
        prompt=f"Compare: {n1}/{d1} ___ {n2}/{d2}. Use >, <, or =.",
        canonical_answer=answer,
        difficulty=difficulty,
        problem_type="FRACTION_COMPARE",
        parameters={"numerator1": n1, "denominator1": d1, "numerator2": n2, "denominator2": d2},
    )


def _generate_fraction_on_number_line(rng: random.Random, difficulty: int) -> GeneratedProblem:
    denominator = rng.choice([2, 3, 4, 6, 8])
    numerator = rng.randint(1, denominator - 1)
    return GeneratedProblem(
        prompt=f"Where is the fraction {numerator}/{denominator} located on a number line from 0 to 1?",
        canonical_answer=f"{numerator}/{denominator}",
        difficulty=difficulty,
        problem_type="FRACTION_NUMBER_LINE",
        parameters={"numerator": numerator, "denominator": denominator},
    )


def _generate_area_perimeter_rectangle(rng: random.Random, difficulty: int) -> GeneratedProblem:
    length = rng.randint(2, 10)
    width = rng.randint(2, 10)
    op = rng.choice(["area", "perimeter"])
    if op == "area":
        answer = length * width
        prompt = f"A rectangle has length {length} units and width {width} units. What is its area?"
    else:
        answer = 2 * (length + width)
        prompt = (
            f"A rectangle has length {length} units and width {width} units. What is its perimeter?"
        )
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "AREA_PERIMETER_RECTANGLE",
        parameters={"length": length, "width": width, "measure": op},
    )


def _generate_elapsed_time(rng: random.Random, difficulty: int) -> GeneratedProblem:
    start_hour = rng.randint(1, 11)
    start_minute = rng.choice([0, 15, 30, 45])
    elapsed = rng.choice([15, 30, 45, 60, 90])
    start_total = start_hour * 60 + start_minute
    end_total = start_total + elapsed
    end_hour = (end_total // 60) % 12
    if end_hour == 0:
        end_hour = 12
    end_minute = end_total % 60
    start_str = f"{start_hour}:{start_minute:02d}"
    end_str = f"{end_hour}:{end_minute:02d}"
    return GeneratedProblem(
        prompt=f"A movie starts at {start_str} and ends at {end_str}. How many minutes long is the movie?",
        canonical_answer=str(elapsed),
        difficulty=difficulty,
        problem_type="ELAPSED_TIME",
        parameters={"start": start_str, "end": end_str, "elapsed": elapsed},
    )


def _generate_line_plot_read(rng: random.Random, difficulty: int) -> GeneratedProblem:
    data_points = [rng.randint(1, 10) for _ in range(rng.randint(8, 15))]
    value = rng.choice(list(set(data_points)))
    answer = data_points.count(value)
    return GeneratedProblem(
        prompt=f"A line plot shows these measurements in inches: {data_points}. How many measurements are {value} inches?",
        canonical_answer=str(answer),
        difficulty=difficulty,
        problem_type="LINE_PLOT_READ",
        parameters={"data": data_points, "value": value, "count": answer},
    )


def _generate_classify_shape(rng: random.Random, difficulty: int) -> GeneratedProblem:
    shapes = ["quadrilateral", "parallelogram", "rectangle", "rhombus", "square", "trapezoid"]
    shape = rng.choice(shapes)
    attr_map = {
        "quadrilateral": "4 sides",
        "parallelogram": "2 pairs of parallel sides",
        "rectangle": "4 right angles",
        "rhombus": "4 equal sides",
        "square": "4 equal sides and 4 right angles",
        "trapezoid": "at least 1 pair of parallel sides",
    }
    answer = attr_map[shape]
    return GeneratedProblem(
        prompt=f"What is the defining attribute of a {shape}?",
        canonical_answer=answer,
        difficulty=difficulty,
        problem_type="CLASSIFY_SHAPE",
        parameters={"shape": shape, "attribute": answer},
    )


def _generate_lines_parallel_perpendicular(rng: random.Random, difficulty: int) -> GeneratedProblem:
    relation = rng.choice(["parallel", "perpendicular"])
    if relation == "parallel":
        answer = "parallel"
        prompt = "Two lines in the same plane never meet. What are they called?"
    else:
        answer = "perpendicular"
        prompt = "Two lines meet at a right angle. What are they called?"
    return GeneratedProblem(
        prompt,
        answer,
        difficulty,
        "LINES_PARALLEL_PERPENDICULAR",
        parameters={"relation": relation},
    )


def _generate_multiply_by_whole(rng: random.Random, difficulty: int) -> GeneratedProblem:
    whole = rng.randint(2, 9)
    denominator = rng.randint(2, 8)
    numerator = rng.randint(1, denominator - 1)
    answer_num = whole * numerator
    return GeneratedProblem(
        prompt=f"What is {whole} × {numerator}/{denominator}?",
        canonical_answer=f"{answer_num}/{denominator}",
        difficulty=difficulty,
        problem_type="MULTIPLY_FRACTION_BY_WHOLE",
        parameters={"whole": whole, "numerator": numerator, "denominator": denominator},
    )


def _generate_add_subtract_unlike_fractions(
    rng: random.Random, difficulty: int
) -> GeneratedProblem:
    from fractions import Fraction

    d1, d2 = rng.sample([2, 3, 4, 5, 6, 8, 10], 2)
    n1 = rng.randint(1, d1 - 1)
    n2 = rng.randint(1, d2 - 1)
    op = rng.choice(["+", "-"])
    f1 = Fraction(n1, d1)
    f2 = Fraction(n2, d2)
    result = f1 + f2 if op == "+" else f1 - f2
    if result <= 0:
        result = f1 + f2
        op = "+"
    prompt = f"What is {n1}/{d1} {op} {n2}/{d2}?"
    return GeneratedProblem(
        prompt,
        f"{result.numerator}/{result.denominator}",
        difficulty,
        "ADD_SUBTRACT_UNLIKE_FRACTIONS",
        parameters={
            "numerator1": n1,
            "denominator1": d1,
            "numerator2": n2,
            "denominator2": d2,
            "operation": op,
        },
    )


def _generate_multiply_fractions(rng: random.Random, difficulty: int) -> GeneratedProblem:
    from fractions import Fraction

    denominators = [2, 3, 4, 5, 6, 8]
    d1, d2 = rng.sample(denominators, 2)
    n1 = rng.randint(1, d1 - 1)
    n2 = rng.randint(1, d2 - 1)
    result = Fraction(n1, d1) * Fraction(n2, d2)
    prompt = f"What is {n1}/{d1} × {n2}/{d2}?"
    return GeneratedProblem(
        prompt,
        f"{result.numerator}/{result.denominator}",
        difficulty,
        "MULTIPLY_FRACTIONS",
        parameters={"numerator1": n1, "denominator1": d1, "numerator2": n2, "denominator2": d2},
    )


def _generate_divide_fractions(rng: random.Random, difficulty: int) -> GeneratedProblem:
    from fractions import Fraction

    d = rng.choice([2, 3, 4, 5, 6, 8])
    n = rng.randint(1, d - 1)
    whole = rng.randint(2, 9)
    fraction = Fraction(n, d)
    result = Fraction(whole) / fraction
    prompt = f"How many servings of {n}/{d} are in {whole}?"
    return GeneratedProblem(
        prompt,
        f"{result.numerator}/{result.denominator}",
        difficulty,
        "DIVIDE_FRACTIONS",
        parameters={"whole": whole, "numerator": n, "denominator": d},
    )


def _generate_powers_of_ten(rng: random.Random, difficulty: int) -> GeneratedProblem:
    exponent = rng.randint(1, 4)
    answer = 10**exponent
    prompt = f"What is 10^{exponent}?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "POWERS_OF_TEN",
        parameters={"exponent": exponent, "base": 10},
    )


def _generate_decimal_operations(rng: random.Random, difficulty: int) -> GeneratedProblem:
    from decimal import Decimal

    op = rng.choice(["+", "-"])
    a = (
        Decimal(rng.randint(1, 99)) / 10
        if rng.random() < 0.5
        else Decimal(rng.randint(1, 999)) / 100
    )
    b = (
        Decimal(rng.randint(1, 99)) / 10
        if rng.random() < 0.5
        else Decimal(rng.randint(1, 999)) / 100
    )
    if op == "+":
        answer = a + b
        prompt = f"What is {a} + {b}?"
    else:
        if a < b:
            a, b = b, a
        answer = a - b
        prompt = f"What is {a} - {b}?"
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "DECIMAL_OPERATIONS",
        parameters={"a": str(a), "b": str(b), "operation": op},
    )


def _generate_measurement_conversion(rng: random.Random, difficulty: int) -> GeneratedProblem:
    conversions = [
        ("m", "cm", 100),
        ("km", "m", 1000),
        ("kg", "g", 1000),
        ("L", "mL", 1000),
        ("ft", "in", 12),
    ]
    from_unit, to_unit, factor = rng.choice(conversions)
    value = rng.randint(1, 9)
    answer = value * factor
    prompt = f"Convert {value} {from_unit} to {to_unit}."
    return GeneratedProblem(
        prompt,
        str(answer),
        difficulty,
        "MEASUREMENT_CONVERSION",
        parameters={"value": value, "from": from_unit, "to": to_unit, "factor": factor},
    )


def _generate_arithmetic(rng: random.Random, difficulty: int) -> GeneratedProblem:
    generated = (
        _generate_fraction_add(rng, difficulty)
        if rng.random() < 0.5
        else _generate_integer_sum(rng, difficulty)
    )
    return GeneratedProblem(
        generated.prompt,
        generated.canonical_answer,
        difficulty,
        "ARITHMETIC",
        parameters=generated.parameters,
    )


def _generate_linear_relation(rng: random.Random, difficulty: int) -> GeneratedProblem:
    generated = _generate_linear_function(rng, difficulty)
    return GeneratedProblem(
        generated.prompt,
        generated.canonical_answer,
        difficulty,
        "LINEAR_RELATION",
        parameters=generated.parameters,
    )


GENERATORS: dict[str, Callable[[random.Random, int], GeneratedProblem]] = {
    "ARITHMETIC": _generate_arithmetic,
    "SIMPLIFY_EXPRESSION": _generate_simplify_expression,
    "COMBINE_LIKE_TERMS": _generate_combine_like_terms,
    "POLYNOMIAL_ADD_SUBTRACT": _generate_polynomial_add_subtract,
    "SOLVE_EQUATION": _generate_solve_equation,
    "LINEAR_FUNCTION": _generate_linear_function,
    "LINEAR_GRAPH": _generate_linear_graph,
    "QUADRATIC_FUNCTION": _generate_quadratic_function,
    "POLYNOMIAL_FUNCTION": _generate_polynomial_function,
    "SOLID_VOLUME": _generate_solid_volume,
    "GEOMETRY_2D": _generate_geometry_2d,
    "TRANSFORMATION": _generate_transformation,
    "SIMILARITY": _generate_similarity,
    "SYSTEM_OF_EQUATIONS": _generate_system,
    "STATISTICS": _generate_statistics,
    "LINEAR_RELATION": _generate_linear_relation,
    "INTEGER_OPERATIONS": _generate_integer_sum,
    "INTEGER_COMPARE": _generate_integer_compare,
    "FRACTION_OPERATIONS": _generate_fraction_add,
    "FRACTION_SUBTRACT": _generate_fraction_subtract,
    "WORD_PROBLEM": _generate_word_problem,
    "ALGEBRA_WORD_PROBLEM": _generate_algebra_word_problem,
    "EQUAL_GROUPS": _generate_equal_groups,
    "EQUAL_SHARING": _generate_equal_sharing,
    "UNIT_FRACTION": _generate_unit_fraction,
    "RECTANGLE_AREA": _generate_rectangle_area,
    "ADDITION_WITHIN_20": _generate_addition_within_20,
    "SUBTRACTION_WITHIN_20": _generate_subtraction_within_20,
    "ADDITION_WITHIN_100": _generate_addition_within_100,
    "SUBTRACTION_WITHIN_100": _generate_subtraction_within_100,
    "PLACE_VALUE_BASE_TEN": _generate_place_value_base_ten,
    "MONEY_COUNT": _generate_money_count,
    "TIME_TO_HOUR_HALF_HOUR": _generate_time_to_hour_half_hour,
    "MULTI_DIGIT_MULTIPLICATION": _generate_multi_digit_multiplication,
    "LONG_DIVISION": _generate_long_division,
    "FRACTION_EQUIVALENCE": _generate_fraction_equivalence,
    "FRACTION_ADD_SUBTRACT_LIKE": _generate_fraction_add_subtract_like,
    "FRACTION_MULTIPLY": _generate_fraction_multiply,
    "DECIMAL_PLACE_VALUE": _generate_decimal_place_value,
    "ANGLE_MEASUREMENT": _generate_angle_measurement,
    "COORDINATE_PLANE": _generate_coordinate_plane,
    "VOLUME": _generate_volume,
    "NUMBER_SEQUENCE": _generate_number_sequence,
    "COMPARE_NUMBERS": _generate_compare_numbers,
    "WORD_PROBLEM_ADD_SUB_20": _generate_word_problem_add_sub_20,
    "WORD_PROBLEM_ADD_SUB_100": _generate_word_problem_add_sub_100,
    "NUMBER_PATTERN": _generate_number_pattern,
    "EQUATION_BALANCE": _generate_equation_balance,
    "COMPARE_LENGTH": _generate_compare_length,
    "TIME_TO_5_MINUTES": _generate_time_to_5_minutes,
    "GEOMETRY_SHAPES": _generate_geometry_shapes,
    "FRACTION_HALVES_THIRDS_FOURTHS": _generate_fraction_halves_thirds_fourths,
    "BAR_GRAPH_READ": _generate_bar_graph_read,
    "PICTURE_GRAPH_READ": _generate_picture_graph_read,
    "MULTIPLICATION_WITHIN_100": _generate_multiplication_within_100,
    "DIVISION_WITHIN_100": _generate_division_within_100,
    "WORD_PROBLEM_MULTIPLY_DIVIDE_100": _generate_word_problem_multiply_divide_100,
    "ROUNDING": _generate_rounding,
    "FRACTION_COMPARE": _generate_fraction_compare,
    "FRACTION_NUMBER_LINE": _generate_fraction_on_number_line,
    "AREA_PERIMETER_RECTANGLE": _generate_area_perimeter_rectangle,
    "ELAPSED_TIME": _generate_elapsed_time,
    "LINE_PLOT_READ": _generate_line_plot_read,
    "CLASSIFY_SHAPE": _generate_classify_shape,
    "LINES_PARALLEL_PERPENDICULAR": _generate_lines_parallel_perpendicular,
    "MULTIPLY_FRACTION_BY_WHOLE": _generate_multiply_by_whole,
    "ADD_SUBTRACT_UNLIKE_FRACTIONS": _generate_add_subtract_unlike_fractions,
    "MULTIPLY_FRACTIONS": _generate_multiply_fractions,
    "DIVIDE_FRACTIONS": _generate_divide_fractions,
    "POWERS_OF_TEN": _generate_powers_of_ten,
    "DECIMAL_OPERATIONS": _generate_decimal_operations,
    "MEASUREMENT_CONVERSION": _generate_measurement_conversion,
}


_ARITHMETIC_MC_TYPES = {
    "ADDITION_WITHIN_20",
    "SUBTRACTION_WITHIN_20",
    "ADDITION_WITHIN_100",
    "SUBTRACTION_WITHIN_100",
    "MULTIPLICATION_WITHIN_100",
    "MULTI_DIGIT_MULTIPLICATION",
    "DIVISION_WITHIN_100",
}


def _mc_transform(candidate: GeneratedProblem, rng: random.Random) -> GeneratedProblem | None:
    """Build a multiple-choice variant with misconception-coded distractors.

    Distractors are computed from the problem's parameters so each wrong option
    encodes a real error pattern from the misconception catalog. Returns None
    when the candidate's type/tier has no distractor construction.
    """
    p = candidate.parameters or {}
    correct_text: str | None = None
    distractors: list[tuple[str, str | None]] = []

    if candidate.problem_type == "SOLVE_EQUATION":
        x = p.get("x")
        if not isinstance(x, int):
            return None
        correct_text = f"x = {x}"
        tier = p.get("tier")
        if tier == "add_inverse":
            b, c = p["b"], x + p["b"]
            distractors = [
                (f"x = {c + b}", "EQ_001"),  # added instead of subtracted
                (f"x = {b - c}", "EQ_001"),  # reversed subtraction (b - c)
                (f"x = {x + 1}", None),
            ]
        elif tier == "coefficient":
            a, c = p["a"], p["a"] * x
            distractors = [
                (f"x = {c * a}", "EQ_003"),  # multiplied instead of divided
                (f"x = {c + a}", "EQ_001"),  # added coefficient instead of dividing
                (f"x = {-x}", None),
            ]
        elif tier == "two_step":
            a, b, c = p["a"], p["b"], p["a"] * x + p["b"]
            distractors = [(f"x = {c - b}", "EQ_002")]  # stopped after undoing b
            if (c + b) % a == 0:
                distractors.append((f"x = {(c + b) // a}", "EQ_001"))
            distractors += [(f"x = {-x}", "ALG_002"), (f"x = {x + 1}", None)]
        elif tier == "distribute_equation":
            a, b, c = p["a"], p["b"], p["a"] * (x + p["b"])
            distractors = [(f"x = {x + b}", "EQ_002")]  # divided by a, forgot -b
            if (c - b) % a == 0:
                distractors.append((f"x = {(c - b) // a}", "DIST_001"))
            distractors += [(f"x = {-x}", "ALG_002"), (f"x = {x - 1}", None)]
    elif candidate.problem_type == "SIMPLIFY_EXPRESSION" and "sign" in p:
        a, b, sign = p["a"], p["b"], p["sign"]
        correct_text = candidate.canonical_answer
        inner = b if sign == "+" else -b
        distractors = [
            (_fmt_expr(a, inner), "DIST_001"),  # only first term multiplied
            (f"{a * b}x", "ALG_001"),  # multiplied everything together
            (_fmt_expr(a, a + inner), "EQ_003"),  # added instead of multiplying
        ]
    elif candidate.problem_type == "COMBINE_LIKE_TERMS":
        a, b, constant, variable = (p["a"], p["b"], p["constant"], p["variable"])
        correct_text = candidate.canonical_answer
        distractors = [
            (_fmt_expr(a - b, constant, variable), "NUM_001"),  # sign slip on second term
            (_fmt_expr(a + b + 1, constant, variable), None),
            (_fmt_expr(a + b - 1, constant, variable), None),
        ]
        if constant:
            distractors.insert(
                0,
                (_fmt_term(a + b + constant, variable), "ALG_001"),  # folded constant in
            )
    elif candidate.problem_type in _ARITHMETIC_MC_TYPES:
        a, b, op = p.get("a"), p.get("b"), p.get("operation")
        if not isinstance(a, int) or not isinstance(b, int) or not isinstance(op, str):
            return None
        correct_text = candidate.canonical_answer
        correct = int(correct_text)
        if op == "+":
            distractors = [
                (str(a - b), None),  # switched to subtraction
                (str(correct + 10), None),  # place-value slip
                (str(correct - 1), None),  # off by one
            ]
        elif op == "-":
            distractors = [
                (str(a + b), None),  # switched to addition
                (str(correct + 10), None),
                (str(b - a), None),  # reversed operands
            ]
        elif op == "×":
            distractors = [
                (str(a + b), None),  # added instead of multiplied
                (str(a * (b + 1)), None),  # adjacent fact
                (str(a * (b - 1)), None),  # adjacent fact
            ]
        elif op == "÷":
            distractors = [
                (str(correct + 1), None),
                (str(correct - 1), None),
                (str(b), None),  # returned the divisor
            ]
        else:
            return None
    elif candidate.problem_type == "INTEGER_OPERATIONS":
        a, b = p.get("a"), p.get("b")
        if not isinstance(a, int) or not isinstance(b, int):
            return None
        correct = a + b
        correct_text = str(correct)
        distractors = [(str(a - b), "NUM_001")]  # sign flip on second operand
        if a < 0 or b < 0:
            distractors.append((str(abs(a) + abs(b)), "NUM_002"))
        distractors.append((str(correct + 1), None))
    elif candidate.problem_type == "FRACTION_OPERATIONS":
        n1, d1, n2, d2 = p.get("n1"), p.get("d1"), p.get("n2"), p.get("d2")
        if not all(isinstance(v, int) for v in (n1, d1, n2, d2)):
            return None
        correct_text = candidate.canonical_answer
        distractors = [
            (f"{n1 + n2}/{d1 + d2}", "NUM_003"),  # added across
            (f"{n1 + n2}/{d1}", None),  # kept one denominator
        ]
        if d1 != d2:
            distractors.append((f"{n1 + n2}/{d2}", None))
    elif candidate.problem_type == "FRACTION_ADD_SUBTRACT_LIKE":
        n1, n2, denom, op = (
            p.get("n1"),
            p.get("n2"),
            p.get("denominator"),
            p.get("operation"),
        )
        if not all(isinstance(v, int) for v in (n1, n2, denom)):
            return None
        correct_text = candidate.canonical_answer
        if op == "+":
            distractors = [
                (f"{n1 + n2}/{denom * 2}", "NUM_003"),  # added denominators too
                (f"{n1 + n2 + 1}/{denom}", None),
            ]
        else:
            distractors = [
                (f"{n1 + n2}/{denom}", None),  # added instead of subtracted
                (f"{abs(n1 - n2)}/{denom * 2}", "NUM_003"),
            ]
    else:
        return None

    if correct_text is None:
        return None
    # Dedupe against the correct answer and each other; pad with near misses.
    seen = {correct_text}
    unique: list[tuple[str, str | None]] = []
    for text, code in distractors:
        if text not in seen:
            seen.add(text)
            unique.append((text, code))
    while len(unique) < 3:
        if correct_text.lstrip("-").isdigit():
            pad = str(int(correct_text) + rng.choice([-9, -5, -2, -1, 1, 2, 5, 9]))
        elif correct_text.startswith("x ="):
            pad = f"x = {rng.randint(-15, 15)}"
        else:
            pad = f"{rng.randint(1, 12)}/{rng.randint(2, 9)}"
        if pad not in seen and pad != correct_text:
            seen.add(pad)
            unique.append((pad, None))
    unique = unique[:3]
    rng.shuffle(unique)

    options = unique + [(correct_text, None)]
    rng.shuffle(options)
    choices = [
        {
            "id": chr(ord("a") + i),
            "text": text,
            **({"misconception_code": code} if code else {}),
        }
        for i, (text, code) in enumerate(options)
    ]
    correct_id = next(c["id"] for c in choices if c["text"] == correct_text)
    return GeneratedProblem(
        prompt=candidate.prompt + " Choose the correct answer.",
        canonical_answer=correct_id,
        difficulty=candidate.difficulty,
        problem_type=candidate.problem_type,
        context=candidate.context,
        parameters={**p, "answer_kind": "MULTIPLE_CHOICE"},
        answer_kind="MULTIPLE_CHOICE",
        choices=choices,
    )


def _family_metadata(generated: GeneratedProblem) -> tuple[str, dict]:
    """Return stable family identity and minimized deterministic parameters.

    Family identity is application-owned and independent of curriculum mapping.
    Word-problem templates are distinct families; other generators currently
    have one family per generator until their representations are split.
    """
    if generated.context is not None:
        template = generated.context.get("template")
        parameters = generated.context.get("parameters") or {}
        if template:
            return f"{generated.problem_type}:{template}", dict(parameters)
    return generated.problem_type, dict(generated.parameters or {})


def _fingerprint(family: str, parameters: dict) -> tuple:
    def freeze(value):
        if isinstance(value, list):
            return tuple(freeze(v) for v in value)
        if isinstance(value, dict):
            return tuple(sorted((k, freeze(v)) for k, v in value.items()))
        return value

    return (family, tuple(sorted((k, freeze(v)) for k, v in parameters.items())))


def _existing_generated_keys(db: Session, skill_id: uuid.UUID) -> tuple[set, set]:
    """(prompts, (problem_family, parameters) fingerprints) already in the pool."""
    rows = db.execute(
        select(Problem.prompt, Problem.solution).where(Problem.primary_skill_id == skill_id)
    ).all()
    prompts = {row[0] for row in rows}
    fingerprints = {
        _fingerprint(solution["problem_family"], solution.get("parameters") or {})
        for _, solution in rows
        if isinstance(solution, dict) and solution.get("problem_family")
    }
    return prompts, fingerprints


def _possible_families(problem_type: str) -> set[str]:
    if problem_type == "WORD_PROBLEM":
        return {"WORD_PROBLEM:percent_of", "WORD_PROBLEM:unit_rate"}
    return {problem_type}


# Graph-read tiers share a constant prompt per tier ("What is the slope of the
# line shown?") — the rendered parameters, not the text, distinguish them. The
# prompt-dedupe check would otherwise starve these families entirely.
PROMPT_SHARED_TYPES = {
    "LINEAR_GRAPH",
    "COORDINATE_PLANE",
    "QUADRATIC_FUNCTION",
    "POLYNOMIAL_FUNCTION",
    "SOLID_VOLUME",
    "GEOMETRY_2D",
    "ANGLE_MEASUREMENT",
    "TRANSFORMATION",
    "SIMILARITY",
    "SYSTEM_OF_EQUATIONS",
    "STATISTICS",
}


def generate_problem(
    db: Session,
    *,
    skill_id: uuid.UUID,
    difficulty: int,
    problem_type: str | None = None,
    family: str | None = None,
    avoid_family: str | None = None,
    answer_kind: str | None = None,
    student_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    rng: random.Random | None = None,
) -> Problem | None:
    rng = rng or random.Random()
    if problem_type is not None:
        supported = [problem_type] if problem_type in GENERATORS else []
    else:
        available = db.scalars(
            select(Problem.problem_type).where(Problem.primary_skill_id == skill_id).distinct()
        ).all()
        supported = [t for t in available if t in GENERATORS]
    if not supported:
        return None
    possible = {f for t in supported for f in _possible_families(t)}
    if family is not None:
        if family not in possible:
            return None
        supported = [t for t in supported if family in _possible_families(t)]
    can_avoid = avoid_family is not None and len(possible - {avoid_family}) >= 1
    existing_prompts, existing_keys = _existing_generated_keys(db, skill_id)
    generated = None
    for _ in range(8):
        candidate = GENERATORS[rng.choice(supported)](rng, difficulty)
        if answer_kind == "MULTIPLE_CHOICE":
            transformed = _mc_transform(candidate, rng)
            if transformed is None:
                continue
            candidate = transformed
        family_id, parameters = _family_metadata(candidate)
        if family is not None and family_id != family:
            continue
        if can_avoid and family_id == avoid_family:
            continue
        if (
            (
                candidate.prompt not in existing_prompts
                or family_id in PROMPT_SHARED_TYPES
            )
            and _fingerprint(family_id, parameters) not in existing_keys
        ):
            generated = candidate
            break
    if generated is None:
        return None
    prompt = generated.prompt
    contextualizer = _module_contextualizer()
    if generated.context is not None and contextualizer is not None:
        narrative = _metered_contextualize(
            db,
            contextualizer,
            template=generated.context["template"],
            parameters=generated.context["parameters"],
            canonical_answer=generated.canonical_answer,
            student_id=student_id,
            session_id=session_id,
        )
        if narrative is not None:
            prompt = narrative.prompt
    family_id, parameters = _family_metadata(generated)
    problem = Problem(
        primary_skill_id=skill_id,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        prompt=prompt,
        canonical_answer=generated.canonical_answer,
        answer_kind=generated.answer_kind,
        choices=generated.choices,
        solution={
            "generated": True,
            "generator": generated.problem_type,
            "problem_family": family_id,
            "parameters": parameters,
            "difficulty": difficulty,
        },
        source_type="GENERATED",
    )
    db.add(problem)
    db.flush()
    return problem


def regenerate_variant(
    db: Session,
    *,
    source_problem: Problem,
    student_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    rng: random.Random | None = None,
) -> Problem | None:
    """Re-serve a missed generated problem with fresh parameters (same template,
    same difficulty, different numbers). Returns None for curated problems or
    unsupported templates."""
    metadata = source_problem.solution or {}
    generator = metadata.get("generator")
    if source_problem.source_type != "GENERATED" or generator not in GENERATORS:
        return None
    return generate_problem(
        db,
        skill_id=source_problem.primary_skill_id,
        difficulty=int(metadata.get("difficulty") or source_problem.difficulty),
        problem_type=generator,
        family=metadata.get("problem_family"),
        student_id=student_id,
        session_id=session_id,
        rng=rng,
    )


@dataclass(frozen=True)
class SkillContentReport:
    skill_id: uuid.UUID
    problem_count: int
    families: tuple[str, ...]
    ready: bool


def content_readiness(
    db: Session, *, skill_id: uuid.UUID, min_families: int = 2
) -> SkillContentReport:
    """A skill is content-ready when it can sustain a session: at least one
    problem and either >= min_families distinct families or a generator-
    capable problem type that can produce fresh items."""
    rows = db.execute(
        select(Problem.problem_type).where(Problem.primary_skill_id == skill_id)
    ).all()
    types = {row[0] for row in rows}
    families: set[str] = set()
    for ptype in types:
        families.update(_possible_families(ptype))
    generatable = bool(types & GENERATORS.keys())
    ready = len(rows) >= 1 and (len(families) >= min_families or generatable)
    return SkillContentReport(
        skill_id=skill_id,
        problem_count=len(rows),
        families=tuple(sorted(families)),
        ready=ready,
    )
