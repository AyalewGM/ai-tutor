"""Fail-closed MSDE 2025 Integrated Algebra I subpart evidence."""
import json
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
          / "md_ia1_2025.source_fidelity_locators.v1.json")


def test_integrated_algebra1_material_subpart_requirements():
    d = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = {r["expectation_id"]: r for r in d["records"]}
    exp = rows["IA1.AT.B.2"]["material_subpart_requirements"]["IA1.AT.B.2.d"]
    assert "at most two steps" in exp and "common base" in exp
    absolute = rows["IA1.AT.B.3"]["material_subpart_requirements"]["IA1.AT.B.3.c"]
    assert "isolated on one side" in absolute
    assert "compound inequalities" in absolute and "number line" in absolute
    system = rows["IA1.AT.B.5"]["material_subpart_requirements"]
    assert set(system) == {"IA1.AT.B.5.b", "IA1.AT.B.5.c", "IA1.AT.B.5.d"}
    assert "substitution" in system["IA1.AT.B.5.b"]
    assert "linear combination" in system["IA1.AT.B.5.b"]
    assert "intersection" in system["IA1.AT.B.5.c"]
    assert "contexts" in system["IA1.AT.B.5.d"]
    for key in ("IA1.AT.B.2", "IA1.AT.B.3", "IA1.AT.B.5"):
        assert rows[key]["independent_acceptance"] == "PENDING"
        assert rows[key]["material_scope_review_status"].endswith("INDEPENDENT_PUBLISHER_REVIEW")
