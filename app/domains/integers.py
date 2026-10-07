"""Canonical integer-foundations problem families.

Covers: positive/negative meaning, number-line position, opposites,
absolute value, comparing, ordering, integer addition, subtraction,
multiplication, division, and real-world contexts.
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


def _signed(n: int) -> str:
    """Format integer with explicit sign for negatives, no sign for positives."""
    return str(n)


def _pos_neg(rng: random.Random, lo: int, hi: int) -> int:
    """Return a non-zero integer in [-hi, -lo] ∪ [lo, hi]."""
    val = rng.randint(lo, hi)
    return val if rng.random() < 0.5 else -val


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.INT.MEANING": ProblemFamilySpec(
        "MATH.INT.MEANING", "Interpret positive/negative in context",
        "MATH.NS.INTEGERS", "REASONING", 1, 3, ALL_MODES,
        frozenset({"conceptual_understanding", "number_sense", "modeling"}),
    ),
    "MATH.INT.OPPOSITE": ProblemFamilySpec(
        "MATH.INT.OPPOSITE", "Find the opposite of an integer",
        "MATH.NS.INTEGERS", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"conceptual_understanding", "number_sense"}),
    ),
    "MATH.INT.ABS_VALUE": ProblemFamilySpec(
        "MATH.INT.ABS_VALUE", "Find the absolute value",
        "MATH.NS.INTEGERS", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"conceptual_understanding", "number_sense"}),
    ),
    "MATH.INT.COMPARE": ProblemFamilySpec(
        "MATH.INT.COMPARE", "Compare two integers",
        "MATH.NS.INTEGERS", "COMPARISON", 1, 4, ALL_MODES,
        frozenset({"comparison", "number_sense", "conceptual_understanding"}),
    ),
    "MATH.INT.ORDER": ProblemFamilySpec(
        "MATH.INT.ORDER", "Order integers from least to greatest",
        "MATH.NS.INTEGERS", "COMPARISON", 1, 4, ALL_MODES,
        frozenset({"comparison", "number_sense"}),
    ),
    "MATH.INT.ADD": ProblemFamilySpec(
        "MATH.INT.ADD", "Add integers",
        "MATH.NS.INTEGER_OPERATIONS", "NUMBER_SENSE", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense", "conceptual_understanding"}),
    ),
    "MATH.INT.SUB": ProblemFamilySpec(
        "MATH.INT.SUB", "Subtract integers",
        "MATH.NS.INTEGER_OPERATIONS", "NUMBER_SENSE", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense", "conceptual_understanding"}),
    ),
    "MATH.INT.MUL": ProblemFamilySpec(
        "MATH.INT.MUL", "Multiply integers",
        "MATH.NS.INTEGER_OPERATIONS", "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.INT.DIV": ProblemFamilySpec(
        "MATH.INT.DIV", "Divide integers",
        "MATH.NS.INTEGER_OPERATIONS", "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.INT.WORD": ProblemFamilySpec(
        "MATH.INT.WORD", "Integer word problem in context",
        "MATH.NS.INTEGER_OPERATIONS", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "number_sense"}),
    ),
    "MATH.INT.ERROR.ABS_COMPARE": ProblemFamilySpec(
        "MATH.INT.ERROR.ABS_COMPARE", "Error: comparing by absolute value",
        "MATH.NS.INTEGERS", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
    "MATH.INT.ERROR.SUB_NEGATIVE": ProblemFamilySpec(
        "MATH.INT.ERROR.SUB_NEGATIVE", "Error: subtracting a negative",
        "MATH.NS.INTEGER_OPERATIONS", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build(family_code: str, rng: random.Random, difficulty: int):

    # --- meaning in context ---
    if family_code == "MATH.INT.MEANING":
        contexts = [
            ("temperature", "3 degrees below zero", -3, "degrees"),
            ("temperature", "15 degrees above zero", 15, "degrees"),
            ("elevation", "200 feet below sea level", -200, "feet"),
            ("elevation", "450 feet above sea level", 450, "feet"),
            ("finance", "a loss of $50", -50, "dollars"),
            ("finance", "a gain of $120", 120, "dollars"),
            ("game", "losing 8 points", -8, "points"),
            ("game", "gaining 12 points", 12, "points"),
        ]
        ctx_name, description, value, _unit = rng.choice(contexts)
        prompt = (
            f"In a {ctx_name} context, how would you represent "
            f"'{description}' as an integer?"
        )
        answer = _signed(value)
        hints = (
            "'Below zero', 'loss', or 'losing' typically means negative.",
            "'Above zero', 'gain', or 'gaining' typically means positive.",
        )
        wrong = -value
        misconceptions = {
            "INT.MEANING.WRONG_SIGN": _signed(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- opposite ---
    if family_code == "MATH.INT.OPPOSITE":
        hi = 10 + difficulty * 20
        n = _pos_neg(rng, 1, hi)
        prompt = f"What is the opposite of {_signed(n)}?"
        answer = _signed(-n)
        hints = (
            "The opposite of a number is the same distance from zero but on the other side.",
            f"The opposite of {_signed(n)} is the number that makes {_signed(n)} + ? = 0.",
        )
        misconceptions = {
            "INT.OPPOSITE.ABS_VALUE": str(abs(n)),
        }
        return prompt, answer, hints, misconceptions

    # --- absolute value ---
    if family_code == "MATH.INT.ABS_VALUE":
        hi = 10 + difficulty * 20
        n = _pos_neg(rng, 1, hi)
        prompt = f"What is |{_signed(n)}|?"
        answer = str(abs(n))
        hints = (
            "Absolute value is the distance from zero on the number line.",
            "It is always non-negative.",
        )
        misconceptions = {
            "INT.ABS.NEGATE": _signed(-abs(n)),
        }
        return prompt, answer, hints, misconceptions

    # --- compare ---
    if family_code == "MATH.INT.COMPARE":
        hi = 10 + difficulty * 15
        a = _pos_neg(rng, 1, hi)
        b = _pos_neg(rng, 1, hi)
        while a == b:
            b = _pos_neg(rng, 1, hi)
        prompt = (
            f"Which is greater: {_signed(a)} or {_signed(b)}? "
            f"(A) {_signed(a)} (B) {_signed(b)}"
        )
        if a > b:
            answer = "A"
            wrong = "B"
        else:
            answer = "B"
            wrong = "A"
        hints = (
            "On a number line, the number further to the right is greater.",
            "A positive number is always greater than a negative number.",
        )
        misconceptions = {
            "INT.COMPARE.ABS_VALUE": wrong,
        }
        return prompt, answer, hints, misconceptions

    # --- order ---
    if family_code == "MATH.INT.ORDER":
        hi = 10 + difficulty * 15
        count = 4 + min(difficulty, 2)
        nums: list[int] = []
        while len(nums) < count:
            n = _pos_neg(rng, 0, hi)
            if n not in nums:
                nums.append(n)
        sorted_nums = sorted(nums)
        prompt = (
            f"Order from least to greatest: "
            f"{', '.join(_signed(n) for n in nums)}"
        )
        answer = ", ".join(_signed(n) for n in sorted_nums)
        hints = (
            "Negative numbers come before positive numbers.",
            "Among negative numbers, the one closer to zero is greater.",
        )
        misconceptions = {
            "INT.ORDER.ABS_SORT": ", ".join(_signed(n) for n in sorted(nums, key=abs)),
        }
        return prompt, answer, hints, misconceptions

    # --- addition ---
    if family_code == "MATH.INT.ADD":
        hi = 10 + difficulty * 15
        a = _pos_neg(rng, 1, hi)
        b = _pos_neg(rng, 1, hi)
        result = a + b
        b_display = f"({_signed(b)})" if b < 0 else _signed(b)
        prompt = f"Compute {_signed(a)} + {b_display}."
        answer = _signed(result)
        hints = (
            "If both signs are the same, add the absolute values and keep the sign.",
            "If the signs differ, subtract the smaller absolute value from the larger.",
        )
        # Misconception: add absolute values with wrong sign
        wrong = -(abs(a) + abs(b)) if result >= 0 else (abs(a) + abs(b))
        misconceptions = {
            "INT.ADD.WRONG_SIGN": _signed(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- subtraction ---
    if family_code == "MATH.INT.SUB":
        hi = 10 + difficulty * 15
        a = _pos_neg(rng, 1, hi)
        b = _pos_neg(rng, 1, hi)
        result = a - b
        b_display = f"({_signed(b)})" if b < 0 else _signed(b)
        prompt = f"Compute {_signed(a)} − {b_display}."
        answer = _signed(result)
        hints = (
            "Subtracting a number is the same as adding its opposite.",
            f"{_signed(a)} − {b_display} = {_signed(a)} + {_signed(-b)}.",
        )
        # Misconception: treat as a + b instead of a - b
        wrong = a + b
        if wrong == result:
            wrong = a + abs(b)  # fallback
        misconceptions = {
            "INT.SUB.ADD_INSTEAD": _signed(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- multiplication ---
    if family_code == "MATH.INT.MUL":
        hi = 5 + difficulty * 4
        a = _pos_neg(rng, 1, hi)
        b = _pos_neg(rng, 1, hi)
        result = a * b
        b_display = f"({_signed(b)})" if b < 0 else _signed(b)
        prompt = f"Compute {_signed(a)} × {b_display}."
        answer = _signed(result)
        hints = (
            "Positive × Positive = Positive. Negative × Negative = Positive.",
            "Positive × Negative = Negative. Negative × Positive = Negative.",
        )
        misconceptions = {
            "INT.MUL.WRONG_SIGN": _signed(-result) if result != 0 else "1",
        }
        return prompt, answer, hints, misconceptions

    # --- division ---
    if family_code == "MATH.INT.DIV":
        hi = 5 + difficulty * 3
        divisor = _pos_neg(rng, 1, hi)
        while divisor == 0:
            divisor = _pos_neg(rng, 1, hi)
        quotient = _pos_neg(rng, 1, hi)
        dividend = divisor * quotient  # ensure exact
        d_display = f"({_signed(divisor)})" if divisor < 0 else _signed(divisor)
        prompt = f"Compute {_signed(dividend)} ÷ {d_display}."
        answer = _signed(quotient)
        hints = (
            "Same sign → positive result. Different signs → negative result.",
            f"|{abs(dividend)}| ÷ |{abs(divisor)}| = {abs(quotient)}. Then apply sign rule.",
        )
        misconceptions = {
            "INT.DIV.WRONG_SIGN": _signed(-quotient) if quotient != 0 else "1",
        }
        return prompt, answer, hints, misconceptions

    # --- word problem ---
    if family_code == "MATH.INT.WORD":
        scenarios = [
            # (template, answer_fn)
            lambda r, d: _temp_scenario(r, d),
            lambda r, d: _elev_scenario(r, d),
            lambda r, d: _money_scenario(r, d),
        ]
        scenario_fn = rng.choice(scenarios)
        prompt, answer, hints, misconceptions = scenario_fn(rng, difficulty)
        return prompt, answer, hints, misconceptions

    # --- error: comparing by absolute value ---
    if family_code == "MATH.INT.ERROR.ABS_COMPARE":
        a = -rng.randint(5 + difficulty, 15 + difficulty * 5)
        b = rng.randint(1, abs(a) - 1)  # |a| > b, but b > a (since a < 0)
        names = ["Ava", "Ethan", "Mia", "Noah"]
        name = rng.choice(names)
        prompt = (
            f"{name} says {_signed(a)} > {_signed(b)} because |{_signed(a)}| > |{_signed(b)}|. "
            f"Is {name} correct? "
            f"(A) No — {_signed(b)} > {_signed(a)} because {_signed(a)} is negative. "
            f"(B) Yes — larger absolute value means greater number. "
            f"(C) They are equal."
        )
        answer = "A"
        hints = (
            "Absolute value tells you distance from zero, not which number is greater.",
            "Any positive number is greater than any negative number.",
        )
        misconceptions = {
            "INT.ERROR.ABS_GREATER": "B",
        }
        return prompt, answer, hints, misconceptions

    # --- error: subtracting a negative ---
    if family_code == "MATH.INT.ERROR.SUB_NEGATIVE":
        a = rng.randint(5, 15 + difficulty * 5)
        b = -rng.randint(2, 8 + difficulty * 3)
        correct = a - b  # a - (-|b|) = a + |b|
        wrong = a + b  # student subtracts instead of adding
        names = ["Zara", "Marcus", "Lin", "Priya"]
        name = rng.choice(names)
        prompt = (
            f"{name} says {_signed(a)} − ({_signed(b)}) = {_signed(wrong)}. "
            f"What is the correct answer? "
            f"(A) {_signed(correct)} "
            f"(B) {_signed(wrong)} "
            f"(C) {_signed(-correct)}"
        )
        answer = "A"
        hints = (
            "Subtracting a negative is the same as adding the positive.",
            f"{_signed(a)} − ({_signed(b)}) = {_signed(a)} + {abs(b)} = {_signed(correct)}.",
        )
        misconceptions = {
            "INT.ERROR.SUB_NEG.DOUBLE_MINUS": "B",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")


# ---------------------------------------------------------------------------
# Word-problem scenario helpers
# ---------------------------------------------------------------------------

def _temp_scenario(rng: random.Random, difficulty: int):
    start = rng.randint(-10, 10) * (1 + difficulty)
    change = rng.randint(1, 10 + difficulty * 5)
    direction = rng.choice(["rose", "dropped"])
    if direction == "rose":
        final = start + change
    else:
        final = start - change
    prompt = (
        f"The temperature was {_signed(start)}°F. It {direction} by {change} degrees. "
        f"What is the new temperature?"
    )
    answer = f"{_signed(final)}"
    hints = (
        f"'{direction}' means {'add' if direction == 'rose' else 'subtract'} {change}.",
        f"{_signed(start)} {'+ ' if direction == 'rose' else '− '}{change} = {_signed(final)}.",
    )
    wrong = start - change if direction == "rose" else start + change
    misconceptions = {
        "INT.WORD.WRONG_DIRECTION": _signed(wrong),
    }
    return prompt, answer, hints, misconceptions


def _elev_scenario(rng: random.Random, difficulty: int):
    a = rng.randint(-500, 500) * (1 + difficulty // 2)
    b = rng.randint(-500, 500) * (1 + difficulty // 2)
    diff = abs(a - b)
    prompt = (
        f"A hiker starts at {_signed(a)} feet elevation and climbs to {_signed(b)} feet. "
        f"What is the change in elevation?"
    )
    answer = _signed(b - a)
    hints = (
        "Change = final − initial.",
        f"{_signed(b)} − {_signed(a)} = {_signed(b - a)}.",
    )
    misconceptions = {
        "INT.WORD.ABS_ONLY": str(diff),
    }
    return prompt, answer, hints, misconceptions


def _money_scenario(rng: random.Random, difficulty: int):
    balance = rng.randint(-100, 200) * (1 + difficulty)
    deposit = rng.randint(10, 100 + difficulty * 50)
    withdrawal = rng.randint(10, 100 + difficulty * 50)
    final = balance + deposit - withdrawal
    prompt = (
        f"A bank account has a balance of ${_signed(balance)}. "
        f"A deposit of ${deposit} is made, then a withdrawal of ${withdrawal}. "
        f"What is the new balance?"
    )
    answer = f"${_signed(final)}"
    hints = (
        f"Start: ${_signed(balance)}. Add the deposit, subtract the withdrawal.",
        f"${_signed(balance)} + ${deposit} − ${withdrawal} = ${_signed(final)}.",
    )
    wrong = balance - deposit + withdrawal
    misconceptions = {
        "INT.WORD.REVERSED_OPS": f"${_signed(wrong)}",
    }
    return prompt, answer, hints, misconceptions
