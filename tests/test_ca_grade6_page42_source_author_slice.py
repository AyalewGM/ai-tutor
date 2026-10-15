"""Bounded California Grade 6 direct-source author scopes: independent review pending."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade6_page42_parent_ids_and_critical_constraints():
    data = json.loads((ROOT / "ca_2013_grade6_page42_source_author_slice.v1.json").read_text())
    rows = data["rows"]
    ids = [r["expectation_id"] for r in rows]
    assert ids == ["6.RP.1", "6.RP.2", "6.RP.3", "6.NS.1",
                   "6.NS.2", "6.NS.3", "6.NS.4"]
    assert len(ids) == len(set(ids)) == data["expectation_count"] == 7
    assert all(r["source_printed_page"] == 42 and
               r["source_pdf_zero_based_page_index"] == 48 for r in rows)
    by_id = {r["expectation_id"]: r for r in rows}
    assert "non-complex fractions" in data["source_footnote"]
    assert "denominator nonzero" in by_id["6.RP.2"]["required_material_conditions"]
    assert "required subparts a b c d" in by_id["6.RP.3"]["required_material_conditions"]
    assert "percent as rate per 100" in by_id["6.RP.3"]["required_material_conditions"]
    assert "fraction divided by fraction" in by_id["6.NS.1"]["required_material_conditions"]
    assert "all four decimal operations" in by_id["6.NS.3"]["required_material_conditions"]
    assert by_id["6.NS.4"]["required_material_conditions"] == [
        "GCF inputs <=100", "LCM inputs <=12",
        "distributive rewrite integers 1-100",
    ]
    assert data["independent_source_fidelity"] == "PENDING"
    assert data["activation"] == "FORBIDDEN"
    for row in rows:
        assert row["canonical_equivalence"] == "UNVERIFIED"
        assert row["assessment"] == "UNVERIFIED"
        assert row["mastery"] == "UNVERIFIED"
