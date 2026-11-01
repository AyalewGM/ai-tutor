"""Fail-closed regression for DC Grade 8 scientific-magnitude estimation.

Locks the official 8.EE.A.3 source, complete unlettered qualifier boundary,
bounded candidate inventory, documented selection rule, and inactive/no-credit semantics.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
EXPECTATIONS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.expectations.v1.json"
LOCATORS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.source_fidelity_locators.v1.json"
TRIAGE = ROOT / "docs/curriculum/coverage/dmv_grades7_8_expectation_depth_triage.v1.json"

OFFICIAL_PDF = "https://corestandards.org/wp-content/uploads/2023/09/ADA-Compliant-Math-Standards.pdf"
EXPECTED_CANDIDATES = {
    "MATH.SCI.CONVERT",
    "MATH.SCI.MULTIPLY",
    "MATH.EXP.EVALUATE",
    "MATH.PROP.SCALE_FACTOR",
    "MATH.RATIO.ERROR.ADDITIVE",
    "MATH.DEC.POWER10",
    "MATH.PV.POWERS_TEN",
    "MATH.PV.REASON.TEN_TIMES",
    "MATH.EST.REASONABLE",
    "MATH.EST.BENCHMARK",
    "MATH.EST.WORD",
    "MATH.MUL.WORD.COMPARE",
    "MATH.MUL.ERROR.ADDITIVE",
}
PARTIAL_CANDIDATES = {
    "MATH.SCI.CONVERT",
    "MATH.PROP.SCALE_FACTOR",
    "MATH.EST.REASONABLE",
    "MATH.EST.BENCHMARK",
    "MATH.EST.WORD",
}


def _row(path: Path, collection: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return next(
        row
        for row in payload[collection]
        if row.get("expectation_id") == "8.EE.A.3"
        and row.get("jurisdiction", "DC") == "DC"
    )


def test_dc_8_ee_a_3_official_source_and_complete_unlettered_scope() -> None:
    expectation = _row(EXPECTATIONS, "expectations")
    locator = _row(LOCATORS, "records")

    assert expectation["source_locator"] == locator["source_text_url"] == OFFICIAL_PDF
    assert expectation["source_domain_section_url"] == locator["source_section_url"] == OFFICIAL_PDF
    assert expectation["source_publication_version"] == locator["source_version"] == "2010"
    assert expectation["source_printed_page"] == locator["source_printed_page"] == 54
    assert expectation["official_subpart_identifiers"] == locator["lettered_subpart_ids"] == []
    assert expectation["adoption_date"] == locator["adoption_date"] == "2010-07-21"
    assert expectation["access_date"] == locator["access_date"] == "2026-10-27"

    scope = expectation["scope_summary"].lower()
    assert all(
        term in scope
        for term in (
            "single-digit-times-integer-power-of-ten",
            "very large",
            "very small",
            "how many times as much",
        )
    )
    bounded = locator["bounded_mathematical_scope_evidence"]
    assert bounded["unlettered_standard"] is True
    assert bounded["source_printed_page"] == 54
    assert bounded["canonical_equivalence"] == "NOT_ESTABLISHED"
    assert bounded["downstream_full_coverage_allowed"] is False


def test_dc_8_ee_a_3_inventories_candidates_without_union_credit() -> None:
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
    assert all({relation["candidate"] for relation in rows} == EXPECTED_CANDIDATES for rows in inventories)
    for rows in inventories:
        for relation in rows:
            assert relation["acceptance_status"] == "PROVISIONAL_NOT_ACCEPTED"
            assert relation["coverage_credit"] is False
            assert relation["mapping_activation"] is False
            assert relation["canonical_correspondence"] == "NOT_ESTABLISHED"
            assert relation["union_inheritance_forbidden"] is True
            assert relation["validated_practice"] is False
            assert relation["assessment_ready"] is False

    status = {relation["candidate"]: relation["status"] for relation in locator["canonical_candidate_inventory"]}
    assert all(status[candidate] == "PARTIAL_NON_EXHAUSTIVE" for candidate in PARTIAL_CANDIDATES)
    assert all(status[candidate] == "NO_COVERAGE_CLAIM" for candidate in EXPECTED_CANDIDATES - PARTIAL_CANDIDATES)
    rule = locator["candidate_selection_rule"]
    assert rule == triage["candidate_selection_rule"]
    assert rule == expectation["mapping_evidence_boundary"]["candidate_selection_rule"]
    assert rule["status"] == "BOUNDED_CANDIDATE_SELECTION_RULE"
    assert rule["coverage_inference_forbidden"] is True
    assert len(rule["included_when"]) == 3
    assert len(rule["excluded_when"]) == 2
    assert expectation["mapping_evidence_boundary"]["missing_mathematical_content_inferred"] is False
    assert expectation["mapping_evidence_boundary"]["union_of_candidates_cannot_establish_coverage"] is True


def test_dc_8_ee_a_3_candidate_boundaries_distinguish_estimation_from_adjacent_work() -> None:
    locator = _row(LOCATORS, "records")
    relations = {relation["candidate"]: relation for relation in locator["canonical_candidate_inventory"]}

    conversion = relations["MATH.SCI.CONVERT"]
    assert any("positive-integer-power" in item for item in conversion["included_scope"])
    assert any("very small" in item for item in conversion["excluded_required_scope"])
    assert any("times as much" in item for item in conversion["excluded_required_scope"])

    scale = relations["MATH.PROP.SCALE_FACTOR"]
    assert any("multiplicative comparison" in item for item in scale["included_scope"])
    assert any("scientific-notation" in item for item in scale["excluded_required_scope"])

    benchmark = relations["MATH.EST.BENCHMARK"]
    assert any("factors of ten" in item for item in benchmark["included_scope"])
    assert any("very small" in item for item in benchmark["excluded_required_scope"])

    reasonable = relations["MATH.EST.REASONABLE"]
    assert any("factor of ten" in item for item in reasonable["included_scope"])
    assert any("single-digit-times" in item for item in reasonable["excluded_required_scope"])
    assert any("very small" in item for item in reasonable["excluded_required_scope"])
    assert any("times as much" in item for item in reasonable["excluded_required_scope"])

    word = relations["MATH.EST.WORD"]
    assert any("contextual" in item for item in word["included_scope"])
    assert any("single-digit-times" in item for item in word["excluded_required_scope"])

    assert relations["MATH.SCI.MULTIPLY"]["relation_qualifier"] == "ADJACENT_STANDARD_ONLY"
    assert relations["MATH.RATIO.ERROR.ADDITIVE"]["relation_qualifier"] == "REPAIR_ONLY"
    assert relations["MATH.MUL.ERROR.ADDITIVE"]["relation_qualifier"] == "REPAIR_ONLY"
    for candidate in (
        "MATH.EXP.EVALUATE",
        "MATH.DEC.POWER10",
        "MATH.PV.POWERS_TEN",
        "MATH.PV.REASON.TEN_TIMES",
        "MATH.MUL.WORD.COMPARE",
    ):
        assert relations[candidate]["relation_qualifier"] == "PREREQUISITE_ONLY"


def test_dc_8_ee_a_3_manifest_pin_and_pr_provenance_are_total() -> None:
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
    manifest = next(item for item in triage["source_manifests"] if item["jurisdiction"] == "DC")
    dc_rows = [row for row in triage["rows"] if row["jurisdiction"] == "DC"]

    assert len(expectations["expectations"]) == 81
    assert len(dc_rows) == 52
    assert manifest["pr"] == 509
    assert manifest["ref"] == "refs/pull/509/head"
    assert all(row["source_pr"] == "#509" for row in dc_rows)
    assert {row["source_blob_sha"] for row in dc_rows} == {manifest["blob_sha"]}
    assert next(row for row in dc_rows if row["expectation_id"] == "8.EE.A.3")["source_url"] == OFFICIAL_PDF
    assert "8.EE.A.3" in manifest["scope_note"]
