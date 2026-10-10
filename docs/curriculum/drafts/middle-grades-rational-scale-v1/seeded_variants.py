"""Draft-only deterministic variants for rational scale/inverse review.

This module is not imported by runtime code and performs no persistence.
"""

import random
from dataclasses import dataclass
from fractions import Fraction

NAMESPACE = "middle-grades-rational-scale-v1"
MODES = frozenset({"guided", "independent"})


@dataclass(frozen=True)
class Variant:
    variant_id: str
    mode: str
    structure: str
    prompt: str
    left: Fraction
    right: Fraction
    answer: Fraction

    def public_payload(self) -> dict[str, str]:
        """Return fields safe to expose before an independent submission."""

        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
        }


def _nonzero_fraction(rng: random.Random) -> Fraction:
    numerator = rng.randint(1, 9)
    denominator = rng.choice((2, 3, 4, 5, 6, 8, 10))
    sign = -1 if rng.randrange(2) else 1
    return sign * Fraction(numerator, denominator)


def generate(seed: int, mode: str) -> Variant:
    """Generate a reproducible review variant in a mode-separated namespace."""

    if mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode}")
    if seed < 0:
        raise ValueError("seed must be nonnegative")

    mode_salt = 104_729 if mode == "independent" else 13_337
    rng = random.Random(seed * 1_000_003 + mode_salt)
    left = _nonzero_fraction(rng)
    right = _nonzero_fraction(rng)
    structure = "MULTIPLY_DIRECTION_SCALE" if seed % 2 == 0 else "DIVIDE_AS_MISSING_SCALE"

    if structure == "MULTIPLY_DIRECTION_SCALE":
        answer = left * right
        prompt = (
            f"A directed quantity {left} is transformed by scale {right}. "
            "Give the exact signed result."
        )
    else:
        answer = left / right
        prompt = (
            f"A scale q transforms {right} into {left}. "
            "Solve q × the input = the output exactly."
        )

    return Variant(
        variant_id=f"{NAMESPACE}:{mode}:{seed}",
        mode=mode,
        structure=structure,
        prompt=prompt,
        left=left,
        right=right,
        answer=answer,
    )
