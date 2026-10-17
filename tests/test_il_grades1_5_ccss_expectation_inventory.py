import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "il_grades1_5_ccss.expectations.v1.json"
)

EXPECTED_COUNTS = {1: 21, 2: 26, 3: 25, 4: 28, 5: 26}
VALID_DOMAINS = {"OA", "NBT", "NF", "MD", "G"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_identifier_set_matches_official_counts() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    ids = [r["expectation_id"] for r in rows]
    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(ids) == 126 and len(set(ids)) == 126
    for grade, count in EXPECTED_COUNTS.items():
        got = [i for i in ids if i.startswith(f"{grade}.")]
        assert len(got) == count, f"grade {grade}: expected {count}, got {len(got)}"


def test_ccss_identifier_shape_and_clusters() -> None:
    for row in _manifest()["expectations"]:
        assert re.fullmatch(r"\d\.(OA|NBT|NF|MD|G)\.[A-Z]\.\d+", row["expectation_id"])
        assert row["domain"] in VALID_DOMAINS
        assert row["cluster"] and len(row["cluster"]) == 1
        if row["domain"] == "NF":
            assert row["grade"] >= 3


def test_illinois_jurisdiction_and_provenance() -> None:
    m = _manifest()
    assert m["jurisdiction"]["state"] == "Illinois"
    assert m["jurisdiction"]["authority_code"] == "ISBE"
    assert m["provenance"]["authoritative_source_url"] == (
        "https://www.isbe.net/Documents/Math_common_core_standards.pdf"
    )


def test_every_row_has_source_locator_and_capture() -> None:
    for row in _manifest()["expectations"]:
        assert row["source_locator"].startswith("https://www.thecorestandards.org/Math/")
        assert row["official_text_capture_status"].startswith("AUTHORITATIVE")
        assert len(row["scope_summary"]) >= 30


def test_zero_coverage_fail_closed() -> None:
    m = _manifest()
    for row in m["expectations"]:
        assert row["repository_existing_crosswalks"] == []
        assert row["proposed_mapping_status"] == "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
        assert row["classification"]["verified_mastery_evidence"] == \
            "NO_AND_MUST_NOT_BE_INFERRED"
        assert "provisional_relations" not in row
    assert m["safety"]["activation"] == "FORBIDDEN"


def test_reconciliation_counts_reconcile() -> None:
    m = _manifest()
    rows = m["expectations"]
    linked = sum(1 for r in rows if r["repository_existing_crosswalks"])
    assert linked == 0
    assert m["reconciliation"]["official_expectation_count"] == len(rows)
    assert m["reconciliation"]["expectations_with_provisional_links"] == 0
    assert m["reconciliation"]["unmapped_expectations"] == len(rows)
