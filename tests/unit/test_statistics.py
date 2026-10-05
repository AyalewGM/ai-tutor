"""STATISTICS generator: associations, outliers, best-fit predictions and
the scatterplot visual spec — plus the dropped-intercept misconception."""

import random
from fractions import Fraction
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(1200):
        generated = GENERATORS["STATISTICS"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no STATISTICS/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def test_low_difficulty_only_reads_association() -> None:
    for seed in range(200):
        generated = GENERATORS["STATISTICS"](random.Random(seed), 1)
        assert generated.parameters["tier"] == "association"


def test_clouds_stay_on_the_grid() -> None:
    for _ in range(150):
        generated = _gen("association", difficulty=1)
        for x, y in generated.parameters["points"]:
            assert 0 <= x <= 10
            assert 0 <= y <= 10


def test_association_answer_matches_cloud() -> None:
    for _ in range(120):
        generated = _gen("association", difficulty=1)
        points = generated.parameters["points"]
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        trend = (xs[-1] - xs[0]) and (ys[-1] - ys[0]) / (xs[-1] - xs[0])
        if correct == "a positive association":
            assert ys[-1] > ys[0] and trend > 0
        elif correct == "a negative association":
            assert ys[-1] < ys[0] and trend < 0
        else:
            assert correct in {"no association", "a curved (nonlinear) association"}


def test_outlier_is_off_pattern_and_the_decoy_is_extreme() -> None:
    for _ in range(80):
        generated = _gen("outlier", difficulty=2)
        points = generated.parameters["points"]
        outlier = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        coords = {tuple(p) for p in points}
        ox, oy = (int(v) for v in outlier.strip("()").split(","))
        assert (ox, oy) in coords
        # Every other point stays within ±1 of the line through the
        # cloud's first and last x-sorted points, while the outlier does not.
        on_pattern = sorted(p for p in points if [p[0], p[1]] != [ox, oy])
        x1, y1 = on_pattern[0]
        x2, y2 = on_pattern[-1]
        m = Fraction(y2 - y1, x2 - x1)
        b = y1 - m * x1
        assert abs(m * ox + b - oy) > 1.5
        decoys = {c["text"]: c.get("misconception_code") for c in generated.choices}
        stat003 = [t for t, code in decoys.items() if code == "STAT_003"]
        assert len(stat003) == 1


def test_predict_matches_the_stated_equation() -> None:
    for _ in range(80):
        generated = _gen("predict", difficulty=3)
        fit = generated.parameters["fit"]
        m = Fraction(fit["m_num"], fit["m_den"])
        b = fit["i_num"]
        x_q = int(generated.prompt.rsplit("x = ", 1)[1].rstrip("."))
        assert int(generated.canonical_answer) == m * x_q + b


def test_predict_renders_the_fit_but_best_fit_line_does_not() -> None:
    predict = _gen("predict", difficulty=3)
    spec = visualization_for(_as_problem(predict))
    assert spec is not None and spec["type"] == "scatterplot"
    assert "fit" in spec
    best_fit = _gen("best_fit_line", difficulty=3)
    spec = visualization_for(_as_problem(best_fit))
    assert spec is not None and "fit" not in spec


def test_correlation_causation_tags_causation_distractors() -> None:
    generated = _gen("correlation_causation", difficulty=4)
    tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
    causation = [t for t in tags if "directly cause" in t]
    assert len(causation) == 2
    assert all(tags[t] == "STAT_002" for t in causation)


def test_dropped_intercept_flags_stat_004() -> None:
    prompt = (
        "The scatterplot shows data with the line of best fit y = 2x + 1. "
        "Use it to predict y when x = 3."
    )
    assert evaluate_problem(prompt, "6", "7").misconception_code == "STAT_004"
    assert evaluate_problem(prompt, "5", "7").misconception_code == "STAT_004"
    assert evaluate_problem(prompt, "7", "7").correct
    assert evaluate_problem(prompt, "8", "7").misconception_code is None
