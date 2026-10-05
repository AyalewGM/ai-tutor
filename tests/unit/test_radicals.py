"""RADICALS generator: irrational-number classification, bounding,
number-line location, estimation, simplest form, comparison, and the
radical misconception rules."""

import math
import random
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(1500):
        generated = GENERATORS["RADICALS"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no RADICALS/{tier} at difficulty {difficulty}")


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


def test_low_difficulty_only_classifies_and_bounds() -> None:
    for seed in range(200):
        generated = GENERATORS["RADICALS"](random.Random(seed), 1)
        assert generated.parameters["tier"] in {"classify", "between_integers"}


def test_classify_answer_matches_squareness() -> None:
    for _ in range(120):
        generated = _gen("classify", difficulty=1)
        n = generated.parameters["n"]
        is_square = math.isqrt(n) ** 2 == n
        assert _correct_text(generated).startswith("Rational") == is_square
        tags = {c.get("misconception_code") for c in generated.choices}
        assert "RAD_004" in tags


def test_between_integers_answer_is_the_floor() -> None:
    for _ in range(120):
        generated = _gen("between_integers", difficulty=1)
        n = generated.parameters["n"]
        floor = math.isqrt(n)
        assert floor * floor < n  # nonsquares only
        assert int(generated.canonical_answer) == floor
        # Text-only: a drawn line would hand over the bound.
        assert visualization_for(_as_problem(generated)) is None


def test_locate_markers_are_distinct_and_lettered() -> None:
    for _ in range(150):
        generated = _gen("locate", difficulty=2)
        p = generated.parameters
        markers = p["markers"]
        assert len(markers) == 4
        positions = [m["position"] for m in markers]
        assert positions == sorted(positions)
        assert len(set(positions)) == 4
        n = p["n"]
        correct = next(
            m for m in markers if m["label"] == _correct_text(generated)
        )
        assert abs(correct["position"] - math.sqrt(n)) < 0.01
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "radical_line"
        assert spec["min"] == p["lo"] and spec["max"] == p["hi"]
        assert spec["markers"] == markers
        assert all(
            p["lo"] <= m["position"] <= p["hi"] for m in spec["markers"]
        )
        # The floor tick is the "round down" distractor, always tagged.
        floor_letter = next(
            (m["label"] for m in markers if m["position"] == float(math.isqrt(n))),
            None,
        )
        if floor_letter is not None:
            tagged = {
                c["text"]: c.get("misconception_code") for c in generated.choices
            }
            assert tagged.get(floor_letter) == "RAD_002"


def test_estimate_is_the_nearest_tenth() -> None:
    for _ in range(120):
        generated = _gen("estimate", difficulty=2)
        n = generated.parameters["n"]
        assert _correct_text(generated) == f"{math.sqrt(n):.1f}"
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        assert tags.get(f"{math.isqrt(n)}.0") == "RAD_002"
        assert tags.get(f"{n / 2:g}") == "RAD_001"


def test_simplify_is_exact_radical_form() -> None:
    for _ in range(120):
        generated = _gen("simplify", difficulty=3)
        n = generated.parameters["n"]
        correct = _correct_text(generated)
        coef, radicand = correct.split("√")
        assert int(coef) ** 2 * int(radicand) == n
        assert math.isqrt(n) ** 2 != n
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        assert tags.get(f"{int(coef) ** 2}√{radicand}") == "RAD_003"


def test_compare_picks_the_larger_side() -> None:
    for _ in range(120):
        generated = _gen("compare", difficulty=3)
        p = generated.parameters
        correct = _correct_text(generated)
        t = math.sqrt(p["n"])
        assert (correct == f"√{p['n']}") == (t > p["d"])
        assert abs(t - p["d"]) >= 0.15
        # Text-only comparison: no visual leaks the ordering.
        assert visualization_for(_as_problem(generated)) is None


def test_bounding_flags_halving_and_upper_bound() -> None:
    prompt = ("The value √50 lies between two consecutive whole numbers. "
              "What is the smaller of the two?")
    assert evaluate_problem(prompt, "25", "7").misconception_code == "RAD_001"
    assert evaluate_problem(prompt, "8", "7").misconception_code == "RAD_002"
    assert evaluate_problem(prompt, "7", "7").correct
    assert evaluate_problem(prompt, "6", "7").misconception_code is None
