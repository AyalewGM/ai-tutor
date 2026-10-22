"""Pure trusted statistical scoring, not a question registry or activation mechanism.

Trusted server routing must supply raw observations and assessment kind.
Uses median-of-halves excluding the middle for odd-sized datasets.
Returns correctness only. Never writes learner or mastery history.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction

_NUMBER = re.compile(r"[+-]?(?:\d+|\d+/[1-9]\d*|\d+\.\d+)")
_MAX_OBSERVATIONS = 128


@dataclass(frozen=True)
class ScoreOutcome:
    correct: bool


def _number(value: object) -> Fraction | None:
    if isinstance(value, bool) or not isinstance(value, (str, int, Fraction)):
        return None
    if isinstance(value, str):
        raw = value.strip()
        if len(raw) > 64 or _NUMBER.fullmatch(raw) is None:
            return None
        try:
            return Fraction(raw)
        except (ValueError, ZeroDivisionError):
            return None
    return Fraction(value)


def _observations(values: Sequence[object]) -> list[Fraction] | None:
    if isinstance(values, (str, bytes)) or not 5 <= len(values) <= _MAX_OBSERVATIONS:
        return None
    parsed = [_number(value) for value in values]
    if any(value is None for value in parsed):
        return None
    return sorted(value for value in parsed if value is not None)


def _median(values: Sequence[Fraction]) -> Fraction:
    n = len(values)
    return values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2


def _summary(values: Sequence[Fraction], modified: bool) -> dict[str, object]:
    half = len(values) // 2
    q1, med, q3 = _median(values[:half]), _median(values), _median(values[-half:])
    iqr = q3 - q1
    low, high = q1 - Fraction(3, 2) * iqr, q3 + Fraction(3, 2) * iqr
    kept = [value for value in values if low <= value <= high]
    result: dict[str, object] = {
        "minimum": values[0], "q1": q1, "median": med, "q3": q3,
        "maximum": values[-1], "iqr": iqr,
    }
    if modified:
        result.update({
            "lower_fence": low, "upper_fence": high,
            "left_whisker": kept[0], "right_whisker": kept[-1],
            "outliers": [value for value in values if value < low or value > high],
        })
    else:
        result.update({"left_whisker": values[0], "right_whisker": values[-1]})
    return result


_FIELDS = {
    "QUARTILES_IQR": ("q1", "median", "q3", "iqr"),
    "FIVE_NUMBER": ("minimum", "q1", "median", "q3", "maximum"),
    "ORDINARY_BOX": (
        "minimum", "q1", "median", "q3", "maximum",
        "left_whisker", "right_whisker",
    ),
    "MODIFIED_BOX": (
        "q1", "median", "q3", "iqr", "lower_fence", "upper_fence",
        "left_whisker", "right_whisker", "outliers",
    ),
}


def score_box_plot(
    observations: Sequence[object], response: Mapping[str, object], *, kind: str
) -> ScoreOutcome:
    """Exact, full-field scoring. Not an authorization or mastery-credit decision."""
    if kind not in _FIELDS or not isinstance(response, Mapping):
        return ScoreOutcome(False)
    values = _observations(observations)
    if values is None or set(response) != set(_FIELDS[kind]):
        return ScoreOutcome(False)
    expected = _summary(values, modified=(kind == "MODIFIED_BOX"))
    for field in _FIELDS[kind]:
        target = expected[field]
        value = response[field]
        if field == "outliers":
            if not isinstance(value, list) or len(value) > _MAX_OBSERVATIONS:
                return ScoreOutcome(False)
            actual = [_number(v) for v in value]
            if any(v is None for v in actual) or sorted(actual) != target:
                return ScoreOutcome(False)
        elif _number(value) != target:
            return ScoreOutcome(False)
    return ScoreOutcome(True)


def score_box_comparison(
    group_a: Sequence[object], group_b: Sequence[object], response: Mapping[str, object]
) -> ScoreOutcome:
    """Exact medians/IQRs and wider-middle-50% decision, including ties."""
    fields = {"median_a", "median_b", "iqr_a", "iqr_b", "wider"}
    if not isinstance(response, Mapping) or set(response) != fields:
        return ScoreOutcome(False)
    a, b = _observations(group_a), _observations(group_b)
    if a is None or b is None:
        return ScoreOutcome(False)
    sa, sb = _summary(a, False), _summary(b, False)
    for key in ("median_a", "median_b", "iqr_a", "iqr_b"):
        metric, side = key.rsplit("_", 1)
        expected = sa[metric] if side == "a" else sb[metric]
        if _number(response[key]) != expected:
            return ScoreOutcome(False)
    width_a, width_b = sa["iqr"], sb["iqr"]
    winner = "A" if width_a > width_b else "B" if width_b > width_a else "EQUAL"
    return ScoreOutcome(
        isinstance(response["wider"], str) and response["wider"].strip().upper() == winner
    )
