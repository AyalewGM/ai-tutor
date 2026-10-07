"""Canonical order-of-operations problem families.

Covers: parentheses, multiplication/division before addition/subtraction,
left-to-right evaluation, multi-operation expressions, grouping
interpretation, error analysis, missing operation.

Explicitly tests the misconception that multiplication ALWAYS comes before
division (rather than left-to-right at equal precedence), and similarly
for addition/subtraction.
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


def _eval_expr(tokens: list) -> int:
    """Evaluate a flat list of [val, op, val, op, val, ...] respecting PEMDAS.

    Handles: +, -, *, //.  No parentheses here (caller resolves those).
    """
    # First pass: * and // (left to right)
    vals: list[int] = [tokens[0]]
    ops: list[str] = []
    i = 1
    while i < len(tokens):
        op = tokens[i]
        right = tokens[i + 1]
        if op in ("*", "//"):
            if op == "*":
                vals[-1] = vals[-1] * right
            else:
                vals[-1] = vals[-1] // right
        else:
            vals.append(right)
            ops.append(op)
        i += 2
    # Second pass: + and - (left to right)
    result = vals[0]
    for j, op in enumerate(ops):
        if op == "+":
            result += vals[j + 1]
        else:
            result -= vals[j + 1]
    return result


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.OOO.BASIC": ProblemFamilySpec(
        "MATH.OOO.BASIC", "Evaluate expression with mixed operations",
        "MATH.NS.ORDER_OF_OPERATIONS", "NUMBER_SENSE", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.OOO.PARENS": ProblemFamilySpec(
        "MATH.OOO.PARENS", "Evaluate expression with parentheses",
        "MATH.NS.ORDER_OF_OPERATIONS", "NUMBER_SENSE", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.OOO.LEFT_RIGHT": ProblemFamilySpec(
        "MATH.OOO.LEFT_RIGHT", "Equal-precedence left-to-right evaluation",
        "MATH.NS.ORDER_OF_OPERATIONS", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "misconception_probe", "procedural_fluency"}),
    ),
    "MATH.OOO.MULTI_OP": ProblemFamilySpec(
        "MATH.OOO.MULTI_OP", "Evaluate multi-operation expression",
        "MATH.NS.ORDER_OF_OPERATIONS", "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "reasoning"}),
    ),
    "MATH.OOO.INSERT_PARENS": ProblemFamilySpec(
        "MATH.OOO.INSERT_PARENS", "Insert parentheses to make equation true",
        "MATH.NS.ORDER_OF_OPERATIONS", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
    "MATH.OOO.ERROR.LEFT_RIGHT": ProblemFamilySpec(
        "MATH.OOO.ERROR.LEFT_RIGHT", "Error analysis: wrong left-to-right rule",
        "MATH.NS.ORDER_OF_OPERATIONS", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
    "MATH.OOO.ERROR.IGNORE_PARENS": ProblemFamilySpec(
        "MATH.OOO.ERROR.IGNORE_PARENS", "Error analysis: ignoring parentheses",
        "MATH.NS.ORDER_OF_OPERATIONS", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):

    # --- basic mixed operations ---
    if family_code == "MATH.OOO.BASIC":
        a = rng.randint(2, 5 + difficulty * 3)
        b = rng.randint(2, 5 + difficulty * 2)
        c = rng.randint(1, 4 + difficulty * 2)
        # a + b × c
        correct = a + b * c
        left_to_right = (a + b) * c  # common mistake
        prompt = f"Evaluate: {a} + {b} × {c}"
        answer = str(correct)
        hints = (
            "Remember: multiplication comes before addition.",
            f"First compute {b} × {c} = {b * c}.",
            f"Then add {a}: {a} + {b * c} = {correct}.",
        )
        misconceptions = {
            "OOO.BASIC.LEFT_TO_RIGHT": str(left_to_right),
        }
        return prompt, answer, hints, misconceptions

    # --- parentheses ---
    if family_code == "MATH.OOO.PARENS":
        a = rng.randint(2, 6 + difficulty * 2)
        b = rng.randint(1, 5 + difficulty)
        c = rng.randint(2, 4 + difficulty)
        # (a + b) × c
        correct = (a + b) * c
        no_parens = a + b * c  # mistake: ignore parens
        prompt = f"Evaluate: ({a} + {b}) × {c}"
        answer = str(correct)
        hints = (
            "Always evaluate what is inside parentheses first.",
            f"({a} + {b}) = {a + b}.",
            f"Then multiply: {a + b} × {c} = {correct}.",
        )
        misconceptions = {
            "OOO.PARENS.IGNORE": str(no_parens),
        }
        return prompt, answer, hints, misconceptions

    # --- equal-precedence left-to-right ---
    if family_code == "MATH.OOO.LEFT_RIGHT":
        # Test that × and ÷ are left-to-right, NOT × always first
        a = rng.randint(2, 4 + difficulty) * rng.randint(2, 4 + difficulty)
        divisor = rng.randint(2, 4 + difficulty)
        while a % divisor != 0:
            a = rng.randint(2, 4 + difficulty) * rng.randint(2, 4 + difficulty)
            divisor = rng.randint(2, 4 + difficulty)
            while a % divisor != 0:
                divisor = rng.randint(2, min(a, 4 + difficulty))
        c = rng.randint(2, 4 + difficulty)
        # a ÷ divisor × c  (left-to-right)
        correct = (a // divisor) * c
        # Mistake: do × first
        mul_first = a // (divisor * c) if divisor * c != 0 and a % (divisor * c) == 0 else correct + 1
        prompt = f"Evaluate: {a} ÷ {divisor} × {c}"
        answer = str(correct)
        hints = (
            "Multiplication and division have equal precedence.",
            "Evaluate left to right.",
            f"First: {a} ÷ {divisor} = {a // divisor}. Then × {c} = {correct}.",
        )
        misconceptions = {
            "OOO.LR.MUL_FIRST": str(mul_first),
        }
        return prompt, answer, hints, misconceptions

    # --- multi-operation expression ---
    if family_code == "MATH.OOO.MULTI_OP":
        a = rng.randint(2, 5 + difficulty)
        b = rng.randint(2, 4 + difficulty)
        c = rng.randint(1, 4 + difficulty)
        d = rng.randint(1, 3 + difficulty)
        # a × b + c - d
        correct = a * b + c - d
        prompt = f"Evaluate: {a} × {b} + {c} − {d}"
        answer = str(correct)
        hints = (
            "Do multiplication first, then addition and subtraction left to right.",
            f"{a} × {b} = {a * b}. Then {a * b} + {c} - {d}.",
        )
        wrong = a * (b + c) - d
        misconceptions = {
            "OOO.MULTI.WRONG_ORDER": str(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- insert parentheses ---
    if family_code == "MATH.OOO.INSERT_PARENS":
        a = rng.randint(2, 5 + difficulty)
        b = rng.randint(1, 4 + difficulty)
        c = rng.randint(2, 4 + difficulty)
        # Without parens: a + b × c
        without = a + b * c
        # With parens around a + b: (a + b) × c
        with_parens = (a + b) * c
        target = with_parens
        prompt = (
            f"Insert one pair of parentheses to make this true: "
            f"{a} + {b} × {c} = {target}"
        )
        answer = f"({a} + {b}) × {c}"
        hints = (
            f"Without parentheses, {a} + {b} × {c} = {without}.",
            "Try grouping the addition first.",
        )
        misconceptions = {
            "OOO.INSERT.NO_CHANGE": f"{a} + {b} × {c}",
        }
        return prompt, answer, hints, misconceptions

    # --- error: wrong left-to-right ---
    if family_code == "MATH.OOO.ERROR.LEFT_RIGHT":
        # Student always does addition before subtraction
        a = rng.randint(10, 20 + difficulty * 10)
        b = rng.randint(1, 5 + difficulty * 2)
        c = rng.randint(1, 5 + difficulty * 2)
        correct = a - b + c
        wrong = a - (b + c)  # student does + first
        names = ["Kai", "Zoe", "Luis", "Nia"]
        name = rng.choice(names)
        prompt = (
            f"{name} evaluates {a} − {b} + {c} as {wrong}. "
            f"What mistake did {name} make? "
            f"(A) Added before subtracting — should evaluate left to right. "
            f"(B) Subtracted before adding — should add first. "
            f"(C) The answer {wrong} is correct."
        )
        answer = "A"
        hints = (
            "Addition and subtraction have equal precedence.",
            "Evaluate left to right: first subtraction, then addition.",
            f"{a} − {b} = {a - b}, then {a - b} + {c} = {correct}.",
        )
        misconceptions = {
            "OOO.ERROR.ADD_FIRST_OK": "B",
            "OOO.ERROR.AGREES": "C",
        }
        return prompt, answer, hints, misconceptions

    # --- error: ignoring parentheses ---
    if family_code == "MATH.OOO.ERROR.IGNORE_PARENS":
        a = rng.randint(2, 6 + difficulty)
        b = rng.randint(1, 5 + difficulty)
        c = rng.randint(2, 4 + difficulty)
        correct = (a + b) * c
        wrong = a + b * c  # ignored parens
        names = ["Sam", "Mia", "Dev", "Ava"]
        name = rng.choice(names)
        prompt = (
            f"{name} says ({a} + {b}) × {c} = {wrong}. "
            f"What mistake did {name} make? "
            f"(A) Ignored the parentheses and multiplied {b} × {c} first. "
            f"(B) Added instead of multiplied. "
            f"(C) The answer {wrong} is correct."
        )
        answer = "A"
        hints = (
            "Parentheses must be evaluated first.",
            f"({a} + {b}) = {a + b}. Then {a + b} × {c} = {correct}.",
        )
        misconceptions = {
            "OOO.ERROR.AGREES_WRONG": "C",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")
