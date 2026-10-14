import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs" / "curriculum" / "standards"
    / "va_algebra1_2023.expectations.v1.json"
)

EXPECTED_IDS = {
    "A.EO.1", "A.EO.2", "A.EO.3", "A.EO.4",
    "A.EI.1", "A.EI.2", "A.EI.3",
    "A.F.1", "A.F.2", "A.ST.1",
}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_identifier_set_is_exactly_the_ten_official() -> None:
    manifest = _manifest()
    ids = {r["expectation_id"] for r in manifest["expectations"]}
    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert ids == EXPECTED_IDS


def test_every_row_has_source_and_capture() -> None:
    for row in _manifest()["expectations"]:
        assert row["source_locator"].startswith(
            "https://www.doe.virginia.gov/home/showpublisheddocument/")
        assert row["official_text_capture_status"].startswith("AUTHORITATIVE")
        assert row["scope_summary"].startswith("The student will")


def test_fail_closed_classification() -> None:
    m = _manifest()
    for row in m["expectations"]:
        assert row["classification"]["verified_mastery_evidence"] == \
            "NO_AND_MUST_NOT_BE_INFERRED"
        assert row["proposed_mapping_status"] in {
            "REPOSITORY_EXISTING_UNVERIFIED", "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"}
    assert m["safety"]["activation"] == "FORBIDDEN"


def test_reconciliation_counts_reconcile() -> None:
    m = _manifest()
    rows = m["expectations"]
    linked = sum(1 for r in rows if r["repository_existing_crosswalks"])
    assert m["reconciliation"]["official_expectation_count"] == 10
    assert m["reconciliation"]["expectations_with_provisional_links"] == linked
    assert m["reconciliation"]["unmapped_expectations"] == 10 - linked


def test_unmapped_are_nonlinear_strands() -> None:
    unmapped = {r["expectation_id"] for r in _manifest()["expectations"]
                if r["proposed_mapping_status"] == "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"}
    assert unmapped == {"A.EO.2", "A.EO.3", "A.EO.4", "A.EI.2", "A.EI.3", "A.F.2", "A.ST.1"}
