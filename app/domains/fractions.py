"""Canonical fraction problem families.

Covers: fraction meaning, equivalence, simplification, comparison, ordering,
four operations, fraction-of-a-quantity, mixed numbers, word problems,
error analysis and misconception probes.
"""

from __future__ import annotations

import random
from fractions import Fraction
from math import gcd

from app.canonical_problem_families import (
    ALL_MODES,
    ProblemFamilySpec,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _frac(n: int, d: int) -> str:
    """Canonical text form of a fraction."""
    if d == 1:
        return str(n)
    return f"{n}/{d}"


def _mixed(whole: int, n: int, d: int) -> str:
    if n == 0:
        return str(whole)
    if whole == 0:
        return _frac(n, d)
    return f"{whole} {n}/{d}"


def _simplify(n: int, d: int) -> tuple[int, int]:
    g = gcd(abs(n), abs(d))
    return n // g, d // g


def _coprime_pair(rng: random.Random, lo: int, hi: int) -> tuple[int, int]:
    """Return (n, d) with 1 <= n < d, gcd(n,d)=1."""
    while True:
        d = rng.randint(lo + 1, hi)
        n = rng.randint(1, d - 1)
        if gcd(n, d) == 1:
            return n, d


def _proper_fraction(rng: random.Random, max_den: int) -> tuple[int, int]:
    d = rng.randint(2, max_den)
    n = rng.randint(1, d - 1)
    return n, d


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    # --- Fraction meaning & equivalence ---
    "MATH.FRAC.EQUIV.FIND": ProblemFamilySpec(
        "MATH.FRAC.EQUIV.FIND", "Find an equivalent fraction",
        "MATH.NF.EQUIVALENT_FRACTIONS", "FRACTION", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.FRAC.SIMPLIFY": ProblemFamilySpec(
        "MATH.FRAC.SIMPLIFY", "Simplify a fraction to lowest terms",
        "MATH.NF.SIMPLIFY", "FRACTION", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency"}),
    ),
    "MATH.FRAC.COMPARE": ProblemFamilySpec(
        "MATH.FRAC.COMPARE", "Compare two fractions",
        "MATH.NF.COMPARE", "COMPARISON", 1, 4, ALL_MODES,
        frozenset({"comparison", "estimation", "conceptual_understanding"}),
    ),
    "MATH.FRAC.ESTIMATE.BENCHMARK": ProblemFamilySpec(
        "MATH.FRAC.ESTIMATE.BENCHMARK", "Estimate a fraction relative to benchmarks",
        "MATH.NF.COMPARE", "ESTIMATION", 1, 3, ALL_MODES,
        frozenset({"estimation", "number_sense", "reasoning"}),
    ),
    # --- Four operations ---
    "MATH.FRAC.ADD.LIKE": ProblemFamilySpec(
        "MATH.FRAC.ADD.LIKE", "Add fractions with like denominators",
        "MATH.NF.ADD_SUBTRACT", "FRACTION", 1, 2, ALL_MODES,
        frozenset({"procedural_fluency"}),
    ),
    "MATH.FRAC.ADD.UNLIKE": ProblemFamilySpec(
        "MATH.FRAC.ADD.UNLIKE", "Add fractions with unlike denominators",
        "MATH.NF.ADD_SUBTRACT", "FRACTION", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.FRAC.SUB.UNLIKE": ProblemFamilySpec(
        "MATH.FRAC.SUB.UNLIKE", "Subtract fractions with unlike denominators",
        "MATH.NF.ADD_SUBTRACT", "FRACTION", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.FRAC.MUL": ProblemFamilySpec(
        "MATH.FRAC.MUL", "Multiply fractions",
        "MATH.NF.MULTIPLY", "FRACTION", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.FRAC.DIV": ProblemFamilySpec(
        "MATH.FRAC.DIV", "Divide fractions",
        "MATH.NF.DIVIDE", "FRACTION", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.FRAC.OF_QUANTITY": ProblemFamilySpec(
        "MATH.FRAC.OF_QUANTITY", "Fraction of a whole-number quantity",
        "MATH.NF.MULTIPLY", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "procedural_fluency", "transfer"}),
    ),
    # --- Error analysis / reasoning ---
    "MATH.FRAC.ERROR.ADD_DENOM": ProblemFamilySpec(
        "MATH.FRAC.ERROR.ADD_DENOM", "Error analysis: adding denominators",
        "MATH.NF.ADD_SUBTRACT", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
    # --- Deep word problems ---
    "MATH.FRAC.WORD.PART_WHOLE": ProblemFamilySpec(
        "MATH.FRAC.WORD.PART_WHOLE", "Fraction word problem: part-whole",
        "MATH.NF.ADD_SUBTRACT", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.FRAC.WORD.REMAINING": ProblemFamilySpec(
        "MATH.FRAC.WORD.REMAINING", "Fraction word problem: what fraction remains",
        "MATH.NF.ADD_SUBTRACT", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "representation"}),
    ),
    "MATH.FRAC.WORD.SCALING": ProblemFamilySpec(
        "MATH.FRAC.WORD.SCALING", "Fraction word problem: recipe scaling",
        "MATH.NF.MULTIPLY", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.FRAC.WORD.DIVISION": ProblemFamilySpec(
        "MATH.FRAC.WORD.DIVISION", "Fraction word problem: sharing/grouping",
        "MATH.NF.DIVIDE", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):
    """Return (prompt, answer, hints, misconceptions) for *family_code*."""

    # --- equivalence ---
    if family_code == "MATH.FRAC.EQUIV.FIND":
        n, d = _coprime_pair(rng, 1, 4 + difficulty * 2)
        mult = rng.randint(2, 3 + difficulty)
        shown_n, shown_d = n * mult, d * mult
        prompt = f"Find a fraction equivalent to {_frac(shown_n, shown_d)} with a smaller denominator."
        answer = _frac(n, d)
        hints = (
            "Look for a number that divides both the numerator and denominator evenly.",
            f"Both {shown_n} and {shown_d} are divisible by {mult}.",
        )
        misconceptions = {
            "FRAC.EQUIV.ADD_INSTEAD": _frac(shown_n - mult, shown_d - mult),
        }
        return prompt, answer, hints, misconceptions

    # --- simplify ---
    if family_code == "MATH.FRAC.SIMPLIFY":
        n, d = _coprime_pair(rng, 1, 4 + difficulty * 2)
        mult = rng.randint(2, 3 + difficulty)
        shown_n, shown_d = n * mult, d * mult
        prompt = f"Simplify {_frac(shown_n, shown_d)} to lowest terms."
        answer = _frac(n, d)
        hints = (
            "Find the greatest common factor of the numerator and denominator.",
            f"GCF({shown_n}, {shown_d}) = {mult}. Divide both by it.",
        )
        # Partial simplification: divide by 2 if mult>2 and both are even
        if mult > 2 and shown_n % 2 == 0 and shown_d % 2 == 0:
            partial = _frac(shown_n // 2, shown_d // 2)
        else:
            partial = _frac(shown_n, shown_d)  # "no simplification" is the error
        misconceptions = {
            "FRAC.SIMPLIFY.PARTIAL": partial,
            "FRAC.SIMPLIFY.FLIP": _frac(d, n),
        }
        return prompt, answer, hints, misconceptions

    # --- compare ---
    if family_code == "MATH.FRAC.COMPARE":
        n1, d1 = _coprime_pair(rng, 1, 4 + difficulty * 2)
        n2, d2 = _coprime_pair(rng, 1, 4 + difficulty * 2)
        while Fraction(n1, d1) == Fraction(n2, d2):
            n2, d2 = _coprime_pair(rng, 1, 4 + difficulty * 2)
        prompt = f"Which is greater: {_frac(n1, d1)} or {_frac(n2, d2)}?"
        if Fraction(n1, d1) > Fraction(n2, d2):
            answer = _frac(n1, d1)
            wrong = _frac(n2, d2)
        else:
            answer = _frac(n2, d2)
            wrong = _frac(n1, d1)
        hints = (
            "Find a common denominator so both fractions have the same-size pieces.",
            f"Convert both to denominator {d1 * d2} and compare numerators.",
        )
        misconceptions = {
            "FRAC.COMPARE.DENOM_ONLY": wrong,
        }
        return prompt, answer, hints, misconceptions

    # --- benchmark estimation ---
    if family_code == "MATH.FRAC.ESTIMATE.BENCHMARK":
        n, d = _proper_fraction(rng, 6 + difficulty * 4)
        val = Fraction(n, d)
        if val < Fraction(1, 4):
            answer = "closer to 0"
        elif val < Fraction(3, 8):
            answer = "closer to 1/4"
        elif val < Fraction(5, 8):
            answer = "closer to 1/2"
        elif val < Fraction(7, 8):
            answer = "closer to 3/4"
        else:
            answer = "closer to 1"
        prompt = f"Is {_frac(n, d)} closer to 0, 1/4, 1/2, 3/4 or 1?"
        hints = (
            "Think about where the fraction sits on a number line between 0 and 1.",
            f"Compare {_frac(n, d)} to 1/2 first — is it more or less than half?",
        )
        misconceptions = {
            "FRAC.ESTIMATE.IGNORE_DENOM": "closer to 0" if n > d // 2 else "closer to 1",
        }
        return prompt, answer, hints, misconceptions

    # --- add like denominators ---
    if family_code == "MATH.FRAC.ADD.LIKE":
        d = rng.randint(3, 6 + difficulty * 2)
        n1 = rng.randint(1, d - 1)
        n2 = rng.randint(1, d - 1)
        total_n = n1 + n2
        sn, sd = _simplify(total_n, d)
        if total_n >= d:
            whole = total_n // d
            rem = total_n % d
            if rem == 0:
                answer = str(whole)
            else:
                rn, rd = _simplify(rem, d)
                answer = _mixed(whole, rn, rd)
        else:
            answer = _frac(sn, sd)
        prompt = f"Add {_frac(n1, d)} + {_frac(n2, d)}."
        hints = (
            "When denominators match, add the numerators and keep the denominator.",
            f"{n1} + {n2} = {total_n}. Write {_frac(total_n, d)} and simplify if needed.",
        )
        misconceptions = {
            "FRAC.ADD.ADD_DENOM": _frac(n1 + n2, d + d),
        }
        return prompt, answer, hints, misconceptions

    # --- add unlike ---
    if family_code == "MATH.FRAC.ADD.UNLIKE":
        max_d = 5 + difficulty * 3
        n1, d1 = _proper_fraction(rng, max_d)
        n2, d2 = _proper_fraction(rng, max_d)
        while d1 == d2:
            n2, d2 = _proper_fraction(rng, max_d)
        result = Fraction(n1, d1) + Fraction(n2, d2)
        if result >= 1:
            whole = int(result)
            frac_part = result - whole
            if frac_part == 0:
                answer = str(whole)
            else:
                answer = _mixed(whole, frac_part.numerator, frac_part.denominator)
        else:
            answer = _frac(result.numerator, result.denominator)
        prompt = f"Add {_frac(n1, d1)} + {_frac(n2, d2)}."
        lcd = (d1 * d2) // gcd(d1, d2)
        hints = (
            f"The denominators {d1} and {d2} are different — find a common denominator.",
            f"The LCD is {lcd}. Rewrite both fractions, then add.",
            f"{_frac(n1 * (lcd // d1), lcd)} + {_frac(n2 * (lcd // d2), lcd)}.",
        )
        misconceptions = {
            "FRAC.ADD.ADD_DENOM": _frac(n1 + n2, d1 + d2),
            "FRAC.ADD.FORGET_CONVERT": _frac(n1 + n2, lcd),
        }
        return prompt, answer, hints, misconceptions

    # --- subtract unlike ---
    if family_code == "MATH.FRAC.SUB.UNLIKE":
        max_d = 5 + difficulty * 3
        n1, d1 = _proper_fraction(rng, max_d)
        n2, d2 = _proper_fraction(rng, max_d)
        while d1 == d2 or Fraction(n1, d1) <= Fraction(n2, d2):
            n1, d1 = _proper_fraction(rng, max_d)
            n2, d2 = _proper_fraction(rng, max_d)
        result = Fraction(n1, d1) - Fraction(n2, d2)
        answer = _frac(result.numerator, result.denominator)
        prompt = f"Subtract {_frac(n1, d1)} − {_frac(n2, d2)}."
        lcd = (d1 * d2) // gcd(d1, d2)
        hints = (
            f"Find a common denominator for {d1} and {d2}.",
            f"The LCD is {lcd}. Rewrite, then subtract numerators.",
        )
        misconceptions = {
            "FRAC.SUB.SUB_DENOM": _frac(abs(n1 - n2), abs(d1 - d2)) if d1 != d2 else "0",
            "FRAC.SUB.FORGET_CONVERT": _frac(abs(n1 - n2), lcd),
        }
        return prompt, answer, hints, misconceptions

    # --- multiply ---
    if family_code == "MATH.FRAC.MUL":
        max_d = 4 + difficulty * 2
        n1, d1 = _proper_fraction(rng, max_d)
        n2, d2 = _proper_fraction(rng, max_d)
        result = Fraction(n1, d1) * Fraction(n2, d2)
        answer = _frac(result.numerator, result.denominator)
        prompt = f"Multiply {_frac(n1, d1)} × {_frac(n2, d2)}."
        hints = (
            "Multiply the numerators together and the denominators together.",
            f"{n1} × {n2} = {n1 * n2} and {d1} × {d2} = {d1 * d2}. Simplify.",
        )
        misconceptions = {
            "FRAC.MUL.COMMON_DENOM": _frac(n1 * n2, d1),
            "FRAC.MUL.ADD_INSTEAD": _frac(
                (Fraction(n1, d1) + Fraction(n2, d2)).numerator,
                (Fraction(n1, d1) + Fraction(n2, d2)).denominator,
            ),
        }
        return prompt, answer, hints, misconceptions

    # --- divide ---
    if family_code == "MATH.FRAC.DIV":
        max_d = 4 + difficulty * 2
        n1, d1 = _proper_fraction(rng, max_d)
        n2, d2 = _proper_fraction(rng, max_d)
        result = Fraction(n1, d1) / Fraction(n2, d2)
        if result >= 1:
            whole = int(result)
            frac_part = result - whole
            if frac_part == 0:
                answer = str(whole)
            else:
                answer = _mixed(whole, frac_part.numerator, frac_part.denominator)
        else:
            answer = _frac(result.numerator, result.denominator)
        prompt = f"Divide {_frac(n1, d1)} ÷ {_frac(n2, d2)}."
        hints = (
            "To divide by a fraction, multiply by its reciprocal.",
            f"Flip {_frac(n2, d2)} to get {_frac(d2, n2)}, then multiply.",
            f"{_frac(n1, d1)} × {_frac(d2, n2)}.",
        )
        # Common error: multiply straight across without flipping
        wrong_result = Fraction(n1 * n2, d1 * d2)
        misconceptions = {
            "FRAC.DIV.NO_RECIPROCAL": _frac(wrong_result.numerator, wrong_result.denominator),
            "FRAC.DIV.FLIP_WRONG": _frac(
                (Fraction(d1, n1) * Fraction(n2, d2)).numerator,
                (Fraction(d1, n1) * Fraction(n2, d2)).denominator,
            ),
        }
        return prompt, answer, hints, misconceptions

    # --- fraction of a quantity ---
    if family_code == "MATH.FRAC.OF_QUANTITY":
        d = rng.randint(2, 4 + difficulty)
        n = rng.randint(2, d - 1) if d > 2 else 1
        while gcd(n, d) != 1:
            n = rng.randint(2, d - 1) if d > 2 else 1
        total = d * rng.randint(2 + difficulty, 6 + difficulty * 2)
        result = n * total // d
        contexts = [
            f"A class has {total} students. {_frac(n, d)} of them brought lunch from home. How many students brought lunch?",
            f"A bookshelf holds {total} books. {_frac(n, d)} of the books are fiction. How many fiction books are there?",
            f"A baker made {total} cookies. She gave away {_frac(n, d)} of them. How many cookies did she give away?",
        ]
        prompt = rng.choice(contexts)
        answer = str(result)
        hints = (
            f"Finding {_frac(n, d)} of {total} means multiplying {_frac(n, d)} × {total}.",
            f"Divide {total} by {d} first to find one part, then multiply by {n}.",
        )
        misconceptions = {
            "FRAC.OF.DIVIDE_ONLY": str(total // d),
            "FRAC.OF.ADD_FRAC": str(total + n),
        }
        return prompt, answer, hints, misconceptions

    # --- error analysis: adding denominators ---
    if family_code == "MATH.FRAC.ERROR.ADD_DENOM":
        max_d = 5 + difficulty * 2
        n1, d1 = _proper_fraction(rng, max_d)
        n2, d2 = _proper_fraction(rng, max_d)
        while d1 == d2:
            n2, d2 = _proper_fraction(rng, max_d)
        wrong_answer = _frac(n1 + n2, d1 + d2)
        correct_result = Fraction(n1, d1) + Fraction(n2, d2)
        correct = _frac(correct_result.numerator, correct_result.denominator)
        names = ["Sam", "Taylor", "Alex", "Jordan", "Riley"]
        name = rng.choice(names)
        prompt = (
            f"{name} says that {_frac(n1, d1)} + {_frac(n2, d2)} = {wrong_answer}. "
            f"What mistake did {name} make?"
        )
        answer = f"{name} added the denominators. The correct answer is {correct}."
        hints = (
            f"Check: is {wrong_answer} a correct sum?",
            "When adding fractions you must find a common denominator first — you cannot add the denominators.",
            "Rewrite both fractions with a common denominator and try again.",
        )
        misconceptions = {
            "FRAC.ERROR.AGREES_WITH_WRONG": wrong_answer,
            "FRAC.ERROR.CORRECT_BUT_NO_EXPLAIN": correct,
        }
        return prompt, answer, hints, misconceptions

    # --- word: part-whole ---
    if family_code == "MATH.FRAC.WORD.PART_WHOLE":
        d = rng.randint(3, 5 + difficulty)
        part1 = rng.randint(1, d - 2)
        part2 = rng.randint(1, d - part1 - 1)
        total_parts = part1 + part2
        result = Fraction(total_parts, d)
        contexts = [
            (f"During a field trip, {_frac(part1, d)} of the class visited the museum "
             f"and {_frac(part2, d)} visited the aquarium. What fraction of the class "
             "went on a trip?"),
            (f"A garden is divided into equal sections. {_frac(part1, d)} is planted with "
             f"tomatoes and {_frac(part2, d)} with peppers. What fraction of the garden "
             "is planted?"),
        ]
        prompt = rng.choice(contexts)
        answer = _frac(result.numerator, result.denominator)
        hints = (
            "Both fractions have the same denominator — add the numerators.",
            f"{part1} + {part2} = {total_parts} parts out of {d}.",
        )
        misconceptions = {
            "FRAC.WORD.ADD_DENOM": _frac(total_parts, d + d),
        }
        return prompt, answer, hints, misconceptions

    # --- word: remaining ---
    if family_code == "MATH.FRAC.WORD.REMAINING":
        d = rng.randint(3, 5 + difficulty)
        used = rng.randint(1, d - 1)
        remaining = Fraction(d - used, d)
        contexts = [
            (f"Lena drank {_frac(used, d)} of a bottle of water. "
             "What fraction of the water is left?"),
            (f"A painter used {_frac(used, d)} of a can of paint. "
             "What fraction remains?"),
        ]
        prompt = rng.choice(contexts)
        answer = _frac(remaining.numerator, remaining.denominator)
        hints = (
            "The whole bottle or can represents 1. Subtract the fraction used.",
            f"1 − {_frac(used, d)} = {_frac(d, d)} − {_frac(used, d)}.",
        )
        misconceptions = {
            "FRAC.WORD.SUBTRACT_FROM_NUMER": _frac(used, d),
        }
        return prompt, answer, hints, misconceptions

    # --- word: recipe scaling ---
    if family_code == "MATH.FRAC.WORD.SCALING":
        ingredient_d = rng.randint(2, 4)
        ingredient_n = rng.randint(1, ingredient_d)
        scale_factor = rng.choice([2, 3]) if difficulty <= 2 else Fraction(3, 2)
        result = Fraction(ingredient_n, ingredient_d) * scale_factor
        if isinstance(scale_factor, int):
            scale_text = str(scale_factor)
        else:
            scale_text = _frac(scale_factor.numerator, scale_factor.denominator)
        items = [("cups of flour", "a recipe"), ("tablespoons of sugar", "a batch"),
                 ("cups of milk", "a recipe")]
        item_text, batch_text = rng.choice(items)
        prompt = (
            f"A recipe calls for {_frac(ingredient_n, ingredient_d)} {item_text}. "
            f"If you make {scale_text} times {batch_text}, how much {item_text.split(' ', 1)[0]}s "
            "do you need?"
        )
        if result >= 1:
            whole = int(result)
            fpart = result - whole
            answer = _mixed(whole, fpart.numerator, fpart.denominator) if fpart else str(whole)
        else:
            answer = _frac(result.numerator, result.denominator)
        hints = (
            f"Multiply {_frac(ingredient_n, ingredient_d)} by {scale_text}.",
            "Multiply numerators and denominators, then simplify.",
        )
        misconceptions = {
            "FRAC.WORD.ADD_SCALE": _frac(
                (Fraction(ingredient_n, ingredient_d) + scale_factor).numerator,
                (Fraction(ingredient_n, ingredient_d) + scale_factor).denominator,
            ),
        }
        return prompt, answer, hints, misconceptions

    # --- word: division (sharing/grouping) ---
    if family_code == "MATH.FRAC.WORD.DIVISION":
        total_n = rng.randint(1, 3 + difficulty)
        total_d = rng.randint(2, 4)
        divisor_n = rng.randint(1, 2)
        divisor_d = rng.randint(2, 4)
        total = Fraction(total_n, total_d)
        divisor = Fraction(divisor_n, divisor_d)
        result = total / divisor
        if result >= 1:
            whole = int(result)
            fpart = result - whole
            answer = _mixed(whole, fpart.numerator, fpart.denominator) if fpart else str(whole)
        else:
            answer = _frac(result.numerator, result.denominator)
        contexts = [
            (f"You have {_frac(total_n, total_d)} of a pizza. Each serving is "
             f"{_frac(divisor_n, divisor_d)} of a pizza. How many servings do you have?"),
            (f"A ribbon is {_frac(total_n, total_d)} meters long. Each bow needs "
             f"{_frac(divisor_n, divisor_d)} meters. How many bows can be made?"),
        ]
        prompt = rng.choice(contexts)
        hints = (
            f"This is a division problem: {_frac(total_n, total_d)} ÷ {_frac(divisor_n, divisor_d)}.",
            "Multiply by the reciprocal of the divisor.",
        )
        wrong_mul = total * divisor
        misconceptions = {
            "FRAC.DIV.MULTIPLY_INSTEAD": _frac(wrong_mul.numerator, wrong_mul.denominator),
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"Unknown fraction family: {family_code}")
