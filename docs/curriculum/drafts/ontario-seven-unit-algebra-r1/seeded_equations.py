"""Draft-only deterministic variants for the Issue #337 equation slice.

This module is deliberately outside the runtime registry.  It supplies reviewable
content/oracle evidence without activating a lesson, assessment, or mastery path.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
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
    left_coefficient: int
    left_constant: Fraction
    right_coefficient: int
    right_constant: Fraction
    distribution_factor: int | None
    distribution_shift: int | None
    options: tuple[str, ...]
    teacher_answer: dict[str, Any]

    def public_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
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
        teacher_answer=teacher_answer,
    )
