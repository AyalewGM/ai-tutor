"""Aggregate Texas Grades 1-8 proposed content gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, gap_counts
from app.texas_grade1_gap_audit import TX_GRADE1_GAPS
from app.texas_grade2_gap_audit import TX_GRADE2_GAPS
from app.texas_grade3_gap_audit import TX_GRADE3_GAPS
from app.texas_grade4_gap_audit import TX_GRADE4_GAPS
from app.texas_grade5_gap_audit import TX_GRADE5_GAPS
from app.texas_grade6_gap_audit import TX_GRADE6_GAPS
from app.texas_grade7_gap_audit import TX_GRADE7_GAPS
from app.texas_grade8_gap_audit import TX_GRADE8_GAPS

TX_GRADE1_8_GAPS: dict[int, tuple[StandardGap, ...]] = {
    1: TX_GRADE1_GAPS,
    2: TX_GRADE2_GAPS,
    3: TX_GRADE3_GAPS,
    4: TX_GRADE4_GAPS,
    5: TX_GRADE5_GAPS,
    6: TX_GRADE6_GAPS,
    7: TX_GRADE7_GAPS,
    8: TX_GRADE8_GAPS,
}


def texas_grade1_8_summary() -> dict[GapStatus, int]:
    return gap_counts(tuple(item for grade in range(1, 9) for item in TX_GRADE1_8_GAPS[grade]))


def texas_true_gap_keys() -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                item.rationale
                for grade in range(1, 9)
                for item in TX_GRADE1_8_GAPS[grade]
                if item.status == GapStatus.GAP and item.rationale
            }
        )
    )
