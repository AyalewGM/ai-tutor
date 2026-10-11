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
import math
import random
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

DRAFT_RUNTIME_ACTIVATION = False
CONTRACT_VERSION = "issue-337-exact-r3"
MAX_RESPONSE_TEXT = 120


class ExactAlgebraKind(StrEnum):
    LINEAR_EQUATION = "LINEAR_EQUATION"
    ROOT_EQUATION = "ROOT_EQUATION"
    MONOMIAL_QUOTIENT = "MONOMIAL_QUOTIENT"
    POLYNOMIAL_QUOTIENT = "POLYNOMIAL_QUOTIENT"
    POLYNOMIAL_AREA_TRANSFER = "POLYNOMIAL_AREA_TRANSFER"
    EXPONENT_LAWS = "EXPONENT_LAWS"
    SCIENTIFIC_NOTATION = "SCIENTIFIC_NOTATION"
    GEOMETRY_TRANSFER = "GEOMETRY_TRANSFER"


class ExactAssessmentTarget(StrEnum):
    """One review-only atomic target for a generated independent task.

    The ``MATH.*`` values are existing canonical or accepted DRAFT atom labels.
    They are deliberately server-only here: this enum does not register an
    alias, capability, mastery target, runtime route or production taxonomy row.
    """

    LINEAR_TWO_STEP = "MATH.EQ.TWO.DIRECT"
    SQUARE_EQUATION_REAL_SOLUTIONS = "MATH.ALGEBRA.SQUARE_EQUATION_REAL_SOLUTIONS"
    DIVIDE_MONOMIALS = "MATH.POLY.DIVIDE_MONOMIALS"
    DIVIDE_POLYNOMIAL_BY_MONOMIAL = "MATH.POLY.DIVIDE_POLYNOMIAL_BY_MONOMIAL"
    EXPONENT_PRODUCT = "MATH.EXPONENT.LAW.PRODUCT"
    EXPONENT_QUOTIENT = "MATH.EXPONENT.LAW.QUOTIENT"
    EXPONENT_POWER_OF_POWER = "MATH.EXPONENT.LAW.POWER_OF_POWER"
    EXPONENT_ZERO = "MATH.EXPONENT.ZERO_NONZERO_BASE"
    EXPONENT_NEGATIVE_RECIPROCAL = "MATH.EXPONENT.NEGATIVE_AS_RECIPROCAL"
    SCIENTIFIC_CONVERT_NORMALIZE = "MATH.SCIENTIFIC_NOTATION.CONVERT_NORMALIZE"
    SCIENTIFIC_MULTIPLY_NORMALIZE = "MATH.SCIENTIFIC_NOTATION.MULTIPLY_NORMALIZE"
    SCIENTIFIC_DIVIDE_NORMALIZE = "MATH.SCIENTIFIC_NOTATION.DIVIDE_NORMALIZE"


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
    primary_target: ExactAssessmentTarget
    supporting_targets: tuple[ExactAssessmentTarget, ...] = ()

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


@dataclass(frozen=True, order=True)
class ExactReal:
    """Canonical exact real number ``rational + coefficient * sqrt(radicand)``."""

    rational: Fraction
    radical_coefficient: Fraction = Fraction(0)
    radicand: int = 0


_FRACTION = re.compile(r"-?(?:0|[1-9]\d*)(?:/-?[1-9]\d*)?")


def _parse_fraction(value: object) -> Fraction:
    if not isinstance(value, str) or len(value) > MAX_RESPONSE_TEXT:
        raise ValueError("exact numbers must be short strings")
    text = value.strip()
    if not _FRACTION.fullmatch(text):
        raise ValueError("exact number must be an integer or reduced/ unreduced fraction")
    result = Fraction(text)
    if abs(result.numerator) > 10**18 or result.denominator > 10**18:
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


def _parse_canonical_fraction(value: object) -> Fraction:
    result = _parse_fraction(value)
    if value.strip() != _fraction_text(result):
        raise ValueError("polynomial coefficients must be reduced canonical fractions")
    return result


def _term_multiply(
    left: tuple[Fraction, int, int],
    right: tuple[Fraction, int, int],
) -> tuple[Fraction, int, int]:
    return left[0] * right[0], left[1] + right[1], left[2] + right[2]


