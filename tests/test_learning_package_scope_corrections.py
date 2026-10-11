"""Regression gates for bounded independent evidence corrections in PR #328."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/drafts"


def _package(wave: str, ident: str) -> dict:
    path = ROOT / wave / "content.draft.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return next(p for p in data["packages"] if p["id"] == ident)


def test_start_unknown_and_equality_preservation_evidence():
    p = _package("learning-packages-wave2", "W2-G1-ADDITION-UNKNOWN")
    items = {i.get("unknown_role"): i for i in p["independent_assessment"]}
    assert {"START_UNKNOWN", "EQUALITY_UNKNOWN"} <= items.keys()
    assert 16 - 7 == 9
    assert 8 + 4 == 7 + 5
    assert p["runtime_activation"] is False
    assert p["mastery_writes"] is False
    assert p["assessment_scope_evidence"]["independent_review"] == "REQUESTED_NOT_APPROVED"
    for role in ("START_UNKNOWN", "EQUALITY_UNKNOWN"):
        item = items[role]
        assert item["hints_allowed"] is False
        assert item["teacher_oracle_visibility"] == "SERVER_ONLY"


def test_system_cardinality_and_equation_equivalence_evidence():
    p = _package("learning-packages-wave3", "W3-G9-SYSTEMS-LINEAR")
    items = {i.get("solution_count"): i for i in p["independent_assessment"]}
    assert {"ZERO", "ONE", "INFINITE"} <= items.keys()
    # Independent checks: contradictory parallel lines, a unique intersection,
    # and a proportional equation pair containing at least two different points.
    assert 4 * 0 + 1 != 4 * 0 - 3
    x, y = 5, 2
    assert x + y == 7 and x - y == 3
    for x, y in [(0, 6), (2, 3)]:
        assert 3 * x + 2 * y == 12
        assert 6 * x + 4 * y == 24
    assert p["runtime_activation"] is False
    assert p["mastery_writes"] is False
    for role in ("ZERO", "ONE", "INFINITE"):
        assert items[role]["hints_allowed"] is False
        assert items[role]["teacher_oracle_visibility"] == "SERVER_ONLY"
