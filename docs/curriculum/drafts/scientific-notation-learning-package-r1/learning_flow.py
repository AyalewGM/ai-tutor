"""Draft-only scientific-notation learning flow for Issue #337.

This module consumes the accepted draft generator contract without registering a
runtime family, route, scorer, or mastery event.  Guided feedback is deliberately
unavailable for independent variants.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import replace
from fractions import Fraction
from typing import Any

PACKAGE_ID = "SCIENTIFIC-NOTATION-LEARNING-PACKAGE-R1"
STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
CANONICAL_FAMILY = "MATH.NS.SCIENTIFIC_NOTATION"
PHASES = (
    "OBSERVE",
    "PREDICT",
    "MANIPULATE",
    "EXPLAIN",
    "PRACTICE",
    "DIAGNOSE",
    "TRANSFER",
    "VERIFY",
)
EXPLANATION_CODES = {
    "TO_SCIENTIFIC": "INVERSE_SCALE_PRESERVES_VALUE",
    "TO_ORDINARY": "PLACE_VALUE_FOLLOWS_EXPONENT",
    "MULTIPLY": "MULTIPLY_COEFFICIENTS_ADD_EXPONENTS_THEN_NORMALIZE",
    "DIVIDE": "DIVIDE_COEFFICIENTS_SUBTRACT_EXPONENTS_THEN_NORMALIZE",
}
SOCRATIC_PATHS = {
    "SCI.EXPONENT.DIRECTION": (
        "Did the coefficient become ten times larger or ten times smaller?",
        "What inverse power-of-ten change keeps the total value fixed?",
        "Does the revised form reproduce the exact ordinary value?",
    ),
    "SCI.NOT_NORMALIZED": (
        "Is the coefficient magnitude at least 1 and less than 10?",
        "How many factors of ten must move between coefficient and exponent?",
        "Does that inverse pair of changes preserve the exact value?",
    ),
    "SCI.PRODUCT.EXPONENTS_MULTIPLIED": (
        "When powers with base 10 are multiplied, how are their exponents combined?",
        "What repeated-factor count comes from placing the two powers side by side?",
        "After combining exponents, does the coefficient still need normalization?",
    ),
    "SCI.QUOTIENT.EXPONENTS_ADDED": (
        "Which power-of-ten factors cancel between numerator and denominator?",
        "What exponent difference counts the factors that remain?",
        "After subtracting exponents, does the coefficient still need normalization?",
    ),
    "SCI.COEFFICIENT.ARITHMETIC": (
        "Which operation applies to the two leading coefficients?",
        "Can that coefficient calculation be kept as an exact fraction?",
        "Does the exact coefficient and power reproduce the ordinary value?",
    ),
    "SCI.INEXACT.WHEN_EXACT_REQUIRED": (
        "Did the prompt request an exact value or a rounded measurement?",
        "What fraction records the coefficient without discarding digits?",
        "Can you verify the exact result before any optional rounding step?",
    ),
}


def scientific_seed(index: int, *, transfer: bool = False) -> int:
    """Map an item index to the existing generator's scientific structure."""

    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise ValueError("index must be a non-negative integer")
    namespace_offset = 10_000 if transfer else 0
    return 5 * (namespace_offset + index) + 4


def _field(item: Any, name: str) -> Any:
    try:
        return getattr(item, name)
    except AttributeError as exc:  # pragma: no cover - defensive contract check
        raise TypeError(f"generator item is missing {name}") from exc


def _validate_item(item: Any) -> None:
    if _field(item, "structure") != "SCIENTIFIC_NOTATION":
        raise ValueError("learning package only accepts SCIENTIFIC_NOTATION variants")
    if _field(item, "canonical_family") != CANONICAL_FAMILY:
        raise ValueError("learning package requires the historical canonical family")
    if _field(item, "mode") not in {"guided", "independent"}:
        raise ValueError("unsupported generator mode")


def _fraction(payload: Mapping[str, Any], field: str) -> Fraction:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        raise TypeError(f"{field} must be an exact numerator/denominator object")
    numerator = value.get("numerator")
    denominator = value.get("denominator")
    if isinstance(numerator, bool) or not isinstance(numerator, int):
        raise TypeError(f"{field}.numerator must be an integer")
    if isinstance(denominator, bool) or not isinstance(denominator, int) or denominator == 0:
        raise ValueError(f"{field}.denominator must be a nonzero integer")
    return Fraction(numerator, denominator)


def _power_of_ten(exponent: int) -> Fraction:
    return Fraction(10**exponent) if exponent >= 0 else Fraction(1, 10 ** (-exponent))


