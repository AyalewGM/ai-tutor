import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "il_grades6_8_ccss.expectations.v1.json"
)

EXPECTED_COUNTS = {6: 29, 7: 24, 8: 28}
VALID_DOMAINS = {"RP", "NS", "EE", "G", "SP", "F"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_identifier_set_matches_official_counts() -> None:
    manifest = _manifest()
    ids = [r["expectation_id"] for r in manifest["expectations"]]
    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(ids) == 81 and len(set(ids)) == 81
    for grade, count in EXPECTED_COUNTS.items():
        got = [i for i in ids if i.startswith(f"{grade}.")]
        assert len(got) == count, f"grade {grade}: expected {count}, got {len(got)}"


def test_ccss_identifier_shape() -> None:
    for row in _manifest()["expectations"]:
        assert re.fullmatch(r"\d\.(RP|NS|EE|G|SP|F)\.[A-Z]\.\d+", row["expectation_id"])
        assert row["domain"] in VALID_DOMAINS
        # F (Functions) is grade 8 only; RP is grades 6-7 only
        if row["domain"] == "F":
            assert row["grade"] == 8
        if row["domain"] == "RP":
            assert row["grade"] in (6, 7)


def test_illinois_jurisdiction_and_provenance() -> None:
    m = _manifest()
    assert m["jurisdiction"]["state"] == "Illinois"
    assert m["jurisdiction"]["authority_code"] == "ISBE"
    assert m["provenance"]["authoritative_source_url"] == (
        "https://www.isbe.net/Documents/Math_common_core_standards.pdf"
    )


def test_every_row_has_source_locator_and_capture() -> None:
    for row in _manifest()["expectations"]:
        assert row["source_locator"]
        assert row["official_text_capture_status"].startswith("AUTHORITATIVE")
        assert len(row["scope_summary"]) >= 30


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
