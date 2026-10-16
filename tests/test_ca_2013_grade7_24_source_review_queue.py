import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/ca_2013_grade7_24_source_review_queue.v1.json"

def test_grade7_review_queue_identity_and_gates():
    d = json.loads(PATH.read_text(encoding="utf-8"))
    ids = [r["expectation_id"] for r in d["rows"]]
    assert len(ids) == len(set(ids)) == 24
    assert d["status"] == "AUTHOR_REVIEW_QUEUE_NOT_ACCEPTED"
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
    assert all(d[g] == "UNVERIFIED" for g in ("canonical_equivalence", "assessment", "mastery"))
    assert all(r["author_status"] == "PENDING_INDEPENDENT_SOURCE_FIDELITY" for r in d["rows"])
    assert all(48 <= r["source_printed_page"] <= 51 for r in d["rows"])

def test_grade7_lettered_review_requirements():
    d = json.loads(PATH.read_text(encoding="utf-8"))
    expected = {"7.RP.2": "abcd", "7.NS.1": "abcd", "7.NS.2": "abcd", "7.EE.4": "ab", "7.SP.7": "ab", "7.SP.8": "abc"}
    actual = {r["expectation_id"]: "".join(r["lettered_subparts"]) for r in d["rows"] if r["lettered_subparts"]}
    assert actual == expected

def test_grade7_subject_counts():
    d = json.loads(PATH.read_text(encoding="utf-8"))
    expected = {"7.RP": 3, "7.NS": 3, "7.EE": 4, "7.G": 6, "7.SP": 8}
    actual = {prefix: sum(r["expectation_id"].startswith(prefix + ".") for r in d["rows"]) for prefix in expected}
    assert actual == expected

def test_grade7_exact_source_page_corrections():
    d = json.loads(PATH.read_text(encoding="utf-8"))
    rows = {r["expectation_id"]: r for r in d["rows"]}
    assert rows["7.NS.2"]["source_printed_page"] == 48
    assert rows["7.NS.2"]["source_printed_pages"] == [48, 49]
    assert rows["7.NS.2"]["lettered_subparts"] == ["a", "b", "c", "d"]
    assert rows["7.G.1"]["source_printed_page"] == 49
    assert rows["7.G.2"]["source_printed_page"] == 50
