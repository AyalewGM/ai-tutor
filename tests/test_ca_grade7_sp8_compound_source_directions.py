"""Guard California Grade 7 compound-event subparts (CDE printed p. 51).

Author-side source evidence only; this is not independent acceptance.
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
SUPPLEMENT = BASE / "ca_2013_grade7_probability_subparts_author_supplement.v1.json"
PARENTS = BASE / "ca_2013_grade7_24_source_author_slice.v1.json"


def test_ca_7sp8_three_material_source_directions():
    notes = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
    parent = json.loads(PARENTS.read_text(encoding="utf-8"))
    item = next(row for row in notes["rows"] if row["expectation_id"] == "7.SP.8")
    record = next(row for row in parent["rows"] if row["expectation_id"] == "7.SP.8")

    assert item["subparts"] == record["required_lettered_subparts"] == ["a", "b", "c"]
    assert item["printed_page"] == record["source_printed_page"] == 51
    assert item["pdf_zero_based_page"] == record["source_pdf_page_index"] == 57
    conditions = item["material_conditions"]
    assert len(conditions) == 3
    assert any("7.SP.8.a:" in clause and "fractions of outcomes" in clause
               and "sample space" in clause for clause in conditions)
    assert any("7.SP.8.b:" in clause and "everyday-language" in clause
               and "lists, tables and tree diagrams" in clause for clause in conditions)
    assert any("7.SP.8.c:" in clause and "design and use" in clause
               and "generate event frequencies" in clause
               and "approximate compound-event probabilities" in clause
               for clause in conditions)

    summary = record["author_mathematical_scope_summary"]
    for requirement in (
        "7.SP.8.a", "sample-space outcomes",
        "7.SP.8.b", "organized lists, tables and tree diagrams",
        "everyday-language", "7.SP.8.c",
        "design and use simulations", "generate frequencies",
    ):
        assert requirement in summary

    assert len(parent["rows"]) == 24
    assert notes["new_standard_count"] == 0
    assert parent["independent_source_fidelity"] == notes["independent_source_fidelity"] == "PENDING"
    assert parent["activation"] == notes["activation"] == "FORBIDDEN"
    assert record["source_review_status"].startswith("AUTHOR_")
    assert all(record[key] == "UNVERIFIED"
               for key in ("canonical_equivalence", "assessment", "mastery"))
