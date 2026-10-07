"""Canonical addition problem families.

Covers: basic addition facts, missing addends, multi-digit addition with
regrouping, estimation, properties of addition, and a range of word problem
situations (result unknown, change unknown, start unknown, combine, compare,
multi-step).  Also includes error analysis targeting the classic
failure-to-regroup misconception.
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


def _round_to(n: int, unit: int) -> int:
    """Round *n* to the nearest multiple of *unit*."""
    half = unit // 2
    remainder = n % unit
    if remainder >= half:
        return n - remainder + unit
    return n - remainder


def _requires_regrouping(a: int, b: int) -> bool:
    """Return True if a+b needs regrouping in at least one column."""
    while a > 0 or b > 0:
        if (a % 10) + (b % 10) >= 10:
            return True
        a //= 10
        b //= 10
    return False


def _multidigit_pair(rng: random.Random, digits: int, ensure_regroup: bool) -> tuple[int, int]:
    """Return two *digits*-wide numbers, optionally requiring regrouping."""
    lo = 10 ** (digits - 1)
    hi = 10 ** digits - 1
    while True:
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        if not ensure_regroup or _requires_regrouping(a, b):
            return a, b


def _fail_regroup_sum(a: int, b: int) -> int:
    """Add digits column-wise without carrying; mimics the classic regroup error."""
    result = 0
    place = 1
    while a > 0 or b > 0:
        col_sum = (a % 10) + (b % 10)
        result += (col_sum % 10) * place
        place *= 10
        a //= 10
        b //= 10
    return result


# Varied word-problem contexts so problems do not all sound like "apples".
_NAMES = ["Sara", "Tom", "Maya", "Liam", "Ava", "Noah", "Priya", "Omar",
          "Ms. Chen", "Mr. Patel", "Jordan", "Taylor"]


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.ADD.FACTS": ProblemFamilySpec(
        "MATH.ADD.FACTS", "Basic addition facts",
        "MATH.NS.ADDITION", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.ADD.MISSING_ADDEND": ProblemFamilySpec(
        "MATH.ADD.MISSING_ADDEND", "Find the missing addend",
        "MATH.NS.ADDITION", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "reasoning"}),
    ),
    "MATH.ADD.MULTIDIGIT": ProblemFamilySpec(
        "MATH.ADD.MULTIDIGIT", "Multi-digit addition with regrouping",
        "MATH.NS.ADDITION", "NUMBER_SENSE", 1, 4, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.ADD.ESTIMATE": ProblemFamilySpec(
        "MATH.ADD.ESTIMATE", "Estimate a sum",
        "MATH.NS.ADDITION", "ESTIMATION", 2, 4, ALL_MODES,
        frozenset({"estimation", "number_sense", "reasoning"}),
    ),
    "MATH.ADD.PROPERTIES": ProblemFamilySpec(
        "MATH.ADD.PROPERTIES", "Properties of addition",
        "MATH.NS.ADDITION", "REASONING", 2, 3, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
    "MATH.ADD.WORD.RESULT_UNKNOWN": ProblemFamilySpec(
        "MATH.ADD.WORD.RESULT_UNKNOWN", "Word problem: result unknown",
        "MATH.NS.ADDITION", "WORD_PROBLEM", 1, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.ADD.WORD.CHANGE_UNKNOWN": ProblemFamilySpec(
        "MATH.ADD.WORD.CHANGE_UNKNOWN", "Word problem: change unknown",
        "MATH.NS.ADDITION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.ADD.WORD.START_UNKNOWN": ProblemFamilySpec(
        "MATH.ADD.WORD.START_UNKNOWN", "Word problem: start unknown",
        "MATH.NS.ADDITION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.ADD.WORD.COMBINE": ProblemFamilySpec(
        "MATH.ADD.WORD.COMBINE", "Word problem: combine",
        "MATH.NS.ADDITION", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "transfer"}),
    ),
    "MATH.ADD.WORD.COMPARE": ProblemFamilySpec(
        "MATH.ADD.WORD.COMPARE", "Word problem: comparison addition",
        "MATH.NS.ADDITION", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "comparison", "transfer"}),
    ),
    "MATH.ADD.WORD.MULTISTEP": ProblemFamilySpec(
        "MATH.ADD.WORD.MULTISTEP", "Word problem: multi-step addition",
        "MATH.NS.ADDITION", "WORD_PROBLEM", 3, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.ADD.ERROR.REGROUP": ProblemFamilySpec(
        "MATH.ADD.ERROR.REGROUP", "Error analysis: regrouping mistake",
        "MATH.NS.ADDITION", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):

    # --- basic facts ---
    if family_code == "MATH.ADD.FACTS":
        lo = 1 + (difficulty - 1)
        hi = 5 + difficulty * 3
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        total = a + b
        prompt = f"What is {a} + {b}?"
        answer = str(total)
        hints = (
            "Think about starting at the larger number and counting up.",
            f"{max(a, b)} + {min(a, b)} = {total}.",
        )
        misconceptions = {
            "ADD.FACTS.OFF_BY_ONE_PLUS": str(total + 1),
            "ADD.FACTS.OFF_BY_ONE_MINUS": str(total - 1),
        }
        return prompt, answer, hints, misconceptions

    # --- missing addend ---
    if family_code == "MATH.ADD.MISSING_ADDEND":
        x = rng.randint(2, 5 + difficulty * 4)
        missing = rng.randint(1, 5 + difficulty * 4)
        y = x + missing
        prompt = f"What number added to {x} gives {y}?"
        answer = str(missing)
        hints = (
            f"Rewrite the question as: {x} + ___ = {y}.",
            f"Use the inverse operation: {y} - {x}.",
        )
        misconceptions = {
            "ADD.MISSING.ADD_INSTEAD": str(x + y),
        }
        return prompt, answer, hints, misconceptions

    # --- multi-digit with regrouping ---
    if family_code == "MATH.ADD.MULTIDIGIT":
        if difficulty == 1:
            digits = 2
            ensure_regroup = False
        elif difficulty == 2:
            digits = 2
            ensure_regroup = True
        elif difficulty == 3:
            digits = 3
            ensure_regroup = True
        else:
            digits = rng.choice([3, 4])
            ensure_regroup = True

        a, b = _multidigit_pair(rng, digits, ensure_regroup)
        total = a + b
        prompt = f"Add: {_comma(a)} + {_comma(b)}"
        answer = _comma(total)
        hints = (
            "Add the digits starting from the right (ones place).",
            "If a column sums to 10 or more, regroup (carry) to the next column.",
        )
        misconceptions = {
            "ADD.MULTI.FAIL_REGROUP": _comma(_fail_regroup_sum(a, b)),
        }
        return prompt, answer, hints, misconceptions

    # --- estimate a sum ---
    if family_code == "MATH.ADD.ESTIMATE":
        if difficulty == 2:
            unit, place_name, lo, hi = 10, "ten", 10, 99
        elif difficulty == 3:
            unit, place_name, lo, hi = 100, "hundred", 100, 999
        else:
            unit, place_name, lo, hi = 1_000, "thousand", 1_000, 9_999

        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        rounded_a = _round_to(a, unit)
        rounded_b = _round_to(b, unit)
        prompt = (
            f"Estimate {_comma(a)} + {_comma(b)} by rounding each number "
            f"to the nearest {place_name}."
        )
        answer = _comma(rounded_a + rounded_b)
        hints = (
            f"Round each addend to the nearest {place_name} first.",
            (f"{_comma(a)} rounds to {_comma(rounded_a)} and "
             f"{_comma(b)} rounds to {_comma(rounded_b)}."),
        )
        misconceptions = {
            "ADD.ESTIMATE.EXACT_ANSWER": _comma(a + b),
        }
        return prompt, answer, hints, misconceptions

    # --- properties of addition ---
    if family_code == "MATH.ADD.PROPERTIES":
        a = rng.randint(2, 9)
        b = rng.randint(2, 9)
        c = rng.randint(2, 9)

        target = "commutative" if difficulty == 2 else rng.choice(["commutative", "associative"])

        options = [
            ("commutative", f"{a}+{b}={b}+{a}"),
            ("associative", f"({a}+{b})+{c}={a}+({b}+{c})"),
            ("identity", f"{a}+0={a}"),
            ("distractor", f"{a}+{b}={a}×{b}"),
        ]
        rng.shuffle(options)

        correct_idx = next(i for i, (label, _) in enumerate(options) if label == target)
        answer = chr(ord("A") + correct_idx)
        option_text = " ".join(
            f"({chr(ord('A') + i)}) {expr}" for i, (_, expr) in enumerate(options)
        )
        prompt = f"Which equation shows the {target} property of addition? {option_text}"
        hints = (
            "The commutative property says the order of addends does not matter.",
            "The associative property says the grouping of addends does not matter.",
        )
        misconceptions = {}
        for i, (label, _) in enumerate(options):
            if label != target:
                misconceptions[f"ADD.PROPERTIES.{label.upper()}"] = chr(ord("A") + i)
        return prompt, answer, hints, misconceptions

    # --- word problem: result unknown ---
    if family_code == "MATH.ADD.WORD.RESULT_UNKNOWN":
        if difficulty == 1:
            x = rng.randint(1, 10)
            y = rng.randint(1, 10)
        elif difficulty == 2:
            x = rng.randint(10, 50)
            y = rng.randint(10, 50)
        elif difficulty == 3:
            x = rng.randint(50, 500)
            y = rng.randint(50, 500)
        else:
            x = rng.randint(100, 2_000)
            y = rng.randint(100, 2_000)

        templates = [
            f"A store had {_comma(x)} books in stock. They received {_comma(y)} more books. How many books are there in all?",
            f"There were {_comma(x)} students in the cafeteria. {_comma(y)} more students joined. How many students are there now?",
            f"A farmer had {_comma(x)} animals in the barn. {_comma(y)} more animals came inside. How many animals are in the barn now?",
            f"A bus had {_comma(x)} passengers. At the next stop, {_comma(y)} more passengers got on. How many passengers are on the bus now?",
            f"A museum display had {_comma(x)} artifacts. The curator added {_comma(y)} more artifacts. How many artifacts are on display?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(x + y)
        hints = (
            "Look for words that tell you to combine amounts.",
            f"Add the starting amount {_comma(x)} to the amount that joined {_comma(y)}.",
        )
        misconceptions = {
            "ADD.WORD.RESULT.SUBTRACTED": _comma(abs(x - y)),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: change unknown ---
    if family_code == "MATH.ADD.WORD.CHANGE_UNKNOWN":
        if difficulty == 2:
            x = rng.randint(10, 50)
            change = rng.randint(5, 30)
        elif difficulty == 3:
            x = rng.randint(50, 500)
            change = rng.randint(20, 200)
        else:
            x = rng.randint(100, 2_000)
            change = rng.randint(50, 1_000)
        y = x + change

        templates = [
            f"A jar had {_comma(x)} marbles. After adding some more, there are {_comma(y)} marbles. How many marbles were added?",
            f"A box had {_comma(x)} crayons. A teacher added some crayons, and now there are {_comma(y)}. How many crayons did she add?",
            f"A tree had {_comma(x)} birds. More birds flew in, and now there are {_comma(y)} birds. How many birds flew in?",
            f"A bank account had ${_comma(x)}. After a deposit, the balance is ${_comma(y)}. How much was deposited?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(change)
        hints = (
            "The start plus the unknown change equals the final amount.",
            f"Use the inverse operation: {_comma(y)} - {_comma(x)}.",
        )
        misconceptions = {
            "ADD.WORD.CHANGE.ADD_INSTEAD": _comma(x + y),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: start unknown ---
    if family_code == "MATH.ADD.WORD.START_UNKNOWN":
        if difficulty == 2:
            start = rng.randint(10, 50)
            x = rng.randint(5, 30)
        elif difficulty == 3:
            start = rng.randint(50, 500)
            x = rng.randint(20, 200)
        else:
            start = rng.randint(100, 2_000)
            x = rng.randint(50, 1_000)
        y = start + x

        name = rng.choice(_NAMES)
        templates = [
            f"Some students were on the bus. {_comma(x)} more students got on. Now there are {_comma(y)} students. How many students were on the bus at first?",
            f"A bakery had some muffins in the display case. It added {_comma(x)} muffins. Now there are {_comma(y)} muffins. How many were there at first?",
            f"{name} had some money in a wallet. After earning ${_comma(x)}, {name} has ${_comma(y)}. How much did {name} have at first?",
            f"A fish tank had some fish. The store added {_comma(x)} fish. Now there are {_comma(y)} fish. How many fish were in the tank at first?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(start)
        hints = (
            "The unknown is the starting amount, not the amount added.",
            f"Start + {x} = {y}, so start = {_comma(y)} - {_comma(x)}.",
        )
        misconceptions = {
            "ADD.WORD.START.ADD_INSTEAD": _comma(x + y),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: combine ---
    if family_code == "MATH.ADD.WORD.COMBINE":
        if difficulty == 1:
            x = rng.randint(1, 10)
            y = rng.randint(1, 10)
        elif difficulty == 2:
            x = rng.randint(10, 50)
            y = rng.randint(10, 50)
        else:
            x = rng.randint(50, 500)
            y = rng.randint(50, 500)

        templates = [
            f"A jar has {_comma(x)} red marbles and {_comma(y)} blue marbles. How many marbles are there in all?",
            f"There are {_comma(x)} red cars and {_comma(y)} blue cars in the parking lot. How many cars are there total?",
            f"A basket contains {_comma(x)} green apples and {_comma(y)} red apples. How many apples are in the basket?",
            f"A class has {_comma(x)} girls and {_comma(y)} boys. How many students are in the class?",
            f"A garden has {_comma(x)} tulips and {_comma(y)} daisies. How many flowers are in the garden?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(x + y)
        hints = (
            "The word 'and' tells you to combine the two groups.",
            f"Add {_comma(x)} + {_comma(y)}.",
        )
        misconceptions = {
            "ADD.WORD.COMBINE.SUBTRACTED": _comma(abs(x - y)),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: comparison addition ---
    if family_code == "MATH.ADD.WORD.COMPARE":
        if difficulty == 2:
            x = rng.randint(10, 50)
            y = rng.randint(5, 30)
        elif difficulty == 3:
            x = rng.randint(50, 500)
            y = rng.randint(20, 200)
        else:
            x = rng.randint(100, 2_000)
            y = rng.randint(50, 1_000)

        name1, name2 = rng.sample(_NAMES, 2)
        templates = [
            f"{name1} has {_comma(x)} stickers. {name2} has {_comma(y)} more stickers than {name1}. How many stickers does {name2} have?",
            f"{name1} ran {_comma(x)} laps. {name2} ran {_comma(y)} more laps than {name1}. How many laps did {name2} run?",
            f"{name1} has ${_comma(x)}. {name2} has ${_comma(y)} more than {name1}. How much money does {name2} have?",
            f"{name1} read {_comma(x)} pages. {name2} read {_comma(y)} more pages than {name1}. How many pages did {name2} read?",
        ]
        prompt = rng.choice(templates)
        answer = _comma(x + y)
        hints = (
            f"'{y} more' means you add {y} to {name1}'s amount.",
            f"{_comma(x)} + {_comma(y)} = {_comma(x + y)}.",
        )
        misconceptions = {
            "ADD.WORD.COMPARE.SUBTRACTED": _comma(abs(x - y)),
        }
        return prompt, answer, hints, misconceptions

    # --- word problem: multi-step addition ---
    if family_code == "MATH.ADD.WORD.MULTISTEP":
        if difficulty == 3:
            x = rng.randint(10, 99)
            y = rng.randint(10, 99)
            z = rng.randint(10, 99)
        else:
            x = rng.randint(100, 999)
            y = rng.randint(100, 999)
            z = rng.randint(100, 999)

        total = x + y + z
        if difficulty == 3:
            templates = [
                f"A museum had {_comma(x)} visitors in the morning. {_comma(y)} more visitors came in the afternoon. Then {_comma(z)} more visitors came in the evening. How many visitors did the museum have altogether?",
                f"A truck delivered {_comma(x)} boxes in the morning, {_comma(y)} boxes in the afternoon, and {_comma(z)} boxes in the evening. How many boxes were delivered in all?",
                f"A school collected {_comma(x)} cans on Monday, {_comma(y)} cans on Tuesday, and {_comma(z)} cans on Wednesday. How many cans were collected total?",
            ]
            prompt = rng.choice(templates)
            misconceptions = {
                "ADD.WORD.MULTISTEP.TWO_ONLY": _comma(x + y),
            }
        else:
            irrelevant = rng.randint(10, 99)
            templates = [
                f"A museum had {_comma(x)} visitors in the morning, {_comma(y)} in the afternoon, and {_comma(z)} in the evening. The museum is open {irrelevant} hours today. How many visitors did the museum have altogether?",
                f"A truck delivered {_comma(x)} boxes in the morning, {_comma(y)} boxes in the afternoon, and {_comma(z)} boxes in the evening. The truck made {irrelevant} stops. How many boxes were delivered in all?",
                f"A school collected {_comma(x)} cans on Monday, {_comma(y)} cans on Tuesday, and {_comma(z)} cans on Wednesday. The collection drive lasts {irrelevant} days. How many cans were collected total?",
            ]
            prompt = rng.choice(templates)
            misconceptions = {
                "ADD.WORD.MULTISTEP.IRRELEVANT": _comma(total + irrelevant),
            }
        answer = _comma(total)
        hints = (
            "This problem needs more than one addition.",
            f"Add all three amounts: {_comma(x)} + {_comma(y)} + {_comma(z)}.",
        )
        return prompt, answer, hints, misconceptions

    # --- error analysis: regrouping mistake ---
    if family_code == "MATH.ADD.ERROR.REGROUP":
        if difficulty == 2:
            digits = 2
        elif difficulty == 3:
            digits = 3
        else:
            digits = 4

        a, b = _multidigit_pair(rng, digits, ensure_regroup=True)
        wrong = _fail_regroup_sum(a, b)
        name = rng.choice(["Alex", "Jordan", "Taylor", "Morgan", "Casey"])
        prompt = (
            f"{name} added {_comma(a)} + {_comma(b)} and got {_comma(wrong)}. "
            f"What mistake did {name} make? "
            "(A) Forgot to regroup/carry from one place to the next. "
            "(B) Added the wrong digits in the tens place. "
            "(C) Subtracted instead of added. "
            "(D) There is no mistake."
        )
        answer = "A"
        hints = (
            "Check each column starting from the ones place.",
            "When a column adds to 10 or more, you must regroup to the next place.",
        )
        misconceptions = {
            "ADD.ERROR.REGROUP.DISTRACTOR_B": "B",
            "ADD.ERROR.REGROUP.DISTRACTOR_C": "C",
            "ADD.ERROR.REGROUP.DISTRACTOR_D": "D",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")
