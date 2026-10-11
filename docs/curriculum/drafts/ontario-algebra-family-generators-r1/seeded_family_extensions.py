"""Draft-only exact generators for the non-equation Issue #337 gaps.

The module is intentionally outside ``app.domains`` and the runtime registry.
It creates review fixtures only; it cannot award mastery or write learner data.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any

NAMESPACE = "ontario-algebra-family-generators-r1"
MODES = frozenset({"guided", "independent"})
STRUCTURES = (
    "MONOMIAL_QUOTIENT",
    "POLYNOMIAL_BY_MONOMIAL",
    "COMBINED_EXPONENT_LAWS",
    "ROOT_EQUATION",
    "SCIENTIFIC_NOTATION",
)
MISCONCEPTIONS = frozenset(
    {
        "POLY.DIV.COEFFICIENT_RECIPROCAL",
        "POLY.DIV.ADD_EXPONENTS",
        "POLY.DIV.ONE_TERM_ONLY",
        "EXP.NEGATIVE_IS_NEGATIVE_VALUE",
        "EXP.GEOMETRY.POWER_NOT_DISTRIBUTED",
        "ROOT.PRINCIPAL_ONLY",
        "SCI.EXPONENT.DIRECTION",
        "SCI.NOT_NORMALIZED",
    }
)


def _validate(seed: int, mode: str) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")


def _fraction_text(value: Fraction | int) -> str:
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _pow_fraction(base: int, exponent: int) -> Fraction:
    if exponent >= 0:
        return Fraction(base**exponent)
    return Fraction(1, base ** (-exponent))


@dataclass(frozen=True)
class Monomial:
    coefficient: Fraction
    powers: tuple[tuple[str, int], ...]

    @classmethod
    def make(cls, coefficient: Fraction | int, powers: dict[str, int]) -> Monomial:
        return cls(Fraction(coefficient), tuple(sorted((name, power) for name, power in powers.items() if power)))

    def power_map(self) -> dict[str, int]:
        return dict(self.powers)

    def multiply(self, other: Monomial) -> Monomial:
        powers = self.power_map()
        for name, exponent in other.powers:
            powers[name] = powers.get(name, 0) + exponent
        return Monomial.make(self.coefficient * other.coefficient, powers)

    def evaluate(self, values: dict[str, Fraction | int]) -> Fraction:
        result = self.coefficient
        for name, exponent in self.powers:
            value = Fraction(values[name])
            if value == 0 and exponent < 0:
                raise ZeroDivisionError(f"{name} must be nonzero")
            result *= _pow_fraction(value.numerator, exponent) / _pow_fraction(value.denominator, exponent)
        return result

    def text(self) -> str:
        pieces: list[str] = []
        if self.coefficient == -1 and self.powers:
            pieces.append("-")
        elif self.coefficient != 1 or not self.powers:
            pieces.append(_fraction_text(self.coefficient))
        for name, exponent in self.powers:
            pieces.append(name if exponent == 1 else f"{name}^{exponent}")
        return "".join(pieces)


def divide_monomials(dividend: Monomial, divisor: Monomial) -> tuple[Monomial, tuple[str, ...]]:
    """Divide exactly and retain restrictions from the original divisor."""

    if divisor.coefficient == 0:
        raise ZeroDivisionError("monomial divisor coefficient cannot be zero")
    powers = dividend.power_map()
    for name, exponent in divisor.powers:
        powers[name] = powers.get(name, 0) - exponent
    quotient = Monomial.make(dividend.coefficient / divisor.coefficient, powers)
    restrictions = tuple(sorted(name for name, exponent in divisor.powers if exponent > 0))
    return quotient, restrictions


def normalize_scientific(coefficient: Fraction | int, exponent: int) -> tuple[Fraction, int]:
    coefficient = Fraction(coefficient)
    if coefficient == 0:
        return Fraction(0), 0
    while abs(coefficient) >= 10:
        coefficient /= 10
        exponent += 1
    while abs(coefficient) < 1:
        coefficient *= 10
        exponent -= 1
    return coefficient, exponent


@dataclass(frozen=True)
class DraftVariant:
    variant_id: str
    mode: str
    structure: str
    canonical_family: str
    prompt: str
    response_schema: tuple[str, ...]
    parameters: dict[str, Any]
    teacher_oracle: dict[str, Any]

    def public_payload(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "canonical_family": self.canonical_family,
            "prompt": self.prompt,
            "response_schema": list(self.response_schema),
        }


def _monomial_quotient(rng: random.Random, variant_id: str, mode: str) -> DraftVariant:
    divisor = Monomial.make(
        rng.choice((-6, -4, -3, 2, 3, 4, 6)),
        {"x": rng.randint(2, 5), "y": rng.randint(1, 4)},
    )
    quotient = Monomial.make(
        rng.choice((-5, -3, -2, 2, 3, 5)),
        {"x": rng.randint(-2, 3), "y": rng.randint(-1, 3)},
    )
    dividend = quotient.multiply(divisor)
    restrictions = tuple(name for name, _ in divisor.powers)
    prompt = (
        f"Simplify ({dividend.text()}) / ({divisor.text()}) exactly. "
        "Use positive exponents where practical and state every restriction from the original divisor."
    )
    return DraftVariant(
        variant_id,
        mode,
        "MONOMIAL_QUOTIENT",
        "MATH.EE.POLYNOMIAL_OPERATIONS",
        prompt,
        ("exact_expression", "domain_restrictions", "law_explanation"),
        {"dividend": dividend, "divisor": divisor},
        {"quotient": quotient, "domain_restrictions": restrictions},
    )


def _polynomial_quotient(rng: random.Random, variant_id: str, mode: str) -> DraftVariant:
    divisor = Monomial.make(
        rng.choice((-5, -3, -2, 2, 3, 5)),
        {"x": rng.randint(1, 3), "y": rng.randint(0, 2)},
    )
    q1 = Monomial.make(rng.choice((-6, -4, 3, 5, 7)), {"x": rng.randint(1, 3), "y": rng.randint(0, 2)})
    q2 = Monomial.make(rng.choice((-7, -5, -3, 2, 4, 6)), {"x": rng.randint(0, 2), "y": rng.randint(0, 2)})
    if q1.powers == q2.powers:
        q2 = Monomial.make(q2.coefficient, {**q2.power_map(), "y": q2.power_map().get("y", 0) + 1})
    dividend_terms = (q1.multiply(divisor), q2.multiply(divisor))
    restrictions = tuple(name for name, _ in divisor.powers)
    joined = " + ".join(term.text() for term in dividend_terms).replace("+ -", "- ")
    prompt = (
        f"Divide ({joined}) by ({divisor.text()}) term by term. "
        "Give the exact simplified polynomial and state the original-domain restrictions."
    )
    return DraftVariant(
        variant_id,
        mode,
        "POLYNOMIAL_BY_MONOMIAL",
        "MATH.EE.POLYNOMIAL_OPERATIONS",
        prompt,
        ("exact_terms", "domain_restrictions", "distribution_explanation"),
        {"dividend_terms": dividend_terms, "divisor": divisor},
        {"quotient_terms": (q1, q2), "domain_restrictions": restrictions},
    )


def _combined_exponents(rng: random.Random, variant_id: str, mode: str) -> DraftVariant:
    base = rng.randint(2, 7)
    m, n = rng.randint(2, 7), rng.randint(2, 6)
    p, q = rng.randint(2, 5), rng.randint(2, 4)
    exponent = m + n - p * q
    if exponent == 0:
        n += 1
        exponent += 1
    prompt = (
        f"Simplify ({base}^{m} x {base}^{n}) / (({base}^{p})^{q}) as one power, "
        "then give its exact value and justify each exponent law."
    )
    return DraftVariant(
        variant_id,
        mode,
        "COMBINED_EXPONENT_LAWS",
        "MATH.NS.EXPONENTS",
        prompt,
        ("single_power", "exact_value", "law_explanation"),
        {"base": base, "m": m, "n": n, "p": p, "q": q},
        {"result_exponent": exponent, "exact_value": _pow_fraction(base, exponent)},
    )


def generate_geometry_transfer(seed: int, mode: str) -> DraftVariant:
    """Build a fresh exponent-law transfer through area or volume."""

    _validate(seed, mode)
    rng = random.Random(f"{NAMESPACE}:geometry-transfer:{mode}:{seed}")
    base = rng.randint(2, 5)
    dimension_coefficient = rng.randint(2, 5)
    dimension_exponent = rng.randint(1, 4)
    shape = "SQUARE" if seed % 2 == 0 else "CUBE"
    dimensional_power = 2 if shape == "SQUARE" else 3
    measure_name = "area" if shape == "SQUARE" else "volume"
    unit = "square units" if shape == "SQUARE" else "cubic units"
    result_coefficient = dimension_coefficient**dimensional_power
    result_exponent = dimension_exponent * dimensional_power
    exact_value = result_coefficient * base**result_exponent
    prompt = (
        f"A {shape.lower()} has side length {dimension_coefficient}({base}^{dimension_exponent}) units. "
        f"Express its {measure_name} as a coefficient times one power of {base}, then evaluate it exactly "
        f"and label the answer in {unit}."
    )
    item = DraftVariant(
        f"{NAMESPACE}:geometry-transfer:{mode}:{seed}",
        mode,
        "EXPONENT_GEOMETRY_TRANSFER",
        "MATH.NS.EXPONENTS",
        prompt,
        ("symbolic_measure", "exact_measure", "units", "power_of_power_explanation"),
        {
            "shape": shape,
            "base": base,
            "dimension_coefficient": dimension_coefficient,
            "dimension_exponent": dimension_exponent,
            "dimensional_power": dimensional_power,
        },
        {
            "result_coefficient": result_coefficient,
            "result_exponent": result_exponent,
            "exact_value": exact_value,
            "units": unit,
        },
    )
    prefix = "Guided exploration" if mode == "guided" else "Independent transfer"
    return replace(item, prompt=f"{prefix}: {item.prompt}")


def _root_equation(rng: random.Random, variant_id: str, mode: str) -> DraftVariant:
    coefficient = rng.choice((-5, -3, -2, 2, 3, 5))
    shift = rng.randint(-8, 8)
    no_real = rng.random() < 0.35
    root = rng.randint(2, 9)
    radicand = -(root * root) if no_real else root * root
    prompt = (
        f"Solve ({coefficient}x + ({shift}))^2 = {radicand} over the real numbers. "
        "Give the complete solution set and distinguish it from a principal square-root value."
    )
    if no_real:
        solutions: tuple[Fraction, ...] = ()
        classification = "NO_REAL_SOLUTIONS"
    else:
        solutions = tuple(sorted({Fraction(root - shift, coefficient), Fraction(-root - shift, coefficient)}))
        classification = "TWO_REAL_SOLUTIONS"
    return DraftVariant(
        variant_id,
        mode,
        "ROOT_EQUATION",
        "MATH.NS.ROOTS",
        prompt,
        ("solution_set", "classification", "substitution_check"),
        {"coefficient": coefficient, "shift": shift, "radicand": radicand},
        {"solutions": solutions, "classification": classification},
    )


def _scientific(rng: random.Random, variant_id: str, mode: str, seed: int) -> DraftVariant:
    operation = ("TO_SCIENTIFIC", "TO_ORDINARY", "MULTIPLY", "DIVIDE")[seed % 4]
    c1 = Fraction(rng.randint(12, 98), 10)
    e1 = rng.randint(-7, 7)
    c2 = Fraction(rng.randint(12, 98), 10)
    e2 = rng.randint(-7, 7)
    if operation == "TO_SCIENTIFIC":
        source_coefficient = c1 * rng.choice((10, 100, Fraction(1, 10)))
        source_exponent = e1 - (2 if abs(source_coefficient) >= 100 else 1)
        ordinary = source_coefficient * _pow_fraction(10, source_exponent)
        coefficient, exponent = normalize_scientific(ordinary, 0)
        prompt = f"Write the exact value {_fraction_text(ordinary)} in normalized scientific notation."
    elif operation == "TO_ORDINARY":
        coefficient, exponent = normalize_scientific(c1, e1)
        ordinary = coefficient * _pow_fraction(10, exponent)
        prompt = (
            f"Write ({_fraction_text(coefficient)} x 10^{exponent}) as an exact ordinary number "
            "and explain the direction of the decimal shift."
        )
    elif operation == "MULTIPLY":
        raw_coefficient = c1 * c2
        raw_exponent = e1 + e2
        coefficient, exponent = normalize_scientific(raw_coefficient, raw_exponent)
        ordinary = coefficient * _pow_fraction(10, exponent)
        prompt = (
            f"Compute ({_fraction_text(c1)} x 10^{e1})({_fraction_text(c2)} x 10^{e2}) "
            "and normalize the exact result."
        )
    else:
        raw_coefficient = c1 / c2
        raw_exponent = e1 - e2
        coefficient, exponent = normalize_scientific(raw_coefficient, raw_exponent)
        ordinary = coefficient * _pow_fraction(10, exponent)
        prompt = (
            f"Compute ({_fraction_text(c1)} x 10^{e1}) / ({_fraction_text(c2)} x 10^{e2}) "
            "and normalize the exact result."
        )
    return DraftVariant(
        variant_id,
        mode,
        "SCIENTIFIC_NOTATION",
        "MATH.NS.SCIENTIFIC_NOTATION",
        prompt,
        ("normalized_coefficient", "power_of_ten", "exact_ordinary_value", "normalization_explanation"),
        {"operation": operation, "c1": c1, "e1": e1, "c2": c2, "e2": e2},
        {"coefficient": coefficient, "exponent": exponent, "ordinary_value": ordinary},
    )


def generate(seed: int, mode: str) -> DraftVariant:
    """Generate a deterministic review variant in a mode-separated namespace."""

    _validate(seed, mode)
    rng = random.Random(f"{NAMESPACE}:{mode}:{seed}")
    structure = STRUCTURES[seed % len(STRUCTURES)]
    variant_id = f"{NAMESPACE}:{mode}:{seed}"
    if structure == "MONOMIAL_QUOTIENT":
        item = _monomial_quotient(rng, variant_id, mode)
    elif structure == "POLYNOMIAL_BY_MONOMIAL":
        item = _polynomial_quotient(rng, variant_id, mode)
    elif structure == "COMBINED_EXPONENT_LAWS":
        item = _combined_exponents(rng, variant_id, mode)
    elif structure == "ROOT_EQUATION":
        item = _root_equation(rng, variant_id, mode)
    else:
        item = _scientific(rng, variant_id, mode, seed)
    prefix = "Guided exploration" if mode == "guided" else "Independent task"
    return replace(item, prompt=f"{prefix}: {item.prompt}")


def diagnose_response(evidence: dict[str, bool]) -> str | None:
    """Map concrete response evidence to one misconception; never use generic hints."""

    if not isinstance(evidence, dict):
        raise TypeError("evidence must be a dictionary")
    allowed = {
        "response_correct",
        "coefficient_division_reversed",
        "quotient_exponents_added",
        "all_polynomial_terms_divided",
        "negative_exponent_written_as_negative_value",
        "geometry_power_applied_to_coefficient",
        "geometry_power_applied_to_exponent",
        "equation_requires_solution_set",
        "only_principal_root_given",
        "decimal_shift_matches_exponent",
        "coefficient_normalized",
    }
    unknown = set(evidence) - allowed
    if unknown:
        raise ValueError(f"Unsupported evidence fields: {sorted(unknown)!r}")
    if any(type(value) is not bool for value in evidence.values()):
        raise TypeError("all evidence values must be booleans")
    if evidence.get("response_correct"):
        return None
    if evidence.get("coefficient_division_reversed"):
        return "POLY.DIV.COEFFICIENT_RECIPROCAL"
    if evidence.get("quotient_exponents_added"):
        return "POLY.DIV.ADD_EXPONENTS"
    if evidence.get("all_polynomial_terms_divided") is False:
        return "POLY.DIV.ONE_TERM_ONLY"
    if evidence.get("negative_exponent_written_as_negative_value"):
        return "EXP.NEGATIVE_IS_NEGATIVE_VALUE"
    if evidence.get("geometry_power_applied_to_coefficient") and not evidence.get(
        "geometry_power_applied_to_exponent"
    ):
        return "EXP.GEOMETRY.POWER_NOT_DISTRIBUTED"
    if evidence.get("equation_requires_solution_set") and evidence.get("only_principal_root_given"):
        return "ROOT.PRINCIPAL_ONLY"
    if evidence.get("decimal_shift_matches_exponent") is False:
        return "SCI.EXPONENT.DIRECTION"
    if evidence.get("coefficient_normalized") is False:
        return "SCI.NOT_NORMALIZED"
    return None
