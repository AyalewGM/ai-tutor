"""California Grade 3 area subpart evidence, author-only."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade3_area_lettered_requirements_preserved():
    supplement = json.loads((ROOT / "ca_2013_grade3_p27_area_lettered_subparts_author_guard.v1.json").read_text())
    source = json.loads((ROOT / "ca_2013_grade3_page27_source_author_slice.v1.json").read_text())
    ids = [r["expectation_id"] for r in source["rows"]]
    assert len(ids) == len(set(ids))
    assert {"3.MD.5", "3.MD.7"}.issubset(set(ids))
    assert supplement["subparts_by_parent"] == {
        "3.MD.5": ["a", "b"],
        "3.MD.7": ["a", "b", "c", "d"],
    }
    assert supplement["source_printed_page"] == 27
    assert supplement["source_pdf_zero_based_page_index"] == 33
    assert supplement["publisher_original_bytes_authenticated"] is False
    assert supplement["independent_source_fidelity"] == "PENDING"
    assert supplement["activation"] == "FORBIDDEN"
    assert supplement["canonical_equivalence"] == "UNVERIFIED"
