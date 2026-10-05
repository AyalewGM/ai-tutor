"""SIGNED_NUMBERS generator: signed add/subtract, multiplication and
division sign rules, additive inverses, number-line placement and
distance, plus the NEG misconception rules."""

import random
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(2500):
        generated = GENERATORS["SIGNED_NUMBERS"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no SIGNED_NUMBERS/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def test_low_difficulty_covers_add_word_and_inverse() -> None:
    for seed in range(200):
        generated = GENERATORS["SIGNED_NUMBERS"](random.Random(seed), 1)
        assert generated.parameters["tier"] in {"add", "word", "inverse"}


def test_add_and_subtract_evaluate_correctly() -> None:
    for _ in range(150):
        add = _gen("add", difficulty=1)
        p = add.parameters
        assert int(add.canonical_answer) == p["a"] + p["b"]
        assert p["a"] != 0 and p["b"] != 0
        sub = _gen("subtract", difficulty=2)
        p = sub.parameters
        assert int(sub.canonical_answer) == p["a"] - p["b"]
        assert visualization_for(_as_problem(sub)) is None


def test_word_and_inverse_answers_match_the_model() -> None:
    for _ in range(120):
        word = _gen("word", difficulty=1)
        p = word.parameters
        assert int(word.canonical_answer) == p["a"] + p["direction"] * p["b"]
        inverse = _gen("inverse", difficulty=1)
        assert int(inverse.canonical_answer) == -inverse.parameters["a"]


def test_multiply_and_divide_follow_the_sign_rules() -> None:
    for _ in range(150):
        mul = _gen("multiply", difficulty=3)
        p = mul.parameters
        assert int(mul.canonical_answer) == p["a"] * p["b"]
        assert abs(p["a"]) > 1 and abs(p["b"]) > 1
        div = _gen("divide", difficulty=3)
        p = div.parameters
        assert p["a"] % p["b"] == 0
        assert int(div.canonical_answer) == p["a"] // p["b"]


def test_which_point_marks_a_distinct_set_with_diagnostics() -> None:
    for _ in range(150):
        generated = _gen("which_point", difficulty=2)
        p = generated.parameters
        positions = [m["position"] for m in p["markers"]]
        assert len(set(positions)) == len(positions)
        correct_letter = next(
            c["text"] for c in generated.choices
            if c["id"] == generated.canonical_answer
        )
        correct = next(
            m for m in p["markers"] if m["label"] == correct_letter
        )
        assert correct["position"] == p["a"] + p["b"]
        spec = visualization_for(_as_problem(generated))
        assert spec["type"] == "radical_line"
        assert spec["min"] <= min(positions) < max(positions) <= spec["max"]
        tag_by_id = {c["id"].lower(): c.get("misconception_code")
                     for c in generated.choices}
        assert "NEG_003" in tag_by_id.values()


def test_distance_is_always_the_positive_gap() -> None:
    for _ in range(120):
        generated = _gen("distance", difficulty=4)
        p = generated.parameters
        assert int(generated.canonical_answer) == abs(p["q"] - p["p"])
        assert visualization_for(_as_problem(generated)) is None


def test_evaluation_flags_the_signature_signed_errors() -> None:
    # Subtracting a negative: 3 - (-4) answered as 3 - 4.
    prompt = "Evaluate 3 - (-4)."
    assert evaluate_problem(prompt, "-1", "7").misconception_code == "NEG_001"
    # Sign rule missed on a product of two negatives.
    assert evaluate_problem(
        "Evaluate (-6) × (-4).", "-24", "24"
    ).misconception_code == "NEG_002"
    # Magnitudes added keeping the sign: -5 + 3 answered as -8.
    # The legacy integer rules fire first on bare evaluate prompts.
    assert evaluate_problem(
        "Evaluate -5 + 3.", "-8", "-2"
    ).misconception_code == "NUM_001"
    # The same error inside a context prompt reads NEG_003.
    assert evaluate_problem(
        "The temperature was -5 degrees and rose by 3 degrees. "
        "What is the temperature now?",
        "-8", "-2",
    ).misconception_code == "NEG_003"
    # Additive inverse reported with the same sign.
    assert evaluate_problem(
        "What number added to 7 gives 0?", "7", "-7"
    ).misconception_code == "NEG_004"
    # Temperature moved the wrong direction.
    assert evaluate_problem(
        "The temperature was -3 degrees and fell by 5 degrees. "
        "What is the temperature now?",
        "2", "-8",
    ).misconception_code == "NEG_003"
    assert evaluate_problem("Evaluate -5 + 3.", "-2", "-2").correct
