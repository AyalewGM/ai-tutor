"""Author-source gate for California 7.SP.7.a/b; independent review pending."""

import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/ca_2013_grade7_24_source_author_slice.v1.json"


def test_grade7_empirical_model_is_not_assumed_uniform():
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["expectation_id"] == "7.SP.7")
    assert row["required_lettered_subparts"] == ["a", "b"]
    assert row["source_printed_page"] == 51
    assert row["source_pdf_page_index"] == 57
    conditions = set(row["test_material_conditions"])
    assert "uniform equal-probability outcome model (a)" in conditions
    assert "empirical chance-process frequency model (b)" in conditions
    assert "empirical model may be nonuniform (b)" in conditions
    assert "assess equal likelihood from observed frequencies (b)" in conditions
    assert "compare model probabilities with observed frequencies" in conditions
    assert "explain discrepancies between model and data" in conditions
    assert "need not be uniform" in row["author_mathematical_scope_summary"]
    assert "whether outcomes seem equally likely" in row["author_mathematical_scope_summary"]
    assert row["source_review_status"].startswith("AUTHOR_")
    assert doc["independent_source_fidelity"] == "PENDING"
    assert doc["activation"] == "FORBIDDEN"
    assert all(row[gate] == "UNVERIFIED" for gate in ("canonical_equivalence", "assessment", "mastery"))
