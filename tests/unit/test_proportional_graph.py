"""PROPORTIONAL_GRAPH generator: proportional-table recognition,
context scaling, the constant of proportionality from tables and
graphs, y = kx equations, the (1, r) point, and misconception rules."""

import random
from fractions import Fraction
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(1500):
        generated = GENERATORS["PROPORTIONAL_GRAPH"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no PROPORTIONAL_GRAPH/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _correct_text(generated) -> str:
    return next(
        c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
    )


def test_low_difficulty_only_identifies_and_scales() -> None:
    for seed in range(200):
        generated = GENERATORS["PROPORTIONAL_GRAPH"](random.Random(seed), 1)
        assert generated.parameters["tier"] in {"identify_table", "solve_proportion"}


def test_identify_table_verdict_matches_the_ratios() -> None:
    for _ in range(150):
        generated = _gen("identify_table", difficulty=1)
        pairs = generated.parameters["pairs"]
        ratios = {Fraction(y, x) for x, y in pairs}
        proportional = len(ratios) == 1 and pairs[0][0] != 0
        # Shifted lines have constant differences but are not proportional.
        diffs = {pairs[i + 1][1] - pairs[i][1] for i in range(len(pairs) - 1)}
        assert _correct_text(generated).startswith("Yes") == proportional
        if not proportional:
            assert len(diffs) == 1  # the constant-rate trap
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "xy_table"


def test_solve_proportion_scales_cleanly() -> None:
    for _ in range(120):
        generated = _gen("solve_proportion", difficulty=1)
        p = generated.parameters
        assert int(generated.canonical_answer) == p["a"] * p["scale"]
        assert p["b"] % p["a"] == 0
        assert visualization_for(_as_problem(generated)) is None


def test_find_k_matches_the_table_ratio() -> None:
    for _ in range(150):
        generated = _gen("find_k", difficulty=2)
        pairs = generated.parameters["pairs"]
        x1, y1 = pairs[0]
        k = Fraction(y1, x1)
        assert all(Fraction(y, x) == k for x, y in pairs)
        assert Fraction(generated.canonical_answer) == k
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "xy_table"


def test_graph_k_matches_the_drawn_slope() -> None:
    for _ in range(120):
        generated = _gen("graph_k", difficulty=2)
        p = generated.parameters
        k = Fraction(p["m_num"], p["m_den"])
        assert Fraction(generated.canonical_answer) == k
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "linear_graph"
        assert spec["b"] == 0  # through the origin by definition


def test_write_equation_is_multiplicative() -> None:
    for _ in range(150):
        generated = _gen("write_equation", difficulty=3)
        pairs = generated.parameters["pairs"]
        k = Fraction(pairs[0][1], pairs[0][0])
        correct = _correct_text(generated)
        assert "+" not in correct  # no intercept — through the origin
        assert f"y = ({k})x" == correct or f"y = {k}x" == correct
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        assert any(v == "PROP_003" for v in tags.values())
        assert visualization_for(_as_problem(generated))["type"] == "xy_table"


def test_unit_point_interprets_one_comma_r() -> None:
    for _ in range(60):
        generated = _gen("unit_point", difficulty=3)
        r = generated.parameters["r"]
        correct = _correct_text(generated)
        assert "unit rate" in correct and str(r) in correct
        assert generated.parameters["y_label"] in correct
        tags = {c.get("misconception_code") for c in generated.choices}
        assert "PROP_004" in tags
        assert visualization_for(_as_problem(generated)) is None


def test_find_k_flags_inverted_and_additive_answers() -> None:
    prompt = ("The table shows a proportional relationship with the "
              "values (2, 6), (4, 12), (6, 18). "
              "What is the constant of proportionality?")
    assert evaluate_problem(prompt, "1/3", "3").misconception_code == "PROP_002"
    assert evaluate_problem(prompt, "4", "3").misconception_code == "PROP_003"
    assert evaluate_problem(prompt, "3", "3").correct
    assert evaluate_problem(prompt, "2", "3").misconception_code is None
