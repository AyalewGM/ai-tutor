"""FUNCTIONS generator: relation classification, rate of change from
tables and graphs, linear vs nonlinear, comparing representations,
building y = mx + b, and the function misconception rules."""

import random
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(1500):
        generated = GENERATORS["FUNCTIONS"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no FUNCTIONS/{tier} at difficulty {difficulty}")


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


def test_low_difficulty_only_classifies_and_rates() -> None:
    for seed in range(200):
        generated = GENERATORS["FUNCTIONS"](random.Random(seed), 1)
        assert generated.parameters["tier"] in {"is_function", "rate_table"}


def test_is_function_verdict_matches_the_pairs() -> None:
    for _ in range(150):
        generated = _gen("is_function", difficulty=1)
        pairs = generated.parameters["pairs"]
        xs = [x for x, _ in pairs]
        is_fn = len(set(xs)) == len(xs)
        assert _correct_text(generated).startswith("Yes") == is_fn
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "xy_table"
        assert spec["pairs"] == pairs


def test_rate_table_answer_is_the_slope() -> None:
    for _ in range(120):
        generated = _gen("rate_table", difficulty=1)
        p = generated.parameters
        pairs = p["pairs"]
        dx = pairs[1][0] - pairs[0][0]
        dy = pairs[1][1] - pairs[0][1]
        assert dx != 0 and dy % dx == 0
        assert int(generated.canonical_answer) == dy // dx == p["m"]
        # Every pair is collinear with the stated slope and intercept.
        assert all(y == p["m"] * x + p["b"] for x, y in pairs)
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "xy_table"


def test_linear_or_not_verdict_is_correct() -> None:
    for _ in range(150):
        generated = _gen("linear_or_not", difficulty=2)
        p = generated.parameters
        correct = _correct_text(generated)
        if p["form"] == "table":
            pairs = p["pairs"]
            diffs = {
                pairs[i + 1][1] - pairs[i][1] for i in range(len(pairs) - 1)
            }
            assert correct.startswith("Linear") == (len(diffs) == 1)
        else:
            linear = "x²" not in p["equation"] and "x³" not in p["equation"]
            assert correct.startswith("Linear") == linear
        tags = {c.get("misconception_code") for c in generated.choices}
        assert "FUNC_002" in tags


def test_graph_rate_matches_the_drawn_slope() -> None:
    for _ in range(120):
        generated = _gen("graph_rate", difficulty=2)
        p = generated.parameters
        assert int(generated.canonical_answer) == p["m_num"]
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "linear_graph"
        assert spec["m_num"] == p["m_num"] and spec["b"] == p["b"]


def test_compare_rates_picks_the_steeper_function() -> None:
    for _ in range(120):
        generated = _gen("compare_rates", difficulty=3)
        p = generated.parameters
        pairs = p["pairs"]
        m2 = (pairs[1][1] - pairs[0][1]) // (pairs[1][0] - pairs[0][0])
        assert m2 == p["m2"]
        correct = _correct_text(generated)
        if p["m1"] > m2:
            assert correct == "Function A"
        elif m2 > p["m1"]:
            assert correct == "Function B"
        else:
            assert correct == "They have the same rate of change"


def test_build_function_matches_the_situation() -> None:
    for _ in range(120):
        generated = _gen("build_function", difficulty=3)
        p = generated.parameters
        correct = _correct_text(generated)
        assert str(p["start"]) in correct and str(p["rate"]) in correct
        if p["decreasing"]:
            assert correct == f"y = {p['start']} − {p['rate']}m"
        else:
            assert correct == f"y = {p['rate']}m + {p['start']}"
        # The swap distractor always carries FUNC_003.
        tags = {c.get("misconception_code") for c in generated.choices}
        assert "FUNC_003" in tags


def test_rate_table_flags_inverted_and_intercept_answers() -> None:
    prompt = ("A function has the values (1, 3), (2, 7), (3, 11). "
              "What is its rate of change?")
    # y ÷ x on the first row (3/1 = 3) is the wrong-ratio error.
    assert evaluate_problem(prompt, "3", "4").misconception_code == "FUNC_004"
    # The y-intercept (−1) is not the rate.
    assert evaluate_problem(prompt, "-1", "4").misconception_code == "FUNC_002"
    assert evaluate_problem(prompt, "4", "4").correct
    assert evaluate_problem(prompt, "5", "4").misconception_code is None
