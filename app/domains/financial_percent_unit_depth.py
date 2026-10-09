"""Original financial reasoning: discount, sales tax, and unit-price comparison."""

import random

from app.answer_contracts import AnswerContract, AnswerKind
from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec

DISCOUNT = "MATH.FIN.DISCOUNT.FINAL_PRICE"
TAX = "MATH.FIN.TAX.FINAL_PRICE"
UNIT = "MATH.FIN.UNIT_PRICE.COMPARE"

FAMILIES = {
    DISCOUNT: ProblemFamilySpec(
        DISCOUNT, "Final price after percent discount", "MATH.FIN.PERCENT.DISCOUNT",
        "WORD_PROBLEM", 1, 4, ALL_MODES,
        frozenset({"financial_literacy", "percent_reasoning", "modeling"}),
        answer_contract=AnswerContract(AnswerKind.INTEGER),
    ),
    TAX: ProblemFamilySpec(
        TAX, "Final price including sales tax", "MATH.FIN.PERCENT.TAX",
        "WORD_PROBLEM", 1, 4, ALL_MODES,
        frozenset({"financial_literacy", "percent_reasoning", "modeling"}),
        answer_contract=AnswerContract(AnswerKind.INTEGER),
    ),
    UNIT: ProblemFamilySpec(
        UNIT, "Compare exact unit prices", "MATH.FIN.UNIT_PRICE",
        "COMPARISON", 1, 4, ALL_MODES,
        frozenset({"financial_literacy", "ratio_reasoning", "comparison"}),
        answer_contract=AnswerContract(AnswerKind.CATEGORY, choices=frozenset({"A", "B"})),
    ),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == DISCOUNT:
        price = 20 * rng.randint(3, 8 + difficulty)
        rate = rng.choice((10, 20, 25))
        discount = price * rate // 100
        return (
            (f"An item costs ${price}. A {rate}% discount applies before tax. "
             "What is its price after the discount, in whole dollars?"),
            str(price - discount),
            ("Find the discount amount from the original price.",
             "Subtract the discount from the original price."),
            {"FIN.DISCOUNT.REPORT_SAVINGS": str(discount)},
        )
    if family_code == TAX:
        price = 20 * rng.randint(3, 8 + difficulty)
        rate = rng.choice((5, 10, 15))
        tax = price * rate // 100
        return (
            (f"An item costs ${price} before tax. Sales tax is {rate}%. "
             "What is the total price including tax, in whole dollars?"),
            str(price + tax),
            ("Compute tax using the price before tax.",
             "Add the tax to the original price."),
            {"FIN.TAX.REPORT_TAX_ONLY": str(tax)},
        )
    if family_code == UNIT:
        count_a = rng.randint(2, 4 + difficulty)
        count_b = rng.randint(2, 4 + difficulty)
        unit_a = rng.randint(2, 6 + difficulty)
        unit_b = unit_a + rng.randint(1, 3)
        if rng.random() < 0.5:
            unit_a, unit_b = unit_b, unit_a
        cost_a, cost_b = count_a * unit_a, count_b * unit_b
        answer = "A" if unit_a < unit_b else "B"
        wrong = "B" if answer == "A" else "A"
        return (
            (f"Offer A: {count_a} identical notebooks for ${cost_a}. "
             f"Offer B: {count_b} identical notebooks for ${cost_b}. "
             "Which offer has the lower price per notebook? Answer A or B."),
            answer,
            ("Divide each total price by its notebook count.",
             "Compare the two prices for one notebook, not the package totals."),
            {"FIN.UNIT.PRICE_REVERSED": wrong},
        )
    raise ValueError(f"Unknown family: {family_code}")
