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


def test_exact_unseen_transfer_arithmetic() -> None:
    assert 13 + 4 * 4 == 5 + 6 * 4 == 29
    assert (3 + 2) * (3 + 5) == 3**2 + 7 * 3 + 10 == 40
    assert 320 * 3**2 // 4**2 == 180
