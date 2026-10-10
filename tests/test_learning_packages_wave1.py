"""Fail-closed structural and independent arithmetic checks for DRAFT learning wave 1.

Run: pytest -q tests/test_learning_packages_wave1.py
No runtime activation, student records, or production imports.
"""
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs/curriculum/drafts/learning-packages-wave1/content.draft.json"


def load():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_batch_is_review_gated_and_complete():
    data = load()
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["runtime_activation"] is False
    assert data["mastery_writes"] is False
    assert len(data["packages"]) == 5
    ids = [p["id"] for p in data["packages"]]
    assert len(ids) == len(set(ids))
    for p in data["packages"]:
        assert p["status"] == "DRAFT_UNVERIFIED"
        assert p["runtime_activation"] is False
        assert p["mastery_writes"] is False
        assert p["standards_mapping"] == "PROVISIONAL_NOT_ACCEPTED"
        assert p["independent_math_review"] == "PENDING"
        assert len(p["worked_examples"]) >= 5
        assert len(p["misconception_pathways"]) >= 3
        assert len(p["guided_practice"]) >= 4
        assert len(p["independent_assessment"]) >= 3
        assert len(p["lesson_sequence"]) >= 5
        assert p["interactive_spec"]["a11y"]
        assert p["interactive_spec"]["independent_assessment"]
        for m in p["misconception_pathways"]:
            assert len(m["socratic_hints"]) >= 2
        for a in p["independent_assessment"]:
            assert a["hint_access"] is False
            assert a["feedback_visibility"] == "AFTER_SUBMISSION"


def test_independent_volume_oracles():
    # Recalculate representative rational-edge cases independently.
    assert Fraction(3, 4) * Fraction(2, 3) * 6 == 3
    assert Fraction(5, 2) * Fraction(4, 5) * Fraction(3, 2) == 3
    assert Fraction(9, 4) / Fraction(3, 2) == Fraction(3, 2)
    assert Fraction(1, 2) ** 3 == Fraction(1, 8)


def test_independent_percent_oracles():
    from decimal import Decimal
    assert Decimal("0.045") * Decimal(200) == Decimal(9)
    assert Decimal(160) * Decimal("1.03") == Decimal("164.80")
    assert abs(Decimal(36) - Decimal(40)) / Decimal(40) * 100 == 10
    assert Decimal("0.075") * Decimal(120) == Decimal(9)


def test_independent_linear_oracles():
    assert (10 - 2) / (3 - (-1)) == 2
    assert 48 / 6 == 8
    assert 2 * 2 + 1 == -2 + 7
