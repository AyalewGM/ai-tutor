"""California 7.SP.6 probability source directions, author-only review gate."""
import json
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
          / "ca_2013_grade7_24_source_author_slice.v1.json")


def test_grade7_probability_bidirectional_frequency_prediction():
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["expectation_id"] == "7.SP.6")
    conditions = set(row["test_material_conditions"])
    assert "long-run relative frequency" in conditions
    assert "predict relative frequency from probability" in conditions
    assert "predict approximate counts for a stated trial count" in conditions
    assert "given an event probability" in row["author_mathematical_scope_summary"]
    assert row["required_lettered_subparts"] == []
    assert row["source_printed_page"] == 50
    assert row["source_pdf_page_index"] == 56
    assert row["source_review_status"].startswith("AUTHOR_")
    assert all(row[key] == "UNVERIFIED" for key in
               ("canonical_equivalence", "assessment", "mastery"))
    assert doc["independent_source_fidelity"] == "PENDING"
    assert doc["activation"] == "FORBIDDEN"
