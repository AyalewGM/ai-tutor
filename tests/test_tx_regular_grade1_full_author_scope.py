"""Texas regular Grade 1 author-scope inventory; no source acceptance inference."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"


def test_grade1_50_distinct_source_drafts_fail_closed():
    names = ["tx_regular_grade1_process_number_operations_author.v1.json",
             "tx_regular_grade1_remaining_author.v1.json"]
    docs = [json.loads((ROOT / name).read_text()) for name in names]
    ids = [r["id"] for doc in docs for r in doc["rows"]]
    assert len(ids) == len(set(ids)) == 50
    rows = {r["id"]: r for doc in docs for r in doc["rows"]}
    assert "multiple of ten" in rows["111.3(b)(3)(A)"]["scope"]
    assert "fair shares" in rows["111.3(b)(6)(G)"]["scope"]
    assert "no gaps or overlaps" in rows["111.3(b)(7)(B)"]["scope"]
    assert "spending from saving" in rows["111.3(b)(9)(C)"]["scope"]
    assert "income" in rows["111.3(b)(9)(A)"]["scope"]
    for doc in docs:
        assert doc["independent_source_fidelity"] == "PENDING"
        assert doc["activation"] == "FORBIDDEN"
        assert doc["publisher_original_bytes_authenticated"] is False
        assert all(doc[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))