def _seeded(kind: ExactAlgebraKind, seed: int) -> tuple[random.Random, str]:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    digest = hashlib.sha256(f"{CONTRACT_VERSION}|{kind.value}|{seed}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16)), digest[:20]


def _substitution_record(
    solution: Fraction,
    left_value: Fraction,
    right_value: Fraction,
) -> tuple[Fraction, Fraction, Fraction]:
    return solution, left_value, right_value


def _exact_real(
    rational: Fraction | int,
    radical_coefficient: Fraction | int = 0,
    radicand: int = 0,
) -> ExactReal:
    rational = Fraction(rational)
    radical_coefficient = Fraction(radical_coefficient)
    if radicand < 0:
        raise ValueError("an exact real cannot contain a negative radicand")
    if radical_coefficient == 0 or radicand == 0:
        return ExactReal(rational)
    return ExactReal(rational, radical_coefficient, radicand)


def _affine_exact(value: ExactReal, coefficient: int, shift: int) -> ExactReal:
    return _exact_real(
        coefficient * value.rational + shift,
        coefficient * value.radical_coefficient,
        value.radicand,
    )


def _square_exact(value: ExactReal) -> ExactReal:
    return _exact_real(
        value.rational**2 + value.radical_coefficient**2 * value.radicand,
        2 * value.rational * value.radical_coefficient,
        value.radicand,
    )


def _root_substitution_record(
    solution: ExactReal,
    coefficient: int,
    shift: int,
    radicand: int,
) -> tuple[ExactReal, ExactReal, ExactReal]:
    return solution, _square_exact(_affine_exact(solution, coefficient, shift)), _exact_real(radicand)


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
    correct_left = left_coefficient * solution + left_constant
    correct_right = right_coefficient * solution + right_constant
    wrong_left = left_coefficient * wrong_sign + left_constant
    wrong_right = right_coefficient * wrong_sign + right_constant
    return HiddenExactVariant(
        variant_id,
        ExactAlgebraKind.LINEAR_EQUATION,
        prompt,
        ("classification", "solutions", "substitution_checks"),
        {
            "left_coefficient": left_coefficient,
            "left_constant": left_constant,
            "right_coefficient": right_coefficient,
            "right_constant": right_constant,
        },
        {
            "classification": "ONE_REAL_SOLUTION",
            "solutions": (solution,),
            "substitution_checks": (_substitution_record(solution, correct_left, correct_right),),
        },
        {
            "EQ.SIGN.MOVE_WITHOUT_BALANCE": {
                "classification": "ONE_REAL_SOLUTION",
                "solutions": (wrong_sign,),
                "substitution_checks": (_substitution_record(wrong_sign, wrong_left, wrong_right),),
            }
        },
        ExactAssessmentTarget.LINEAR_TWO_STEP,
    )


def _root(seed: int) -> HiddenExactVariant:
    rng, variant_id = _seeded(ExactAlgebraKind.ROOT_EQUATION, seed)
    coefficient = rng.choice((-5, -3, -2, 2, 3, 5))
    shift = rng.randint(-8, 8)
    root = rng.randint(2, 9)
    outcome = ("NEGATIVE", "ZERO", "POSITIVE_SQUARE", "POSITIVE_NONSQUARE")[seed % 4]
    if outcome == "NEGATIVE":
        radicand = -(root * root)
    elif outcome == "ZERO":
        radicand = 0
    elif outcome == "POSITIVE_SQUARE":
        radicand = root * root
    else:
        radicand = rng.choice((2, 3, 5, 6, 7, 10, 11, 13))
    if radicand < 0:
        classification = "NO_REAL_SOLUTIONS"
        solutions: tuple[ExactReal, ...] = ()
        substitution_checks: tuple[tuple[ExactReal, ExactReal, ExactReal], ...] = ()
        alternatives: dict[str, Mapping[str, object]] = {}
    elif radicand == 0:
        solutions = (_exact_real(Fraction(-shift, coefficient)),)
        classification = "ONE_REAL_SOLUTION"
        substitution_checks = (
            _root_substitution_record(solutions[0], coefficient, shift, radicand),
        )
        alternatives = {}
    else:
        square_root = math.isqrt(radicand)
        if square_root * square_root == radicand:
            positive_solution = _exact_real(Fraction(square_root - shift, coefficient))
            negative_solution = _exact_real(Fraction(-square_root - shift, coefficient))
        else:
            center = Fraction(-shift, coefficient)
            positive_solution = _exact_real(center, Fraction(1, coefficient), radicand)
            negative_solution = _exact_real(center, Fraction(-1, coefficient), radicand)
        solutions = tuple(sorted({positive_solution, negative_solution}))
        classification = "TWO_REAL_SOLUTIONS"
        substitution_checks = tuple(
            _root_substitution_record(solution, coefficient, shift, radicand)
            for solution in solutions
        )
        alternatives = {
            "ROOT.PRINCIPAL_ONLY": {
                "classification": "ONE_REAL_SOLUTION",
                "solutions": (positive_solution,),
                "substitution_checks": (
                    _root_substitution_record(
                        positive_solution, coefficient, shift, radicand
                    ),
                ),
            }
        }
    return HiddenExactVariant(
        variant_id,
        ExactAlgebraKind.ROOT_EQUATION,
        (
            f"Solve ({coefficient}x + ({shift}))^2 = {radicand} over the real numbers. "
            "Return the complete exact solution set and verify every candidate."
        ),
        ("classification", "solutions", "substitution_checks"),
        {
            "coefficient": coefficient,
            "shift": shift,
            "radicand": radicand,
            "root_outcome": outcome,
        },
        {
            "classification": classification,
            "solutions": solutions,
            "substitution_checks": substitution_checks,
        },
        alternatives,
        ExactAssessmentTarget.SQUARE_EQUATION_REAL_SOLUTIONS,
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
        x_exp = rng.randint(max(-2, -divisor_x), 3)
        y_exp = rng.randint(max(-1, -divisor_y), 3)
        if index and (x_exp, y_exp) == (quotient_terms[0][1], quotient_terms[0][2]):
            y_exp += 1
        quotient_terms.append((coefficient, x_exp, y_exp))
        dividend_terms.append(
            (coefficient * divisor_coefficient, x_exp + divisor_x, y_exp + divisor_y)
        )
    if polynomial:
        ordered_pairs = sorted(
            zip(quotient_terms, dividend_terms, strict=True),
            key=lambda pair: (-pair[0][1], -pair[0][2], pair[0][0]),
        )
        quotient_terms = [pair[0] for pair in ordered_pairs]
        dividend_terms = [pair[1] for pair in ordered_pairs]
    prompt = (
        "Divide every numerator term by the monomial denominator. Give exact coefficient and exponent "
        "fields, and retain all restrictions from the original denominator."
    )
    response_fields = (
        (
            "terms",
            "domain_restrictions",
            "coefficient_reason",
            "exponent_reason",
            "reconstruction",
        )
        if polynomial
        else ("coefficient", "x_exponent", "y_exponent", "domain_restrictions")
    )
    oracle: Mapping[str, object]
    if polynomial:
        divisor = (Fraction(divisor_coefficient), divisor_x, divisor_y)
        reconstruction = tuple(
            (quotient, divisor, dividend)
            for quotient, dividend in zip(quotient_terms, dividend_terms, strict=True)
        )
        oracle = {
            "terms": tuple(quotient_terms),
            "domain_restrictions": ("x", "y"),
            "coefficient_reason": "DIVIDEND_COEFFICIENT_DIVIDED_BY_DIVISOR_COEFFICIENT",
            "exponent_reason": "DIVIDEND_EXPONENT_MINUS_DIVISOR_EXPONENT",
            "reconstruction": reconstruction,
        }
        reciprocal_terms = tuple(
            (
                divisor[0] / dividend[0],
                quotient[1],
                quotient[2],
            )
            for quotient, dividend in zip(quotient_terms, dividend_terms, strict=True)
        )
        added_exponent_terms = tuple(
            (
                quotient[0],
                dividend[1] + divisor_x,
                dividend[2] + divisor_y,
            )
            for quotient, dividend in zip(quotient_terms, dividend_terms, strict=True)
        )
        alternatives = {
            "POLY.DIV.COEFFICIENT_RECIPROCAL": {
                **oracle,
                "terms": reciprocal_terms,
                "coefficient_reason": "DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT",
                "reconstruction": tuple(
                    (term, divisor, _term_multiply(term, divisor)) for term in reciprocal_terms
                ),
            },
            "POLY.DIV.ADD_EXPONENTS": {
                **oracle,
                "terms": added_exponent_terms,
                "exponent_reason": "DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT",
                "reconstruction": tuple(
                    (term, divisor, _term_multiply(term, divisor)) for term in added_exponent_terms
                ),
            },
            "POLY.DIV.ONE_TERM_ONLY": {
                **oracle,
                "terms": (quotient_terms[0],),
                "reconstruction": (reconstruction[0],),
            },
            "POLY.DIV.DOMAIN_OMITTED": {
                **oracle,
                "domain_restrictions": (),
            },
        }
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
        alternatives if polynomial else {},
        (
            ExactAssessmentTarget.DIVIDE_POLYNOMIAL_BY_MONOMIAL
            if polynomial
            else ExactAssessmentTarget.DIVIDE_MONOMIALS
        ),
        ((ExactAssessmentTarget.DIVIDE_MONOMIALS,) if polynomial else ()),
    )


def _polynomial_area_transfer(seed: int) -> HiddenExactVariant:
    rng, variant_id = _seeded(ExactAlgebraKind.POLYNOMIAL_AREA_TRANSFER, seed)
    height = (Fraction(rng.choice((2, 3, 4))), rng.randint(1, 2), rng.randint(0, 1))
    width_terms = tuple(
        sorted(
            (
                (Fraction(rng.choice((2, 3, 5))), rng.randint(0, 2), 1),
                (Fraction(rng.choice((3, 4, 6))), rng.randint(0, 1), 2),
            ),
            key=lambda term: (-term[1], -term[2], term[0]),
        )
    )
    area_terms = tuple(_term_multiply(width, height) for width in width_terms)
    restrictions = tuple(
        variable for variable, exponent in zip(("x", "y"), height[1:], strict=True) if exponent > 0
    )
    reconstruction = tuple(
        (width, height, area) for width, area in zip(width_terms, area_terms, strict=True)
    )
    return HiddenExactVariant(
        variant_id,
        ExactAlgebraKind.POLYNOMIAL_AREA_TRANSFER,
        (
            "A composite rectangle has two algebraic area terms and one shared monomial "
            "height. Recover both width terms, give the total width, retain every original "
            "nonzero restriction, and reconstruct both square-unit areas."
        ),
        (
            "width_terms",
            "total_width_terms",
            "domain_restrictions",
            "multiplication_checks",
            "units",
        ),
        {"common_height": height, "area_terms": area_terms},
        {
            "width_terms": width_terms,
            "total_width_terms": width_terms,
            "domain_restrictions": restrictions,
            "multiplication_checks": reconstruction,
            "units": ("units", "square units"),
        },
        {},
        ExactAssessmentTarget.DIVIDE_POLYNOMIAL_BY_MONOMIAL,
        (ExactAssessmentTarget.DIVIDE_MONOMIALS,),
    )


def _exponents(seed: int) -> HiddenExactVariant:
    rng, variant_id = _seeded(ExactAlgebraKind.EXPONENT_LAWS, seed)
    base = rng.randint(2, 7)
    p, q = rng.randint(2, 5), rng.randint(2, 4)
    product_exponent = p * q
    outcome = ("ZERO", "POSITIVE", "NEGATIVE")[seed % 3]
    if outcome == "ZERO":
        m = rng.randint(1, product_exponent - 1)
        n = product_exponent - m
    elif outcome == "POSITIVE":
        m = rng.randint(1, product_exponent - 1)
        n = product_exponent - m + rng.randint(1, 4)
    else:
        deficit = rng.randint(1, min(4, product_exponent - 2))
        m = rng.randint(1, product_exponent - deficit - 1)
        n = product_exponent - deficit - m
    exponent = m + n - product_exponent
    value = Fraction(base**exponent) if exponent >= 0 else Fraction(1, base ** (-exponent))
    misconception_responses: dict[str, Mapping[str, object]] = {}
    if exponent < 0:
        misconception_responses["EXP.NEGATIVE_IS_NEGATIVE_VALUE"] = {
            "result_exponent": exponent,
            "exact_value": Fraction(-(base ** abs(exponent))),
        }
    elif exponent == 0:
        misconception_responses["EXP.ZERO_WRITTEN_AS_ZERO"] = {
            "result_exponent": exponent,
            "exact_value": Fraction(0),
        }
    primary_target = {
        "POSITIVE": ExactAssessmentTarget.EXPONENT_POWER_OF_POWER,
        "ZERO": ExactAssessmentTarget.EXPONENT_ZERO,
        "NEGATIVE": ExactAssessmentTarget.EXPONENT_NEGATIVE_RECIPROCAL,
    }[outcome]
    supporting_targets = (
        ExactAssessmentTarget.EXPONENT_PRODUCT,
        ExactAssessmentTarget.EXPONENT_QUOTIENT,
        ExactAssessmentTarget.EXPONENT_POWER_OF_POWER,
    )
    supporting_targets = tuple(
        target for target in supporting_targets if target != primary_target
    )
    return HiddenExactVariant(
        variant_id,
        ExactAlgebraKind.EXPONENT_LAWS,
        (
            f"Simplify ({base}^{m} x {base}^{n}) / (({base}^{p})^{q}) as one power and "
            f"evaluate exactly. The numeric base {base} is nonzero."
        ),
        ("result_exponent", "exact_value"),
        {
            "base": base,
            "base_nonzero": True,
            "outcome": outcome,
            "m": m,
            "n": n,
            "p": p,
            "q": q,
        },
        {"result_exponent": exponent, "exact_value": value},
        misconception_responses,
        primary_target,
        supporting_targets,
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
    primary_target = {
        "TO_SCIENTIFIC": ExactAssessmentTarget.SCIENTIFIC_CONVERT_NORMALIZE,
        "TO_ORDINARY": ExactAssessmentTarget.SCIENTIFIC_CONVERT_NORMALIZE,
        "MULTIPLY": ExactAssessmentTarget.SCIENTIFIC_MULTIPLY_NORMALIZE,
        "DIVIDE": ExactAssessmentTarget.SCIENTIFIC_DIVIDE_NORMALIZE,
    }[operation]
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
        primary_target,
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
                "result_coefficient": coefficient**dimensional_power,
                "result_exponent": exponent,
                "exact_value": coefficient**dimensional_power * base**exponent,
                "units": units,
            }
        },
        ExactAssessmentTarget.EXPONENT_POWER_OF_POWER,
        (ExactAssessmentTarget.EXPONENT_PRODUCT,),
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
        ExactAlgebraKind.POLYNOMIAL_AREA_TRANSFER: _polynomial_area_transfer,
        ExactAlgebraKind.EXPONENT_LAWS: _exponents,
        ExactAlgebraKind.SCIENTIFIC_NOTATION: _scientific,
        ExactAlgebraKind.GEOMETRY_TRANSFER: _geometry,
    }
    return builders[kind](seed)


