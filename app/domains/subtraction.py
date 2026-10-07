"""Canonical subtraction problem families.

Covers: basic subtraction facts, missing subtrahend/minuend, multi-digit
subtraction with regrouping, estimation, the inverse relationship with addition,
a full range of word-problem situations (result unknown, change unknown,
start unknown, compare), multi-step subtraction, and regrouping error analysis.
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


def _round_to(n: int, unit: int) -> int:
    """Round *n* to the nearest multiple of *unit*."""
    half = unit // 2
    remainder = n % unit
    if remainder >= half:
        return n - remainder + unit
    return n - remainder


def _requires_borrow(a: int, b: int) -> bool:
    """Return True if a-b needs regrouping (borrowing) in at least one column."""
    while a > 0 or b > 0:
        if (a % 10) < (b % 10):
            return True
        a //= 10
        b //= 10
    return False


def _sub_multidigit_pair(rng: random.Random, digits: int, ensure_borrow: bool) -> tuple[int, int]:
    """Return two *digits*-wide numbers with a > b, optionally requiring a borrow."""
    lo = 10 ** (digits - 1)
    hi = 10 ** digits - 1
    while True:
        a = rng.randint(lo + 1, hi)
        b = rng.randint(lo, a - 1)
        if not ensure_borrow or _requires_borrow(a, b):
            return a, b


def _flip_digits_diff(a: int, b: int) -> int:
    """Subtract the smaller digit from the larger in each column independently."""
    result = 0
    place = 1
    while a > 0 or b > 0:
        d1 = a % 10
        d2 = b % 10
        result += abs(d1 - d2) * place
        place *= 10
        a //= 10
        b //= 10
    return result


def _name(rng: random.Random) -> str:
    return rng.choice(
        ["Sara", "Tom", "Maya", "Liam", "Ava", "Noah", "Priya", "Omar",
         "Ms. Chen", "Mr. Patel", "Jordan", "Taylor"]
    )


def _difficulty_range(difficulty: int) -> tuple[int, int]:
    """Return (lo, hi) number bounds scaled by difficulty."""
    if difficulty <= 1:
        return 2, 20
    if difficulty == 2:
        return 10, 100
    if difficulty == 3:
        return 50, 1_000
    return 100, 10_000


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    # --- Core facts & missing values ---
    "MATH.SUB.FACTS": ProblemFamilySpec(
        "MATH.SUB.FACTS", "Basic subtraction facts",
        "MATH.NS.SUBTRACTION", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.SUB.MISSING_SUBTRAHEND": ProblemFamilySpec(
        "MATH.SUB.MISSING_SUBTRAHEND", "Missing subtrahend",
        "MATH.NS.SUBTRACTION", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "reasoning"}),
    ),
    "MATH.SUB.MISSING_MINUEND": ProblemFamilySpec(
        "MATH.SUB.MISSING_MINUEND", "Missing minuend",
        "MATH.NS.SUBTRACTION", "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"reasoning", "procedural_fluency"}),
    ),
    # --- Multi-digit & estimation ---
    "MATH.SUB.MULTIDIGIT": ProblemFamilySpec(
        "MATH.SUB.MULTIDIGIT", "Multi-digit subtraction with regrouping",
        "MATH.NS.SUBTRACTION", "NUMBER_SENSE", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.SUB.ESTIMATE": ProblemFamilySpec(
        "MATH.SUB.ESTIMATE", "Estimate a difference",
        "MATH.NS.SUBTRACTION", "ESTIMATION", 2, 4, ALL_MODES,
        frozenset({"estimation", "number_sense"}),
    ),
    # --- Reasoning / inverse ---
    "MATH.SUB.INVERSE": ProblemFamilySpec(
        "MATH.SUB.INVERSE", "Relate subtraction to addition",
        "MATH.NS.SUBTRACTION", "REASONING", 2, 3, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
    # --- Word problems ---
    "MATH.SUB.WORD.RESULT_UNKNOWN": ProblemFamilySpec(
        "MATH.SUB.WORD.RESULT_UNKNOWN", "Word problem: result unknown",
        "MATH.NS.SUBTRACTION", "WORD_PROBLEM", 1, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.SUB.WORD.CHANGE_UNKNOWN": ProblemFamilySpec(
        "MATH.SUB.WORD.CHANGE_UNKNOWN", "Word problem: change unknown",
        "MATH.NS.SUBTRACTION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.SUB.WORD.START_UNKNOWN": ProblemFamilySpec(
        "MATH.SUB.WORD.START_UNKNOWN", "Word problem: start unknown",
        "MATH.NS.SUBTRACTION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.SUB.WORD.COMPARE_DIFF": ProblemFamilySpec(
        "MATH.SUB.WORD.COMPARE_DIFF", "Comparison: difference unknown",
        "MATH.NS.SUBTRACTION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "comparison", "transfer"}),
    ),
    "MATH.SUB.WORD.COMPARE_LARGER": ProblemFamilySpec(
        "MATH.SUB.WORD.COMPARE_LARGER", "Comparison: larger unknown",
        "MATH.NS.SUBTRACTION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "comparison", "reasoning", "transfer"}),
    ),
    "MATH.SUB.WORD.COMPARE_SMALLER": ProblemFamilySpec(
        "MATH.SUB.WORD.COMPARE_SMALLER", "Comparison: smaller unknown",
        "MATH.NS.SUBTRACTION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "comparison", "reasoning", "transfer"}),
    ),
    "MATH.SUB.WORD.MULTISTEP": ProblemFamilySpec(
        "MATH.SUB.WORD.MULTISTEP", "Multi-step subtraction word problem",
        "MATH.NS.SUBTRACTION", "WORD_PROBLEM", 3, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    # --- Error analysis ---
    "MATH.SUB.ERROR.REGROUP": ProblemFamilySpec(
        "MATH.SUB.ERROR.REGROUP", "Error analysis: regrouping mistake",
        "MATH.NS.SUBTRACTION", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build(family_code: str, rng: random.Random, difficulty: int):
    """Return (prompt, answer, hints, misconceptions) for *family_code*."""

    # --- basic facts ---
    if family_code == "MATH.SUB.FACTS":
        if difficulty == 1:
            a = rng.randint(2, 10)
        elif difficulty == 2:
            a = rng.randint(5, 20)
        else:
            a = rng.randint(10, 100)
        b = rng.randint(1, a)
        prompt = f"What is {a} - {b}?"
        answer = str(a - b)
        hints = (
            "Start at the first number and count down by the second number.",
            f"{a} - {b} is the same as asking what plus {b} equals {a}.",
        )
        misconceptions = {
            "SUB.FACTS.ADD_INSTEAD": str(a + b),
        }
        return prompt, answer, hints, misconceptions

    # --- missing subtrahend ---
    if family_code == "MATH.SUB.MISSING_SUBTRAHEND":
        lo, hi = _difficulty_range(difficulty)
        y = rng.randint(lo, hi // 2)
        missing = rng.randint(1, y)
        x = y + missing  # x - missing = y, so x > y
        prompt = f"{_comma(x)} - ____ = {_comma(y)}"
        answer = str(missing)
        hints = (
            f"What number subtracted from {_comma(x)} gives {_comma(y)}?",
            f"Think: {_comma(x)} - ? = {_comma(y)}, so ? = {_comma(x)} - {_comma(y)}.",
        )
        misconceptions = {
            "SUB.MISSING_SUBTRAHEND.ADD_INSTEAD": str(x + y),
        }
        return prompt, answer, hints, misconceptions

    # --- missing minuend ---
    if family_code == "MATH.SUB.MISSING_MINUEND":
        lo, hi = _difficulty_range(difficulty)
        x = rng.randint(lo, hi)
        y = rng.randint(lo, hi)
        prompt = f"____ - {_comma(x)} = {_comma(y)}"
        answer = str(x + y)
        hints = (
            "The missing number is the total of the two known numbers.",
            f"Add {_comma(x)} and {_comma(y)}.",
        )
        misconceptions = {
            "SUB.MISSING_MINUEND.SUBTRACT_INSTEAD": str(abs(x - y)),
        }
        return prompt, answer, hints, misconceptions

    # --- multi-digit with regrouping ---
    if family_code == "MATH.SUB.MULTIDIGIT":
        if difficulty == 1 or difficulty == 2:
            digits = 2
        elif difficulty == 3:
            digits = 3
        else:
            digits = rng.choice([3, 4])
        ensure_borrow = True

        a, b = _sub_multidigit_pair(rng, digits, ensure_borrow)
        diff = a - b
        prompt = f"Subtract: {_comma(a)} - {_comma(b)}"
        answer = _comma(diff)
        hints = (
            "Subtract starting from the right (ones place).",
            "If the top digit in a column is smaller, regroup (borrow) from the next column.",
        )
        misconceptions = {
            "SUB.MULTIDIGIT.FLIP_DIGITS": _comma(_flip_digits_diff(a, b)),
        }
        return prompt, answer, hints, misconceptions

    # --- estimate a difference ---
    if family_code == "MATH.SUB.ESTIMATE":
        if difficulty == 2:
            unit, place_name, lo, hi = 10, "ten", 10, 99
        elif difficulty == 3:
            unit, place_name, lo, hi = 100, "hundred", 100, 999
        else:
            unit, place_name, lo, hi = 1_000, "thousand", 1_000, 9_999

        a = rng.randint(lo + 1, hi)
        b = rng.randint(lo, a - 1)
        rounded_a = _round_to(a, unit)
        rounded_b = _round_to(b, unit)
        estimate = rounded_a - rounded_b
        prompt = (
            f"Estimate {_comma(a)} - {_comma(b)} by rounding each number "
            f"to the nearest {place_name}."
        )
        answer = _comma(estimate)
        hints = (
            f"Round each number to the nearest {place_name} first.",
            (f"{_comma(a)} rounds to {_comma(rounded_a)} and "
             f"{_comma(b)} rounds to {_comma(rounded_b)}."),
        )
        misconceptions = {
            "SUB.ESTIMATE.EXACT_ANSWER": _comma(a - b),
        }
        return prompt, answer, hints, misconceptions

    # --- inverse relationship with addition ---
    if family_code == "MATH.SUB.INVERSE":
        a = rng.randint(2, 9 + difficulty * 3)
        b = rng.randint(2, 9 + difficulty * 3)
        while a == b:
            b = rng.randint(2, 9 + difficulty * 3)
        c = a + b
        options = [
            (str(b), "correct"),
            (str(a), "SUB.INVERSE.PICK_A"),
            (str(c), "distractor"),
        ]
        rng.shuffle(options)
        labels = ["A", "B", "C"]
        option_text = " ".join(
            f"({labels[i]}) {val}" for i, (val, _) in enumerate(options)
        )
        prompt = (
            f"If {a} + {b} = {c}, what is {c} - {a}? {option_text}"
        )
        correct_idx = next(i for i, (_, tag) in enumerate(options) if tag == "correct")
        answer = labels[correct_idx]
        misconceptions: dict[str, str] = {}
        for i, (_, tag) in enumerate(options):
            if tag == "SUB.INVERSE.PICK_A":
                misconceptions[tag] = labels[i]
        hints = (
            "Subtraction undoes addition.",
            f"If {a} + {b} = {c}, then {c} - {a} must be the other addend.",
        )
        return prompt, answer, hints, misconceptions

    # --- word problem: result unknown ---
    if family_code == "MATH.SUB.WORD.RESULT_UNKNOWN":
        lo, hi = _difficulty_range(difficulty)
        x = rng.randint(lo + 1, hi)
        y = rng.randint(lo, x - 1)

        templates = [
            f"Maria has {_comma(x)} stickers. She gave {_comma(y)} to her friend. How many stickers does Maria have now?",
            f"A basket had {_comma(x)} apples. {_comma(y)} apples were used for a pie. How many apples are left?",
            f"A classroom had {_comma(x)} pencils. {_comma(y)} pencils were lost. How many pencils remain?",
            f"There were {_comma(x)} books on a shelf. {_comma(y)} were checked out. How many books are still on the shelf?",
            f"A baker made {_comma(x)} cookies. {_comma(y)} cookies were sold. How many cookies are left?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(x - y)
        hints = (
            "Look for words like 'gave away' or 'left' that tell you to subtract.",
            f"Subtract {_comma(y)} from {_comma(x)}.",
        )
        misconceptions = {
            "SUB.WORD.RESULT.ADD_INSTEAD": _comma(x + y),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: change unknown ---
    if family_code == "MATH.SUB.WORD.CHANGE_UNKNOWN":
        lo, hi = _difficulty_range(difficulty)
        x = rng.randint(lo + 1, hi)
        y = rng.randint(lo, x - 1)

        name = _name(rng)
        templates = [
            f"{name} had {_comma(x)} marbles. After losing some, {name} has {_comma(y)} marbles. How many marbles were lost?",
            f"A jar had {_comma(x)} crayons. After some were used, {_comma(y)} crayons remained. How many crayons were used?",
            f"A bus had {_comma(x)} passengers. After some got off, {_comma(y)} passengers remained. How many passengers got off?",
            f"A bank account had ${_comma(x)}. After a withdrawal, the balance is ${_comma(y)}. How much was withdrawn?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(x - y)
        hints = (
            "The start minus the unknown change equals the final amount.",
            f"Use the inverse operation: {_comma(x)} - {_comma(y)}.",
        )
        misconceptions = {
            "SUB.WORD.CHANGE.ANSWER_FINAL": _comma(y),
            "SUB.WORD.CHANGE.ADD_INSTEAD": _comma(x + y),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: start unknown ---
    if family_code == "MATH.SUB.WORD.START_UNKNOWN":
        lo, hi = _difficulty_range(difficulty)
        x = rng.randint(lo, hi)
        y = rng.randint(lo, hi)

        name = _name(rng)
        templates = [
            f"{name} lost {_comma(x)} stickers and now has {_comma(y)} stickers. How many stickers did {name} have at the start?",
            f"After {_comma(x)} birds flew away, {_comma(y)} birds remained in the tree. How many birds were in the tree at first?",
            f"A store sold {_comma(x)} books and has {_comma(y)} books left. How many books did the store have to begin with?",
            f"{name} spent ${_comma(x)} and now has ${_comma(y)}. How much money did {name} have at first?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(x + y)
        hints = (
            "The unknown is the starting amount, not the amount lost.",
            f"Start - {_comma(x)} = {_comma(y)}, so start = {_comma(x)} + {_comma(y)}.",
        )
        misconceptions = {
            "SUB.WORD.START.SUBTRACT_INSTEAD": _comma(abs(x - y)),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: compare difference unknown ---
    if family_code == "MATH.SUB.WORD.COMPARE_DIFF":
        lo, hi = _difficulty_range(difficulty)
        x = rng.randint(lo + 1, hi)
        y = rng.randint(lo, x - 1)

        name1, name2 = _name(rng), _name(rng)
        while name1 == name2:
            name2 = _name(rng)
        templates = [
            f"{name1} has {_comma(x)} stickers. {name2} has {_comma(y)} stickers. How many more stickers does {name1} have than {name2}?",
            f"{name1} ran {_comma(x)} laps. {name2} ran {_comma(y)} laps. How many more laps did {name1} run?",
            f"{name1} has ${_comma(x)}. {name2} has ${_comma(y)}. How much more money does {name1} have?",
            f"{name1} read {_comma(x)} pages. {name2} read {_comma(y)} pages. How many more pages did {name1} read?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(x - y)
        hints = (
            "'How many more' means find the difference between the two amounts.",
            f"Subtract {_comma(y)} from {_comma(x)}.",
        )
        misconceptions = {
            "SUB.WORD.COMPARE_DIFF.PICK_SMALLER": _comma(y),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: compare larger unknown ---
    if family_code == "MATH.SUB.WORD.COMPARE_LARGER":
        lo, hi = _difficulty_range(difficulty)
        x = rng.randint(lo, hi)
        y = rng.randint(lo, hi)

        name1, name2 = _name(rng), _name(rng)
        while name1 == name2:
            name2 = _name(rng)
        templates = [
            f"{name1} has {_comma(x)} more stickers than {name2}. {name2} has {_comma(y)} stickers. How many stickers does {name1} have?",
            f"{name1} ran {_comma(x)} more laps than {name2}. {name2} ran {_comma(y)} laps. How many laps did {name1} run?",
            f"{name1} has ${_comma(x)} more than {name2}. {name2} has ${_comma(y)}. How much money does {name1} have?",
            f"{name1} read {_comma(x)} more pages than {name2}. {name2} read {_comma(y)} pages. How many pages did {name1} read?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(y + x)
        hints = (
            f"'{_comma(x)} more' means you add {_comma(x)} to {name2}'s amount.",
            f"{_comma(y)} + {_comma(x)} = {_comma(y + x)}.",
        )
        misconceptions = {
            "SUB.WORD.COMPARE_LARGER.IGNORE_DIFFERENCE": _comma(y),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: compare smaller unknown ---
    if family_code == "MATH.SUB.WORD.COMPARE_SMALLER":
        lo, hi = _difficulty_range(difficulty)
        x = rng.randint(lo, hi - 1)
        y = rng.randint(x + 1, hi)

        name1, name2 = _name(rng), _name(rng)
        while name1 == name2:
            name2 = _name(rng)
        templates = [
            f"{name1} has {_comma(x)} more stickers than {name2}. {name1} has {_comma(y)} stickers. How many stickers does {name2} have?",
            f"{name1} ran {_comma(x)} more laps than {name2}. {name1} ran {_comma(y)} laps. How many laps did {name2} run?",
            f"{name1} has ${_comma(x)} more than {name2}. {name1} has ${_comma(y)}. How much money does {name2} have?",
            f"{name1} read {_comma(x)} more pages than {name2}. {name1} read {_comma(y)} pages. How many pages did {name2} read?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(y - x)
        hints = (
            f"{name2} has less than {name1}. Subtract {_comma(x)} from {_comma(y)}.",
            f"{_comma(y)} - {_comma(x)} = {_comma(y - x)}.",
        )
        misconceptions = {
            "SUB.WORD.COMPARE_SMALLER.ADD_INSTEAD": _comma(y + x),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: multi-step ---
    if family_code == "MATH.SUB.WORD.MULTISTEP":
        if difficulty == 3:
            lo, hi = 10, 100
        else:
            lo, hi = 100, 1_000
        a = rng.randint(lo * 3, hi)
        b = rng.randint(lo, a - 2 * lo)
        c = rng.randint(lo, a - b - lo)

        templates = [
            f"A box contains {_comma(a)} crayons. During art class, {_comma(b)} crayons were used. Later, {_comma(c)} more crayons were used. How many crayons are left?",
            f"A library had {_comma(a)} books. On Monday {_comma(b)} books were checked out. On Tuesday {_comma(c)} more books were checked out. How many books remain?",
            f"A bakery made {_comma(a)} cookies. In the morning {_comma(b)} were sold. In the afternoon {_comma(c)} more were sold. How many cookies are left?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(a - b - c)
        hints = (
            "This problem needs two subtractions.",
            f"First subtract {_comma(b)} from {_comma(a)}, then subtract {_comma(c)}.",
        )
        misconceptions = {
            "SUB.WORD.MULTISTEP.SUBTRACT_ONCE": _comma(a - b),
            "SUB.WORD.MULTISTEP.ADD_INSTEAD": _comma(a + b + c),
        }
        return prompt, answer, hints, misconceptions

    # --- error analysis: regrouping mistake ---
    if family_code == "MATH.SUB.ERROR.REGROUP":
        if difficulty == 2:
            digits = 2
        elif difficulty == 3:
            digits = 3
        else:
            digits = 4

        a, b = _sub_multidigit_pair(rng, digits, ensure_borrow=True)
        correct = a - b
        flipped = _flip_digits_diff(a, b)

        # Build unique distractors so no two MC labels share the same value.
        used = {correct, flipped}
        distractor1 = correct + 10
        if distractor1 in used:
            distractor1 = correct + 1
        used.add(distractor1)
        distractor2 = max(correct - 10, 0)
        while distractor2 in used:
            distractor2 += 1

        options = [
            (correct, "correct"),
            (flipped, "SUB.ERROR.REGROUP.FLIP_DIGITS"),
            (distractor1, "distractor"),
            (distractor2, "distractor"),
        ]
        rng.shuffle(options)
        labels = ["A", "B", "C", "D"]
        name = _name(rng)
        option_text = " ".join(
            f"({labels[i]}) {_comma(val)}" for i, (val, _) in enumerate(options)
        )
        prompt = (
            f"{name} subtracted {_comma(a)} - {_comma(b)} by subtracting the smaller "
            f"digit from the larger digit in each column and got {_comma(flipped)}. "
            f"What is the correct answer? {option_text}"
        )
        correct_idx = next(i for i, (_, tag) in enumerate(options) if tag == "correct")
        answer = labels[correct_idx]
        misconceptions: dict[str, str] = {}
        for i, (_, tag) in enumerate(options):
            if tag == "SUB.ERROR.REGROUP.FLIP_DIGITS":
                misconceptions[tag] = labels[i]
        hints = (
            "Check the ones column. Do you need to regroup?",
            "Regrouping lets you subtract the bottom digit from a larger top digit.",
            f"The correct difference is {_comma(correct)}.",
        )
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")
