"""Fail-closed tests for TX 2025 advanced Grade 6 author scope batch."""
import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/tx_advanced_2025_grade6_111_29_scope_batch_01.v1.json"


def test_scope_batch_identifiers_and_boundaries():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    rows = data["rows"]
    expected = [f"111.29(c)(2)({letter})" for letter in "ABCDEFGH"]
    expected += [f"111.29(c)(3)({letter})" for letter in "ABCDEFGHI"]
    assert [r["expectation_id"] for r in rows] == expected
    assert len(set(expected)) == len(rows) == 17
    assert data["editorial_scope_rows_in_this_batch"] == 17
    assert data["existing_grade6_id_queue_expected_total"] == 68
    assert data["other_grade6_records_still_unscoped"] == 51
    assert all(r["author_mathematical_scope"].strip() for r in rows)


def test_acceptance_must_remain_fail_closed():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    assert data["independent_source_fidelity"] == "PENDING"
    assert data["activation"] == "FORBIDDEN"
    assert all(data[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))
    for row in data["rows"]:
        assert row["source_scope_status"] == "AUTHOR_EDITORIAL_PARAPHRASE_AWAITING_INDEPENDENT_SOURCE_FIDELITY"
        assert all(row[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
