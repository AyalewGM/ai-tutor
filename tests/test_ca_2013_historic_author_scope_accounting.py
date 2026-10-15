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


def test_math1_bracket_evidence_remains_review_only():
    audit = json.loads((BASE / "ca_2013_mathematics1_pages90_94_author_audit.v1.json").read_text())
    expected = {"A-CED.1": 90, "A-REI.3": 91, "A-REI.11": 91, "F-IF.7.a": 92, "F-IF.7.e": 92, "F-BF.3": 92, "F-LE.5": 93, "S-ID.6.a": 94}
    assert len(audit["rows"]) == 59
    assert audit["bounded_author_course_bracket_evidence"]["record_count"] == 8
    for row in audit["rows"]:
        if row["expectation_id"] in expected:
            evidence = row["source_bracket_author_evidence"]
            assert evidence["source_printed_page"] == expected[row["expectation_id"]]
            assert evidence["source_pdf_zero_based_page_index"] == expected[row["expectation_id"]] + 6
            assert evidence["material_conditions"]
            assert evidence["independent_resolution"] == "PENDING"
            assert evidence["curriculum_activation"] == "FORBIDDEN"
            assert row["publisher_wording_verification"] == "REQUIRES_INDEPENDENT_LINE_BY_LINE_CHECK"
