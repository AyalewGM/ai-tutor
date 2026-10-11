"""Draft-only deterministic variants for the Issue #337 equation slice.

This module is deliberately outside the runtime registry.  It supplies reviewable
content/oracle evidence without activating a lesson, assessment, or mastery path.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any

NAMESPACE = "algebra-equation-reasoning-r1"
MODES = frozenset({"guided", "independent"})
STRUCTURES = (
    "TWO_STEP_RATIONAL",
    "NEGATIVE_DISTRIBUTION",
    "VARIABLES_BOTH_SIDES",
    "EQUIVALENT_EQUATIONS",
)
TRANSFER_STRUCTURES = ("PERIMETER_MODEL", "SERVICE_RATE_MODEL")
MISCONCEPTIONS = frozenset(
    {
        "EQ.OP.ONE_SIDE",
        "DIST.PARTIAL",
        "DIST.NEGATIVE_DROPPED",
        "EQ.DENOMINATOR_IGNORED",
        "EQ.FALSE_EQUIVALENCE",
    }
)


def _text(value: Fraction | int) -> str:
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _term(coefficient: int, variable: str = "x") -> str:
    if coefficient == 1:
        return variable
    if coefficient == -1:
        return f"-{variable}"
    return f"{coefficient}{variable}"


def _linear(coefficient: int, constant: Fraction, variable: str = "x") -> str:
    first = _term(coefficient, variable)
    if constant == 0:
        return first
    sign = "+" if constant > 0 else "-"
    return f"{first} {sign} {_text(abs(constant))}"


def _solution(rng: random.Random) -> Fraction:
    denominator = rng.choice((2, 3, 4, 5))
    numerator = rng.choice(tuple(n for n in range(-19, 20) if n and n % denominator))
    return Fraction(numerator, denominator)


@dataclass(frozen=True)
class EquationVariant:
    variant_id: str
    mode: str
    structure: str
    prompt: str
    variable: str
    left_coefficient: Fraction | int
    left_constant: Fraction
    right_coefficient: Fraction | int
    right_constant: Fraction
    distribution_factor: int | None
    distribution_shift: int | None
    options: tuple[str, ...]
    response_schema: tuple[str, ...]
    teacher_answer: dict[str, Any]

    def public_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
            "response_schema": list(self.response_schema),
        }
        if self.options:
            payload["options"] = list(self.options)
        return payload


def generate(seed: int, mode: str) -> EquationVariant:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")

    rng = random.Random(f"{NAMESPACE}:{mode}:{seed}")
    structure = STRUCTURES[seed % len(STRUCTURES)]
    solution = _solution(rng)
    variable = rng.choice(("x", "n", "p"))
    options: tuple[str, ...] = ()
    factor: int | None = None
    shift: int | None = None

    if structure == "TWO_STEP_RATIONAL":
        left_coefficient = rng.choice((-7, -6, -5, -4, -3, -2, 2, 3, 4, 5))
        left_constant = Fraction(rng.choice(tuple(n for n in range(-9, 10) if n)))
        right_coefficient = 0
        right_constant = left_coefficient * solution + left_constant
        equation = f"{_linear(left_coefficient, left_constant, variable)} = {_text(right_constant)}"
        prompt = f"Solve {equation}. Keep the answer exact, then check it by substitution."
    elif structure == "NEGATIVE_DISTRIBUTION":
        factor = rng.choice((-6, -5, -4, -3, -2))
        shift = rng.choice(tuple(n for n in range(-6, 7) if n))
        outside = Fraction(rng.choice(tuple(n for n in range(-8, 9) if n)))
        left_coefficient = factor
        left_constant = Fraction(factor * shift) + outside
        right_coefficient = 0
        right_constant = left_coefficient * solution + left_constant
        inside = f"{variable} {'+' if shift > 0 else '-'} {abs(shift)}"
        equation = f"{factor}({inside}) {'+' if outside > 0 else '-'} {abs(outside)} = {_text(right_constant)}"
        prompt = f"Solve {equation}. Explain how the negative factor affects both terms, then substitute to check."
    elif structure == "VARIABLES_BOTH_SIDES":
        left_coefficient = rng.choice((-8, -7, -5, -3, 3, 5, 7))
        right_coefficient = rng.choice(tuple(n for n in range(-6, 7) if n != left_coefficient))
        left_constant = Fraction(rng.randint(-9, 9))
        right_constant = (left_coefficient - right_coefficient) * solution + left_constant
        equation = (
            f"{_linear(left_coefficient, left_constant, variable)} = "
            f"{_linear(right_coefficient, right_constant, variable)}"
        )
        prompt = f"Solve {equation} by applying equality-preserving operations to both sides. Verify by substitution."
    else:
        left_coefficient = rng.choice((-6, -5, -4, 3, 4, 5, 6))
        left_constant = Fraction(rng.randint(-8, 8))
        right_coefficient = 0
        right_constant = left_coefficient * solution + left_constant
        scale = rng.choice((-4, -3, -2, 2, 3, 4))
        correct = f"{_linear(scale * left_coefficient, scale * left_constant, variable)} = {_text(scale * right_constant)}"
        distractors = (
            f"{_linear(scale * left_coefficient, left_constant, variable)} = {_text(scale * right_constant)}",
            f"{_linear(scale * left_coefficient, scale * left_constant, variable)} = {_text(right_constant)}",
            f"{_linear(-scale * left_coefficient, scale * left_constant, variable)} = {_text(scale * right_constant)}",
        )
        option_list = [correct, *distractors]
        rng.shuffle(option_list)
        options = tuple(option_list)
        equation = f"{_linear(left_coefficient, left_constant, variable)} = {_text(right_constant)}"
        prompt = (
            f"Which option is equivalent to {equation}? Justify the operation applied to both sides, "
            "then solve and check both equations."
        )

    left_value = left_coefficient * solution + left_constant
    right_value = right_coefficient * solution + right_constant
    teacher_answer: dict[str, Any] = {
        "solution": _text(solution),
        "left_at_solution": _text(left_value),
        "right_at_solution": _text(right_value),
        "substitution_verified": left_value == right_value,
    }
    if options:
        scale_equation = next(
            option
            for option in options
            if option
            == f"{_linear(scale * left_coefficient, scale * left_constant, variable)} = {_text(scale * right_constant)}"
        )
        teacher_answer["equivalent_option_index"] = options.index(scale_equation)

    return EquationVariant(
        variant_id=f"{NAMESPACE}:{mode}:{seed}",
        mode=mode,
        structure=structure,
        prompt=prompt,
        variable=variable,
        left_coefficient=left_coefficient,
        left_constant=left_constant,
        right_coefficient=right_coefficient,
        right_constant=right_constant,
        distribution_factor=factor,
        distribution_shift=shift,
        options=options,
        response_schema=(
            "exact_solution",
            "substitution_left",
            "substitution_right",
            "transformation_justification",
        ),
        teacher_answer=teacher_answer,
    )


@dataclass(frozen=True)
class TransferVariant:
    variant_id: str
    mode: str
    structure: str
    prompt: str
    response_schema: tuple[str, ...]
    model_parameters: dict[str, Fraction | int]
    teacher_answer: dict[str, str]

    def public_payload(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
            "response_schema": list(self.response_schema),
        }


def generate_transfer(seed: int, mode: str) -> TransferVariant:
    """Create an unfamiliar, multi-field context without exposing its oracle."""

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")

    rng = random.Random(f"{NAMESPACE}:transfer:{mode}:{seed}")
    structure = TRANSFER_STRUCTURES[seed % len(TRANSFER_STRUCTURES)]
    response_schema = (
        "relationship_equation",
        "unknown_value",
        "unknown_unit",
        "derived_quantity",
        "derived_quantity_unit",
        "verification_left",
        "verification_left_unit",
        "verification_right",
        "verification_right_unit",
        "model_explanation",
    )

    if structure == "PERIMETER_MODEL":
        width = rng.randint(3, 12)
        multiplier = rng.choice((2, 3, 4))
        offset = rng.randint(1, 8)
        length = multiplier * width + offset
        perimeter = 2 * width + 2 * length
        rectangle_context = "community garden" if mode == "guided" else "solar-panel frame"
        prompt = (
            f"A rectangular {rectangle_context} has a length that is "
            f"{multiplier} times its width plus {offset} metres. Its perimeter is "
            f"{perimeter} metres. Define the unknown, construct one equation, find both "
            "dimensions, and verify the perimeter with units."
        )
        teacher_answer = {
            "relationship_equation": f"2w + 2({multiplier}w + {offset}) = {perimeter}",
            "unknown_value": str(width),
            "unknown_unit": "metres",
            "derived_quantity": str(length),
            "derived_quantity_unit": "metres",
            "verification_left": str(perimeter),
            "verification_left_unit": "metres",
            "verification_right": str(perimeter),
            "verification_right_unit": "metres",
            "model_explanation": "Two widths plus two related lengths equal the perimeter.",
        }
        model_parameters: dict[str, Fraction | int] = {
            "width": width,
            "length": length,
            "multiplier": multiplier,
            "offset": offset,
            "perimeter": perimeter,
        }
    else:
        sessions = rng.randint(3, 12)
        denominator = rng.choice((2, 4))
        rate = Fraction(rng.choice((3, 5, 7, 9, 11)), denominator)
        fixed_fee = Fraction(rng.randint(2, 9))
        total = fixed_fee + rate * sessions
        service_context = "tool-lending club" if mode == "guided" else "bike-repair membership"
        prompt = (
            f"A {service_context} charges a fixed {_text(fixed_fee)}-dollar fee plus "
            f"{_text(rate)} dollars per borrowing session. A member paid {_text(total)} "
            "dollars. Define the unknown, construct and solve an equation for the number "
            "of sessions, and verify the total with units."
        )
        teacher_answer = {
            "relationship_equation": f"{_text(fixed_fee)} + {_text(rate)}s = {_text(total)}",
            "unknown_value": str(sessions),
            "unknown_unit": "sessions",
            "derived_quantity": _text(rate * sessions),
            "derived_quantity_unit": "dollars",
            "verification_left": _text(total),
            "verification_left_unit": "dollars",
            "verification_right": _text(total),
            "verification_right_unit": "dollars",
            "model_explanation": "The total is the fixed fee plus rate times session count.",
        }
        model_parameters = {
            "sessions": sessions,
            "rate": rate,
            "fixed_fee": fixed_fee,
            "total": total,
        }

    return TransferVariant(
        variant_id=f"{NAMESPACE}:transfer:{mode}:{seed}",
        mode=mode,
        structure=structure,
        prompt=prompt,
        response_schema=response_schema,
        model_parameters=model_parameters,
        teacher_answer=teacher_answer,
    )


def diagnose_response(evidence: dict[str, object]) -> str | None:
    """Route structured step evidence; correct work never enters remediation."""

    if not isinstance(evidence, dict):
        raise TypeError("evidence must be a dictionary")
    boolean_fields = {
        "changed_left",
        "changed_right",
        "outside_factor_applied_to_variable",
        "outside_factor_applied_to_constant",
        "negative_factor_present",
        "constant_product_sign_correct",
        "denominator_present",
        "denominator_operation_both_sides",
        "equivalence_task",
        "global_nonzero_operation",
        "response_correct",
    }
    unknown = set(evidence) - boolean_fields
    if unknown:
        raise ValueError(f"Unsupported evidence fields: {sorted(unknown)!r}")
    if any(type(value) is not bool for value in evidence.values()):
        raise TypeError("all evidence values must be booleans")
    if evidence.get("response_correct") is True:
        return None

    changed_left = evidence.get("changed_left")
    changed_right = evidence.get("changed_right")
    if changed_left is not None and changed_right is not None and changed_left != changed_right:
        return "EQ.OP.ONE_SIDE"
    if (
        evidence.get("outside_factor_applied_to_variable") is True
        and evidence.get("outside_factor_applied_to_constant") is False
    ):
        return "DIST.PARTIAL"
    if (
        evidence.get("negative_factor_present") is True
        and evidence.get("outside_factor_applied_to_constant") is True
        and evidence.get("constant_product_sign_correct") is False
    ):
        return "DIST.NEGATIVE_DROPPED"
    if (
        evidence.get("denominator_present") is True
        and evidence.get("denominator_operation_both_sides") is False
    ):
        return "EQ.DENOMINATOR_IGNORED"
    if evidence.get("equivalence_task") is True and evidence.get("global_nonzero_operation") is False:
        return "EQ.FALSE_EQUIVALENCE"
    return None


def generate_repair_exit(seed: int, misconception_id: str) -> EquationVariant:
    """Return a fresh guided exit item targeted to one diagnosed misconception."""

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if misconception_id not in MISCONCEPTIONS:
        raise ValueError(f"Unsupported misconception: {misconception_id!r}")
    if misconception_id == "EQ.DENOMINATOR_IGNORED":
        rng = random.Random(f"{NAMESPACE}:repair-exit:{misconception_id}:{seed}")
        variable = rng.choice(("x", "n", "p"))
        denominator = rng.choice((3, 4, 5, 6))
        solution = _solution(rng)
        addend = Fraction(rng.choice(tuple(n for n in range(-8, 9) if n)))
        left_coefficient = Fraction(1, denominator)
        right_constant = left_coefficient * solution + addend
        prompt = (
            f"Solve {variable}/{denominator} {'+' if addend > 0 else '-'} "
            f"{_text(abs(addend))} = {_text(right_constant)}. Name the operation that "
            "undoes the denominator, apply it to the entire left and right sides, and "
            "verify the original fractional equation by substitution."
        )
        return EquationVariant(
            variant_id=f"{NAMESPACE}:repair-exit:{misconception_id}:{seed}",
            mode="guided",
            structure="TWO_STEP_RATIONAL",
            prompt=prompt,
            variable=variable,
            left_coefficient=left_coefficient,
            left_constant=addend,
            right_coefficient=0,
            right_constant=right_constant,
            distribution_factor=None,
            distribution_shift=None,
            options=(),
            response_schema=(
                "exact_solution",
                "substitution_left",
                "substitution_right",
                "transformation_justification",
            ),
            teacher_answer={
                "solution": _text(solution),
                "left_at_solution": _text(right_constant),
                "right_at_solution": _text(right_constant),
                "substitution_verified": True,
            },
        )
    target_structure = {
        "EQ.OP.ONE_SIDE": "VARIABLES_BOTH_SIDES",
        "DIST.PARTIAL": "NEGATIVE_DISTRIBUTION",
        "DIST.NEGATIVE_DROPPED": "NEGATIVE_DISTRIBUTION",
        "EQ.FALSE_EQUIVALENCE": "EQUIVALENT_EQUATIONS",
    }[misconception_id]
    target_index = STRUCTURES.index(target_structure)
    fresh_seed = 10_000 + seed * len(STRUCTURES) + target_index
    item = generate(fresh_seed, "guided")
    return replace(
        item,
        variant_id=f"{NAMESPACE}:repair-exit:{misconception_id}:{seed}",
    )
