"""POLYNOMIAL_FUNCTION generator: tiers, canonical answers, distractor tags,
grid bounds and the polynomial graph visual spec."""

import random
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS, _poly_expand, _poly_val
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(400):
        generated = GENERATORS["POLYNOMIAL_FUNCTION"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no POLYNOMIAL_FUNCTION/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def test_expand_matches_roots() -> None:
    # (x-1)(x+2)(x-3) = x^3 - 2x^2 - 5x + 6... verified term by term below.
    assert _poly_expand(1, [1, -2, 3]) == [1, -2, -5, 6]
    assert _poly_expand(1, [2]) == [1, -2]
    assert _poly_expand(-1, [0, 2]) == [-1, 2, 0]


def test_evaluate_answer_matches_coeffs() -> None:
    for seed in range(200):
        generated = GENERATORS["POLYNOMIAL_FUNCTION"](random.Random(seed), 2)
        p = generated.parameters
        if p["tier"] != "evaluate":
            continue
        x_val = int(generated.prompt.split("p(")[-1].rstrip(")?"))
        expected = int(_poly_val(p["coeffs"], x_val))
        assert generated.canonical_answer == str(expected)
        assert evaluate_problem(
            generated.prompt, generated.canonical_answer, generated.canonical_answer
        ).correct


def test_degree_answer_and_distractors() -> None:
    for seed in range(300):
        generated = GENERATORS["POLYNOMIAL_FUNCTION"](random.Random(seed), 2)
        p = generated.parameters
        if p["tier"] != "degree":
            continue
        correct = next(
            c for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert correct["text"] == str(len(p["coeffs"]) - 1)
        assert any(
            c.get("misconception_code") == "POLY_003" for c in generated.choices
        )


def test_zeros_from_factors_lists_roots() -> None:
    generated = _gen("zeros_from_factors", difficulty=3)
    p = generated.parameters
    correct = next(c for c in generated.choices if c["id"] == generated.canonical_answer)
    for r in sorted(p["roots"]):
        assert f"x = {r}" in correct["text"]
    codes = {c.get("misconception_code") for c in generated.choices}
    assert "POLY_001" in codes


def test_count_roots_matches_root_count() -> None:
    for seed in range(300):
        generated = GENERATORS["POLYNOMIAL_FUNCTION"](random.Random(seed), 3)
        p = generated.parameters
        if p["tier"] != "count_roots":
            continue
        correct = next(
            c for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert correct["text"] == str(len(p["roots"]))
        # coeffs and roots describe the same curve.
        assert _poly_expand(p["a"], p["roots"]) == p["coeffs"]


def test_end_behavior_matches_degree_and_sign() -> None:
    for seed in range(300):
        generated = GENERATORS["POLYNOMIAL_FUNCTION"](random.Random(seed), 4)
        p = generated.parameters
        if p["tier"] != "end_behavior":
            continue
        even = (len(p["coeffs"]) - 1) % 2 == 0
        up = p["coeffs"][0] > 0
        correct = next(
            c for c in generated.choices if c["id"] == generated.canonical_answer
        )
        expected = {
            (True, True): "Rises to the left and rises to the right",
            (True, False): "Falls to the left and falls to the right",
            (False, True): "Falls to the left and rises to the right",
            (False, False): "Rises to the left and falls to the right",
        }[(even, up)]
        assert correct["text"] == expected
        assert any(
            c.get("misconception_code") == "POLY_002" for c in generated.choices
        )


def test_write_equation_is_factored_form() -> None:
    generated = _gen("write_equation", difficulty=5)
    correct = next(c for c in generated.choices if c["id"] == generated.canonical_answer)
    assert correct["text"].startswith("y=")
    assert "(x" in correct["text"]
    codes = {c.get("misconception_code") for c in generated.choices}
    assert "POLY_001" in codes


def test_polynomial_visual_spec_graph_tiers_only() -> None:
    graphed = _gen("count_roots", difficulty=3)
    visual = visualization_for(_as_problem(graphed))
    assert visual["type"] == "polynomial_graph"
    assert visual["coeffs"] == graphed.parameters["coeffs"]
    assert visual["mark_roots"] is False

    matched = _gen("write_equation", difficulty=5)
    visual = visualization_for(_as_problem(matched))
    assert visual["type"] == "polynomial_graph"
    assert visual["mark_roots"] is True
    assert visual["roots"] == matched.parameters["roots"]

    text_only = _gen("evaluate", difficulty=2)
    assert visualization_for(_as_problem(text_only)) is None


def test_curve_extrema_stay_on_the_grid() -> None:
    for seed in range(200):
        generated = GENERATORS["POLYNOMIAL_FUNCTION"](random.Random(seed), 5)
        p = generated.parameters
        if p["tier"] not in {"count_roots", "write_equation"}:
            continue
        roots = p["roots"]
        lo, hi = roots[0] - 1.2, roots[-1] + 1.2
        i = 0
        while lo + i * 0.02 <= hi + 1e-9:
            assert abs(_poly_val(p["coeffs"], lo + i * 0.02)) <= 9
            i += 1
        assert all(-9 <= r <= 9 for r in roots)
