"""Canonical proportion problem families.

Covers: identifying proportional relationships, missing-value proportions,
scale factors, proportion construction, solving, distinguishing proportional
from non-proportional, multi-step proportional reasoning, and reasoning tasks.
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

def _frac(n: int, d: int) -> str:
    if d == 1:
        return str(n)
    return f"{n}/{d}"


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.PROP.IDENTIFY": ProblemFamilySpec(
        "MATH.PROP.IDENTIFY", "Identify whether a relationship is proportional",
        "MATH.RP.PROPORTION.IDENTIFY", "REASONING", 1, 3, ALL_MODES,
        frozenset({"conceptual_understanding", "reasoning", "misconception_probe"}),
    ),
    "MATH.PROP.MISSING_VALUE": ProblemFamilySpec(
        "MATH.PROP.MISSING_VALUE", "Find the missing value in a proportion",
        "MATH.RP.PROPORTION.SOLVE", "PROPORTION", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency"}),
    ),
    "MATH.PROP.SCALE_FACTOR": ProblemFamilySpec(
        "MATH.PROP.SCALE_FACTOR", "Determine the scale factor",
        "MATH.RP.PROPORTION.SOLVE", "PROPORTION", 1, 3, ALL_MODES,
        frozenset({"conceptual_understanding", "procedural_fluency"}),
    ),
    "MATH.PROP.CONSTRUCT": ProblemFamilySpec(
        "MATH.PROP.CONSTRUCT", "Set up a proportion from a word context",
        "MATH.RP.PROPORTION.SOLVE", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "representation", "reasoning"}),
    ),
    "MATH.PROP.SOLVE_WORD": ProblemFamilySpec(
        "MATH.PROP.SOLVE_WORD", "Solve a proportion word problem",
        "MATH.RP.PROPORTION.SOLVE", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "procedural_fluency", "transfer"}),
    ),
    "MATH.PROP.NONPROPORTIONAL": ProblemFamilySpec(
        "MATH.PROP.NONPROPORTIONAL", "Distinguish proportional from non-proportional",
        "MATH.RP.PROPORTION.IDENTIFY", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "misconception_probe", "conceptual_understanding"}),
    ),
    "MATH.PROP.MULTISTEP": ProblemFamilySpec(
        "MATH.PROP.MULTISTEP", "Multi-step proportional reasoning",
        "MATH.RP.PROPORTION.SOLVE", "WORD_PROBLEM", 3, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer", "procedural_fluency"}),
    ),
    "MATH.PROP.CROSS_MULTIPLY.WHY": ProblemFamilySpec(
        "MATH.PROP.CROSS_MULTIPLY.WHY", "Reasoning: why cross multiplication works",
        "MATH.RP.PROPORTION.SOLVE", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):
    """Return (prompt, answer, hints, misconceptions) for *family_code*."""

    # --- identify proportional ---
    if family_code == "MATH.PROP.IDENTIFY":
        is_prop = rng.choice([True, False])
        k = rng.randint(2, 5 + difficulty)
        offset = rng.randint(1, 4)
        xs = [rng.randint(1, 4 + difficulty) for _ in range(4)]
        xs = sorted(set(xs))
        while len(xs) < 3:
            xs.append(xs[-1] + 1)
        if is_prop:
            pairs = [(x, k * x) for x in xs]
            answer = "Yes, the relationship is proportional."
        else:
            pairs = [(x, k * x + offset) for x in xs]
            answer = "No, the relationship is not proportional."
        table_str = " | ".join(f"({x}, {y})" for x, y in pairs)
        prompt = f"Is the relationship shown in this table proportional? {table_str}"
        hints = (
            "Check whether y/x gives the same value for every pair.",
            (f"For the first pair, y/x = {pairs[0][1]}/{pairs[0][0]}."
             f" For the second, y/x = {pairs[1][1]}/{pairs[1][0]}."),
        )
        misconceptions = {
            "PROP.IDENTIFY.CONSTANT_DIFF": (
                "Yes, the relationship is proportional."
                if not is_prop else
                "No, the relationship is not proportional."
            ),
        }
        return prompt, answer, hints, misconceptions

    # --- missing value ---
    if family_code == "MATH.PROP.MISSING_VALUE":
        a = rng.randint(2, 6 + difficulty)
        b = rng.randint(2, 6 + difficulty)
        while a == b:
            b = rng.randint(2, 6 + difficulty)
        mult = rng.randint(2, 4 + difficulty)
        position = rng.choice(["d", "c"])  # a/b = c/d
        if position == "d":
            c = a * mult
            d = b * mult
            prompt = f"Solve {a}/{b} = {c}/?."
            answer = str(d)
            misconceptions = {
                "PROP.MISSING.ADD_CROSS": str(a * c + b),
                "PROP.MISSING.WRONG_PAIR": str(a * b // c) if c != 0 else "1",
            }
        else:
            c = a * mult
            d = b * mult
            prompt = f"Solve {a}/{b} = ?/{d}."
            answer = str(c)
            misconceptions = {
                "PROP.MISSING.ADD_CROSS": str(a * d + b),
                "PROP.MISSING.DIVIDE_WRONG": str(d // b) if b != 0 else "1",
            }
        hints = (
            "Cross-multiply and solve for the unknown.",
            f"Multiply {a} × {d if position == 'd' else '?'} = {b} × {c if position == 'c' else '?'}.",
        )
        return prompt, answer, hints, misconceptions

    # --- scale factor ---
    if family_code == "MATH.PROP.SCALE_FACTOR":
        small = rng.randint(2, 6 + difficulty)
        factor = rng.randint(2, 5 + difficulty)
        large = small * factor
        contexts = [
            (f"A photo is enlarged from {small} cm wide to {large} cm wide.",
             "enlargement"),
            (f"A model train is {small} cm long. The real train is {large} cm long.",
             "the model to the real train"),
        ]
        ctx, label = rng.choice(contexts)
        prompt = f"{ctx} What is the scale factor of {label}?"
        answer = str(factor)
        hints = (
            f"The scale factor tells you how many times larger {large} is than {small}.",
            f"Divide: {large} ÷ {small}.",
        )
        misconceptions = {
            "PROP.SCALE.SUBTRACT": str(large - small),
            "PROP.SCALE.REVERSED": _frac(1, factor),
        }
        return prompt, answer, hints, misconceptions

    # --- construct proportion ---
    if family_code == "MATH.PROP.CONSTRUCT":
        a = rng.randint(2, 5 + difficulty)
        b = rng.randint(3, 8 + difficulty)
        while a == b:
            b = rng.randint(3, 8 + difficulty)
        mult = rng.randint(2, 4 + difficulty)
        while a * b == b * mult:  # avoid misconception matching correct
            mult = rng.randint(2, 4 + difficulty)
        target_a = a * mult
        contexts = [
            (f"If {a} tickets cost ${b}, how much do {target_a} tickets cost?",
             f"{a}/{b} = {target_a}/x", str(b * mult)),
            (f"A car uses {a} gallons of gas to go {b} miles. How far can it go on {target_a} gallons?",
             f"{a}/{b} = {target_a}/x", str(b * mult)),
        ]
        ctx, proportion, ans = rng.choice(contexts)
        prompt = f"{ctx} Write the proportion and solve."
        answer = ans
        hints = (
            "Set up equal ratios with the unknown on one side.",
            f"The proportion is {proportion}.",
        )
        misconceptions = {
            "PROP.CONSTRUCT.WRONG_CORRESPONDENCE": str(a * b),
        }
        return prompt, answer, hints, misconceptions

    # --- solve word ---
    if family_code == "MATH.PROP.SOLVE_WORD":
        rate_n = rng.randint(2, 6 + difficulty)
        rate_d = rng.randint(2, 5)
        while rate_n == rate_d:
            rate_d = rng.randint(2, 5)
        mult = rng.randint(2, 5 + difficulty)
        target_d = rate_d * mult
        answer_val = rate_n * mult
        contexts = [
            (f"A machine makes {rate_n} parts every {rate_d} minutes. "
             f"How many parts does it make in {target_d} minutes?"),
            (f"A recipe serves {rate_n} people and uses {rate_d} cups of rice. "
             f"How many people can you serve with {target_d} cups of rice?"),
        ]
        prompt = rng.choice(contexts)
        answer = str(answer_val)
        hints = (
            f"Set up the proportion: {rate_n}/{rate_d} = ?/{target_d}.",
            f"The multiplier is {mult}.",
        )
        wrong_add = rate_n + (target_d - rate_d)
        misconceptions = {
            "PROP.SOLVE.ADDITIVE": str(wrong_add),
            "PROP.SOLVE.ONLY_ONE_SIDE": str(rate_n),
        }
        return prompt, answer, hints, misconceptions

    # --- non-proportional ---
    if family_code == "MATH.PROP.NONPROPORTIONAL":
        k = rng.randint(2, 5 + difficulty)
        offset = rng.randint(1, 4 + difficulty)
        xs = sorted({rng.randint(1, 5 + difficulty) for _ in range(5)})
        while len(xs) < 3:
            xs.append(xs[-1] + 1)
        pairs = [(x, k * x + offset) for x in xs[:4]]
        table_str = " | ".join(f"({x}, {y})" for x, y in pairs)
        prompt = (
            f"A table shows: {table_str}. "
            "Jamie says this is proportional because the difference between "
            "consecutive y-values is constant. Is Jamie correct?"
        )
        answer = (
            f"No. A constant difference means linear, not proportional. "
            f"y/x is not constant: {pairs[0][1]}/{pairs[0][0]} ≠ {pairs[1][1]}/{pairs[1][0]}."
        )
        hints = (
            "Proportional means y/x is the same for every row, not just that y increases at a constant rate.",
            "Check: does dividing y by x give the same result each time?",
        )
        misconceptions = {
            "PROP.NONPROP.CONSTANT_DIFF_IS_PROP": "Yes, it is proportional.",
        }
        return prompt, answer, hints, misconceptions

    # --- multi-step ---
    if family_code == "MATH.PROP.MULTISTEP":
        price_per = rng.randint(2, 5 + difficulty)
        qty = rng.randint(3, 8 + difficulty)
        tax_pct = rng.choice([5, 8, 10])
        subtotal = price_per * qty
        tax = subtotal * tax_pct // 100
        total = subtotal + tax
        prompt = (
            f"Pens cost ${price_per} each. You buy {qty} pens and pay {tax_pct}% sales tax. "
            "What is the total cost?"
        )
        answer = f"${total}"
        hints = (
            f"First find the subtotal: {price_per} × {qty}.",
            f"Then calculate {tax_pct}% of the subtotal and add it.",
            f"${subtotal} + ${tax} = ${total}.",
        )
        misconceptions = {
            "PROP.MULTI.TAX_ON_ONE": f"${price_per + price_per * tax_pct // 100}",
            "PROP.MULTI.FORGET_TAX": f"${subtotal}",
        }
        return prompt, answer, hints, misconceptions

    # --- why cross multiply ---
    if family_code == "MATH.PROP.CROSS_MULTIPLY.WHY":
        a = rng.randint(2, 5)
        b = rng.randint(2, 5)
        c = rng.randint(2, 5)
        d = rng.randint(2, 5)
        while a * d != b * c:
            d = rng.randint(2, 5)
            c = rng.randint(2, 5)
        prompt = (
            f"Explain why cross-multiplying works to solve {a}/{b} = {c}/{d}. "
            "What mathematical property justifies this step?"
        )
        answer = (
            f"Multiplying both sides of {a}/{b} = {c}/{d} by {b}×{d} eliminates "
            f"both denominators, giving {a}×{d} = {b}×{c}. This is the multiplication "
            "property of equality applied to clear fractions."
        )
        hints = (
            "Think about what happens when you multiply both sides by the LCD.",
            f"If {a}/{b} = {c}/{d}, multiplying both sides by {b}·{d} gives {a}·{d} = {b}·{c}.",
        )
        misconceptions = {
            "PROP.CROSS.JUST_A_RULE": "It works because you multiply diagonally.",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"Unknown proportion family: {family_code}")
