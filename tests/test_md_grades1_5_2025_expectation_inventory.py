import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "md_grades1_5_2025.expectations.v1.json"
)

EXPECTED_COUNTS = {1: 24, 2: 24, 3: 26, 4: 30, 5: 27}
VALID_DOMAINS = {"NOS", "AT", "GR", "DS"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_identifier_set_matches_official_counts() -> None:
    manifest = _manifest()
    rows = manifest["expectations"]
    ids = [r["expectation_id"] for r in rows]
    assert manifest["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(ids) == 131 and len(set(ids)) == 131
    for grade, count in EXPECTED_COUNTS.items():
        got = [i for i in ids if i.startswith(f"{grade}.")]
        assert len(got) == count, f"grade {grade}: expected {count}, got {len(got)}"


def test_only_new_scheme_identifiers() -> None:
    # Legacy CCSS codes (OA/NBT/NF/MD/G) must never appear as expectation ids.
    import re
    for row in _manifest()["expectations"]:
        assert re.fullmatch(r"\d\.(NOS|AT|GR|DS)\.[A-Z]\.\d+", row["expectation_id"])
        assert row["domain"] in VALID_DOMAINS


def test_every_row_has_source_locator_and_capture() -> None:
    for row in _manifest()["expectations"]:
        assert row["source_locator"].startswith("https://msde.maryland.gov/media/")
        assert row["official_text_capture_status"].startswith("AUTHORITATIVE")
        assert len(row["scope_summary"]) >= 20


def test_provisional_links_carry_crosswalk_evidence() -> None:
    for row in _manifest()["expectations"]:
        if row["repository_existing_crosswalks"]:
            ev = row["crosswalk_evidence"]
            assert ev["pack_standard_ref"], row["expectation_id"]
            assert row["provisional_relations"]


def test_fail_closed_classification_on_every_row() -> None:
    m = _manifest()
    for row in m["expectations"]:
        c = row["classification"]
        assert c["verified_mastery_evidence"] == "NO_AND_MUST_NOT_BE_INFERRED"
        assert row["proposed_mapping_status"] in {
            "REPOSITORY_EXISTING_UNVERIFIED", "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"}
    assert m["safety"]["activation"] == "FORBIDDEN"
    assert m["safety"]["new_canonical_ids_created"] is False


def test_reconciliation_counts_reconcile() -> None:
    m = _manifest()
    rows = m["expectations"]
    linked = sum(1 for r in rows if r["repository_existing_crosswalks"])
    assert m["reconciliation"]["official_expectation_count"] == len(rows)
    assert m["reconciliation"]["expectations_with_provisional_links"] == linked
    assert m["reconciliation"]["unmapped_expectations"] == len(rows) - linked
