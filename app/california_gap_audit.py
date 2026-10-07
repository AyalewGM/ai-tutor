"""Aggregate California Grades 1-8 proposed gap audit."""

from app.california_grade1_gap_audit import CA_GRADE1_GAPS
from app.california_grade2_gap_audit import CA_GRADE2_GAPS
from app.california_grade3_gap_audit import CA_GRADE3_GAPS
from app.california_grade4_gap_audit import CA_GRADE4_GAPS
from app.california_grade5_gap_audit import CA_GRADE5_GAPS
from app.california_grade6_gap_audit import CA_GRADE6_GAPS
from app.california_grade7_gap_audit import CA_GRADE7_GAPS
from app.california_grade8_gap_audit import CA_GRADE8_GAPS
from app.curriculum_gap_analysis import GapStatus, StandardGap, gap_counts

CA_GRADE1_8_GAPS: dict[int, tuple[StandardGap, ...]] = {
    1: CA_GRADE1_GAPS,
    2: CA_GRADE2_GAPS,
    3: CA_GRADE3_GAPS,
    4: CA_GRADE4_GAPS,
    5: CA_GRADE5_GAPS,
    6: CA_GRADE6_GAPS,
    7: CA_GRADE7_GAPS,
    8: CA_GRADE8_GAPS,
}


def california_grade1_8_summary() -> dict[GapStatus, int]:
    return gap_counts(tuple(item for grade in range(1, 9) for item in CA_GRADE1_8_GAPS[grade]))


def california_true_gap_keys() -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                item.rationale
                for grade in range(1, 9)
                for item in CA_GRADE1_8_GAPS[grade]
                if item.status == GapStatus.GAP and item.rationale
            }
        )
    )
