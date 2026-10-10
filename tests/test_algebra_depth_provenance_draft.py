"""Fail-closed checks for authored Grade 9 algebra records."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs/curriculum/drafts/algebra_depth_provenance_20261010"


def test_algebra_drafts_are_inactive() -> None:
    for filename in ("linear.provenance.json", "w2-status.json", "exponential.provenance.json"):
        entry = json.loads((DRAFT / filename).read_text(encoding="utf-8"))
        assert entry["runtime_activation"] is False
        assert entry["mastery_writes"] is False
        assert entry["learner_data_writes"] is False


def test_source_heads_and_review_dispositions_are_current() -> None:
    consolidated = json.loads(
        (DRAFT / "content_provenance.v2.json").read_text(encoding="utf-8")
    )
    sources = consolidated["sources"]
    packages = {item["package_id"]: item for item in consolidated["packages"]}
    linear = json.loads((DRAFT / "linear.provenance.json").read_text(encoding="utf-8"))
    quadratic = json.loads((DRAFT / "w2-status.json").read_text(encoding="utf-8"))

    assert "PR #328 current exact-head 2445f197259ff27b5c99dd2b45c4bcbc2e5292f8" in sources
    assert "PR #325 exact-head c1fa26a560ebea022202bace38d51e91ca5d08fa" in sources
    assert {item["revision"] for item in packages.values()} == {"G9_DEPTH_R3_2026-10-10"}
    assert linear["pedagogical_review"] == "CHANGES_REQUIRED"
    assert quadratic["pedagogy_review"] == "CHANGES_REQUIRED"
    assert linear["source_head"] == "5d4e613b4aa241384809e048c60ee082e6f14fe4"
    assert quadratic["source_head"] == "2445f197259ff27b5c99dd2b45c4bcbc2e5292f8"


def test_exact_unseen_transfer_arithmetic() -> None:
    assert 13 + 4 * 4 == 5 + 6 * 4 == 29
    assert (3 + 2) * (3 + 5) == 3**2 + 7 * 3 + 10 == 40
    assert 320 * 3**2 // 4**2 == 180
