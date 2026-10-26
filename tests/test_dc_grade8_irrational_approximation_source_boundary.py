"""Fail-closed regression for the DC Grade 8 irrational-approximation slice.

Locks the official source locator, complete rational-approximation qualifier
boundary, and inactive candidate relation required by Issue #377.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
EXPECTATIONS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.expectations.v1.json"
LOCATORS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.source_fidelity_locators.v1.json"
TRIAGE = ROOT / "docs/curriculum/coverage/dmv_grades7_8_expectation_depth_triage.v1.json"

OFFICIAL_PDF = "https://corestandards.org/wp-content/uploads/2023/09/ADA-Compliant-Math-Standards.pdf"
EXPECTED_INCLUDED = {
    "Bound a square root between consecutive integers.",
    "Locate one supplied square root approximately on a number line.",
}
EXPECTED_EXCLUDED = {
    "Compare sizes of irrational numbers through rational approximations.",
    "Estimate the value of expressions involving irrational numbers.",
    "Generate and explain successively better rational or decimal approximations.",
}


def _row(path: Path, collection: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return next(
        row
        for row in payload[collection]
        if row.get("expectation_id") == "8.NS.A.2"
        and row.get("jurisdiction", "DC") == "DC"
    )


def test_dc_8_ns_a_2_official_source_and_complete_scope() -> None:
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
        "rational approximations",
        "compare irrational sizes",
        "number-line diagram",
        "estimate expressions",
        "successive refinement",
    ))

    bounded = locator["bounded_mathematical_scope_evidence"]
    conditions = " ".join(bounded["required_conditions"]).lower()
    assert bounded["unlettered_standard"] is True
    assert bounded["source_printed_page"] == 54
    assert bounded["canonical_equivalence"] == "NOT_ESTABLISHED"
    assert bounded["downstream_full_coverage_allowed"] is False
    assert all(term in conditions for term in (
        "compare",
        "number-line",
        "expressions",
        "successively better",
        "explain",
    ))


def test_dc_8_ns_a_2_partial_reuse_is_fail_closed() -> None:
    expectation = _row(EXPECTATIONS, "expectations")
    locator = _row(LOCATORS, "records")
    triage = _row(TRIAGE, "rows")

    assert expectation["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    assert expectation["classification"]["standards_mapped"] == "NO"
    assert expectation["repository_existing_crosswalks"] == []
    assert expectation["repository_candidate_crosswalks"] == ["M8.NS.RAD"]
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
        assert relation["candidate"] == "M8.NS.RAD"
        assert relation["status"] == "PARTIAL_NON_EXHAUSTIVE"
        assert relation["acceptance_status"] == "PROVISIONAL_NOT_ACCEPTED"
        evidenced = relation.get("included_scope", relation.get("evidenced_scope"))
        assert set(evidenced) == EXPECTED_INCLUDED
        assert set(relation["excluded_required_scope"]) == EXPECTED_EXCLUDED
        assert relation["coverage_credit"] is False
        assert relation["mapping_activation"] is False
        assert relation["canonical_correspondence"] == "NOT_ESTABLISHED"
        assert relation["union_inheritance_forbidden"] is True

    assert expectation["mapping_evidence_boundary"]["missing_mathematical_content_inferred"] is False


def test_dc_8_ns_a_2_manifest_pin_and_pr_provenance_are_total() -> None:
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
    manifest = next(
        source for source in triage["source_manifests"] if source["jurisdiction"] == "DC"
    )
    dc_rows = [row for row in triage["rows"] if row["jurisdiction"] == "DC"]

    assert len(expectations["expectations"]) == 81
    assert len(dc_rows) == 52
    assert manifest["ref"] == f"refs/pull/{manifest['pr']}/head"
    assert all(row["source_pr"] == f"#{manifest['pr']}" for row in dc_rows)
    assert {row["source_blob_sha"] for row in dc_rows} == {manifest["blob_sha"]}
    assert next(
        row for row in dc_rows if row["expectation_id"] == "8.NS.A.2"
    )["source_url"] == OFFICIAL_PDF
    assert "8.NS.A.2" in manifest["scope_note"]
