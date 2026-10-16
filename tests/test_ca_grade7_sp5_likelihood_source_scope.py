"""California 7.SP.5 author-source fidelity regression; no independent acceptance."""

import json
from pathlib import Path

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/standards/ca_2013_grade7_24_source_author_slice.v1.json"
)


def test_ca_grade7_sp5_probability_likelihood_scope_fail_closed():
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert len(doc["rows"]) == 24
    assert len({row["expectation_id"] for row in doc["rows"]}) == 24
    row = next(row for row in doc["rows"] if row["expectation_id"] == "7.SP.5")

    assert row["track"] == "GRADE_7"
    assert row["source_printed_page"] == 50
    assert row["source_pdf_page_index"] == 56
    assert row["required_lettered_subparts"] == []

    conditions = set(row["test_material_conditions"])
    assert conditions == {
        "probability between 0 and 1",
        "larger number indicates greater likelihood",
        "near 0: unlikely",
        "around 1/2: neither unlikely nor likely",
        "near 1: likely",
    }
    scope = row["author_mathematical_scope_summary"]
    assert "larger numbers indicate greater likelihood" in scope
    assert "near 0 indicates an unlikely event" in scope
    assert "around 1/2 indicates an event that is neither unlikely nor likely" in scope
    assert "near 1 indicates a likely event" in scope

    assert row["source_review_status"].startswith("AUTHOR_")
    assert doc["independent_source_fidelity"] == "PENDING"
    assert doc["activation"] == "FORBIDDEN"
    assert all(
        row[gate] == "UNVERIFIED"
        for gate in ("canonical_equivalence", "assessment", "mastery")
    )
