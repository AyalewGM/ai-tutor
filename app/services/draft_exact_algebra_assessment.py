"""Fail-closed exact scorer for the draft Issue #337 algebra milestone.

This module is intentionally *not* registered by an API router or canonical
problem-family registry.  It gives backend, mathematics and frontend reviewers
a concrete contract for independently scored, multi-field responses without
activating unreviewed Ontario content or writing learner evidence.

The public payload contains only the prompt and response-field names.  Seeds,
parameters, exact answers and misconception alternatives remain server-side.
"""

from __future__ import annotations

import hashlib
import random
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

DRAFT_RUNTIME_ACTIVATION = False
CONTRACT_VERSION = "issue-337-exact-r1"
MAX_RESPONSE_TEXT = 120


class ExactAlgebraKind(StrEnum):
    LINEAR_EQUATION = "LINEAR_EQUATION"
    ROOT_EQUATION = "ROOT_EQUATION"
    MONOMIAL_QUOTIENT = "MONOMIAL_QUOTIENT"
    POLYNOMIAL_QUOTIENT = "POLYNOMIAL_QUOTIENT"
    EXPONENT_LAWS = "EXPONENT_LAWS"
    SCIENTIFIC_NOTATION = "SCIENTIFIC_NOTATION"
    GEOMETRY_TRANSFER = "GEOMETRY_TRANSFER"


@dataclass(frozen=True)
class HiddenExactVariant:
    """Server-only generated item, including its trusted exact oracle."""

    variant_id: str
    kind: ExactAlgebraKind
    prompt: str
    response_fields: tuple[str, ...]
    parameters: Mapping[str, object]
    oracle: Mapping[str, object]
    misconception_responses: Mapping[str, Mapping[str, object]]

    def public_payload(self) -> dict[str, object]:
        """Return the only representation permitted in a student client."""

        return {
            "contract_version": CONTRACT_VERSION,
            "variant_id": self.variant_id,
            "kind": self.kind.value,
            "prompt": self.prompt,
            "response_fields": list(self.response_fields),
            "assessment_mode": "INDEPENDENT",
        }


@dataclass(frozen=True)
class ExactScore:
    is_correct: bool
    misconception_code: str | None
    assistance_level: int = 0


_FRACTION = re.compile(r"-?(?:0|[1-9]\d*)(?:/-?[1-9]\d*)?")


def _parse_fraction(value: object) -> Fraction:
    if not isinstance(value, str) or len(value) > MAX_RESPONSE_TEXT:
        raise ValueError("exact numbers must be short strings")
    text = value.strip()
    if not _FRACTION.fullmatch(text):
        raise ValueError("exact number must be an integer or reduced/ unreduced fraction")
    result = Fraction(text)
    if abs(result.numerator) > 10**12 or result.denominator > 10**12:
        raise ValueError("exact number is outside the accepted assessment range")
    return result


def _integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("integer response field required")
    if abs(value) > 10**9:
        raise ValueError("integer response is outside the accepted assessment range")
    return value


