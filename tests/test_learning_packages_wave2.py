"""Structural review gates and independent sample mathematical oracles.

Run pytest -q tests/test_learning_packages_wave2.py
These checks do NOT constitute full math, curriculum, or QA approval.
"""
import json
from fractions import Fraction
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "docs/curriculum/drafts/learning-packages-wave2/content.draft.json"


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_review_gates_and_content_depth():
    manifest = load()
    assert manifest["status"] == "DRAFT_UNVERIFIED"
    assert manifest["runtime_activation"] is False
    assert manifest["mastery_writes"] is False
    packages = manifest["packages"]
    assert len(packages) == 6
    assert len({p["id"] for p in packages}) == len(packages)
    for package in packages:
        assert package["status"] == "DRAFT_UNVERIFIED"
        assert package["runtime_activation"] is False
        assert package["mastery_writes"] is False
        assert package["standards_mapping"] == "PROVISIONAL_NOT_ACCEPTED"
        assert package["mathematical_review"] == "PENDING"
        assert package["qa"] == "PENDING"
        assert len(package["worked_examples"]) >= 5
        assert len(package["misconception_pathways"]) >= 3
        assert len(package["guided_practice"]) >= 4
        assert len(package["independent_assessment"]) >= 3
        assert len(package["lesson_sequence"]) >= 5
        assert len(package["diagnostic"]) >= 2
        assert package["interactive_spec"]["accessibility"]
        assert package["interactive_spec"]["assessment"]
        for misconception in package["misconception_pathways"]:
            assert len(misconception["hints"]) >= 2
        for item in package["independent_assessment"]:
            assert item["hints_allowed"] is False
            assert item["feedback_after_submission"] is True


def test_independent_early_arithmetic_and_decimal():
    assert 16 - 9 == 7
    assert 18 - 11 == 7
    assert Fraction(7, 20) == Fraction(35, 100)
    assert Fraction(740, 1000) > Fraction(704, 1000)
    assert Fraction(5, 2) - Fraction(85, 100) == Fraction(165, 100)


def test_independent_ratio_and_quartile():
    assert Fraction(21, 7) * 5 == 15
    assert Fraction(12, 1) / Fraction(3, 2) == 8
    assert Fraction(18, 2) == 9
    ordered = [2, 4, 6, 8, 10, 12, 14, 16]
    assert Fraction(ordered[3] + ordered[4], 2) == 9
    assert 11 - 5 == 6


def test_independent_nets_area_and_quadratics():
    assert 6 * 4**2 == 96
    assert 6 * 5**2 == 150
    assert Fraction(6) * Fraction(1, 2)**2 == Fraction(3, 2)
    assert (4 + 2) * (4 + 5) == 4**2 + 7 * 4 + 10
    assert (-5)**2 - 25 == 0
    assert 5**2 - 25 == 0
    assert (3 + 4, 3 * 4) == (7, 12)
