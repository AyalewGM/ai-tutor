"""Texas 2025 advanced 111.30(c)(14)(B) author-source regression."""

import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/national_tx_grades7_9.author_intake.v1.json"


def test_advanced_grade7_family_budget_local_city_constraint():
    d = json.loads(SOURCE.read_text(encoding="utf-8"))
    evidence = d["advanced_2025_final_adoption_evidence"]
    rows = [r for r in evidence["verified_final_rule_scope_slice"]["rows"]
            if r["expectation_id"] == "111.30(c)(14)(B)"]
    rows += [r for r in evidence["advanced_course_expectation_identifier_inventory"]["expectations"]
             if r["expectation_id"] == "111.30(c)(14)(B)"]
    assert len(rows) == 2
    for r in rows:
        scope = r["editorial_mathematical_scope"]
        assert "family budget estimator" in scope
        assert "minimum household budget" in scope
        assert "average hourly wage" in scope
        assert "student's city or another nearby large city" in scope
        assert "PENDING_INDEPENDENT" in r["source_fidelity"]
        assert all(r[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
