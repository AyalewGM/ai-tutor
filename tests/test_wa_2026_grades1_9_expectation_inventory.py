import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs" / "curriculum" / "standards"
    / "wa_2026_grades1_9.expectations.v1.json"
)

DOMAINS = {"Quantity", "Relationships", "Data Analysis", "Spatial Reasoning"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_expectation_count_and_band() -> None:
    m = _manifest()
    rows = m["expectations"]
    assert len(rows) == m["reconciliation"]["official_expectation_count"]
    assert {r["grade"] for r in rows} == set(range(1, 10))
    assert len(rows) == 288


def test_codes_and_domains() -> None:
    for row in _manifest()["expectations"]:
        assert re.fullmatch(r"M\.(HS|\d+)\.[A-Z]+\.[A-Z]+\.\d+", row["expectation_id"])
        assert row["strand"] in DOMAINS
        assert row["scope_summary"]
        assert row["official_text_capture_status"].startswith(
            "AUTHOR_EXTRACTED_FROM_ADOPTION_WORKBOOK")


def test_verification_status_is_honest() -> None:
    for row in _manifest()["expectations"]:
        assert "SOURCE_VERIFICATION_PENDING" in row["blockers"]
        assert row["repository_existing_crosswalks"] == []
        assert row["classification"]["verified_mastery_evidence"] == \
            "NO_AND_MUST_NOT_BE_INFERRED"


def test_grade_nine_is_alg1_track() -> None:
    g9 = [r for r in _manifest()["expectations"] if r["grade"] == 9]
    assert len(g9) == 50
    assert all(r["course"] == "ALG 1" for r in g9)


def test_fail_closed_safety() -> None:
    m = _manifest()
    assert m["safety"]["activation"] == "FORBIDDEN"
    assert m["reconciliation"]["expectations_with_provisional_links"] == 0
