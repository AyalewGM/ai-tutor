import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "va_grades1_5_2023.expectations.v1.json"
)

EXPECTED_COUNTS = {1: 9, 2: 11, 3: 12, 4: 18, 5: 14}
VALID_STRANDS = {"NS", "CE", "MG", "PS", "PFA"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_identifier_set_matches_official_counts() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    ids = [r["expectation_id"] for r in rows]
    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(ids) == 64 and len(set(ids)) == 64
    for grade, count in EXPECTED_COUNTS.items():
        got = [i for i in ids if i.startswith(f"{grade}.")]
        assert len(got) == count, f"grade {grade}: expected {count}, got {len(got)}"


def test_every_row_has_source_locator_and_official_capture() -> None:
    for row in _manifest()["expectations"]:
        assert row["source_locator"].startswith(
            "https://www.doe.virginia.gov/home/showpublisheddocument/")
        assert row["official_text_capture_status"].startswith(
            ("AUTHORITATIVE_STATEMENT_EXTRACTED", "EXTRACTED_VIA_ARCHIVED"))
        assert row["scope_summary"].startswith("The student will")
        assert row["strand"] in VALID_STRANDS


def test_fail_closed_classification_on_every_row() -> None:
    for row in _manifest()["expectations"]:
        c = row["classification"]
        assert c["verified_mastery_evidence"] == "NO_AND_MUST_NOT_BE_INFERRED"
        assert row["proposed_mapping_status"] in {
            "REPOSITORY_EXISTING_UNVERIFIED", "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"}


def test_unmapped_are_all_ps_or_pfa_strand() -> None:
    unmapped = [r for r in _manifest()["expectations"]
                if r["proposed_mapping_status"] == "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"]
    assert len(unmapped) == 13
    assert {r["strand"] for r in unmapped} == {"PS", "PFA"}


def test_reconciliation_counts_reconcile() -> None:
    m = _manifest()
    rows = m["expectations"]
    linked = sum(1 for r in rows if r["repository_existing_crosswalks"])
    assert m["reconciliation"]["official_expectation_count"] == len(rows)
    assert m["reconciliation"]["expectations_with_provisional_links"] == linked
    assert m["reconciliation"]["unmapped_expectations"] == len(rows) - linked
