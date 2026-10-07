"""Canonical percent problem families.

Covers: fraction/decimal/percent conversion, percent of a quantity, finding the
whole, finding the percent, discounts, markups, tax, tip, percent
increase/decrease, reverse percent, multi-step applications, estimation,
error analysis.

Mathematical correctness contract
----------------------------------
* Integer-result problems construct operands so ``whole * pct`` is exactly
  divisible by 100.  No silent floor division.
* Money problems use ``Decimal`` with explicit ``ROUND_HALF_UP`` to two
  decimal places.  Answers use ``$X.XX`` format when cents are non-zero.
* Percent-change problems derive the change from exact multiplication so
  the stated percent is the *true* percent of the original.
"""

from __future__ import annotations

import random
from decimal import ROUND_HALF_UP, Decimal
from math import gcd

from app.canonical_problem_families import (
    ALL_MODES,
    ProblemFamilySpec,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CENTS = Decimal("0.01")


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


def _exact_whole(rng: random.Random, pct: int, lo: int, hi: int) -> int:
    """Return a random whole in [lo, hi] such that whole * pct / 100 is exact."""
    divisor = 100 // gcd(pct, 100)  # smallest unit that makes pct exact
    candidates = list(range(((lo + divisor - 1) // divisor) * divisor, hi + 1, divisor))
    if not candidates:
        return divisor  # safe fallback
    return rng.choice(candidates)


def _money(val: Decimal) -> str:
    """Format a Decimal as a dollar string with proper cent handling."""
    rounded = val.quantize(_CENTS, rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        return f"${int(rounded)}"
    return f"${rounded}"


def _pct_of(amount: Decimal, pct: int) -> Decimal:
    """Compute pct% of amount using exact Decimal arithmetic, rounded to cents."""
    return (amount * pct / 100).quantize(_CENTS, rounding=ROUND_HALF_UP)


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
        whole = _exact_whole(rng, pct, 20, 100 + difficulty * 50)
        part = whole * pct // 100  # exact by construction
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
        whole = _exact_whole(rng, pct, 40, 200 + difficulty * 50)
        part = whole * pct // 100  # exact by construction
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
        pct = rng.choice([10, 20, 25, 30, 40, 50, 60, 75, 80])
        whole = _exact_whole(rng, pct, 20, 100 + difficulty * 50)
        part = whole * pct // 100  # exact by construction
        # Verify: part / whole * 100 == pct exactly
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

    # --- discount (money with Decimal) ---
    if family_code == "MATH.PCT.DISCOUNT":
        pct = rng.choice([10, 15, 20, 25, 30, 40])  # exclude 50: savings = sale price
        # Use Decimal for realistic money amounts
        price_cents = rng.randint(1500, 8000 + difficulty * 3000)
        price = Decimal(price_cents) / Decimal(100)
        savings = _pct_of(price, pct)
        sale = price - savings
        items = ["jacket", "backpack", "pair of shoes", "tablet", "bicycle helmet"]
        item = rng.choice(items)
        prompt = f"A {item} costs {_money(price)}. It is on sale for {pct}% off. What is the sale price?"
        answer = _money(sale)
        hints = (
            f"Find {pct}% of {_money(price)} to get the discount amount.",
            f"Discount = {_money(savings)}. Subtract from the original price.",
        )
        misconceptions = {
            "PCT.DISCOUNT.REPORT_SAVINGS": _money(savings),
            "PCT.DISCOUNT.ADD_INSTEAD": _money(price + savings),
        }
        return prompt, answer, hints, misconceptions

    # --- markup (money with Decimal) ---
    if family_code == "MATH.PCT.MARKUP":
        pct = rng.choice([10, 20, 25, 30, 40, 50])
        cost_cents = rng.randint(1000, 6000 + difficulty * 2000)
        cost = Decimal(cost_cents) / Decimal(100)
        markup = _pct_of(cost, pct)
        selling = cost + markup
        prompt = (
            f"A store buys an item for {_money(cost)} and marks it up by {pct}%. "
            "What is the selling price?"
        )
        answer = _money(selling)
        hints = (
            f"Markup = {pct}% of {_money(cost)} = {_money(markup)}.",
            f"Selling price = cost + markup = {_money(cost)} + {_money(markup)}.",
        )
        misconceptions = {
            "PCT.MARKUP.REPORT_MARKUP_ONLY": _money(markup),
            "PCT.MARKUP.SUBTRACT": _money(cost - markup),
        }
        return prompt, answer, hints, misconceptions

    # --- tax (money with Decimal) ---
    if family_code == "MATH.PCT.TAX":
        tax_pct = rng.choice([5, 6, 8, 10])
        price_cents = rng.randint(1000, 8000 + difficulty * 3000)
        price = Decimal(price_cents) / Decimal(100)
        tax = _pct_of(price, tax_pct)
        total = price + tax
        items = ["phone case", "board game", "water bottle", "headphones"]
        item = rng.choice(items)
        prompt = f"A {item} costs {_money(price)}. Sales tax is {tax_pct}%. What is the total cost?"
        answer = _money(total)
        hints = (
            f"Tax = {tax_pct}% of {_money(price)} = {_money(tax)}.",
            f"Total = {_money(price)} + {_money(tax)}.",
        )
        misconceptions = {
            "PCT.TAX.TAX_ONLY": _money(tax),
            "PCT.TAX.SUBTRACT_TAX": _money(price - tax),
        }
        return prompt, answer, hints, misconceptions

    # --- tip (money with Decimal) ---
    if family_code == "MATH.PCT.TIP":
        tip_pct = rng.choice([10, 15, 18, 20])
        bill_cents = rng.randint(1500, 6000 + difficulty * 2000)
        bill = Decimal(bill_cents) / Decimal(100)
        tip = _pct_of(bill, tip_pct)
        total = bill + tip
        prompt = f"A restaurant bill is {_money(bill)}. You leave a {tip_pct}% tip. What is the total?"
        answer = _money(total)
        hints = (
            f"Tip = {tip_pct}% of {_money(bill)} = {_money(tip)}.",
            f"Total = bill + tip = {_money(bill)} + {_money(tip)}.",
        )
        misconceptions = {
            "PCT.TIP.TIP_ONLY": _money(tip),
            "PCT.TIP.TIP_ON_TOTAL": _money(total + _pct_of(total, tip_pct)),
        }
        return prompt, answer, hints, misconceptions

    # --- percent increase ---
    if family_code == "MATH.PCT.INCREASE":
        increase_pct = rng.choice([10, 20, 25, 50])
        # Construct original so that increase is exact
        original = _exact_whole(rng, increase_pct, 20, 100 + difficulty * 30)
        increase = original * increase_pct // 100  # exact by construction
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
        # Wrong-base misconception: divides by new value
        wrong_base_pct = Decimal(increase * 100) / Decimal(new_val)
        wrong_base_pct = int(wrong_base_pct.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        misconceptions = {
            "PCT.INCREASE.WRONG_BASE": f"{wrong_base_pct}%",
            "PCT.INCREASE.REPORT_NEW": str(new_val),
        }
        return prompt, answer, hints, misconceptions

    # --- percent decrease ---
    if family_code == "MATH.PCT.DECREASE":
        decrease_pct = rng.choice([10, 20, 25, 50])
        original = _exact_whole(rng, decrease_pct, 40, 150 + difficulty * 30)
        decrease = original * decrease_pct // 100  # exact by construction
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
        wrong_base_pct = Decimal(decrease * 100) / Decimal(new_val) if new_val else Decimal(0)
        wrong_base_pct = int(wrong_base_pct.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        misconceptions = {
            "PCT.DECREASE.WRONG_BASE": f"{wrong_base_pct}%",
        }
        return prompt, answer, hints, misconceptions

    # --- reverse percent ---
    if family_code == "MATH.PCT.REVERSE":
        pct = rng.choice([10, 20, 25, 40, 50])
        original = _exact_whole(rng, pct, 40, 200 + difficulty * 50)
        change = original * pct // 100  # exact by construction
        direction = rng.choice(["increase", "decrease"])
        if direction == "increase":
            final = original + change
            prompt = (
                f"After a {pct}% increase, a price is ${final}. "
                "What was the original price?"
            )
            divisor_pct = 100 + pct
        else:
            final = original - change
            prompt = (
                f"After a {pct}% discount, the sale price is ${final}. "
                "What was the original price?"
            )
            divisor_pct = 100 - pct
        answer = f"${original}"
        hints = (
            f"The final amount is {divisor_pct}% of the original.",
            f"Divide ${final} by {Decimal(divisor_pct) / Decimal(100)}.",
        )
        # Classic error: apply pct to the final instead of dividing
        wrong_change = final * pct // 100
        if direction == "increase":
            wrong = final - wrong_change
        else:
            wrong = final + wrong_change
        misconceptions = {
            "PCT.REVERSE.APPLY_TO_FINAL": f"${wrong}",
        }
        return prompt, answer, hints, misconceptions

    # --- multi-step (money with Decimal) ---
    if family_code == "MATH.PCT.MULTI_STEP":
        discount_pct = rng.choice([10, 20, 25])
        tax_pct = rng.choice([5, 8, 10])
        price_cents = rng.randint(4000, 12000 + difficulty * 3000)
        price = Decimal(price_cents) / Decimal(100)
        discount = _pct_of(price, discount_pct)
        after_discount = price - discount
        tax = _pct_of(after_discount, tax_pct)
        total = after_discount + tax
        prompt = (
            f"An item costs {_money(price)}. It is {discount_pct}% off, and then you pay "
            f"{tax_pct}% sales tax on the discounted price. What is the final cost?"
        )
        answer = _money(total)
        hints = (
            f"Step 1: Discount = {discount_pct}% of {_money(price)} = {_money(discount)}. After discount: {_money(after_discount)}.",
            f"Step 2: Tax = {tax_pct}% of {_money(after_discount)} = {_money(tax)}. Final: {_money(total)}.",
        )
        # Error: calculate tax on original price instead of discounted price
        wrong_tax = _pct_of(price, tax_pct)
        misconceptions = {
            "PCT.MULTI.TAX_ON_ORIGINAL": _money(price - discount + wrong_tax),
        }
        return prompt, answer, hints, misconceptions

    # --- estimate ---
    if family_code == "MATH.PCT.ESTIMATE":
        pct = rng.choice([10, 15, 20, 25, 50, 75])
        # Ensure the value is NOT a multiple of 10 so estimate differs from exact
        value = rng.randint(30, 200 + difficulty * 50)
        while value % 10 == 0:
            value = rng.randint(30, 200 + difficulty * 50)
        # Use Decimal for exact computation
        exact = (Decimal(value) * pct / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        rounded = round(value, -1)
        estimate = Decimal(rounded) * pct // 100
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

    # --- error: wrong base (structured deterministic assessment) ---
    if family_code == "MATH.PCT.ERROR.BASE":
        pct = rng.choice([20, 25, 50])
        original = _exact_whole(rng, pct, 40, 150)
        increase = original * pct // 100  # exact by construction
        new_val = original + increase
        wrong_pct = Decimal(increase * 100) / Decimal(new_val)
        wrong_pct = int(wrong_pct.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        names = ["Aisha", "Ben", "Clara", "Derek"]
        name = rng.choice(names)
        prompt = (
            f"A price increased from ${original} to ${new_val}. "
            f"{name} says the percent increase is {wrong_pct}% because "
            f"{increase}/{new_val} = {wrong_pct}%. "
            f"What is {name}'s error? "
            f"(A) Divided by the new value instead of the original. "
            f"(B) Subtracted instead of dividing. "
            f"(C) Used the wrong change amount. "
            f"(D) There is no error."
        )
        answer = "A"
        hints = (
            "Percent change is always calculated relative to the original value.",
            f"The increase is {increase}. Divide by the starting value: {original}.",
            f"Correct: {increase}/{original} × 100 = {pct}%.",
        )
        misconceptions = {
            "PCT.ERROR.AGREE_WRONG_BASE": "D",
            "PCT.ERROR.WRONG_OPERATION": "B",
        }
        return prompt, answer, hints, misconceptions

    raise ValueError(f"Unknown percent family: {family_code}")
