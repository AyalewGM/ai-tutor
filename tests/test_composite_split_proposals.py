"""Structural tests for scripts/propose_composite_splits.py."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "propose_composite_splits", ROOT / "scripts" / "propose_composite_splits.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_proposals_cover_every_composite_local_skill():
    d = mod.propose()
    dec = mod._dec.decompose()
    composite_locals = {
        r["local_code"]
        for row in dec["rows"] if row["disposition"] == "DECOMPOSE_REQUIRED"
        for r in row["references"] if r["local_code"]
    }
    assert {p["local_skill_code"] for p in d["proposals"]} == composite_locals


def test_atomic_codes_are_unique_and_review_gated():
    d = mod.propose()
    codes = [a["proposed_skill_code"] for p in d["proposals"]
             for a in p["proposed_atomic_skills"]]
    assert len(codes) == len(set(codes)), "duplicate proposed skill codes"
    for p in d["proposals"]:
        assert p["status"].endswith(("NEEDS_MATH_REVIEW", "ALIGN_OR_RETIRE"))
        for a in p["proposed_atomic_skills"]:
            assert a["needs_math_review"] is True


def test_one_atomic_per_expectation():
    d = mod.propose()
    for p in d["proposals"]:
        exps = [a["covers_expectation"] for a in p["proposed_atomic_skills"]]
        assert len(exps) == len(set(exps)), \
            f"{p['local_skill_code']}: atomic skill spans two expectations"


def test_summary_reconciles_and_fails_closed():
    d = mod.propose()
    s = d["summary"]
    assert s["composite_local_skills"] == len(d["proposals"])
    assert s["proposed_atomic_skills"] == sum(
        len(p["proposed_atomic_skills"]) for p in d["proposals"])
    assert d["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    assert "MUST" in d["safety"]


def test_checked_in_review_snapshot_is_preserved():
    """New provisional standards may add candidates without approving taxonomy.

    The checked-in artifact is a historical review snapshot, not an
    automatically accepted live inventory. Ensure every prior claimed
    expectation remains proposed and no previous proposal disappears.
    """
    path = ROOT / "docs/curriculum/standards/seed_composite_split_proposals.v1.json"
    if not path.exists():
        import pytest
        pytest.skip("artifact not generated")
    checked_in = json.loads(path.read_text())
    current = mod.propose()
    assert checked_in["status"] == current["status"] == "DRAFT_PROPOSED_NOT_VERIFIED"
    old_by_local = {p["local_skill_code"]: p for p in checked_in["proposals"]}
    new_by_local = {p["local_skill_code"]: p for p in current["proposals"]}
    assert old_by_local.keys() == new_by_local.keys()
    for local, previous in old_by_local.items():
        existing = new_by_local[local]
        old_claims = {a["covers_expectation"] for a in previous["proposed_atomic_skills"]}
        new_claims = {a["covers_expectation"] for a in existing["proposed_atomic_skills"]}
        assert old_claims <= new_claims, f"{local}: reviewed proposal evidence disappeared"
        assert all(a["needs_math_review"] is True for a in existing["proposed_atomic_skills"])
    assert current["summary"]["proposed_atomic_skills"] >= checked_in["summary"]["proposed_atomic_skills"]
