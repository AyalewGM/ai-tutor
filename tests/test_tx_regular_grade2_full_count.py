"""All Texas Grade 2 rows are author provisional, not activated."""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade2_50_distinct_ids_stay_provisional():
    tx = json.loads((P / "national_ca_tx_wa_completion_matrix.v1.json").read_text())["states"]["TX"]
    assert tx["regular_grade2_111_4_author_scope_rows"] == 50
    assert tx["regular_grade2_111_4_independently_accepted_source_rows"] == 0
    assert len(tx["regular_grade2_source_files"]) == 11
    ids = []
    for filename in tx["regular_grade2_source_files"]:
        doc = json.loads((P / filename).read_text())
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["activation"] == "FORBIDDEN"
        ids.extend(row["id"] for row in doc["rows"])
    assert len(ids) == len(set(ids)) == 50
