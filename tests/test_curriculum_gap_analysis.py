import pytest

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
