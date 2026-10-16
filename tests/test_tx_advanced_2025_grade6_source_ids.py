"""Fail-closed regression for Texas advanced Grade 6 author source identifiers.

These tests do not constitute independent TEA source approval.
"""

import json
from collections import Counter
from pathlib import Path

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/standards/tx_advanced_2025_grade6_111_29_id_author_queue.v1.json"
)
EXPECTED_COUNTS = [7, 8, 9, 2, 4, 3, 3, 6, 4, 1, 2, 4, 2, 6, 7]


def _evidence():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def test_advanced_grade6_unique_official_identifier_shape():
    evidence = _evidence()
    rows = evidence["rows"]
    ids = [row["expectation_id"] for row in rows]
    assert len(ids) == len(set(ids)) == 68
    assert evidence["accounting"]["groups"] == 15
    assert evidence["accounting"]["group_expected_counts"] == EXPECTED_COUNTS
    assert Counter(r["parent_group"] for r in rows) == {
        idx: count for idx, count in enumerate(EXPECTED_COUNTS, 1)
    }
    expected = [
        f"111.29(c)({group})({chr(65 + letter)})"
        for group, count in enumerate(EXPECTED_COUNTS, 1)
        if group != 10
        for letter in range(count)
    ] + ["111.29(c)(10)"]
    assert set(ids) == set(expected)
    assert "111.29(c)(10)(A)" not in ids
    assert sum(r["lettered_subpart"] is None for r in rows) == 1
    assert next(r for r in rows if r["parent_group"] == 10)[
        "source_pdf_zero_based_pages"
    ] == [3]


def test_advanced_grade6_source_and_publishing_gates_fail_closed():
    evidence = _evidence()
    assert evidence["track"] == "ADVANCED_GRADE_6"
    assert evidence["official_section"] == "19 TAC 111.29(c)"
    assert evidence["adoption"]["effective_date"] == "2025-07-06"
    assert evidence["source"]["current_codified_text_parity"] == "PENDING"
    assert evidence["independent_source_fidelity"] == "PENDING"
    assert evidence["status"] == "AUTHOR_IDENTIFIER_INTAKE_NOT_INDEPENDENTLY_ACCEPTED"
    assert evidence["activation"] == "FORBIDDEN"
    assert evidence["canonical_mapping"] == "UNVERIFIED"
    assert evidence["assessment"] == "UNVERIFIED"
    assert all(row["mathematical_scope"] is None for row in evidence["rows"])
    assert all(row["canonical_equivalence"] == "UNVERIFIED" for row in evidence["rows"])
    assert all(row["mastery"] == "UNVERIFIED" for row in evidence["rows"])
    assert all(
        row["source_fidelity"]
        == "AUTHOR_LOCATED_IN_TEA_PROPOSAL_INDEPENDENT_REVIEW_PENDING"
        for row in evidence["rows"]
    )