def independent_public_task(item: Any) -> dict[str, Any]:
    """Return a no-answer public payload for an unseen independent variant."""

    _validate_item(item)
    if _field(item, "mode") != "independent":
        raise ValueError("independent payload requires an independent variant")
    task_id = hashlib.sha256(_field(item, "variant_id").encode()).hexdigest()[:24]
    return {
        "task_id": task_id,
        "mode": "independent",
        "structure": "SCIENTIFIC_NOTATION",
        "canonical_family": CANONICAL_FAMILY,
        "prompt": _field(item, "prompt"),
        "response_fields": list(_field(item, "response_schema")),
        "hints": [],
        "worked_steps": [],
        "guided_feedback_available": False,
        "mastery_credit": False,
    }


def guided_lesson(item: Any) -> dict[str, Any]:
    """Build the full guided journey without exposing the teacher oracle."""

    _validate_item(item)
    if _field(item, "mode") != "guided":
        raise ValueError("guided lesson requires a guided variant")
    operation = _field(item, "parameters")["operation"]
    return {
        "variant_id": _field(item, "variant_id"),
        "mode": "guided",
        "prompt": _field(item, "prompt"),
        "operation": operation,
        "phases": list(PHASES),
        "representations": ["CONCRETE_PLACE_VALUE", "VISUAL_EXPONENT_SCALE", "SYMBOLIC"],
        "prediction_prompt": (
            "Predict whether the coefficient must grow or shrink and whether the power of ten "
            "must change in the inverse direction."
        ),
        "manipulation_prompt": (
            "Shift one factor of ten at a time between the coefficient and 10^n; keep an exact "
            "before/after value equation visible."
        ),
        "explanation_target": EXPLANATION_CODES[operation],
        "normalization_interval": "1 <= |coefficient| < 10",
        "exact_only": True,
        "rounded_response_policy": "PROVISIONAL_NOT_IMPLEMENTED",
        "mastery_credit": False,
    }



