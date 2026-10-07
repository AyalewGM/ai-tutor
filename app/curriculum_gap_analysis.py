"""Fail-closed curriculum-to-canonical gap accounting.

This module deliberately does not infer mathematical equivalence. Mapping authors
must classify each authoritative standard explicitly; automation only validates
completeness and aggregates the reviewed/proposed classifications.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum


class GapStatus(StrEnum):
    COVERED = "COVERED"
    PARTIAL = "PARTIAL"
    GAP = "GAP"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class StandardGap:
    state_code: str
    grade: int
    standard_code: str
    status: GapStatus
    canonical_skill_code: str | None = None
    rationale: str | None = None

    def __post_init__(self) -> None:
        if len(self.state_code.strip()) != 2:
            raise ValueError("state_code must be a two-letter code")
        if self.grade not in range(1, 10):
            raise ValueError("grade must be 1 through 9")
        if not self.standard_code.strip():
            raise ValueError("standard_code is required")
        if self.status in {GapStatus.COVERED, GapStatus.PARTIAL} and not (
            self.canonical_skill_code and self.canonical_skill_code.strip()
        ):
            raise ValueError(f"{self.status} requires a canonical skill")
        if self.status in {GapStatus.GAP, GapStatus.AMBIGUOUS} and self.canonical_skill_code:
            raise ValueError(
                f"{self.status} must fail closed without a canonical skill assignment"
            )


def validate_inventory(
    expected_standard_codes: tuple[str, ...],
    gaps: tuple[StandardGap, ...],
) -> None:
    """Require exactly one explicit classification for every authoritative code."""

    expected = tuple(code.strip() for code in expected_standard_codes)
    if any(not code for code in expected):
        raise ValueError("authoritative standard codes must be non-empty")
    if len(set(expected)) != len(expected):
        raise ValueError("authoritative standard inventory contains duplicate codes")

    actual = tuple(item.standard_code.strip() for item in gaps)
    counts = Counter(actual)
    duplicates = sorted(code for code, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate gap classifications: {', '.join(duplicates)}")

    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        raise ValueError("; ".join(details))


def gap_counts(gaps: tuple[StandardGap, ...]) -> dict[GapStatus, int]:
    counts = Counter(item.status for item in gaps)
    return {status: counts[status] for status in GapStatus}


def implementation_priority(
    state_gaps: dict[str, tuple[StandardGap, ...]],
) -> tuple[tuple[str, int], ...]:
    """Rank shared gap audit keys by the number of states requiring them."""

    states_by_gap: dict[str, set[str]] = {}
    for state_code, gaps in state_gaps.items():
        for item in gaps:
            if item.status != GapStatus.GAP or not item.rationale:
                continue
            marker = item.rationale.strip()
            if not marker.startswith("gap:"):
                continue
            states_by_gap.setdefault(marker, set()).add(state_code.strip().upper())
    return tuple(
        sorted(
            ((key, len(states)) for key, states in states_by_gap.items()),
            key=lambda row: (-row[1], row[0]),
        )
    )
