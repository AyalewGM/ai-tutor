"""Retrospective MD source omissions from independent reviewer, not acceptance."""
import json
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
          / "md_grades6_8_2025.source_fidelity_locators.v1.json")


def test_md_geometry_number_system_and_systems_scope_is_non_exhaustive():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = {row["expectation_id"]: row for row in data["records"]}
    expected = {
        "7.GR.A.2": {"parent"},
        "8.GR.B.4": {"8.GR.B.4.b"},
        "8.NOS.B.4": {"8.NOS.B.4.b"},
        "8.AT.B.5": {"8.AT.B.5.b", "8.AT.B.5.c", "8.AT.B.5.d"},
    }
    for parent, subparts in expected.items():
        row = rows[parent]
        evidence = row["retrospective_reviewer_requested_2025_scope"]
        assert set(evidence["requirements"]) == subparts
        assert subparts - {"parent"} <= set(row["official_subpart_ids"])
        assert evidence["short_summary_exhaustive"] is False
        assert evidence["publisher_column"] == "2025 Standards Statement"
        assert evidence["printed_page_start"] == row["printed_page_start"]
        assert evidence["printed_page_end"] == row["printed_page_end"]
        assert evidence["independent_source_fidelity"] == "PENDING"
        assert evidence["activation"] == "FORBIDDEN"
        assert all(evidence[k] == "UNVERIFIED" for k in
                   ("canonical_equivalence", "assessment", "mastery"))

    def detail(parent, key):
        return rows[parent]["retrospective_reviewer_requested_2025_scope"]["requirements"][key]

    assert "volume and surface area" in detail("7.GR.A.2", "parent")
    assert "acute or obtuse" in detail("8.GR.B.4", "8.GR.B.4.b")
    assert "1–100" in detail("8.NOS.B.4", "8.NOS.B.4.b")
    assert "1–125" in detail("8.NOS.B.4", "8.NOS.B.4.b")
    assert "graphing and substitution" in detail("8.AT.B.5", "8.AT.B.5.b")
    assert "zero, one or infinitely many" in detail("8.AT.B.5", "8.AT.B.5.c")
    assert "contextual" in detail("8.AT.B.5", "8.AT.B.5.d")
