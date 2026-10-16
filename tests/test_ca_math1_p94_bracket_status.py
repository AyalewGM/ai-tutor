import json
from pathlib import Path


def test_ca_math1_p94_bracket_pending():
    p = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/ca_math1_p94_sid3_5_author_notes.v1.json"
    d = json.loads(p.read_text())
    assert d["publisher_strand_bracket_review_status"] == "PENDING_INDEPENDENT_SOURCE_FIDELITY"
    assert "linear focus" in d["publisher_strand_bracket_author_note"].lower()
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"


def test_ca_math1_sid6a_model_scope_requires_independent_adjudication():
    p = Path(__file__).resolve().parents[1] / "docs/curriculum/standards/ca_math1_p94_sid3_5_author_notes.v1.json"
    d = json.loads(p.read_text())
    assert d["publisher_sid6a_source_id"] == "S-ID.6.a"
    note = d["publisher_sid6a_scope_author_note"].lower()
    assert all(model in note for model in ("linear", "quadratic", "exponential"))
    assert "mathematics ii or iii" in note
    assert d["publisher_sid6a_scope_review_status"] == "PENDING_INDEPENDENT_SOURCE_FIDELITY"
    assert d["supplemental_existing_placements_only"] is True
    assert d["independent_source_fidelity"] == "PENDING"
    assert d["activation"] == "FORBIDDEN"
