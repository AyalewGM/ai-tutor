"""Fail-closed regression for the DC Grade 8 integer-exponents slice.

Locks the official source, complete 8.EE.A.1 qualifier boundary, exhaustive
repository-candidate inventory, and inactive/no-credit relation semantics.
"""

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
EXPECTATIONS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.expectations.v1.json"
LOCATORS = ROOT / "docs/curriculum/standards/dc_grades6_8_ccss.source_fidelity_locators.v1.json"
TRIAGE = ROOT / "docs/curriculum/coverage/dmv_grades7_8_expectation_depth_triage.v1.json"
ADVANCED_NUMBER = ROOT / "app/domains/advanced_number.py"
FRACTION_DECIMAL_DEPTH = ROOT / "app/domains/fraction_decimal_depth.py"
PLACE_VALUE = ROOT / "app/domains/place_value.py"

OFFICIAL_PDF = (
    "https://corestandards.org/wp-content/uploads/2023/09/"
    "ADA-Compliant-Math-Standards.pdf"
)
EXPECTED_CANDIDATES = {
    "MATH.EXP.EVALUATE",
    "MATH.EXP.PRODUCT",
    "MATH.EXP.QUOTIENT",
    "MATH.EXP.POWER",
    "MATH.SCI.CONVERT",
    "MATH.SCI.MULTIPLY",
    "MATH.DEC.POWER10",
    "MATH.PV.POWERS_TEN",
    "MATH.PV.REASON.TEN_TIMES",
}


def _row(path: Path, collection: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return next(
        row
        for row in payload[collection]
        if row.get("expectation_id") == "8.EE.A.1"
        and row.get("jurisdiction", "DC") == "DC"
    )


def test_dc_8_ee_a_1_official_source_and_complete_unlettered_scope() -> None:
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
    assert all(term in scope for term in (
        "exponent properties",
        "integer exponents",
        "zero",
        "negative",
        "equivalent",
    ))
    bounded = locator["bounded_mathematical_scope_evidence"]
    assert bounded["unlettered_standard"] is True
    assert bounded["source_printed_page"] == 54
    assert bounded["short_summary_is_exhaustive"] is False
    assert bounded["canonical_equivalence"] == "NOT_ESTABLISHED"
    assert bounded["downstream_full_coverage_allowed"] is False
    conditions = " ".join(bounded["required_conditions"]).lower()
    assert all(term in conditions for term in (
        "know exponent properties",
        "integer exponents",
        "zero",
        "negative",
        "equivalent",
    ))


def test_dc_8_ee_a_1_inventories_all_candidates_without_union_credit() -> None:
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
    assert all(status[c] == "NO_COVERAGE_CLAIM" for c in (
        "MATH.EXP.EVALUATE",
        "MATH.SCI.CONVERT",
        "MATH.DEC.POWER10",
        "MATH.PV.POWERS_TEN",
        "MATH.PV.REASON.TEN_TIMES",
    ))
    assert all(status[c] == "PARTIAL_NON_EXHAUSTIVE" for c in (
        "MATH.EXP.PRODUCT",
        "MATH.EXP.QUOTIENT",
        "MATH.EXP.POWER",
        "MATH.SCI.MULTIPLY",
    ))
    assert expectation["mapping_evidence_boundary"]["missing_mathematical_content_inferred"] is False


def test_dc_8_ee_a_1_positive_only_families_do_not_claim_integer_exponent_scope() -> None:
    locator = _row(LOCATORS, "records")
    relations = {r["candidate"]: r for r in locator["canonical_candidate_inventory"]}
    advanced_number = ADVANCED_NUMBER.read_text(encoding="utf-8")
    fraction_decimal = FRACTION_DECIMAL_DEPTH.read_text(encoding="utf-8")
    place_value = PLACE_VALUE.read_text(encoding="utf-8")

    assert all(
        f'"{candidate}"' in advanced_number
        for candidate in (
            "MATH.EXP.EVALUATE",
            "MATH.EXP.PRODUCT",
            "MATH.EXP.QUOTIENT",
            "MATH.EXP.POWER",
            "MATH.SCI.CONVERT",
            "MATH.SCI.MULTIPLY",
        )
    )
    assert '"MATH.DEC.POWER10"' in fraction_decimal
    assert all(
        f'"{candidate}"' in place_value
        for candidate in ("MATH.PV.POWERS_TEN", "MATH.PV.REASON.TEN_TIMES")
    )
    for candidate in (
        "MATH.EXP.PRODUCT",
        "MATH.EXP.QUOTIENT",
        "MATH.EXP.POWER",
        "MATH.SCI.MULTIPLY",
    ):
        relation = relations[candidate]
        included = " ".join(relation["included_scope"]).lower()
        excluded = " ".join(relation["excluded_required_scope"]).lower()
        assert "positive" in included
        assert "zero" in excluded
        assert "negative" in excluded

    evaluate = relations["MATH.EXP.EVALUATE"]
    assert evaluate["status"] == "NO_COVERAGE_CLAIM"
    assert "repeated multiplication" in " ".join(evaluate["included_scope"]).lower()
    assert "equivalent numerical expression" in " ".join(
        evaluate["excluded_required_scope"]
    ).lower()

    for candidate in (
        "MATH.DEC.POWER10",
        "MATH.PV.POWERS_TEN",
        "MATH.PV.REASON.TEN_TIMES",
    ):
        relation = relations[candidate]
        assert relation["status"] == "NO_COVERAGE_CLAIM"
        assert relation["evidence_role"] == "PREREQUISITE_ONLY"
        excluded = " ".join(relation["excluded_required_scope"]).lower()
        assert "exponent property" in excluded
        assert "zero" in excluded
        assert "negative" in excluded


def test_dc_8_ee_a_1_manifest_pin_and_pr_provenance_are_total() -> None:
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    triage = json.loads(TRIAGE.read_text(encoding="utf-8"))
    manifest = next(m for m in triage["source_manifests"] if m["jurisdiction"] == "DC")
    dc_rows = [row for row in triage["rows"] if row["jurisdiction"] == "DC"]

    assert len(expectations["expectations"]) == 81
    assert len(dc_rows) == 52
    repository_existing = {
        row["expectation_id"]
        for row in expectations["expectations"]
        if row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
    }
    assert repository_existing == {
        "8.NS.A.1", "8.NS.A.2", "8.EE.A.1", "8.SP.A.3",
        *{
            row["expectation_id"]
            for row in expectations["expectations"]
            if row["grade"] in (6, 7)
            and row["proposed_mapping_status"] == "REPOSITORY_EXISTING_UNVERIFIED"
        },
    }
    assert manifest["pr"] == 510
    assert manifest["ref"] == "refs/pull/510/head"
    assert manifest["blob_sha"] == "656b0bb971469429d48677f98d5c00a47ecfc4bc"
    assert all(row["source_pr"] == "#510" for row in dc_rows)
    assert {row["source_blob_sha"] for row in dc_rows} == {manifest["blob_sha"]}
    assert next(
        row for row in dc_rows if row["expectation_id"] == "8.EE.A.1"
    )["source_url"] == OFFICIAL_PDF
    assert "8.NS.A.1" in manifest["scope_note"]
    assert "8.EE.A.1" in manifest["scope_note"]
