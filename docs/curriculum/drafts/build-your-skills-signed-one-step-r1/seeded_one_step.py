"""Draft-only signed one-step equation content for Issue #337.

The module reuses the existing one-step equation family boundary. It is not
registered at runtime and never writes learner, attempt, diagnostic, or mastery
evidence.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass

NAMESPACE = "build-your-skills-signed-one-step-r1"
MODES = frozenset({"guided", "independent"})
STRUCTURES = ("ADD", "SUBTRACT", "MULTIPLY", "DIVIDE")
RESPONSE_FIELDS = (
    "inverse_operation",
    "inverse_operand",
    "transformed_left",
    "transformed_right",
    "exact_solution",
    "substitution_left",
    "substitution_right",
    "equality_reason",
)


def _nonzero_signed(rng: random.Random, low: int = 2, high: int = 9) -> int:
    value = rng.randint(low, high)
    return value if rng.choice((False, True)) else -value


def _signed(value: int) -> str:
    return f"({value})" if value < 0 else str(value)


@dataclass(frozen=True)
class OneStepVariant:
    variant_id: str
    mode: str
    structure: str
    variable: str
    operand: int
    right_value: int
    solution: int
    prompt: str
    inverse_operation: str

    def public_payload(self) -> dict[str, object]:
        """Return learner-visible fields without answer or worked-step leakage."""

        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
            "response_fields": list(RESPONSE_FIELDS),
        }

    def teacher_evidence(self) -> dict[str, object]:
        """Return exact author evidence kept outside the public payload."""

        return {
            "inverse_operation": self.inverse_operation,
            "inverse_operand": self.operand,
            "transformed_left": self.solution,
            "transformed_right": self.solution,
            "exact_solution": self.solution,
            "substitution_left": _left_value(self, self.solution),
            "substitution_right": self.right_value,
            "equality_reason": "SAME_OPERATION_APPLIED_TO_BOTH_SIDES",
        }


def _validate(seed: int, mode: str) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")


def _left_value(item: OneStepVariant, value: int) -> int:
    if item.structure == "ADD":
        return value + item.operand
    if item.structure == "SUBTRACT":
        return value - item.operand
    if item.structure == "MULTIPLY":
        return item.operand * value
    if value % item.operand:
        raise ValueError("division substitution must be exact")
    return value // item.operand


def generate(seed: int, mode: str) -> OneStepVariant:
    """Generate all four signed inverse-operation structures reproducibly."""

    _validate(seed, mode)
    rng = random.Random(f"{NAMESPACE}:{mode}:{seed}")
    structure = STRUCTURES[seed % len(STRUCTURES)]
    variable = rng.choice(("x", "n", "p", "t"))
    operand = _nonzero_signed(rng)

    if structure == "DIVIDE":
        right_value = _nonzero_signed(rng, 1, 12)
        solution = operand * right_value
        equation = f"{variable} ÷ {_signed(operand)} = {right_value}"
        inverse_operation = "MULTIPLY_BOTH_SIDES"
    else:
        solution = rng.randint(-18, 18)
        if structure == "ADD":
            right_value = solution + operand
            equation = f"{variable} + {_signed(operand)} = {right_value}"
            inverse_operation = "SUBTRACT_FROM_BOTH_SIDES"
        elif structure == "SUBTRACT":
            right_value = solution - operand
            equation = f"{variable} - {_signed(operand)} = {right_value}"
            inverse_operation = "ADD_TO_BOTH_SIDES"
        else:
            right_value = operand * solution
            equation = f"{_signed(operand)}{variable} = {right_value}"
            inverse_operation = "DIVIDE_BOTH_SIDES"

    prompt = (
        f"Solve {equation}. Predict the inverse operation, apply it to both sides, "
        "keep every sign visible, and verify in the original equation."
    )
    return OneStepVariant(
        variant_id=f"{NAMESPACE}:{mode}:{seed}",
        mode=mode,
        structure=structure,
        variable=variable,
        operand=operand,
        right_value=right_value,
        solution=solution,
        prompt=prompt,
        inverse_operation=inverse_operation,
    )


_INVERSE_ERRORS = {
    "ADD": "ADDITION_NOT_UNDONE_BY_SUBTRACTION",
    "SUBTRACT": "SUBTRACTION_NOT_UNDONE_BY_ADDITION",
    "MULTIPLY": "MULTIPLICATION_NOT_UNDONE_BY_DIVISION",
    "DIVIDE": "DIVISION_NOT_UNDONE_BY_MULTIPLICATION",
}


def diagnose_guided_response(item: OneStepVariant, response: Mapping[str, object]) -> str:
    """Evaluate guided structured evidence only; never score independent mastery."""

    if item.mode != "guided":
        return "INDEPENDENT_ASSESSMENT_NOT_SCORED_HERE"
    if not isinstance(response, Mapping) or set(response) != set(RESPONSE_FIELDS):
        return "INCOMPLETE_ONE_STEP_EVIDENCE"
    if response["inverse_operation"] != item.inverse_operation:
        return _INVERSE_ERRORS[item.structure]
    if response["inverse_operand"] != item.operand:
        return "SIGNED_INVERSE_OPERAND_ERROR"
    if response["transformed_left"] != response["transformed_right"]:
        return "ONE_SIDE_CHANGED"
    if (
        response["transformed_left"] != item.solution
        or response["exact_solution"] != item.solution
    ):
        return "SIGNED_INVERSE_RESULT_ERROR"
    if (
        response["substitution_left"] != _left_value(item, item.solution)
        or response["substitution_right"] != item.right_value
        or response["substitution_left"] != response["substitution_right"]
    ):
        return "SUBSTITUTION_CHECK_FAILED"
    if response["equality_reason"] != "SAME_OPERATION_APPLIED_TO_BOTH_SIDES":
        return "EQUALITY_PRESERVATION_NOT_EXPLAINED"
    return "CORRECT_GUIDED_PRACTICE_ONLY"


def generate_repair_exit(misconception: str, seed: int) -> OneStepVariant:
    """Return a deterministic different item targeted to one misconception."""

    if misconception not in set(_INVERSE_ERRORS.values()) | {
        "SIGNED_INVERSE_OPERAND_ERROR",
        "ONE_SIDE_CHANGED",
        "SIGNED_INVERSE_RESULT_ERROR",
        "SUBSTITUTION_CHECK_FAILED",
        "EQUALITY_PRESERVATION_NOT_EXPLAINED",
    }:
        raise ValueError(f"Unsupported misconception: {misconception!r}")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    offset = sum(ord(char) for char in misconception) % 97 + 1
    item = generate(seed + offset, "guided")
    return OneStepVariant(
        **{
            **item.__dict__,
            "variant_id": f"{NAMESPACE}:repair:{misconception}:{seed}",
        }
    )
