"""Fail-closed source-intake checks; not independent standards verification."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
FILES = {
    "CA": "national_ca_grades7_9.author_intake.v1.json",
    "TX": "national_tx_grades7_9.author_intake.v1.json",
    "WA": "national_wa_2026_grades7_9.source_blocker.v1.json",
}


def _data(key):
    return json.loads((ROOT / FILES[key]).read_text(encoding="utf-8"))


def test_historical_ca_tx_rows_are_source_pending_and_not_mastery_evidence():
    for key, count in (("CA", 173), ("TX", 88)):
        data = _data(key)
        assert data["status"] == "DRAFT_INCOMPLETE_SOURCE_FIDELITY"
        assert len(data["expectations"]) == count
        assert len({(r["track"], r["expectation_id"]) for r in data["expectations"]}) == count
        for row in data["expectations"]:
            assert row["source_fidelity"].startswith("AUTHOR_REUSE_FROM_HISTORIC_AUDIT_PENDING")
            assert row["exact_mathematical_scope"] is None
            assert row["canonical_equivalence"] == "UNVERIFIED"
            assert row["assessment"] == "UNVERIFIED"
            assert row["mastery"] == "UNVERIFIED"


def test_california_grade8_irrational_candidates_do_not_imply_coverage():
    data = _data("CA")
    rows = {r["expectation_id"]: r for r in data["expectations"] if r["track"] == "GRADE_8"}
    for code in ("8.NS.1", "8.NS.2"):
        assert rows[code]["candidate_canonical"] == "M8.NS.RAD"
        assert rows[code]["canonical_equivalence"] == "UNVERIFIED"


def test_texas_regular_and_advanced_are_not_conflated():
    data = _data("TX")
    assert {r["track"] for r in data["expectations"]} == {"REGULAR_GRADE_7", "REGULAR_GRADE_8"}
    assert {p["section"] for p in data["separate_courses"]} == {"111.39", "111.30", "111.31"}
    for row in data["expectations"]:
        assert row["exact_mathematical_scope"] is None


def test_wa_2026_missing_originals_fail_closed():
    data = _data("WA")
    assert data["status"] == "BLOCKED_AUTHORITATIVE_2026_DOCUMENT_BYTES_NOT_RETRIEVED"
    assert data["expectations"] == []
    assert data["required"] == "2027-2028"
    assert "2011" in data["crosswalk"]


def test_wa_high_school_tracks_are_separate_from_legacy_2011_crosswalk():
    data = _data("WA")
    tracks = data["high_school_arrangements"]
    assert tracks["not_grade9_equivalences"] is True
    assert set(tracks["tracks"]) == {
        "Integrated 1", "Integrated 2", "Integrated 3", "Geometry",
        "Algebra 1", "Algebra 2", "Credit 3",
    }
    acquisition = data["source_acquisition"]
    assert acquisition["initial_adoption_2025_role"].startswith("HISTORICAL_TRANSITION_RESEARCH_ONLY")
    assert acquisition["official_2026_spreadsheet"] == "UNRESOLVED_DIRECT_URL"
    assert acquisition["no_2011_2026_crosswalk_rows_invented"] is True
