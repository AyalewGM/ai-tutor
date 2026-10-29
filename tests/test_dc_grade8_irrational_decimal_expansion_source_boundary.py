"""Fail-closed regression for the DC Grade 8 irrational/decimal-expansion slice.

Locks the official source, complete 8.NS.A.1 qualifier boundary, exhaustive
repository-candidate inventory, and inactive/no-credit relation semantics.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
EXPECTATIONS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.expectations.v1.json"
LOCATORS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.source_fidelity_locators.v1.json"
TRIAGE = ROOT / "docs/curriculum/coverage/dmv_grades7_8_expectation_depth_triage.v1.json"

OFFICIAL_PDF = "https://corestandards.org/wp-content/uploads/2023/09/ADA-Compliant-Math-Standards.pdf"
EXPECTED_CANDIDATES = {
    "M8.NS.RAD",
    "MATH.NS.IRRATIONAL.CLASSIFY",
    "MATH.NS.IRRATIONAL.APPROX",
    "MATH.DEC.FRAC_TO_DEC",
    "MATH.DEC.DEC_TO_FRAC",
    "MATH.DEC.FRACTION.TENTHS",
    "MATH.DEC.FRACTION.HUNDREDTHS",
}


def _row(path: Path, collection: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return next(
        row for row in payload[collection]
        if row.get("expectation_id") == "8.NS.A.1"
        and row.get("jurisdiction", "DC") == "DC"
    )


def test_dc_8_ns_a_1_official_source_and_complete_unlettered_scope() -> None:
    expectation = _row(EXPECTATIONS, "expectations")
    locator = _row(LOCATORS, "records")

    assert expectation["source_locator"] == locator["source_text_url"] == OFFICIAL_PDF
    assert expectation["source_domain_section_url"] == locator["source_section_url"] == OFFICIAL_PDF
    assert expectation["source_publication_version"] == locator["source_version"] == "2010"
    assert expectation["source_printed_page"] == locator["source_printed_page"] == 54
    assert expectation["official_subpart_identifiers"] == locator["lettered_subpart_ids"] == []
    assert expectation["adoption_date"] == locator["adoption_date"] == "2010-07-21"
    assert expectation["access_date"] == locator["access_date"] == "2026-10-26"

    scope = expectation["scope_summary"].lower()
    assert all(term in scope for term in (
        "non-rational numbers are irrational",
        "every number has a decimal expansion",
        "eventually repeats",
        "eventually repeating decimal expansion",
        "rational number",
    ))
    bounded = locator["bounded_mathematical_scope_evidence"]
    assert bounded["unlettered_standard"] is True
    assert bounded["source_printed_page"] == 54
    assert bounded["short_summary_is_exhaustive"] is False
    assert bounded["canonical_equivalence"] == "NOT_ESTABLISHED"
    assert bounded["downstream_full_coverage_allowed"] is False


def test_dc_8_ns_a_1_inventories_all_candidates_without_union_credit() -> None:
    expectation = _row(EXPECTATIONS, "expectations")
    locator = _row(LOCATORS, "records")
    triage = _row(TRIAGE, "rows")

    assert expectation["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    assert expectation["classification"]["standards_mapped"] == "NO"
    assert expectation["repository_existing_crosswalks"] == []
    assert set(expectation["repository_candidate_crosswalks"]) == EXPECTED_CANDIDATES
    assert triage["coverage_classification"] == "NEEDS_IDENTITY_DECISION"
    assert triage["missing_core_verified"] is False
    assert triage["verified_depth"] is False
    assert triage["provisional"] is True

    inventories = [
        expectation["mapping_evidence_boundary"]["candidate_inventory"],
        locator["canonical_candidate_inventory"],
        triage["reuse_relations"],
    ]
    assert all({r["candidate"] for r in rows} == EXPECTED_CANDIDATES for rows in inventories)
    for rows in inventories:
        for relation in rows:
            assert relation["acceptance_status"] == "PROVISIONAL_NOT_ACCEPTED"
            assert relation["coverage_credit"] is False
            assert relation["mapping_activation"] is False
            assert relation["canonical_correspondence"] == "NOT_ESTABLISHED"
            assert relation["union_inheritance_forbidden"] is True
            assert relation["validated_practice"] is False
            assert relation["assessment_ready"] is False

    status = {r["candidate"]: r["status"] for r in locator["canonical_candidate_inventory"]}
    assert status["M8.NS.RAD"] == "PARTIAL_NON_EXHAUSTIVE"
    assert status["MATH.NS.IRRATIONAL.CLASSIFY"] == "PARTIAL_NON_EXHAUSTIVE"
    assert all(status[c] == "NO_COVERAGE_CLAIM" for c in EXPECTED_CANDIDATES - {
        "M8.NS.RAD", "MATH.NS.IRRATIONAL.CLASSIFY"
    })
    assert expectation["mapping_evidence_boundary"]["missing_mathematical_content_inferred"] is False


def test_dc_8_ns_a_1_repeating_decimal_gap_is_not_inferred_from_finite_conversion() -> None:
    locator = _row(LOCATORS, "records")
    relations = {r["candidate"]: r for r in locator["canonical_candidate_inventory"]}

    for candidate in (
        "MATH.DEC.FRAC_TO_DEC",
        "MATH.DEC.DEC_TO_FRAC",
        "MATH.DEC.FRACTION.TENTHS",
        "MATH.DEC.FRACTION.HUNDREDTHS",
    ):
        relation = relations[candidate]
        assert relation["status"] == "NO_COVERAGE_CLAIM"
        excluded = " ".join(relation["excluded_required_scope"]).lower()
        assert "repeating" in excluded
        assert relation["canonical_parent"] == "MATH.NS.DECIMAL.CONVERT"

    approximate = relations["MATH.NS.IRRATIONAL.APPROX"]
    assert approximate["status"] == "NO_COVERAGE_CLAIM"
    assert any("nearest tenth" in item for item in approximate["included_scope"])
    classify = relations["MATH.NS.IRRATIONAL.CLASSIFY"]
    assert classify["canonical_parent"] == "MATH.NS.IRRATIONAL"
    assert any("non-perfect-square" in item for item in classify["included_scope"])


def test_dc_8_ns_a_1_manifest_pin_and_pr_provenance_are_total() -> None:
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
    manifest = next(m for m in triage["source_manifests"] if m["jurisdiction"] == "DC")
    dc_rows = [row for row in triage["rows"] if row["jurisdiction"] == "DC"]

    assert len(expectations["expectations"]) == 81
    assert len(dc_rows) == 52
    assert manifest["pr"] == 510
    assert manifest["ref"] == "refs/pull/510/head"
    assert all(row["source_pr"] == "#510" for row in dc_rows)
    assert {row["source_blob_sha"] for row in dc_rows} == {manifest["blob_sha"]}
    assert next(row for row in dc_rows if row["expectation_id"] == "8.NS.A.1")["source_url"] == OFFICIAL_PDF
    assert "8.NS.A.1" in manifest["scope_note"]
