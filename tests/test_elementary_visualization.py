from app.models import Problem
from app.services.visualization import visualization_for


def _problem(problem_type, parameters):
    return Problem(
        primary_skill_id=None,
        problem_type=problem_type,
        difficulty=1,
        prompt="Synthetic elementary visual fixture",
        canonical_answer="12",
        solution={"parameters": parameters},
    )


def test_equal_groups_array_is_deterministic_and_answer_consistent():
    problem = _problem("EQUAL_GROUPS", {"rows": 3, "columns": 4})
    spec = visualization_for(problem)
    assert spec == {
        "type": "array_model",
        "rows": 3,
        "columns": 4,
        "mode": "counters",
        "aria_label": "Array with 3 rows and 4 columns, showing 12 items in all.",
    }
    assert spec["rows"] * spec["columns"] == int(problem.canonical_answer)


def test_rectangle_area_uses_unit_squares():
    problem = _problem("RECTANGLE_AREA", {"rows": 2, "columns": 6})
    spec = visualization_for(problem)
    assert spec["type"] == "array_model"
    assert spec["mode"] == "squares"
    assert spec["rows"] * spec["columns"] == int(problem.canonical_answer)


def test_unit_fraction_bar_uses_stored_math_state():
    problem = _problem("UNIT_FRACTION", {"numerator": 1, "denominator": 4})
    problem.canonical_answer = "1/4"
    spec = visualization_for(problem)
    assert spec["type"] == "fraction_bar"
    assert spec["numerator"] == 1
    assert spec["denominator"] == 4
    assert "4 equal parts" in spec["aria_label"]


def test_bar_graph_read_visualizes_category_value():
    problem = _problem("BAR_GRAPH_READ", {"category": "blue", "value": 7, "total": 20})
    spec = visualization_for(problem)
    assert spec["type"] == "bar_graph"
    assert spec["category"] == "blue"
    assert spec["value"] == 7
    assert "blue" in spec["aria_label"]
    assert "7" in spec["aria_label"]


def test_picture_graph_read_visualizes_category_value():
    problem = _problem("PICTURE_GRAPH_READ", {"category": "dog", "value": 5, "total": 14})
    spec = visualization_for(problem)
    assert spec["type"] == "picture_graph"
    assert spec["category"] == "dog"
    assert spec["value"] == 5
    assert "dog" in spec["aria_label"]


def test_visual_specs_include_accessibility_metadata():
    """Every returned visual spec must carry non-color descriptive metadata."""
    specs = [
        visualization_for(_problem("EQUAL_GROUPS", {"rows": 3, "columns": 4})),
        visualization_for(_problem("BAR_GRAPH_READ", {"category": "blue", "value": 7, "total": 20})),
        visualization_for(_problem("PICTURE_GRAPH_READ", {"category": "dog", "value": 5, "total": 14})),
        visualization_for(_problem("UNIT_FRACTION", {"numerator": 1, "denominator": 4})),
    ]
    for spec in specs:
        assert spec is not None
        assert "aria_label" in spec
        assert isinstance(spec["aria_label"], str)
        assert len(spec["aria_label"]) > 0


def test_invalid_elementary_visual_fails_closed():
    assert visualization_for(_problem("EQUAL_GROUPS", {"rows": 50, "columns": 2})) is None
    assert visualization_for(_problem("UNIT_FRACTION", {"numerator": 3, "denominator": 2})) is None