def _expected_primary_target(variant: HiddenExactVariant) -> ExactAssessmentTarget:
    """Derive the only target this task may evidence from its hidden structure."""

    static_targets = {
        ExactAlgebraKind.LINEAR_EQUATION: ExactAssessmentTarget.LINEAR_TWO_STEP,
        ExactAlgebraKind.ROOT_EQUATION: (
            ExactAssessmentTarget.SQUARE_EQUATION_REAL_SOLUTIONS
        ),
        ExactAlgebraKind.MONOMIAL_QUOTIENT: ExactAssessmentTarget.DIVIDE_MONOMIALS,
        ExactAlgebraKind.POLYNOMIAL_QUOTIENT: (
            ExactAssessmentTarget.DIVIDE_POLYNOMIAL_BY_MONOMIAL
        ),
        ExactAlgebraKind.POLYNOMIAL_AREA_TRANSFER: (
            ExactAssessmentTarget.DIVIDE_POLYNOMIAL_BY_MONOMIAL
        ),
        ExactAlgebraKind.GEOMETRY_TRANSFER: (
            ExactAssessmentTarget.EXPONENT_POWER_OF_POWER
        ),
    }
    if variant.kind in static_targets:
        return static_targets[variant.kind]
    if variant.kind == ExactAlgebraKind.SCIENTIFIC_NOTATION:
        operation_targets = {
            "TO_SCIENTIFIC": ExactAssessmentTarget.SCIENTIFIC_CONVERT_NORMALIZE,
            "TO_ORDINARY": ExactAssessmentTarget.SCIENTIFIC_CONVERT_NORMALIZE,
            "MULTIPLY": ExactAssessmentTarget.SCIENTIFIC_MULTIPLY_NORMALIZE,
            "DIVIDE": ExactAssessmentTarget.SCIENTIFIC_DIVIDE_NORMALIZE,
        }
        try:
            return operation_targets[variant.parameters["operation"]]
        except (KeyError, TypeError) as error:
            raise ValueError("scientific task has no exact atomic operation") from error
    if variant.kind == ExactAlgebraKind.EXPONENT_LAWS:
        outcome_targets = {
            "POSITIVE": ExactAssessmentTarget.EXPONENT_POWER_OF_POWER,
            "ZERO": ExactAssessmentTarget.EXPONENT_ZERO,
            "NEGATIVE": ExactAssessmentTarget.EXPONENT_NEGATIVE_RECIPROCAL,
        }
        try:
            return outcome_targets[variant.parameters["outcome"]]
        except (KeyError, TypeError) as error:
            raise ValueError("exponent task has no exact atomic outcome") from error
    raise ValueError("assessment kind has no exact atomic target")


