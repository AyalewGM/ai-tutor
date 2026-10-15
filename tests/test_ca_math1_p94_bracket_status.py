import json
from pathlib import Path


def test_ca_math1_p94_bracket_pending():
    p = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/ca_math1_p94_sid3_5_author_notes.v1.json"
    d = json.loads(p.read_text())
    assert d["publisher_strand_bracket_review_status"] == "PENDING_INDEPENDENT_SOURCE_FIDELITY"
    assert "linear focus" in d["publisher_strand_bracket_author_note"].lower()
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
