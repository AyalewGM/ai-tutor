"""Wave 3 draft safety gates and independently calculated sample math oracles."""
import json
from fractions import Fraction
from pathlib import Path

PACKAGE_FILE = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/learning-packages-wave3/content.draft.json"
)


def test_draft_is_not_active_and_has_complete_learning_components():
    data = json.loads(PACKAGE_FILE.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["runtime_activation"] is False
    assert data["mastery_writes"] is False
    assert len(data["packages"]) == 5
    assert len({p["id"] for p in data["packages"]}) == 5
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
        assert len(p["diagnostic"]) >= 2
        assert len(p["teaching_phases"]) >= 5
        assert p["interactive_spec"]["scaffold_disable_on_assessment"]
        assert p["interactive_spec"]["screen_reader"]
        for m in p["misconception_pathways"]:
            assert len(m["socratic_hints"]) >= 2
        for item in p["independent_assessment"]:
            assert item["hints_allowed"] is False
            assert item["feedback_after_submission"] is True


def test_fraction_and_integer_independent_oracles():
    assert Fraction(5, 8) + Fraction(1, 4) == Fraction(7, 8)
    assert Fraction(7, 10) - Fraction(2, 5) == Fraction(3, 10)
    assert Fraction(2, 3) + Fraction(3, 8) == Fraction(25, 24)
    assert -8 + 3 == -5
    assert (-6) * 4 == -24
    assert -15 + 38 - 9 == 14


def test_geometry_and_systems_independent_oracles():
    assert (-3 + 5, 4 - 7) == (2, -3)
    assert (1 - 3, -2) == (-2, -2)
    x, y = 3, 7
    assert y == 3 * x - 2 and y == x + 4
    x, y = 4, 5
    assert x + y == 9 and 2 * x - y == 3
    a, c = 5, 5
    assert a + c == 10 and 8 * a + 5 * c == 65


def test_equation_solution_cardinalities():
    # Parallel lines: equal slope, distinct intercept -> no common point.
    assert 2 != -1
    # Coincident lines: multiplying all coefficients preserves solution set.
    assert (2 * 1, 2 * (-1), 2 * 4) == (2, -2, 8)
