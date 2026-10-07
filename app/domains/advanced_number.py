"""Canonical rational-number, exponent, root, and scientific-notation families."""

from __future__ import annotations

import math
import random
from fractions import Fraction

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec


def _spec(
    code: str, name: str, skill: str, problem_type: str, lo: int, hi: int, *dims: str
) -> ProblemFamilySpec:
    return ProblemFamilySpec(code, name, skill, problem_type, lo, hi, ALL_MODES, frozenset(dims))


FAMILIES = {
    "MATH.RAT.COMPARE": _spec("MATH.RAT.COMPARE", "Compare rational numbers", "MATH.NS.RATIONAL.COMPARE", "COMPARISON", 1, 4, "number_sense", "representation"),
    "MATH.RAT.ADD": _spec("MATH.RAT.ADD", "Add signed rational numbers", "MATH.NS.RATIONAL.OPERATIONS", "RATIONAL_OPERATION", 1, 4, "procedural_fluency", "number_sense"),
    "MATH.RAT.SUB": _spec("MATH.RAT.SUB", "Subtract signed rational numbers", "MATH.NS.RATIONAL.OPERATIONS", "RATIONAL_OPERATION", 1, 4, "procedural_fluency", "inverse_operations"),
    "MATH.RAT.MUL": _spec("MATH.RAT.MUL", "Multiply signed rational numbers", "MATH.NS.RATIONAL.OPERATIONS", "RATIONAL_OPERATION", 2, 4, "procedural_fluency", "sign_reasoning"),
    "MATH.RAT.DIV": _spec("MATH.RAT.DIV", "Divide signed rational numbers", "MATH.NS.RATIONAL.OPERATIONS", "RATIONAL_OPERATION", 2, 4, "procedural_fluency", "sign_reasoning"),
    "MATH.RAT.NUMBER_LINE": _spec("MATH.RAT.NUMBER_LINE", "Locate rational numbers on a number line", "MATH.NS.RATIONAL.COMPARE", "REPRESENTATION", 1, 4, "representation", "number_sense"),
    "MATH.RAT.ERROR.SIGN": _spec("MATH.RAT.ERROR.SIGN", "Diagnose a rational-number sign error", "MATH.NS.RATIONAL.OPERATIONS", "ERROR_ANALYSIS", 2, 4, "error_analysis", "misconception_probe"),
    "MATH.EXP.EVALUATE": _spec("MATH.EXP.EVALUATE", "Evaluate integer exponents", "MATH.NS.EXPONENTS", "EXPONENT", 1, 4, "procedural_fluency", "structure_identification"),
    "MATH.EXP.PRODUCT": _spec("MATH.EXP.PRODUCT", "Product rule for exponents", "MATH.NS.EXPONENTS", "EXPONENT", 2, 4, "procedural_fluency", "structure_identification"),
    "MATH.EXP.QUOTIENT": _spec("MATH.EXP.QUOTIENT", "Quotient rule for exponents", "MATH.NS.EXPONENTS", "EXPONENT", 2, 4, "procedural_fluency", "structure_identification"),
    "MATH.EXP.POWER": _spec("MATH.EXP.POWER", "Power-of-a-power rule", "MATH.NS.EXPONENTS", "EXPONENT", 2, 4, "procedural_fluency", "structure_identification"),
    "MATH.ROOT.SQUARE": _spec("MATH.ROOT.SQUARE", "Perfect square roots", "MATH.NS.ROOTS", "ROOT", 1, 4, "procedural_fluency", "inverse_operations"),
    "MATH.ROOT.CUBE": _spec("MATH.ROOT.CUBE", "Perfect cube roots", "MATH.NS.ROOTS", "ROOT", 2, 4, "procedural_fluency", "inverse_operations"),
    "MATH.SCI.CONVERT": _spec("MATH.SCI.CONVERT", "Convert to scientific notation", "MATH.NS.SCIENTIFIC_NOTATION", "CONVERSION", 2, 4, "representation", "place_value"),
    "MATH.SCI.MULTIPLY": _spec("MATH.SCI.MULTIPLY", "Multiply in scientific notation", "MATH.NS.SCIENTIFIC_NOTATION", "SCIENTIFIC_NOTATION", 3, 4, "procedural_fluency", "exponent_reasoning"),
}


