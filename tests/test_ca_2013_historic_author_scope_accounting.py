import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
LEDGER = BASE / "ca_2013_g7_g8_algebra1_math1_author_scope_accounting.v1.json"
HISTORY = BASE / "national_ca_grades7_9.author_intake.v1.json"


def test_ca_173_placements_are_127_unique_source_ids():
    d = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = json.loads(HISTORY.read_text(encoding="utf-8"))["expectations"]
    assert len(rows) == d["total_historical_placements"] == 173
    assert len({(r["track"], r["expectation_id"]) for r in rows}) == 173
    assert len({r["expectation_id"] for r in rows}) == 127
    assert d["cross_track_repeated_placements"] == 46
    for track, files in d["author_scope_files_by_track"].items():
        author_ids = [
            row["expectation_id"]
            for filename in files
            for row in json.loads((BASE / filename).read_text(encoding="utf-8"))["rows"]
        ]
        historic_ids = [r["expectation_id"] for r in rows if r["track"] == track]
        assert author_ids == historic_ids


def test_ca_historic_accounting_is_not_acceptance():
    d = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert d["rows_independently_accepted"] == 0
    assert d["publisher_source_fidelity"] == "PENDING_INDEPENDENT_REVIEW"
    assert d["activation"] == "FORBIDDEN"
    assert d["grade9_course_equivalence"] == "NOT_ASSUMED"
    assert all(d[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
