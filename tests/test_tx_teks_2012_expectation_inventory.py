import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs" / "curriculum" / "standards"
    / "tx_teks_2012_grades1_9.expectations.v1.json"
)


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_expectation_count_and_band() -> None:
    m = _manifest()
    rows = m["expectations"]
    assert len(rows) == 463
    assert {r["grade"] for r in rows} == set(range(1, 10))
    assert len(rows) == m["reconciliation"]["official_expectation_count"]


def test_teks_identifier_format() -> None:
    for row in _manifest()["expectations"]:
        if row["grade"] <= 8:
            assert re.fullmatch(r"\d\.\d{1,2}[A-Z]{1,2}", row["expectation_id"])
            assert row["expectation_id"].startswith(f"{row['grade']}.")
        else:
            assert re.fullmatch(r"A1\.\d{1,2}[A-Z]{1,2}", row["expectation_id"])
            assert "111.39" in row["course"]
        assert len(row["scope_summary"]) >= 15
        assert row["strand_title"]
        assert row["source_locator"].startswith("https://tea.texas.gov/")


def test_process_standard_rows_marked() -> None:
    rows = _manifest()["expectations"]
    proc = [r for r in rows if r["is_process_standard"]]
    assert all(r["strand"] == "KS1" for r in proc)
    # KS1 A-G per grade 1-8 = 56 rows (A1's KS1 also A-G)
    assert len(proc) == 9 * 7


def test_fail_closed() -> None:
    m = _manifest()
    for row in m["expectations"]:
        assert row["classification"]["verified_mastery_evidence"] == \
            "NO_AND_MUST_NOT_BE_INFERRED"
        assert row["repository_existing_crosswalks"] == []
    assert m["safety"]["activation"] == "FORBIDDEN"
