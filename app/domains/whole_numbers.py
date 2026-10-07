"""Canonical whole-number foundations problem families.

Covers: counting, number recognition, sequencing, before/after/between,
comparing, ordering, number magnitude, number lines,
composing/decomposing, expanded form, standard form.
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


def _expanded(n: int) -> str:
    """Return expanded-form string for *n*, e.g. 5000 + 300 + 20 + 4."""
    if n == 0:
        return "0"
    parts: list[str] = []
    s = str(n)
    length = len(s)
    for i, ch in enumerate(s):
        digit = int(ch)
        if digit == 0:
            continue
        place_val = 10 ** (length - 1 - i)
        parts.append(str(digit * place_val))
    return " + ".join(parts) if parts else "0"


def _word_form(n: int) -> str:
    """Simple word form for numbers 0-999,999.  Sufficient for pedagogical use."""
    if n == 0:
        return "zero"
    ones = ["", "one", "two", "three", "four", "five", "six", "seven",
            "eight", "nine", "ten", "eleven", "twelve", "thirteen",
            "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
            "nineteen"]
    tens_words = ["", "", "twenty", "thirty", "forty", "fifty", "sixty",
                  "seventy", "eighty", "ninety"]

    def _under_1000(x: int) -> str:
        if x == 0:
            return ""
        if x < 20:
            return ones[x]
        if x < 100:
            t, o = divmod(x, 10)
            return tens_words[t] + ("-" + ones[o] if o else "")
        h, rest = divmod(x, 100)
        base = ones[h] + " hundred"
        if rest:
            return base + " " + _under_1000(rest)
        return base

    parts: list[str] = []
    if n >= 1_000_000:
        m, n = divmod(n, 1_000_000)
        parts.append(_under_1000(m) + " million")
    if n >= 1000:
        t, n = divmod(n, 1000)
        parts.append(_under_1000(t) + " thousand")
    tail = _under_1000(n)
    if tail:
        parts.append(tail)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    # --- Counting & sequencing ---
    "MATH.WN.COUNT.FORWARD": ProblemFamilySpec(
        "MATH.WN.COUNT.FORWARD", "Count forward from a given number",
        "MATH.NS.COUNTING", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.WN.COUNT.BACKWARD": ProblemFamilySpec(
        "MATH.WN.COUNT.BACKWARD", "Count backward from a given number",
        "MATH.NS.COUNTING", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.WN.COUNT.SKIP": ProblemFamilySpec(
        "MATH.WN.COUNT.SKIP", "Skip-count by a given number",
        "MATH.NS.COUNTING", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense", "reasoning"}),
    ),
    "MATH.WN.SEQUENCE.NEXT": ProblemFamilySpec(
        "MATH.WN.SEQUENCE.NEXT", "Find the next number in a sequence",
        "MATH.NS.COUNTING", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"reasoning", "number_sense"}),
    ),
    "MATH.WN.BETWEEN": ProblemFamilySpec(
        "MATH.WN.BETWEEN", "Identify number between two given numbers",
        "MATH.NS.COUNTING", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"number_sense", "reasoning"}),
    ),
    # --- Comparing & ordering ---
    "MATH.WN.COMPARE": ProblemFamilySpec(
        "MATH.WN.COMPARE", "Compare two whole numbers",
        "MATH.NS.COMPARE_ORDER", "COMPARISON", 1, 4, ALL_MODES,
        frozenset({"comparison", "number_sense", "conceptual_understanding"}),
    ),
    "MATH.WN.ORDER": ProblemFamilySpec(
        "MATH.WN.ORDER", "Order whole numbers from least to greatest",
        "MATH.NS.COMPARE_ORDER", "COMPARISON", 1, 4, ALL_MODES,
        frozenset({"comparison", "number_sense"}),
    ),
    # --- Number line ---
    "MATH.WN.NUMBERLINE": ProblemFamilySpec(
        "MATH.WN.NUMBERLINE", "Identify a value on a number line",
        "MATH.NS.NUMBER_LINE", "REPRESENTATION", 1, 3, ALL_MODES,
        frozenset({"representation", "number_sense", "conceptual_understanding"}),
    ),
    # --- Compose/decompose ---
    "MATH.WN.COMPOSE": ProblemFamilySpec(
        "MATH.WN.COMPOSE", "Compose a number from place-value parts",
        "MATH.NS.COMPOSE_DECOMPOSE", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"conceptual_understanding", "number_sense"}),
    ),
    "MATH.WN.DECOMPOSE": ProblemFamilySpec(
        "MATH.WN.DECOMPOSE", "Decompose a number into place-value parts",
        "MATH.NS.COMPOSE_DECOMPOSE", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"conceptual_understanding", "number_sense"}),
    ),
    # --- Expanded form ---
    "MATH.WN.EXPANDED": ProblemFamilySpec(
        "MATH.WN.EXPANDED", "Write a number in expanded form",
        "MATH.NS.EXPANDED_FORM", "REPRESENTATION", 1, 4, ALL_MODES,
        frozenset({"representation", "conceptual_understanding", "number_sense"}),
    ),
    "MATH.WN.STANDARD_FROM_EXPANDED": ProblemFamilySpec(
        "MATH.WN.STANDARD_FROM_EXPANDED", "Write standard form from expanded form",
        "MATH.NS.EXPANDED_FORM", "REPRESENTATION", 1, 4, ALL_MODES,
        frozenset({"representation", "conceptual_understanding"}),
    ),
    # --- Word form ---
    "MATH.WN.WORD_TO_STANDARD": ProblemFamilySpec(
        "MATH.WN.WORD_TO_STANDARD", "Convert word form to standard form",
        "MATH.NS.WORD_FORM", "CONVERSION", 1, 3, ALL_MODES,
        frozenset({"representation", "number_sense"}),
    ),
    # --- Error analysis ---
    "MATH.WN.ERROR.COMPARE": ProblemFamilySpec(
        "MATH.WN.ERROR.COMPARE", "Error analysis: comparison mistake",
        "MATH.NS.COMPARE_ORDER", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _num_range(difficulty: int, base_lo: int = 1, scale: int = 10) -> tuple[int, int]:
    """Return (lo, hi) scaled by difficulty."""
    return base_lo, base_lo + scale * (10 ** difficulty)


def build(family_code: str, rng: random.Random, difficulty: int):
    """Return (prompt, answer, hints, misconceptions) for *family_code*."""

    # --- count forward ---
    if family_code == "MATH.WN.COUNT.FORWARD":
        lo, hi = _num_range(difficulty, 1, 8)
        start = rng.randint(lo, hi)
        count = rng.randint(3, 5 + difficulty)
        nums = [start + i for i in range(count)]
        prompt = f"Count forward {count} numbers starting from {_comma(start)}."
        answer = ", ".join(_comma(n) for n in nums)
        hints = (
            f"Start at {_comma(start)} and add 1 each time.",
            f"The first three are {_comma(nums[0])}, {_comma(nums[1])}, {_comma(nums[2])}.",
        )
        misconceptions = {
            "WN.COUNT.SKIP_ONE": ", ".join(_comma(n) for n in [start + i + 1 for i in range(count)]),
        }
        return prompt, answer, hints, misconceptions

    # --- count backward ---
    if family_code == "MATH.WN.COUNT.BACKWARD":
        lo, hi = _num_range(difficulty, 5, 8)
        start = rng.randint(max(lo, 5 + difficulty), hi)
        count = rng.randint(3, 4 + difficulty)
        start = max(start, count)  # ensure we don't go negative
        nums = [start - i for i in range(count)]
        prompt = f"Count backward {count} numbers starting from {_comma(start)}."
        answer = ", ".join(_comma(n) for n in nums)
        hints = (
            f"Start at {_comma(start)} and subtract 1 each time.",
            f"After {_comma(start)} comes {_comma(start - 1)}.",
        )
        misconceptions = {
            "WN.COUNT.FORWARD_INSTEAD": ", ".join(_comma(n) for n in [start + i for i in range(count)]),
        }
        return prompt, answer, hints, misconceptions

    # --- skip counting ---
    if family_code == "MATH.WN.COUNT.SKIP":
        skips = [2, 5, 10] if difficulty <= 1 else [2, 3, 5, 10, 25]
        if difficulty >= 3:
            skips.extend([4, 6, 100])
        skip = rng.choice(skips)
        start = rng.randint(0, 3) * skip
        count = rng.randint(4, 6 + difficulty)
        nums = [start + skip * i for i in range(count)]
        prompt = f"Skip-count by {skip}s starting from {_comma(start)}. Write the next {count} numbers."
        answer = ", ".join(_comma(n) for n in nums)
        hints = (
            f"Each number is {skip} more than the last.",
            f"After {_comma(nums[0])}: {_comma(nums[1])}, {_comma(nums[2])}, ...",
        )
        wrong_skip = skip + 1 if skip < 10 else skip - 1
        misconceptions = {
            "WN.SKIP.WRONG_INCREMENT": ", ".join(_comma(start + wrong_skip * i) for i in range(count)),
        }
        return prompt, answer, hints, misconceptions

    # --- sequence next ---
    if family_code == "MATH.WN.SEQUENCE.NEXT":
        step = rng.randint(2, 5 + difficulty * 3)
        start = rng.randint(1, 10 + difficulty * 10)
        seq = [start + step * i for i in range(4)]
        answer_val = start + step * 4
        prompt = f"What comes next? {', '.join(_comma(n) for n in seq)}, ?"
        answer = _comma(answer_val)
        hints = (
            "Find the difference between consecutive numbers.",
            f"Each number increases by {step}.",
        )
        misconceptions = {
            "WN.SEQ.ADD_LAST": _comma(seq[-1] + seq[-2]),
        }
        return prompt, answer, hints, misconceptions

    # --- between ---
    if family_code == "MATH.WN.BETWEEN":
        lo, hi = _num_range(difficulty, 1, 8)
        a = rng.randint(lo, hi - 2)
        b = a + 2
        mid = a + 1
        prompt = f"What number is between {_comma(a)} and {_comma(b)}?"
        answer = _comma(mid)
        hints = (
            f"Find the number that is one more than {_comma(a)}.",
            f"It is also one less than {_comma(b)}.",
        )
        misconceptions = {
            "WN.BETWEEN.PICK_ENDPOINT": _comma(a),
        }
        return prompt, answer, hints, misconceptions

    # --- compare ---
    if family_code == "MATH.WN.COMPARE":
        lo, hi = _num_range(difficulty, 1, 50)
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        while a == b:
            b = rng.randint(lo, hi)
        prompt = f"Compare {_comma(a)} and {_comma(b)}. Which is greater?"
        answer = _comma(max(a, b))
        hints = (
            "Look at the number of digits first. More digits means a larger number.",
            "If they have the same number of digits, compare from left to right.",
        )
        # Misconception: student picks the one with more digits or first digit confusion
        misconceptions = {
            "WN.COMPARE.PICK_SMALLER": _comma(min(a, b)),
        }
        return prompt, answer, hints, misconceptions

    # --- order ---
    if family_code == "MATH.WN.ORDER":
        lo, hi = _num_range(difficulty, 1, 50)
        count = 4 + min(difficulty, 2)
        nums: list[int] = []
        while len(nums) < count:
            n = rng.randint(lo, hi)
            if n not in nums:
                nums.append(n)
        sorted_nums = sorted(nums)
        prompt = f"Order from least to greatest: {', '.join(_comma(n) for n in nums)}."
        answer = ", ".join(_comma(n) for n in sorted_nums)
        hints = (
            "Find the smallest number first.",
            f"The smallest is {_comma(sorted_nums[0])}.",
        )
        misconceptions = {
            "WN.ORDER.REVERSED": ", ".join(_comma(n) for n in sorted_nums[::-1]),
        }
        return prompt, answer, hints, misconceptions

    # --- number line ---
    if family_code == "MATH.WN.NUMBERLINE":
        step = rng.choice([1, 2, 5, 10, 25, 50, 100][:3 + difficulty])
        start = rng.randint(0, 5) * step
        tick_count = rng.randint(5, 8)
        target_idx = rng.randint(1, tick_count - 1)
        target = start + step * target_idx
        endpoints = f"{_comma(start)} to {_comma(start + step * tick_count)}"
        prompt = (
            f"A number line goes from {endpoints} with equal intervals. "
            f"What number is at the {_ordinal(target_idx + 1)} tick mark?"
        )
        answer = _comma(target)
        hints = (
            f"The number line is divided into {tick_count} equal intervals.",
            f"Each interval is {_comma(step)} units.",
        )
        misconceptions = {
            "WN.NUMLINE.COUNT_FROM_ONE": _comma(start + step * (target_idx + 1)),
        }
        return prompt, answer, hints, misconceptions

    # --- compose ---
    if family_code == "MATH.WN.COMPOSE":
        digits_count = 2 + min(difficulty, 3)
        number = rng.randint(10 ** (digits_count - 1), 10 ** digits_count - 1)
        expanded = _expanded(number)
        prompt = f"What number is {expanded}?"
        answer = _comma(number)
        hints = (
            "Add all the place values together.",
            f"The largest place value is {str(number)[0]}{'0' * (len(str(number)) - 1)}.",
        )
        # swap two place values
        s = str(number)
        if len(s) >= 2:
            swapped = s[-1] + s[1:-1] + s[0] if len(s) > 2 else s[1] + s[0]
            wrong = int(swapped)
        else:
            wrong = number + 1
        misconceptions = {
            "WN.COMPOSE.SWAP_PLACES": _comma(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- decompose ---
    if family_code == "MATH.WN.DECOMPOSE":
        digits_count = 2 + min(difficulty, 3)
        number = rng.randint(10 ** (digits_count - 1), 10 ** digits_count - 1)
        prompt = f"Decompose {_comma(number)} into its place-value parts."
        answer = _expanded(number)
        hints = (
            "Write each digit multiplied by its place value.",
            "The leftmost digit has the highest place value.",
        )
        # Misconception: list digits instead of values
        digits_only = " + ".join(str(int(ch)) for ch in str(number) if ch != "0")
        misconceptions = {
            "WN.DECOMPOSE.DIGITS_ONLY": digits_only if digits_only != answer else str(number),
        }
        return prompt, answer, hints, misconceptions

    # --- expanded form ---
    if family_code == "MATH.WN.EXPANDED":
        digits_count = 2 + difficulty
        number = rng.randint(10 ** (digits_count - 1), 10 ** digits_count - 1)
        # Ensure at least one zero digit for higher difficulty
        if difficulty >= 2:
            s = list(str(number))
            zero_pos = rng.randint(1, len(s) - 1)
            s[zero_pos] = "0"
            number = int("".join(s))
            if number < 10 ** (digits_count - 1):
                number += 10 ** (digits_count - 1)
        prompt = f"Write {_comma(number)} in expanded form."
        answer = _expanded(number)
        hints = (
            "Break the number into the value of each digit.",
            "Multiply each digit by its place value (ones, tens, hundreds, ...).",
        )
        # Misconception: use digit values not place values
        misconceptions = {
            "WN.EXPANDED.DIGIT_ONLY": " + ".join(ch for ch in str(number) if ch != "0"),
        }
        return prompt, answer, hints, misconceptions

    # --- standard from expanded ---
    if family_code == "MATH.WN.STANDARD_FROM_EXPANDED":
        digits_count = 2 + difficulty
        number = rng.randint(10 ** (digits_count - 1), 10 ** digits_count - 1)
        expanded = _expanded(number)
        prompt = f"Write {expanded} in standard form."
        answer = _comma(number)
        hints = (
            "Add all the values together.",
            "Start with the largest place value and combine.",
        )
        wrong = number + 10 ** (rng.randint(0, digits_count - 2))
        misconceptions = {
            "WN.STANDARD.ADDITION_ERROR": _comma(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- word to standard ---
    if family_code == "MATH.WN.WORD_TO_STANDARD":
        digits_count = 2 + difficulty
        number = rng.randint(10 ** (digits_count - 1), 10 ** digits_count - 1)
        wf = _word_form(number)
        prompt = f"Write {wf} in standard form."
        answer = _comma(number)
        hints = (
            "Break the word form into place values.",
            "Think about how many thousands, hundreds, tens, and ones.",
        )
        # Wrong: off by a factor of 10
        wrong = number * 10 if number < 100_000 else number // 10
        misconceptions = {
            "WN.WORD.PLACE_SHIFT": _comma(wrong),
        }
        return prompt, answer, hints, misconceptions

    # --- error analysis: comparison ---
    if family_code == "MATH.WN.ERROR.COMPARE":
        lo, hi = _num_range(difficulty, 10, 50)
        # Create a pair where digit count or leading digit is misleading
        # e.g. 89 vs 102 — student might pick 89 because "8 > 1"
        bigger = rng.randint(lo + 10, hi)
        smaller = rng.randint(lo, bigger - 1)
        # Ensure different digit counts at higher difficulty
        if difficulty >= 3 and len(str(bigger)) == len(str(smaller)):
            bigger = bigger * 10 + rng.randint(0, 9)
        names = ["Emma", "Liam", "Aisha", "Carlos", "Mei"]
        name = rng.choice(names)
        prompt = (
            f"{name} says {_comma(smaller)} is greater than {_comma(bigger)} "
            f"because the first digit {str(smaller)[0]} is larger than {str(bigger)[0]}. "
            f"Is {name} correct? "
            f"(A) No — {_comma(bigger)} is greater because it has more digits or a larger overall value. "
            f"(B) Yes — the first digit determines which number is greater. "
            f"(C) They are equal."
        )
        answer = "A"
        hints = (
            "Compare the number of digits first.",
            f"{_comma(bigger)} has {len(str(bigger))} digits while {_comma(smaller)} has {len(str(smaller))} digits.",
            "A number with more digits is always greater.",
        )
        misconceptions = {
            "WN.ERROR.FIRST_DIGIT_ONLY": "B",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")


def _ordinal(n: int) -> str:
    """Return ordinal string for *n* (1st, 2nd, 3rd, etc.)."""
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    return f"{n}{suffixes.get(n % 10, 'th')}"
