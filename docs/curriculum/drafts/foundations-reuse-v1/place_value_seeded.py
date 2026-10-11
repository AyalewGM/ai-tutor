"""Draft-only seeded variants for three-digit place-value reasoning.

This module is deliberately outside the runtime registry.  It gives reviewers
replayable guided and independent items without activating content or writing
learner, attempt, diagnostic, or mastery evidence.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

NAMESPACE = "foundations-place-value-r2"
MODES = frozenset({"guided", "independent"})
STRUCTURES = (
    "COMPOSE_NONSTANDARD",
    "EXCHANGE_INVARIANT",
    "ZERO_PLACEHOLDER",
    "COMPARE_FIRST_DIFFERENCE",
    "TRANSFER_BUNDLES",
)


@dataclass(frozen=True)
class PlaceValueVariant:
    variant_id: str
    mode: str
    structure: str
    prompt: str
    hundreds: int
    tens: int
    ones: int
    total: int
    canonical_inventory: tuple[int, int, int]
    answer: str
    verification: str
    comparison_values: tuple[int, int] | None = None
    first_differing_place: str | None = None

    def public_payload(self) -> dict[str, object]:
        """Return learner-visible fields with no answer, hint, or worked step."""

        response_fields = ["answer", "equation", "explanation"]
        if self.structure == "COMPARE_FIRST_DIFFERENCE":
            response_fields = ["comparison_symbol", "first_differing_place", "explanation"]
        elif self.structure == "EXCHANGE_INVARIANT":
            response_fields = ["new_inventory", "total_before", "total_after", "explanation"]
        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
            "response_fields": response_fields,
        }


def _canonical(total: int) -> tuple[int, int, int]:
    return total // 100, (total // 10) % 10, total % 10


def _symbol(left: int, right: int) -> str:
    if left < right:
        return "<"
    if left > right:
        return ">"
    return "="


def _validate(seed: int, mode: str) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")


def generate(seed: int, mode: str) -> PlaceValueVariant:
    _validate(seed, mode)
    rng = random.Random(f"{NAMESPACE}:{mode}:{seed}")
    structure = STRUCTURES[(seed + (2 if mode == "independent" else 0)) % len(STRUCTURES)]
    variant_id = f"{NAMESPACE}:{mode}:{seed}"

    if structure == "COMPOSE_NONSTANDARD":
        hundreds = rng.randint(1, 5)
        tens = rng.randint(10, 18)
        ones = rng.randint(0, 9)
        total = 100 * hundreds + 10 * tens + ones
        canonical = _canonical(total)
        return PlaceValueVariant(
            variant_id,
            mode,
            structure,
            f"A model has {hundreds} hundreds, {tens} tens, and {ones} ones. What number does it represent?",
            hundreds,
            tens,
            ones,
            total,
            canonical,
            str(total),
            f"{hundreds}×100 + {tens}×10 + {ones} = {total}",
        )

    if structure == "EXCHANGE_INVARIANT":
        hundreds = rng.randint(2, 7)
        tens = rng.randint(1, 8)
        ones = rng.randint(0, 9)
        total = 100 * hundreds + 10 * tens + ones
        # Always exchange one hundred for ten tens.  Counts change; value does not.
        after = (hundreds - 1, tens + 10, ones)
        return PlaceValueVariant(
            variant_id,
            mode,
            structure,
            f"Start with {hundreds} hundreds, {tens} tens, and {ones} ones. Exchange one hundred for ten tens. Record the new inventory and both totals.",
            hundreds,
            tens,
            ones,
            total,
            after,
            f"{after[0]} hundreds, {after[1]} tens, {after[2]} ones; total {total}",
            f"{hundreds}×100 + {tens}×10 + {ones} = {after[0]}×100 + {after[1]}×10 + {after[2]} = {total}",
        )

    if structure == "ZERO_PLACEHOLDER":
        hundreds = rng.randint(1, 9)
        tens = 0
        ones = rng.randint(1, 9)
        total = 100 * hundreds + ones
        return PlaceValueVariant(
            variant_id,
            mode,
            structure,
            f"Write the numeral for {hundreds} hundreds, zero tens, and {ones} ones. Explain what the zero records.",
            hundreds,
            tens,
            ones,
            total,
            _canonical(total),
            str(total),
            f"{hundreds}×100 + 0×10 + {ones} = {total}",
        )

    if structure == "COMPARE_FIRST_DIFFERENCE":
        hundreds = rng.randint(2, 8)
        left_tens = rng.randint(0, 8)
        right_tens = rng.randint(left_tens + 1, 9)
        # Make the ones suggest the opposite result so ones-first reasoning is observable.
        left_ones = rng.randint(5, 9)
        right_ones = rng.randint(0, 4)
        left = 100 * hundreds + 10 * left_tens + left_ones
        right = 100 * hundreds + 10 * right_tens + right_ones
        return PlaceValueVariant(
            variant_id,
            mode,
            structure,
            f"Compare {left} and {right}. Give the symbol and name the first place where the values differ.",
            hundreds,
            left_tens,
            left_ones,
            left,
            _canonical(left),
            _symbol(left, right),
            f"Hundreds are equal; {left_tens} tens < {right_tens} tens, so {left} < {right}.",
            comparison_values=(left, right),
            first_differing_place="tens",
        )

    hundreds = rng.randint(1, 4)
    tens = rng.randint(10, 19)
    ones = rng.randint(0, 9)
    total = 100 * hundreds + 10 * tens + ones
    canonical = _canonical(total)
    return PlaceValueVariant(
        variant_id,
        mode,
        structure,
        f"A supply room has {hundreds} cartons of 100 cards, {tens} packs of 10, and {ones} loose cards. Find the total and a canonical hundreds-tens-ones inventory.",
        hundreds,
        tens,
        ones,
        total,
        canonical,
        f"{total}; {canonical[0]} hundreds, {canonical[1]} tens, {canonical[2]} ones",
        f"{hundreds}×100 + {tens}×10 + {ones} = {total}",
    )


def diagnose_numeric_response(item: PlaceValueVariant, response: int) -> str:
    """Classify observable numeric evidence without awarding mastery."""

    if isinstance(response, bool) or not isinstance(response, int):
        return "INVALID_RESPONSE"
    if item.structure == "COMPARE_FIRST_DIFFERENCE":
        return "WRONG_RESPONSE_TYPE"
    if response == item.total:
        return "CORRECT_PRACTICE_ONLY"
    if response == item.hundreds + item.tens + item.ones:
        return "DIGIT_VS_VALUE"
    if item.structure in {"COMPOSE_NONSTANDARD", "TRANSFER_BUNDLES"}:
        ignored_extra_tens = 100 * item.hundreds + 10 * (item.tens % 10) + item.ones
        if response == ignored_extra_tens:
            return "NONSTANDARD_COUNT_AS_DIGIT"
    if item.structure == "ZERO_PLACEHOLDER" and response == 10 * item.hundreds + item.ones:
        return "ZERO_PLACEHOLDER_OMITTED"
    if item.structure == "EXCHANGE_INVARIANT" and response == item.total + 100:
        return "EXCHANGE_CREATES_VALUE"
    return "PLACE_VALUE_RELATION_NOT_ESTABLISHED"


def diagnose_comparison_response(
    item: PlaceValueVariant,
    symbol: str,
    first_differing_place: str,
) -> str:
    """Classify comparison evidence tied to the selected symbol and place."""

    if item.structure != "COMPARE_FIRST_DIFFERENCE" or item.comparison_values is None:
        return "WRONG_RESPONSE_TYPE"
    if symbol == item.answer and first_differing_place == item.first_differing_place:
        return "CORRECT_PRACTICE_ONLY"
    left, right = item.comparison_values
    ones_first = _symbol(left % 10, right % 10)
    if symbol == ones_first and first_differing_place == "ones":
        return "COMPARED_ONES_FIRST"
    if symbol == _symbol(right, left):
        return "INEQUALITY_SYMBOL_REVERSED"
    if first_differing_place != item.first_differing_place:
        return "PLACE_SEQUENCE_CONFUSION"
    return "COMPARISON_NOT_ESTABLISHED"
