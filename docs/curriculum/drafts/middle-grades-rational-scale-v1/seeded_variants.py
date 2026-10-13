"""Draft-only deterministic variants for rational scale/inverse review.

This module is not imported by runtime code and performs no persistence. Its
teacher oracle and diagnostic classifier exist only to make the authored
content independently testable; they are not an assessment API.
"""

import random
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction

NAMESPACE = "middle-grades-rational-scale-v1"
MODES = frozenset({"guided", "independent"})
RESPONSE_FIELDS = (
    "operation_choice",
    "output_direction_prediction",
    "magnitude_relation",
    "inverse_strategy",
    "exact_result",
    "recomposition_check",
)


@dataclass(frozen=True)
class Variant:
    variant_id: str
    mode: str
    structure: str
    prompt: str
    input_value: Fraction
    given_value: Fraction
    hidden_quantity: str
    operation: str
    direction: str
    magnitude_relation: str
    answer: Fraction
    recomposition: str

    def public_payload(self) -> dict[str, object]:
        """Return fields safe to expose before an independent submission."""

        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
            "response_fields": list(RESPONSE_FIELDS),
        }

    def teacher_oracle(self) -> dict[str, str]:
        """Return the independently testable multi-part concept oracle."""

        return {
            "operation_choice": self.operation,
            "output_direction_prediction": self.direction,
            "magnitude_relation": self.magnitude_relation,
            "inverse_strategy": (
                "MULTIPLY_OUTPUT_BY_RECIPROCAL_OF_INPUT"
                if self.hidden_quantity == "scale"
                else "NOT_APPLICABLE"
            ),
            "exact_result": str(self.answer),
            "recomposition_check": self.recomposition,
        }


def _positive_fraction(rng: random.Random) -> Fraction:
    return Fraction(rng.randint(1, 9), rng.choice((2, 3, 4, 5, 6, 8, 10)))


def _direction(value: Fraction) -> str:
    if value == 0:
        raise ValueError("Direction is undefined for zero in this nonzero calibration model")
    return "POSITIVE" if value > 0 else "NEGATIVE"


def _magnitude_relation(result: Fraction, input_value: Fraction) -> str:
    if abs(result) > abs(input_value):
        return "GROWS"
    if abs(result) < abs(input_value):
        return "SHRINKS"
    return "SAME"


