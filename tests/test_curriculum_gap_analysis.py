import pytest

from app.california_gap_audit import california_grade1_8_summary, california_true_gap_keys
from app.california_grade1_gap_audit import CA_GRADE1_GAPS, CA_GRADE1_STANDARD_CODES
from app.california_grade2_gap_audit import CA_GRADE2_GAPS, CA_GRADE2_STANDARD_CODES
from app.california_grade3_gap_audit import CA_GRADE3_GAPS, CA_GRADE3_STANDARD_CODES
from app.california_grade4_gap_audit import CA_GRADE4_GAPS, CA_GRADE4_STANDARD_CODES
from app.california_grade5_gap_audit import CA_GRADE5_GAPS, CA_GRADE5_STANDARD_CODES
from app.california_grade6_gap_audit import CA_GRADE6_GAPS, CA_GRADE6_STANDARD_CODES
from app.california_grade7_gap_audit import CA_GRADE7_GAPS, CA_GRADE7_STANDARD_CODES
from app.california_grade8_gap_audit import CA_GRADE8_GAPS, CA_GRADE8_STANDARD_CODES
from app.california_grade9_inventory import (
    CA_ALGEBRA_I_STANDARD_CODES,
    CA_MATHEMATICS_I_STANDARD_CODES,
)
from app.curriculum_gap_analysis import (
    GapStatus,
    StandardGap,
    gap_counts,
    implementation_priority,
    validate_inventory,
)
from app.us_state_curriculum_sources import Grade9Structure, source_for


def test_texas_and_florida_sources_are_verified_without_claiming_coverage() -> None:
    texas = source_for("TX")
    florida = source_for("FL")
    assert texas is not None
    assert florida is not None
    assert texas.grade9_structure == Grade9Structure.COURSE
    assert florida.grade9_structure == Grade9Structure.COURSE
    assert texas.lifecycle_status == "IMPLEMENTED"
    assert florida.lifecycle_status == "IMPLEMENTED"


def test_gap_records_fail_closed() -> None:
    with pytest.raises(ValueError, match="requires a canonical skill"):
        StandardGap("CA", 4, "4.NF.1", GapStatus.COVERED)
    with pytest.raises(ValueError, match="fail closed"):
        StandardGap(
            "CA",
            4,
            "4.NF.1",
            GapStatus.GAP,
            canonical_skill_code="MATH.NF.EQUIVALENT_FRACTIONS",
        )


def test_inventory_requires_exact_authoritative_code_coverage() -> None:
    gaps = (
        StandardGap(
            "CA",
            4,
            "4.NF.1",
            GapStatus.COVERED,
            "MATH.NF.EQUIVALENT_FRACTIONS",
        ),
    )
    validate_inventory(("4.NF.1",), gaps)
    with pytest.raises(ValueError, match="missing"):
        validate_inventory(("4.NF.1", "4.NF.2"), gaps)


def test_gap_counts_preserve_ambiguous_as_distinct_from_gap() -> None:
    gaps = (
        StandardGap("CA", 8, "8.G.1", GapStatus.PARTIAL, "MATH.GEO.TRANSFORMATIONS"),
        StandardGap("CA", 8, "8.G.2", GapStatus.AMBIGUOUS),
        StandardGap("CA", 8, "8.G.3", GapStatus.GAP, rationale="gap:dilation-coordinates"),
    )
    counts = gap_counts(gaps)
    assert counts[GapStatus.PARTIAL] == 1
    assert counts[GapStatus.AMBIGUOUS] == 1
    assert counts[GapStatus.GAP] == 1
    assert counts[GapStatus.COVERED] == 0


def test_cross_state_priority_counts_each_state_once_per_gap() -> None:
    california = (
        StandardGap("CA", 7, "7.G.4", GapStatus.GAP, rationale="gap:circle-measures"),
        StandardGap("CA", 8, "8.G.9", GapStatus.GAP, rationale="gap:solid-volume"),
    )
    texas = (
        StandardGap("TX", 7, "111.27.b.8", GapStatus.GAP, rationale="gap:circle-measures"),
    )
    florida = (
        StandardGap("FL", 7, "MA.7.GR.1.1", GapStatus.GAP, rationale="gap:circle-measures"),
    )
    assert implementation_priority(
        {"CA": california, "TX": texas, "FL": florida}
    ) == (("gap:circle-measures", 3), ("gap:solid-volume", 1))


def test_california_grade8_inventory_is_complete_and_exposes_depth_not_fake_gaps() -> None:
    assert len(CA_GRADE8_STANDARD_CODES) == 28
    assert len(CA_GRADE8_GAPS) == 28
    counts = gap_counts(CA_GRADE8_GAPS)
    assert counts == {
        GapStatus.COVERED: 15,
        GapStatus.PARTIAL: 11,
        GapStatus.GAP: 2,
        GapStatus.AMBIGUOUS: 0,
    }
    true_gaps = {
        item.rationale for item in CA_GRADE8_GAPS if item.status == GapStatus.GAP
    }
    assert true_gaps == {
        "gap:irrational-number-concept",
        "gap:irrational-approximation",
    }


