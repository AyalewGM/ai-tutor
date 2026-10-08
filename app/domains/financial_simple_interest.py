"""Original canonical simple-interest word problems."""

import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec

CODE = "MATH.FIN.INTEREST.SIMPLE"
FAMILIES = {
    CODE: ProblemFamilySpec(
        CODE, "Calculate simple interest", "MATH.FIN.INTEREST",
        "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"financial_literacy", "percent_reasoning", "modeling"}),
    ),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code != CODE:
        raise ValueError(f"Unknown family: {family_code}")
    principal = 100 * rng.randint(2, 5 + difficulty)
    rate = rng.choice((5, 10, 20))
    years = rng.randint(2, 2 + difficulty)
    interest = principal * rate * years // 100
    return (
        f"A deposit of {principal} dollars earns {rate}% simple interest "
        f"annually for {years} years. How many dollars of interest are earned?",
        str(interest),
        ("Use the original principal each year.", "Multiply principal, rate, and years."),
        {"FIN.INTEREST.REPORT_BALANCE": str(principal + interest)},
    )
