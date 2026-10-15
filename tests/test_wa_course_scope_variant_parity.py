"""Washington course-placement scope-variant evidence, not publisher approval."""
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_wa_high_school_scope_variants_match_author_extraction_without_collapsing():
    audit = json.loads((BASE / "wa_2026_v3_1_course_scope_cell_audit.v1.json").read_text())
    source = json.loads((BASE / "wa_2026_v3_1_source_extraction.json").read_text())
    grouped = defaultdict(list)
    for row in source["high_school_course_rows"]:
        grouped[row["code"]].append(row)
    variants = {code: rows for code, rows in grouped.items()
                if len({row["scope"] for row in rows}) > 1}
    assert len(variants) == len(audit["course_scope_variants"]) == 22
    assert set(variants) == {v["code"] for v in audit["course_scope_variants"]}
    for record in audit["course_scope_variants"]:
        rows = variants[record["code"]]
        assert len(rows) == len(record["scope_cells"])
        assert len({row["scope"] for row in rows}) == record["distinct_source_scope_texts"]
        assert record["extraction_matches_original_cells"] is True
        assert record["independent_source_acceptance"] == "PENDING"
    assert source["source"]["publisher_byte_match"] == "NOT_INDEPENDENTLY_VERIFIED"
    assert source["acceptance"]["canonical_equivalence"] == "UNVERIFIED"
    assert source["acceptance"]["activation"] == "FORBIDDEN"
