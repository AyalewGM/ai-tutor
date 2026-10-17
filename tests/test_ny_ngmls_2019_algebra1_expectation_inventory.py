import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs" / "curriculum" / "standards"
    / "ny_ngmls_2019_algebra1.expectations.v1.json"
)

VALID_DOMAINS = {"N.RN", "N.Q", "A.SSE", "A.APR", "A.CED", "A.REI",
                 "F.IF", "F.BF", "F.LE", "S.ID"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_exactly_43_algebra1_expectations() -> None:
    m = _manifest()
    assert m["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(m["expectations"]) == 43
    assert m["reconciliation"]["official_expectation_count"] == 43


def test_ai_identifier_shape() -> None:
    for row in _manifest()["expectations"]:
        assert re.fullmatch(r"AI-[A-Z]+\.[A-Z]+\.\d+[a-z]?", row["expectation_id"])
        assert row["domain"] in VALID_DOMAINS
        assert row["grade"] == "AI"


def test_all_appendix_a_domains_present() -> None:
    domains = {r["domain"] for r in _manifest()["expectations"]}
    assert domains == VALID_DOMAINS


def test_noncontiguous_numbering_and_shared_notes() -> None:
    rows = _manifest()["expectations"]
    apr = {r["expectation_id"] for r in rows if r["domain"] == "A.APR"}
    assert apr == {"AI-A.APR.1", "AI-A.APR.3"}
    shared = [r for r in rows if any("Shared standard" in n for n in r["notes"])]
    assert len(shared) >= 10
    # sub-lettered standards exist (e.g. AI-A.REI.7a)
    assert any(re.search(r"\d[a-z]$", r["expectation_id"]) for r in rows)


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
    assert m["reconciliation"]["unmapped_expectations"] == len(rows)
