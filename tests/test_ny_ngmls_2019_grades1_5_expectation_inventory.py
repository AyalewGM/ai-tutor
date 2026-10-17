import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "ny_ngmls_2019_grades1_5.expectations.v1.json"
)

EXPECTED_COUNTS = {1: 24, 2: 31, 3: 30, 4: 31, 5: 26}
VALID_DOMAINS = {"OA", "NBT", "NF", "MD", "G"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_identifier_set_matches_extracted_counts() -> None:
    manifest = _manifest()
    ids = [r["expectation_id"] for r in manifest["expectations"]]
    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(ids) == 142 and len(set(ids)) == 142
    for grade, count in EXPECTED_COUNTS.items():
        got = [i for i in ids if i.startswith(f"NY-{grade}.")]
        assert len(got) == count, f"grade {grade}: expected {count}, got {len(got)}"


def test_ny_identifier_shape() -> None:
    for row in _manifest()["expectations"]:
        assert re.fullmatch(r"NY-\d\.(OA|NBT|NF|MD|G)\.\d+[a-z]?", row["expectation_id"])
        assert row["domain"] in VALID_DOMAINS
        if row["domain"] == "NF":
            assert row["grade"] >= 3


def test_new_york_jurisdiction_and_provenance() -> None:
    m = _manifest()
    assert m["jurisdiction"]["state"] == "New York"
    assert m["jurisdiction"]["authority_code"] == "NYSED"
    assert m["provenance"]["authoritative_source_url"] == (
        "https://www.nysed.gov/sites/default/files/programs/"
        "curriculum-instruction/nys-next-generation-mathematics-p-12-standards.pdf"
    )


def test_every_row_has_source_page_and_capture_status() -> None:
    for row in _manifest()["expectations"]:
        assert "#page=" in row["source_locator"]
        assert row["official_text_capture_status"] in {
            "AUTHORITATIVE_STATEMENT_EXTRACTED",
            "EXTRACTION_REVIEW_REQUIRED",
        }
        assert len(row["scope_summary"]) >= 10


def test_flagged_rows_carry_review_blocker() -> None:
    for row in _manifest()["expectations"]:
        if row["official_text_capture_status"] == "EXTRACTION_REVIEW_REQUIRED":
            assert "STATEMENT_EXTRACTION_REQUIRES_MANUAL_REVIEW" in row["blockers"]


def test_zero_coverage_fail_closed() -> None:
    m = _manifest()
    for row in m["expectations"]:
        assert row["repository_existing_crosswalks"] == []
        assert row["proposed_mapping_status"] == "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
        assert row["classification"]["verified_mastery_evidence"] == \
            "NO_AND_MUST_NOT_BE_INFERRED"
    assert m["safety"]["activation"] == "FORBIDDEN"


def test_reconciliation_counts_reconcile() -> None:
    m = _manifest()
    rows = m["expectations"]
    linked = sum(1 for r in rows if r["repository_existing_crosswalks"])
    assert linked == 0
    assert m["reconciliation"]["official_expectation_count"] == len(rows)
    assert m["reconciliation"]["unmapped_expectations"] == len(rows)
