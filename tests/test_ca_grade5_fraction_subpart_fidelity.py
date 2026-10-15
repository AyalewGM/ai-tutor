"""Grade 5 fraction subpart source-fidelity regression; author evidence only."""
import json
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
          / "ca_2013_grade5_pages37_39_source_author_slice.v1.json")


def test_fraction_area_and_division_source_subparts_fail_closed():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = {r["expectation_id"]: r for r in data["rows"]}
    area = rows["5.NF.4"]["required_material_conditions"]
    assert any("unit-fraction side lengths" in x for x in area)
    assert any("tiled area equals length-product area" in x for x in area)
    assert any("fractional products represented by rectangular areas" in x for x in area)
    division = rows["5.NF.7"]["required_material_conditions"]
    assert any(x.startswith("5.NF.7.a:") and "nonzero whole number" in x
               and "visual model" in x for x in division)
    assert any(x.startswith("5.NF.7.b:") and "whole number divided by unit fraction" in x
               for x in division)
    assert any(x.startswith("5.NF.7.c:") and "both forms" in x for x in division)
    assert any("general fraction divided by fraction not required" in x for x in division)
    assert data["independent_source_fidelity"] == "PENDING"
    assert data["activation"] == "FORBIDDEN"
    assert all(data[x] == "UNVERIFIED" for x in
               ("canonical_equivalence", "assessment", "mastery"))
