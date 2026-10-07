"""Canonical estimation and number-sense problem families.

Covers: rounding, compatible numbers, estimating sums/differences/products/
quotients, magnitude comparison, reasonableness checks, benchmark reasoning.
"""

from __future__ import annotations

import random

from app.canonical_problem_families import (
    ALL_MODES,
    ProblemFamilySpec,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _comma(n: int) -> str:
    return f"{n:,}"


def _round_to(n: int, place: int) -> int:
    remainder = n % place
    if remainder >= place // 2 + (place % 2):
        return n - remainder + place
    return n - remainder


def _compatible(n: int, place: int) -> int:
    """Round to nearest multiple of *place* for mental math."""
    return _round_to(n, place)


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.EST.SUM": ProblemFamilySpec(
        "MATH.EST.SUM", "Estimate a sum using rounding",
        "MATH.NS.ESTIMATION", "ESTIMATION", 1, 4, ALL_MODES,
        frozenset({"estimation", "number_sense", "reasoning"}),
    ),
    "MATH.EST.DIFF": ProblemFamilySpec(
        "MATH.EST.DIFF", "Estimate a difference using rounding",
        "MATH.NS.ESTIMATION", "ESTIMATION", 1, 4, ALL_MODES,
        frozenset({"estimation", "number_sense", "reasoning"}),
    ),
    "MATH.EST.PRODUCT": ProblemFamilySpec(
        "MATH.EST.PRODUCT", "Estimate a product using rounding",
        "MATH.NS.ESTIMATION", "ESTIMATION", 2, 4, ALL_MODES,
        frozenset({"estimation", "number_sense", "reasoning"}),
    ),
    "MATH.EST.QUOTIENT": ProblemFamilySpec(
        "MATH.EST.QUOTIENT", "Estimate a quotient using compatible numbers",
        "MATH.NS.ESTIMATION", "ESTIMATION", 2, 4, ALL_MODES,
        frozenset({"estimation", "number_sense", "reasoning"}),
    ),
    "MATH.EST.REASONABLE": ProblemFamilySpec(
        "MATH.EST.REASONABLE", "Is the answer reasonable?",
        "MATH.NS.ESTIMATION", "REASONING", 1, 4, ALL_MODES,
        frozenset({"estimation", "reasoning", "number_sense"}),
    ),
    "MATH.EST.BENCHMARK": ProblemFamilySpec(
        "MATH.EST.BENCHMARK", "Use benchmark numbers to estimate",
        "MATH.NS.ESTIMATION", "ESTIMATION", 2, 4, ALL_MODES,
        frozenset({"estimation", "number_sense", "conceptual_understanding"}),
    ),
    "MATH.EST.WORD": ProblemFamilySpec(
        "MATH.EST.WORD", "Estimation word problem",
        "MATH.NS.ESTIMATION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"estimation", "modeling", "transfer", "number_sense"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):

    # --- estimate sum ---
    if family_code == "MATH.EST.SUM":
        places = [10, 100, 1_000]
        place = places[min(difficulty - 1, len(places) - 1)]
        a = rng.randint(place, place * 10 * difficulty)
        b = rng.randint(place, place * 10 * difficulty)
        ra, rb = _round_to(a, place), _round_to(b, place)
        estimate = ra + rb
        exact = a + b
        place_name = {10: "ten", 100: "hundred", 1_000: "thousand"}[place]
        prompt = (
            f"Estimate {_comma(a)} + {_comma(b)} by rounding to the nearest {place_name}."
        )
        answer = _comma(estimate)
        hints = (
            f"Round {_comma(a)} to the nearest {place_name}: {_comma(ra)}.",
            f"Round {_comma(b)} to the nearest {place_name}: {_comma(rb)}.",
            f"Add: {_comma(ra)} + {_comma(rb)} = {_comma(estimate)}.",
        )
        misconceptions = {
            "EST.SUM.EXACT": _comma(exact),
        }
        return prompt, answer, hints, misconceptions

    # --- estimate difference ---
    if family_code == "MATH.EST.DIFF":
        places = [10, 100, 1_000]
        place = places[min(difficulty - 1, len(places) - 1)]
        a = rng.randint(place * 2, place * 10 * difficulty)
        b = rng.randint(place, a)
        ra, rb = _round_to(a, place), _round_to(b, place)
        estimate = ra - rb
        exact = a - b
        place_name = {10: "ten", 100: "hundred", 1_000: "thousand"}[place]
        prompt = (
            f"Estimate {_comma(a)} − {_comma(b)} by rounding to the nearest {place_name}."
        )
        answer = _comma(estimate)
        hints = (
            f"Round {_comma(a)} → {_comma(ra)}, {_comma(b)} → {_comma(rb)}.",
            f"Subtract: {_comma(ra)} − {_comma(rb)} = {_comma(estimate)}.",
        )
        misconceptions = {
            "EST.DIFF.EXACT": _comma(exact),
        }
        return prompt, answer, hints, misconceptions

    # --- estimate product ---
    if family_code == "MATH.EST.PRODUCT":
        place = 10 if difficulty <= 2 else 100
        a = rng.randint(10 + difficulty * 5, 50 + difficulty * 50)
        b = rng.randint(10, 30 + difficulty * 20)
        ra, rb = _round_to(a, place), _round_to(b, place)
        estimate = ra * rb
        exact = a * b
        prompt = (
            f"Which is the best estimate for {_comma(a)} × {_comma(b)}? "
            f"(A) {_comma(estimate)} "
            f"(B) {_comma(exact)} "
            f"(C) {_comma(estimate * 2)} "
            f"(D) {_comma(estimate // 3 if estimate > 3 else 1)}"
        )
        answer = "A"
        hints = (
            f"Round the factors: {_comma(a)} ≈ {_comma(ra)}, {_comma(b)} ≈ {_comma(rb)}.",
            f"Multiply: {_comma(ra)} × {_comma(rb)} = {_comma(estimate)}.",
        )
        misconceptions = {
            "EST.PRODUCT.EXACT": "B",
        }
        return prompt, answer, hints, misconceptions

    # --- estimate quotient ---
    if family_code == "MATH.EST.QUOTIENT":
        divisor = rng.randint(3, 6 + difficulty * 2)
        quotient = rng.randint(5, 20 + difficulty * 10)
        # Make a "messy" dividend near divisor * quotient
        exact_div = divisor * quotient
        dividend = exact_div + rng.randint(-divisor + 1, divisor - 1)
        # Compatible number: nearest multiple of divisor
        compatible_dividend = _round_to(dividend, divisor)
        if compatible_dividend == 0:
            compatible_dividend = divisor
        est_quotient = compatible_dividend // divisor
        prompt = (
            f"Estimate {_comma(dividend)} ÷ {divisor} using compatible numbers."
        )
        answer = str(est_quotient)
        hints = (
            f"Find a number close to {_comma(dividend)} that divides evenly by {divisor}.",
            f"{_comma(compatible_dividend)} ÷ {divisor} = {est_quotient}.",
        )
        misconceptions = {
            "EST.QUOT.EXACT": str(dividend // divisor),
        }
        return prompt, answer, hints, misconceptions

    # --- reasonableness ---
    if family_code == "MATH.EST.REASONABLE":
        ops = ["+", "−", "×"]
        op = rng.choice(ops[:2 + min(difficulty, 1)])
        a = rng.randint(20, 100 + difficulty * 200)
        b = rng.randint(10, 50 + difficulty * 100)
        if op == "+":
            correct_result = a + b
        elif op == "−":
            if a < b:
                a, b = b, a
            correct_result = a - b
        else:
            correct_result = a * b
        # Generate a clearly wrong answer
        wrong_results = [
            correct_result * 10,
            correct_result // 10 if correct_result > 10 else correct_result + 100,
            correct_result + rng.randint(50, 200) * (1 + difficulty),
        ]
        wrong_answer = rng.choice(wrong_results)
        is_proposed_reasonable = rng.choice([True, False])
        proposed = correct_result if is_proposed_reasonable else wrong_answer
        prompt = (
            f"A student says {_comma(a)} {op} {_comma(b)} = {_comma(proposed)}. "
            f"Is this answer reasonable? Answer Yes or No."
        )
        answer = "Yes" if is_proposed_reasonable else "No"
        hints = (
            "Estimate: round the numbers and compute.",
            f"The estimate should be close to {_comma(correct_result)}.",
        )
        misconceptions = {
            "EST.REASONABLE.REVERSED": "No" if is_proposed_reasonable else "Yes",
        }
        return prompt, answer, hints, misconceptions

    # --- benchmark reasoning ---
    if family_code == "MATH.EST.BENCHMARK":
        # "Is 398 × 21 closer to 8000 or 80000?"
        a = rng.randint(100, 500 + difficulty * 200)
        b = rng.randint(10, 30 + difficulty * 10)
        exact = a * b
        # Create two choices: one reasonable, one 10x off
        reasonable = _round_to(exact, 10 ** (len(str(exact)) - 1))
        if reasonable == 0:
            reasonable = 10 ** (len(str(exact)) - 1)
        off_by_10x = reasonable * 10
        prompt = (
            f"Without calculating exactly, which is the best estimate for "
            f"{_comma(a)} × {_comma(b)}? "
            f"(A) {_comma(reasonable)} "
            f"(B) {_comma(off_by_10x)} "
            f"(C) {_comma(reasonable // 10 if reasonable >= 10 else 1)}"
        )
        answer = "A"
        hints = (
            f"Round: {_comma(a)} ≈ {_comma(_round_to(a, 100))}, {_comma(b)} ≈ {_comma(_round_to(b, 10))}.",
            "Multiply the rounded values for a quick estimate.",
        )
        misconceptions = {
            "EST.BENCH.OFF_10X": "B",
        }
        return prompt, answer, hints, misconceptions

    # --- estimation word problem ---
    if family_code == "MATH.EST.WORD":
        contexts = [
            _est_word_seats,
            _est_word_budget,
        ]
        fn = rng.choice(contexts)
        return fn(rng, difficulty)

    raise ValueError(f"No builder for family: {family_code}")


def _est_word_seats(rng: random.Random, difficulty: int):
    sections = rng.randint(3, 5 + difficulty)
    per_section = rng.randint(80, 200 + difficulty * 100)
    exact = sections * per_section
    rounded_per = _round_to(per_section, 100 if per_section >= 100 else 10)
    estimate = sections * rounded_per
    prompt = (
        f"A stadium has {sections} sections, each with about {_comma(per_section)} seats. "
        f"Estimate the total number of seats."
    )
    answer = _comma(estimate)
    hints = (
        f"Round {_comma(per_section)} to a convenient number.",
        f"{_comma(rounded_per)} × {sections} = {_comma(estimate)}.",
    )
    misconceptions = {
        "EST.WORD.EXACT": _comma(exact),
    }
    return prompt, answer, hints, misconceptions


def _est_word_budget(rng: random.Random, difficulty: int):
    items = []
    total = 0
    for _ in range(3 + min(difficulty, 2)):
        price = rng.randint(5, 30 + difficulty * 10)
        items.append(price)
        total += price
    budget = _round_to(total, 10) + rng.choice([10, 20, -10])
    item_list = ", ".join(f"${p}" for p in items)
    prompt = (
        f"You want to buy items costing {item_list}. "
        f"You have ${_comma(budget)}. "
        f"Without computing the exact total, do you have enough? Answer Yes or No."
    )
    est_total = sum(_round_to(p, 10) for p in items)
    has_enough = est_total <= budget
    answer = "Yes" if has_enough else "No"
    hints = (
        "Round each price to the nearest ten.",
        f"Estimated total: {_comma(est_total)}. Budget: ${_comma(budget)}.",
    )
    misconceptions = {
        "EST.WORD.REVERSED": "No" if has_enough else "Yes",
    }
    return prompt, answer, hints, misconceptions
