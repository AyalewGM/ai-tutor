import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs" / "curriculum" / "standards"
    / "dc_algebra1_ccss.expectations.v1.json"
)


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_exactly_48_appendix_a_standards() -> None:
    m = _manifest()
    assert m["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(m["expectations"]) == 48
    assert m["reconciliation"]["official_expectation_count"] == 48


def test_domains_and_units_valid() -> None:
    valid_domains = {"N.RN", "N.Q", "A.SSE", "A.APR", "A.CED", "A.REI",
                     "F.IF", "F.BF", "F.LE", "S.ID"}
    for row in _manifest()["expectations"]:
        assert row["strand"] in valid_domains
        assert row["strand_title"]
        assert row["appendix_a_units"] and all(1 <= u <= 5 for u in row["appendix_a_units"])
        assert row["official_text_capture_status"] == "AUTHORITATIVE_STATEMENT_EXTRACTED"
        assert len(row["scope_summary"]) > 20


def test_expected_domain_coverage() -> None:
    domains = {r["strand"] for r in _manifest()["expectations"]}
    # every Appendix A Algebra I domain must be represented
    assert domains == {"N.RN", "N.Q", "A.SSE", "A.APR", "A.CED", "A.REI",
                       "F.IF", "F.BF", "F.LE", "S.ID"}
    assert "A.REI.4" in {r["expectation_id"] for r in _manifest()["expectations"]}
    # A.REI.2 (rational/radical equations) is Algebra II, not A1
    assert "A.REI.2" not in {r["expectation_id"] for r in _manifest()["expectations"]}


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
    linked = sum(1 for r in m["expectations"] if r["repository_existing_crosswalks"])
    assert m["reconciliation"]["expectations_with_provisional_links"] == linked
    assert m["reconciliation"]["unmapped_expectations"] == 48 - linked
