import random
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Problem


@dataclass(frozen=True)
class GeneratedProblem:
    prompt: str
    canonical_answer: str
    difficulty: int
    problem_type: str


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
    else:
        a, c = rng.randint(2, 9), rng.randint(2, 9)
        b = rng.randint(-9, 9)
        d = rng.randint(-9, 9)
        prompt = f"{_fmt_expr(a, b)} + {_fmt_expr(c, d)}"
        prompt = prompt.replace("+ -", "- ")
        answer = _fmt_expr(a + c, b + d)
    return GeneratedProblem(prompt, answer, difficulty, "SIMPLIFY_EXPRESSION")


def _generate_solve_equation(rng: random.Random, difficulty: int) -> GeneratedProblem:
    x = rng.randint(-12, 12) if difficulty >= 4 else rng.randint(1, 12)
    if difficulty <= 1:
        b = rng.randint(1, 20)
        prompt = f"x + {b} = {x + b}"
    elif difficulty == 2:
        a = rng.randint(2, 9)
        prompt = f"{a}x = {a * x}"
    elif difficulty <= 4:
        a, b = rng.randint(2, 9), rng.randint(1, 15)
        prompt = f"{_fmt_expr(a, b)} = {a * x + b}"
    else:
        a, b = rng.randint(2, 6), rng.randint(-9, 9)
        prompt = f"{a}({_fmt_expr(1, b)}) = {a * (x + b)}"
    return GeneratedProblem(prompt, f"x={x}", difficulty, "SOLVE_EQUATION")


def _generate_linear_function(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        m = rng.randint(1, 8)
        b = rng.randint(-8, 8) if difficulty == 2 else rng.randint(0, 8)
        prompt = (
            f"A line has slope {m} and y-intercept {b}. "
            "Write its equation in slope-intercept form."
        )
        answer = f"y={_fmt_expr(m, b)}"
    else:
        m = rng.randint(-8, 8)
        b = rng.randint(-9, 9)
        x = rng.randint(-6, 6)
        prompt = f"For y = {_fmt_expr(m, b)}, what is y when x = {x}?"
        answer = str(m * x + b)
    return GeneratedProblem(prompt, answer, difficulty, "LINEAR_FUNCTION")


def _generate_integer_sum(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        a, b = rng.randint(1, 20), rng.randint(1, 20)
    elif difficulty <= 4:
        a, b = rng.randint(-15, 15), rng.randint(1, 15)
    else:
        a, b = rng.randint(-20, 20), rng.randint(-20, 20)
    prompt = f"Evaluate {a} + {b}." if b >= 0 else f"Evaluate {a} - {abs(b)}."
    return GeneratedProblem(prompt, str(a + b), difficulty, "INTEGER_OPERATIONS")


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
    return GeneratedProblem(prompt, answer, difficulty, "FRACTION_OPERATIONS")


def _generate_word_problem(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        percent = rng.choice([10, 20, 25, 50])
        amount = rng.choice([40, 60, 80, 100, 120, 200])
        prompt = f"What is {percent}% of {amount}?"
        answer = str(percent * amount // 100)
    else:
        total = rng.choice([60, 90, 120, 150, 240, 300])
        hours = rng.choice([2, 3, 4, 5, 6])
        prompt = (
            f"A car travels {total} miles in {hours} hours at a constant rate. "
            "What is the unit rate in miles per hour?"
        )
        answer = str(total // hours) if total % hours == 0 else f"{total}/{hours}"
    return GeneratedProblem(prompt, answer, difficulty, "WORD_PROBLEM")


def _generate_arithmetic(rng: random.Random, difficulty: int) -> GeneratedProblem:
    generated = (
        _generate_fraction_add(rng, difficulty)
        if rng.random() < 0.5
        else _generate_integer_sum(rng, difficulty)
    )
    return GeneratedProblem(
        generated.prompt, generated.canonical_answer, difficulty, "ARITHMETIC"
    )


GENERATORS: dict[str, Callable[[random.Random, int], GeneratedProblem]] = {
    "ARITHMETIC": _generate_arithmetic,
    "SIMPLIFY_EXPRESSION": _generate_simplify_expression,
    "SOLVE_EQUATION": _generate_solve_equation,
    "LINEAR_FUNCTION": _generate_linear_function,
    "INTEGER_OPERATIONS": _generate_integer_sum,
    "FRACTION_OPERATIONS": _generate_fraction_add,
    "WORD_PROBLEM": _generate_word_problem,
}


def generate_problem(
    db: Session,
    *,
    skill_id: uuid.UUID,
    difficulty: int,
    rng: random.Random | None = None,
) -> Problem | None:
    rng = rng or random.Random()
    available = db.scalars(
        select(Problem.problem_type)
        .where(Problem.primary_skill_id == skill_id)
        .distinct()
    ).all()
    supported = [t for t in available if t in GENERATORS]
    if not supported:
        return None
    existing_prompts = {
        row[0]
        for row in db.execute(
            select(Problem.prompt).where(Problem.primary_skill_id == skill_id)
        )
    }
    generated = None
    for _ in range(5):
        candidate = GENERATORS[rng.choice(supported)](rng, difficulty)
        if candidate.prompt not in existing_prompts:
            generated = candidate
            break
    if generated is None:
        return None
    problem = Problem(
        primary_skill_id=skill_id,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        prompt=generated.prompt,
        canonical_answer=generated.canonical_answer,
        solution={"generated": True},
        source_type="GENERATED",
    )
    db.add(problem)
    db.flush()
    return problem