def _fraction(rng: random.Random, *, signed: bool = True) -> Fraction:
    denominator = rng.choice([2, 3, 4, 5, 6, 8, 10])
    numerator = rng.randint(1, denominator * 2)
    value = Fraction(numerator, denominator)
    if signed and rng.random() < 0.5:
        value = -value
    return value


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.RAT.COMPARE":
        a, b = _fraction(rng), _fraction(rng)
        while a == b:
            b = _fraction(rng)
        answer = "<" if a < b else ">"
        wrong = ">" if answer == "<" else "<"
        return (
            f"Compare {a} and {b} using < or >.",
            answer,
            ("Place both values on the same number line.", "The value farther right is greater."),
            {"RAT.COMPARE.ABSOLUTE_ONLY": wrong},
        )
    if family_code in {"MATH.RAT.ADD", "MATH.RAT.SUB", "MATH.RAT.MUL", "MATH.RAT.DIV"}:
        a, b = _fraction(rng), _fraction(rng)
        if family_code == "MATH.RAT.ADD":
            answer, symbol = a + b, "+"
            wrong = abs(a) + abs(b)
            hint = "Use a common denominator, then combine signed numerators."
        elif family_code == "MATH.RAT.SUB":
            answer, symbol = a - b, "-"
            wrong = a + b
            hint = "Rewrite subtraction as addition of the opposite."
        elif family_code == "MATH.RAT.MUL":
            answer, symbol = a * b, "×"
            wrong = abs(a * b)
            hint = "Multiply numerators and denominators, then determine the sign."
        else:
            while b == 0:
                b = _fraction(rng)
            answer, symbol = a / b, "÷"
            wrong = a * b
            hint = "Multiply by the reciprocal of the divisor."
        if wrong == answer:
            wrong = -answer
        return (
            f"Compute {a} {symbol} {b}. Give the simplified result.",
            str(answer),
            (hint, "Simplify the resulting fraction."),
            {"RAT.OPERATION.SIGN_OR_INVERSE": str(wrong)},
        )
    if family_code == "MATH.RAT.NUMBER_LINE":
        value = _fraction(rng)
        return (
            (
                f"Which rational number is located exactly at {value} on a number line? "
                f"(A) {value} (B) {-value} (C) {value + 1} (D) {value - 1}"
            ),
            "A",
            ("A coordinate names its exact position on the number line.", "Keep the sign."),
            {"RAT.NUMBER_LINE.REFLECT": "B"},
        )
    if family_code == "MATH.RAT.ERROR.SIGN":
        a = Fraction(rng.randint(1, 7), rng.choice([2, 3, 4, 5]))
        b = Fraction(rng.randint(1, 7), rng.choice([2, 3, 4, 5]))
        correct = -a + b
        claimed = -(a + b)
        while correct == claimed:
            b += Fraction(1, 2)
            correct = -a + b
            claimed = -(a + b)
        return (
            (
                f"A student says -{a} + {b} = {claimed}. Which response is correct? "
                f"(A) The correct value is {correct}. (B) The student is correct. "
                "(C) Both signs should be positive. (D) The denominators must be added."
            ),
            "A",
            ("The addends have different signs.", "Compare magnitudes and keep the sign of the larger magnitude."),
            {"RAT.SIGN.ADD_MAGNITUDES": "B"},
        )
    if family_code == "MATH.EXP.EVALUATE":
        base = rng.randint(2, 5 + difficulty)
        exponent = rng.randint(2, min(5, 2 + difficulty))
        return (
            f"Evaluate {base}^{exponent}.",
            str(base**exponent),
            ("An exponent tells how many equal factors to multiply.", f"Multiply {base} by itself {exponent} times."),
            {"EXP.MULTIPLY.BASE_EXPONENT": str(base * exponent)},
        )
    if family_code in {"MATH.EXP.PRODUCT", "MATH.EXP.QUOTIENT", "MATH.EXP.POWER"}:
        base = rng.randint(2, 7)
        m, n = rng.randint(2, 5), rng.randint(2, 4)
        if family_code == "MATH.EXP.PRODUCT":
            return (
                f"Simplify {base}^{m} × {base}^{n} as a single power.",
                f"{base}^{m+n}",
                ("The bases match.", "Add exponents when multiplying like bases."),
                {"EXP.PRODUCT.MULTIPLY_EXPONENTS": f"{base}^{m*n}"},
            )
        if family_code == "MATH.EXP.QUOTIENT":
            high = m + n
            return (
                f"Simplify {base}^{high} ÷ {base}^{n} as a single power.",
                f"{base}^{m}",
                ("The bases match.", "Subtract exponents when dividing like bases."),
                {"EXP.QUOTIENT.DIVIDE_EXPONENTS": f"{base}^{high//n}"},
            )
        return (
            f"Simplify ({base}^{m})^{n} as a single power.",
            f"{base}^{m*n}",
            ("A power is being raised to another power.", "Multiply the exponents."),
            {"EXP.POWER.ADD_EXPONENTS": f"{base}^{m+n}"},
        )
    if family_code == "MATH.ROOT.SQUARE":
        root = rng.randint(2, 12 + difficulty)
        square = root * root
        return (
            f"What is the principal square root of {square}?",
            str(root),
            ("Find the nonnegative number whose square equals the radicand.", f"{root} × {root} = {square}."),
            {"ROOT.RETURN_RADICAND": str(square)},
        )
    if family_code == "MATH.ROOT.CUBE":
        root = rng.randint(2, 6 + difficulty)
        cube = root**3
        return (
            f"What is the cube root of {cube}?",
            str(root),
            ("Find the number that is used as a factor three times.", f"{root}^3 = {cube}."),
            {"ROOT.SQUARE_INSTEAD": str(math.isqrt(cube))},
        )
    if family_code == "MATH.SCI.CONVERT":
        coefficient = rng.randint(11, 99)
        exponent = rng.randint(2, 5 + difficulty)
        value = coefficient * (10 ** (exponent - 1))
        normalized = f"{coefficient / 10:g}x10^{exponent}"
        return (
            f"Write {value} in scientific notation using x10^n.",
            normalized,
            ("Move the decimal so the leading factor is at least 1 and less than 10.", "The number of places moved becomes the exponent."),
            {"SCI.EXPONENT.OFF_BY_ONE": f"{coefficient:g}x10^{exponent-1}"},
        )
    if family_code == "MATH.SCI.MULTIPLY":
        a, b = rng.randint(2, 8), rng.randint(2, 8)
        m, n = rng.randint(2, 5), rng.randint(2, 5)
        coefficient = a * b
        exponent = m + n
        if coefficient >= 10:
            coefficient /= 10
            exponent += 1
        answer = f"{coefficient:g}x10^{exponent}"
        return (
            f"Compute ({a}x10^{m})({b}x10^{n}) and give normalized scientific notation.",
            answer,
            ("Multiply the leading factors and add powers of ten.", "Renormalize if the leading factor is 10 or more."),
            {"SCI.MULTIPLY.KEEP_EXPONENT": f"{a*b:g}x10^{m+n}"},
        )
    raise ValueError(f"No advanced-number builder for family: {family_code}")
