"""Bounded traditional Maryland Algebra I source-scope safety checks."""
import json
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
          / "md_algebra1_traditional_2026_27.source_fidelity_locators.v1.json")


def test_traditional_algebra1_material_bounds_fail_closed():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = {r["expectation_id"]: r for r in data["records"]}
    rational = rows["N.RN.B.3"]["material_scope_conditions"]
    assert len(rational) == 3
    assert "NONZERO rational" in rational[2]
    quadratic = rows["A.REI.B.4"]["material_scope_conditions"]
    assert any("complex solutions" in s and "real a and b" in s for s in quadratic)
    inequality = rows["A.REI.D.12"]["material_scope_conditions"]
    assert any("boundary line is excluded" in s for s in inequality)
    assert any("intersection" in s for s in inequality)
    for code in ("N.RN.B.3", "A.REI.B.4", "A.REI.D.12"):
        assert rows[code]["independent_acceptance"] == "PENDING"
        assert rows[code]["material_scope_review_status"].endswith("INDEPENDENT_PUBLISHER_REVIEW")
