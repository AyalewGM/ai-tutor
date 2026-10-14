"""Author evidence counts are not independent source acceptance."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_advanced_grade6_all_author_batches_and_fail_closed():
    matrix = json.loads((ROOT / "national_ca_tx_wa_completion_matrix.v1.json").read_text())
    tx = matrix["states"]["TX"]
    rows = []
    assert len(tx["advanced_grade6_source_batches"]) == 6
    for name in tx["advanced_grade6_source_batches"]:
        data = json.loads((ROOT / name).read_text())
        assert data["independent_source_fidelity"] == "PENDING"
        assert data["activation"] == "FORBIDDEN"
        rows.extend(data["rows"])
    ids = [row["expectation_id"] for row in rows]
    assert len(ids) == len(set(ids)) == 68
    assert tx["advanced_grade6_111_29_author_identifier_rows"] == 68
    assert tx["advanced_grade6_111_29_author_scope_rows"] == 68
    assert tx["advanced_grade6_111_29_independently_accepted_source_rows"] == 0
    assert "ADVANCED_GRADE_6" not in tx["unextracted_tracks"]
    for row in rows:
        assert row["author_mathematical_scope"].strip()
        assert row["canonical_equivalence"] == "UNVERIFIED"
        assert row["assessment"] == "UNVERIFIED"
        assert row["mastery"] == "UNVERIFIED"
