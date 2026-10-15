import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs" / "curriculum" / "standards"
    / "ca_ccss_2013_grades1_9.expectations.v1.json"
)

EXPECTED_PER_GRADE = {1: 21, 2: 26, 3: 25, 4: 28, 5: 26, 6: 29, 7: 24, 8: 28, 9: 48}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_per_grade_counts_match_ccss() -> None:
    rows = _manifest()["expectations"]
    per = {}
    for r in rows:
        per[r["grade"]] = per.get(r["grade"], 0) + 1
    assert per == EXPECTED_PER_GRADE


def test_identifier_format() -> None:
    for row in _manifest()["expectations"]:
        if row["grade"] <= 8:
            assert re.fullmatch(
                r"\d\.(OA|NBT|NF|MD|G|RP|NS|EE|F|SP)\.[A-Z]\.\d+",
                row["expectation_id"])
        else:
            assert re.fullmatch(
                r"(N\.RN|N\.Q|A\.SSE|A\.APR|A\.CED|A\.REI|F\.IF|F\.BF|F\.LE|S\.ID)\.\d+",
                row["expectation_id"])
        assert row["scope_summary"]
        assert row["source_locator"].endswith("ccssmathstandardaug2013.pdf")


def test_grade9_is_algebra1_appendix_a_set() -> None:
    g9 = {r["expectation_id"] for r in _manifest()["expectations"] if r["grade"] == 9}
    assert "A.REI.4" in g9 and "A.REI.2" not in g9 and "S.ID.4" not in g9
    ced1 = [r for r in _manifest()["expectations"] if r["expectation_id"] == "A.CED.1"][0]
    assert "absolute" in ced1["ca_modification_note"].lower()


def test_fail_closed() -> None:
    m = _manifest()
    for row in m["expectations"]:
        assert row["classification"]["verified_mastery_evidence"] == \
            "NO_AND_MUST_NOT_BE_INFERRED"
        assert row["repository_existing_crosswalks"] == []
    assert m["safety"]["activation"] == "FORBIDDEN"
