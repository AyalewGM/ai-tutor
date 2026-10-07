from app.curriculum_gap_analysis import GapStatus, gap_counts
from app.texas_grade1_gap_audit import TX_GRADE1_GAPS, TX_GRADE1_STANDARD_CODES
from app.texas_grade2_gap_audit import TX_GRADE2_GAPS, TX_GRADE2_STANDARD_CODES


def test_texas_grade1_content_inventory_is_complete() -> None:
    assert len(TX_GRADE1_STANDARD_CODES) == 43
    assert len(TX_GRADE1_GAPS) == 43
    assert gap_counts(TX_GRADE1_GAPS) == {
        GapStatus.COVERED: 17,
        GapStatus.PARTIAL: 22,
        GapStatus.GAP: 4,
        GapStatus.AMBIGUOUS: 0,
    }


def test_texas_grade1_financial_literacy_is_not_silently_ignored() -> None:
    finance = [item for item in TX_GRADE1_GAPS if item.standard_code.startswith("1.9")]
    assert len(finance) == 4
    assert all(item.status == GapStatus.GAP for item in finance)
    assert {item.rationale for item in finance} == {
        "gap:personal-financial-literacy-foundations"
    }


def test_texas_process_standards_are_not_misrepresented_as_content_skills() -> None:
    assert not any(code.startswith("1.1") for code in TX_GRADE1_STANDARD_CODES)


def test_texas_grade2_content_inventory_is_complete() -> None:
    assert len(TX_GRADE2_STANDARD_CODES) == 43
    assert len(TX_GRADE2_GAPS) == 43
    assert gap_counts(TX_GRADE2_GAPS) == {
        GapStatus.COVERED: 13,
        GapStatus.PARTIAL: 24,
        GapStatus.GAP: 6,
        GapStatus.AMBIGUOUS: 0,
    }


def test_texas_grade2_financial_literacy_reuses_shared_gap() -> None:
    finance = [item for item in TX_GRADE2_GAPS if item.standard_code.startswith("2.11")]
    assert len(finance) == 6
    assert {item.rationale for item in finance} == {
        "gap:personal-financial-literacy-foundations"
    }