def test_california_grade7_inventory_is_complete_and_exposes_true_gaps() -> None:
    assert len(CA_GRADE7_STANDARD_CODES) == 24
    assert len(CA_GRADE7_GAPS) == 24
    counts = gap_counts(CA_GRADE7_GAPS)
    assert counts == {
        GapStatus.COVERED: 13,
        GapStatus.PARTIAL: 9,
        GapStatus.GAP: 2,
        GapStatus.AMBIGUOUS: 0,
    }
    true_gaps = {
        item.rationale for item in CA_GRADE7_GAPS if item.status == GapStatus.GAP
    }
    assert true_gaps == {
        "gap:geometric-construction-conditions",
        "gap:solid-cross-sections",
    }


def test_california_grade6_inventory_is_complete_and_exposes_true_gap() -> None:
    assert len(CA_GRADE6_STANDARD_CODES) == 29
    assert len(CA_GRADE6_GAPS) == 29
    counts = gap_counts(CA_GRADE6_GAPS)
    assert counts == {
        GapStatus.COVERED: 13,
        GapStatus.PARTIAL: 15,
        GapStatus.GAP: 1,
        GapStatus.AMBIGUOUS: 0,
    }
    assert {
        item.rationale for item in CA_GRADE6_GAPS if item.status == GapStatus.GAP
    } == {"gap:statistical-question-variability"}


def test_california_grade5_inventory_includes_ca_addition_and_no_fake_gap() -> None:
    assert "5.OA.2.1" in CA_GRADE5_STANDARD_CODES
    assert len(CA_GRADE5_STANDARD_CODES) == 27
    assert len(CA_GRADE5_GAPS) == 27
    assert gap_counts(CA_GRADE5_GAPS) == {
        GapStatus.COVERED: 11,
        GapStatus.PARTIAL: 16,
        GapStatus.GAP: 0,
        GapStatus.AMBIGUOUS: 0,
    }


def test_california_grade4_inventory_is_complete_and_exposes_true_gap() -> None:
    assert len(CA_GRADE4_STANDARD_CODES) == 28
    assert len(CA_GRADE4_GAPS) == 28
    assert gap_counts(CA_GRADE4_GAPS) == {
        GapStatus.COVERED: 17,
        GapStatus.PARTIAL: 10,
        GapStatus.GAP: 1,
        GapStatus.AMBIGUOUS: 0,
    }
    assert {
        item.rationale for item in CA_GRADE4_GAPS if item.status == GapStatus.GAP
    } == {"gap:angle-measure-draw-protractor"}


def test_california_grade3_inventory_is_complete_without_fake_gaps() -> None:
    assert len(CA_GRADE3_STANDARD_CODES) == 25
    assert len(CA_GRADE3_GAPS) == 25
    assert gap_counts(CA_GRADE3_GAPS) == {
        GapStatus.COVERED: 15,
        GapStatus.PARTIAL: 10,
        GapStatus.GAP: 0,
        GapStatus.AMBIGUOUS: 0,
    }


def test_california_grade2_inventory_is_complete_without_fake_gaps() -> None:
    assert len(CA_GRADE2_STANDARD_CODES) == 26
    assert len(CA_GRADE2_GAPS) == 26
    assert gap_counts(CA_GRADE2_GAPS) == {
        GapStatus.COVERED: 11,
        GapStatus.PARTIAL: 15,
        GapStatus.GAP: 0,
        GapStatus.AMBIGUOUS: 0,
    }


def test_california_grade1_inventory_is_complete_without_fake_gaps() -> None:
    assert len(CA_GRADE1_STANDARD_CODES) == 21
    assert len(CA_GRADE1_GAPS) == 21
    assert gap_counts(CA_GRADE1_GAPS) == {
        GapStatus.COVERED: 9,
        GapStatus.PARTIAL: 12,
        GapStatus.GAP: 0,
        GapStatus.AMBIGUOUS: 0,
    }


def test_california_grade1_8_aggregate_is_complete_and_conservative() -> None:
    assert california_grade1_8_summary() == {
        GapStatus.COVERED: 104,
        GapStatus.PARTIAL: 98,
        GapStatus.GAP: 6,
        GapStatus.AMBIGUOUS: 0,
    }
    assert california_true_gap_keys() == (
        "gap:angle-measure-draw-protractor",
        "gap:geometric-construction-conditions",
        "gap:irrational-approximation",
        "gap:irrational-number-concept",
        "gap:solid-cross-sections",
        "gap:statistical-question-variability",
    )


def test_california_grade9_pathway_inventories_are_explicit_and_distinct() -> None:
    assert len(CA_ALGEBRA_I_STANDARD_CODES) == 62
    assert len(CA_MATHEMATICS_I_STANDARD_CODES) == 59
    assert len(set(CA_ALGEBRA_I_STANDARD_CODES)) == 62
    assert len(set(CA_MATHEMATICS_I_STANDARD_CODES)) == 59
    assert "N-RN.1" in CA_ALGEBRA_I_STANDARD_CODES
    assert "G-CO.12" in CA_MATHEMATICS_I_STANDARD_CODES
    assert "G-CO.12" not in CA_ALGEBRA_I_STANDARD_CODES
