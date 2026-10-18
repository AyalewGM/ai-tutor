"""Fail-closed checks for the VDOE Grade 8 revision overview transcription.

These expectations assert the bounded *overview* artifact, not completeness of
the separately published 2023 Standards of Learning or accepted mappings.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs" / "curriculum" / "standards"
SOURCE = ROOT / "va_grade8_2023.overview_ks_clause_inventory_446.v1.json"
COUNTS = {
    "8.NS.1": 3, "8.NS.2": 3, "8.CE.1": 3,
    "8.MG.1": 2, "8.MG.2": 4, "8.MG.3": 7,
    "8.MG.4": 5, "8.MG.5": 3, "8.PS.1": 4,
    "8.PS.2": 10, "8.PS.3": 6, "8.PFA.1": 2,
    "8.PFA.2": 2, "8.PFA.3": 6, "8.PFA.4": 7,
    "8.PFA.5": 7,
}

def test_all_16_grade8_parent_clauses_are_indexed_from_overview():
    evidence = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = {r["parent_id"]: r for r in evidence["parent_rows"]}
    assert set(rows) == set(COUNTS)
    assert sum(COUNTS.values()) == 74
    for parent, n in COUNTS.items():
        row = rows[parent]
        assert row["knowledge_skill_clause_ids"] == [parent + chr(97 + i) for i in range(n)]
        assert row["overview_printed_pages"]
        assert row["review_status"] == "AUTHOR_TRANSCRIPTION_PENDING_INDEPENDENT_ORIGINAL_SOL_COMPARISON"

def test_no_overview_evidence_can_claim_standards_approval():
    evidence = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert evidence["source_role"] == "OFFICIAL_VDOE_REVISION_OVERVIEW_NOT_ORIGINAL_STANDARDS"
    assert evidence["original_2023_sol_document_verified"] is False
    assert evidence["canonical_correspondence_approved"] is False
    assert evidence["activation"] == "FORBIDDEN"
