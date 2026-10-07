"""Canonical factors, multiples, GCF, LCM, prime/composite, divisibility families.

Covers: identifying factors, factor pairs, multiples, common factors,
common multiples, GCF, LCM, prime identification, composite identification,
prime factorization, divisibility rules, misconception probes, reasoning.
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


def _comma(n: int) -> str:
    return f"{n:,}"


def _factors(n: int) -> list[int]:
    """Return sorted list of all factors of *n*."""
    fs: set[int] = set()
    for i in range(1, int(n ** 0.5) + 1):
        if n % i == 0:
            fs.add(i)
            fs.add(n // i)
    return sorted(fs)


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def _lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b)


def _prime_factorization(n: int) -> list[int]:
    """Return prime factors of *n* in ascending order with repetition."""
    factors: list[int] = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.FAC.LIST_FACTORS": ProblemFamilySpec(
        "MATH.FAC.LIST_FACTORS", "List all factors of a number",
        "MATH.NS.FACTORS_MULTIPLES", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.FAC.FACTOR_PAIRS": ProblemFamilySpec(
        "MATH.FAC.FACTOR_PAIRS", "Find factor pairs of a number",
        "MATH.NS.FACTORS_MULTIPLES", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.FAC.IS_FACTOR": ProblemFamilySpec(
        "MATH.FAC.IS_FACTOR", "Determine if one number is a factor of another",
        "MATH.NS.FACTORS_MULTIPLES", "REASONING", 1, 3, ALL_MODES,
        frozenset({"reasoning", "number_sense"}),
    ),
    "MATH.FAC.LIST_MULTIPLES": ProblemFamilySpec(
        "MATH.FAC.LIST_MULTIPLES", "List multiples of a number",
        "MATH.NS.FACTORS_MULTIPLES", "NUMBER_SENSE", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "number_sense"}),
    ),
    "MATH.FAC.GCF": ProblemFamilySpec(
        "MATH.FAC.GCF", "Find the greatest common factor",
        "MATH.NS.GCF_LCM", "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "reasoning"}),
    ),
    "MATH.FAC.LCM": ProblemFamilySpec(
        "MATH.FAC.LCM", "Find the least common multiple",
        "MATH.NS.GCF_LCM", "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "reasoning"}),
    ),
    "MATH.FAC.PRIME_OR_COMPOSITE": ProblemFamilySpec(
        "MATH.FAC.PRIME_OR_COMPOSITE", "Classify a number as prime or composite",
        "MATH.NS.PRIME_COMPOSITE", "REASONING", 1, 3, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding", "number_sense"}),
    ),
    "MATH.FAC.PRIME_FACTORIZATION": ProblemFamilySpec(
        "MATH.FAC.PRIME_FACTORIZATION", "Find the prime factorization",
        "MATH.NS.PRIME_COMPOSITE", "NUMBER_SENSE", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "reasoning"}),
    ),
    "MATH.FAC.DIVISIBILITY": ProblemFamilySpec(
        "MATH.FAC.DIVISIBILITY", "Apply divisibility rules",
        "MATH.NS.DIVISIBILITY", "REASONING", 1, 3, ALL_MODES,
        frozenset({"reasoning", "number_sense", "conceptual_understanding"}),
    ),
    "MATH.FAC.DIVISIBILITY.WHY": ProblemFamilySpec(
        "MATH.FAC.DIVISIBILITY.WHY", "Explain why a divisibility rule works",
        "MATH.NS.DIVISIBILITY", "REASONING", 2, 4, ALL_MODES,
        frozenset({"reasoning", "conceptual_understanding"}),
    ),
    "MATH.FAC.GCF_WORD": ProblemFamilySpec(
        "MATH.FAC.GCF_WORD", "GCF word problem",
        "MATH.NS.GCF_LCM", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.FAC.LCM_WORD": ProblemFamilySpec(
        "MATH.FAC.LCM_WORD", "LCM word problem",
        "MATH.NS.GCF_LCM", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "transfer"}),
    ),
    "MATH.FAC.ERROR.PRIME_ONE": ProblemFamilySpec(
        "MATH.FAC.ERROR.PRIME_ONE", "Misconception probe: is 1 prime?",
        "MATH.NS.PRIME_COMPOSITE", "ERROR_ANALYSIS", 1, 3, ALL_MODES,
        frozenset({"misconception_probe", "error_analysis", "reasoning"}),
    ),
    "MATH.FAC.ERROR.FACTOR_MULTIPLE": ProblemFamilySpec(
        "MATH.FAC.ERROR.FACTOR_MULTIPLE", "Error: factor/multiple confusion",
        "MATH.NS.FACTORS_MULTIPLES", "ERROR_ANALYSIS", 2, 3, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):

    # --- list factors ---
    if family_code == "MATH.FAC.LIST_FACTORS":
        pools = {1: range(6, 25), 2: range(12, 50), 3: range(20, 80)}
        n = rng.choice(list(pools.get(difficulty, pools[1])))
        fs = _factors(n)
        prompt = f"List all factors of {n}."
        answer = ", ".join(str(f) for f in fs)
        hints = (
            "Start with 1 and the number itself.",
            "Check each number from 2 upward to see if it divides evenly.",
        )
        # Misconception: include a non-factor
        wrong_factor = n + 1
        misconceptions = {
            "FAC.LIST.INCLUDE_NON": ", ".join(str(f) for f in fs[:-1]) + f", {wrong_factor}",
        }
        return prompt, answer, hints, misconceptions

    # --- factor pairs ---
    if family_code == "MATH.FAC.FACTOR_PAIRS":
        pools = {1: range(6, 20), 2: range(12, 36), 3: range(20, 60)}
        n = rng.choice(list(pools.get(difficulty, pools[1])))
        fs = _factors(n)
        pairs = [(a, n // a) for a in fs if a <= n // a]
        pairs_str = ", ".join(f"({a}, {b})" for a, b in pairs)
        prompt = f"Find all factor pairs of {n}."
        answer = pairs_str
        hints = (
            "A factor pair is two numbers that multiply to give the number.",
            f"Start with (1, {n}). Then try (2, ?).",
        )
        misconceptions = {
            "FAC.PAIRS.MISS_ONE": ", ".join(f"({a}, {b})" for a, b in pairs[1:]) if len(pairs) > 1 else pairs_str,
        }
        return prompt, answer, hints, misconceptions

    # --- is factor ---
    if family_code == "MATH.FAC.IS_FACTOR":
        n = rng.randint(10 + difficulty * 5, 30 + difficulty * 20)
        candidate = rng.choice(_factors(n)) if rng.random() < 0.5 else rng.randint(2, n - 1)
        is_fac = n % candidate == 0
        prompt = (
            f"Is {candidate} a factor of {n}? Answer Yes or No."
        )
        answer = "Yes" if is_fac else "No"
        hints = (
            f"Divide {n} by {candidate}. Is there a remainder?",
            f"{n} ÷ {candidate} = {n / candidate:.2g}.",
        )
        misconceptions = {
            "FAC.IS.REVERSED": "No" if is_fac else "Yes",
        }
        return prompt, answer, hints, misconceptions

    # --- list multiples ---
    if family_code == "MATH.FAC.LIST_MULTIPLES":
        base = rng.randint(2, 5 + difficulty * 3)
        count = 5 + difficulty
        multiples = [base * i for i in range(1, count + 1)]
        prompt = f"List the first {count} multiples of {base}."
        answer = ", ".join(str(m) for m in multiples)
        hints = (
            f"Multiply {base} by 1, 2, 3, ...",
            f"The first multiple is {base} × 1 = {base}.",
        )
        misconceptions = {
            "FAC.MUL.START_ZERO": ", ".join(str(m) for m in [0] + multiples[:-1]),
        }
        return prompt, answer, hints, misconceptions

    # --- GCF ---
    if family_code == "MATH.FAC.GCF":
        gcf_val = rng.randint(2, 4 + difficulty * 2)
        m1 = rng.randint(2, 4 + difficulty)
        m2 = rng.randint(2, 4 + difficulty)
        while m1 == m2 or gcd(m1, m2) > 1:
            m2 = rng.randint(2, 4 + difficulty)
        a, b = gcf_val * m1, gcf_val * m2
        prompt = f"Find the GCF of {a} and {b}."
        answer = str(gcf_val)
        hints = (
            f"List the factors of {a} and {b}.",
            "Find the largest number that appears in both lists.",
        )
        misconceptions = {
            "FAC.GCF.USE_LCM": str(_lcm(a, b)),
        }
        return prompt, answer, hints, misconceptions

    # --- LCM ---
    if family_code == "MATH.FAC.LCM":
        a = rng.randint(2, 5 + difficulty * 2)
        b = rng.randint(2, 5 + difficulty * 2)
        while a == b:
            b = rng.randint(2, 5 + difficulty * 2)
        lcm_val = _lcm(a, b)
        prompt = f"Find the LCM of {a} and {b}."
        answer = str(lcm_val)
        hints = (
            f"List multiples of {a}: {a}, {a * 2}, {a * 3}, ...",
            f"List multiples of {b}: {b}, {b * 2}, {b * 3}, ...",
            "Find the smallest number that appears in both lists.",
        )
        misconceptions = {
            "FAC.LCM.USE_PRODUCT": str(a * b),
        }
        return prompt, answer, hints, misconceptions

    # --- prime or composite ---
    if family_code == "MATH.FAC.PRIME_OR_COMPOSITE":
        pools = {1: range(2, 20), 2: range(2, 50), 3: range(2, 100)}
        n = rng.choice(list(pools.get(difficulty, pools[1])))
        is_p = _is_prime(n)
        prompt = f"Is {n} prime or composite?"
        answer = "Prime" if is_p else "Composite"
        hints = (
            "A prime number has exactly two factors: 1 and itself.",
            f"Try dividing {n} by small primes: 2, 3, 5, 7.",
        )
        misconceptions = {
            "FAC.PRIME.REVERSED": "Composite" if is_p else "Prime",
        }
        return prompt, answer, hints, misconceptions

    # --- prime factorization ---
    if family_code == "MATH.FAC.PRIME_FACTORIZATION":
        pools = {2: range(12, 40), 3: range(20, 80), 4: range(40, 150)}
        n = rng.choice(list(pools.get(difficulty, pools[2])))
        while _is_prime(n):
            n += 1
        pf = _prime_factorization(n)
        pf_str = " × ".join(str(p) for p in pf)
        prompt = f"Find the prime factorization of {n}."
        answer = pf_str
        hints = (
            f"Start by dividing {n} by the smallest prime, 2.",
            "Keep dividing until all factors are prime.",
        )
        # Wrong: include 1
        misconceptions = {
            "FAC.PF.INCLUDE_ONE": "1 × " + pf_str,
        }
        return prompt, answer, hints, misconceptions

    # --- divisibility ---
    if family_code == "MATH.FAC.DIVISIBILITY":
        divisors = [2, 3, 5, 9, 10][:3 + min(difficulty, 2)]
        d = rng.choice(divisors)
        # Half the time make it divisible, half not
        if rng.random() < 0.5:
            base = rng.randint(10 + difficulty * 5, 50 + difficulty * 20)
            n = base * d
        else:
            n = rng.randint(10 + difficulty * 5, 200 + difficulty * 50)
            while n % d == 0:
                n += 1
        is_div = n % d == 0
        prompt = f"Is {_comma(n)} divisible by {d}? Answer Yes or No."
        answer = "Yes" if is_div else "No"
        rule_hints = {
            2: "A number is divisible by 2 if its last digit is even.",
            3: "A number is divisible by 3 if the sum of its digits is divisible by 3.",
            5: "A number is divisible by 5 if it ends in 0 or 5.",
            9: "A number is divisible by 9 if the sum of its digits is divisible by 9.",
            10: "A number is divisible by 10 if it ends in 0.",
        }
        hints = (
            rule_hints.get(d, f"Try dividing {_comma(n)} by {d}."),
            f"{_comma(n)} ÷ {d} = {n / d:.2g}.",
        )
        misconceptions = {
            "FAC.DIV.REVERSED": "No" if is_div else "Yes",
        }
        return prompt, answer, hints, misconceptions

    # --- divisibility reasoning ---
    if family_code == "MATH.FAC.DIVISIBILITY.WHY":
        scenarios = [
            (3, "sum of digits"),
            (9, "sum of digits"),
            (2, "last digit is even"),
            (5, "last digit is 0 or 5"),
        ]
        d, rule_desc = rng.choice(scenarios[:2 + min(difficulty, 2)])
        n = rng.randint(100, 500 + difficulty * 200) * d
        digit_sum = sum(int(ch) for ch in str(n))
        prompt = (
            f"Why is {_comma(n)} divisible by {d}? "
            f"(A) Because the {rule_desc} is divisible by {d}. "
            f"(B) Because {_comma(n)} is even. "
            f"(C) Because {_comma(n)} ends in {d}. "
            f"(D) Because {_comma(n)} is greater than {d}."
        )
        answer = "A"
        hints = (
            f"The divisibility rule for {d} involves the {rule_desc}.",
            f"The sum of the digits of {_comma(n)} is {digit_sum}.",
        )
        misconceptions = {
            "FAC.DIV_WHY.GREATER_THAN": "D",
        }
        return prompt, answer, hints, misconceptions

    # --- GCF word problem ---
    if family_code == "MATH.FAC.GCF_WORD":
        gcf_val = rng.randint(3, 5 + difficulty * 2)
        m1, m2 = rng.randint(2, 4 + difficulty), rng.randint(2, 4 + difficulty)
        while m1 == m2 or gcd(m1, m2) > 1:
            m2 = rng.randint(2, 4 + difficulty)
        a, b = gcf_val * m1, gcf_val * m2
        contexts = [
            (f"You have {a} red beads and {b} blue beads. "
             "You want to make identical gift bags with no beads left over. "
             "What is the greatest number of bags you can make?"),
            (f"A florist has {a} roses and {b} lilies. "
             "She wants to make identical bouquets with no flowers left over. "
             "What is the greatest number of bouquets?"),
        ]
        prompt = rng.choice(contexts)
        answer = str(gcf_val)
        hints = (
            f"Find the GCF of {a} and {b}.",
            "The GCF tells you the most equal groups you can make.",
        )
        misconceptions = {
            "FAC.GCF_WORD.USE_LCM": str(_lcm(a, b)),
            "FAC.GCF_WORD.USE_SMALLER": str(min(a, b)),
        }
        return prompt, answer, hints, misconceptions

    # --- LCM word problem ---
    if family_code == "MATH.FAC.LCM_WORD":
        a = rng.randint(2, 4 + difficulty * 2)
        b = rng.randint(3, 5 + difficulty * 2)
        while a == b:
            b = rng.randint(3, 5 + difficulty * 2)
        lcm_val = _lcm(a, b)
        contexts = [
            (f"Train A departs every {a} minutes. Train B departs every {b} minutes. "
             "Both leave the station at noon. "
             "After how many minutes will they next depart at the same time?"),
            (f"Hot dogs come in packs of {a}. Buns come in packs of {b}. "
             "What is the least number of each you must buy so you have the same number?"),
        ]
        prompt = rng.choice(contexts)
        answer = str(lcm_val)
        hints = (
            f"Find the LCM of {a} and {b}.",
            "List multiples of each number until you find a common one.",
        )
        misconceptions = {
            "FAC.LCM_WORD.USE_GCF": str(gcd(a, b)),
            "FAC.LCM_WORD.USE_PRODUCT": str(a * b),
        }
        return prompt, answer, hints, misconceptions

    # --- error: is 1 prime? ---
    if family_code == "MATH.FAC.ERROR.PRIME_ONE":
        names = ["Maya", "Ben", "Zara", "Leo", "Priya"]
        name = rng.choice(names)
        prompt = (
            f"{name} says 1 is a prime number because it is only divisible by 1 and itself. "
            f"Is {name} correct? "
            f"(A) No — 1 is neither prime nor composite. "
            f"(B) Yes — 1 is prime. "
            f"(C) 1 is composite."
        )
        answer = "A"
        hints = (
            "A prime number must have exactly two distinct factors.",
            "1 has only one factor: itself.",
        )
        misconceptions = {
            "FAC.PRIME_ONE.IS_PRIME": "B",
        }
        return prompt, answer, hints, misconceptions

    # --- error: factor/multiple confusion ---
    if family_code == "MATH.FAC.ERROR.FACTOR_MULTIPLE":
        a = rng.randint(2, 5 + difficulty)
        b = a * rng.randint(2, 4 + difficulty)
        names = ["Jordan", "Alex", "Taylor", "Sam"]
        name = rng.choice(names)
        prompt = (
            f"{name} says {b} is a factor of {a}. Is {name} correct? "
            f"(A) No — {b} is a multiple of {a}, not a factor. "
            f"(B) Yes — {b} is a factor of {a}. "
            f"(C) They are neither factors nor multiples of each other."
        )
        answer = "A"
        hints = (
            f"A factor of {a} must divide {a} evenly.",
            f"Since {b} > {a}, {b} cannot be a factor of {a}.",
        )
        misconceptions = {
            "FAC.ERROR.CONFUSED": "B",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"No builder for family: {family_code}")
