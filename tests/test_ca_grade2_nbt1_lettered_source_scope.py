"""Source author guard for California 2.NBT.1.a/b (not publisher approval)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade2_nbt1_lettered_source_scope_and_fail_closed():
    source = json.loads((ROOT / "ca_2013_grade2_page20_source_author_slice.v1.json").read_text())
    row = next(r for r in source["rows"] if r["expectation_id"] == "2.NBT.1")
    assert row["required_lettered_subparts"] == ["a", "b"]
    assert (row["source_printed_page"], row["source_pdf_zero_based_page_index"]) == (20, 26)
    assert row["required_material_conditions"] == ["three-digit", "ten tens", "100–900"]
    scope = row["required_lettered_subpart_scope"]
    assert set(scope) == {"a", "b"}
    assert "bundle of ten tens" in scope["a"]
    assert "one through nine hundreds" in scope["b"]
    assert "zero tens and zero ones" in scope["b"]
    assert source["independent_source_fidelity"] == "PENDING"
    assert source["activation"] == "FORBIDDEN"
    assert row["canonical_equivalence"] == "UNVERIFIED"
    assert row["assessment"] == "UNVERIFIED"
    assert row["mastery"] == "UNVERIFIED"
