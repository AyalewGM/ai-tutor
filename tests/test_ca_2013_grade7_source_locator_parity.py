"""Author-side California Grade 7 source parity; does not grant source acceptance."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
QUEUE = BASE / "ca_2013_grade7_24_source_review_queue.v1.json"
SCOPES = BASE / "ca_2013_grade7_24_source_author_slice.v1.json"


def test_grade7_queue_scope_locator_parity():
    q, s = (json.loads(p.read_text(encoding="utf-8")) for p in (QUEUE, SCOPES))
    queue = {r["expectation_id"]: r for r in q["rows"]}
    scopes = {r["expectation_id"]: r for r in s["rows"]}
    assert len(queue) == len(scopes) == 24
    assert queue.keys() == scopes.keys()
    for code, row in queue.items():
        assert row["source_printed_page"] == scopes[code]["source_printed_page"], code
        assert row["lettered_subparts"] == scopes[code]["required_lettered_subparts"], code
        assert row.get("source_printed_pages", [row["source_printed_page"]]) == scopes[code]["source_printed_page_span"], code
    assert q["independent_source_fidelity"] == s["independent_source_fidelity"] == "PENDING"
    assert q["activation"] == s["activation"] == "FORBIDDEN"


def test_cde_grade7_statistic_page_boundaries_and_geometry_derivation():
    q, s = (json.loads(p.read_text(encoding="utf-8")) for p in (QUEUE, SCOPES))
    pages = {r["expectation_id"]: r["source_printed_page"] for r in q["rows"]}
    assert {f"7.SP.{i}": pages[f"7.SP.{i}"] for i in range(1, 9)} == {
        **{f"7.SP.{i}": 50 for i in range(1, 7)},
        **{f"7.SP.{i}": 51 for i in range(7, 9)},
    }
    g4 = next(r for r in s["rows"] if r["expectation_id"] == "7.G.4")
    assert g4["source_printed_page"] == 50
    assert "informal derivation" in g4["author_mathematical_scope_summary"]
    assert "informal derivation" in g4["test_material_conditions"]
    assert s["canonical_equivalence"] == "UNVERIFIED"
    assert s["assessment"] == s["mastery"] == "UNVERIFIED"
