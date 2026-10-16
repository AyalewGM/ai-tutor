"""Provisional CA Mathematics I page-91 notes: structural and fail-closed tests.

These assertions are not independent publisher source-fidelity approval.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
SOURCE = ROOT / "ca_2013_mathematics1_page91_11_scope_notes.v1.json"


def _document():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def test_math1_page91_existing_placement_ids_and_locator():
    d = _document()
    ids = [row["expectation_id"] for row in d["rows"]]
    assert ids == [
        "A-REI.3", "A-REI.3.1", "A-REI.5", "A-REI.6",
        "A-REI.10", "A-REI.11", "A-REI.12",
        "F-IF.1", "F-IF.2", "F-IF.3", "F-IF.4",
    ]
    assert len(ids) == len(set(ids)) == d["requirement_count"] == 11
    assert d["source_printed_page"] == 91
    assert d["source_pdf_zero_based_page_index"] == 97
    assert d["original_math1_placement_count"] == 59
    assert d["historical_grade7_8_algebra1_math1_placements"] == 173
    assert all(r["source_printed_page"] == 91 for r in d["rows"])
    assert all(r["source_pdf_zero_based_page_index"] == 97 for r in d["rows"])


def test_math1_page91_material_qualifiers_and_unverified_gates():
    d = _document()
    by_id = {r["expectation_id"]: r for r in d["rows"]}
    assert any("absolute-value" in s for s in by_id["A-REI.3.1"]["material_conditions"])
    assert any("same solution set" in s for s in by_id["A-REI.5"]["material_conditions"])
    assert any("exclude boundary" in s for s in by_id["A-REI.12"]["material_conditions"])
    assert any("subset of integers" in s for s in by_id["F-IF.3"]["material_conditions"])
    assert by_id["F-IF.4"]["source_scope_tension"] == "LITERAL_MATH1_LINEAR_DOMAIN_BRACKET_PENDING_ADJUDICATION"
    assert any("linear domain" in s.lower() for s in by_id["F-IF.4"]["material_conditions"])
    assert d["publisher_original_file_bytes_hash_authenticated"] is False
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
    assert all(d[k] == "UNVERIFIED" for k in ("canonical_equivalence", "generator", "assessment", "mastery"))
    assert all(row["source_review_status"] == "PENDING_INDEPENDENT_SOURCE_FIDELITY" for row in d["rows"])