def _expected_supporting_targets(
    variant: HiddenExactVariant,
) -> tuple[ExactAssessmentTarget, ...]:
    """Return evidence-only atoms permitted by this exact task structure."""

    if variant.kind in {
        ExactAlgebraKind.POLYNOMIAL_QUOTIENT,
        ExactAlgebraKind.POLYNOMIAL_AREA_TRANSFER,
    }:
        return (ExactAssessmentTarget.DIVIDE_MONOMIALS,)
    if variant.kind == ExactAlgebraKind.EXPONENT_LAWS:
        return tuple(
            target
            for target in (
                ExactAssessmentTarget.EXPONENT_PRODUCT,
                ExactAssessmentTarget.EXPONENT_QUOTIENT,
                ExactAssessmentTarget.EXPONENT_POWER_OF_POWER,
            )
            if target != variant.primary_target
        )
    if variant.kind == ExactAlgebraKind.GEOMETRY_TRANSFER:
        return (ExactAssessmentTarget.EXPONENT_PRODUCT,)
    return ()


def _validate_atomic_binding(variant: HiddenExactVariant) -> None:
    """Fail closed on broad, missing, duplicated or structurally wrong bindings."""

    if not isinstance(variant.primary_target, ExactAssessmentTarget):
        raise TypeError("primary target must be one accepted exact assessment atom")
    if variant.primary_target != _expected_primary_target(variant):
        raise ValueError("primary target does not match the hidden task structure")
    if any(
        not isinstance(target, ExactAssessmentTarget)
        for target in variant.supporting_targets
    ):
        raise ValueError("supporting targets must be accepted exact assessment atoms")
    if len(set(variant.supporting_targets)) != len(variant.supporting_targets):
        raise ValueError("supporting targets must not contain duplicates")
    if variant.primary_target in variant.supporting_targets:
        raise ValueError("the primary target must not be duplicated as supporting evidence")
    if variant.supporting_targets != _expected_supporting_targets(variant):
        raise ValueError("supporting targets do not match the hidden task structure")


