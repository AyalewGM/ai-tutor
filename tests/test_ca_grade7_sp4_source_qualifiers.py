"""Source-parity gate for CA 7.SP.4; does not grant independent approval."""

import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/ca_2013_grade7_24_source_author_slice.v1.json"


def test_ca_grade7_sp4_center_variability_and_random_sampling():
    document = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert len(document["rows"]) == 24
    row = next(x for x in document["rows"] if x["expectation_id"] == "7.SP.4")
    assert (row["source_printed_page"], row["source_pdf_page_index"]) == (50, 56)
    expected = [
        "measures of center",
        "measures of variability",
        "numerical data from random samples",
        "informal comparative inferences about two populations",
    ]
    assert row["test_material_conditions"] == expected
    assert all(item in row["author_mathematical_scope_summary"] for item in expected)
    assert row["required_lettered_subparts"] == []
    assert row["source_review_status"].startswith("AUTHOR_")
    assert all(row[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
    assert document["independent_source_fidelity"] == "PENDING"
    assert document["activation"] == "FORBIDDEN"
