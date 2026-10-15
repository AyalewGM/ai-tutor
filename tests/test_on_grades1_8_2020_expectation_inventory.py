import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs" / "curriculum" / "standards"
    / "on_grades1_8_2020.expectations.v1.json"
)


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_expectation_count_and_grade_band() -> None:
    m = _manifest()
    rows = m["expectations"]
    assert m["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert len(rows) == m["reconciliation"]["official_expectation_count"]
    assert {r["grade"] for r in rows} == set(range(1, 9))
    assert all(r["grade"] in range(1, 9) for r in rows)


def test_identifier_format_and_strands() -> None:
    for row in _manifest()["expectations"]:
        g, code = row["expectation_id"].split(".", 1)
        assert int(g) == row["grade"]
        assert re.fullmatch(r"[A-F]\d\.\d+", code)
        assert row["strand"] in set("ABCDEF")
        assert row["strand_title"]
        assert row["overall_expectation"].startswith(row["strand"])
        assert row["scope_summary"]


def test_all_content_strands_present_per_grade() -> None:
    # Strand A (SEL / Mathematical Processes) has no numbered specific
    # expectations by design — its skills embed across strands B-F.
    per_grade = {}
    for r in _manifest()["expectations"]:
        per_grade.setdefault(r["grade"], set()).add(r["strand"])
    for g, strands in per_grade.items():
        assert strands == set("BCDEF"), f"grade {g} missing {set('BCDEF')-strands}"


def test_fail_closed_classification() -> None:
    m = _manifest()
    for row in m["expectations"]:
        assert row["classification"]["verified_mastery_evidence"] == \
            "NO_AND_MUST_NOT_BE_INFERRED"
        assert row["proposed_mapping_status"] == "NO_REPOSITORY_SPECIFIC_MAPPING_FOUND"
        assert row["repository_existing_crosswalks"] == []
    assert m["safety"]["activation"] == "FORBIDDEN"


def test_reconciliation_counts_reconcile() -> None:
    m = _manifest()
    assert m["reconciliation"]["expectations_with_provisional_links"] == 0
    assert m["reconciliation"]["unmapped_expectations"] == len(m["expectations"])
