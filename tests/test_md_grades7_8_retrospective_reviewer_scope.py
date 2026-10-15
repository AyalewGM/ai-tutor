"""Independent-review requested Maryland Grade 7/8 source conditions; author-only."""
import json
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
          / "md_grades6_8_2025.source_fidelity_locators.v1.json")


def test_2025_maryland_grade7_8_reviewer_requested_subparts_fail_closed():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = {r["expectation_id"]: r for r in data["records"]}
    expected = {
        "7.DS.A.1": "ab", "7.DS.A.2": "ab", "7.DS.B.3": "abc",
        "7.DS.C.5": "abc", "7.DS.C.6": "abc",
        "7.AT.C.8": "abc", "7.AT.C.9": "abc",
        "8.GR.A.2": "", "8.GR.A.3": "",
        "8.AT.C.8": "", "8.AT.D.11": "",
    }
    for parent, letters in expected.items():
        row = rows[parent]
        scope = row["retrospective_reviewer_requested_2025_scope"]
        keys = {f"{parent}.{letter}" for letter in letters} if letters else {"parent"}
        assert set(scope["requirements"]) == keys
        assert set(row["official_subpart_ids"]) == (keys if letters else set())
        assert scope["publisher_column"] == "2025 Standards Statement"
        assert scope["printed_page_start"] == row["printed_page_start"]
        assert scope["independent_source_fidelity"] == "PENDING"
        assert scope["activation"] == "FORBIDDEN"
        assert all(scope[k] == "UNVERIFIED" for k in
                   ("canonical_equivalence", "assessment", "mastery"))

    def requirement(parent, part):
        return rows[parent]["retrospective_reviewer_requested_2025_scope"]["requirements"][part]

    assert "selection method" in requirement("7.DS.A.1", "7.DS.A.1.a")
    assert "multiple random samples of the same size" in requirement("7.DS.A.2", "7.DS.A.2.b")
    assert "range, distribution shape and clustering" in requirement("7.DS.B.3", "7.DS.B.3.a")
    assert "simulation trials" in requirement("7.DS.C.5", "7.DS.C.5.b")
    assert "bar graphs and circle graphs" in requirement("7.DS.C.5", "7.DS.C.5.c")
    assert "equally likely" in requirement("7.DS.C.6", "7.DS.C.6.a")
    assert "discrepancies" in requirement("7.DS.C.6", "7.DS.C.6.c")
    assert "px+q=r and p(x+q)=r" in requirement("7.AT.C.8", "7.AT.C.8.a")
    assert "original equality" in requirement("7.AT.C.8", "7.AT.C.8.b")
    assert "strict px+q>r or px+q<r" in requirement("7.AT.C.9", "7.AT.C.9.a")
    assert "entire solution set" in requirement("7.AT.C.9", "7.AT.C.9.b")
    assert "reasonable solution values" in requirement("7.AT.C.9", "7.AT.C.9.c")
    assert "ruler, protractor, technology or physical manipulatives" in requirement("8.GR.A.2", "parent")
    assert "two remote interior angles" in requirement("8.GR.A.3", "parent")
    assert "proportional reasoning" in requirement("8.AT.C.8", "parent")
    assert "increasing/decreasing and linear/nonlinear" in requirement("8.AT.D.11", "parent")
