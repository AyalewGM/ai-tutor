"""Canonical decimal problem families.

Covers: place value, comparison, ordering, fraction-decimal conversion,
four operations, estimation, money/application contexts, error analysis.
"""

from __future__ import annotations

import random
from decimal import ROUND_HALF_UP, Decimal
from math import gcd

from app.canonical_problem_families import (
    ALL_MODES,
    ProblemFamilySpec,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _frac(n: int, d: int) -> str:
    if d == 1:
        return str(n)
    return f"{n}/{d}"


def _dec_str(val: Decimal) -> str:
    """Normalize: strip trailing zeros but keep at least one decimal digit."""
    return f"{val.normalize():f}"


def _rand_decimal(rng: random.Random, lo: float, hi: float, places: int) -> Decimal:
    raw = rng.uniform(lo, hi)
    return Decimal(str(round(raw, places)))


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.DEC.COMPARE": ProblemFamilySpec(
        "MATH.DEC.COMPARE", "Compare two decimals",
        "MATH.NS.DECIMAL.COMPARE", "COMPARISON", 1, 3, ALL_MODES,
        frozenset({"comparison", "number_sense", "conceptual_understanding"}),
    ),
    "MATH.DEC.PLACE_VALUE": ProblemFamilySpec(
        "MATH.DEC.PLACE_VALUE", "Identify decimal place value",
        "MATH.NS.DECIMAL.PLACE_VALUE", "IDENTIFICATION", 1, 3, ALL_MODES,
        frozenset({"conceptual_understanding"}),
    ),
    "MATH.DEC.FRAC_TO_DEC": ProblemFamilySpec(
        "MATH.DEC.FRAC_TO_DEC", "Convert fraction to decimal",
        "MATH.NS.DECIMAL.CONVERT", "CONVERSION", 1, 3, ALL_MODES,
        frozenset({"representation", "procedural_fluency"}),
    ),
    "MATH.DEC.DEC_TO_FRAC": ProblemFamilySpec(
        "MATH.DEC.DEC_TO_FRAC", "Convert decimal to fraction",
        "MATH.NS.DECIMAL.CONVERT", "CONVERSION", 1, 3, ALL_MODES,
        frozenset({"representation", "procedural_fluency"}),
    ),
    "MATH.DEC.ADD": ProblemFamilySpec(
        "MATH.DEC.ADD", "Add decimals",
        "MATH.NS.DECIMAL.ADD_SUBTRACT", "DECIMAL", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency"}),
    ),
    "MATH.DEC.SUB": ProblemFamilySpec(
        "MATH.DEC.SUB", "Subtract decimals",
        "MATH.NS.DECIMAL.ADD_SUBTRACT", "DECIMAL", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency"}),
    ),
    "MATH.DEC.MUL": ProblemFamilySpec(
        "MATH.DEC.MUL", "Multiply decimals",
        "MATH.NS.DECIMAL.MULTIPLY", "DECIMAL", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency"}),
    ),
    "MATH.DEC.DIV": ProblemFamilySpec(
        "MATH.DEC.DIV", "Divide decimals",
        "MATH.NS.DECIMAL.DIVIDE", "DECIMAL", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency"}),
    ),
    "MATH.DEC.ESTIMATE": ProblemFamilySpec(
        "MATH.DEC.ESTIMATE", "Estimate a decimal computation",
        "MATH.NS.DECIMAL.COMPARE", "ESTIMATION", 2, 4, ALL_MODES,
        frozenset({"estimation", "number_sense", "reasoning"}),
    ),
    "MATH.DEC.MONEY.CHANGE": ProblemFamilySpec(
        "MATH.DEC.MONEY.CHANGE", "Money context: calculate change",
        "MATH.NS.DECIMAL.ADD_SUBTRACT", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.DEC.MONEY.TOTAL": ProblemFamilySpec(
        "MATH.DEC.MONEY.TOTAL", "Money context: total cost",
        "MATH.NS.DECIMAL.ADD_SUBTRACT", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "transfer"}),
    ),
    "MATH.DEC.ERROR.LONGER_LARGER": ProblemFamilySpec(
        "MATH.DEC.ERROR.LONGER_LARGER", "Error analysis: longer decimal is larger",
        "MATH.NS.DECIMAL.COMPARE", "ERROR_ANALYSIS", 2, 3, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):
    """Return (prompt, answer, hints, misconceptions) for *family_code*."""

    # --- compare ---
    if family_code == "MATH.DEC.COMPARE":
        places = 1 + difficulty
        a = _rand_decimal(rng, 0.1, 10.0, places)
        b = _rand_decimal(rng, 0.1, 10.0, places)
        while a == b:
            b = _rand_decimal(rng, 0.1, 10.0, places)
        prompt = f"Which is greater: {a} or {b}?"
        answer = _dec_str(max(a, b))
        hints = (
            "Line up the decimal points and compare digit by digit from left to right.",
            "Look at the digits in the same place value position.",
        )
        misconceptions = {
            "DEC.COMPARE.LONGER_IS_LARGER": _dec_str(min(a, b)),
        }
        return prompt, answer, hints, misconceptions

    # --- place value ---
    if family_code == "MATH.DEC.PLACE_VALUE":
        whole = rng.randint(1, 9 + difficulty * 10)
        tenths = rng.randint(1, 9)
        # Ensure ones digit differs from tenths so WRONG_DIRECTION misconception is diagnostic
        while whole % 10 == tenths:
            whole = rng.randint(1, 9 + difficulty * 10)
        hundredths = rng.randint(0, 9) if difficulty >= 2 else 0
        thousandths = rng.randint(1, 9) if difficulty >= 3 else 0
        num_str = f"{whole}.{tenths}{hundredths}{thousandths}".rstrip("0")
        if "." not in num_str:
            num_str += ".0"
        place_targets = [("tenths", tenths)]
        if hundredths:
            place_targets.append(("hundredths", hundredths))
        if thousandths:
            place_targets.append(("thousandths", thousandths))
        place_name, digit = rng.choice(place_targets)
        prompt = f"In the number {num_str}, what digit is in the {place_name} place?"
        answer = str(digit)
        hints = (
            f"The {place_name} place is the {'first' if place_name == 'tenths' else 'second' if place_name == 'hundredths' else 'third'} digit after the decimal point.",
        )
        misconceptions = {
            "DEC.PLACE.WRONG_DIRECTION": str(int(num_str.split(".")[0]) % 10),
        }
        return prompt, answer, hints, misconceptions

    # --- fraction to decimal ---
    if family_code == "MATH.DEC.FRAC_TO_DEC":
        terminators = [(1, 2), (1, 4), (3, 4), (1, 5), (2, 5), (3, 5), (4, 5),
                       (1, 8), (3, 8), (5, 8), (7, 8), (1, 10), (3, 10)]
        if difficulty >= 2:
            terminators += [(1, 20), (7, 20), (1, 25), (3, 25)]
        n, d = rng.choice(terminators)
        result = Decimal(str(n)) / Decimal(str(d))
        result = result.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP).normalize()
        prompt = f"Convert {_frac(n, d)} to a decimal."
        answer = _dec_str(result)
        hints = (
            f"Divide the numerator ({n}) by the denominator ({d}).",
            f"{n} ÷ {d} = ?",
        )
        misconceptions = {
            "DEC.CONVERT.REVERSE_DIVISION": _dec_str(
                (Decimal(str(d)) / Decimal(str(n))).quantize(
                    Decimal("0.001"), rounding=ROUND_HALF_UP
                ).normalize()
            ) if n != 0 else "0",
        }
        return prompt, answer, hints, misconceptions

    # --- decimal to fraction ---
    if family_code == "MATH.DEC.DEC_TO_FRAC":
        places_list = [1] if difficulty == 1 else [1, 2] if difficulty == 2 else [1, 2, 3]
        places = rng.choice(places_list)
        denom = 10 ** places
        numer = rng.randint(1, denom - 1)
        dec_val = Decimal(str(numer)) / Decimal(str(denom))
        g = gcd(numer, denom)
        sn, sd = numer // g, denom // g
        prompt = f"Convert {_dec_str(dec_val)} to a fraction in simplest form."
        answer = _frac(sn, sd)
        hints = (
            f"Write the decimal as a fraction over {denom}.",
            f"{_dec_str(dec_val)} = {_frac(numer, denom)}. Now simplify.",
        )
        misconceptions = {
            "DEC.CONVERT.NO_SIMPLIFY": _frac(numer, denom) if g > 1 else _frac(numer + 1, denom),
        }
        return prompt, answer, hints, misconceptions

    # --- add decimals ---
    if family_code == "MATH.DEC.ADD":
        p1 = rng.randint(1, 1 + difficulty)
        p2 = rng.randint(1, 1 + difficulty)
        a = _rand_decimal(rng, 1.0, 20.0 + difficulty * 10, p1)
        b = _rand_decimal(rng, 1.0, 20.0 + difficulty * 10, p2)
        result = a + b
        prompt = f"Add {a} + {b}."
        answer = _dec_str(result)
        hints = (
            "Line up the decimal points before adding.",
            "Add zeros to fill missing decimal places if needed.",
        )
        # Misalignment error: concatenate digits as if no decimal
        misconceptions = {
            "DEC.ADD.MISALIGN": _dec_str(
                Decimal(str(a).replace(".", "")) + Decimal(str(b).replace(".", ""))
            ) if difficulty >= 2 else str(int(a) + int(b)),
        }
        return prompt, answer, hints, misconceptions

    # --- subtract decimals ---
    if family_code == "MATH.DEC.SUB":
        p1 = rng.randint(1, 1 + difficulty)
        p2 = rng.randint(1, 1 + difficulty)
        a = _rand_decimal(rng, 5.0, 20.0 + difficulty * 10, p1)
        b = _rand_decimal(rng, 1.0, float(a) - 0.1, p2)
        result = a - b
        prompt = f"Subtract {a} − {b}."
        answer = _dec_str(result)
        hints = (
            "Line up the decimal points before subtracting.",
            "Annex zeros to the right if the decimals have different lengths.",
        )
        misconceptions = {
            "DEC.SUB.MISALIGN": str(abs(int(str(a).replace(".", "")) - int(str(b).replace(".", "")))),
        }
        return prompt, answer, hints, misconceptions

    # --- multiply decimals ---
    if family_code == "MATH.DEC.MUL":
        p1 = 1 if difficulty <= 2 else rng.randint(1, 2)
        p2 = 1 if difficulty <= 2 else rng.randint(1, 2)
        a = _rand_decimal(rng, 1.0, 10.0 + difficulty * 3, p1)
        b = _rand_decimal(rng, 1.0, 10.0, p2)
        result = a * b
        prompt = f"Multiply {a} × {b}."
        answer = _dec_str(result)
        total_places = p1 + p2
        hints = (
            "Multiply as if there are no decimal points, then count total decimal places.",
            f"The answer should have {total_places} decimal place(s).",
        )
        # Wrong decimal placement
        shifted = result * 10
        misconceptions = {
            "DEC.MUL.WRONG_PLACES": _dec_str(shifted),
        }
        return prompt, answer, hints, misconceptions

    # --- divide decimals ---
    if family_code == "MATH.DEC.DIV":
        divisor = _rand_decimal(rng, 0.2, 5.0, 1)
        if divisor == Decimal(0):
            divisor = Decimal("0.5")
        multiplier = rng.randint(2, 6 + difficulty * 2)
        dividend = divisor * multiplier
        prompt = f"Divide {_dec_str(dividend)} ÷ {_dec_str(divisor)}."
        answer = str(multiplier)
        hints = (
            f"Move the decimal in {_dec_str(divisor)} to make it a whole number, then do the same to {_dec_str(dividend)}.",
            f"This becomes {int(dividend * 10)} ÷ {int(divisor * 10)}.",
        )
        misconceptions = {
            "DEC.DIV.FORGET_SHIFT": _dec_str(Decimal(str(multiplier)) / Decimal(10)),
        }
        return prompt, answer, hints, misconceptions

    # --- estimate ---
    if family_code == "MATH.DEC.ESTIMATE":
        a = _rand_decimal(rng, 5.0, 50.0 + difficulty * 20, 2)
        b = _rand_decimal(rng, 2.0, 30.0 + difficulty * 10, 2)
        exact = a + b
        rounded_a = a.quantize(Decimal(1), rounding=ROUND_HALF_UP)
        rounded_b = b.quantize(Decimal(1), rounding=ROUND_HALF_UP)
        estimate = rounded_a + rounded_b
        prompt = (
            f"Estimate {a} + {b} by rounding each number to the nearest whole number."
        )
        answer = _dec_str(estimate)
        hints = (
            f"Round {a} to {rounded_a} and {b} to {rounded_b}.",
            f"Now add: {rounded_a} + {rounded_b}.",
        )
        misconceptions = {
            "DEC.ESTIMATE.EXACT_NOT_ESTIMATE": _dec_str(exact),
        }
        return prompt, answer, hints, misconceptions

    # --- money change ---
    if family_code == "MATH.DEC.MONEY.CHANGE":
        price = _rand_decimal(rng, 1.5, 15.0 + difficulty * 5, 2)
        bills = [Decimal(5), Decimal(10), Decimal(20), Decimal(50)]
        paid = rng.choice([b for b in bills if b > price])
        change = paid - price
        items = ["sandwich", "notebook", "toy", "book", "snack"]
        item = rng.choice(items)
        prompt = (
            f"A {item} costs ${price}. You pay with a ${_dec_str(paid)} bill. "
            "How much change do you receive?"
        )
        answer = f"${_dec_str(change)}"
        hints = (
            f"Subtract the price from the amount paid: {paid} − {price}.",
        )
        misconceptions = {
            "DEC.MONEY.ADD_INSTEAD": f"${_dec_str(paid + price)}",
        }
        return prompt, answer, hints, misconceptions

    # --- money total ---
    if family_code == "MATH.DEC.MONEY.TOTAL":
        n_items = rng.randint(2, 3 + difficulty)
        prices = [_rand_decimal(rng, 0.5, 8.0 + difficulty * 3, 2) for _ in range(n_items)]
        total = sum(prices, Decimal(0))
        items = ["pencil", "eraser", "ruler", "marker", "sticker", "folder"]
        chosen = rng.sample(items, min(n_items, len(items)))
        parts = [f"a {chosen[i]} for ${prices[i]}" for i in range(len(chosen))]
        listing = ", ".join(parts[:-1]) + f" and {parts[-1]}"
        prompt = f"You buy {listing}. What is the total cost?"
        answer = f"${_dec_str(total)}"
        hints = (
            "Add all the prices together. Line up the decimal points.",
        )
        misconceptions = {
            "DEC.MONEY.MISS_ONE": f"${_dec_str(total - prices[-1])}",
        }
        return prompt, answer, hints, misconceptions

    # --- error: longer is larger ---
    if family_code == "MATH.DEC.ERROR.LONGER_LARGER":
        # Construct a pair where the shorter decimal is larger
        a = Decimal(str(rng.randint(3, 9))) / Decimal(10)  # e.g. 0.6
        b_digits = rng.randint(10, 99)
        b = Decimal(str(b_digits)) / Decimal(1000)  # e.g. 0.045
        while b >= a:
            b_digits = rng.randint(10, 99)
            b = Decimal(str(b_digits)) / Decimal(1000)
        names = ["Chen", "Maria", "Sam", "Priya"]
        name = rng.choice(names)
        prompt = (
            f"{name} says {_dec_str(b)} > {_dec_str(a)} because {_dec_str(b)} "
            f"has more digits. Is {name} correct? Explain."
        )
        answer = f"No. {_dec_str(a)} > {_dec_str(b)} because the tenths digit of {_dec_str(a)} is larger."
        hints = (
            "Compare the tenths digit of each number first.",
            f"{_dec_str(a)} has {int(a * 10)} tenths; {_dec_str(b)} has {int(b * 10)} tenths.",
        )
        misconceptions = {
            "DEC.ERROR.AGREE_LONGER": f"Yes, {_dec_str(b)} is greater.",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"Unknown decimal family: {family_code}")
