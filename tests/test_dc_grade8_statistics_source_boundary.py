"""Focused fail-closed regression for the DC Grade 8 linear-model slice.

Locks the official source locator, complete qualifier boundary, and inactive
partial-reuse relation required by the independent Standards verdict on #377.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
EXPECTATIONS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.expectations.v1.json"
LOCATORS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.source_fidelity_locators.v1.json"
TRIAGE = ROOT / "docs/curriculum/coverage/dmv_grades7_8_expectation_depth_triage.v1.json"

OFFICIAL_PDF = "https://corestandards.org/wp-content/uploads/2023/09/ADA-Compliant-Math-Standards.pdf"
EXPECTED_EXCLUDED = {
    "A bivariate measurement-data context with named quantities and units.",
    "Contextual interpretation of slope.",
    "Contextual interpretation of intercept.",
}


def _row(path: Path, collection: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload[collection]
    return next(row for row in rows if row.get("expectation_id") == "8.SP.A.3" and row.get("jurisdiction", "DC") == "DC")


def test_dc_8_sp_a_3_official_source_and_complete_scope() -> None:
    expectation = _row(EXPECTATIONS, "expectations")
    locator = _row(LOCATORS, "records")

    assert expectation["source_locator"] == locator["source_text_url"] == OFFICIAL_PDF
    assert expectation["source_domain_section_url"] == locator["source_section_url"] == OFFICIAL_PDF
    assert expectation["source_publication_version"] == locator["source_version"] == "2010"
    assert expectation["source_printed_page"] == locator["source_printed_page"] == 56
    assert expectation["official_subpart_identifiers"] == locator["lettered_subpart_ids"] == []
    assert expectation["adoption_date"] == locator["adoption_date"] == "2010-07-21"
    assert expectation["access_date"] == locator["access_date"] == "2026-10-26"

    scope = expectation["scope_summary"].lower()
    assert "bivariate measurement data" in scope
    assert "both the slope and intercept" in scope

    bounded = locator["bounded_mathematical_scope_evidence"]
    assert bounded["unlettered_standard"] is True
    assert bounded["source_printed_page"] == 56
    assert bounded["canonical_equivalence"] == "NOT_ESTABLISHED"
    assert bounded["downstream_full_coverage_allowed"] is False
    assert any("slope" in item.lower() for item in bounded["required_conditions"])
    assert any("intercept" in item.lower() for item in bounded["required_conditions"])


def test_dc_8_sp_a_3_partial_reuse_is_fail_closed() -> None:
    expectation = _row(EXPECTATIONS, "expectations")
    locator = _row(LOCATORS, "records")
    triage = _row(TRIAGE, "rows")

    assert triage["coverage_classification"] == "NEEDS_IDENTITY_DECISION"
    assert triage["missing_core_verified"] is False
    assert triage["verified_depth"] is False
    assert triage["provisional"] is True

    relations = [
        expectation["mapping_evidence_boundary"],
        locator["provisional_reuse_boundary"],
        triage["reuse_relation"],
    ]
    for relation in relations:
        assert relation["candidate"] == "M8.SP.STAT"
        assert relation["status"] == "PARTIAL_NON_EXHAUSTIVE"
        assert relation["acceptance_status"] == "PROVISIONAL_NOT_ACCEPTED"
        assert set(relation["excluded_required_scope"]) == EXPECTED_EXCLUDED
        assert relation["coverage_credit"] is False
        assert relation["mapping_activation"] is False
        assert relation["canonical_correspondence"] == "NOT_ESTABLISHED"
        assert relation["union_inheritance_forbidden"] is True

    assert expectation["mapping_evidence_boundary"]["missing_mathematical_content_inferred"] is False
    assert triage["reuse_relation"]["evidenced_scope"] == [
        "Evaluate a supplied linear-model equation for a prediction."
    ]
    assert "y = 2x + 1" in locator["provisional_reuse_boundary"]["evidenced_capability"]


def test_dc_8_sp_a_3_manifest_pin_is_total_after_correction() -> None:
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
    dc_rows = [row for row in triage["rows"] if row["jurisdiction"] == "DC"]

    assert len(dc_rows) == 52
    assert len({row["source_blob_sha"] for row in dc_rows}) == 1
    assert next(row for row in dc_rows if row["expectation_id"] == "8.SP.A.3")["source_url"] == OFFICIAL_PDF
    assert len(expectations["expectations"]) == 81
