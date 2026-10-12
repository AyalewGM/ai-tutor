"""Draft-only seeded reasoning variants for fraction equivalence.

This module is not imported by runtime code and performs no persistence.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from math import gcd

NAMESPACE = "foundations-fraction-equivalence-v2"
MODES = frozenset({"guided", "independent"})
STRUCTURES = (
    "REPARTITION_EQUIVALENCE",
    "REJECT_ADD_BOTH_CLAIM",
    "EQUIVALENT_FRACTIONS_DIFFERENT_WHOLES",
)


@dataclass(frozen=True)
class Variant:
    variant_id: str
    mode: str
    structure: str
    prompt: str
    numerator: int
    denominator: int
    scale: int
    whole_a: int | None
    whole_b: int | None
    teacher_answer: dict[str, str | bool]

    def public_payload(self) -> dict[str, str]:
        """Return only fields safe before an independent submission."""

        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
        }


def _reduced_proper_fraction(rng: random.Random) -> tuple[int, int]:
    while True:
        denominator = rng.randint(3, 10)
        numerator = rng.randint(1, denominator - 1)
        if gcd(numerator, denominator) == 1:
            return numerator, denominator


def generate(seed: int, mode: str) -> Variant:
    """Generate a reproducible, mode-separated review variant."""

    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode}")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")

    salt = 130_363 if mode == "independent" else 41_009
    rng = random.Random(seed * 1_000_003 + salt)
    numerator, denominator = _reduced_proper_fraction(rng)
    scale = rng.randint(2, 5)
    structure = STRUCTURES[seed % len(STRUCTURES)]
    whole_a: int | None = None
    whole_b: int | None = None

    if structure == "REPARTITION_EQUIVALENCE":
        target_numerator = numerator * scale
        target_denominator = denominator * scale
        prompt = (
            f"A fixed whole has {numerator}/{denominator} shaded. Each part is split "
            f"into {scale} equal subparts. Name the shaded fraction after repartitioning "
            "and explain why the shaded amount is unchanged."
        )
        teacher_answer: dict[str, str | bool] = {
            "fraction": f"{target_numerator}/{target_denominator}",
            "equivalent": True,
            "reason": "both numerator and denominator scaled by the same factor",
        }
    elif structure == "REJECT_ADD_BOTH_CLAIM":
        claimed_numerator = numerator + 1
        claimed_denominator = denominator + 1
        prompt = (
            f"A learner claims {numerator}/{denominator} equals "
            f"{claimed_numerator}/{claimed_denominator} because one was added to both "
            "numbers. Decide whether the claim is valid and justify with exact values."
        )
        teacher_answer = {
            "equivalent": False,
            "original": str(Fraction(numerator, denominator)),
            "claimed": str(Fraction(claimed_numerator, claimed_denominator)),
            "reason": "adding the same number does not preserve the ratio",
        }
    else:
        whole_a = denominator * rng.randint(2, 5)
        whole_b = denominator * rng.randint(6, 9)
        equivalent_numerator = numerator * scale
        equivalent_denominator = denominator * scale
        quantity_a = Fraction(numerator, denominator) * whole_a
        quantity_b = Fraction(equivalent_numerator, equivalent_denominator) * whole_b
        prompt = (
            f"Ribbon A is {whole_a} units long with {numerator}/{denominator} colored. "
            f"Ribbon B is {whole_b} units long with {equivalent_numerator}/"
            f"{equivalent_denominator} colored. Are the fraction values equivalent, "
            "and are the colored lengths equal? Explain both decisions."
        )
        teacher_answer = {
            "fractions_equivalent": True,
            "quantities_equal": False,
            "quantity_a": str(quantity_a),
            "quantity_b": str(quantity_b),
            "reason": "equal fractions of different-size wholes can represent different quantities",
        }

    return Variant(
        variant_id=f"{NAMESPACE}:{mode}:{seed}",
        mode=mode,
        structure=structure,
        prompt=prompt,
        numerator=numerator,
        denominator=denominator,
        scale=scale,
        whole_a=whole_a,
        whole_b=whole_b,
        teacher_answer=teacher_answer,
    )
