"""California Grade 3 final source-page author evidence; no acceptance inference."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade3_final_page_requirements_and_fail_closed():
    data = json.loads((ROOT / "ca_2013_grade3_page27_source_author_slice.v1.json").read_text())
    rows = {r["expectation_id"]: r for r in data["rows"]}
    assert list(rows) == [f"3.MD.{i}" for i in range(3, 9)] + ["3.G.1", "3.G.2"]
    assert len(rows) == data["expectation_count"] == 8
    assert all(r["source_printed_page"] == 27 and r["source_pdf_zero_based_page_index"] == 33 for r in rows.values())
    assert "one- and two-step comparison" in rows["3.MD.3"]["required_material_conditions"]
    assert "nearest halves and fourths of an inch" in rows["3.MD.4"]["required_material_conditions"]
    assert "no gaps or overlaps" in rows["3.MD.5"]["required_material_conditions"]
    assert "required subparts a b c d" in rows["3.MD.7"]["required_material_conditions"]
    assert "same perimeter/different areas" in rows["3.MD.8"]["required_material_conditions"]
    assert "quadrilateral hierarchy" in rows["3.G.1"]["required_material_conditions"]
    assert "unit fraction of whole" in rows["3.G.2"]["required_material_conditions"]
    assert data["independent_source_fidelity"] == "PENDING"
    assert data["activation"] == "FORBIDDEN"
    assert all(data[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))


def test_grade3_pages_cover_distinct_29_source_identifiers():
    ids = []
    for page in (25, 26, 27):
        data = json.loads((ROOT / f"ca_2013_grade3_page{page}_source_author_slice.v1.json").read_text())
        ids.extend(r["expectation_id"] for r in data["rows"])
    assert len(ids) == len(set(ids)) == 29