def _restrictions(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or any(item not in {"x", "y"} for item in value):
        raise ValueError("restrictions must be a list containing only x and/or y")
    if len(value) != len(set(value)):
        raise ValueError("restrictions must not contain duplicates")
    return tuple(sorted(value))


def _fraction_text(value: Fraction | int) -> str:
    value = Fraction(value)
    return (
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    )


def _seeded(kind: ExactAlgebraKind, seed: int) -> tuple[random.Random, str]:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    digest = hashlib.sha256(f"{CONTRACT_VERSION}|{kind.value}|{seed}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16)), digest[:20]


def _linear(seed: int) -> HiddenExactVariant:
    rng, variant_id = _seeded(ExactAlgebraKind.LINEAR_EQUATION, seed)
    solution = Fraction(rng.choice((-9, -7, -5, -3, 3, 5, 7, 9)), rng.choice((2, 3, 4)))
    left_coefficient = Fraction(rng.choice((-7, -5, -3, 3, 5, 7)), rng.choice((1, 2, 3)))
    right_coefficient = Fraction(rng.choice((-6, -4, -2, 2, 4, 6)), rng.choice((1, 2, 3)))
    while right_coefficient == left_coefficient:
        right_coefficient += 1
    right_constant = Fraction(rng.randint(-8, 8))
    left_constant = (right_coefficient - left_coefficient) * solution + right_constant
    prompt = (
        f"Solve {_fraction_text(left_coefficient)}x + ({_fraction_text(left_constant)}) = "
        f"{_fraction_text(right_coefficient)}x + ({_fraction_text(right_constant)}). "
        "Return the complete exact solution set and verify it by substitution."
    )
    wrong_sign = -solution
    return HiddenExactVariant(
        variant_id,
        ExactAlgebraKind.LINEAR_EQUATION,
        prompt,
        ("classification", "solutions", "substitution_check"),
        {
            "left_coefficient": left_coefficient,
            "left_constant": left_constant,
            "right_coefficient": right_coefficient,
            "right_constant": right_constant,
        },
        {
            "classification": "ONE_REAL_SOLUTION",
            "solutions": (solution,),
            "substitution_check": True,
        },
        {
            "EQ.SIGN.MOVE_WITHOUT_BALANCE": {
                "classification": "ONE_REAL_SOLUTION",
                "solutions": (wrong_sign,),
                "substitution_check": False,
            }
        },
    )


def _root(seed: int) -> HiddenExactVariant:
    rng, variant_id = _seeded(ExactAlgebraKind.ROOT_EQUATION, seed)
    coefficient = rng.choice((-5, -3, -2, 2, 3, 5))
    shift = rng.randint(-8, 8)
    root = rng.randint(2, 9)
    radicand = -(root * root) if seed % 3 == 0 else root * root
    if radicand < 0:
        classification = "NO_REAL_SOLUTIONS"
        solutions: tuple[Fraction, ...] = ()
        alternatives: dict[str, Mapping[str, object]] = {}
    else:
        solutions = tuple(
            sorted({Fraction(root - shift, coefficient), Fraction(-root - shift, coefficient)})
        )
        classification = "TWO_REAL_SOLUTIONS"
        alternatives = {
            "ROOT.PRINCIPAL_ONLY": {
                "classification": "ONE_REAL_SOLUTION",
                "solutions": (solutions[-1],),
                "substitution_check": True,
            }
        }
    return HiddenExactVariant(
        variant_id,
        ExactAlgebraKind.ROOT_EQUATION,
        (
            f"Solve ({coefficient}x + ({shift}))^2 = {radicand} over the real numbers. "
            "Return the complete exact solution set and verify every candidate."
        ),
        ("classification", "solutions", "substitution_check"),
        {"coefficient": coefficient, "shift": shift, "radicand": radicand},
        {"classification": classification, "solutions": solutions, "substitution_check": True},
        alternatives,
    )


def _monomial(seed: int, *, polynomial: bool) -> HiddenExactVariant:
    kind = (
        ExactAlgebraKind.POLYNOMIAL_QUOTIENT if polynomial else ExactAlgebraKind.MONOMIAL_QUOTIENT
    )
    rng, variant_id = _seeded(kind, seed)
    divisor_coefficient = rng.choice((-6, -4, -3, 2, 3, 4, 6))
    divisor_x, divisor_y = rng.randint(1, 4), rng.randint(1, 3)
    terms = 2 if polynomial else 1
    quotient_terms: list[tuple[Fraction, int, int]] = []
    dividend_terms: list[tuple[Fraction, int, int]] = []
    for index in range(terms):
        coefficient = Fraction(rng.choice((-7, -5, -3, 2, 4, 6, 8)))
        x_exp = rng.randint(-2, 3)
        y_exp = rng.randint(-1, 3)
        if index and (x_exp, y_exp) == (quotient_terms[0][1], quotient_terms[0][2]):
            y_exp += 1
        quotient_terms.append((coefficient, x_exp, y_exp))
        dividend_terms.append(
            (coefficient * divisor_coefficient, x_exp + divisor_x, y_exp + divisor_y)
        )
    prompt = (
        "Divide every numerator term by the monomial denominator. Give exact coefficient and exponent "
        "fields, and retain all restrictions from the original denominator."
    )
    response_fields = (
        ("terms", "domain_restrictions")
        if polynomial
        else ("coefficient", "x_exponent", "y_exponent", "domain_restrictions")
    )
    oracle: Mapping[str, object]
    if polynomial:
        oracle = {"terms": tuple(quotient_terms), "domain_restrictions": ("x", "y")}
    else:
        coefficient, x_exp, y_exp = quotient_terms[0]
        oracle = {
            "coefficient": coefficient,
            "x_exponent": x_exp,
            "y_exponent": y_exp,
            "domain_restrictions": ("x", "y"),
        }
    return HiddenExactVariant(
        variant_id,
        kind,
        prompt,
        response_fields,
        {
            "divisor": (Fraction(divisor_coefficient), divisor_x, divisor_y),
            "dividend_terms": tuple(dividend_terms),
        },
        oracle,
        {},
    )


def _exponents(seed: int) -> HiddenExactVariant:
    rng, variant_id = _seeded(ExactAlgebraKind.EXPONENT_LAWS, seed)
    base = rng.randint(2, 7)
    while True:
        m, n = rng.randint(2, 7), rng.randint(2, 6)
        p, q = rng.randint(2, 5), rng.randint(2, 4)
        exponent = m + n - p * q
        if exponent != 0 and abs(exponent) <= 9:
            break
    value = Fraction(base**exponent) if exponent >= 0 else Fraction(1, base ** (-exponent))
    return HiddenExactVariant(
        variant_id,
        ExactAlgebraKind.EXPONENT_LAWS,
        f"Simplify ({base}^{m} x {base}^{n}) / (({base}^{p})^{q}) as one power and evaluate exactly.",
        ("result_exponent", "exact_value"),
        {"base": base, "m": m, "n": n, "p": p, "q": q},
        {"result_exponent": exponent, "exact_value": value},
        {
            "EXP.NEGATIVE_IS_NEGATIVE_VALUE": {
                "result_exponent": exponent,
                "exact_value": Fraction(-(base ** abs(exponent))),
            }
        }
        if exponent < 0
        else {},
    )


def _normalize_scientific(coefficient: Fraction, exponent: int) -> tuple[Fraction, int]:
    if coefficient == 0:
        return Fraction(0), 0
    while abs(coefficient) >= 10:
        coefficient /= 10
        exponent += 1
    while abs(coefficient) < 1:
        coefficient *= 10
        exponent -= 1
    return coefficient, exponent


def _scientific(seed: int) -> HiddenExactVariant:
    rng, variant_id = _seeded(ExactAlgebraKind.SCIENTIFIC_NOTATION, seed)
    operation = ("TO_SCIENTIFIC", "TO_ORDINARY", "MULTIPLY", "DIVIDE")[seed % 4]
    c1, c2 = Fraction(rng.randint(12, 98), 10), Fraction(rng.randint(12, 98), 10)
    e1, e2 = rng.randint(-7, 7), rng.randint(-7, 7)
    if operation == "MULTIPLY":
        coefficient, exponent = _normalize_scientific(c1 * c2, e1 + e2)
        prompt = f"Compute ({_fraction_text(c1)} x 10^{e1})({_fraction_text(c2)} x 10^{e2}) and normalize."
    elif operation == "DIVIDE":
        coefficient, exponent = _normalize_scientific(c1 / c2, e1 - e2)
        prompt = f"Compute ({_fraction_text(c1)} x 10^{e1}) / ({_fraction_text(c2)} x 10^{e2}) and normalize."
    elif operation == "TO_ORDINARY":
        coefficient, exponent = _normalize_scientific(c1, e1)
        prompt = f"Write {_fraction_text(coefficient)} x 10^{exponent} as an exact ordinary number."
    else:
        raw = c1 * Fraction(10 ** abs(e1)) if e1 >= 0 else c1 / Fraction(10 ** abs(e1))
        coefficient, exponent = _normalize_scientific(raw, 0)
        prompt = f"Write {_fraction_text(raw)} in normalized scientific notation."
    ordinary = coefficient * (
        Fraction(10**exponent) if exponent >= 0 else Fraction(1, 10 ** (-exponent))
    )
    return HiddenExactVariant(
        variant_id,
        ExactAlgebraKind.SCIENTIFIC_NOTATION,
        prompt,
        ("normalized_coefficient", "power_of_ten", "ordinary_value"),
        {"operation": operation, "c1": c1, "e1": e1, "c2": c2, "e2": e2},
        {
            "normalized_coefficient": coefficient,
            "power_of_ten": exponent,
            "ordinary_value": ordinary,
        },
        {},
    )


def _geometry(seed: int) -> HiddenExactVariant:
    rng, variant_id = _seeded(ExactAlgebraKind.GEOMETRY_TRANSFER, seed)
    shape = "SQUARE" if seed % 2 == 0 else "CUBE"
    dimensional_power = 2 if shape == "SQUARE" else 3
    units = "square units" if shape == "SQUARE" else "cubic units"
    base, coefficient, exponent = rng.randint(2, 4), rng.randint(2, 4), rng.randint(1, 3)
    result_coefficient = coefficient**dimensional_power
    result_exponent = exponent * dimensional_power
    exact_value = result_coefficient * base**result_exponent
    return HiddenExactVariant(
        variant_id,
        ExactAlgebraKind.GEOMETRY_TRANSFER,
        (
            f"A {shape.lower()} has side length {coefficient}({base}^{exponent}) units. "
            "Give its exact measure as a coefficient times one power, its value, and its units."
        ),
        ("result_coefficient", "result_exponent", "exact_value", "units"),
        {
            "shape": shape,
            "base": base,
            "coefficient": coefficient,
            "exponent": exponent,
            "dimensional_power": dimensional_power,
        },
        {
            "result_coefficient": result_coefficient,
            "result_exponent": result_exponent,
            "exact_value": exact_value,
            "units": units,
        },
        {
            "EXP.GEOMETRY.POWER_NOT_DISTRIBUTED": {
                "result_coefficient": coefficient,
                "result_exponent": exponent * dimensional_power,
                "exact_value": coefficient * base ** (exponent * dimensional_power),
                "units": units,
            }
        },
    )


def generate_hidden_variant(kind: ExactAlgebraKind, seed: int) -> HiddenExactVariant:
    """Create a deterministic unseen item in an independent-only namespace."""

    if not isinstance(kind, ExactAlgebraKind):
        raise TypeError("kind must be an ExactAlgebraKind")
    builders = {
        ExactAlgebraKind.LINEAR_EQUATION: _linear,
        ExactAlgebraKind.ROOT_EQUATION: _root,
        ExactAlgebraKind.MONOMIAL_QUOTIENT: lambda value: _monomial(value, polynomial=False),
        ExactAlgebraKind.POLYNOMIAL_QUOTIENT: lambda value: _monomial(value, polynomial=True),
        ExactAlgebraKind.EXPONENT_LAWS: _exponents,
        ExactAlgebraKind.SCIENTIFIC_NOTATION: _scientific,
        ExactAlgebraKind.GEOMETRY_TRANSFER: _geometry,
    }
    return builders[kind](seed)


def _solutions(value: object) -> tuple[Fraction, ...]:
    if not isinstance(value, list) or len(value) > 2:
        raise ValueError("solutions must be a list of at most two exact numbers")
    parsed = tuple(sorted({_parse_fraction(item) for item in value}))
    if len(parsed) != len(value):
        raise ValueError("solution set must not contain duplicates")
    return parsed


def _terms(value: object) -> tuple[tuple[Fraction, int, int], ...]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("polynomial quotient requires exactly two term records")
    parsed: list[tuple[Fraction, int, int]] = []
    for term in value:
        if not isinstance(term, dict) or set(term) != {"coefficient", "x_exponent", "y_exponent"}:
            raise ValueError("each term requires coefficient, x_exponent and y_exponent")
        parsed.append(
            (
                _parse_fraction(term["coefficient"]),
                _integer(term["x_exponent"]),
                _integer(term["y_exponent"]),
            )
        )
    return tuple(parsed)


def _normalize_response(
    kind: ExactAlgebraKind, response: Mapping[str, object]
) -> dict[str, object]:
    if not isinstance(response, dict):
        raise TypeError("response must be an object")
    if kind in {ExactAlgebraKind.LINEAR_EQUATION, ExactAlgebraKind.ROOT_EQUATION}:
        if set(response) != {"classification", "solutions", "substitution_check"}:
            raise ValueError("equation response fields do not match the contract")
        classification = response["classification"]
        if classification not in {"ONE_REAL_SOLUTION", "TWO_REAL_SOLUTIONS", "NO_REAL_SOLUTIONS"}:
            raise ValueError("unsupported solution classification")
        if type(response["substitution_check"]) is not bool:
            raise ValueError("substitution_check must be boolean")
        return {
            "classification": classification,
            "solutions": _solutions(response["solutions"]),
            "substitution_check": response["substitution_check"],
        }
    if kind == ExactAlgebraKind.MONOMIAL_QUOTIENT:
        expected = {"coefficient", "x_exponent", "y_exponent", "domain_restrictions"}
        if set(response) != expected:
            raise ValueError("monomial response fields do not match the contract")
        return {
            "coefficient": _parse_fraction(response["coefficient"]),
            "x_exponent": _integer(response["x_exponent"]),
            "y_exponent": _integer(response["y_exponent"]),
            "domain_restrictions": _restrictions(response["domain_restrictions"]),
        }
    if kind == ExactAlgebraKind.POLYNOMIAL_QUOTIENT:
        if set(response) != {"terms", "domain_restrictions"}:
            raise ValueError("polynomial response fields do not match the contract")
        return {
            "terms": _terms(response["terms"]),
            "domain_restrictions": _restrictions(response["domain_restrictions"]),
        }
    if kind == ExactAlgebraKind.EXPONENT_LAWS:
        if set(response) != {"result_exponent", "exact_value"}:
            raise ValueError("exponent response fields do not match the contract")
        return {
            "result_exponent": _integer(response["result_exponent"]),
            "exact_value": _parse_fraction(response["exact_value"]),
        }
    if kind == ExactAlgebraKind.SCIENTIFIC_NOTATION:
        if set(response) != {"normalized_coefficient", "power_of_ten", "ordinary_value"}:
            raise ValueError("scientific-notation response fields do not match the contract")
        coefficient = _parse_fraction(response["normalized_coefficient"])
        if coefficient and not (1 <= abs(coefficient) < 10):
            raise ValueError("scientific-notation coefficient must be normalized")
        return {
            "normalized_coefficient": coefficient,
            "power_of_ten": _integer(response["power_of_ten"]),
            "ordinary_value": _parse_fraction(response["ordinary_value"]),
        }
    if set(response) != {"result_coefficient", "result_exponent", "exact_value", "units"}:
        raise ValueError("geometry response fields do not match the contract")
    if response["units"] not in {"square units", "cubic units"}:
        raise ValueError("unsupported geometry units")
    return {
        "result_coefficient": _integer(response["result_coefficient"]),
        "result_exponent": _integer(response["result_exponent"]),
        "exact_value": _integer(response["exact_value"]),
        "units": response["units"],
    }


def score_exact_response(
    variant: HiddenExactVariant,
    response: Mapping[str, object],
    *,
    already_answered: bool = False,
) -> ExactScore:
    """Score once against the hidden oracle; never return tutoring content."""

    if already_answered:
        raise ValueError("variant already answered")
    normalized = _normalize_response(variant.kind, response)
    if normalized == dict(variant.oracle):
        return ExactScore(is_correct=True, misconception_code=None)
    for code, misconception_response in variant.misconception_responses.items():
        if normalized == dict(misconception_response):
            return ExactScore(is_correct=False, misconception_code=code)
    return ExactScore(is_correct=False, misconception_code=None)
