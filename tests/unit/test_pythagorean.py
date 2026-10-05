"""PYTHAGOREAN generator: right-triangle side lengths, the converse,
coordinate-plane distance, and the leg/hypotenuse misconception rules."""

import math
import random
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(1500):
        generated = GENERATORS["PYTHAGOREAN"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no PYTHAGOREAN/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def test_low_difficulty_only_finds_hypotenuses() -> None:
    for seed in range(200):
        generated = GENERATORS["PYTHAGOREAN"](random.Random(seed), 1)
        assert generated.parameters["tier"] == "hypotenuse"


def test_hypotenuse_and_leg_answers_are_exact_triples() -> None:
    for _ in range(120):
        generated = _gen("hypotenuse", difficulty=1)
        p = generated.parameters
        assert int(generated.canonical_answer) ** 2 == p["a"] ** 2 + p["b"] ** 2
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "right_triangle"
        assert spec["hyp"] == "?" and spec["leg_a"] == str(p["a"])
    for _ in range(120):
        generated = _gen("leg", difficulty=2)
        p = generated.parameters
        assert p["a"] ** 2 + p["b"] ** 2 == p["c"] ** 2
        assert int(generated.canonical_answer) == p["b"]
        spec = visualization_for(_as_problem(generated))
        assert spec["hyp"] == str(p["c"]) and spec["leg_b"] == "?"


def test_radical_hypotenuse_is_the_exact_root() -> None:
    for _ in range(120):
        generated = _gen("radical_hypotenuse", difficulty=2)
        p = generated.parameters
        c2 = p["a"] ** 2 + p["b"] ** 2
        # Non-triples only: the answer must be an irrational root.
        assert math.isqrt(c2) ** 2 != c2
        correct = next(
            c["text"] for c in generated.choices if c["id"] == generated.canonical_answer
        )
        assert correct == f"√{c2}"
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        assert tags.get(str(p["a"] + p["b"])) == "PYTH_002"
        assert tags.get(str(c2)) == "PYTH_001"


def test_converse_answer_matches_the_square_check() -> None:
    for _ in range(120):
        generated = _gen("converse", difficulty=3)
        a, b, c = generated.parameters["sides"]
        correct = next(
            c_["text"] for c_ in generated.choices if c_["id"] == generated.canonical_answer
        )
        assert correct.startswith("Yes") == (a * a + b * b == c * c)
        # Text-only: a drawn right triangle would answer the question.
        assert visualization_for(_as_problem(generated)) is None


def test_distance_is_the_hypotenuse_of_the_deltas() -> None:
    for _ in range(120):
        generated = _gen("distance", difficulty=4)
        (x1, y1), (x2, y2) = generated.parameters["points"]
        assert all(-9 <= v <= 9 for v in (x1, y1, x2, y2))
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        assert int(generated.canonical_answer) ** 2 == dx * dx + dy * dy
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "distance_segment"
        assert spec["points"] == [[x1, y1], [x2, y2]]


def test_leg_addition_flags_pyth_002() -> None:
    prompt = ("The right triangle has legs of length 3 and 4. "
              "What is the length of the hypotenuse?")
    assert evaluate_problem(prompt, "7", "5").misconception_code == "PYTH_002"
    assert evaluate_problem(prompt, "25", "5").misconception_code == "PYTH_001"
    assert evaluate_problem(prompt, "5", "5").correct
    assert evaluate_problem(prompt, "9", "5").misconception_code is None


def test_leg_tier_flags_added_sides_and_unrooted_squares() -> None:
    prompt = ("The right triangle has a hypotenuse of length 13 and one leg "
              "of length 5. What is the length of the other leg?")
    assert evaluate_problem(prompt, "18", "12").misconception_code == "PYTH_002"
    assert evaluate_problem(prompt, "144", "12").misconception_code == "PYTH_001"
    assert evaluate_problem(prompt, "194", "12").misconception_code == "PYTH_002"
    assert evaluate_problem(prompt, "12", "12").correct


def test_distance_flags_manhattan_and_unrooted_answers() -> None:
    prompt = "What is the distance between point A(1, 1) and point B(5, 4)?"
    assert evaluate_problem(prompt, "7", "5").misconception_code == "PYTH_002"
    assert evaluate_problem(prompt, "25", "5").misconception_code == "PYTH_001"
    assert evaluate_problem(prompt, "5", "5").correct
