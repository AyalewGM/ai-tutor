"""Scope ledgers are non-authoritative draft interpretation, never mastery activation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs" / "curriculum" / "standards"


def test_texas_advanced_batch02_consistent_with_inventory_but_not_approved():
    batch = json.loads((ROOT / "tx_advanced_2025_scope_batch_02.v1.json").read_text(encoding="utf-8"))
    inventory = json.loads((ROOT / "national_tx_grades7_9.author_intake.v1.json").read_text(encoding="utf-8"))
    items = inventory["advanced_2025_final_adoption_evidence"]["advanced_course_expectation_identifier_inventory"]
    original = {r["expectation_id"]: r for r in items["expectations"]}
    rows = batch["rows"]
    assert len(rows) == len({r["expectation_id"] for r in rows}) == 18
    assert batch["status"] == "AUTHOR_EDITORIAL_SOURCE_SCOPE_NOT_INDEPENDENTLY_ACCEPTED"
    assert batch["source"]["publisher_bytes_verified"] is False
    assert batch["activation"] == "FORBIDDEN"
    for row in rows:
        existing = original[row["expectation_id"]]
        assert existing["editorial_mathematical_scope"] in (None, row["scope"])
        assert existing["source_fidelity"] != "APPROVED"
        assert existing["canonical_equivalence"] == "UNVERIFIED"
        assert existing["assessment"] == "UNVERIFIED"
        assert existing["mastery"] == "UNVERIFIED"
    assert items["complete_scope_rows_independently_accepted"] == 0
    assert "positive rational scale factor" in next(
        r["scope"] for r in rows if r["expectation_id"] == "111.30(c)(5)(E)"
    )
