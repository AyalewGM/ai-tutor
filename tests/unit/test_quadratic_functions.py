"""QUADRATIC_FUNCTION generator: tiers, canonical answers, distractor tags,
grid bounds and the parabola visual spec."""

import random
from fractions import Fraction
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(400):
        generated = GENERATORS["QUADRATIC_FUNCTION"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no QUADRATIC_FUNCTION/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _a(params) -> Fraction:
    return Fraction(params["a_num"], params["a_den"])


def test_evaluate_matches_vertex_params_in_standard_form() -> None:
    for seed in range(200):
        generated = GENERATORS["QUADRATIC_FUNCTION"](random.Random(seed), 3)
        p = generated.parameters
        if p["tier"] != "evaluate":
            continue
        # prompt embeds standard form; params carry vertex form — verify
        # they describe the same parabola and the answer matches.
        x_val = int(generated.prompt.split("f(")[-1].rstrip(")?"))
        expected = p["a_num"] * (x_val - p["h"]) ** 2 + p["a_den"] * p["k"]
        assert expected % p["a_den"] == 0
        assert generated.canonical_answer == str(expected // p["a_den"])


def test_opens_direction_and_root_count_are_correct() -> None:
    for seed in range(200):
        generated = GENERATORS["QUADRATIC_FUNCTION"](random.Random(seed), 4)
        p = generated.parameters
        if not generated.choices:
            continue
        correct = next(
            c for c in generated.choices if c["id"] == generated.canonical_answer
        )
        a = _a(p)
        if p["tier"] == "opens_direction":
            assert correct["text"] == ("Upward" if a > 0 else "Downward")
            assert any(
                c.get("misconception_code") == "QUAD_002" for c in generated.choices
            )
        elif p["tier"] == "count_roots":
            expected = 1 if p["k"] == 0 else (2 if (a > 0) == (p["k"] < 0) else 0)
            assert correct["text"] == str(expected)


def test_vertex_answer_matches_params() -> None:
    generated = _gen("vertex", difficulty=3)
    p = generated.parameters
    assert generated.canonical_answer == f'({p["h"]}, {p["k"]})'
    assert evaluate_problem(
        generated.prompt, generated.canonical_answer, generated.canonical_answer
    ).correct


def test_axis_of_symmetry_is_x_equals_h() -> None:
    generated = _gen("axis_of_symmetry", difficulty=5)
    correct = next(c for c in generated.choices if c["id"] == generated.canonical_answer)
    assert correct["text"] == f'x={generated.parameters["h"]}'


def test_write_equation_is_vertex_form_with_tagged_distractors() -> None:
    generated = _gen("write_equation", difficulty=6)
    p = generated.parameters
    correct = next(c for c in generated.choices if c["id"] == generated.canonical_answer)
    h, k = p["h"], p["k"]
    assert f"(x{'+' if h < 0 else '-'}{abs(h)})^2" in correct["text"] or h == 0
    assert str(abs(k)) in correct["text"] or k == 0
    codes = {c.get("misconception_code") for c in generated.choices}
    assert {"QUAD_001", "QUAD_002"} <= codes


def test_vertex_misconception_rules() -> None:
    prompt = "What are the coordinates of the vertex of the parabola shown?"
    swapped = evaluate_problem(prompt, "(-1, 2)", "(2, -1)")
    assert not swapped.correct and swapped.misconception_code == "QUAD_003"
    sign_flip = evaluate_problem(prompt, "(-2, -1)", "(2, -1)")
    assert not sign_flip.correct and sign_flip.misconception_code == "QUAD_001"


def test_parabola_visual_spec() -> None:
    generated = GENERATORS["QUADRATIC_FUNCTION"](random.Random(7), 3)
    visual = visualization_for(_as_problem(generated))
    assert visual["type"] == "parabola_graph"
    assert {"a_num", "a_den", "h", "k", "min", "max"} <= set(visual)


def test_curve_stays_near_the_grid() -> None:
    for seed in range(300):
        generated = GENERATORS["QUADRATIC_FUNCTION"](random.Random(seed), 4)
        p = generated.parameters
        if p["tier"] == "evaluate":
            continue  # evaluate is text-only
        a = _a(p)
        # The vertex and its one-step neighbours must be inside ±9.
        assert abs(p["h"]) <= 9 and abs(p["k"]) <= 9 and abs(p["k"] + a) <= 9
