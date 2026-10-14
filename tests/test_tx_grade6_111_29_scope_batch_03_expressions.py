"""TX advanced Grade 6 111.29(c)(7) editor scopes: no accepted coverage."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
BATCH = BASE / "tx_advanced_2025_grade6_111_29_scope_batch_03_expressions.v1.json"
QUEUE = BASE / "tx_advanced_2025_grade6_111_29_id_author_queue.v1.json"


def test_expression_scopes_match_source_queue_and_preserve_gates():
    data = json.loads(BATCH.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    ids = [r["expectation_id"] for r in data["rows"]]
    assert ids == [f"111.29(c)(7)({s})" for s in "ABC"]
    assert set(ids).issubset({r["expectation_id"] for r in queue["rows"]})
    assert (data["prior_scoped"], data["new_author_scoped"], data["remaining_unscoped"]) == (26, 3, 39)
    a, b, c = [r["author_mathematical_scope"].lower() for r in data["rows"]]
    assert all(v in a for v in ("verbal", "numerical", "algebraic", "expressions", "equations"))
    assert all(v in b for v in ("concrete", "pictorial", "algebraic", "equivalent"))
    assert all(v in c for v in ("inverse", "identity", "commutative", "associative", "distributive"))
    assert data["independent_source_fidelity"] == "PENDING"
    assert data["activation"] == "FORBIDDEN"
    assert all(data[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))
    for row in data["rows"]:
        assert row["source_scope_status"] == "AUTHOR_EDITORIAL_PARAPHRASE_AWAITING_INDEPENDENT_SOURCE_FIDELITY"
        assert all(row[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
