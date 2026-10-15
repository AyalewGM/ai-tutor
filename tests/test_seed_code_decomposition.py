"""Structural tests for scripts/decompose_seed_codes.py artifacts."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "decompose_seed_codes", ROOT / "scripts" / "decompose_seed_codes.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

VALID = {"REMAP_CANDIDATES", "DECOMPOSE_REQUIRED", "TAXONOMY_CANDIDATE"}


def test_rows_cover_every_absent_code():
    d = mod.decompose()
    audit = mod._audit.audit()
    absent = set(audit["totals"]["seed_codes_not_in_catalog"])
    assert {r["seed_code"] for r in d["rows"]} == absent
    assert d["summary"]["absent_codes"] == len(absent)


def test_every_row_is_review_gated_and_valid():
    d = mod.decompose()
    for r in d["rows"]:
        assert r["disposition"] in VALID
        assert r["needs_math_review"] is True
        # A remap/decompose row must propose at least one catalog candidate.
        if r["disposition"] != "TAXONOMY_CANDIDATE":
            assert r["candidate_catalog_codes"], r["seed_code"]


def test_summary_counts_reconcile():
    d = mod.decompose()
    s = d["summary"]
    assert (s["decompose_required"] + s["remap_candidates"]
            + s["taxonomy_candidates"]) == s["absent_codes"]


def test_checked_in_artifact_is_fresh():
    path = ROOT / "docs/curriculum/standards/seed_canonical_decomposition.v1.json"
    if not path.exists():
        import pytest
        pytest.skip("artifact not generated on this branch")
    checked_in = json.loads(path.read_text())
    live = mod.decompose()
    assert {r["seed_code"] for r in checked_in["rows"]} == {r["seed_code"] for r in live["rows"]}
    assert checked_in["summary"] == live["summary"]


def test_no_row_claims_activation():
    d = mod.decompose()
    assert d["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert "MUST" in d["safety"] or "must" in d["safety"]