def generate_contextual_transfer(index: int, mode: str, source_generate: Any) -> Any:
    """Reuse accepted exact generators for a genuinely shifted-context draft exit.

    The source variant retains its typed teacher-only oracle. The returned item
    can be passed to independent_public_task, which exposes only an opaque ID
    and the necessary task input. This is not an authorized assessment route.
    """

    if type(index) is not int or index < 0:
        raise ValueError("index must be a non-negative integer")
    if mode not in {"guided", "independent"}:
        raise ValueError("unsupported transfer mode")
    if not callable(source_generate):
        raise TypeError("source_generate must be the accepted draft generator")

    practice = source_generate(scientific_seed(index), "guided")
    _validate_item(practice)
    operations = ("TO_SCIENTIFIC", "TO_ORDINARY", "MULTIPLY", "DIVIDE")
    previous = _field(practice, "parameters")["operation"]
    if previous not in operations:
        raise ValueError("unsupported practice operation")
    previous_position = operations.index(previous)
    target_position = (previous_position + 1 + (index // 4) % 3) % len(operations)

    # The source generator's scientific operation is selected by seed % 4.
    # 5 * (10_000 + transfer_index) + 4 retains transfer_index % 4.
    transfer_index = 10_000 + 16 * index + target_position
    candidate = source_generate(scientific_seed(transfer_index, transfer=True), mode)
    _validate_item(candidate)
    parameters = _field(candidate, "parameters")
    operation = parameters["operation"]
    if operation != operations[target_position] or operation == previous:
        raise ValueError("fresh transfer failed the operation-shift invariant")

    c1, e1 = Fraction(parameters["c1"]), parameters["e1"]
    c2, e2 = Fraction(parameters["c2"]), parameters["e2"]
    context = (index // 4) % 2
    if operation == "TO_SCIENTIFIC":
        unit = ("pulses", "events")[context]
        ordinary = Fraction(_field(candidate, "teacher_oracle")["ordinary_value"])
        task = (
            f"A synthetic counter recorded {ordinary} {unit}. "
            f"Express this exact value {ordinary} in normalized scientific notation, "
            "explain the inverse factor-of-ten change, and verify the original exact count."
        )
    elif operation == "TO_ORDINARY":
        unit = ("micrometres", "grams")[context]
        task = (
            f"A synthetic sensor reports {c1} x 10^{e1} {unit}. "
            "Express this as an exact ordinary value and explain the direction "
            "of the place-value shift."
        )
    elif operation == "MULTIPLY":
        unit = ("metres", "centimetres")[context]
        task = (
            f"A rectangular display measures {c1} x 10^{e1} {unit} by "
            f"{c2} x 10^{e2} {unit}. Find its exact area in square {unit}, "
            "combine exponents, normalize, and verify the ordinary value."
        )
    else:
        unit = ("metres per second", "records per second")[context]
        numerator_unit = ("metres", "records")[context]
        task = (
            f"A synthetic process covers {c1} x 10^{e1} {numerator_unit} "
            f"in {c2} x 10^{e2} seconds. Find the exact rate in {unit}, "
            "subtract exponents, normalize, and verify the ordinary value."
        )

    return replace(
        candidate,
        variant_id=f"{PACKAGE_ID}:contextual-transfer:{mode}:{index}:{operation}",
        prompt=(
            f"Contextual {'guided practice' if mode == 'guided' else 'independent transfer'}: "
            f"{task} State why the resulting units match the operation."
        ),
    )


def verify_teacher_oracle(item: Any) -> bool:
    """Reconstruct the generator result independently from its typed parameters."""

    _validate_item(item)
    parameters = _field(item, "parameters")
    oracle = _field(item, "teacher_oracle")
    operation = parameters["operation"]
    c1 = Fraction(parameters["c1"])
    e1 = parameters["e1"]
    c2 = Fraction(parameters["c2"])
    e2 = parameters["e2"]

    if operation == "TO_ORDINARY":
        expected = c1 * _power_of_ten(e1)
    elif operation == "MULTIPLY":
        expected = c1 * c2 * _power_of_ten(e1 + e2)
    elif operation == "DIVIDE":
        expected = c1 / c2 * _power_of_ten(e1 - e2)
    else:
        match = re.search(r"exact value ([^ ]+) in normalized", _field(item, "prompt"))
        if match is None:
            raise ValueError("TO_SCIENTIFIC prompt lacks an independently readable exact value")
        expected = Fraction(match.group(1))

    coefficient = Fraction(oracle["coefficient"])
    exponent = oracle["exponent"]
    return (
        Fraction(1) <= abs(coefficient) < 10
        and coefficient * _power_of_ten(exponent) == expected
        and Fraction(oracle["ordinary_value"]) == expected
    )


def evaluate_guided_response(item: Any, response: Mapping[str, Any]) -> dict[str, Any]:
    """Check exact guided evidence and select one misconception-specific branch."""

    _validate_item(item)
    if _field(item, "mode") != "guided":
        raise PermissionError("guided feedback is unavailable in independent assessment")
    if not isinstance(response, Mapping):
        raise TypeError("response must be a mapping")

    coefficient = _fraction(response, "normalized_coefficient")
    ordinary = _fraction(response, "exact_ordinary_value")
    exponent = response.get("power_of_ten")
    if isinstance(exponent, bool) or not isinstance(exponent, int):
        raise TypeError("power_of_ten must be an integer")
    explanation = response.get("normalization_explanation")
    if not isinstance(explanation, str):
        raise TypeError("normalization_explanation must be a string code")

    parameters = _field(item, "parameters")
    oracle = _field(item, "teacher_oracle")
    expected_coefficient = Fraction(oracle["coefficient"])
    expected_exponent = oracle["exponent"]
    expected_ordinary = Fraction(oracle["ordinary_value"])
    operation = parameters["operation"]

    exact = (
        coefficient == expected_coefficient
        and exponent == expected_exponent
        and ordinary == expected_ordinary
        and explanation == EXPLANATION_CODES[operation]
    )
    if exact:
        return {"correct": True, "misconception_id": None, "socratic_questions": []}

    if coefficient * _power_of_ten(exponent) == expected_ordinary and not (
        Fraction(1) <= abs(coefficient) < 10
    ):
        misconception = "SCI.NOT_NORMALIZED"
    elif (
        operation == "MULTIPLY"
        and exponent != expected_exponent
        and exponent == parameters["e1"] * parameters["e2"]
    ):
        misconception = "SCI.PRODUCT.EXPONENTS_MULTIPLIED"
    elif (
        operation == "DIVIDE"
        and exponent != expected_exponent
        and exponent == parameters["e1"] + parameters["e2"]
    ):
        misconception = "SCI.QUOTIENT.EXPONENTS_ADDED"
    elif coefficient == expected_coefficient and exponent != expected_exponent:
        misconception = "SCI.EXPONENT.DIRECTION"
    elif coefficient != expected_coefficient:
        misconception = "SCI.COEFFICIENT.ARITHMETIC"
    else:
        misconception = "SCI.INEXACT.WHEN_EXACT_REQUIRED"
    return {
        "correct": False,
        "misconception_id": misconception,
        "socratic_questions": list(SOCRATIC_PATHS[misconception]),
        "fresh_exit_seed_rule": "scientific_seed(index, transfer=True)",
    }
