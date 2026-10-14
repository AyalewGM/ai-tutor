"""Fail-closed author source-boundary checks for CA Grade 1."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_ca_grade1_bounded_scopes_preserve_mathematical_constraints():
    d = json.loads((ROOT / "ca_2013_grade1_bounded_scope_author_slice.v1.json").read_text())
    rows = {r["expectation_id"]: r for r in d["rows"]}
    assert len(rows) == 5
    assert all(r["pdf_page_index"] == r["printed_page"] + 6 for r in rows.values())
    assert "within 20" in rows["1.OA.1"]["scope"]
    assert "within 10" in rows["1.OA.6"]["scope"]
    assert rows["1.NBT.2"]["required_subparts"] == ["a", "b", "c"]
    assert "no gaps or overlaps" in rows["1.MD.2"]["scope"]
    assert "two and four equal shares" in rows["1.G.3"]["scope"]
    assert d["independent_source_fidelity"] == "PENDING"
    assert all(d[k] == "UNVERIFIED" for k in
               ("canonical_equivalence", "generator", "assessment", "mastery"))
    assert d["activation"] == "FORBIDDEN"
