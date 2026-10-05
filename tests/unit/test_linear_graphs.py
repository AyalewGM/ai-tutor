"""LINEAR_GRAPH + upgraded COORDINATE_PLANE generators: canonical answers,
distractor misconception tags, grid bounds and visual specs."""

import random
from fractions import Fraction
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _as_problem(generated) -> SimpleNamespace:
    """visualization_for reads solution.parameters off a persisted Problem."""
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _gen(problem_type: str, tier: str, *, difficulty: int) -> object:
    for seed in range(400):
        generated = GENERATORS[problem_type](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no {problem_type}/{tier} generated at difficulty {difficulty}")


def test_read_slope_and_intercept_match_the_line() -> None:
    slope_problem = _gen("LINEAR_GRAPH", "read_slope", difficulty=3)
    params = slope_problem.parameters
    assert Fraction(params["m_num"], params["m_den"]) == Fraction(
        slope_problem.canonical_answer
    )
    assert slope_problem.answer_kind == "FRACTION"
    assert visualization_for(_as_problem(slope_problem))["type"] == "linear_graph"

    intercept_problem = _gen("LINEAR_GRAPH", "read_intercept", difficulty=3)
    assert intercept_problem.canonical_answer == str(
        intercept_problem.parameters["b"]
    )


def test_read_value_and_point_stay_on_the_grid() -> None:
    for tier in ("read_value", "point_on_line"):
        for seed in range(300):
            generated = GENERATORS["LINEAR_GRAPH"](random.Random(seed), 5)
            params = generated.parameters
            if params.get("tier") != tier:
                continue
            x = params["x"]
            y = Fraction(params["m_num"], params["m_den"]) * x + params["b"]
            assert abs(x) <= 9 and abs(y) <= 9
            if tier == "read_value":
                assert generated.canonical_answer == str(int(y))


def test_point_on_line_distractors_are_tagged() -> None:
    generated = _gen("LINEAR_GRAPH", "point_on_line", difficulty=4)
    params = generated.parameters
    correct = next(c for c in generated.choices if c["id"] == generated.canonical_answer)
    x, y = (int(v) for v in correct["text"].strip("()").split(","))
    assert y == params["m_num"] / params["m_den"] * x + params["b"]
    codes = {
        c["misconception_code"] for c in generated.choices if "misconception_code" in c
    }
    assert "COORDINATE_ORDER_SWAP" in codes


def test_write_equation_distractors_cover_all_three_misconceptions() -> None:
    generated = _gen("LINEAR_GRAPH", "write_equation", difficulty=6)
    codes = {
        c["misconception_code"] for c in generated.choices if "misconception_code" in c
    }
    assert codes == {"REL_001", "GR_002", "GR_003"}
    correct = next(c for c in generated.choices if c["id"] == generated.canonical_answer)
    assert evaluate_problem(
        generated.prompt, correct["id"], generated.canonical_answer,
        answer_kind="MULTIPLE_CHOICE", choices=generated.choices,
    ).correct


def test_slope_misconception_rules() -> None:
    prompt = "What is the slope of the line shown?"
    flipped = evaluate_problem(
        prompt, "-2/3", "2/3", answer_kind="FRACTION"
    )
    assert not flipped.correct and flipped.misconception_code == "GR_002"
    inverted = evaluate_problem(
        prompt, "3/2", "2/3", answer_kind="FRACTION"
    )
    assert not inverted.correct and inverted.misconception_code == "GR_001"
    assert evaluate_problem(
        prompt, "4/6", "2/3", answer_kind="FRACTION"
    ).correct


def test_coordinate_plane_asks_real_reads() -> None:
    read = _gen("COORDINATE_PLANE", "read_point", difficulty=2)
    assert "(" not in read.prompt
    assert read.parameters["labeled"] is False
    assert evaluate_problem(read.prompt, read.canonical_answer, read.canonical_answer).correct
    quadrant = _gen("COORDINATE_PLANE", "quadrant", difficulty=3)
    assert quadrant.answer_kind == "MULTIPLE_CHOICE"
    assert len(quadrant.choices) == 4


def test_linear_graph_visual_carries_renderable_geometry() -> None:
    generated = GENERATORS["LINEAR_GRAPH"](random.Random(5), 3)
    visual = visualization_for(_as_problem(generated))
    assert visual["type"] == "linear_graph"
    assert {"m_num", "m_den", "b"} <= set(visual)
    point = GENERATORS["COORDINATE_PLANE"](random.Random(5), 3)
    cp_visual = visualization_for(_as_problem(point))
    assert cp_visual["type"] == "coordinate_plane"
    assert cp_visual["labeled"] is False
