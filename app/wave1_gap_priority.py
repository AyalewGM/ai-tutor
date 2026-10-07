"""Cross-state Wave-1 canonical gap ranking.

Only completed proposed audits are included. Adding a state is explicit so an
unmapped jurisdiction cannot silently influence implementation priority.
"""

from app.california_gap_audit import CA_GRADE1_8_GAPS
from app.curriculum_gap_analysis import StandardGap, implementation_priority
from app.texas_gap_audit import TX_GRADE1_8_GAPS


def _flatten(grades: dict[int, tuple[StandardGap, ...]]) -> tuple[StandardGap, ...]:
    return tuple(item for grade in sorted(grades) for item in grades[grade])


def wave1_grade1_8_priority() -> tuple[tuple[str, int], ...]:
    return implementation_priority(
        {
            "CA": _flatten(CA_GRADE1_8_GAPS),
            "TX": _flatten(TX_GRADE1_8_GAPS),
        }
    )
