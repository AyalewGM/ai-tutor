"""Canonical ratio and rate problem families.

Covers: ratio interpretation, equivalent ratios, ratio tables, unit rates,
rate comparison, scale reasoning, recipe contexts, price/value comparisons,
distance-rate-time, error analysis, and misconception probes.
"""

from __future__ import annotations

import random
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


def _simplify(n: int, d: int) -> tuple[int, int]:
    g = gcd(abs(n), abs(d))
    return n // g, d // g


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.RATIO.INTERPRET": ProblemFamilySpec(
        "MATH.RATIO.INTERPRET", "Interpret a ratio from context",
        "MATH.RP.RATIO.INTERPRET", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"conceptual_understanding", "representation"}),
    ),
    "MATH.RATIO.EQUIVALENT": ProblemFamilySpec(
        "MATH.RATIO.EQUIVALENT", "Find an equivalent ratio",
        "MATH.RP.RATIO.EQUIVALENT", "RATIO", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.RATIO.TABLE.MISSING": ProblemFamilySpec(
        "MATH.RATIO.TABLE.MISSING", "Complete a ratio table",
        "MATH.RP.RATIO.EQUIVALENT", "RATIO_TABLE", 1, 4, ALL_MODES,
        frozenset({"representation", "procedural_fluency", "transfer"}),
    ),
    "MATH.RATIO.PART_WHOLE": ProblemFamilySpec(
        "MATH.RATIO.PART_WHOLE", "Distinguish part-to-part from part-to-whole",
        "MATH.RP.RATIO.INTERPRET", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"conceptual_understanding", "reasoning", "misconception_probe"}),
    ),
    "MATH.RATE.UNIT": ProblemFamilySpec(
        "MATH.RATE.UNIT", "Find a unit rate",
        "MATH.RP.RATE.UNIT", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "modeling"}),
    ),
    "MATH.RATE.COMPARE": ProblemFamilySpec(
        "MATH.RATE.COMPARE", "Compare two rates to find the better value",
        "MATH.RP.RATE.UNIT", "COMPARISON", 2, 4, ALL_MODES,
        frozenset({"comparison", "reasoning", "transfer"}),
    ),
    "MATH.RATE.DRT": ProblemFamilySpec(
        "MATH.RATE.DRT", "Distance-rate-time word problem",
        "MATH.RP.RATE.UNIT", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.RATIO.RECIPE": ProblemFamilySpec(
        "MATH.RATIO.RECIPE", "Scale a recipe using ratio reasoning",
        "MATH.RP.RATIO.EQUIVALENT", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "reasoning"}),
    ),
    "MATH.RATIO.SCALE": ProblemFamilySpec(
        "MATH.RATIO.SCALE", "Map/scale drawing ratio reasoning",
        "MATH.RP.RATIO.EQUIVALENT", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "representation"}),
    ),
    "MATH.RATIO.ERROR.ADDITIVE": ProblemFamilySpec(
        "MATH.RATIO.ERROR.ADDITIVE", "Error analysis: additive vs multiplicative",
        "MATH.RP.RATIO.EQUIVALENT", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):
    """Return (prompt, answer, hints, misconceptions) for *family_code*."""

    # --- interpret ---
    if family_code == "MATH.RATIO.INTERPRET":
        a = rng.randint(2, 5 + difficulty * 2)
        b = rng.randint(2, 5 + difficulty * 2)
        while a == b:
            b = rng.randint(2, 5 + difficulty * 2)
        contexts = [
            (f"In a bag of marbles, there are {a} red and {b} blue marbles.",
             "red to blue", "blue to red"),
            (f"A class has {a} boys and {b} girls.",
             "boys to girls", "girls to boys"),
            (f"A recipe uses {a} cups of flour and {b} cups of sugar.",
             "flour to sugar", "sugar to flour"),
        ]
        ctx, label, _rev_label = rng.choice(contexts)
        prompt = f"{ctx} What is the ratio of {label}?"
        answer = f"{a}:{b}"
        hints = (
            "A ratio compares two quantities in order.",
            f"Count the {label.split(' to ')[0]} and the {label.split(' to ')[1]}.",
        )
        misconceptions = {
            "RATIO.INTERPRET.REVERSED": f"{b}:{a}",
            "RATIO.INTERPRET.TOTAL": f"{a}:{a + b}",
        }
        return prompt, answer, hints, misconceptions

    # --- equivalent ratio ---
    if family_code == "MATH.RATIO.EQUIVALENT":
        a, b = rng.randint(2, 5), rng.randint(2, 5)
        while a == b:
            b = rng.randint(2, 5)
        mult = rng.randint(2, 4 + difficulty)
        prompt = f"Find a ratio equivalent to {a}:{b} with first term {a * mult}."
        answer = f"{a * mult}:{b * mult}"
        hints = (
            f"What was {a} multiplied by to get {a * mult}?",
            f"Multiply both terms by {mult}.",
        )
        misconceptions = {
            "RATIO.EQUIV.ADD_INSTEAD": f"{a * mult}:{b + (a * mult - a)}",
            "RATIO.EQUIV.ONLY_ONE": f"{a * mult}:{b}",
        }
        return prompt, answer, hints, misconceptions

    # --- ratio table missing ---
    if family_code == "MATH.RATIO.TABLE.MISSING":
        a, b = rng.randint(2, 5), rng.randint(2, 5)
        while a == b:
            b = rng.randint(2, 5)
        steps = 3 + difficulty
        mults = list(range(1, steps + 1))
        hide_idx = rng.randint(1, steps - 1)
        hide_col = rng.choice(["a", "b"])
        table_rows = []
        for m in mults:
            va, vb = a * m, b * m
            if m == mults[hide_idx]:
                if hide_col == "a":
                    table_rows.append(f"(?, {vb})")
                    missing_val = va
                else:
                    table_rows.append(f"({va}, ?)")
                    missing_val = vb
            else:
                table_rows.append(f"({va}, {vb})")
        table_str = " | ".join(table_rows)
        prompt = f"Complete the ratio table: {table_str}. What is the missing value?"
        answer = str(missing_val)
        hints = (
            "Find the pattern: each row multiplies both terms by the same number.",
            f"The ratio is {a}:{b}. Use it to find the missing entry.",
        )
        additive_wrong = missing_val + a if hide_col == "b" else missing_val + b
        misconceptions = {
            "RATIO.TABLE.ADDITIVE": str(additive_wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- part-to-part vs part-to-whole ---
    if family_code == "MATH.RATIO.PART_WHOLE":
        a = rng.randint(2, 5 + difficulty)
        b = rng.randint(2, 5 + difficulty)
        while a == b:
            b = rng.randint(2, 5 + difficulty)
        total = a + b
        ask_type = rng.choice(["part_to_whole", "part_to_part"])
        color1, color2 = rng.choice([("red", "blue"), ("green", "yellow"), ("striped", "solid")])
        if ask_type == "part_to_whole":
            prompt = (
                f"A bag has {a} {color1} and {b} {color2} beads. "
                f"What is the ratio of {color1} beads to the total number of beads?"
            )
            answer = f"{a}:{total}"
            wrong = f"{a}:{b}"
            misconceptions = {"RATIO.PART.CONFUSE_PART_PART": wrong}
        else:
            prompt = (
                f"A bag has {a} {color1} and {b} {color2} beads. "
                f"What is the ratio of {color1} beads to {color2} beads?"
            )
            answer = f"{a}:{b}"
            wrong = f"{a}:{total}"
            misconceptions = {"RATIO.PART.CONFUSE_PART_WHOLE": wrong}
        hints = (
            "Read carefully: is the ratio comparing a part to the total or a part to another part?",
            f"Count each group. {color1}: {a}, {color2}: {b}, total: {total}.",
        )
        return prompt, answer, hints, misconceptions

    # --- unit rate ---
    if family_code == "MATH.RATE.UNIT":
        rate = rng.randint(2, 8 + difficulty * 3)
        qty = rng.randint(2, 6 + difficulty)
        total = rate * qty
        contexts = [
            (f"A factory produces {total} widgets in {qty} hours.",
             "widgets per hour", "hours per widget"),
            (f"A car travels {total} miles in {qty} hours.",
             "miles per hour", "hours per mile"),
            (f"A store sells {total} apples for ${qty}.",
             "apples per dollar", "dollars per apple"),
        ]
        ctx, unit_label, _rev_label = rng.choice(contexts)
        prompt = f"{ctx} What is the unit rate in {unit_label}?"
        answer = str(rate)
        hints = (
            "A unit rate tells you the amount per one unit.",
            f"Divide {total} by {qty}.",
        )
        misconceptions = {
            "RATE.UNIT.REVERSED": _frac(qty, total) if total != 0 else "0",
            "RATE.UNIT.MULTIPLY": str(total * qty),
        }
        return prompt, answer, hints, misconceptions

    # --- compare rates ---
    if family_code == "MATH.RATE.COMPARE":
        # Construct so that the option with the LOWER rate has the HIGHER total,
        # making the "compare totals" misconception genuinely wrong.
        rate_a = rng.randint(3, 8 + difficulty)
        rate_b = rate_a + rng.randint(1, 3 + difficulty)
        # B has the higher rate; give A more time so A's total > B's total
        qty_a = rng.randint(4, 7 + difficulty)
        qty_b = rng.randint(2, max(2, qty_a - 1))
        total_a = rate_a * qty_a
        total_b = rate_b * qty_b
        # Ensure totals are ordered opposite to rates
        while total_a <= total_b:
            qty_a += 1
            total_a = rate_a * qty_a
        contexts = [
            ("miles", "hours", "faster"),
            ("problems", "minutes", "faster"),
            ("items", "dollars", "better value"),
        ]
        unit, per, comp = rng.choice(contexts)
        prompt = (
            f"Option A: {total_a} {unit} in {qty_a} {per}. "
            f"Option B: {total_b} {unit} in {qty_b} {per}. "
            f"Which is {comp}?"
        )
        # B always has the higher rate
        answer = "Option B"
        hints = (
            "Find each unit rate by dividing, then compare.",
            f"A: {total_a} ÷ {qty_a} = {rate_a}. B: {total_b} ÷ {qty_b} = {rate_b}.",
        )
        # Total-only thinker picks A (higher total), which is wrong
        misconceptions = {
            "RATE.COMPARE.TOTAL_ONLY": "Option A",
        }
        return prompt, answer, hints, misconceptions

    # --- distance-rate-time ---
    if family_code == "MATH.RATE.DRT":
        unknowns = ["distance", "rate", "time"]
        unknown = rng.choice(unknowns)
        rate = rng.randint(20, 40 + difficulty * 15)
        time_val = rng.randint(2, 5 + difficulty)
        distance = rate * time_val
        if unknown == "distance":
            prompt = (
                f"A train travels at {rate} miles per hour for {time_val} hours. "
                "How far does it travel?"
            )
            answer = f"{distance} miles"
            hints = (
                "Distance = rate × time.",
                f"{rate} × {time_val} = ?",
            )
            misconceptions = {
                "DRT.DIVIDE_INSTEAD": f"{rate // time_val if time_val != 0 else 0} miles",
            }
        elif unknown == "rate":
            prompt = (
                f"A cyclist covers {distance} miles in {time_val} hours. "
                "What is the cyclist's speed?"
            )
            answer = f"{rate} miles per hour"
            hints = (
                "Rate = distance ÷ time.",
                f"{distance} ÷ {time_val} = ?",
            )
            misconceptions = {
                "DRT.MULTIPLY_INSTEAD": f"{distance * time_val} miles per hour",
            }
        else:
            prompt = (
                f"A bus travels {distance} miles at {rate} miles per hour. "
                "How long does the trip take?"
            )
            answer = f"{time_val} hours"
            hints = (
                "Time = distance ÷ rate.",
                f"{distance} ÷ {rate} = ?",
            )
            misconceptions = {
                "DRT.MULTIPLY_INSTEAD": f"{distance * rate} hours",
            }
        return prompt, answer, hints, misconceptions

    # --- recipe ---
    if family_code == "MATH.RATIO.RECIPE":
        base_a = rng.randint(2, 4)
        base_b = rng.randint(1, 3)
        while base_a == base_b:
            base_b = rng.randint(1, 3)
        scale = rng.randint(2, 4 + difficulty)
        target_a = base_a * scale
        target_b = base_b * scale
        items_a = rng.choice(["cups of flour", "eggs", "tablespoons of butter"])
        items_b = rng.choice(["cups of sugar", "cups of milk", "teaspoons of vanilla"])
        prompt = (
            f"A recipe uses {base_a} {items_a} for every {base_b} {items_b}. "
            f"If you use {target_a} {items_a}, how much {items_b.split(' ', 1)[-1] if ' ' in items_b else items_b} do you need?"
        )
        answer = str(target_b)
        hints = (
            f"Set up the ratio: {base_a}/{base_b} = {target_a}/?",
            f"What was {base_a} multiplied by? Multiply {base_b} by the same number.",
        )
        additive_wrong = base_b + (target_a - base_a)
        misconceptions = {
            "RATIO.RECIPE.ADDITIVE": str(additive_wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- scale/map ---
    if family_code == "MATH.RATIO.SCALE":
        scale_a = rng.randint(1, 3)
        scale_b = rng.randint(5, 20 + difficulty * 10)
        map_dist = rng.randint(2, 6 + difficulty)
        actual = map_dist * scale_b // scale_a
        # Ensure clean division
        actual = (map_dist * scale_b) // scale_a
        map_dist_adj = actual * scale_a // scale_b  # adjust to be clean
        if map_dist_adj == 0:
            map_dist_adj = 1
        actual = map_dist_adj * scale_b // scale_a
        prompt = (
            f"On a map, {scale_a} cm represents {scale_b} km. "
            f"If two cities are {map_dist_adj} cm apart on the map, "
            "what is the actual distance?"
        )
        answer = f"{actual} km"
        hints = (
            f"Set up a proportion: {scale_a} cm / {scale_b} km = {map_dist_adj} cm / ? km.",
            f"Multiply: {map_dist_adj} × {scale_b} ÷ {scale_a}.",
        )
        misconceptions = {
            "RATIO.SCALE.ADD_INSTEAD": f"{map_dist_adj + scale_b} km",
        }
        return prompt, answer, hints, misconceptions

    # --- error: additive reasoning (structured MC) ---
    if family_code == "MATH.RATIO.ERROR.ADDITIVE":
        # Force clean multiplication
        mult = rng.randint(2, 4 + difficulty)
        a, b = rng.randint(2, 5), rng.randint(3, 7)
        while a == b:
            b = rng.randint(3, 7)
        new_a = a * mult
        correct_b = b * mult
        additive_b = b + (new_a - a)
        names = ["Jada", "Marcus", "Lin", "Tyler"]
        name = rng.choice(names)
        prompt = (
            f"The ratio of red to blue paint is {a}:{b}. {name} needs {new_a} cups of red. "
            f"{name} says you need {additive_b} cups of blue because \"I added {new_a - a} to red "
            f"so I add {new_a - a} to blue.\" "
            f"What is the correct amount of blue paint? "
            f"(A) {correct_b} cups "
            f"(B) {additive_b} cups "
            f"(C) {b} cups "
            f"(D) {new_a} cups"
        )
        answer = "A"
        hints = (
            f"How many times larger is {new_a} than {a}?",
            "Ratios scale by multiplication, not addition.",
            f"Multiply both terms by {mult}: blue = {b} × {mult} = {correct_b}.",
        )
        misconceptions = {
            "RATIO.ERROR.AGREE_ADDITIVE": "B",
            "RATIO.ERROR.ORIGINAL_ONLY": "C",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"Unknown ratio family: {family_code}")
