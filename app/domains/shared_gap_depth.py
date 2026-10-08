"""Curriculum-neutral Mihur-authored content for shared state gap signals."""

from __future__ import annotations

import math
import random
from fractions import Fraction

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(
    code: str, name: str, skill: str, kind: str, minimum: int, *dimensions: str
) -> ProblemFamilySpec:
    return ProblemFamilySpec(
        code, name, skill, kind, minimum, 4, ALL_MODES, frozenset(dimensions)
    )


FAMILIES = {
    "MATH.DATA.MAD.COMPUTE": _spec(
        "MATH.DATA.MAD.COMPUTE", "Mean absolute deviation",
        "MATH.DATA.SPREAD", "DATA_ANALYSIS", 2, "data_reasoning", "procedural_fluency",
    ),
    "MATH.DATA.MAD.COMPARE": _spec(
        "MATH.DATA.MAD.COMPARE", "Compare variability using MAD",
        "MATH.DATA.SPREAD", "DATA_REASONING", 2, "data_reasoning", "comparison",
    ),
    "MATH.NS.IRRATIONAL.CLASSIFY": _spec(
        "MATH.NS.IRRATIONAL.CLASSIFY", "Classify square roots",
        "MATH.NS.IRRATIONAL", "CLASSIFICATION", 2,
        "number_sense", "conceptual_understanding",
    ),
    "MATH.NS.IRRATIONAL.APPROX": _spec(
        "MATH.NS.IRRATIONAL.APPROX", "Approximate irrational square roots",
        "MATH.NS.IRRATIONAL", "NUMERIC_APPROXIMATION", 3,
        "number_sense", "estimation",
    ),
    "MATH.FIN.UNIT_PRICE": _spec(
        "MATH.FIN.UNIT_PRICE", "Compare unit prices",
        "MATH.FIN.UNIT_RATES", "WORD_PROBLEM", 2,
        "proportional_reasoning", "financial_literacy",
    ),
    "MATH.FIN.BUDGET": _spec(
        "MATH.FIN.BUDGET", "Balance a simple budget",
        "MATH.FIN.BUDGETING", "WORD_PROBLEM", 1,
        "arithmetic", "financial_literacy",
    ),
    "MATH.FIN.SAVINGS_GOAL": _spec(
        "MATH.FIN.SAVINGS_GOAL", "Weeks to reach a savings goal",
        "MATH.FIN.BUDGETING", "WORD_PROBLEM", 2,
        "division_with_remainder", "financial_literacy",
    ),
    "MATH.FIN.DISCOUNT": _spec(
        "MATH.FIN.DISCOUNT", "Calculate a percentage discount",
        "MATH.FIN.PERCENT", "WORD_PROBLEM", 3,
        "percent_reasoning", "financial_literacy",
    ),
}


def _money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d} dollars"


