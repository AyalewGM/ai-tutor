"""Canonical division problem families.

Covers division facts, missing values, remainders, estimation, inverse
relationships, varied word-problem structures, and error analysis.
"""

from __future__ import annotations

import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _comma(n: int) -> str:
    return f"{n:,}"


def _mc(rng: random.Random, correct: str, distractors: list[str]) -> tuple[str, str]:
    """Return shuffled option text and the letter of the correct option."""
    values = [correct, *distractors]
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    candidate = 1
    while len(unique) < 4:
        value = str(candidate)
        if value not in unique:
            unique.append(value)
        candidate += 1
    rng.shuffle(unique)
    answer = chr(ord("A") + unique.index(correct))
    options = " ".join(
        f"({chr(ord('A') + i)}) {value}" for i, value in enumerate(unique)
    )
    return options, answer


FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.DIV.FACTS": ProblemFamilySpec(
        "MATH.DIV.FACTS", "Basic division facts", "MATH.NS.DIVISION",
        "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.DIV.MISSING_DIVISOR": ProblemFamilySpec(
        "MATH.DIV.MISSING_DIVISOR", "Missing divisor", "MATH.NS.DIVISION",
        "NUMBER_SENSE", 2, 3, ALL_MODES,
        frozenset({"procedural_fluency", "reasoning"}),
    ),
    "MATH.DIV.MISSING_DIVIDEND": ProblemFamilySpec(
        "MATH.DIV.MISSING_DIVIDEND", "Missing dividend", "MATH.NS.DIVISION",
        "NUMBER_SENSE", 2, 3, ALL_MODES,
        frozenset({"reasoning", "procedural_fluency"}),
    ),
    "MATH.DIV.REMAINDER": ProblemFamilySpec(
        "MATH.DIV.REMAINDER", "Division with remainder", "MATH.NS.DIVISION",
        "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.DIV.INTERPRET_REMAINDER": ProblemFamilySpec(
        "MATH.DIV.INTERPRET_REMAINDER", "Interpret a remainder in context",
        "MATH.NS.DIVISION", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "modeling", "transfer"}),
    ),
    "MATH.DIV.MULTIDIGIT": ProblemFamilySpec(
        "MATH.DIV.MULTIDIGIT", "Multi-digit division", "MATH.NS.DIVISION",
        "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.DIV.ESTIMATE": ProblemFamilySpec(
        "MATH.DIV.ESTIMATE", "Estimate a quotient", "MATH.NS.DIVISION",
        "ESTIMATION", 2, 4, ALL_MODES,
        frozenset({"estimation", "number_sense"}),
    ),
    "MATH.DIV.INVERSE": ProblemFamilySpec(
        "MATH.DIV.INVERSE", "Relate division to multiplication",
        "MATH.NS.DIVISION", "REASONING", 2, 3, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
    "MATH.DIV.WORD.PARTITIVE": ProblemFamilySpec(
        "MATH.DIV.WORD.PARTITIVE", "Word problem: partitive division",
        "MATH.NS.DIVISION", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.DIV.WORD.MEASUREMENT": ProblemFamilySpec(
        "MATH.DIV.WORD.MEASUREMENT", "Word problem: measurement division",
        "MATH.NS.DIVISION", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.DIV.WORD.COMPARE": ProblemFamilySpec(
        "MATH.DIV.WORD.COMPARE", "Word problem: division comparison",
        "MATH.NS.DIVISION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "comparison", "reasoning", "transfer"}),
    ),
    "MATH.DIV.WORD.REMAINDER_CONTEXT": ProblemFamilySpec(
        "MATH.DIV.WORD.REMAINDER_CONTEXT", "Word problem: remainder in context",
        "MATH.NS.DIVISION", "WORD_PROBLEM", 3, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.DIV.WORD.MULTISTEP": ProblemFamilySpec(
        "MATH.DIV.WORD.MULTISTEP", "Word problem: multi-step division",
        "MATH.NS.DIVISION", "WORD_PROBLEM", 3, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.DIV.ERROR.REVERSED": ProblemFamilySpec(
        "MATH.DIV.ERROR.REVERSED", "Error analysis: reversed divisor and dividend",
        "MATH.NS.DIVISION", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.DIV.FACTS":
        divisor = rng.randint(2, 4 + difficulty * 2)
        quotient = rng.randint(1, 4 + difficulty * 3)
        dividend = divisor * quotient
        prompt = f"What is {dividend} ÷ {divisor}?"
        answer = str(quotient)
        hints = (
            f"Think: {divisor} times what number equals {dividend}?",
            f"{divisor} × {quotient} = {dividend}.",
        )
        misconceptions = {"DIV.FACTS.MUL_INSTEAD": str(dividend * divisor)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.MISSING_DIVISOR":
        divisor = rng.randint(2, 5 + difficulty * 2)
        quotient = rng.randint(2, 5 + difficulty * 2)
        dividend = divisor * quotient
        prompt = f"Find the missing number: {dividend} ÷ ? = {quotient}"
        answer = str(divisor)
        hints = (
            "The missing number is the divisor.",
            f"Ask what number times {quotient} equals {dividend}.",
        )
        misconceptions = {"DIV.MISSING_DIVISOR.SUBTRACT": str(dividend - quotient)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.MISSING_DIVIDEND":
        divisor = rng.randint(2, 5 + difficulty * 2)
        quotient = rng.randint(2, 5 + difficulty * 2)
        dividend = divisor * quotient
        prompt = f"Find the missing number: ? ÷ {divisor} = {quotient}"
        answer = str(dividend)
        hints = (
            "Use multiplication to undo division.",
            f"Multiply {divisor} × {quotient}.",
        )
        misconceptions = {"DIV.MISSING_DIVIDEND.DIVIDE": str(divisor // quotient)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.REMAINDER":
        divisor = rng.randint(3, 5 + difficulty * 2)
        quotient = rng.randint(2, 5 + difficulty * 4)
        remainder = rng.randint(1, divisor - 1)
        dividend = divisor * quotient + remainder
        prompt = f"Divide: {dividend} ÷ {divisor} = ? R ?"
        answer = f"{quotient} R {remainder}"
        hints = (
            f"Find the greatest multiple of {divisor} that does not exceed {dividend}.",
            f"{divisor} × {quotient} = {divisor * quotient}; subtract from {dividend}.",
        )
        misconceptions = {"DIV.REMAINDER.FORGET_REMAINDER": str(quotient)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.INTERPRET_REMAINDER":
        divisor = rng.randint(4, 5 + difficulty * 2)
        quotient = rng.randint(3, 5 + difficulty * 2)
        remainder = rng.randint(1, divisor - 1)
        total = divisor * quotient + remainder
        if rng.choice([True, False]):
            noun = rng.choice(["vans", "buses", "boats", "elevators", "tables"])
            prompt = (f"{total} students need {noun} that each hold {divisor}. "
                      f"How many {noun} are needed?")
            answer = str(quotient + 1)
            literal = rng.choice([f"{quotient} R {remainder}", str(quotient)])
            hints = (
                f"{total} ÷ {divisor} leaves some students without a place.",
                "A partly filled group still requires one whole vehicle or space.",
            )
        else:
            item = rng.choice(["ribbon", "rope", "wire", "fabric", "lumber"])
            prompt = (f"A {total}-inch length of {item} is cut into {divisor}-inch pieces. "
                      "How many full pieces can be cut?")
            answer = str(quotient)
            literal = f"{quotient} R {remainder}"
            hints = (
                f"Compute {total} ÷ {divisor} and identify the remainder.",
                "Only complete pieces count; the leftover is not a full piece.",
            )
        misconceptions = {"DIV.INTERPRET.LITERAL_REMAINDER": literal}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.MULTIDIGIT":
        divisor = rng.randint(3, 9 if difficulty == 2 else 15 + difficulty * 5)
        lo, hi = (12, 99) if difficulty == 2 else ((50, 499) if difficulty == 3 else (200, 1999))
        quotient = rng.randint(lo, hi)
        dividend = divisor * quotient
        prompt = f"Divide: {_comma(dividend)} ÷ {_comma(divisor)}"
        answer = _comma(quotient)
        hints = (
            "Use place value and divide from left to right.",
            f"Check your quotient by multiplying it by {divisor}.",
        )
        misconceptions = {"DIV.MULTIDIGIT.REVERSED": str(divisor // dividend)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.ESTIMATE":
        divisor = rng.randint(3, 9 if difficulty == 2 else 20)
        target = rng.randint(4, 12 if difficulty == 2 else 40)
        compatible = divisor * target
        offset = rng.choice([-2, -1, 1, 2]) * max(1, divisor // 3)
        dividend = max(divisor, compatible + offset)
        correct = str(target)
        options, answer = _mc(rng, correct, [str(target - 2), str(target + 2), str(target * divisor)])
        prompt = f"Which is the best estimate for {dividend} ÷ {divisor}? {options}"
        hints = (
            f"Replace {dividend} with a nearby number divisible by {divisor}.",
            f"{compatible} is compatible because {compatible} ÷ {divisor} = {target}.",
        )
        misconceptions = {"DIV.ESTIMATE.NO_DIVISION": chr(ord("A") + options.split().index(str(target * divisor)) // 2) if False else str(target * divisor)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.INVERSE":
        a = rng.randint(2, 6 + difficulty * 2)
        b = rng.randint(2, 7 + difficulty * 3)
        c = a * b
        options, answer = _mc(rng, str(b), [str(a), str(c), str(max(1, b - 1))])
        prompt = f"If {a} × {b} = {c}, what is {c} ÷ {a}? {options}"
        hints = (
            "Multiplication and division are inverse operations.",
            f"The equation {a} × {b} = {c} can be rewritten as a division fact.",
        )
        misconceptions = {"DIV.INVERSE.OTHER_FACTOR": str(a), "DIV.INVERSE.PRODUCT": str(c)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.WORD.PARTITIVE":
        groups = rng.randint(2, 5 + difficulty * 2)
        each = rng.randint(2, 6 + difficulty * 4)
        total = groups * each
        template = rng.choice([
            "{x} stickers are shared equally among {y} students. How many does each student get?",
            "{x} cookies are divided equally among {y} families. How many does each family get?",
            "{x} books are shared equally among {y} classrooms. How many per classroom?",
            "{x} seeds are divided equally among {y} gardeners. How many does each get?",
            "{x} markers are shared equally among {y} teams. How many per team?",
        ])
        prompt = template.format(x=total, y=groups)
        answer = str(each)
        hints = ("Sharing equally means division.", f"Compute {total} ÷ {groups}.")
        misconceptions = {"DIV.WORD.PARTITIVE.MULTIPLY": str(total * groups)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.WORD.MEASUREMENT":
        size = rng.randint(2, 5 + difficulty * 2)
        groups = rng.randint(2, 6 + difficulty * 4)
        total = size * groups
        template = rng.choice([
            "{x} pencils are placed into boxes of {y}. How many boxes are filled?",
            "{x} flowers are arranged in bouquets of {y}. How many bouquets are made?",
            "{x} players form teams of {y}. How many teams are formed?",
            "{x} cans are packed in cases of {y}. How many cases are packed?",
            "{x} chairs are set in rows of {y}. How many rows are made?",
        ])
        prompt = template.format(x=total, y=size)
        answer = str(groups)
        hints = ("Count how many equal-size groups fit in the total.", f"Compute {total} ÷ {size}.")
        misconceptions = {"DIV.WORD.MEASUREMENT.GROUP_SIZE": str(size)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.WORD.COMPARE":
        factor = rng.randint(2, 5 + difficulty)
        smaller = rng.randint(3, 8 + difficulty * 5)
        larger = factor * smaller
        names = rng.choice([("Tom", "Sara"), ("Maya", "Liam"), ("Ava", "Noah"), ("Priya", "Omar"), ("Jordan", "Taylor")])
        item = rng.choice(["cards", "shells", "points", "coins", "beads"])
        prompt = (f"{names[0]} has {factor} times as many {item} as {names[1]}. "
                  f"{names[0]} has {larger} {item}. How many does {names[1]} have?")
        answer = str(smaller)
        hints = ("The larger amount and comparison factor are known.", f"Compute {larger} ÷ {factor}.")
        misconceptions = {"DIV.WORD.COMPARE.MULTIPLY": str(larger * factor)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.WORD.REMAINDER_CONTEXT":
        capacity = rng.randint(6, 12 + difficulty * 2)
        full = rng.randint(5, 12 + difficulty * 3)
        rem = rng.randint(1, capacity - 1)
        total = capacity * full + rem
        if rng.choice([True, False]):
            template = rng.choice([
                "A camp must transport {x} campers in canoes holding {y} each. How many canoes are needed?",
                "A museum has {x} visitors and schedules tours of at most {y}. How many guides are needed?",
                "A school packs {x} meals in crates holding {y}. How many crates are needed?",
                "A theater seats {x} guests at tables holding {y}. How many tables are needed?",
                "A rescue team moves {x} people in vehicles holding {y}. How many vehicles are needed?",
            ])
            answer = str(full + 1)
            action = "round up so everyone or everything is accommodated"
        else:
            template = rng.choice([
                "A bakery has {x} ounces of dough. Each full loaf needs {y} ounces. How many full loaves can be made?",
                "A carpenter has {x} inches of wood. Each shelf needs {y} inches. How many complete shelves can be made?",
                "A lab has {x} milliliters of solution. Each full sample uses {y}. How many full samples are possible?",
                "A farmer has {x} meters of fencing. Each pen needs {y}. How many complete pens can be built?",
                "A printer has {x} sheets. Each booklet needs {y}. How many complete booklets can be printed?",
            ])
            answer = str(full)
            action = "drop the remainder because only complete products count"
        prompt = template.format(x=total, y=capacity)
        hints = (f"Divide {total} by {capacity} and inspect the remainder.", f"In this context, {action}.")
        misconceptions = {"DIV.WORD.REMAINDER.LITERAL": f"{full} R {rem}"}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.WORD.MULTISTEP":
        groups = rng.randint(3, 7 + difficulty)
        each_first = rng.randint(10, 20 + difficulty * 5)
        each_second = rng.randint(5, 15 + difficulty * 4)
        first = each_first * groups
        second = each_second * groups
        total = first + second
        template = rng.choice([
            "A school has {a} red pencils and {b} blue pencils. They are shared equally among {g} classes. How many pencils does each class get?",
            "A club collected {a} cans in the morning and {b} in the afternoon. The cans are split among {g} teams. How many cans per team?",
            "A library received {a} books Monday and {b} Tuesday. They are divided among {g} rooms. How many books per room?",
            "A garden harvested {a} tomatoes and {b} peppers. They are shared among {g} stalls. How many items per stall?",
            "A drive gathered {a} food items and {b} drinks. They are shared among {g} shelters. How many items per shelter?",
        ])
        prompt = template.format(a=first, b=second, g=groups)
        answer = str(total // groups)
        hints = (f"First add the two amounts: {first} + {second}.", f"Then divide the total, {total}, equally among {groups} groups.")
        misconceptions = {"DIV.WORD.MULTISTEP.ONE_STEP": str(total)}
        return prompt, answer, hints, misconceptions

    if family_code == "MATH.DIV.ERROR.REVERSED":
        divisor = rng.randint(2, 9)
        quotient = rng.randint(3, 10 + difficulty * 3)
        dividend = divisor * quotient
        student = divisor / dividend
        prompt = (
            f"A student was asked to compute {dividend} ÷ {divisor}, but computed "
            f"{divisor} ÷ {dividend} = {student:g}. What mistake did the student make? "
            "(A) Reversed the dividend and divisor. (B) Forgot a remainder. "
            "(C) Multiplied instead of dividing. (D) Made no mistake."
        )
        answer = "A"
        hints = ("Identify which number should be divided.", f"The original expression is {dividend} ÷ {divisor}, not {divisor} ÷ {dividend}.")
        misconceptions = {
            "DIV.ERROR.REVERSED.REMAINDER": "B",
            "DIV.ERROR.REVERSED.MULTIPLY": "C",
            "DIV.ERROR.REVERSED.NO_ERROR": "D",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")
