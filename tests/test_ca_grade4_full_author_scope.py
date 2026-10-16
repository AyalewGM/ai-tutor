"""Fail-closed California Grade 4 author source inventory across p30–33."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade4_all_28_source_parent_expectations_and_bounds():
    a = json.loads((ROOT / "ca_2013_grade4_page30_source_author_slice.v1.json").read_text())
    b = json.loads((ROOT / "ca_2013_grade4_pages31_33_source_author_slice.v1.json").read_text())
    rows = a["rows"] + b["rows"]
    ids = [r["expectation_id"] for r in rows]
    expected = ([f"4.OA.{i}" for i in range(1, 6)]
                + [f"4.NBT.{i}" for i in range(1, 7)]
                + [f"4.NF.{i}" for i in range(1, 8)]
                + [f"4.MD.{i}" for i in range(1, 8)]
                + [f"4.G.{i}" for i in range(1, 4)])
    assert ids == expected
    assert len(ids) == len(set(ids)) == 28
    assert all(r["source_pdf_zero_based_index"] == r["source_printed_page"] + 6 for r in rows)
    assert b["grade4_fraction_domain_denominators"] == [2, 3, 4, 5, 6, 8, 10, 12, 100]
    assert b["grade4_unlike_denominator_general_add_sub_required"] is False
    by_id = {r["expectation_id"]: r["author_mathematical_scope"] for r in rows}
    assert "a-d" in by_id["4.NF.3"]
    assert "a-c" in by_id["4.NF.4"]
    assert "same whole" in by_id["4.NF.7"]
    assert "California" in by_id["4.G.2"]
    assert "1/2, 1/4, 1/8" in by_id["4.MD.4"]
    assert b["independent_source_fidelity"] == "PENDING"
    assert b["activation"] == "FORBIDDEN"
    assert a["independent_source_fidelity"] == "PENDING"
    assert all(b[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
