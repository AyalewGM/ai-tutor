"""Canonical percent problem families.

Covers: fraction/decimal/percent conversion, percent of a quantity, finding the
whole, finding the percent, discounts, markups, tax, tip, percent
increase/decrease, reverse percent, multi-step applications, error analysis.
"""

from __future__ import annotations

import random
from decimal import Decimal
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


def _pct_to_frac(p: int) -> str:
    n, d = p, 100
    g = gcd(n, d)
    return _frac(n // g, d // g)


def _pct_to_dec(p: int) -> str:
    val = Decimal(str(p)) / Decimal(100)
    return f"{val.normalize():f}"


# ---------------------------------------------------------------------------
# Family specifications
# ---------------------------------------------------------------------------

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.PCT.CONVERT.TO_DEC": ProblemFamilySpec(
        "MATH.PCT.CONVERT.TO_DEC", "Convert percent to decimal",
        "MATH.RP.PERCENT.CONVERT", "CONVERSION", 1, 2, ALL_MODES,
        frozenset({"representation", "procedural_fluency"}),
    ),
    "MATH.PCT.CONVERT.TO_FRAC": ProblemFamilySpec(
        "MATH.PCT.CONVERT.TO_FRAC", "Convert percent to fraction",
        "MATH.RP.PERCENT.CONVERT", "CONVERSION", 1, 2, ALL_MODES,
        frozenset({"representation", "procedural_fluency"}),
    ),
    "MATH.PCT.CONVERT.FROM_DEC": ProblemFamilySpec(
        "MATH.PCT.CONVERT.FROM_DEC", "Convert decimal to percent",
        "MATH.RP.PERCENT.CONVERT", "CONVERSION", 1, 2, ALL_MODES,
        frozenset({"representation", "procedural_fluency"}),
    ),
    "MATH.PCT.OF_QUANTITY": ProblemFamilySpec(
        "MATH.PCT.OF_QUANTITY", "Find a percent of a quantity",
        "MATH.RP.PERCENT.OF", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"procedural_fluency", "modeling"}),
    ),
    "MATH.PCT.FIND_WHOLE": ProblemFamilySpec(
        "MATH.PCT.FIND_WHOLE", "Find the whole given a part and a percent",
        "MATH.RP.PERCENT.OF", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning", "procedural_fluency"}),
    ),
    "MATH.PCT.FIND_PERCENT": ProblemFamilySpec(
        "MATH.PCT.FIND_PERCENT", "Determine the percent a part represents",
        "MATH.RP.PERCENT.OF", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"modeling", "reasoning"}),
    ),
    "MATH.PCT.DISCOUNT": ProblemFamilySpec(
        "MATH.PCT.DISCOUNT", "Calculate a discounted price",
        "MATH.RP.PERCENT.APPLICATIONS", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.PCT.MARKUP": ProblemFamilySpec(
        "MATH.PCT.MARKUP", "Calculate a markup price",
        "MATH.RP.PERCENT.APPLICATIONS", "WORD_PROBLEM", 2, 3, ALL_MODES,
        frozenset({"modeling", "transfer"}),
    ),
    "MATH.PCT.TAX": ProblemFamilySpec(
        "MATH.PCT.TAX", "Calculate total with sales tax",
        "MATH.RP.PERCENT.APPLICATIONS", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "transfer", "procedural_fluency"}),
    ),
    "MATH.PCT.TIP": ProblemFamilySpec(
        "MATH.PCT.TIP", "Calculate a restaurant tip and total",
        "MATH.RP.PERCENT.APPLICATIONS", "WORD_PROBLEM", 1, 3, ALL_MODES,
        frozenset({"modeling", "transfer"}),
    ),
    "MATH.PCT.INCREASE": ProblemFamilySpec(
        "MATH.PCT.INCREASE", "Calculate percent increase",
        "MATH.RP.PERCENT.CHANGE", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.PCT.DECREASE": ProblemFamilySpec(
        "MATH.PCT.DECREASE", "Calculate percent decrease",
        "MATH.RP.PERCENT.CHANGE", "WORD_PROBLEM", 2, 4, ALL_MODES,
        frozenset({"procedural_fluency", "conceptual_understanding"}),
    ),
    "MATH.PCT.REVERSE": ProblemFamilySpec(
        "MATH.PCT.REVERSE", "Reverse percent: find the original value",
        "MATH.RP.PERCENT.CHANGE", "WORD_PROBLEM", 3, 4, ALL_MODES,
        frozenset({"reasoning", "modeling", "transfer"}),
    ),
    "MATH.PCT.MULTI_STEP": ProblemFamilySpec(
        "MATH.PCT.MULTI_STEP", "Multi-step percent application",
        "MATH.RP.PERCENT.APPLICATIONS", "WORD_PROBLEM", 3, 4, ALL_MODES,
        frozenset({"modeling", "transfer", "reasoning", "procedural_fluency"}),
    ),
    "MATH.PCT.ESTIMATE": ProblemFamilySpec(
        "MATH.PCT.ESTIMATE", "Estimate a percent of a quantity",
        "MATH.RP.PERCENT.OF", "ESTIMATION", 2, 3, ALL_MODES,
        frozenset({"estimation", "number_sense", "reasoning"}),
    ),
    "MATH.PCT.ERROR.BASE": ProblemFamilySpec(
        "MATH.PCT.ERROR.BASE", "Error analysis: wrong base in percent problem",
        "MATH.RP.PERCENT.CHANGE", "ERROR_ANALYSIS", 2, 4, ALL_MODES,
        frozenset({"error_analysis", "misconception_probe", "reasoning"}),
    ),
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build(family_code: str, rng: random.Random, difficulty: int):
    """Return (prompt, answer, hints, misconceptions) for *family_code*."""

    # --- convert to decimal ---
    if family_code == "MATH.PCT.CONVERT.TO_DEC":
        p = rng.choice([5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 80, 90] if difficulty == 1
                       else [1, 2, 5, 12, 15, 33, 45, 62, 78, 85, 125, 150])
        prompt = f"Convert {p}% to a decimal."
        answer = _pct_to_dec(p)
        hints = (
            "To convert a percent to a decimal, divide by 100.",
            f"{p} ÷ 100 = {_pct_to_dec(p)}.",
        )
        # Only one decimal-place error: student moves decimal once instead of twice
        misconceptions = {
            "PCT.CONVERT.MOVE_ONE_PLACE": str(Decimal(str(p)) / Decimal(10)),
        }
        return prompt, answer, hints, misconceptions

    # --- convert to fraction ---
    if family_code == "MATH.PCT.CONVERT.TO_FRAC":
        p = rng.choice([10, 20, 25, 30, 40, 50, 60, 75, 80, 90])
        prompt = f"Convert {p}% to a fraction in simplest form."
        answer = _pct_to_frac(p)
        hints = (
            f"Write {p}% as {p}/100, then simplify.",
        )
        misconceptions = {
            "PCT.CONVERT.NO_SIMPLIFY": _frac(p, 100) if gcd(p, 100) > 1 else _frac(p + 1, 100),
        }
        return prompt, answer, hints, misconceptions

    # --- convert from decimal ---
    if family_code == "MATH.PCT.CONVERT.FROM_DEC":
        pool = ([5, 10, 20, 25, 30, 40, 50, 60, 75, 80] if difficulty == 1
                else [1, 8, 12, 15, 35, 45, 55, 65, 85, 125])
        p = rng.choice(pool)
        dec_val = Decimal(str(p)) / Decimal(100)
        prompt = f"Convert {dec_val.normalize():f} to a percent."
        answer = f"{p}%"
        hints = (
            "To convert a decimal to a percent, multiply by 100.",
        )
        misconceptions = {
            "PCT.CONVERT.WRONG_DIRECTION": f"{Decimal(str(p)) / Decimal(10000)}%",
        }
        return prompt, answer, hints, misconceptions

    # --- percent of quantity ---
    if family_code == "MATH.PCT.OF_QUANTITY":
        pct = rng.choice([10, 15, 20, 25, 30, 40, 50, 75] if difficulty <= 2
                         else [5, 12, 15, 20, 33, 40, 60, 75, 80])
        whole = rng.randint(20, 100 + difficulty * 50)
        # Ensure clean result for common percentages
        whole = whole - (whole * pct % 100 != 0) * (whole % (100 // gcd(pct, 100)))
        if whole <= 0:
            whole = 100
        part = whole * pct // 100
        contexts = [
            f"What is {pct}% of {whole}?",
            f"A class has {whole} students. {pct}% passed the test. How many students passed?",
            f"A store has {whole} items. {pct}% of them are on sale. How many items are on sale?",
        ]
        prompt = rng.choice(contexts)
        answer = str(part)
        hints = (
            f"Convert {pct}% to a decimal: {_pct_to_dec(pct)}.",
            f"Multiply: {_pct_to_dec(pct)} × {whole}.",
        )
        misconceptions = {
            "PCT.OF.DIVIDE_INSTEAD": str(whole // pct) if pct != 0 else "0",
            "PCT.OF.WRONG_DECIMAL": str(whole * pct // 10),
        }
        return prompt, answer, hints, misconceptions

    # --- find the whole ---
    if family_code == "MATH.PCT.FIND_WHOLE":
        pct = rng.choice([10, 20, 25, 40, 50, 75])
        whole = rng.randint(40, 200 + difficulty * 50)
        whole = whole - (whole * pct % 100 != 0) * (whole % (100 // gcd(pct, 100)))
        if whole <= 0:
            whole = 100
        part = whole * pct // 100
        prompt = f"{part} is {pct}% of what number?"
        answer = str(whole)
        hints = (
            f"If {pct}% of a number = {part}, divide {part} by the decimal form of {pct}%.",
            f"{part} ÷ {_pct_to_dec(pct)} = ?",
        )
        misconceptions = {
            "PCT.WHOLE.MULTIPLY_INSTEAD": str(part * pct),
            "PCT.WHOLE.ADD_100": str(part + 100),
        }
        return prompt, answer, hints, misconceptions

    # --- find the percent ---
    if family_code == "MATH.PCT.FIND_PERCENT":
        whole = rng.randint(20, 100 + difficulty * 50)
        pct = rng.choice([10, 20, 25, 30, 40, 50, 60, 75, 80])
        part = whole * pct // 100
        if part == 0:
            part = 1
            pct = round(part * 100 / whole)
        prompt = f"{part} is what percent of {whole}?"
        answer = f"{pct}%"
        hints = (
            f"Divide the part by the whole: {part} ÷ {whole}.",
            "Multiply the result by 100 to get the percent.",
        )
        misconceptions = {
            "PCT.FIND.REVERSED_DIVISION": f"{whole * 100 // part if part else 0}%",
        }
        return prompt, answer, hints, misconceptions

    # --- discount ---
    if family_code == "MATH.PCT.DISCOUNT":
        pct = rng.choice([10, 15, 20, 25, 30, 40])  # exclude 50: savings = sale price
        price = rng.randint(20, 80 + difficulty * 30)
        price = price - (price * pct % 100 != 0) * (price % (100 // gcd(pct, 100)))
        if price <= 0:
            price = 100
        savings = price * pct // 100
        sale = price - savings
        items = ["jacket", "backpack", "pair of shoes", "tablet", "bicycle helmet"]
        item = rng.choice(items)
        prompt = f"A {item} costs ${price}. It is on sale for {pct}% off. What is the sale price?"
        answer = f"${sale}"
        hints = (
            f"Find {pct}% of ${price} to get the discount amount.",
            f"Discount = ${savings}. Subtract from the original price.",
        )
        misconceptions = {
            "PCT.DISCOUNT.REPORT_SAVINGS": f"${savings}",
            "PCT.DISCOUNT.ADD_INSTEAD": f"${price + savings}",
        }
        return prompt, answer, hints, misconceptions

    # --- markup ---
    if family_code == "MATH.PCT.MARKUP":
        pct = rng.choice([10, 20, 25, 30, 40, 50])
        cost = rng.randint(10, 60 + difficulty * 20)
        cost = cost - (cost * pct % 100 != 0) * (cost % (100 // gcd(pct, 100)))
        if cost <= 0:
            cost = 50
        markup = cost * pct // 100
        selling = cost + markup
        prompt = (
            f"A store buys an item for ${cost} and marks it up by {pct}%. "
            "What is the selling price?"
        )
        answer = f"${selling}"
        hints = (
            f"Markup = {pct}% of ${cost} = ${markup}.",
            f"Selling price = cost + markup = ${cost} + ${markup}.",
        )
        misconceptions = {
            "PCT.MARKUP.REPORT_MARKUP_ONLY": f"${markup}",
            "PCT.MARKUP.SUBTRACT": f"${cost - markup}",
        }
        return prompt, answer, hints, misconceptions

    # --- tax ---
    if family_code == "MATH.PCT.TAX":
        tax_pct = rng.choice([5, 6, 8, 10])
        price = rng.randint(10, 80 + difficulty * 30)
        price = price - (price * tax_pct % 100 != 0) * (price % (100 // gcd(tax_pct, 100)))
        if price <= 0:
            price = 100
        tax = price * tax_pct // 100
        total = price + tax
        items = ["phone case", "board game", "water bottle", "headphones"]
        item = rng.choice(items)
        prompt = f"A {item} costs ${price}. Sales tax is {tax_pct}%. What is the total cost?"
        answer = f"${total}"
        hints = (
            f"Tax = {tax_pct}% of ${price} = ${tax}.",
            f"Total = ${price} + ${tax}.",
        )
        misconceptions = {
            "PCT.TAX.TAX_ONLY": f"${tax}",
            "PCT.TAX.SUBTRACT_TAX": f"${price - tax}",
        }
        return prompt, answer, hints, misconceptions

    # --- tip ---
    if family_code == "MATH.PCT.TIP":
        tip_pct = rng.choice([10, 15, 18, 20])
        bill = rng.randint(15, 60 + difficulty * 20)
        bill = bill - (bill * tip_pct % 100 != 0) * (bill % (100 // gcd(tip_pct, 100)))
        if bill <= 0:
            bill = 40
        tip = bill * tip_pct // 100
        total = bill + tip
        prompt = f"A restaurant bill is ${bill}. You leave a {tip_pct}% tip. What is the total?"
        answer = f"${total}"
        hints = (
            f"Tip = {tip_pct}% of ${bill} = ${tip}.",
            f"Total = bill + tip = ${bill} + ${tip}.",
        )
        misconceptions = {
            "PCT.TIP.TIP_ONLY": f"${tip}",
            "PCT.TIP.TIP_ON_TOTAL": f"${total + total * tip_pct // 100}",
        }
        return prompt, answer, hints, misconceptions

    # --- percent increase ---
    if family_code == "MATH.PCT.INCREASE":
        original = rng.randint(20, 100 + difficulty * 30)
        increase_pct = rng.choice([10, 20, 25, 50])
        increase = original * increase_pct // 100
        if increase == 0:
            increase = 1
            increase_pct = round(100 * increase / original)
        new_val = original + increase
        prompt = (
            f"A quantity increases from {original} to {new_val}. "
            "What is the percent increase?"
        )
        answer = f"{increase_pct}%"
        hints = (
            f"Change = {new_val} − {original} = {increase}.",
            f"Percent increase = change ÷ original × 100 = {increase} ÷ {original} × 100.",
        )
        misconceptions = {
            "PCT.INCREASE.WRONG_BASE": f"{round(100 * increase / new_val)}%" if new_val else "0%",
            "PCT.INCREASE.REPORT_NEW": str(new_val),
        }
        return prompt, answer, hints, misconceptions

    # --- percent decrease ---
    if family_code == "MATH.PCT.DECREASE":
        original = rng.randint(40, 150 + difficulty * 30)
        decrease_pct = rng.choice([10, 20, 25, 50])
        decrease = original * decrease_pct // 100
        if decrease == 0:
            decrease = 1
            decrease_pct = round(100 * decrease / original)
        new_val = original - decrease
        prompt = (
            f"A quantity decreases from {original} to {new_val}. "
            "What is the percent decrease?"
        )
        answer = f"{decrease_pct}%"
        hints = (
            f"Change = {original} − {new_val} = {decrease}.",
            "Percent decrease = change ÷ original × 100.",
        )
        misconceptions = {
            "PCT.DECREASE.WRONG_BASE": f"{round(100 * decrease / new_val) if new_val else 0}%",
        }
        return prompt, answer, hints, misconceptions

    # --- reverse percent ---
    if family_code == "MATH.PCT.REVERSE":
        pct = rng.choice([10, 20, 25, 40, 50])
        original = rng.randint(40, 200 + difficulty * 50)
        original = original - (original * pct % 100 != 0) * (original % (100 // gcd(pct, 100)))
        if original <= 0:
            original = 100
        change = original * pct // 100
        direction = rng.choice(["increase", "decrease"])
        if direction == "increase":
            final = original + change
            prompt = (
                f"After a {pct}% increase, a price is ${final}. "
                "What was the original price?"
            )
            divisor = 100 + pct
        else:
            final = original - change
            prompt = (
                f"After a {pct}% discount, the sale price is ${final}. "
                "What was the original price?"
            )
            divisor = 100 - pct
        answer = f"${original}"
        hints = (
            f"The final amount is {100 + pct if direction == 'increase' else 100 - pct}% of the original.",
            f"Divide ${final} by {divisor / 100}.",
        )
        # Classic error: apply pct to the final instead of dividing
        if direction == "increase":
            wrong = final - final * pct // 100
        else:
            wrong = final + final * pct // 100
        misconceptions = {
            "PCT.REVERSE.APPLY_TO_FINAL": f"${wrong}",
        }
        return prompt, answer, hints, misconceptions

    # --- multi-step ---
    if family_code == "MATH.PCT.MULTI_STEP":
        price = rng.randint(40, 120 + difficulty * 30)
        discount_pct = rng.choice([10, 20, 25])
        tax_pct = rng.choice([5, 8, 10])
        price = price - (price * discount_pct % 100 != 0) * (price % (100 // gcd(discount_pct, 100)))
        if price <= 0:
            price = 100
        discount = price * discount_pct // 100
        after_discount = price - discount
        tax = after_discount * tax_pct // 100
        total = after_discount + tax
        prompt = (
            f"An item costs ${price}. It is {discount_pct}% off, and then you pay "
            f"{tax_pct}% sales tax on the discounted price. What is the final cost?"
        )
        answer = f"${total}"
        hints = (
            f"Step 1: Discount = {discount_pct}% of ${price} = ${discount}. After discount: ${after_discount}.",
            f"Step 2: Tax = {tax_pct}% of ${after_discount} = ${tax}. Final: ${total}.",
        )
        # Error: calculate tax on original price instead of discounted price
        wrong_tax = price * tax_pct // 100
        misconceptions = {
            "PCT.MULTI.TAX_ON_ORIGINAL": f"${price - discount + wrong_tax}",
        }
        return prompt, answer, hints, misconceptions

    # --- estimate ---
    if family_code == "MATH.PCT.ESTIMATE":
        pct = rng.choice([10, 15, 20, 25, 50, 75])
        # Ensure the value is NOT a multiple of 10 so estimate differs from exact
        value = rng.randint(30, 200 + difficulty * 50)
        while value % 10 == 0:
            value = rng.randint(30, 200 + difficulty * 50)
        exact = value * pct // 100
        rounded = round(value, -1)
        estimate = rounded * pct // 100
        prompt = (
            f"Estimate {pct}% of {value} by rounding {value} to the nearest ten first."
        )
        answer = str(estimate)
        hints = (
            f"{value} rounds to {rounded}.",
            f"{pct}% of {rounded} = {estimate}.",
        )
        misconceptions = {
            "PCT.ESTIMATE.EXACT_INSTEAD": str(exact),
        }
        return prompt, answer, hints, misconceptions

    # --- error: wrong base ---
    if family_code == "MATH.PCT.ERROR.BASE":
        original = rng.randint(40, 150)
        pct = rng.choice([20, 25, 50])
        increase = original * pct // 100
        if increase == 0:
            increase = 1
        new_val = original + increase
        wrong_pct = round(100 * increase / new_val) if new_val else 0
        names = ["Aisha", "Ben", "Clara", "Derek"]
        name = rng.choice(names)
        prompt = (
            f"A price increased from ${original} to ${new_val}. "
            f"{name} says the percent increase is {wrong_pct}% because "
            f"{increase}/{new_val} = {wrong_pct}%. What is {name}'s mistake?"
        )
        answer = (
            f"{name} divided by the new value instead of the original. "
            f"Percent increase = {increase}/{original} × 100 = {pct}%."
        )
        hints = (
            "Percent change is always calculated relative to the original value.",
            f"The increase is {increase}. Divide by the starting value: {original}.",
        )
        misconceptions = {
            "PCT.ERROR.AGREE_WRONG_BASE": f"{wrong_pct}%",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"Unknown percent family: {family_code}")
