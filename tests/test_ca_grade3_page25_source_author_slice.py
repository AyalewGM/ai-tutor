"""Author-side Grade 3 p25 identity and fail-closed tests; not an acceptance verdict."""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/ca_2013_grade3_page25_source_author_slice.v1.json"


def test_grade3_page25_exact_ids_and_source():
    d = json.loads(P.read_text(encoding="utf8"))
    assert [r["expectation_id"] for r in d["rows"]] == [f"3.OA.{i}" for i in range(1, 10)] + ["3.NBT.1"]
    assert len(d["rows"]) == d["expectation_count"] == 10
    for r in d["rows"]:
        assert (r["source_printed_page"], r["source_pdf_zero_based_page_index"]) == (25, 31)
        assert r["author_mathematical_scope"] and r["required_material_conditions"]


def test_grade3_p25_boundaries_fail_closed():
    d = json.loads(P.read_text(encoding="utf8"))
    rows = {r["expectation_id"]: " ".join(r["required_material_conditions"]) for r in d["rows"]}
    assert "group size" in rows["3.OA.2"] and "number of groups" in rows["3.OA.2"]
    assert all(v in rows["3.OA.5"] for v in ("commutative", "associative", "distributive"))
    assert "whole-number inputs and answers" in rows["3.OA.8"]
    assert "conventional order" in rows["3.OA.8"]
    assert "nearest 100" in rows["3.NBT.1"]
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
    assert all(d[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
