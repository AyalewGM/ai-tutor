"""Texas regular Grade 6 partial author inventory: never source approval."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_texas_regular_grade6_partial_source_accounting():
    tx = json.loads((BASE / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["TX"]
    assert tx["regular_grade6_111_26_author_scope_rows"] == 59
    assert tx["regular_grade6_111_26_independently_accepted_source_rows"] == 0
    assert tx["partially_author_scoped_tracks"] == []
    assert "REGULAR_GRADE_6" not in tx["unextracted_tracks"]
    assert all(f.startswith("tx_regular_grade6_") for f in tx["regular_grade6_source_files"])
    rows = []
    for name in tx["regular_grade6_source_files"][:3]:
        doc = json.loads((BASE / name).read_text(encoding="utf-8"))
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["activation"] == "FORBIDDEN"
        assert doc["publisher_original_bytes_authenticated"] is False
        assert doc["canonical_mapping"] == doc["assessment"] == doc["mastery"] == "UNVERIFIED"
        rows.extend(doc["rows"])
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)) == 16
    assert ids == ([f"111.26(b)(2)({x})" for x in "ABCDE"] +
                   [f"111.26(b)(4)({x})" for x in "ABCDEFGH"] +
                   [f"111.26(b)(5)({x})" for x in "ABC"])
