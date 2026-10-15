"""California Mathematics I p.92 author notes: inventory and safety invariants.

These checks do not independently certify the official publisher source.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
SUPPLEMENT = ROOT / "ca_2013_mathematics1_page92_12_scope_notes.v1.json"
AUDIT = ROOT / "ca_2013_mathematics1_pages90_94_author_audit.v1.json"
MATRIX = ROOT / "national_ca_tx_wa_completion_matrix.v1.json"

EXPECTED_IDS = [
    "F-IF.5", "F-IF.6", "F-IF.7.a", "F-IF.7.e", "F-IF.9",
    "F-BF.1.a", "F-BF.1.b", "F-BF.2", "F-BF.3",
    "F-LE.1.a", "F-LE.1.b", "F-LE.1.c",
]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_page92_supplement_matches_existing_author_audit_without_new_ids():
    d = _load(SUPPLEMENT)
    audit = _load(AUDIT)
    ids = [r["expectation_id"] for r in d["rows"]]
    audit_ids = [
        r["expectation_id"] for r in audit["rows"]
        if r["source_printed_page"] == 92
    ]
    assert ids == audit_ids == EXPECTED_IDS
    assert len(set(ids)) == d["requirement_count"] == 12
    assert d["source_printed_page"] == 92
    assert d["source_pdf_zero_based_page_index"] == 98
    assert all(
        (r["source_printed_page"], r["source_pdf_zero_based_page_index"])
        == (92, 98) for r in d["rows"]
    )
    assert d["original_math1_placement_count"] == 59
    assert d["historical_grade7_8_algebra1_math1_placements"] == 173
    matrix = _load(MATRIX)["states"]["CA"]
    assert matrix["author_source_scope_rows_by_track"]["MATHEMATICS_I"] == 59
    assert matrix["author_scope_total_staged"] == 334


def test_page92_source_qualifiers_fail_closed():
    d = _load(SUPPLEMENT)
    by_id = {r["expectation_id"]: r for r in d["rows"]}
    f7a = " ".join(by_id["F-IF.7.a"]["material_conditions"])
    f7e = " ".join(by_id["F-IF.7.e"]["material_conditions"])
    fbf3 = " ".join(by_id["F-BF.3"]["material_conditions"])
    fle1a = " ".join(by_id["F-LE.1.a"]["material_conditions"])
    assert "quadratic" in f7a and "course" in f7a
    assert "logarithmic" in f7e and "trigonometric" in f7e
    assert "vertical translations" in fbf3
    assert all(
        expression in fbf3
        for expression in ("f(x)+k", "k*f(x)", "f(k*x)", "f(x+k)")
    )
    assert "equal differences" in fle1a and "equal multiplicative factors" in fle1a
    assert "integer inputs" in " ".join(by_id["F-BF.2"]["material_conditions"])
    assert d["publisher_original_file_bytes_hash_authenticated"] is False
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
    assert all(
        d[key] == "UNVERIFIED"
        for key in ("canonical_equivalence", "generator", "assessment", "mastery")
    )
    assert all(
        r["source_review_status"] == "PENDING_INDEPENDENT_SOURCE_FIDELITY"
        for r in d["rows"]
    )
