"""California Grade 6 printed p.43 complete-parent source-intake invariants.

These assertions protect author material qualifiers, not publisher acceptance.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
PAGE43 = ROOT / "ca_2013_grade6_page43_complete_parent_source_author_slice.v1.json"


def test_grade6_page43_parent_identifiers_and_publisher_locator():
    batch = json.loads(PAGE43.read_text(encoding="utf-8"))
    rows = batch["rows"]
    ids = [row["expectation_id"] for row in rows]
    assert ids == ["6.NS.5", "6.NS.6", "6.NS.7", "6.NS.8", "6.EE.1"]
    assert len(ids) == len(set(ids)) == batch["expectation_count"] == 5
    assert batch["source_printed_page"] == 43
    assert batch["source_pdf_zero_based_page_index"] == 49
    assert all((r["source_printed_page"], r["source_pdf_zero_based_page_index"]) == (43, 49) for r in rows)
    assert "6.EE.2" in batch["coverage_boundary"]


def test_grade6_page43_material_conditions_and_fail_closed_boundaries():
    batch = json.loads(PAGE43.read_text(encoding="utf-8"))
    by_id = {r["expectation_id"]: r for r in batch["rows"]}
    conditions = {k: set(v["required_material_conditions"]) for k, v in by_id.items()}
    assert "contextual meaning of zero" in conditions["6.NS.5"]
    assert {"required subparts a b c", "opposite of opposite equals original and zero is its own opposite",
            "reflections across one or both axes", "rational coordinate plotting"} <= conditions["6.NS.6"]
    assert {"required subparts a b c d", "absolute value as distance from zero",
            "magnitude comparison not conflated with order"} <= conditions["6.NS.7"]
    assert {"all four coordinate-plane quadrants",
            "distance between points with equal first coordinate or equal second coordinate"} <= conditions["6.NS.8"]
    assert {"both writing and evaluating expressions", "whole-number exponents"} <= conditions["6.EE.1"]
    assert batch["independent_source_fidelity"] == "PENDING"
    assert batch["activation"] == "FORBIDDEN"
    assert all(batch[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
    for row in batch["rows"]:
        assert row["source_review_status"] == "AUTHOR_PARAPHRASE_PENDING_INDEPENDENT_FIDELITY"
        assert all(row[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
