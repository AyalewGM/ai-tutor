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


def test_checked_in_artifact_is_fresh():
    path = ROOT / "docs/curriculum/standards/seed_composite_split_proposals.v1.json"
    if not path.exists():
        import pytest
        pytest.skip("artifact not generated")
    checked_in = json.loads(path.read_text())
    assert checked_in["summary"] == mod.propose()["summary"]
