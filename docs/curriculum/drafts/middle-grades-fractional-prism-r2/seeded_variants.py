"""Draft-only seeded variants for fractional rectangular-prism reasoning.

This module is intentionally outside the runtime registry.  It provides exact,
replayable content for independent review without activating assessment or
writing learner, attempt, diagnostic, or mastery evidence.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction

NAMESPACE = "middle-grades-fractional-prism-r2"
MODES = frozenset({"guided", "independent"})
STRUCTURES = (
    "PACK_FRACTIONAL_CELLS",
    "MIXED_EDGE_VOLUME",
    "MISSING_HEIGHT",
    "DECOMPOSE_MIXED_EDGE",
    "TRANSFER_MOLD_PLAN",
)


def _fmt(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    if value > 1:
        whole, remainder = divmod(value.numerator, value.denominator)
        return f"{whole} {remainder}/{value.denominator}"
    return f"{value.numerator}/{value.denominator}"


def _proper(rng: random.Random) -> Fraction:
    denominator = rng.choice((2, 3, 4, 5, 6))
    return Fraction(rng.randint(1, denominator - 1), denominator)


def _mixed(rng: random.Random) -> Fraction:
    return Fraction(rng.randint(1, 3)) + _proper(rng)


@dataclass(frozen=True)
class PrismVariant:
    variant_id: str
    mode: str
    structure: str
    context: str
    prompt: str
    length: Fraction
    width: Fraction
    height: Fraction
    base_area: Fraction
    volume: Fraction
    target: str
    expected_operation: str
    exact_answer: Fraction
    expected_unit_power: int
    decomposition: tuple[Fraction, Fraction] | None = None

    def public_payload(self) -> dict[str, object]:
        """Return learner-visible fields with no answer, hint, or worked step."""

        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "context": self.context,
            "prompt": self.prompt,
            "response_fields": [
                "operation_choice",
                "base_area_or_layer_size",
                "layer_reasoning",
                "exact_answer",
                "unit_and_power",
                "equation",
                "check_or_explanation",
            ],
        }


def _validate(seed: int, mode: str) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")


def _item(
    *,
    seed: int,
    mode: str,
    structure: str,
    context: str,
    prompt: str,
    length: Fraction,
    width: Fraction,
    height: Fraction,
    target: str = "volume",
    decomposition: tuple[Fraction, Fraction] | None = None,
) -> PrismVariant:
    base_area = length * width
    volume = base_area * height
    operation = "MULTIPLY_THREE_EDGES" if target == "volume" else "DIVIDE_VOLUME_BY_BASE_AREA"
    answer = volume if target == "volume" else height
    return PrismVariant(
        variant_id=f"{NAMESPACE}:{mode}:{seed}",
        mode=mode,
        structure=structure,
        context=context,
        prompt=prompt,
        length=length,
        width=width,
        height=height,
        base_area=base_area,
        volume=volume,
        target=target,
        expected_operation=operation,
        exact_answer=answer,
        expected_unit_power=3 if target == "volume" else 1,
        decomposition=decomposition,
    )


def generate(seed: int, mode: str) -> PrismVariant:
    _validate(seed, mode)
    rng = random.Random(f"{NAMESPACE}:{mode}:{seed}")
    structure = STRUCTURES[(seed + (2 if mode == "independent" else 0)) % len(STRUCTURES)]

    if structure == "PACK_FRACTIONAL_CELLS":
        length, width, height = _proper(rng), Fraction(rng.randint(2, 5)), _proper(rng)
        prompt = (
            f"A prism measures {_fmt(length)} by {_fmt(width)} by {_fmt(height)} unit. "
            "Partition a unit cube to match the edge fractions, describe one layer, and find the exact volume."
        )
        return _item(
            seed=seed,
            mode=mode,
            structure=structure,
            context="fractional unit-cube packing",
            prompt=prompt,
            length=length,
            width=width,
            height=height,
        )

    if structure == "MIXED_EDGE_VOLUME":
        length, width, height = _mixed(rng), _proper(rng), _mixed(rng)
        prompt = (
            f"A rectangular storage insert is {_fmt(length)} cm by {_fmt(width)} cm by "
            f"{_fmt(height)} cm. Predict whether its volume is greater or less than the base area, "
            "then calculate the exact volume with units."
        )
        return _item(
            seed=seed,
            mode=mode,
            structure=structure,
            context="mixed-number edge lengths",
            prompt=prompt,
            length=length,
            width=width,
            height=height,
        )

    if structure == "MISSING_HEIGHT":
        length, width, height = _mixed(rng), _proper(rng), _mixed(rng)
        volume = length * width * height
        prompt = (
            f"A prism has base edges {_fmt(length)} m and {_fmt(width)} m and volume "
            f"{_fmt(volume)} cubic metres. Choose an operation, find its height, and verify by recomposing the volume."
        )
        return _item(
            seed=seed,
            mode=mode,
            structure=structure,
            context="inverse dimension reasoning",
            prompt=prompt,
            length=length,
            width=width,
            height=height,
            target="height",
        )

    if structure == "DECOMPOSE_MIXED_EDGE":
        whole = Fraction(rng.randint(1, 3))
        fractional = _proper(rng)
        length = whole + fractional
        width, height = _proper(rng), Fraction(rng.randint(2, 5))
        prompt = (
            f"A prism is {_fmt(length)} by {_fmt(width)} by {_fmt(height)} unit. "
            f"Decompose the first edge as {_fmt(whole)} + {_fmt(fractional)}, find both partial volumes, "
            "and show that their sum equals the direct product."
        )
        return _item(
            seed=seed,
            mode=mode,
            structure=structure,
            context="equivalent volume decomposition",
            prompt=prompt,
            length=length,
            width=width,
            height=height,
            decomposition=(whole, fractional),
        )

    length, width, height = _mixed(rng), _proper(rng), _mixed(rng)
    volume = length * width * height
    if seed % 2 == 0:
        prompt = (
            f"A makerspace mold measures {_fmt(length)} dm by {_fmt(width)} dm by {_fmt(height)} dm. "
            "Decide what operation the situation requires, then find the exact amount of casting material."
        )
        target = "volume"
    else:
        prompt = (
            f"A makerspace mold has base {_fmt(length)} dm by {_fmt(width)} dm and holds "
            f"{_fmt(volume)} cubic decimetres. Decide what operation is needed, then find the mold height."
        )
        target = "height"
    return _item(
        seed=seed,
        mode=mode,
        structure=structure,
        context="unfamiliar mold planning",
        prompt=prompt,
        length=length,
        width=width,
        height=height,
        target=target,
    )


def diagnose_response(
    item: PrismVariant,
    operation: str,
    exact_answer: Fraction | int,
    unit_power: int,
) -> str:
    """Route captured response evidence without awarding mastery."""

    if not isinstance(item, PrismVariant):
        raise TypeError("item must be a PrismVariant")
    if not isinstance(operation, str) or not operation:
        raise TypeError("operation must be a non-empty string")
    if isinstance(exact_answer, bool) or not isinstance(exact_answer, (Fraction, int)):
        raise TypeError("exact_answer must be an integer or Fraction")
    if isinstance(unit_power, bool) or not isinstance(unit_power, int):
        raise TypeError("unit_power must be an integer")
    if unit_power not in {1, 2, 3}:
        raise ValueError("unit_power must be 1, 2, or 3")
    answer = Fraction(exact_answer)
    if operation != item.expected_operation:
        return "OPERATION_SELECTION_ERROR"
    if answer == item.exact_answer and unit_power != item.expected_unit_power:
        return "UNIT_DIMENSION_ERROR"
    if item.target == "volume":
        if answer == item.base_area:
            return "AREA_AS_VOLUME"
        if answer == item.length + item.width + item.height:
            return "ADDED_EDGE_LENGTHS"
        truncated = Fraction(int(item.length) * int(item.width) * int(item.height))
        if answer == truncated and truncated != item.volume:
            return "IGNORED_FRACTIONAL_EDGE"
    else:
        if answer == item.volume - item.base_area:
            return "SUBTRACTED_BASE_FROM_VOLUME"
        if answer == item.volume * item.base_area:
            return "MULTIPLIED_INSTEAD_OF_DIVIDED"
    if answer == item.exact_answer and unit_power == item.expected_unit_power:
        return "CORRECT_PRACTICE_ONLY"
    return "VOLUME_RELATION_NOT_ESTABLISHED"
