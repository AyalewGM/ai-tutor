"""California 7.SP.6 bidirectional probability source regression; author-only gate."""
import json
from pathlib import Path

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/standards/ca_2013_grade7_24_source_author_slice.v1.json"
)


def test_grade7_probability_bidirectional_frequency_prediction():
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert len(doc["rows"]) == 24
    assert len({row["expectation_id"] for row in doc["rows"]}) == 24
    row = next(r for r in doc["rows"] if r["expectation_id"] == "7.SP.6")
    assert set(row["test_material_conditions"]) == {
        "collect data on the chance process",
        "observe long-run relative frequency",
        "predict approximate relative frequency from known probability",
        "predict approximate event count over repeated trials",
        "predicted count is not an exact guarantee",
    }
    summary = row["author_mathematical_scope_summary"].lower()
    assert "collecting data on the process" in summary
    assert "long-run relative frequency" in summary
    assert "given an event probability" in summary
    assert "approximate event count" in summary
    assert "predictions are not exact guarantees" in summary
    assert "200" in summary and "600" in summary
    assert row["required_lettered_subparts"] == []
    assert row["source_printed_page"] == 50
    assert row["source_pdf_page_index"] == 56
    assert row["source_review_status"].startswith("AUTHOR_")
    assert all(row[key] == "UNVERIFIED" for key in
               ("canonical_equivalence", "assessment", "mastery"))
    assert doc["independent_source_fidelity"] == "PENDING"
    assert doc["activation"] == "FORBIDDEN"
