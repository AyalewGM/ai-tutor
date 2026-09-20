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


@dataclass(frozen=True)
class GeneratedProblem:
    prompt: str
    canonical_answer: str
    difficulty: int
    problem_type: str
    context: dict | None = None
    parameters: dict | None = None


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
    else:
        a, b = rng.randint(2, 6), rng.randint(-9, 9)
        prompt = f"{a}({_fmt_expr(1, b)}) = {a * (x + b)}"
        parameters = {"tier": "distribute_equation", "a": a, "b": b, "x": x}
    return GeneratedProblem(
        prompt, f"x={x}", difficulty, "SOLVE_EQUATION", parameters=parameters
    )


def _generate_linear_function(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        m = rng.randint(1, 8)
        b = rng.randint(-8, 8) if difficulty == 2 else rng.randint(0, 8)
        prompt = (
            f"A line has slope {m} and y-intercept {b}. "
            "Write its equation in slope-intercept form."
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
    return GeneratedProblem(
        prompt, answer, difficulty, "LINEAR_FUNCTION", parameters=parameters
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
        prompt, str(a + b), difficulty, "INTEGER_OPERATIONS",
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
        prompt, str(max(a, b)), difficulty, "INTEGER_COMPARE",
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
        prompt, answer, difficulty, "FRACTION_OPERATIONS",
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
    prompt = (
        f"Evaluate {f1.numerator}/{f1.denominator} - "
        f"{f2.numerator}/{f2.denominator}."
    )
    return GeneratedProblem(
        prompt, answer, difficulty, "FRACTION_SUBTRACT",
        parameters={
            "n1": f1.numerator, "d1": f1.denominator,
            "n2": f2.numerator, "d2": f2.denominator,
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
        prompt, answer, difficulty, "WORD_PROBLEM",
        context=context, parameters=parameters,
    )


def _generate_arithmetic(rng: random.Random, difficulty: int) -> GeneratedProblem:
    generated = (
        _generate_fraction_add(rng, difficulty)
        if rng.random() < 0.5
        else _generate_integer_sum(rng, difficulty)
    )
    return GeneratedProblem(
        generated.prompt, generated.canonical_answer, difficulty, "ARITHMETIC",
        parameters=generated.parameters,
    )


def _generate_linear_relation(rng: random.Random, difficulty: int) -> GeneratedProblem:
    generated = _generate_linear_function(rng, difficulty)
    return GeneratedProblem(
        generated.prompt, generated.canonical_answer, difficulty, "LINEAR_RELATION",
        parameters=generated.parameters,
    )


GENERATORS: dict[str, Callable[[random.Random, int], GeneratedProblem]] = {
    "ARITHMETIC": _generate_arithmetic,
    "SIMPLIFY_EXPRESSION": _generate_simplify_expression,
    "SOLVE_EQUATION": _generate_solve_equation,
    "LINEAR_FUNCTION": _generate_linear_function,
    "LINEAR_RELATION": _generate_linear_relation,
    "INTEGER_OPERATIONS": _generate_integer_sum,
    "INTEGER_COMPARE": _generate_integer_compare,
    "FRACTION_OPERATIONS": _generate_fraction_add,
    "FRACTION_SUBTRACT": _generate_fraction_subtract,
    "WORD_PROBLEM": _generate_word_problem,
}


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
    return (family, tuple(sorted(parameters.items())))


def _existing_generated_keys(db: Session, skill_id: uuid.UUID) -> tuple[set, set]:
    """(prompts, (problem_family, parameters) fingerprints) already in the pool."""
    rows = db.execute(
        select(Problem.prompt, Problem.solution).where(
            Problem.primary_skill_id == skill_id
        )
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


def generate_problem(
    db: Session,
    *,
    skill_id: uuid.UUID,
    difficulty: int,
    problem_type: str | None = None,
    family: str | None = None,
    avoid_family: str | None = None,
    rng: random.Random | None = None,
) -> Problem | None:
    rng = rng or random.Random()
    if problem_type is not None:
        supported = [problem_type] if problem_type in GENERATORS else []
    else:
        available = db.scalars(
            select(Problem.problem_type)
            .where(Problem.primary_skill_id == skill_id)
            .distinct()
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
        family_id, parameters = _family_metadata(candidate)
        if family is not None and family_id != family:
            continue
        if can_avoid and family_id == avoid_family:
            continue
        if (
            candidate.prompt not in existing_prompts
            and _fingerprint(family_id, parameters) not in existing_keys
        ):
            generated = candidate
            break
    if generated is None:
        return None
    prompt = generated.prompt
    contextualizer = _module_contextualizer()
    if generated.context is not None and contextualizer is not None:
        narrative = contextualizer.contextualize(
            template=generated.context["template"],
            parameters=generated.context["parameters"],
            canonical_answer=generated.canonical_answer,
        )
        if narrative:
            prompt = narrative
    family_id, parameters = _family_metadata(generated)
    problem = Problem(
        primary_skill_id=skill_id,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        prompt=prompt,
        canonical_answer=generated.canonical_answer,
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
