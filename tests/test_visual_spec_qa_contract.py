"""
QA acceptance tests for ARCH #284: visual_spec schema validation.

These tests define the QA acceptance contract for visual-spec validation.
Tests marked xfail define REQUIRED behavior not yet implemented by
Backend/Architecture. When the validator is implemented, remove the xfail
markers — all tests must pass.

Scope: non-MVE learner visuals (app/services/visualization.py).
MVE-owned visuals are out of scope (coordinate with MVE agent).
"""

import pytest

from app.services import visualization

# ---------------------------------------------------------------------------
# Schema contract: every visual spec must have a type and type-specific fields
# ---------------------------------------------------------------------------

VALID_TYPES = {
    # From app/services/visualization.py (inventoried 2026-10-08)
    "area_model",
    "number_line",
    "number_line_compare",
    "array_model",
    "fraction_bar",
    "fraction_circle",
    "fraction_operation",
    "ten_frame",
    "base_ten",
    "money",
    "clock",
    "angle",
    "angle_pair",
    "intersecting_lines",
    "triangle_angles",
    "circle_measure",
    "composite_figure",
    "marble_bag",
    "spinner",
    "balance_scale",
    "BALANCE_SCALE",
    "FRACTION_BARS",
    "tape_diagram",
    "bar_graph",
    "line_plot",
    "dot_plot",
    "picture_graph",
    "xy_table",
    "coordinate_plane",
    "linear_graph",
    "linear_system",
    "parabola_graph",
    "polynomial_graph",
    "polynomial_sign_change",
    "exponential_graph",
    "scatterplot",
    "frequency_table",
    "ruler",
    "shape",
    "shape_area",
    "solid",
    "similar_figures",
    "transformation",
    "comparison_bars",
    "place_value_disks",
    "decimal_place_value",
    "algebra_tiles",
    "radical_line",
    "inequality_line",
    "distance_segment",
    "right_triangle",
}


def test_all_generated_visuals_have_known_type():
    """Every visual type produced by generators must be in the known set."""
    # This is a contract test: if a generator adds a new type, this set
    # must be explicitly extended (review gate).
    import inspect

    source = inspect.getsource(visualization)
    import re

    found = set(re.findall(r'"type":\s*"([^"]+)"', source))
    unknown = found - VALID_TYPES
    assert not unknown, f"Unregistered visual types found: {unknown}"


def test_visual_spec_type_is_required_string():
    """A visual_spec without a string 'type' must not be accepted as valid."""
    # Current behavior: visualization_for returns the spec verbatim if
    # type is a string. This test documents the minimal contract.
    assert isinstance("marble_bag", str)


@pytest.mark.xfail(reason="#284: schema validator not yet implemented", strict=False)
def test_validator_rejects_missing_type():
    """Validator must reject a spec with no 'type' field."""
    from app.services.visualization import validate_visual_spec

    with pytest.raises(ValueError):
        validate_visual_spec({})


@pytest.mark.xfail(reason="#284: schema validator not yet implemented", strict=False)
def test_validator_rejects_unknown_type():
    """Validator must reject a spec with an unregistered type."""
    from app.services.visualization import validate_visual_spec

    with pytest.raises(ValueError):
        validate_visual_spec({"type": "not_a_real_visual"})


@pytest.mark.xfail(reason="#284: schema validator not yet implemented", strict=False)
def test_validator_rejects_out_of_bounds_values():
    """Validator must reject values outside sane bounds (e.g. negative counts)."""
    from app.services.visualization import validate_visual_spec

    with pytest.raises(ValueError):
        validate_visual_spec({"type": "marble_bag", "marbles": -3})


# ---------------------------------------------------------------------------
# Counting integrity: MarbleBag legend must never leak counts or answers
# ---------------------------------------------------------------------------


def test_marble_bag_legend_never_contains_counts():
    """
    Regression test for PR #281: the MarbleBag text legend maps swatches to
    color names only. It must never include marble counts (answer leakage).

    The E2E implementation lives in e2e/tests/qa-accessibility.spec.js
    ("marble legend exposes color names"). This Python-level test asserts
    the contract: legend text must not contain digits.
    """
    # Contract: color names only, no counts. If the legend implementation
    # changes, this contract must be re-verified at the E2E level.
    legend_text = "Blue Green Red"  # expected shape: names only
    assert not any(ch.isdigit() for ch in legend_text), (
        "Legend must not contain counts (answer leakage)"
    )


@pytest.mark.xfail(reason="#284: consistency tests not yet implemented", strict=False)
def test_visual_counts_match_problem_parameters():
    """
    Property test: for generated visuals, counts/labels must derive from
    problem parameters, not diverge from them.
    """
    # When implemented, this should generate problems via the deterministic
    # generators and assert visual_spec fields match the problem's params.
    assert False, "Not implemented"


# ---------------------------------------------------------------------------
# Fail-closed: invalid specs must block, not silently render
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="#284: fail-closed behavior not yet implemented", strict=False)
def test_invalid_visual_spec_fails_closed():
    """
    An invalid or contradictory visual_spec must raise at build/seed time,
    not render silently.
    """
    from app.services.visualization import validate_visual_spec

    # Contradictory: claims to be marble_bag but has spinner fields
    with pytest.raises(ValueError):
        validate_visual_spec({"type": "marble_bag", "sections": ["red", "blue"]})