def _validate(seed: int, mode: str) -> None:
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode}")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def generate(seed: int, mode: str) -> Variant:
    """Generate an unseen calibration record without announcing its operation."""

    _validate(seed, mode)
    mode_salt = 104_729 if mode == "independent" else 13_337
    rng = random.Random(seed * 1_000_003 + mode_salt)
    family = seed % 6

    if family == 0:
        structure = "DIRECT_NEGATIVE_GROW"
        input_value = _positive_fraction(rng)
        scale = -Fraction(rng.randint(3, 9), 2)
        if abs(scale) <= 1:
            scale = Fraction(-3, 2)
        hidden_quantity = "output"
        given_value = scale
        operation = "MULTIPLY"
        prompt = (
            f"A calibration log shows input {input_value} and scale {scale}, with the "
            "output hidden. Decide which operation recovers the hidden value; then "
            "predict the output direction and whether magnitude grows, shrinks, or STAYS THE SAME; calculate and recompose."
        )
    elif family == 1:
        structure = "DIRECT_DOUBLE_NEGATIVE_SHRINK"
        input_value = -_positive_fraction(rng)
        scale = -Fraction(rng.randint(1, 4), rng.randint(5, 9))
        hidden_quantity = "output"
        given_value = scale
        operation = "MULTIPLY"
        prompt = (
            f"A calibration log shows input {input_value} and scale {scale}, with the "
            "output hidden. Decide which operation recovers the hidden value; then "
            "predict direction and magnitude change, calculate, and recompose."
        )
    elif family == 2:
        structure = "MISSING_SCALE_INVERT_DIVISOR"
        input_value = _positive_fraction(rng)
        scale = -Fraction(rng.randint(3, 9), rng.choice((2, 4)))
        if abs(scale) == 1:
            scale = Fraction(-3, 2)
        hidden_quantity = "scale"
        given_value = input_value * scale
        operation = "DIVIDE_AS_MISSING_SCALE"
        prompt = (
            f"A calibration log shows input {input_value} and output {given_value}, "
            "with the scale hidden. Decide which operation recovers the hidden value; "
            "then predict the output's direction and magnitude relative to the input (not the hidden scale's sign), calculate, and recompose."
        )
    elif family == 3:
        structure = "MISSING_SCALE_POSITIVE_SHRINK"
        input_value = -_positive_fraction(rng)
        scale = Fraction(rng.randint(1, 4), rng.randint(5, 9))
        hidden_quantity = "scale"
        given_value = input_value * scale
        operation = "DIVIDE_AS_MISSING_SCALE"
        prompt = (
            f"A calibration log shows input {input_value} and output {given_value}, "
            "with the scale hidden. Decide which operation recovers the hidden value; "
            "then predict the output's direction and magnitude relative to the input (not the hidden scale's sign), calculate, and recompose."
        )

    elif family in (4, 5):
        # Unit-scale boundary: +1 preserves direction, -1 reverses direction.
        # Input is nonzero; outputs and scales must remain nonzero.
        structure = "UNIT_SCALE_POSITIVE" if family == 4 else "UNIT_SCALE_NEGATIVE"
        input_value = _positive_fraction(rng) if family == 4 else -_positive_fraction(rng)
        scale = Fraction(1 if family == 4 else -1)
        hidden_quantity = "output" if family == 4 else "scale"
        given_value = scale if hidden_quantity == "output" else input_value * scale
        operation = "MULTIPLY" if hidden_quantity == "output" else "DIVIDE_AS_MISSING_SCALE"
        if hidden_quantity == "output":
            prompt = (
                f"A calibration log shows nonzero input {input_value} and scale +1, "
                "with output hidden. Predict the output's direction and decide "
                "whether its magnitude grows, shrinks, or STAYS THE SAME; calculate and recompose."
            )
        else:
            prompt = (
                f"A calibration log shows nonzero input {input_value} and output "
                f"{given_value}, with scale hidden. Determine the scale and predict "
                "the OUTPUT'S direction (not the hidden scale's sign); decide "
                "whether the output's magnitude grows, shrinks, or STAYS THE SAME."
            )

    if input_value == 0 or scale == 0:
        raise ValueError("This signed-direction calibration scope excludes zero")
    answer = scale if hidden_quantity == "scale" else input_value * scale
    result = input_value * scale
    direction = _direction(result)
    magnitude_relation = _magnitude_relation(result, input_value)
    recomposition = f"({scale}) * ({input_value}) = {result}"
    return Variant(
        variant_id=f"{NAMESPACE}:{mode}:{seed}",
        mode=mode,
        structure=structure,
        prompt=prompt,
        input_value=input_value,
        given_value=given_value,
        hidden_quantity=hidden_quantity,
        operation=operation,
        direction=direction,
        magnitude_relation=magnitude_relation,
        answer=answer,
        recomposition=recomposition,
    )


def diagnose_response(variant: Variant, response: Mapping[str, object]) -> str:
    """Classify a captured guided diagnostic response, or fail unclassified."""

    # Guided diagnostic only: a fully correct response is not a misconception.
    # Require every reasoning field, not merely the final numeric answer.
    if not isinstance(response, Mapping):
        return "UNCLASSIFIED_FOR_HUMAN_REVIEW"
    oracle = variant.teacher_oracle()
    if (
        set(response) == set(RESPONSE_FIELDS)
        and not isinstance(response.get("exact_result"), (bool, float))
        and all(
            response.get(field) == expected
            for field, expected in oracle.items()
            if field != "exact_result"
        )
    ):
        try:
            if Fraction(str(response["exact_result"])) == variant.answer:
                return "CORRECT_NO_REMEDIATION"
        except (ValueError, ZeroDivisionError, TypeError):
            pass

    raw_result = response.get("exact_result")
    try:
        submitted_result = Fraction(str(raw_result))
    except (ValueError, ZeroDivisionError):
        submitted_result = None

    if variant.hidden_quantity == "scale" and submitted_result is not None:
        if (
            response.get("inverse_strategy")
            == "MULTIPLY_INPUT_BY_RECIPROCAL_OF_OUTPUT"
            or submitted_result == variant.input_value / variant.given_value
        ):
            return "RECIPROCAL_WRONG_OPERAND"
        if response.get("inverse_strategy") == "DIVIDE_COMPONENTS_INDEPENDENTLY":
            return "DIVIDE_STRAIGHT_ACROSS"

    if variant.structure == "DIRECT_DOUBLE_NEGATIVE_SHRINK" and (
        response.get("output_direction_prediction") == "NEGATIVE"
        or submitted_result == -variant.answer
    ):
        return "ONE_NEGATIVE_MEANS_ALWAYS_NEGATIVE"

    if (
        variant.structure == "DIRECT_NEGATIVE_GROW"
        and response.get("output_direction_prediction") == variant.direction
        and response.get("magnitude_relation") == "SHRINKS"
    ):
        return "NEGATIVE_MEANS_SMALLER_MAGNITUDE"

    return "UNCLASSIFIED_FOR_HUMAN_REVIEW"
