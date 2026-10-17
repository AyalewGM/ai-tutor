import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs" / "curriculum" / "standards"
    / "il_algebra1_ccss.expectations.v1.json"
)

VALID_DOMAINS = {"N.RN", "N.Q", "A.SSE", "A.APR", "A.CED", "A.REI",
                 "F.IF", "F.BF", "F.LE", "S.ID"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_exactly_48_appendix_a_standards() -> None:
    m = _manifest()
    assert m["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(m["expectations"]) == 48
    assert m["reconciliation"]["official_expectation_count"] == 48


def test_domains_and_units_valid() -> None:
    for row in _manifest()["expectations"]:
        assert row["strand"] in VALID_DOMAINS
        assert row["strand_title"]
        assert row["appendix_a_units"] and all(1 <= u <= 5 for u in row["appendix_a_units"])
        assert row["official_text_capture_status"] == "AUTHORITATIVE_STATEMENT_EXTRACTED"
        assert len(row["scope_summary"]) > 20


def test_expected_domain_coverage() -> None:
    rows = _manifest()["expectations"]
    domains = {r["strand"] for r in rows}
    assert domains == VALID_DOMAINS
    ids = {r["expectation_id"] for r in rows}
    assert "A.REI.4" in ids
    # A.REI.2 (rational/radical equations) is Algebra II, not A1
    assert "A.REI.2" not in ids


def test_illinois_jurisdiction_and_provenance() -> None:
    m = _manifest()
    assert m["jurisdiction"]["state"] == "Illinois"
    assert m["jurisdiction"]["authority_code"] == "ISBE"
    assert m["provenance"]["authoritative_source_url"] == (
        "https://www.isbe.net/Documents/Math_common_core_standards.pdf"
    )


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
    assert m["reconciliation"]["expectations_with_provisional_links"] == 0
    assert m["reconciliation"]["unmapped_expectations"] == len(rows)
