"""Draft-only deterministic box-plot comparison variants.

This module is not imported by runtime code.  It supplies reviewable content
and independent-oracle fixtures without activating assessment or mastery.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction

NAMESPACE = "middle-grades-iqr-boxplot-r1"
MODES = frozenset({"guided", "independent"})


def five_number(values: tuple[int, ...]) -> tuple[Fraction, ...]:
    if len(values) != 8 or tuple(sorted(values)) != values:
        raise ValueError("values must be eight sorted observations")
    lower, upper = values[:4], values[4:]
    return (
        Fraction(values[0]),
        Fraction(lower[1] + lower[2], 2),
        Fraction(values[3] + values[4], 2),
        Fraction(upper[1] + upper[2], 2),
        Fraction(values[-1]),
    )


@dataclass(frozen=True)
class BoxPlotVariant:
    variant_id: str
    mode: str
    context: str
    data_a: tuple[int, ...]
    data_b: tuple[int, ...]
    summary_a: tuple[Fraction, ...]
    summary_b: tuple[Fraction, ...]
    iqr_a: Fraction
    iqr_b: Fraction
    range_a: int
    range_b: int
    more_middle_spread: str
    more_consistent_middle: str

    def public_payload(self) -> dict[str, object]:
        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "context": self.context,
            "data_a": list(self.data_a),
            "data_b": list(self.data_b),
            "response_fields": [
                "five_number_a",
                "five_number_b",
                "iqr_a",
                "iqr_b",
                "more_middle_spread",
                "more_consistent_middle",
                "range_contrast_explanation",
            ],
        }


def _data(center: int, low: int, high: int, outer_left: int, outer_right: int) -> tuple[int, ...]:
    return (
        center - outer_left,
        center - high,
        center - low,
        center - 1,
        center + 1,
        center + low,
        center + high,
        center + outer_right,
    )


def generate(seed: int, mode: str) -> BoxPlotVariant:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")

    rng = random.Random(f"{NAMESPACE}:{mode}:{seed}")
    center = rng.randint(25, 60)
    small_low = rng.randint(2, 3)
    small_high = small_low + rng.randint(2, 3)
    large_low = small_low + rng.randint(2, 3)
    large_high = max(small_high + 2, large_low + rng.randint(2, 3))

    # The smaller-IQR set deliberately has the larger range.  This makes the
    # transfer distinguish middle-half spread from whole-data range.
    small_outer_left = large_high + rng.randint(7, 10)
    small_outer_right = large_high + rng.randint(7, 10)
    large_outer_left = large_high + rng.randint(1, 2)
    large_outer_right = large_high + rng.randint(1, 2)

    small = _data(center, small_low, small_high, small_outer_left, small_outer_right)
    large = _data(center, large_low, large_high, large_outer_left, large_outer_right)
    if rng.choice((False, True)):
        data_a, data_b = small, large
    else:
        data_a, data_b = large, small

    summary_a = five_number(data_a)
    summary_b = five_number(data_b)
    iqr_a = summary_a[3] - summary_a[1]
    iqr_b = summary_b[3] - summary_b[1]
    range_a = data_a[-1] - data_a[0]
    range_b = data_b[-1] - data_b[0]
    more_spread = "A" if iqr_a > iqr_b else "B"
    more_consistent = "B" if more_spread == "A" else "A"
    context = (
        "Compare two sensor-calibration runs. A smaller IQR means the middle half "
        "of readings is more consistent, while range describes all readings."
        if mode == "independent"
        else "Build and compare box plots for two practice-session score sets."
    )

    return BoxPlotVariant(
        variant_id=f"{NAMESPACE}:{mode}:{seed}",
        mode=mode,
        context=context,
        data_a=data_a,
        data_b=data_b,
        summary_a=summary_a,
        summary_b=summary_b,
        iqr_a=iqr_a,
        iqr_b=iqr_b,
        range_a=range_a,
        range_b=range_b,
        more_middle_spread=more_spread,
        more_consistent_middle=more_consistent,
    )


def diagnose_comparison(
    item: BoxPlotVariant,
    submitted_iqr_a: Fraction | int,
    submitted_iqr_b: Fraction | int,
    chosen_more_spread: str,
) -> str:
    a = Fraction(submitted_iqr_a)
    b = Fraction(submitted_iqr_b)
    if a < 0 or b < 0:
        return "QUARTILE_ORDER_REVERSED"
    if a == item.range_a and b == item.range_b:
        return "RANGE_USED_AS_IQR"
    if chosen_more_spread != item.more_middle_spread:
        range_choice = "A" if item.range_a > item.range_b else "B"
        if chosen_more_spread == range_choice:
            return "WHOLE_RANGE_CHOSEN_FOR_MIDDLE_SPREAD"
        return "COMPARISON_NOT_JUSTIFIED"
    if a != item.iqr_a or b != item.iqr_b:
        return "IQR_CALCULATION_ERROR"
    return "CORRECT_PRACTICE_ONLY"
