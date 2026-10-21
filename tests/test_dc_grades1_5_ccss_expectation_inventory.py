import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "dc_grades1_5_ccss.expectations.v1.json"
)

EXPECTED_COUNTS = {1: 21, 2: 26, 3: 25, 4: 28, 5: 26}
VALID_DOMAINS = {"OA", "NBT", "NF", "MD", "G"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_identifier_set_matches_official_counts() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    ids = [r["expectation_id"] for r in rows]
    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(ids) == 126 and len(set(ids)) == 126
    for grade, count in EXPECTED_COUNTS.items():
        got = [i for i in ids if i.startswith(f"{grade}.")]
        assert len(got) == count, f"grade {grade}: expected {count}, got {len(got)}"


def test_ccss_identifier_shape_and_clusters() -> None:
    for row in _manifest()["expectations"]:
        assert re.fullmatch(r"\d\.(OA|NBT|NF|MD|G)\.[A-Z]\.\d+", row["expectation_id"])
        assert row["domain"] in VALID_DOMAINS
        assert row["cluster"] and len(row["cluster"]) == 1
        # NF exists only in grades 3-5
        if row["domain"] == "NF":
            assert row["grade"] >= 3


def test_every_row_has_source_locator_and_capture() -> None:
    for row in _manifest()["expectations"]:
        grade, domain, cluster, number = row["expectation_id"].split(".")
        assert row["source_locator"] == (
            f"https://www.thecorestandards.org/Math/Content/{grade}/{domain}/{cluster}/{number}/"
        )
        assert "/None/" not in row["source_locator"]
        assert row["source_locator_status"] == "DERIVED_FROM_CCSSL_ID_NOT_INDEPENDENTLY_FETCH_VERIFIED"
        assert row["scope_completeness_status"] in {
            "PENDING_OFFICIAL_TEXT_AND_CLUSTER_BOUNDARY_REEXTRACTION",
            "BOUNDED_HEADING_SPILLOVER_CORRECTED_REMAINDER_UNVERIFIED",
        }
        assert "<div" not in row["scope_summary"].lower()
        assert "<span" not in row["scope_summary"].lower()
        assert row["official_text_capture_status"] == "AUTHOR_EXTRACTION_UNVERIFIED_NOT_ACCEPTED"
        assert len(row["scope_summary"]) >= 30
        assert "CCSS.Math" not in row["scope_summary"]


def test_fail_closed_classification_on_every_row() -> None:
    m = _manifest()
    for row in m["expectations"]:
        c = row["classification"]
        assert c["verified_mastery_evidence"] == "NO_AND_MUST_NOT_BE_INFERRED"
        assert row["proposed_mapping_status"] in {
            "REPOSITORY_EXISTING_UNVERIFIED", "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"}
    assert m["safety"]["activation"] == "FORBIDDEN"


def test_reconciliation_counts_reconcile() -> None:
    m = _manifest()
    rows = m["expectations"]
    linked = sum(1 for r in rows if r["repository_existing_crosswalks"])
    assert m["reconciliation"]["official_expectation_count"] == len(rows)
    assert m["reconciliation"]["expectations_with_provisional_links"] == linked
    assert m["reconciliation"]["unmapped_expectations"] == len(rows) - linked


def test_contaminated_original_preserved_and_all_scope_claims_blocked() -> None:
    rows = _manifest()["expectations"]
    captured = [r for r in rows if "raw_scope_capture" in r]
    assert len(captured) == 94
    assert all("<div" in r["raw_scope_capture"].lower() for r in captured)
    assert sum("SCOPE_TEXT_MAY_CONTAIN_ADJACENT_CLUSTER_HEADING_REQUIRES_SOURCE_REVIEW" in r["blockers"] for r in rows) == 108
    assert all(r["classification"]["verified_mastery_evidence"] == "NO_AND_MUST_NOT_BE_INFERRED" for r in rows)


def test_seven_verified_individual_standard_boundaries() -> None:
    """Pin publisher-checked heading spillovers; never imply whole-inventory acceptance."""
    rows = {r["expectation_id"]: r for r in _manifest()["expectations"]}
    heading_by_id = {
        "1.OA.A.2": "Understand and apply properties of operations and the relationship between addition and subtraction.",
        "1.OA.B.4": "Add and subtract within 20.",
        "1.OA.C.6": "Work with addition and subtraction equations.",
        "1.NBT.A.1": "Understand place value.",
        "1.NBT.B.3": "Use place value understanding and properties of operations to add and subtract.",
        "2.OA.A.1": "Add and subtract within 20.",
        "2.NBT.A.4": "Use place value understanding and properties of operations to add and subtract.",
    }
    assert sum("source_boundary_evidence" in row for row in rows.values()) == 18
    for standard_id, heading in heading_by_id.items():
        row = rows[standard_id]
        evidence = row["source_boundary_evidence"]
        assert evidence["removed_adjacent_cluster_heading"] == heading
        assert evidence["individual_standard_url"] == row["source_locator"]
        assert not row["scope_summary"].endswith(heading)
        assert row["scope_completeness_status"] == (
            "BOUNDED_HEADING_SPILLOVER_CORRECTED_REMAINDER_UNVERIFIED"
        )
        assert row["official_text_capture_status"] == "AUTHOR_EXTRACTION_UNVERIFIED_NOT_ACCEPTED"
        assert row["classification"]["verified_mastery_evidence"] == "NO_AND_MUST_NOT_BE_INFERRED"
        assert "REMAINING_SOURCE_FIDELITY_NOT_INDEPENDENTLY_ACCEPTED" in row["blockers"]


def test_nine_more_publisher_cluster_boundaries_are_excluded() -> None:
    """Bounded source repair, not independent full statement acceptance."""
    rows = {r["expectation_id"]: r for r in _manifest()["expectations"]}
    headings = {
        "1.MD.B.3": "Represent and interpret data.",
        "2.MD.C.8": "Represent and interpret data.",
        "3.MD.A.2": "Represent and interpret data.",
        "3.MD.B.4": "Geometric measurement: understand concepts of area and relate area to multiplication and to addition.",
        "4.NBT.A.3": "Use place value understanding and properties of operations to perform multi-digit arithmetic.",
        "4.MD.A.3": "Represent and interpret data.",
        "4.MD.B.4": "Geometric measurement: understand concepts of angle and measure angles.",
        "5.MD.A.1": "Represent and interpret data.",
        "5.MD.B.2": "Geometric measurement: understand concepts of volume.",
    }
    for code, heading in headings.items():
        row = rows[code]
        assert not row["scope_summary"].endswith(heading)
        assert row["source_boundary_evidence"]["removed_adjacent_cluster_heading"] == heading
        assert row["source_boundary_evidence"]["individual_standard_url"] == row["source_locator"]
        assert row["scope_completeness_status"] == (
            "BOUNDED_HEADING_SPILLOVER_CORRECTED_REMAINDER_UNVERIFIED"
        )
        assert "REMAINING_SOURCE_FIDELITY_NOT_INDEPENDENTLY_ACCEPTED" in row["blockers"]
        assert row["official_text_capture_status"] == "AUTHOR_EXTRACTION_UNVERIFIED_NOT_ACCEPTED"
        assert row["classification"]["verified_mastery_evidence"] == "NO_AND_MUST_NOT_BE_INFERRED"
    assert _manifest()["safety"]["activation"] == "FORBIDDEN"


def test_two_grade3_heading_boundaries_are_excluded() -> None:
    rows = {r["expectation_id"]: r for r in _manifest()["expectations"]}
    expected = {
        "3.OA.A.4": "Understand properties of multiplication and the relationship between multiplication and division.",
        "3.OA.B.6": "Multiply and divide within 100.",
    }
    for standard_id, heading in expected.items():
        row = rows[standard_id]
        assert row["source_boundary_evidence"]["removed_adjacent_cluster_heading"] == heading
        assert row["source_boundary_evidence"]["individual_standard_url"] == row["source_locator"]
        assert not row["scope_summary"].endswith(heading)
        assert row["scope_completeness_status"] == (
            "BOUNDED_HEADING_SPILLOVER_CORRECTED_REMAINDER_UNVERIFIED"
        )
        assert row["official_text_capture_status"] == "AUTHOR_EXTRACTION_UNVERIFIED_NOT_ACCEPTED"
        assert row["classification"]["verified_mastery_evidence"] == "NO_AND_MUST_NOT_BE_INFERRED"
