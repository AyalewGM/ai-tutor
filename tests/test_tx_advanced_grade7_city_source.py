"""Author-source contract regression for Texas advanced Grade 7."""

import json
from pathlib import Path


def test_texas_advanced_grade7_c14b_city_scope():
    path = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/national_tx_grades7_9.author_intake.v1.json"
    data = json.loads(path.read_text())
    evidence = data["advanced_2025_final_adoption_evidence"]
    inventory = evidence["advanced_course_expectation_identifier_inventory"]
    rows = evidence["verified_final_rule_scope_slice"]["rows"]
    target = "111.30(c)(14)(B)"
    scopes = [next(r for r in section if r["expectation_id"] == target)["editorial_mathematical_scope"]
              for section in (inventory["expectations"], rows)]
    assert scopes[0] == scopes[1]
    assert "student's city or another nearby large city" in scopes[0]
    assert inventory["complete_scope_rows_independently_accepted"] == 0
