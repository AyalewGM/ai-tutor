"""Draft-only exact generators for thin Algebra I linear foundations.

This module is deliberately outside ``app`` and is not registered by the
runtime.  It proposes reusable mathematical families for independent review;
it does not map a jurisdiction, select learner content, score mastery, or
write persistence records.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

MODES = ("guided", "independent")

SKILL_FAMILIES = {
    "MATH.EE.EXPR": (
        "MATH.ALG.EXPR.EVALUATE",
        "MATH.ALG.EXPR.TRANSLATE",
        "MATH.ALG.EXPR.ERROR.DISTRIBUTE",
    ),
    "MATH.EE.EQUATION.ONE": (
        "MATH.EQ.ONE.ADD_DIRECT",
        "MATH.ALG.EQ.ONE.MULT",
    ),
    "MATH.F.LINEAR.SLOPE_INTERCEPT": (
        "MATH.FUNC.LINEAR.SLOPE.TABLE",
        "MATH.FUNC.LINEAR.MODEL",
        "MATH.FUNC.LINEAR.ERROR.INTERCEPT",
    ),
}

FAMILY_SKILL = {
    family: skill
    for skill, families in SKILL_FAMILIES.items()
    for family in families
}


def _fraction(value: Fraction | int) -> str:
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _term(coefficient: Fraction, variable: str = "x") -> str:
    if coefficient == 1:
        return variable
    if coefficient == -1:
        return f"-{variable}"
    return f"{_fraction(coefficient)}{variable}"


def _linear(m: Fraction, b: Fraction) -> str:
    if b == 0:
        return f"y={_term(m)}"
    sign = "+" if b > 0 else "-"
    return f"y={_term(m)}{sign}{_fraction(abs(b))}"


def _rng(family_code: str, seed: int, mode: str) -> tuple[random.Random, str]:
    if mode not in MODES:
        raise ValueError(f"unsupported draft mode: {mode}")
    key = f"canonical-algebra-linear-foundations-r1|{family_code}|{mode}|{seed}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    return random.Random(int(digest[:16], 16)), digest[:20]


@dataclass(frozen=True)
class Variant:
    family_code: str
    canonical_skill_code: str
    structure_code: str
    mode: str
    variant_id: str
    prompt: str
    answer_kind: str
    canonical_answer: str
    oracle: dict[str, Any]
    misconception_answers: dict[str, str]
    socratic_prompts: tuple[str, ...]

    def public_payload(self) -> dict[str, Any]:
        """Return a learner-safe draft payload with no hidden evidence."""
        return {
            "variant_id": self.variant_id,
            "family_code": self.family_code,
            "canonical_skill_code": self.canonical_skill_code,
            "structure_code": self.structure_code,
            "mode": self.mode,
            "prompt": self.prompt,
            "answer_kind": self.answer_kind,
            "mastery_credit": False,
        }

    def guided_support(self) -> tuple[str, ...]:
        if self.mode != "guided":
            return ()
        return self.socratic_prompts

    def diagnose(self, answer: str) -> str | None:
        normalized = "".join(answer.lower().split()).replace("−", "-")
        for code, candidate in self.misconception_answers.items():
            if normalized == "".join(candidate.lower().split()).replace("−", "-"):
                return code
        return None


def _evaluate_expression(rng: random.Random) -> tuple:
    x = Fraction(rng.choice((-5, -3, -2, 2, 3, 5)), rng.choice((1, 2)))
    a = rng.choice((-4, -3, 2, 3, 4))
    b = rng.randint(1, 5)
    c = rng.choice((-3, -2, 2, 3))
    d = rng.randint(1, 4)
    value = a * (x + b) - c * (x - d)
    ignored_parentheses = a * x + b - c * x - d
    while ignored_parentheses == value:
        d += 1
        value = a * (x + b) - c * (x - d)
        ignored_parentheses = a * x + b - c * x - d
    prompt = f"Evaluate {a}(x + {b}) - ({c})(x - {d}) when x = {_fraction(x)}."
    oracle = {
        "x": _fraction(x), "a": a, "b": b, "c": c, "d": d,
        "left_group": _fraction(x + b), "right_group": _fraction(x - d),
        "value": _fraction(value),
    }
    wrong = {"ALG.EXPR.DROPPED_GROUPING": _fraction(ignored_parentheses)}
    hints = (
        "What value replaces every occurrence of x before any operation is done?",
        "Which grouped quantities must be evaluated before multiplying?",
        "How can you recompute both grouped terms separately to verify the total?",
    )
    return "NESTED_SIGNED_SUBSTITUTION", prompt, "EXACT_RATIONAL", _fraction(value), oracle, wrong, hints


def _translate_expression(rng: random.Random) -> tuple:
    rate = rng.choice((3, 4, 6, 8))
    fixed = rng.choice((5, 7, 9, 12))
    prompt = (
        f"A repair service charges a fixed ${fixed} inspection fee and ${rate} for each "
        "replacement part. Write the total cost C for p parts."
    )
    answer = f"C={rate}p+{fixed}"
    oracle = {"dependent": "C", "independent": "p", "rate": rate, "fixed": fixed}
    wrong = {
        "ALG.TRANSLATE.SWAPPED_RATE_FIXED": f"C={fixed}p+{rate}",
        "ALG.TRANSLATE.OMITTED_FIXED": f"C={rate}p",
    }
    hints = (
        "Which charge stays the same even when no parts are used?",
        "Which quantity repeats once for every part?",
        "What does your expression give when p = 0, and does that match the context?",
    )
    return "FIXED_PLUS_RATE_MODEL", prompt, "LINEAR_EXPRESSION", answer, oracle, wrong, hints


def _distribution_error(rng: random.Random) -> tuple:
    a = rng.choice((2, 3, 4, 5))
    b = rng.choice((2, 3, 5, 6))
    prompt = (
        f"A student rewrites -{a}(2x - {b}) as -{2*a}x - {a*b}. "
        "Name the first error and give the correctly expanded expression."
    )
    answer = f"SIGN_NOT_DISTRIBUTED_TO_CONSTANT|-{2*a}x+{a*b}"
    oracle = {
        "outside_factor": -a,
        "inside_terms": ["2x", str(-b)],
        "products": [f"-{2*a}x", str(a * b)],
        "expanded": f"-{2*a}x+{a*b}",
    }
    wrong = {
        "ALG.DISTRIBUTE.SIGN_TO_FIRST_TERM_ONLY": f"NO_ERROR|-{2*a}x-{a*b}",
        "ALG.DISTRIBUTE.MISSED_SECOND_TERM": f"MISSING_SECOND_PRODUCT|-{2*a}x-{b}",
    }
    hints = (
        "What are the two separate terms inside the parentheses?",
        "What is the sign of (-a) times (-b)?",
        "Can multiplying the expanded form by substituting x = 0 verify the constant term?",
    )
    return "NEGATIVE_DISTRIBUTION_ERROR", prompt, "ERROR_AND_EXPRESSION", answer, oracle, wrong, hints


def _additive_equation(rng: random.Random) -> tuple:
    x = Fraction(rng.randint(-12, 12), rng.choice((1, 2, 3)))
    offset = Fraction(rng.choice((-9, -7, -5, 4, 6, 8)), rng.choice((1, 2)))
    total = x + offset
    prompt = f"Solve x + ({_fraction(offset)}) = {_fraction(total)}. Show the same inverse operation on both sides."
    answer = f"x={_fraction(x)}"
    oracle = {
        "inverse_operation": f"subtract {_fraction(offset)} from both sides",
        "left_after_inverse": _fraction(x),
        "right_after_inverse": _fraction(total - offset),
        "solution": _fraction(x),
        "substitution_total": _fraction(x + offset),
    }
    wrong = {"ALG.EQ.ADD_WRONG_DIRECTION": f"x={_fraction(total + offset)}"}
    hints = (
        "Which signed quantity is combined with x?",
        "What operation undoes that quantity while preserving equality?",
        "When your solution replaces x, do both sides have the same exact value?",
    )
    return "SIGNED_RATIONAL_ADDITIVE_BALANCE", prompt, "EQUATION_SOLUTION", answer, oracle, wrong, hints


def _multiplicative_equation(rng: random.Random) -> tuple:
    x = Fraction(rng.choice((-10, -8, -6, 6, 8, 10)), rng.choice((1, 2)))
    coefficient = Fraction(rng.choice((-5, -3, 2, 3, 5)), rng.choice((2, 3, 4)))
    while abs(coefficient) == 1:
        coefficient = Fraction(rng.choice((-5, -3, 2, 3, 5)), rng.choice((2, 3, 4)))
    total = coefficient * x
    prompt = f"Solve ({_fraction(coefficient)})x = {_fraction(total)} using an equality-preserving inverse."
    answer = f"x={_fraction(x)}"
    reciprocal = 1 / coefficient
    oracle = {
        "coefficient": _fraction(coefficient),
        "inverse_multiplier": _fraction(reciprocal),
        "left_after_inverse": _fraction(reciprocal * coefficient * x),
        "right_after_inverse": _fraction(reciprocal * total),
        "solution": _fraction(x),
        "substitution_total": _fraction(coefficient * x),
    }
    wrong = {"ALG.EQ.MULTIPLY_BY_COEFFICIENT": f"x={_fraction(total * coefficient)}"}
    if coefficient < 0:
        wrong["ALG.EQ.RECIPROCAL_SIGN_LOST"] = f"x={_fraction(abs(reciprocal) * total)}"
    hints = (
        "What single factor multiplies x, including its sign?",
        "Which reciprocal makes that coefficient exactly 1?",
        "Can exact substitution reproduce the original right-hand side?",
    )
    return "SIGNED_FRACTIONAL_MULTIPLICATIVE_BALANCE", prompt, "EQUATION_SOLUTION", answer, oracle, wrong, hints


def _slope_table(rng: random.Random) -> tuple:
    slope = Fraction(rng.choice((-5, -3, -2, 2, 3, 5)), rng.choice((1, 2, 3)))
    while abs(slope) == 1:
        slope = Fraction(rng.choice((-5, -3, -2, 2, 3, 5)), rng.choice((1, 2, 3)))
    dx = slope.denominator * 2
    x0 = rng.randint(-4, 2)
    b = rng.randint(-6, 6)
    points = [(x0 + i * dx, slope * (x0 + i * dx) + b) for i in range(3)]
    table = ", ".join(f"({_fraction(x)}, {_fraction(y)})" for x, y in points)
    prompt = f"A linear table contains {table}. Determine its exact slope and explain the ratio of changes."
    answer = _fraction(slope)
    oracle = {
        "points": [[_fraction(x), _fraction(y)] for x, y in points],
        "delta_x": dx,
        "delta_y": _fraction(slope * dx),
        "slope": _fraction(slope),
    }
    wrong = {
        "FUNC.SLOPE.RECIPROCAL": _fraction(1 / slope),
        "FUNC.SLOPE.USES_OUTPUT_ONLY": _fraction(slope * dx),
    }
    hints = (
        "How much does x change between consecutive rows?",
        "How much does y change over the same interval?",
        "Does delta-y divided by delta-x agree for both intervals?",
    )
    return "UNEQUAL_STEP_TABLE_RATE", prompt, "EXACT_RATIONAL", answer, oracle, wrong, hints


def _linear_model(rng: random.Random) -> tuple:
    slope = Fraction(rng.choice((-5, -3, 2, 3, 5)), rng.choice((1, 2)))
    while abs(slope) == 1:
        slope = Fraction(rng.choice((-5, -3, 2, 3, 5)), rng.choice((1, 2)))
    dx = slope.denominator * 2
    x1 = rng.randint(-3, 1)
    b = Fraction(rng.choice(tuple(range(-8, 0)) + tuple(range(1, 9))))
    x2 = x1 + dx
    y1, y2 = slope * x1 + b, slope * x2 + b
    prompt = (
        f"A line passes through ({x1}, {_fraction(y1)}) and ({x2}, {_fraction(y2)}). "
        "Write its equation in slope-intercept form and verify both points."
    )
    answer = _linear(slope, b)
    oracle = {
        "points": [[x1, _fraction(y1)], [x2, _fraction(y2)]],
        "slope": _fraction(slope), "intercept": _fraction(b),
        "equation": answer,
        "substitution_totals": [_fraction(slope * x1 + b), _fraction(slope * x2 + b)],
    }
    wrong = {
        "FUNC.MODEL.ZERO_INTERCEPT": _linear(slope, Fraction(0)),
        "FUNC.MODEL.SLOPE_RECIPROCAL": _linear(1 / slope, b),
    }
    hints = (
        "What exact ratio of coordinate changes gives the slope?",
        "After finding m, what does y - mx equal at either point?",
        "Do both original points satisfy the same proposed equation exactly?",
    )
    return "TWO_POINT_EXACT_MODEL", prompt, "LINEAR_EQUATION", answer, oracle, wrong, hints


def _intercept_error(rng: random.Random) -> tuple:
    rate = rng.choice((4, 6, 9, 12))
    fixed = rng.choice((5, 8, 11, 15))
    hours = rng.choice((2, 3, 5))
    prompt = (
        f"A studio charges ${fixed} to enter and ${rate} per hour. A student models the cost as "
        f"C={fixed}h+{rate}. Diagnose the parameter error, write the correct model, and find C({hours})."
    )
    answer = f"SWAPPED_RATE_AND_INTERCEPT|C={rate}h+{fixed}|{rate*hours+fixed}"
    oracle = {
        "rate": rate, "intercept": fixed, "input": hours,
        "correct_model": f"C={rate}h+{fixed}",
        "verification_total": rate * hours + fixed,
        "zero_input_total": fixed,
    }
    wrong = {"FUNC.SLOPE_INTERCEPT.SWAPPED": f"NO_ERROR|C={fixed}h+{rate}|{fixed*hours+rate}"}
    hints = (
        "Which amount is paid even when h = 0?",
        "Which amount repeats once for every hour?",
        "What totals do the proposed and corrected models give at h = 0 and at the requested time?",
    )
    return "CONTEXT_PARAMETER_ERROR", prompt, "ERROR_MODEL_AND_VALUE", answer, oracle, wrong, hints


BUILDERS = {
    "MATH.ALG.EXPR.EVALUATE": _evaluate_expression,
    "MATH.ALG.EXPR.TRANSLATE": _translate_expression,
    "MATH.ALG.EXPR.ERROR.DISTRIBUTE": _distribution_error,
    "MATH.EQ.ONE.ADD_DIRECT": _additive_equation,
    "MATH.ALG.EQ.ONE.MULT": _multiplicative_equation,
    "MATH.FUNC.LINEAR.SLOPE.TABLE": _slope_table,
    "MATH.FUNC.LINEAR.MODEL": _linear_model,
    "MATH.FUNC.LINEAR.ERROR.INTERCEPT": _intercept_error,
}


def generate(family_code: str, seed: int, mode: str) -> Variant:
    if family_code not in BUILDERS:
        raise ValueError(f"unknown draft family: {family_code}")
    rng, digest = _rng(family_code, seed, mode)
    structure, prompt, kind, answer, oracle, wrong, hints = BUILDERS[family_code](rng)
    return Variant(
        family_code=family_code,
        canonical_skill_code=FAMILY_SKILL[family_code],
        structure_code=structure,
        mode=mode,
        variant_id=f"alg-lf-r1-{digest}",
        prompt=prompt,
        answer_kind=kind,
        canonical_answer=answer,
        oracle=oracle,
        misconception_answers=wrong,
        socratic_prompts=hints,
    )


def fresh_transfer(source: Variant, seed: int) -> Variant:
    """Return deterministic unseen transfer in another family of the same skill."""
    families = SKILL_FAMILIES[source.canonical_skill_code]
    index = families.index(source.family_code)
    family = families[(index + 1 + seed % (len(families) - 1)) % len(families)]
    transfer = generate(family, seed + 700_001, "independent")
    if transfer.structure_code == source.structure_code or transfer.variant_id == source.variant_id:
        raise AssertionError("fresh transfer collided with taught structure")
    return transfer


def materialize_manifest(seeds: range = range(8)) -> str:
    """Pure synthetic manifest used to prove stable, duplicate-free identities."""
    rows = []
    for family in sorted(BUILDERS):
        for mode in MODES:
            used_tasks: set[tuple[str, str]] = set()
            cursor = min(seeds, default=0)
            for _ in seeds:
                for _attempt in range(10_000):
                    item = generate(family, cursor, mode)
                    source_seed = cursor
                    cursor += 1
                    task = (item.prompt, item.canonical_answer)
                    if task not in used_tasks:
                        used_tasks.add(task)
                        break
                else:  # pragma: no cover - bounded fail-closed guard
                    raise RuntimeError(f"unable to materialize unique task for {family}/{mode}")
                rows.append({
                    "variant_id": item.variant_id,
                    "family_code": family,
                    "mode": mode,
                    "source_seed": source_seed,
                    "structure_code": item.structure_code,
                    "prompt": item.prompt,
                    "canonical_answer": item.canonical_answer,
                })
    return json.dumps(rows, sort_keys=True, separators=(",", ":"))
