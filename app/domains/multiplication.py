"""Canonical multiplication problem families.

Covers: multiplication facts, missing factors, multi-digit multiplication,
estimation, properties, distributive property, area models, word problems
(equal groups, arrays, comparison, scaling, multi-step), and error analysis.
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
    """Format an integer with commas for readability."""
    return f"{n:,}"


_NAMES = ["Emma", "Liam", "Aisha", "Carlos", "Mei", "Sofia", "Noah", "Zoe"]
_GROUP_ITEMS = [
    ("bags", "marbles", "marbles"),
    ("boxes", "crayons", "crayons"),
    ("baskets", "apples", "apples"),
    ("pages", "stickers", "stickers"),
    ("packs", "juice boxes", "juice boxes"),
    ("shelves", "books", "books"),
]
_ARRAY_ITEMS = ["chairs", "desks", "tiles", "seats", "plants", "windows"]
_UNITS = ["square units", "square feet", "square meters", "square inches"]


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    # --- Facts & fluency ---
    "MATH.MUL.FACTS": ProblemFamilySpec(
        "MATH.MUL.FACTS", "Recall a multiplication fact",
        "MATH.NS.MULTIPLICATION", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.MUL.MISSING_FACTOR": ProblemFamilySpec(
        "MATH.MUL.MISSING_FACTOR", "Find the missing factor",
        "MATH.NS.MULTIPLICATION", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "reasoning"}),
    ),
    "MATH.MUL.MULTIDIGIT": ProblemFamilySpec(
        "MATH.MUL.MULTIDIGIT", "Multiply multi-digit numbers",
        "MATH.NS.MULTIPLICATION", "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    # --- Estimation ---
    "MATH.MUL.ESTIMATE": ProblemFamilySpec(
        "MATH.MUL.ESTIMATE", "Estimate a product by rounding",
        "MATH.NS.MULTIPLICATION", "ESTIMATION", 2, 4, ALL_MODES,
        frozenset({"estimation", "number_sense"}),
    ),
    # --- Properties & reasoning ---
    "MATH.MUL.PROPERTIES": ProblemFamilySpec(
        "MATH.MUL.PROPERTIES", "Identify a multiplication property",
        "MATH.NS.MULTIPLICATION", "REASONING", 2, 3, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
    "MATH.MUL.DISTRIBUTIVE": ProblemFamilySpec(
        "MATH.MUL.DISTRIBUTIVE", "Use the distributive property to multiply",
        "MATH.NS.MULTIPLICATION", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding", "procedural_fluency"}),
    ),
    # --- Area model ---
    "MATH.MUL.AREA": ProblemFamilySpec(
        "MATH.MUL.AREA", "Find the area of a rectangle",
        "MATH.NS.MULTIPLICATION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "representation", "procedural_fluency"}),
    ),
    # --- Word problems ---
    "MATH.MUL.WORD.EQUAL_GROUPS": ProblemFamilySpec(
        "MATH.MUL.WORD.EQUAL_GROUPS", "Word problem: equal groups",
        "MATH.NS.MULTIPLICATION", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.MUL.WORD.ARRAY": ProblemFamilySpec(
        "MATH.MUL.WORD.ARRAY", "Word problem: array arrangement",
        "MATH.NS.MULTIPLICATION", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "representation", "transfer"}),
    ),
    "MATH.MUL.WORD.COMPARE": ProblemFamilySpec(
        "MATH.MUL.WORD.COMPARE", "Word problem: multiplicative comparison",
        "MATH.NS.MULTIPLICATION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "comparison", "transfer"}),
    ),
    "MATH.MUL.WORD.SCALING": ProblemFamilySpec(
        "MATH.MUL.WORD.SCALING", "Word problem: scale a recipe",
        "MATH.NS.MULTIPLICATION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "reasoning"}),
    ),
    "MATH.MUL.WORD.MULTISTEP": ProblemFamilySpec(
        "MATH.MUL.WORD.MULTISTEP", "Word problem: multi-step multiplication",
        "MATH.NS.MULTIPLICATION", "WORD_PROBLEM", 3, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    # --- Error analysis ---
    "MATH.MUL.ERROR.ADDITIVE": ProblemFamilySpec(
        "MATH.MUL.ERROR.ADDITIVE",
        "Error analysis: additive vs multiplicative reasoning",
        "MATH.NS.MULTIPLICATION", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _fact_range(difficulty: int) -> tuple[int, int]:
    """Return (lo, hi) factor range scaled by difficulty."""
    if difficulty <= 1:
        return 2, 10
    if difficulty == 2:
        return 2, 12
    return 4, 12


def build(family_code: str, rng: random.Random, difficulty: int):
    """Return (prompt, answer, hints, misconceptions) for *family_code*."""

    # --- multiplication facts ---
    if family_code == "MATH.MUL.FACTS":
        lo, hi = _fact_range(difficulty)
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        prompt = f"What is {a} × {b}?"
        answer = str(a * b)
        hints = (
            f"Think of {a} × {b} as {a} groups of {b}.",
            f"You can count by {a}s: {a}, {2 * a}, {3 * a}, ...",
            f"{b} groups of {a} gives {a * b}.",
        )
        misconceptions = {
            "MUL.FACTS.ADD_INSTEAD": str(a + b),
        }
        return prompt, answer, hints, misconceptions

    # --- missing factor ---
    if family_code == "MATH.MUL.MISSING_FACTOR":
        lo, hi = _fact_range(difficulty)
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        p = a * b
        prompt = f"What number makes this true? ? × {b} = {p}"
        answer = str(a)
        hints = (
            f"Ask: how many groups of {b} make {p}?",
            f"You can divide: {p} ÷ {b}.",
            f"{p} ÷ {b} = {a}.",
        )
        misconceptions = {
            "MUL.MISSING.SUBTRACT": str(p - b),
        }
        return prompt, answer, hints, misconceptions

    # --- multi-digit multiplication ---
    if family_code == "MATH.MUL.MULTIDIGIT":
        if difficulty <= 2:
            a = rng.randint(12, 99)
            b = rng.randint(3, 9)
        elif difficulty == 3:
            a = rng.randint(12, 99)
            b = rng.randint(12, 99)
        else:
            a = rng.randint(101, 999)
            b = rng.randint(12, 99)
        product = a * b
        prompt = f"Multiply {_comma(a)} × {_comma(b)}."
        answer = _comma(product)
        hints = (
            "Break the problem into partial products by place value.",
            f"Multiply each part of {_comma(a)} by {_comma(b)}, then add.",
            f"The product is {_comma(product)}.",
        )
        # Misconception: omit one partial product.
        # e.g. 23 × 14 -> (23 × 10) only, or (a × tens of b) + (a × ones of b
        # but missing cross term for 2-digit × 2-digit).
        if b >= 10:
            tens_b = (b // 10) * 10
            ones_b = b % 10
            wrong = a * tens_b if ones_b else a * (b // 10)
        else:
            tens_a = (a // 10) * 10
            wrong = tens_a * b
        misconceptions = {
            "MUL.MULTIDIGIT.PARTIAL_PRODUCT_OMIT": _comma(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- estimate a product ---
    if family_code == "MATH.MUL.ESTIMATE":
        a = rng.randint(12, 9 + 10 ** difficulty)
        b = rng.randint(12, 99) if difficulty <= 3 else rng.randint(12, 999)
        # Round each factor to its leading place.
        def _round(x: int) -> int:
            s = str(x)
            place = 10 ** (len(s) - 1)
            return round(x / place) * place

        ra, rb = _round(a), _round(b)
        estimate = ra * rb
        exact = a * b
        distractor1 = exact + rng.randint(1, max(a, b)) * 10
        distractor2 = max(estimate // 10, 1)
        prompt = (
            f"Which is the best estimate for {_comma(a)} × {_comma(b)}? "
            f"(A) {_comma(estimate)} "
            f"(B) {_comma(exact)} "
            f"(C) {_comma(distractor1)} "
            f"(D) {_comma(distractor2)}"
        )
        answer = "A"
        hints = (
            "Round each factor to its greatest place value first.",
            f"{_comma(a)} rounds to {_comma(ra)} and {_comma(b)} rounds to {_comma(rb)}.",
            f"{_comma(ra)} × {_comma(rb)} = {_comma(estimate)}.",
        )
        misconceptions = {
            "MUL.ESTIMATE.WRONG_CHOICE": rng.choice(["B", "C", "D"]),
        }
        return prompt, answer, hints, misconceptions

    # --- multiplication properties ---
    if family_code == "MATH.MUL.PROPERTIES":
        prop = rng.choice(["commutative", "associative", "zero"])
        if prop == "commutative":
            a = rng.randint(3, 12)
            b = rng.randint(3, 12)
            while a == b:
                b = rng.randint(3, 12)
            prompt = (
                f"Which equation shows the commutative property of multiplication? "
                f"(A) {a} × {b} = {b} × {a} "
                f"(B) ({a} × {b}) × 2 = {a} × ({b} × 2) "
                f"(C) {a} × 0 = 0 "
                f"(D) {a} + {b} = {b} + {a}"
            )
            answer = "A"
            hints = (
                "The commutative property lets you swap the order of factors.",
                "Only one choice swaps the factors in a multiplication.",
            )
            misconceptions = {
                "MUL.PROP.ADDITIVE_CONFUSION": "D",
            }
        elif prop == "associative":
            a = rng.randint(2, 9)
            b = rng.randint(2, 9)
            c = rng.randint(2, 9)
            prompt = (
                f"Which equation shows the associative property of multiplication? "
                f"(A) ({a} × {b}) × {c} = {a} × ({b} × {c}) "
                f"(B) {a} × {b} = {b} × {a} "
                f"(C) {a} × ({b} + {c}) = {a} × {b} + {a} × {c} "
                f"(D) {a} × 1 = {a}"
            )
            answer = "A"
            hints = (
                "The associative property lets you regroup the factors.",
                "Look for the choice where only the grouping changes.",
            )
            misconceptions = {
                "MUL.PROP.DISTRIBUTIVE_CONFUSION": "C",
            }
        else:
            a = rng.randint(3, 99)
            prompt = (
                f"What is {a} × 0? "
                f"(A) {a} "
                f"(B) 0 "
                f"(C) 1 "
                f"(D) {a} + 0"
            )
            answer = "B"
            hints = (
                "The zero property says any number times zero is zero.",
                f"{a} × 0 means zero groups of {a}.",
            )
            misconceptions = {
                "MUL.PROP.ZERO_KEEP_NUMBER": "A",
            }
        return prompt, answer, hints, misconceptions

    # --- distributive property ---
    if family_code == "MATH.MUL.DISTRIBUTIVE":
        b = rng.randint(3, 9)
        if difficulty <= 2:
            tens = rng.choice([10, 20])
            ones = rng.randint(2, 9)
        elif difficulty == 3:
            tens = rng.choice([10, 20, 30, 40])
            ones = rng.randint(2, 9)
        else:
            tens = rng.choice([10, 20, 30, 40, 50])
            ones = rng.randint(2, 9)
            b = rng.randint(6, 15)
        a = tens + ones
        prompt = (
            f"Which rewrite makes {a} × {b} easier to solve? "
            f"(A) ({tens} × {b}) + ({ones} × {b}) "
            f"(B) ({a} × {b}) + ({a} × {b}) "
            f"(C) ({tens} + {b}) × ({ones} + {b}) "
            f"(D) {a} + {b}"
        )
        answer = "A"
        hints = (
            f"Break {a} into {tens} + {ones}.",
            f"Multiply each part by {b}, then add the partial products.",
            f"({tens} × {b}) + ({ones} × {b}) = {tens * b} + {ones * b} = {a * b}.",
        )
        misconceptions = {
            "MUL.DISTRIBUTIVE.ADD_FACTORS": "D",
        }
        return prompt, answer, hints, misconceptions

    # --- area model ---
    if family_code == "MATH.MUL.AREA":
        if difficulty <= 2:
            length = rng.randint(3, 12)
            width = rng.randint(2, 9)
        elif difficulty == 3:
            length = rng.randint(12, 30)
            width = rng.randint(3, 12)
        else:
            length = rng.randint(15, 99)
            width = rng.randint(12, 30)
        unit = rng.choice(_UNITS)
        area = length * width
        prompt = (
            f"A rectangle is {length} units long and {width} units wide. "
            f"What is its area?"
        )
        answer = f"{_comma(area)} {unit}"
        hints = (
            "Area of a rectangle = length × width.",
            f"Multiply {length} × {width}.",
            f"The area is {_comma(area)} {unit}.",
        )
        misconceptions = {
            "MUL.AREA.PERIMETER": f"{_comma(2 * length + 2 * width)} {unit}",
        }
        return prompt, answer, hints, misconceptions

    # --- word: equal groups ---
    if family_code == "MATH.MUL.WORD.EQUAL_GROUPS":
        lo, hi = _fact_range(difficulty)
        x = rng.randint(lo, hi)
        y = rng.randint(lo, hi)
        container, item, plural = rng.choice(_GROUP_ITEMS)
        name = rng.choice(_NAMES)
        prompt = (
            f"{name} has {x} {container} with {y} {item} in each. "
            f"How many {plural} does {name} have in all?"
        )
        answer = str(x * y)
        hints = (
            f"There are {x} equal groups of {y}.",
            f"Multiply {x} × {y}.",
            f"{x} × {y} = {x * y}.",
        )
        misconceptions = {
            "MUL.WORD.ADD_INSTEAD": str(x + y),
        }
        return prompt, answer, hints, misconceptions

    # --- word: array ---
    if family_code == "MATH.MUL.WORD.ARRAY":
        lo, hi = _fact_range(difficulty)
        r = rng.randint(lo, hi)
        c = rng.randint(lo, hi)
        item = rng.choice(_ARRAY_ITEMS)
        prompt = (
            f"The hall has {r} rows of {item} with {c} {item} in each row. "
            f"How many {item} are there in all?"
        )
        answer = str(r * c)
        hints = (
            f"An array has {r} rows and {c} columns.",
            f"Multiply {r} × {c}.",
            f"{r} × {c} = {r * c}.",
        )
        misconceptions = {
            "MUL.ARRAY.ADD_INSTEAD": str(r + c),
        }
        return prompt, answer, hints, misconceptions

    # --- word: multiplicative comparison ---
    if family_code == "MATH.MUL.WORD.COMPARE":
        x = rng.randint(2, 4 + difficulty * 2)
        y = rng.randint(3, 9 + difficulty * 3)
        name1, name2 = rng.sample(_NAMES, 2)
        item = rng.choice(["stickers", "points", "coins", "cards", "shells"])
        prompt = (
            f"{name1} has {x} times as many {item} as {name2}. "
            f"{name2} has {y} {item}. "
            f"How many {item} does {name1} have?"
        )
        answer = str(x * y)
        hints = (
            f"“{x} times as many” means multiply.",
            f"Multiply {x} × {y}.",
            f"{x} × {y} = {x * y}.",
        )
        misconceptions = {
            "MUL.COMPARE.ADD": str(x + y),
        }
        return prompt, answer, hints, misconceptions

    # --- word: scaling ---
    if family_code == "MATH.MUL.WORD.SCALING":
        serves = rng.choice([2, 3, 4, 5, 6])
        multiplier = rng.randint(2, 4 + difficulty)
        target = serves * multiplier
        cups = rng.randint(2, 6)
        food = rng.choice(["recipe", "batch of cookies", "soup pot", "punch bowl"])
        prompt = (
            f"A {food} serves {serves} people and uses {cups} cups of flour. "
            f"How many cups of flour are needed to serve {target} people?"
        )
        answer = str(cups * multiplier)
        hints = (
            f"Find the scale factor: {target} ÷ {serves} = {multiplier}.",
            f"Multiply the flour by the scale factor: {cups} × {multiplier}.",
            f"{cups} × {multiplier} = {cups * multiplier} cups.",
        )
        misconceptions = {
            "MUL.SCALING.ADD_DIFF": str(cups + (target - serves)),
        }
        return prompt, answer, hints, misconceptions

    # --- word: multi-step ---
    if family_code == "MATH.MUL.WORD.MULTISTEP":
        packs = rng.randint(3, 9)
        per_pack = rng.randint(4, 12)
        extra = rng.randint(2, 15)
        item = rng.choice(["pencils", "stickers", "cards", "beads"])
        name = rng.choice(_NAMES)
        if difficulty <= 3:
            prompt = (
                f"{name} buys {packs} packs of {item} with {per_pack} {item} "
                f"in each pack. Then {name} gets {extra} more {item}. "
                f"How many {item} does {name} have now?"
            )
            answer = str(packs * per_pack + extra)
            hints = (
                f"First multiply: {packs} × {per_pack}.",
                f"Then add the extra {extra}.",
                f"{packs} × {per_pack} + {extra} = {packs * per_pack + extra}.",
            )
            misconceptions = {
                "MUL.MULTISTEP.FORGOT_ADD": str(packs * per_pack),
            }
        else:
            distractor = rng.randint(2, 10)
            prompt = (
                f"{name} buys {packs} packs of {item} with {per_pack} {item} "
                f"in each pack for a class of {distractor} students. "
                f"Then {name} gets {extra} more {item}. "
                f"How many {item} does {name} have now?"
            )
            answer = str(packs * per_pack + extra)
            hints = (
                "Not every number in the problem is needed.",
                f"Multiply {packs} × {per_pack}, then add {extra}.",
                f"{packs} × {per_pack} + {extra} = {packs * per_pack + extra}.",
            )
            misconceptions = {
                "MUL.MULTISTEP.USE_DISTRACTOR": str(packs * per_pack + distractor),
            }
        return prompt, answer, hints, misconceptions

    # --- error analysis: additive vs multiplicative ---
    if family_code == "MATH.MUL.ERROR.ADDITIVE":
        x = rng.randint(2, 5 + difficulty)
        y = rng.randint(4, 9 + difficulty * 3)
        name1, name2 = rng.sample(_NAMES, 2)
        item = rng.choice(["stickers", "points", "coins", "books", "laps"])
        wrong = x + y
        prompt = (
            f"{name1} has {x} times as many {item} as {name2}. "
            f"{name2} has {y} {item}. "
            f"A student says {name1} has {wrong} {item} because {x} + {y} = {wrong}. "
            f"What did the student do wrong? "
            f"(A) The student added instead of multiplying — "
            f"{name1} has {x} × {y} = {x * y} {item}. "
            f"(B) Nothing is wrong — the answer is {wrong}. "
            f"(C) The student should have subtracted — {name1} has {y - x} {item}. "
            f"(D) The student should have divided — {name1} has {y // max(x, 1)} {item}."
        )
        answer = "A"
        hints = (
            "“Times as many” is a multiplicative comparison.",
            f"Correct answer is {x} × {y} = {x * y}, not {x} + {y}.",
        )
        misconceptions = {
            "MUL.ERROR.ADDITIVE_REASONING": "B",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")