def _solutions(value: object) -> tuple[Fraction, ...]:
    if not isinstance(value, list) or len(value) > 2:
        raise ValueError("solutions must be a list of at most two exact numbers")
    parsed = tuple(sorted({_parse_fraction(item) for item in value}))
    if len(parsed) != len(value):
        raise ValueError("solution set must not contain duplicates")
    return parsed


def _parse_exact_real(value: object) -> ExactReal:
    required = {"rational", "radical_coefficient", "radicand"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(
            "each exact real requires rational, radical_coefficient and radicand"
        )
    rational = _parse_fraction(value["rational"])
    radical_coefficient = _parse_fraction(value["radical_coefficient"])
    radicand = _integer(value["radicand"])
    if radicand < 0:
        raise ValueError("exact-real radicand must be non-negative")
    if radical_coefficient == 0:
        if radicand != 0:
            raise ValueError("a rational exact real must use radicand zero")
        return ExactReal(rational)
    if radicand <= 1:
        raise ValueError("a radical exact real requires radicand greater than one")
    if math.isqrt(radicand) ** 2 == radicand:
        raise ValueError("perfect-square radicals must be simplified")
    if any(radicand % (factor * factor) == 0 for factor in range(2, math.isqrt(radicand) + 1)):
        raise ValueError("radicand must be square-free")
    return ExactReal(rational, radical_coefficient, radicand)


def _root_solutions(value: object) -> tuple[ExactReal, ...]:
    if not isinstance(value, list) or len(value) > 2:
        raise ValueError("solutions must be a list of at most two exact reals")
    parsed = tuple(sorted({_parse_exact_real(item) for item in value}))
    if len(parsed) != len(value):
        raise ValueError("solution set must not contain duplicates")
    return parsed


def _substitution_checks(
    value: object,
) -> tuple[tuple[Fraction, Fraction, Fraction], ...]:
    if not isinstance(value, list) or len(value) > 2:
        raise ValueError("substitution_checks must be a list of at most two records")
    required = {"solution", "left_value", "right_value"}
    parsed: list[tuple[Fraction, Fraction, Fraction]] = []
    for record in value:
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError(
                "each substitution check requires solution, left_value and right_value"
            )
        parsed.append(
            _substitution_record(
                _parse_fraction(record["solution"]),
                _parse_fraction(record["left_value"]),
                _parse_fraction(record["right_value"]),
            )
        )
    if len({record[0] for record in parsed}) != len(parsed):
        raise ValueError("substitution checks must not repeat a solution")
    return tuple(sorted(parsed, key=lambda record: record[0]))


def _root_substitution_checks(
    value: object,
) -> tuple[tuple[ExactReal, ExactReal, ExactReal], ...]:
    if not isinstance(value, list) or len(value) > 2:
        raise ValueError("substitution_checks must be a list of at most two records")
    required = {"solution", "left_value", "right_value"}
    parsed: list[tuple[ExactReal, ExactReal, ExactReal]] = []
    for record in value:
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError(
                "each substitution check requires solution, left_value and right_value"
            )
        parsed.append(
            (
                _parse_exact_real(record["solution"]),
                _parse_exact_real(record["left_value"]),
                _parse_exact_real(record["right_value"]),
            )
        )
    if len({record[0] for record in parsed}) != len(parsed):
        raise ValueError("substitution checks must not repeat a solution")
    return tuple(sorted(parsed, key=lambda record: record[0]))


def _terms(
    value: object,
    *,
    minimum: int = 1,
    maximum: int = 4,
) -> tuple[tuple[Fraction, int, int], ...]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"polynomial response requires {minimum} to {maximum} term records")
    parsed: list[tuple[Fraction, int, int]] = []
    for term in value:
        if not isinstance(term, dict) or set(term) != {"coefficient", "x_exponent", "y_exponent"}:
            raise ValueError("each term requires coefficient, x_exponent and y_exponent")
        parsed.append(
            (
                _parse_canonical_fraction(term["coefficient"]),
                _integer(term["x_exponent"]),
                _integer(term["y_exponent"]),
            )
        )
    if len({(term[1], term[2]) for term in parsed}) != len(parsed):
        raise ValueError("polynomial term records must have unique exponent pairs")
    return tuple(sorted(parsed, key=lambda term: (-term[1], -term[2], term[0])))


