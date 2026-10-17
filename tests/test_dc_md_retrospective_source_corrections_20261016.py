"""Retrospective DC/MD official-source correction bounds; no learner authorization."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def _rows(filename):
    doc = json.loads((ROOT / filename).read_text(encoding="utf-8"))
    return {row["expectation_id"]: row for row in doc["records"]}


def test_dc_three_source_scope_omissions_and_no_approval():
    rows = _rows("dc_grades6_8_ccss.source_fidelity_locators.v1.json")
    expected = {"8.G.A.1": {"8.G.A.1.a"}, "8.SP.A.1": {"parent"},
                "8.SP.A.2": {"parent"}}
    for code, keys in expected.items():
        row = rows[code]
        evidence = row["retrospective_source_fidelity_correction_20261016"]
        assert set(evidence["requirements"]) == keys
        assert keys - {"parent"} <= set(row["lettered_subpart_ids"])
        assert row["independent_acceptance"] == "PENDING"
        assert evidence["short_summary_exhaustive"] is False
        assert evidence["independent_source_fidelity"] == "PENDING"
        assert evidence["activation"] == "FORBIDDEN"
        assert all(evidence[k] == "UNVERIFIED" for k in
                   ("canonical_equivalence", "assessment", "mastery"))
    assert "same length" in rows["8.G.A.1"]["retrospective_source_fidelity_correction_20261016"]["requirements"]["8.G.A.1.a"]
    assert "clustering, outliers" in rows["8.SP.A.1"]["retrospective_source_fidelity_correction_20261016"]["requirements"]["parent"]
    assert "closely data points lie" in rows["8.SP.A.2"]["retrospective_source_fidelity_correction_20261016"]["requirements"]["parent"]


def test_maryland_grade8_bias_and_compound_event_language():
    rows = _rows("md_grades6_8_2025.source_fidelity_locators.v1.json")
    expected = {"8.DS.A.1": "8.DS.A.1.b", "8.DS.C.6": "8.DS.C.6.a"}
    for parent, subpart in expected.items():
        row = rows[parent]
        evidence = row["retrospective_source_fidelity_correction_20261016"]
        assert set(evidence["requirements"]) == {subpart}
        assert subpart in row["official_subpart_ids"]
        assert evidence["source_locator"]["printed_page_start"] == row["printed_page_start"]
        assert evidence["source_authority"].startswith("MSDE 2025 Standards Statement")
        assert row["independent_acceptance"] == "PENDING"
        assert evidence["independent_source_fidelity"] == "PENDING"
        assert evidence["activation"] == "FORBIDDEN"
    assert "limitations OR potential bias" in rows["8.DS.A.1"]["retrospective_source_fidelity_correction_20261016"]["requirements"]["8.DS.A.1.b"]
    assert "everyday-language" in rows["8.DS.C.6"]["retrospective_source_fidelity_correction_20261016"]["requirements"]["8.DS.C.6.a"]
    assert "sample space" in rows["8.DS.C.6"]["retrospective_source_fidelity_correction_20261016"]["requirements"]["8.DS.C.6.a"]