def _nearest_tenth_of_sqrt(n: int) -> int:
    """Ten times sqrt(n), rounded to nearest tenth using integer arithmetic."""
    floor = math.isqrt(100 * n)
    return floor + int(400 * n >= (2 * floor + 1) ** 2)


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.DATA.MAD.COMPUTE":
        count = 2 if difficulty <= 2 else 3
        distances = [rng.randint(1, 2 + difficulty * 2) for _ in range(count)]
        center = max(distances) + rng.randint(3, 15)
        values = [value for d in distances for value in (center - d, center + d)]
        rng.shuffle(values)
        return (
            (f"Data values: {', '.join(map(str, values))}. "
            "Find the mean absolute deviation (MAD). Give an integer or simplified fraction."),
            str(Fraction(sum(distances), count)),
            (
                "First calculate the arithmetic mean of the data.",
                "Find each absolute distance from the mean, then average those distances.",
            ),
            {
                "DATA.MAD.USE_RANGE": str(max(values) - min(values)),
                "DATA.MAD.USE_MEAN": str(center),
            },
            {
                "type": "dot_plot",
                "data": values,
                "aria_label": "Dot plot of the values in the mean absolute deviation task.",
            },
        )
    if family_code == "MATH.DATA.MAD.COMPARE":
        center = rng.randint(10, 25)
        narrow = rng.randint(1, 3 + difficulty)
        wide = narrow + rng.randint(2, 3 + difficulty)
        first = [center - narrow, center + narrow] * 2
        second = [center - wide, center + wide] * 2
        if rng.choice([False, True]):
            first, second = second, first
            answer = "A"
        else:
            answer = "B"
        return (
            f"Set A: {', '.join(map(str, first))}. "
            f"Set B: {', '.join(map(str, second))}. "
            "Both sets have the same mean. Which has the larger MAD? Answer A or B.",
            answer,
            (
                "Compare distances from the common mean.",
                "MAD averages absolute distances, not signed deviations.",
            ),
            {"DATA.MAD.CONFUSE_SPREAD": "B" if answer == "A" else "A"},
        )
    if family_code == "MATH.NS.IRRATIONAL.CLASSIFY":
        root = rng.randint(3, 8 + difficulty * 2)
        perfect = rng.choice([True, False])
        radicand = root * root if perfect else root * root + rng.randint(1, root)
        answer = "rational" if perfect else "irrational"
        return (
            f"Is sqrt({radicand}) rational or irrational? Answer rational or irrational.",
            answer,
            (
                "A square root of a perfect-square integer is rational.",
                "Find consecutive perfect squares around the radicand.",
            ),
            {"NS.IRRATIONAL.CONFUSE_ROOTS": "irrational" if perfect else "rational"},
        )
    if family_code == "MATH.NS.IRRATIONAL.APPROX":
        root = rng.randint(3, 8 + difficulty * 3)
        radicand = root * root + rng.randint(1, root)
        rounded = _nearest_tenth_of_sqrt(radicand)
        truncated = math.isqrt(100 * radicand)
        return (
            (f"Approximate sqrt({radicand}) to the nearest tenth. "
            "Write exactly one decimal place."),
            f"{rounded // 10}.{rounded % 10}",
            (
                f"The root is between {root} and {root + 1}.",
                "Compare the squares of the neighboring tenths, then round.",
            ),
            {"NS.IRRATIONAL.TRUNCATE": f"{truncated // 10}.{truncated % 10}"},
        )
    if family_code == "MATH.FIN.UNIT_PRICE":
        quantity_a = rng.randint(2, 4 + difficulty)
        quantity_b = rng.randint(2, 4 + difficulty)
        while quantity_b == quantity_a:
            quantity_b = rng.randint(2, 4 + difficulty)
        unit_a = rng.randint(80, 200 + 30 * difficulty)
        unit_b = unit_a + rng.choice([-1, 1]) * rng.randint(10, 35)
        total_a = quantity_a * unit_a
        total_b = quantity_b * unit_b
        return (
            (
                f"Pack A has {quantity_a} notebooks for {_money(total_a)}. "
                f"Pack B has {quantity_b} notebooks for {_money(total_b)}. "
                "Which pack costs less per notebook? Answer A or B."
            ),
            "A" if unit_a < unit_b else "B",
            (
                "A lower package price does not always mean a lower unit price.",
                "Divide each total price by its number of notebooks.",
            ),
            {"FIN.UNIT_PRICE.COMPARE_TOTALS": "A" if total_a < total_b else "B"},
        )
    if family_code == "MATH.FIN.BUDGET":
        income = rng.randint(30, 70 + 20 * difficulty)
        food = rng.randint(6, 10 + difficulty * 3)
        travel = rng.randint(5, 10 + difficulty * 2)
        supplies = rng.randint(3, 8 + difficulty * 2)
        income = max(income, food + travel + supplies + rng.randint(5, 20))
        return (
            f"A club has {income} dollars for an activity. It spends {food} dollars "
            f"on food, {travel} dollars on travel, and {supplies} dollars on supplies. "
            "How many dollars remain? Answer with a whole number.",
            str(income - food - travel - supplies),
            (
                "Add all three expenses before subtracting.",
                "Remaining money equals the budget minus total expenses.",
            ),
            {"FIN.BUDGET.SKIP_EXPENSE": str(income - food - travel)},
        )
    if family_code == "MATH.FIN.SAVINGS_GOAL":
        starting = rng.randint(5, 15 + 5 * difficulty)
        weekly = rng.randint(4, 8 + 3 * difficulty)
        weeks = rng.randint(3, 6 + difficulty)
        remainder = rng.randint(1, weekly - 1)
        goal = starting + (weeks - 1) * weekly + remainder
        return (
            f"A student has {starting} dollars saved and adds {weekly} dollars "
            f"each week. The goal is {goal} dollars. What is the minimum whole "
            "number of weeks needed to reach or exceed the goal?",
            str(weeks),
            (
                "Subtract the initial savings from the goal.",
                "Divide by weekly savings and round up if any amount remains.",
            ),
            {"FIN.SAVINGS.ROUND_DOWN": str(weeks - 1)},
        )
    if family_code == "MATH.FIN.DISCOUNT":
        price = 20 * rng.randint(2, 5 + difficulty)
        percent = rng.choice([10, 20, 25, 50])
        savings = price * percent // 100
        return (
            f"A board game costs {price} dollars before a {percent}% discount. "
            "What is the price after the discount, before tax? "
            "Answer with a whole number of dollars.",
            str(price - savings),
            (
                f"Find {percent}% of the original price.",
                "Subtract the discount from the original price.",
            ),
            {
                "FIN.DISCOUNT.REPORT_SAVINGS": str(savings),
                "FIN.DISCOUNT.ADD_INSTEAD": str(price + savings),
            },
        )
    raise ValueError(f"No shared-gap builder for family: {family_code}")
