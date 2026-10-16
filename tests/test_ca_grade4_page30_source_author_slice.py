"""California Grade 4 page-30 author evidence remains pending independent fidelity."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_ca_grade4_p30_source_and_domain_bounds():
    d = json.loads((ROOT / "ca_2013_grade4_page30_source_author_slice.v1.json").read_text())
    ids = [r["expectation_id"] for r in d["rows"]]
    assert ids == [f"4.OA.{i}" for i in range(1, 6)] + [f"4.NBT.{i}" for i in range(1, 7)]
    assert len(ids) == len(set(ids)) == d["rows_count"] == 11
    assert d["source_printed_page"] == 30
    assert d["source_pdf_zero_based_index"] == 36
    assert "less than or equal to 1,000,000" in d["domain_footnote"]
    rows = {r["expectation_id"]: r for r in d["rows"]}
    assert "contextual remainders" in rows["4.OA.3"]["required_material_conditions"]
    assert "1 through 100" in rows["4.OA.4"]["required_material_conditions"]
    assert "standard algorithm" in rows["4.NBT.4"]["required_material_conditions"]
    assert "four-digit by one-digit" in rows["4.NBT.5"]["required_material_conditions"]
    assert "remainders" in rows["4.NBT.6"]["required_material_conditions"]
    assert d["not_full_grade4"] is True
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
    assert all(d[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
