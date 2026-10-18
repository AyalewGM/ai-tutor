from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/va_grade8_2023.revision_clause_evidence_446.md"

def test_revision_evidence_is_fail_closed():
    text = LEDGER.read_text(encoding="utf-8")
    assert "AUTHOR EVIDENCE ONLY — NOT ACCEPTED" in text
    assert "original Grade 8 and compiled original links returned HTTP 403" in text
    assert "not a full enumeration of all lettered subparts" in text
    assert "No learner/history/mastery/activation mutation" in text

def test_revision_overview_is_not_promoted_to_original_source():
    text = LEDGER.read_text(encoding="utf-8")
    assert "49365/638315056768230000" in text
    assert "48945/638741652670270000" in text
    assert "not** a substitute for the original standards" in text
    for identifier in ("8.NS.1c", "8.MG.2c", "8.MG.4c", "8.PS.1a", "8.PS.2d", "8.PS.2i", "8.PS.3c", "8.PFA.1a", "8.PFA.3a", "8.PFA.3b", "8.PFA.4c", "8.PFA.4d", "8.PFA.5d", "8.PFA.5e"):
        assert identifier in text
