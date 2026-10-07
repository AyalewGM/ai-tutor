"""Canonical mathematical-properties problem families.

Covers: commutative property, associative property, identity property,
distributive property, zero property of multiplication.

Assessment is structured (MC/classification) — not prose reproduction.
"""

from __future__ import annotations

import random

from app.canonical_problem_families import (
    ALL_MODES,
    ProblemFamilySpec,
)

# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.PROP_MATH.COMMUTATIVE": ProblemFamilySpec(
        "MATH.PROP_MATH.COMMUTATIVE", "Identify the commutative property",
        "MATH.NS.PROPERTIES", "REASONING", 1, 3, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
    "MATH.PROP_MATH.ASSOCIATIVE": ProblemFamilySpec(
        "MATH.PROP_MATH.ASSOCIATIVE", "Identify the associative property",
        "MATH.NS.PROPERTIES", "REASONING", 2, 3, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
    "MATH.PROP_MATH.IDENTITY": ProblemFamilySpec(
        "MATH.PROP_MATH.IDENTITY", "Identify the identity property",
        "MATH.NS.PROPERTIES", "REASONING", 1, 3, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding", "number_sense"}),
    ),
    "MATH.PROP_MATH.DISTRIBUTIVE": ProblemFamilySpec(
        "MATH.PROP_MATH.DISTRIBUTIVE", "Apply the distributive property",
        "MATH.NS.PROPERTIES", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding", "procedural_fluency"}),
    ),
    "MATH.PROP_MATH.ZERO": ProblemFamilySpec(
        "MATH.PROP_MATH.ZERO", "Zero property of multiplication",
        "MATH.NS.PROPERTIES", "REASONING", 1, 2, ALL_MODES,
        frozenset({"conceptual_understanding", "number_sense"}),
    ),
    "MATH.PROP_MATH.IDENTIFY_NAME": ProblemFamilySpec(
        "MATH.PROP_MATH.IDENTIFY_NAME", "Name the property shown",
        "MATH.NS.PROPERTIES", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
    "MATH.PROP_MATH.APPLY": ProblemFamilySpec(
        "MATH.PROP_MATH.APPLY", "Use a property to simplify computation",
        "MATH.NS.PROPERTIES", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "procedural_fluency", "transfer"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):

    # --- commutative ---
    if family_code == "MATH.PROP_MATH.COMMUTATIVE":
        op = rng.choice(["addition", "multiplication"])
        a = rng.randint(3, 10 + difficulty * 5)
        b = rng.randint(3, 10 + difficulty * 5)
        while a == b:
            b = rng.randint(3, 10 + difficulty * 5)
        sym = "+" if op == "addition" else "×"
        prompt = (
            f"Which equation shows the commutative property of {op}? "
            f"(A) {a} {sym} {b} = {b} {sym} {a} "
            f"(B) {a} {sym} {b} = {a} {sym} {b} "
            f"(C) {a} {sym} 0 = {a} "
            f"(D) {a} {sym} {b} = {a * b if sym == '×' else a + b}"
        )
        answer = "A"
        hints = (
            "The commutative property says you can switch the order of the numbers.",
            f"For {op}: a {sym} b = b {sym} a.",
        )
        misconceptions = {
            "PROP.COMM.IDENTITY": "C",
            "PROP.COMM.JUST_COMPUTE": "D",
        }
        return prompt, answer, hints, misconceptions

    # --- associative ---
    if family_code == "MATH.PROP_MATH.ASSOCIATIVE":
        op = rng.choice(["addition", "multiplication"])
        a = rng.randint(2, 8 + difficulty * 3)
        b = rng.randint(2, 8 + difficulty * 3)
        c = rng.randint(2, 8 + difficulty * 3)
        sym = "+" if op == "addition" else "×"
        prompt = (
            f"Which equation shows the associative property of {op}? "
            f"(A) ({a} {sym} {b}) {sym} {c} = {a} {sym} ({b} {sym} {c}) "
            f"(B) {a} {sym} {b} = {b} {sym} {a} "
            f"(C) {a} {sym} 1 = {a} "
            f"(D) {a} {sym} 0 = {a if sym == '+' else 0}"
        )
        answer = "A"
        hints = (
            "The associative property says you can change the grouping.",
            f"({a} {sym} {b}) {sym} {c} = {a} {sym} ({b} {sym} {c}).",
        )
        misconceptions = {
            "PROP.ASSOC.COMMUTATIVE": "B",
        }
        return prompt, answer, hints, misconceptions

    # --- identity ---
    if family_code == "MATH.PROP_MATH.IDENTITY":
        op = rng.choice(["addition", "multiplication"])
        a = rng.randint(2, 20 + difficulty * 10)
        if op == "addition":
            identity_val = 0
            sym = "+"
        else:
            identity_val = 1
            sym = "×"
        prompt = (
            f"What is {a} {sym} {identity_val}?"
        )
        answer = str(a)
        hints = (
            f"The identity element for {op} is {identity_val}.",
            f"Any number {sym} {identity_val} equals itself.",
        )
        wrong = identity_val if op == "addition" else 0
        misconceptions = {
            "PROP.IDENTITY.ZERO_RESULT": str(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- distributive ---
    if family_code == "MATH.PROP_MATH.DISTRIBUTIVE":
        a = rng.randint(2, 5 + difficulty * 2)
        b = rng.randint(10, 20 + difficulty * 5)
        c = rng.randint(1, 9)
        # a × (b + c) or a × (b - c)
        use_sub = rng.random() < 0.3 and difficulty >= 3
        if use_sub:
            total = b - c
            expr = f"{a} × ({b} − {c})"
            expanded = f"{a} × {b} − {a} × {c}"
            result = a * b - a * c
        else:
            total = b + c
            expr = f"{a} × ({b} + {c})"
            expanded = f"{a} × {b} + {a} × {c}"
            result = a * b + a * c
        prompt = (
            f"Use the distributive property to rewrite {expr}, then compute. "
            f"(A) {expanded} = {result} "
            f"(B) {a} × {b + c if not use_sub else b - c} = {a * total} "
            f"(C) ({a} + {b}) × {c} = {(a + b) * c}"
        )
        answer = "A"
        hints = (
            f"Distribute {a} to each term inside the parentheses.",
            f"{expr} = {expanded}.",
            f"Compute: {a * b} {'−' if use_sub else '+'} {a * c} = {result}.",
        )
        misconceptions = {
            "PROP.DIST.JUST_COMPUTE": "B",
        }
        return prompt, answer, hints, misconceptions

    # --- zero property ---
    if family_code == "MATH.PROP_MATH.ZERO":
        a = rng.randint(2, 50 + difficulty * 50)
        prompt = f"What is {a} × 0?"
        answer = "0"
        hints = (
            "Any number multiplied by zero is zero.",
            "This is called the zero property of multiplication.",
        )
        misconceptions = {
            "PROP.ZERO.IDENTITY_CONFUSION": str(a),
        }
        return prompt, answer, hints, misconceptions

    # --- name the property ---
    if family_code == "MATH.PROP_MATH.IDENTIFY_NAME":
        properties = [
            ("commutative", lambda a, b, c: f"{a} + {b} = {b} + {a}"),
            ("commutative", lambda a, b, c: f"{a} × {b} = {b} × {a}"),
            ("associative", lambda a, b, c: f"({a} + {b}) + {c} = {a} + ({b} + {c})"),
            ("associative", lambda a, b, c: f"({a} × {b}) × {c} = {a} × ({b} × {c})"),
            ("identity", lambda a, b, c: f"{a} + 0 = {a}"),
            ("identity", lambda a, b, c: f"{a} × 1 = {a}"),
            ("distributive", lambda a, b, c: f"{a} × ({b} + {c}) = {a} × {b} + {a} × {c}"),
            ("zero", lambda a, b, c: f"{a} × 0 = 0"),
        ]
        name, expr_fn = rng.choice(properties[:4 + min(difficulty, 4)])
        a = rng.randint(2, 10 + difficulty * 3)
        b = rng.randint(2, 10 + difficulty * 3)
        c = rng.randint(2, 10 + difficulty * 3)
        expr = expr_fn(a, b, c)
        options = ["Commutative", "Associative", "Identity", "Distributive"]
        correct_label = name.capitalize()
        # Shuffle but track correct index
        wrong_options = [o for o in options if o.lower() != name]
        rng.shuffle(wrong_options)
        mc_options = [correct_label] + wrong_options[:3]
        rng.shuffle(mc_options)
        correct_idx = mc_options.index(correct_label)
        letters = ["A", "B", "C", "D"]
        options_str = " ".join(f"({letters[i]}) {mc_options[i]}" for i in range(len(mc_options)))
        prompt = f"Which property does this equation show? {expr} {options_str}"
        answer = letters[correct_idx]
        hints = (
            "Look at what changes (or doesn't change) between the two sides.",
            f"This equation shows the {name} property.",
        )
        wrong_letter = letters[(correct_idx + 1) % len(letters)]
        misconceptions = {
            "PROP.NAME.WRONG": wrong_letter,
        }
        return prompt, answer, hints, misconceptions

    # --- apply property to simplify ---
    if family_code == "MATH.PROP_MATH.APPLY":
        # e.g., "Which rewrite makes 17 × 6 easier to calculate?"
        a = rng.choice([12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 25, 32, 45][:5 + difficulty * 2])
        b = rng.randint(3, 6 + difficulty)
        tens = (a // 10) * 10
        ones = a % 10
        result = a * b
        prompt = (
            f"Which rewrite makes {a} × {b} easier to calculate? "
            f"(A) ({tens} × {b}) + ({ones} × {b}) "
            f"(B) {a} + {b} "
            f"(C) ({a} + {b}) × ({a} − {b}) "
            f"(D) {a} × {b} × 1"
        )
        answer = "A"
        hints = (
            f"Break {a} into {tens} + {ones}.",
            f"Then distribute: {tens} × {b} + {ones} × {b} = {tens * b} + {ones * b} = {result}.",
        )
        misconceptions = {
            "PROP.APPLY.ADD": "B",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")
