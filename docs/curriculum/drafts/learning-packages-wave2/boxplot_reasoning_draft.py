"""DRAFT ONLY: deterministic box-plot interpretation and transfer.

This module is not part of runtime routing, assessment, or mastery. All
canonical identities and standards placements remain provisional.
"""
from __future__ import annotations

from fractions import Fraction
from random import Random

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
STANDARDS_MAPPING = "PROVISIONAL_NOT_ACCEPTED"
VARIANTS = (0, 1, 2, 3, 4)


def _median(values: list[int]) -> Fraction:
    ordered = sorted(values)
    n = len(ordered)
    if n % 2:
        return Fraction(ordered[n // 2])
    return Fraction(ordered[n // 2 - 1] + ordered[n // 2], 2)


def five_number(values: list[int]) -> tuple[Fraction, ...]:
    """Median-of-halves; exclude the median for odd sample sizes.

    This is a draft convention requiring independent mathematical acceptance.
    """
    if len(values) < 5:
        raise ValueError("at least five observations required")
    ordered = sorted(values)
    middle = len(ordered) // 2
    lower = ordered[:middle]
    upper = ordered[-middle:]
    return (Fraction(ordered[0]), _median(lower), _median(ordered),
            _median(upper), Fraction(ordered[-1]))


def _fmt(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else str(value)


def _series(rng: Random, count: int) -> list[int]:
    return rng.sample(range(2, 50), count)


def _problem(rng: Random, variant: int):
    if variant == 0:
        data = _series(rng, rng.choice((9, 10)))
        summary = five_number(data)
        prompt = (
            f"Sorted scores: {sorted(data)}. Give min, Q1, median, Q3, max "
            "using median-of-halves quartiles (exclude the middle score for odd n)."
        )
        answer = ", ".join(map(_fmt, summary))
        return prompt, answer, {"data": data}, "five_number", (
            "Place the ordered values on a number line, split into lower and "
            "upper halves, then locate the five landmarks."
        )

    if variant == 1:
        first = _series(rng, 9)
        second = _series(rng, 9)
        a = five_number(first)
        b = five_number(second)
        while a[3] - a[1] == b[3] - b[1]:
            second = _series(rng, 9)
            b = five_number(second)
        answer = "A" if a[3] - a[1] > b[3] - b[1] else "B"
        prompt = (
            f"Class A scores: {sorted(first)}. Class B scores: {sorted(second)}. "
            "Which has a wider middle-half box (A or B)? "
            "Use median-of-halves quartiles."
        )
        return prompt, answer, {"a": first, "b": second}, "compare_iqr", (
            "Draw both boxes on one number line with equal scale; compare Q3−Q1."
        )

    if variant == 2:
        data = _series(rng, rng.choice((9, 10)))
        summary = five_number(data)
        prompt = (
            f"Scores: {sorted(data)}. What are the left and right ends "
            "of the box in a median-of-halves box plot? Give Q1 to Q3."
        )
        return prompt, f"{_fmt(summary[1])} to {_fmt(summary[3])}", (
            {"data": data}, "box_endpoints",
            "Sort observations; the box runs from Q1 to Q3, not min to max."
        )

    if variant == 3:
        data = _series(rng, 10)
        summary = five_number(data)
        fence = summary[3] + Fraction(3, 2) * (summary[3] - summary[1])
        # Test a new hypothetical observation against the upper fence.
        candidate = fence + 1 if rng.choice((True, False)) else fence - 1
        prompt = (
            f"Reference scores: {sorted(data)}. A new score is {_fmt(candidate)}. "
            "Does it exceed the upper 1.5×IQR outlier fence (yes or no)? "
            "Use median-of-halves quartiles from the reference scores."
        )
        return prompt, "yes" if candidate > fence else "no", (
            {"data": data, "candidate_n": candidate.numerator,
             "candidate_d": candidate.denominator}, "upper_fence",
            "Compute Q3 + 1.5×(Q3−Q1); compare the new score strictly above it."
        )

    center = rng.randint(25, 50)
    scale_a, scale_b = rng.sample(range(1, 5), 2)
    offsets = range(-4, 5)
    first = [center + scale_a * i for i in offsets]
    second = [center + scale_b * i for i in offsets]
    prompt = (
        f"Two groups have the same median. A: {first}; B: {second}. "
        "Which has a wider middle 50% (A or B)? Use the IQR, not the range."
    )
    return prompt, "A" if scale_a > scale_b else "B", (
        {"a": first, "b": second}, "same_median_transfer",
        "Hold the medians fixed and compare Q1-to-Q3 widths on one scale."
    )


def generate_item(seed: int, variant: int, mode: str) -> dict:
    """Reproducible draft contract with independent assessment isolation."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(variant) is not int or variant not in VARIANTS:
        raise ValueError("variant must be 0..4")
    if mode not in ("guided", "independent"):
        raise ValueError("mode must be guided or independent")
    rng = Random(f"mihur-w2-boxplot-v1:{mode}:{variant}:{seed}")
    prompt, answer, params, kind, visual = _problem(rng, variant)
    student = {"prompt": prompt, "mode": mode, "response_format": "short_exact"}
    if mode == "guided":
        student["socratic_hints"] = [
            "What does the question ask you to compare or locate?",
            "Which observations belong to the lower and upper halves?",
            visual,
        ]
        student["visual_instruction"] = visual
    return {
        "status": STATUS,
        "runtime_activation": RUNTIME_ACTIVATION,
        "mastery_writes": False,
        "standards_mapping": STANDARDS_MAPPING,
        "canonical_ids": "PROVISIONAL_UNASSIGNED",
        "assessment_readiness": "DRAFT_NOT_VALIDATED",
        "mastery_demonstrated": False,
        "package_id": "W2-G7-DISTRIBUTIONS-IQR",
        "item_id": f"w2-boxplot:{mode}:{variant}:{seed}",
        "student": student,
        "private": {"answer": answer, "parameters": params, "oracle_kind": kind},
    }
