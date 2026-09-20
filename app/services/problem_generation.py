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
    family: str
    parameters: dict
    context: dict | None = None


@dataclass(frozen=True)
class FamilyGenerator:
    """A stable problem family: same template, different parameter draws."""

    family: str
    generate: Callable[[random.Random, int], GeneratedProblem]


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


def _gen_simplify_distribute(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a = rng.randint(2, 9) if difficulty <= 4 else rng.choice([-9, -7, -5, -4, -3, -2, 2, 3, 4, 5, 6, 7, 8, 9])
    b = rng.randint(1, 12)
    sign = "+" if difficulty <= 2 or rng.random() < 0.5 else "-"
    prompt = f"{a}(x{sign}{b})"
    answer = _fmt_expr(a, a * b if sign == "+" else -a * b)
    return GeneratedProblem(
        prompt, answer, difficulty, "SIMPLIFY_EXPRESSION",
        family="simplify/distribute", parameters={"a": a, "b": b, "sign": sign},
    )


def _gen_simplify_combine(rng: random.Random, difficulty: int) -> GeneratedProblem:
    a, c = rng.randint(2, 9), rng.randint(2, 9)
    b = rng.randint(-9, 9)
    d = rng.randint(-9, 9)
    prompt = f"{_fmt_expr(a, b)} + {_fmt_expr(c, d)}".replace("+ -", "- ")
    answer = _fmt_expr(a + c, b + d)
    return GeneratedProblem(
        prompt, answer, difficulty, "SIMPLIFY_EXPRESSION",
        family="simplify/combine_like_terms",
        parameters={"a": a, "b": b, "c": c, "d": d},
    )


def _gen_solve_add_inverse(rng: random.Random, difficulty: int) -> GeneratedProblem:
    x = rng.randint(-9, 12) if difficulty >= 4 else rng.randint(1, 12)
    b = rng.randint(1, 20)
    prompt = f"x + {b} = {x + b}"
    return GeneratedProblem(
        prompt, f"x={x}", difficulty, "SOLVE_EQUATION",
        family="solve/add_inverse", parameters={"x": x, "b": b},
    )


def _gen_solve_coefficient(rng: random.Random, difficulty: int) -> GeneratedProblem:
    x = rng.randint(-9, 12) if difficulty >= 4 else rng.randint(1, 12)
    a = rng.randint(2, 9)
    prompt = f"{a}x = {a * x}"
    return GeneratedProblem(
        prompt, f"x={x}", difficulty, "SOLVE_EQUATION",
        family="solve/coefficient", parameters={"a": a, "x": x},
    )


def _gen_solve_two_step(rng: random.Random, difficulty: int) -> GeneratedProblem:
    x = rng.randint(-12, 12) if difficulty >= 4 else rng.randint(1, 12)
    a, b = rng.randint(2, 9), rng.randint(1, 15)
    prompt = f"{_fmt_expr(a, b)} = {a * x + b}"
    return GeneratedProblem(
        prompt, f"x={x}", difficulty, "SOLVE_EQUATION",
        family="solve/two_step", parameters={"a": a, "b": b, "x": x},
    )


def _gen_solve_distribute(rng: random.Random, difficulty: int) -> GeneratedProblem:
    x = rng.randint(-12, 12) if difficulty >= 4 else rng.randint(1, 12)
    a, b = rng.randint(2, 6), rng.randint(-9, 9)
    prompt = f"{a}({_fmt_expr(1, b)}) = {a * (x + b)}"
    return GeneratedProblem(
        prompt, f"x={x}", difficulty, "SOLVE_EQUATION",
        family="solve/distribute_equation",
        parameters={"a": a, "b": b, "x": x},
    )


def _solve_equation(rng: random.Random, difficulty: int) -> GeneratedProblem:
    """Difficulty-tiered dispatch across the equation families."""
    if difficulty <= 1:
        return _gen_solve_add_inverse(rng, difficulty)
    if difficulty == 2:
        return _gen_solve_coefficient(rng, difficulty)
    if difficulty <= 4:
        return _gen_solve_two_step(rng, difficulty)
    return _gen_solve_distribute(rng, difficulty)


def _gen_linear_write(rng: random.Random, difficulty: int) -> GeneratedProblem:
    m = rng.randint(1, 8)
    b = rng.randint(-8, 8) if difficulty >= 2 else rng.randint(0, 8)
    prompt = (
        f"A line has slope {m} and y-intercept {b}. "
        "Write its equation in slope-intercept form."
    )
    answer = f"y={_fmt_expr(m, b)}"
    return GeneratedProblem(
        prompt, answer, difficulty, "LINEAR_FUNCTION",
        family="linear/write_slope_intercept", parameters={"m": m, "b": b},
    )


def _gen_linear_evaluate(rng: random.Random, difficulty: int) -> GeneratedProblem:
    m = rng.randint(-8, 8)
    b = rng.randint(-9, 9)
    x = rng.randint(-6, 6)
    prompt = f"For y = {_fmt_expr(m, b)}, what is y when x = {x}?"
    answer = str(m * x + b)
    return GeneratedProblem(
        prompt, answer, difficulty, "LINEAR_FUNCTION",
        family="linear/evaluate", parameters={"m": m, "b": b, "x": x},
    )


def _linear_function(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        return _gen_linear_write(rng, difficulty)
    return _gen_linear_evaluate(rng, difficulty)


def _gen_integer_add(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        a, b = rng.randint(1, 20), rng.randint(1, 20)
    elif difficulty <= 4:
        a, b = rng.randint(-15, 15), rng.randint(1, 15)
    else:
        a, b = rng.randint(-20, 20), rng.randint(-20, 20)
    prompt = f"Evaluate {a} + {b}." if b >= 0 else f"Evaluate {a} - {abs(b)}."
    return GeneratedProblem(
        prompt, str(a + b), difficulty, "INTEGER_OPERATIONS",
        family="integer/add", parameters={"a": a, "b": b},
    )


def _gen_integer_compare(rng: random.Random, difficulty: int) -> GeneratedProblem:
    bound = 10 if difficulty <= 2 else 20
    a = rng.randint(-bound, bound)
    b = rng.randint(-bound, bound)
    while b == a:
        b = rng.randint(-bound, bound)
    prompt = f"Which is greater, {a} or {b}?"
    return GeneratedProblem(
        prompt, str(max(a, b)), difficulty, "INTEGER_OPERATIONS",
        family="integer/compare", parameters={"a": a, "b": b},
    )


def _fmt_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _gen_fraction_add(rng: random.Random, difficulty: int) -> GeneratedProblem:
    d1 = rng.choice([2, 3, 4, 5])
    d2 = rng.choice([2, 3, 4, 5, 6, 8])
    n1, n2 = rng.randint(1, d1 - 1), rng.randint(1, d2 - 1)
    result = Fraction(n1, d1) + Fraction(n2, d2)
    prompt = f"Evaluate {n1}/{d1} + {n2}/{d2}."
    return GeneratedProblem(
        prompt, _fmt_fraction(result), difficulty, "FRACTION_OPERATIONS",
        family="fraction/add",
        parameters={"n1": n1, "d1": d1, "n2": n2, "d2": d2},
    )


def _gen_fraction_subtract(rng: random.Random, difficulty: int) -> GeneratedProblem:
    f1 = Fraction(rng.randint(1, 4), rng.choice([2, 3, 4, 5]))
    f2 = Fraction(rng.randint(1, 7), rng.choice([2, 3, 4, 5, 6, 8]))
    while f2 >= f1:
        f2 = Fraction(rng.randint(1, 7), rng.choice([2, 3, 4, 5, 6, 8]))
    result = f1 - f2
    prompt = f"Evaluate {f1.numerator}/{f1.denominator} - {f2.numerator}/{f2.denominator}."
    return GeneratedProblem(
        prompt, _fmt_fraction(result), difficulty, "FRACTION_OPERATIONS",
        family="fraction/subtract",
        parameters={
            "n1": f1.numerator, "d1": f1.denominator,
            "n2": f2.numerator, "d2": f2.denominator,
        },
    )


def _gen_word_percent(rng: random.Random, difficulty: int) -> GeneratedProblem:
    percent = rng.choice([10, 20, 25, 50])
    amount = rng.choice([40, 60, 80, 100, 120, 200])
    prompt = f"What is {percent}% of {amount}?"
    answer = str(percent * amount // 100)
    return GeneratedProblem(
        prompt, answer, difficulty, "WORD_PROBLEM",
        family="word/percent_of",
        parameters={"percent": percent, "amount": amount},
        context={"template": "percent_of",
                 "parameters": {"percent": percent, "amount": amount}},
    )


def _gen_word_unit_rate(rng: random.Random, difficulty: int) -> GeneratedProblem:
    total = rng.choice([60, 90, 120, 150, 240, 300])
    hours = rng.choice([2, 3, 4, 5, 6])
    prompt = (
        f"A car travels {total} miles in {hours} hours at a constant rate. "
        "What is the unit rate in miles per hour?"
    )
    answer = str(total // hours) if total % hours == 0 else f"{total}/{hours}"
    return GeneratedProblem(
        prompt, answer, difficulty, "WORD_PROBLEM",
        family="word/unit_rate",
        parameters={"distance": total, "hours": hours},
        context={"template": "unit_rate",
                 "parameters": {"distance": total, "hours": hours}},
    )


def _word_problem(rng: random.Random, difficulty: int) -> GeneratedProblem:
    if difficulty <= 2:
        return _gen_word_percent(rng, difficulty)
    return _gen_word_unit_rate(rng, difficulty)


def _retype(generated: GeneratedProblem, problem_type: str) -> GeneratedProblem:
    return GeneratedProblem(
        generated.prompt, generated.canonical_answer, generated.difficulty,
        problem_type, family=generated.family, parameters=generated.parameters,
        context=generated.context,
    )


def _family_mixer(family_generators: list, problem_type: str) -> Callable:
    def generate(rng: random.Random, difficulty: int) -> GeneratedProblem:
        return _retype(
            rng.choice(family_generators)(rng, difficulty), problem_type
        )
    return generate


GENERATOR_FAMILIES: dict[str, list[FamilyGenerator]] = {
    "SIMPLIFY_EXPRESSION": [
        FamilyGenerator("simplify/distribute", _gen_simplify_distribute),
        FamilyGenerator("simplify/combine_like_terms", _gen_simplify_combine),
    ],
    "SOLVE_EQUATION": [
        FamilyGenerator("solve/add_inverse", _gen_solve_add_inverse),
        FamilyGenerator("solve/coefficient", _gen_solve_coefficient),
        FamilyGenerator("solve/two_step", _gen_solve_two_step),
        FamilyGenerator("solve/distribute_equation", _gen_solve_distribute),
    ],
    "LINEAR_FUNCTION": [
        FamilyGenerator("linear/write_slope_intercept", _gen_linear_write),
        FamilyGenerator("linear/evaluate", _gen_linear_evaluate),
    ],
    "LINEAR_RELATION": [
        FamilyGenerator("linear/write_slope_intercept", _gen_linear_write),
        FamilyGenerator("linear/evaluate", _gen_linear_evaluate),
    ],
    "INTEGER_OPERATIONS": [
        FamilyGenerator("integer/add", _gen_integer_add),
        FamilyGenerator("integer/compare", _gen_integer_compare),
    ],
    "FRACTION_OPERATIONS": [
        FamilyGenerator("fraction/add", _gen_fraction_add),
        FamilyGenerator("fraction/subtract", _gen_fraction_subtract),
    ],
    "WORD_PROBLEM": [
        FamilyGenerator("word/percent_of", _gen_word_percent),
        FamilyGenerator("word/unit_rate", _gen_word_unit_rate),
    ],
    "ARITHMETIC": [
        FamilyGenerator("integer/add", _gen_integer_add),
        FamilyGenerator("integer/compare", _gen_integer_compare),
        FamilyGenerator("fraction/add", _gen_fraction_add),
        FamilyGenerator("fraction/subtract", _gen_fraction_subtract),
    ],
}

# Type-level dispatch preserved for callers that don't care about families.
GENERATORS: dict[str, Callable[[random.Random, int], GeneratedProblem]] = {
    "ARITHMETIC": _family_mixer(
        [g.generate for g in GENERATOR_FAMILIES["ARITHMETIC"]], "ARITHMETIC"
    ),
    "SIMPLIFY_EXPRESSION": lambda rng, d: (
        _gen_simplify_distribute(rng, d) if d <= 3 else _gen_simplify_combine(rng, d)
    ),
    "SOLVE_EQUATION": _solve_equation,
    "LINEAR_FUNCTION": _linear_function,
    "LINEAR_RELATION": lambda rng, d: _retype(_linear_function(rng, d), "LINEAR_RELATION"),
    "INTEGER_OPERATIONS": _family_mixer(
        [g.generate for g in GENERATOR_FAMILIES["INTEGER_OPERATIONS"]],
        "INTEGER_OPERATIONS",
    ),
    "FRACTION_OPERATIONS": _family_mixer(
        [g.generate for g in GENERATOR_FAMILIES["FRACTION_OPERATIONS"]],
        "FRACTION_OPERATIONS",
    ),
    "WORD_PROBLEM": _word_problem,
}


def _fingerprint(family: str, parameters: dict) -> tuple:
    return (family, tuple(sorted(parameters.items())))


def _existing_generated_keys(db: Session, skill_id: uuid.UUID) -> tuple[set, set]:
    """(prompts, (family, parameters) fingerprints) already in the skill pool."""
    rows = db.execute(
        select(Problem.prompt, Problem.solution).where(
            Problem.primary_skill_id == skill_id
        )
    ).all()
    prompts = {row[0] for row in rows}
    fingerprints = set()
    for _, solution in rows:
        if isinstance(solution, dict) and solution.get("family"):
            fingerprints.add(
                _fingerprint(solution["family"], solution.get("parameters") or {})
            )
    return prompts, fingerprints


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
        types = [problem_type]
    else:
        types = db.scalars(
            select(Problem.problem_type)
            .where(Problem.primary_skill_id == skill_id)
            .distinct()
        ).all()
    pool = [
        (t, gen)
        for t in types
        for gen in GENERATOR_FAMILIES.get(t, [])
        if family is None or gen.family == family
    ]
    alternatives = [entry for entry in pool if entry[1].family != avoid_family]
    if alternatives:
        pool = alternatives
    if not pool:
        return None
    existing_prompts, existing_keys = _existing_generated_keys(db, skill_id)
    generated = None
    for _ in range(8):
        ptype, gen = rng.choice(pool)
        candidate = gen.generate(rng, difficulty)
        if (
            candidate.prompt not in existing_prompts
            and _fingerprint(candidate.family, candidate.parameters)
            not in existing_keys
        ):
            generated = _retype(candidate, ptype)
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
    problem = Problem(
        primary_skill_id=skill_id,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        prompt=prompt,
        canonical_answer=generated.canonical_answer,
        solution={
            "generated": True,
            "generator": generated.problem_type,
            "family": generated.family,
            "parameters": generated.parameters,
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
    """Re-serve a missed generated problem with fresh parameters (same family,
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
        family=metadata.get("family"),
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
    """A skill is content-ready when it has at least one problem and at least
    `min_families` materially different families available across its problem
    types (each declared generator family counts; an ungeneratable type counts
    as a single family)."""
    rows = db.execute(
        select(Problem.problem_type).where(Problem.primary_skill_id == skill_id)
    ).all()
    types = {row[0] for row in rows}
    families: set[str] = set()
    for ptype in types:
        generators = GENERATOR_FAMILIES.get(ptype)
        if generators:
            families.update(gen.family for gen in generators)
        else:
            families.add(ptype)
    return SkillContentReport(
        skill_id=skill_id,
        problem_count=len(rows),
        families=tuple(sorted(families)),
        ready=len(rows) >= 1 and len(families) >= min_families,
    )
