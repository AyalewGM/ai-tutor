"""Original canonical fixed-fee budgeting and remainder interpretation."""

import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec

CODE = "MATH.FIN.BUDGET.CAPACITY"
FAMILIES = {CODE: ProblemFamilySpec(
    CODE, "Maximum affordable activities with a fixed fee", "MATH.FIN.BUDGETING",
    "WORD_PROBLEM", 2, 4, ALL_MODES,
    frozenset({"financial_literacy", "division_with_remainder", "modeling"}),
)}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code != CODE:
        raise ValueError(f"Unknown family: {family_code}")
    cost = rng.randint(5, 12 + difficulty)
    fee = cost * rng.randint(2, 5)
    visits = rng.randint(3, 7 + difficulty)
    remainder = rng.randint(1, cost - 1)
    budget = fee + cost * visits + remainder
    return (
        f"A center charges {fee} dollars to join and {cost} dollars per visit. "
        f"With {budget} dollars, what is the maximum whole number of visits?",
        str(visits),
        ("Subtract the joining fee first.", "Divide by the visit cost and round down."),
        {"FIN.BUDGET.IGNORE_FEE": str(budget // cost),
         "FIN.BUDGET.ROUND_UP": str(visits + 1)},
    )
