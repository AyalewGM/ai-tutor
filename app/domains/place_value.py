"""Canonical place-value problem families.

Covers: digit value, place identification, expanded notation,
composing/decomposing, comparing via place value, rounding,
powers-of-ten relationships, and conceptual reasoning.
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

_PLACE_NAMES = ["ones", "tens", "hundreds", "thousands",
                "ten-thousands", "hundred-thousands", "millions"]
_PLACE_VALUES = [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000]


def _comma(n: int) -> str:
    return f"{n:,}"


def _digit_at_place(number: int, place_index: int) -> int:
    """Return the digit at the given place index (0=ones, 1=tens, ...)."""
    return (number // _PLACE_VALUES[place_index]) % 10


def _value_at_place(number: int, place_index: int) -> int:
    """Return the value of the digit at the given place index."""
    return _digit_at_place(number, place_index) * _PLACE_VALUES[place_index]


def _round_to(n: int, place_value: int) -> int:
    """Round *n* to the nearest *place_value*."""
    remainder = n % place_value
    if remainder >= place_value // 2 + (place_value % 2):
        return n - remainder + place_value
    return n - remainder


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.PV.IDENTIFY_PLACE": ProblemFamilySpec(
        "MATH.PV.IDENTIFY_PLACE", "Identify the place of a digit",
        "MATH.NS.PLACE_VALUE", "NUMBER_SENSE", 1, 4, ALL_MODES,
        frozenset({"conceptual_understanding", "number_sense"}),
    ),
    "MATH.PV.DIGIT_VALUE": ProblemFamilySpec(
        "MATH.PV.DIGIT_VALUE", "Find the value of a digit in a number",
        "MATH.NS.PLACE_VALUE", "NUMBER_SENSE", 1, 4, ALL_MODES,
        frozenset({"conceptual_understanding", "number_sense"}),
    ),
    "MATH.PV.COMPARE": ProblemFamilySpec(
        "MATH.PV.COMPARE", "Compare numbers using place value",
        "MATH.NS.PLACE_VALUE", "COMPARISON", 1, 4, ALL_MODES,
        frozenset({"comparison", "number_sense", "conceptual_understanding"}),
    ),
    "MATH.PV.ROUND": ProblemFamilySpec(
        "MATH.PV.ROUND", "Round a number to a given place",
        "MATH.NS.ROUNDING", "NUMBER_SENSE", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "estimation", "number_sense"}),
    ),
    "MATH.PV.POWERS_TEN": ProblemFamilySpec(
        "MATH.PV.POWERS_TEN", "Place-value power-of-ten reasoning",
        "MATH.NS.PLACE_VALUE", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding", "number_sense"}),
    ),
    "MATH.PV.COMPOSE_NONSTANDARD": ProblemFamilySpec(
        "MATH.PV.COMPOSE_NONSTANDARD", "Compose from non-standard place-value parts",
        "MATH.NS.COMPOSE_DECOMPOSE", "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"conceptual_understanding", "reasoning", "number_sense"}),
    ),
    "MATH.PV.ERROR.DIGIT_VS_VALUE": ProblemFamilySpec(
        "MATH.PV.ERROR.DIGIT_VS_VALUE", "Error analysis: digit vs. value confusion",
        "MATH.NS.PLACE_VALUE", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
    "MATH.PV.REASON.TEN_TIMES": ProblemFamilySpec(
        "MATH.PV.REASON.TEN_TIMES", "Why is a digit worth 10× in the next place?",
        "MATH.NS.PLACE_VALUE", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):

    # --- identify place ---
    if family_code == "MATH.PV.IDENTIFY_PLACE":
        num_digits = 3 + min(difficulty, 4)
        number = rng.randint(10 ** (num_digits - 1), 10 ** num_digits - 1)
        max_place = min(num_digits - 1, len(_PLACE_NAMES) - 1)
        place_idx = rng.randint(0, max_place)
        digit = _digit_at_place(number, place_idx)
        prompt = f"What place is the digit {digit} in within the number {_comma(number)}?"
        answer = _PLACE_NAMES[place_idx]
        hints = (
            "Count from right to left: ones, tens, hundreds, ...",
            "The rightmost digit is in the ones place.",
        )
        wrong_idx = min(place_idx + 1, max_place) if place_idx < max_place else place_idx - 1
        misconceptions = {
            "PV.IDENTIFY.OFF_BY_ONE": _PLACE_NAMES[wrong_idx],
        }
        return prompt, answer, hints, misconceptions

    # --- digit value ---
    if family_code == "MATH.PV.DIGIT_VALUE":
        num_digits = 3 + min(difficulty, 4)
        number = rng.randint(10 ** (num_digits - 1), 10 ** num_digits - 1)
        max_place = min(num_digits - 1, len(_PLACE_NAMES) - 1)
        place_idx = rng.randint(0, max_place)
        while _digit_at_place(number, place_idx) == 0:
            place_idx = rng.randint(0, max_place)
        digit = _digit_at_place(number, place_idx)
        value = _value_at_place(number, place_idx)
        prompt = f"In the number {_comma(number)}, what is the value of the digit {digit} in the {_PLACE_NAMES[place_idx]} place?"
        answer = _comma(value)
        hints = (
            f"The digit {digit} is in the {_PLACE_NAMES[place_idx]} place.",
            f"Multiply the digit by its place value: {digit} × {_comma(_PLACE_VALUES[place_idx])}.",
        )
        misconceptions = {
            "PV.VALUE.DIGIT_ONLY": str(digit),
        }
        return prompt, answer, hints, misconceptions

    # --- compare using place value ---
    if family_code == "MATH.PV.COMPARE":
        num_digits = 3 + min(difficulty, 3)
        a = rng.randint(10 ** (num_digits - 1), 10 ** num_digits - 1)
        b = rng.randint(10 ** (num_digits - 1), 10 ** num_digits - 1)
        while a == b:
            b = rng.randint(10 ** (num_digits - 1), 10 ** num_digits - 1)
        prompt = (
            f"Use place value to compare {_comma(a)} and {_comma(b)}. "
            f"Which symbol goes in the blank: {_comma(a)} ___ {_comma(b)}? "
            f"(A) > (B) < (C) ="
        )
        if a > b:
            answer = "A"
        elif a < b:
            answer = "B"
        else:
            answer = "C"
        hints = (
            "Compare the digits starting from the leftmost place.",
            "The first place where the digits differ tells you which is greater.",
        )
        wrong = "B" if a > b else "A"
        misconceptions = {
            "PV.COMPARE.REVERSED": wrong,
        }
        return prompt, answer, hints, misconceptions

    # --- rounding ---
    if family_code == "MATH.PV.ROUND":
        places = [10, 100, 1_000][:2 + min(difficulty, 2)]
        if difficulty >= 4:
            places.append(10_000)
        place_val = rng.choice(places)
        place_name = _PLACE_NAMES[_PLACE_VALUES.index(place_val)]
        lo = place_val * 2
        hi = place_val * 20 * (1 + difficulty)
        number = rng.randint(lo, hi)
        # Ensure number isn't already a clean multiple
        if number % place_val == 0:
            number += rng.randint(1, place_val - 1)
        rounded = _round_to(number, place_val)
        prompt = f"Round {_comma(number)} to the nearest {place_name.removesuffix('s')}."
        answer = _comma(rounded)
        # Determine direction for hint
        remainder = number % place_val
        direction = "up" if remainder >= place_val // 2 + (place_val % 2) else "down"
        hints = (
            f"Look at the digit in the {_PLACE_NAMES[_PLACE_VALUES.index(place_val) - 1]} place.",
            f"Since the digit is {'5 or more' if direction == 'up' else 'less than 5'}, round {direction}.",
        )
        # Wrong direction
        if direction == "up":
            wrong_rounded = number - remainder
        else:
            wrong_rounded = number - remainder + place_val
        misconceptions = {
            "PV.ROUND.WRONG_DIRECTION": _comma(wrong_rounded),
        }
        return prompt, answer, hints, misconceptions

    # --- powers of ten ---
    if family_code == "MATH.PV.POWERS_TEN":
        base = rng.randint(1, 9)
        places = list(range(1, 4 + difficulty))
        p1, p2 = rng.sample(places, 2)
        if p1 > p2:
            p1, p2 = p2, p1
        val1 = base * (10 ** p1)
        val2 = base * (10 ** p2)
        factor = 10 ** (p2 - p1)
        prompt = (
            f"How many times greater is {_comma(val2)} than {_comma(val1)}?"
        )
        answer = _comma(factor)
        hints = (
            f"Both numbers have the digit {base}, but in different places.",
            "Moving one place to the left multiplies the value by 10.",
            f"Count how many places apart: {p2 - p1} place(s) = 10^{p2 - p1} = {_comma(factor)}.",
        )
        misconceptions = {
            "PV.POWER.ADD_INSTEAD": _comma(val2 - val1),
        }
        return prompt, answer, hints, misconceptions

    # --- compose from non-standard parts ---
    if family_code == "MATH.PV.COMPOSE_NONSTANDARD":
        # e.g., "What number has 14 tens and 3 ones?" = 143
        place_idx = rng.randint(1, 2 + min(difficulty, 3))
        place_name = _PLACE_NAMES[place_idx]
        place_val = _PLACE_VALUES[place_idx]
        count = rng.randint(11, 19 + difficulty * 5)  # non-standard: > 9
        ones = rng.randint(0, 9)
        number = count * place_val + ones
        prompt = f"What number has {count} {place_name} and {ones} ones?"
        answer = _comma(number)
        hints = (
            f"{count} {place_name} = {count} × {_comma(place_val)} = {_comma(count * place_val)}.",
            f"Then add the {ones} ones.",
        )
        # Misconception: treat the count as a single digit
        wrong_digit = count % 10
        wrong = wrong_digit * place_val + ones
        misconceptions = {
            "PV.COMPOSE.SINGLE_DIGIT": _comma(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- error: digit vs value ---
    if family_code == "MATH.PV.ERROR.DIGIT_VS_VALUE":
        num_digits = 3 + min(difficulty, 3)
        number = rng.randint(10 ** (num_digits - 1), 10 ** num_digits - 1)
        place_idx = rng.randint(1, min(num_digits - 1, len(_PLACE_NAMES) - 1))
        while _digit_at_place(number, place_idx) == 0:
            place_idx = rng.randint(1, min(num_digits - 1, len(_PLACE_NAMES) - 1))
        digit = _digit_at_place(number, place_idx)
        value = _value_at_place(number, place_idx)
        names = ["Kai", "Sofia", "Jayden", "Amara", "River"]
        name = rng.choice(names)
        prompt = (
            f"{name} says the value of the {digit} in {_comma(number)} is {digit}. "
            f"What is the correct value? "
            f"(A) {_comma(value)} "
            f"(B) {digit} "
            f"(C) {_comma(_PLACE_VALUES[place_idx])}"
        )
        answer = "A"
        hints = (
            f"The digit {digit} is in the {_PLACE_NAMES[place_idx]} place.",
            f"Its value is {digit} × {_comma(_PLACE_VALUES[place_idx])} = {_comma(value)}.",
        )
        misconceptions = {
            "PV.ERROR.DIGIT_ONLY": "B",
            "PV.ERROR.PLACE_ONLY": "C",
        }
        return prompt, answer, hints, misconceptions

    # --- reasoning: ten times ---
    if family_code == "MATH.PV.REASON.TEN_TIMES":
        digit = rng.randint(1, 9)
        # Pick two adjacent places
        max_place = min(3 + difficulty, len(_PLACE_NAMES) - 1)
        lower = rng.randint(0, max_place - 1)
        upper = lower + 1
        num1_base = rng.randint(1, 5) * 10 ** (upper + 1) + digit * _PLACE_VALUES[lower]
        num2_base = rng.randint(1, 5) * 10 ** (upper + 1) + digit * _PLACE_VALUES[upper]
        prompt = (
            f"The digit {digit} appears in both {_comma(num1_base)} and {_comma(num2_base)}. "
            f"In which number does the {digit} have a greater value, and how many times greater? "
            f"(A) {_comma(num2_base)} — ten times greater "
            f"(B) {_comma(num1_base)} — ten times greater "
            f"(C) They have the same value"
        )
        answer = "A"
        hints = (
            f"In {_comma(num1_base)}, the {digit} is in the {_PLACE_NAMES[lower]} place.",
            f"In {_comma(num2_base)}, the {digit} is in the {_PLACE_NAMES[upper]} place.",
            "Each place to the left is 10 times greater.",
        )
        misconceptions = {
            "PV.REASON.SAME_DIGIT_SAME_VALUE": "C",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")