def _reconstruction(
    value: object,
    *,
    minimum: int = 1,
    maximum: int = 4,
) -> tuple[tuple[tuple[Fraction, int, int], ...], ...]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"reconstruction requires {minimum} to {maximum} records")
    required = {"quotient_term", "divisor_term", "product_term"}
    parsed: list[tuple[tuple[Fraction, int, int], ...]] = []
    for record in value:
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError(
                "each reconstruction requires quotient_term, divisor_term and product_term"
            )
        quotient = _terms([record["quotient_term"]], maximum=1)[0]
        divisor = _terms([record["divisor_term"]], maximum=1)[0]
        product = _terms([record["product_term"]], maximum=1)[0]
        if _term_multiply(quotient, divisor) != product:
            raise ValueError("reconstruction product must be recomputed exactly")
        parsed.append((quotient, divisor, product))
    quotient_powers = [(record[0][1], record[0][2]) for record in parsed]
    if len(set(quotient_powers)) != len(quotient_powers):
        raise ValueError("reconstruction must not repeat quotient exponent pairs")
    return tuple(sorted(parsed, key=lambda record: (-record[0][1], -record[0][2], record[0][0])))


def _polynomial_units(value: object) -> tuple[str, str]:
    if not isinstance(value, dict) or set(value) != {"width", "area"}:
        raise ValueError("transfer units require width and area fields")
    if value["width"] != "units" or value["area"] != "square units":
        raise ValueError("transfer units must preserve width and area dimensions")
    return value["width"], value["area"]


