"""Draft-only deterministic Grade 9 algebra variants and exact oracles.

This module is not imported by runtime code and performs no persistence.
"""

import random
from fractions import Fraction
from itertools import pairwise

NAMESPACE = "g9-algebra-depth-r4"
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
    *,
    seed: int,
    mode: str,
    family: str,
    prompt: str,
    parameters: dict,
    answer: object,
    response_fields: tuple[str, ...] = ("exact_result",),
) -> dict:
    return {
        "variant_id": f"{NAMESPACE}:{mode}:{family}:{seed}",
        "mode": mode,
        "family": family,
        "prompt": prompt,
        "parameters": parameters,
        "response_fields": list(response_fields),
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


def generate_linear_translation(seed: int, mode: str) -> dict:
    """Generate a bounded table-to-graph-to-equation modeling task."""

    rng = _rng(seed, mode, 17)
    intercept = rng.randint(4, 20)
    rate = rng.randint(2, 8)
    maximum_input = rng.randint(6, 12)
    inputs = [0, 1, 2, maximum_input]
    outputs = [intercept + rate * value for value in inputs]
    return _record(
        seed=seed,
        mode=mode,
        family="LINEAR_TABLE_GRAPH_EQUATION_DOMAIN",
        prompt=(
            "A delivery cart starts with a fixed loading time and then adds the same "
            f"time per crate. The observed (crates, minutes) pairs are {list(zip(inputs, outputs))}. "
            f"The cart holds at most {maximum_input} whole crates. Identify the rate and "
            "initial value with units, write the equation, describe the matching graph, "
            "and justify the physical domain."
        ),
        parameters={
            "input_label": "whole crates",
            "output_label": "minutes",
            "table_inputs": inputs,
            "table_outputs": outputs,
            "maximum_input": maximum_input,
        },
        response_fields=(
            "rate_with_units",
            "initial_value_with_units",
            "equation",
            "graph_translation",
            "physical_domain",
            "domain_justification",
        ),
        answer={
            "rate": rate,
            "rate_units": "minutes per crate",
            "initial_value": intercept,
            "initial_units": "minutes",
            "equation": f"T(n)={intercept}+{rate}n",
            "graph_translation": (
                f"starts at (0,{intercept}); rises {rate} minutes for each 1-crate run"
            ),
            "physical_domain": f"n is a whole number and 0<=n<={maximum_input}",
            "domain_justification": "crate count is discrete and cannot exceed cart capacity",
        },
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


def generate_quadratic_pattern(seed: int, mode: str) -> dict:
    """Generate a table whose next value requires constant second differences."""

    rng = _rng(seed, mode, 29)
    leading = rng.randint(1, 3)
    linear = rng.randint(0, 5)
    constant = rng.randint(0, 6)
    inputs = [0, 1, 2, 3]
    outputs = [leading * n**2 + linear * n + constant for n in inputs]
    first_differences = [right - left for left, right in pairwise(outputs)]
    second_differences = [
        right - left for left, right in pairwise(first_differences)
    ]
    next_first_difference = first_differences[-1] + 2 * leading
    next_value = outputs[-1] + next_first_difference
    return _record(
        seed=seed,
        mode=mode,
        family="QUADRATIC_TABLE_SECOND_DIFFERENCE_TRANSFER",
        prompt=(
            f"A growing tile design has counts {list(zip(inputs, outputs))}. Predict the "
            "count at stage 4, show both difference rows, write a rule, and explain why "
            "the growth is quadratic rather than linear."
        ),
        parameters={"stage_inputs": inputs, "tile_counts": outputs},
        response_fields=(
            "first_differences",
            "second_differences",
            "stage_4_prediction",
            "symbolic_rule",
            "quadratic_growth_explanation",
        ),
        answer={
            "first_differences": first_differences,
            "second_differences": second_differences,
            "stage_4_prediction": next_value,
            "symbolic_rule": f"A(n)={leading}n^2+{linear}n+{constant}",
            "leading_coefficient": leading,
            "linear_coefficient": linear,
            "constant": constant,
            "quadratic_growth_explanation": (
                f"first differences change by the constant second difference {2 * leading}"
            ),
        },
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
