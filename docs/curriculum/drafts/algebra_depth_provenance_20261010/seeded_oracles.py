"""Draft-only deterministic Grade 9 algebra variants and exact oracles.

This module is not imported by runtime code and performs no persistence.
"""

import random
from fractions import Fraction

NAMESPACE = "g9-algebra-depth-r3"
MODES = frozenset({"guided", "independent"})


def _rng(seed: int, mode: str, family_salt: int) -> random.Random:
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"unsupported mode: {mode}")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    mode_salt = 104_729 if mode == "independent" else 13_337
    return random.Random(seed * 1_000_003 + mode_salt + family_salt)


def _record(
    *, seed: int, mode: str, family: str, prompt: str, parameters: dict, answer: str
) -> dict:
    return {
        "variant_id": f"{NAMESPACE}:{mode}:{family}:{seed}",
        "mode": mode,
        "family": family,
        "prompt": prompt,
        "parameters": parameters,
        "answer_teacher_only": answer,
    }


def public_payload(record: dict) -> dict:
    """Return the content fields allowed before independent submission."""

    return {
        key: value
        for key, value in record.items()
        if key not in {"answer_teacher_only", "worked_steps", "hints"}
    }


def generate_linear_plan(seed: int, mode: str) -> dict:
    """Generate two plans with one positive integer crossover."""

    rng = _rng(seed, mode, 11)
    crossover = rng.randint(2, 12)
    rate_a = rng.randint(2, 7)
    rate_b = rate_a + rng.randint(1, 5)
    fee_b = rng.randint(1, 12)
    fee_a = fee_b + (rate_b - rate_a) * crossover
    answer = fee_a + rate_a * crossover
    return _record(
        seed=seed,
        mode=mode,
        family="LINEAR_PLAN_CROSSOVER",
        prompt=(
            f"Plan A costs {fee_a}+{rate_a}n and Plan B costs {fee_b}+{rate_b}n. "
            "Find the nonnegative integer n where their costs agree and give that cost."
        ),
        parameters={
            "fee_a": fee_a,
            "rate_a": rate_a,
            "fee_b": fee_b,
            "rate_b": rate_b,
        },
        answer=f"n={crossover}; cost={answer}",
    )


def generate_quadratic_area(seed: int, mode: str) -> dict:
    """Generate a rectangle whose tiled and expanded areas must agree."""

    rng = _rng(seed, mode, 23)
    n = rng.randint(1, 12)
    a = rng.randint(1, 6)
    b = rng.randint(1, 6)
    answer = (n + a) * (n + b)
    return _record(
        seed=seed,
        mode=mode,
        family="QUADRATIC_RECTANGLE_AREA",
        prompt=(
            f"A rectangle has side lengths n+{a} and n+{b}. For n={n}, "
            "find its area and verify the expanded expression."
        ),
        parameters={"n": n, "a": a, "b": b},
        answer=str(answer),
    )


def generate_exponential_change(seed: int, mode: str) -> dict:
    """Generate an exact repeated multiplicative-change comparison."""

    rng = _rng(seed, mode, 37)
    initial = rng.randint(80, 500)
    multiplier = rng.choice((Fraction(3, 4), Fraction(4, 3), Fraction(5, 4), Fraction(6, 5)))
    periods = rng.randint(2, 6)
    answer = Fraction(initial) * multiplier**periods
    return _record(
        seed=seed,
        mode=mode,
        family="EXPONENTIAL_REPEATED_CHANGE",
        prompt=(
            f"A quantity starts at {initial} and is multiplied by {multiplier} each period. "
            f"Find the exact amount after {periods} periods."
        ),
        parameters={
            "initial": initial,
            "multiplier_numerator": multiplier.numerator,
            "multiplier_denominator": multiplier.denominator,
            "periods": periods,
        },
        answer=str(answer),
    )
