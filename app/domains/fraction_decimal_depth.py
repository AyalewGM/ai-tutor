"""Additional canonical fraction and decimal conceptual-depth families."""

from __future__ import annotations

import random
from fractions import Fraction

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(
    code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dims: str
) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dims))


def _text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


FAMILIES = {
    "MATH.FRAC.UNIT.MEANING": _spec("MATH.FRAC.UNIT.MEANING", "Interpret a unit fraction", "MATH.NF.FRACTION_MEANING", "FRACTION_REASONING", 1, 2, "conceptual_understanding", "representation"),
    "MATH.FRAC.NUMBER_LINE": _spec("MATH.FRAC.NUMBER_LINE", "Locate a fraction on a number line", "MATH.NF.FRACTION_MEANING", "FRACTION_REASONING", 1, 3, "representation", "number_sense"),
    "MATH.FRAC.IMPROPER.TO_MIXED": _spec("MATH.FRAC.IMPROPER.TO_MIXED", "Convert improper fraction to mixed number", "MATH.NF.MIXED_NUMBERS", "CONVERSION", 1, 3, "procedural_fluency", "representation"),
    "MATH.FRAC.MIXED.TO_IMPROPER": _spec("MATH.FRAC.MIXED.TO_IMPROPER", "Convert mixed number to improper fraction", "MATH.NF.MIXED_NUMBERS", "CONVERSION", 1, 3, "procedural_fluency", "representation"),
    "MATH.FRAC.MIXED.ADD": _spec("MATH.FRAC.MIXED.ADD", "Add mixed numbers", "MATH.NF.ADD_SUBTRACT", "FRACTION", 2, 4, "procedural_fluency", "conceptual_understanding"),
    "MATH.FRAC.MIXED.SUB": _spec("MATH.FRAC.MIXED.SUB", "Subtract mixed numbers with regrouping", "MATH.NF.ADD_SUBTRACT", "FRACTION", 2, 4, "procedural_fluency", "regrouping"),
    "MATH.FRAC.COMPARE.SAME_NUMERATOR": _spec("MATH.FRAC.COMPARE.SAME_NUMERATOR", "Compare fractions with equal numerators", "MATH.NF.COMPARE", "COMPARISON", 1, 3, "conceptual_understanding", "reasoning"),
    "MATH.FRAC.ERROR.BIGGER_DENOM": _spec("MATH.FRAC.ERROR.BIGGER_DENOM", "Diagnose denominator-size misconception", "MATH.NF.COMPARE", "ERROR_ANALYSIS", 1, 3, "error_analysis", "misconception_probe"),
    "MATH.DEC.ROUND": _spec("MATH.DEC.ROUND", "Round a decimal", "MATH.NS.DECIMAL.PLACE_VALUE", "ROUNDING", 1, 3, "place_value", "procedural_fluency"),
    "MATH.DEC.ORDER": _spec("MATH.DEC.ORDER", "Order decimals", "MATH.NS.DECIMAL.COMPARE", "ORDERING", 1, 3, "comparison", "number_sense"),
    "MATH.DEC.POWER10": _spec("MATH.DEC.POWER10", "Reason about multiplying by 10", "MATH.NS.DECIMAL.PLACE_VALUE", "PLACE_VALUE", 1, 3, "conceptual_understanding", "place_value"),
    "MATH.DEC.WORD.MULT": _spec("MATH.DEC.WORD.MULT", "Decimal multiplication context", "MATH.NS.DECIMAL.MULTIPLY", "WORD_PROBLEM", 2, 4, "modeling", "transfer"),
    "MATH.DEC.WORD.DIV": _spec("MATH.DEC.WORD.DIV", "Decimal division context", "MATH.NS.DECIMAL.DIVIDE", "WORD_PROBLEM", 2, 4, "modeling", "transfer"),
    "MATH.DEC.ERROR.ALIGN": _spec("MATH.DEC.ERROR.ALIGN", "Diagnose decimal alignment error", "MATH.NS.DECIMAL.ADD_SUBTRACT", "ERROR_ANALYSIS", 2, 4, "error_analysis", "misconception_probe"),
    "MATH.DEC.FRACTION.TENTHS": _spec("MATH.DEC.FRACTION.TENTHS", "Connect tenths fractions and decimals", "MATH.NS.DECIMAL.CONVERT", "CONVERSION", 1, 2, "representation", "conceptual_understanding"),
    "MATH.DEC.FRACTION.HUNDREDTHS": _spec("MATH.DEC.FRACTION.HUNDREDTHS", "Connect hundredths fractions and decimals", "MATH.NS.DECIMAL.CONVERT", "CONVERSION", 1, 3, "representation", "conceptual_understanding"),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.FRAC.UNIT.MEANING":
        denominator = rng.randint(2, 12)
        return (
            f"A whole is divided into {denominator} equal parts. What fraction is one part?",
            f"1/{denominator}",
            ("A unit fraction names one equal part of a whole.", "The denominator tells how many equal parts make the whole."),
            {"FRAC.UNIT.USE_WHOLE": f"{denominator}/1"},
        )
    if family_code == "MATH.FRAC.NUMBER_LINE":
        denominator = rng.randint(3, 10)
        numerator = rng.randint(1, denominator - 1)
        return (
            f"The interval from 0 to 1 is divided into {denominator} equal parts. What fraction is at mark {numerator} after 0?",
            f"{numerator}/{denominator}",
            ("Each interval has length one unit fraction.", "Count the equal intervals from 0."),
            {"FRAC.NUMBER_LINE.COUNT_MARKS": f"{numerator}/{denominator+1}"},
        )
    if family_code == "MATH.FRAC.IMPROPER.TO_MIXED":
        denominator = rng.randint(2, 9)
        whole = rng.randint(1, 6)
        remainder = rng.randint(1, denominator - 1)
        numerator = whole * denominator + remainder
        return (
            f"Convert {numerator}/{denominator} to a mixed number.",
            f"{whole} {remainder}/{denominator}",
            ("Divide the numerator by the denominator.", "The quotient is the whole number and the remainder is the new numerator."),
            {"FRAC.MIXED.IGNORE_REMAINDER": str(whole)},
        )
    if family_code == "MATH.FRAC.MIXED.TO_IMPROPER":
        denominator = rng.randint(2, 9)
        whole = rng.randint(1, 6)
        numerator = rng.randint(1, denominator - 1)
        improper = whole * denominator + numerator
        return (
            f"Convert {whole} {numerator}/{denominator} to an improper fraction.",
            f"{improper}/{denominator}",
            ("Multiply the whole number by the denominator.", "Add the original numerator and keep the denominator."),
            {"FRAC.MIXED.ADD_WHOLE_ONLY": f"{whole+numerator}/{denominator}"},
        )
    if family_code == "MATH.FRAC.MIXED.ADD":
        denominator = rng.randint(3, 9)
        w1, w2 = rng.randint(1, 5), rng.randint(1, 5)
        n1, n2 = rng.randint(1, denominator - 1), rng.randint(1, denominator - 1)
        result = Fraction(w1 * denominator + n1, denominator) + Fraction(w2 * denominator + n2, denominator)
        whole, rem = divmod(result.numerator, result.denominator)
        answer = str(whole) if rem == 0 else f"{whole} {rem}/{result.denominator}"
        return (
            f"Add {w1} {n1}/{denominator} + {w2} {n2}/{denominator}.",
            answer,
            ("Add the fractional parts and whole-number parts.", "If the fraction is at least one whole, regroup it."),
            {"FRAC.MIXED.NO_REGROUP": f"{w1+w2} {n1+n2}/{denominator}"},
        )
    if family_code == "MATH.FRAC.MIXED.SUB":
        denominator = rng.randint(3, 9)
        whole = rng.randint(3, 8)
        n1 = rng.randint(1, denominator - 2)
        n2 = rng.randint(n1 + 1, denominator - 1)
        result = Fraction(whole * denominator + n1, denominator) - Fraction((whole - 2) * denominator + n2, denominator)
        q, rem = divmod(result.numerator, result.denominator)
        answer = str(q) if rem == 0 else f"{q} {rem}/{result.denominator}"
        return (
            f"Subtract {whole} {n1}/{denominator} - {whole-2} {n2}/{denominator}.",
            answer,
            ("The first fractional part is too small to subtract directly.", "Regroup one whole as denominator/denominator."),
            {"FRAC.MIXED.SUBTRACT_COMPONENTS": f"2 {n2-n1}/{denominator}"},
        )
    if family_code == "MATH.FRAC.COMPARE.SAME_NUMERATOR":
        numerator = rng.randint(1, 5)
        d1, d2 = rng.sample(range(numerator + 1, numerator + 8), 2)
        answer = f"{numerator}/{min(d1,d2)}"
        return (
            f"Which is greater: {numerator}/{d1} or {numerator}/{d2}?",
            answer,
            ("The numerators are equal.", "With the same number of pieces, larger pieces come from the smaller denominator."),
            {"FRAC.COMPARE.BIGGER_DENOM": f"{numerator}/{max(d1,d2)}"},
        )
    if family_code == "MATH.FRAC.ERROR.BIGGER_DENOM":
        numerator = rng.randint(1, 5)
        small, large = sorted(rng.sample(range(numerator + 1, numerator + 9), 2))
        return (
            f"A student says {numerator}/{large} > {numerator}/{small} because {large} > {small}. "
            f"Which response is correct? (A) {numerator}/{small} is greater because equal numerators mean the smaller denominator makes larger pieces. "
            "(B) The student is correct. (C) They are equal. (D) Denominators never matter.",
            "A",
            ("Imagine dividing the same whole into different numbers of equal pieces.", "More equal pieces means each piece is smaller."),
            {"FRAC.COMPARE.BIGGER_DENOM": "B"},
        )
    if family_code == "MATH.DEC.ROUND":
        whole = rng.randint(1, 30)
        tenths = rng.randint(0, 9)
        hundredths = rng.randint(0, 9)
        value = whole + tenths / 10 + hundredths / 100
        rounded = whole + (tenths + (1 if hundredths >= 5 else 0)) / 10
        return (
            f"Round {value:.2f} to the nearest tenth.",
            f"{rounded:.1f}",
            ("The tenths digit is the rounding place.", "Look at the hundredths digit to decide whether to round up."),
            {"DEC.ROUND.TRUNCATE": f"{whole + tenths/10:.1f}" if hundredths >= 5 else f"{whole + (tenths+1)/10:.1f}"},
        )
    if family_code == "MATH.DEC.ORDER":
        values = rng.sample(range(101, 999), 4)
        decimals = [value / 100 for value in values]
        return (
            f"Order these decimals from least to greatest: {', '.join(f'{value:.2f}' for value in decimals)}.",
            ",".join(f"{value:.2f}" for value in sorted(decimals)),
            ("Line up decimal points.", "Compare ones, then tenths, then hundredths."),
            {"DEC.ORDER.REVERSE": ",".join(f"{value:.2f}" for value in sorted(decimals, reverse=True))},
        )
    if family_code == "MATH.DEC.POWER10":
        value = rng.randint(11, 999) / 100
        return (
            f"What is {value:.2f} multiplied by 10?",
            f"{value*10:g}",
            ("Multiplying by 10 makes each digit worth ten times as much.", "The decimal point appears one place farther right relative to the digits."),
            {"DEC.POWER10.MOVE_WRONG_WAY": f"{value/10:g}"},
        )
    if family_code == "MATH.DEC.WORD.MULT":
        price_cents = rng.randint(125, 875)
        quantity = rng.randint(2, 8)
        price = Fraction(price_cents, 100)
        total = price * quantity
        return (
            f"One item costs {float(price):.2f} dollars. What is the cost of {quantity} items?",
            f"{float(total):.2f}",
            ("Equal-priced items create repeated groups.", "Multiply the unit price by the number of items."),
            {"DEC.WORD.MULT.ADD_QUANTITY": f"{float(price + quantity):.2f}"},
        )
    if family_code == "MATH.DEC.WORD.DIV":
        groups = rng.randint(2, 8)
        per_group_cents = rng.randint(75, 450)
        total = Fraction(groups * per_group_cents, 100)
        per_group = Fraction(per_group_cents, 100)
        return (
            f"{float(total):.2f} liters are shared equally among {groups} containers. How many liters go in each container?",
            f"{float(per_group):.2f}",
            ("Equal sharing is division.", "Divide the total amount by the number of containers."),
            {"DEC.WORD.DIV.MULTIPLY": f"{float(total * groups):.2f}"},
        )
    if family_code == "MATH.DEC.ERROR.ALIGN":
        a = rng.randint(12, 89) / 10
        b = rng.randint(11, 99) / 100
        correct = a + b
        wrong = (int(round(a * 10)) + int(round(b * 100))) / 10
        if abs(wrong - correct) < 1e-9:
            wrong += 1
        return (
            f"A student adds {a:.1f} + {b:.2f} and gets {wrong:g} by lining up the last digits. "
            f"Which response is correct? (A) The decimal points must align; the sum is {correct:.2f}. "
            "(B) The student's alignment is correct. (C) Remove both decimal points. (D) Add only whole-number parts.",
            "A",
            ("Decimal digits represent place values.", "Align ones with ones, tenths with tenths, and hundredths with hundredths."),
            {"DEC.ALIGN.LAST_DIGITS": "B"},
        )
    if family_code in {"MATH.DEC.FRACTION.TENTHS", "MATH.DEC.FRACTION.HUNDREDTHS"}:
        denominator = 10 if family_code.endswith("TENTHS") else 100
        numerator = rng.randint(1, denominator - 1)
        value = Fraction(numerator, denominator)
        return (
            f"Write {numerator}/{denominator} as a decimal.",
            f"{float(value):g}",
            ("The denominator names decimal place value.", "Tenths use one decimal place; hundredths use two."),
            {"DEC.FRACTION.DIVIDE_WRONG_WAY": f"{denominator/numerator:g}"},
        )
    raise ValueError(f"No fraction/decimal depth builder for family: {family_code}")
