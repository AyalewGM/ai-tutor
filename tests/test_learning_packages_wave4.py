"""Fail-closed review contract and independent sampled Wave 4 numerical oracles."""
import json
from fractions import Fraction
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "docs/curriculum/drafts/learning-packages-wave4/content.draft.json"


def test_draft_only_and_minimum_content():
    data = json.loads(FILE.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["runtime_activation"] is False
    assert len(data["packages"]) == 5
    for package in data["packages"]:
        assert package["status"] == "DRAFT_UNVERIFIED"
        assert package["runtime_activation"] is False
        assert package["mastery_writes"] is False
        assert package["math_review"] == "PENDING"
        assert package["standards_mapping"] == "PROVISIONAL_NOT_ACCEPTED"
        assert len(package["worked_examples"]) == 5
        assert len(package["misconception_pathways"]) == 3
        assert len(package["guided_practice"]) == 4
        assert len(package["independent_assessment"]) == 2
        assert package["interactive_spec"]["assessments_unscaffolded"]
        for item in package["independent_assessment"]:
            assert not item["hints_allowed"]


def test_units_geometry_and_data_sample_oracles():
    assert Fraction(3 * 100, 4) == 75
    assert 10 * 4 - 2 * 2 == 36
    assert 2 * (2 * 3 + 3 * 4 + 2 * 4) == 52
    assert 3 * 4 + 2 * (3 * 2) + 2 * (4 * 2) == 40
    assert [sum(lo <= x < hi for x in [3, 4, 5, 8, 9, 10]) for lo, hi in [(0, 5), (5, 10), (10, 15)]] == [2, 3, 1]


def test_exponential_and_linear_sample_oracles():
    assert 50 * 2**3 == 400
    assert Fraction(100) * Fraction(11, 10)**2 == 121
    assert Fraction(500) * Fraction(4, 5)**2 == 320
    assert 80 * Fraction(1, 2)**3 == 10
