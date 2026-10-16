"""California 7.SP.1–3 author-only source-fidelity regression, CDE p.50."""
import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/ca_2013_grade7_24_source_author_slice.v1.json"


def test_grade7_sampling_inference_and_variability_source_conditions():
    d = json.loads(PATH.read_text(encoding="utf-8"))
    r = {x["expectation_id"]: x for x in d["rows"]}
    assert len(r) == 24
    expected = {
        "7.SP.1": ["only when the sample is representative", "tends to produce", "does not guarantee"],
        "7.SP.2": ["samples of the same size", "estimates or predictions", "how far off"],
        "7.SP.3": ["degree of visual overlap", "similar variabilities", "multiple of a measure of variability"],
    }
    for code, clauses in expected.items():
        row = r[code]
        assert all(c in row["author_mathematical_scope_summary"] for c in clauses), code
        assert row["source_printed_page"] == 50
        assert row["source_pdf_page_index"] == 56
        assert row["source_review_status"].startswith("AUTHOR_")
        assert all(row[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
