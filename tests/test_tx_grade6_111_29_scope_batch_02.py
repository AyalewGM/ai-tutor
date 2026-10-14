"""Texas 2025 Advanced Grade 6: bounded, unaccepted author scope batch 02."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "docs/curriculum/standards"
BATCH = BASE / "tx_advanced_2025_grade6_111_29_scope_batch_02.v1.json"
QUEUE = BASE / "tx_advanced_2025_grade6_111_29_id_author_queue.v1.json"


def test_grade6_percent_ratio_scope_ids_match_author_queue():
    batch = json.loads(BATCH.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    expected = [f"111.29(c)(4)({c})" for c in "AB"]
    expected += [f"111.29(c)(5)({c})" for c in "ABCD"]
    expected += [f"111.29(c)(6)({c})" for c in "ABC"]
    rows = batch["rows"]
    assert [r["expectation_id"] for r in rows] == expected
    locators = {r["expectation_id"]: r["source_pdf_zero_based_pages"] for r in queue["rows"]}
    assert all(r["source_pdf_zero_based_pages"] == locators[r["expectation_id"]] for r in rows)
    assert batch["author_scopes_in_this_batch"] == 9
    assert batch["previous_author_scopes"] == 17
    assert batch["remaining_unscoped_after_batch"] == 42


def test_grade6_percent_ratio_source_boundaries_fail_closed():
    batch = json.loads(BATCH.read_text(encoding="utf-8"))
    rows = {r["expectation_id"]: r["author_mathematical_scope"].lower() for r in batch["rows"]}
    assert all(v in rows["111.29(c)(4)(A)"] for v in ("whole", "part", "percent", "concrete", "pictorial"))
    assert all(v in rows["111.29(c)(4)(B)"] for v in ("sales tax", "income tax", "earned wages"))
    assert all(v in rows["111.29(c)(5)(B)"] for v in ("division", "different attributes", "quotient"))
    assert all(v in rows["111.29(c)(5)(D)"] for v in ("scale factors", "tables", "graphs", "proportions"))
    assert all(v in rows["111.29(c)(6)(C)"] for v in ("within", "between", "proportions", "unit rates"))
    assert batch["independent_source_fidelity"] == "PENDING"
    assert batch["activation"] == "FORBIDDEN"
    assert all(batch[k] == "UNVERIFIED" for k in ("canonical_mapping", "assessment", "mastery"))
    for row in batch["rows"]:
        assert row["source_scope_status"] == "AUTHOR_EDITORIAL_PARAPHRASE_AWAITING_INDEPENDENT_SOURCE_FIDELITY"
        assert all(row[k] == "UNVERIFIED" for k in ("canonical_equivalence", "assessment", "mastery"))
