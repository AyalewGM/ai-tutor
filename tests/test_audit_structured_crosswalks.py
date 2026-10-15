"""Structured source crosswalks must not be treated as hashable skill codes."""
from scripts import propose_composite_splits as mod


def test_structured_crosswalk_only_explicit_local_id_counts(monkeypatch):
    monkeypatch.setattr(mod._dec, "decompose", lambda: {"rows": [{
        "disposition": "DECOMPOSE_REQUIRED",
        "seed_code": "MATH.SEED.TEST",
        "references": [{"local_code": "LOCAL.TEST", "seed": "seed_test.py"}],
        "candidate_catalog_codes": [],
    }]})
    monkeypatch.setattr(mod, "_manifest_rows", lambda: [
        {"expectation_id": "A.REI.B.4", "repository_existing_crosswalks": [
            {"local_code": "LOCAL.TEST"}, {"unknown": "not an id"}]},
    ])
    result = mod.propose()
    assert result["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert all(r["status"] != "ACCEPTED" for r in result["proposals"])