def _normalize_response(
    kind: ExactAlgebraKind, response: Mapping[str, object]
) -> dict[str, object]:
    if not isinstance(response, dict):
        raise TypeError("response must be an object")
    if kind == ExactAlgebraKind.LINEAR_EQUATION:
        if set(response) != {"classification", "solutions", "substitution_checks"}:
            raise ValueError("equation response fields do not match the contract")
        classification = response["classification"]
        if classification not in {"ONE_REAL_SOLUTION", "TWO_REAL_SOLUTIONS", "NO_REAL_SOLUTIONS"}:
            raise ValueError("unsupported solution classification")
        return {
            "classification": classification,
            "solutions": _solutions(response["solutions"]),
            "substitution_checks": _substitution_checks(response["substitution_checks"]),
        }
    if kind == ExactAlgebraKind.ROOT_EQUATION:
        if set(response) != {"classification", "solutions", "substitution_checks"}:
            raise ValueError("equation response fields do not match the contract")
        classification = response["classification"]
        if classification not in {"ONE_REAL_SOLUTION", "TWO_REAL_SOLUTIONS", "NO_REAL_SOLUTIONS"}:
            raise ValueError("unsupported solution classification")
        return {
            "classification": classification,
            "solutions": _root_solutions(response["solutions"]),
            "substitution_checks": _root_substitution_checks(response["substitution_checks"]),
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
        required = {
            "terms",
            "domain_restrictions",
            "coefficient_reason",
            "exponent_reason",
            "reconstruction",
        }
        if set(response) != required:
            raise ValueError("polynomial response fields do not match the contract")
        coefficient_reason = response["coefficient_reason"]
        if coefficient_reason not in {
            "DIVIDEND_COEFFICIENT_DIVIDED_BY_DIVISOR_COEFFICIENT",
            "DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT",
        }:
            raise ValueError("unsupported coefficient_reason")
        exponent_reason = response["exponent_reason"]
        if exponent_reason not in {
            "DIVIDEND_EXPONENT_MINUS_DIVISOR_EXPONENT",
            "DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT",
        }:
            raise ValueError("unsupported exponent_reason")
        return {
            "terms": _terms(response["terms"]),
            "domain_restrictions": _restrictions(response["domain_restrictions"]),
            "coefficient_reason": coefficient_reason,
            "exponent_reason": exponent_reason,
            "reconstruction": _reconstruction(response["reconstruction"]),
        }
    if kind == ExactAlgebraKind.POLYNOMIAL_AREA_TRANSFER:
        required = {
            "width_terms",
            "total_width_terms",
            "domain_restrictions",
            "multiplication_checks",
            "units",
        }
        if set(response) != required:
            raise ValueError("polynomial transfer fields do not match the contract")
        return {
            "width_terms": _terms(response["width_terms"], minimum=2, maximum=2),
            "total_width_terms": _terms(response["total_width_terms"], minimum=2, maximum=2),
            "domain_restrictions": _restrictions(response["domain_restrictions"]),
            "multiplication_checks": _reconstruction(
                response["multiplication_checks"], minimum=2, maximum=2
            ),
            "units": _polynomial_units(response["units"]),
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

    _validate_atomic_binding(variant)
    if already_answered:
        raise ValueError("variant already answered")
    normalized = _normalize_response(variant.kind, response)
    if normalized == dict(variant.oracle):
        return ExactScore(is_correct=True, misconception_code=None)
    for code, misconception_response in variant.misconception_responses.items():
        if normalized == dict(misconception_response):
            return ExactScore(is_correct=False, misconception_code=code)
    return ExactScore(is_correct=False, misconception_code=None)
