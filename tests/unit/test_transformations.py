"""TRANSFORMATION generator: image coordinates, misconception-tagged
distractors, the transformation visual spec, and the ordered-pair
misconception rules."""

import random
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(800):
        generated = GENERATORS["TRANSFORMATION"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no TRANSFORMATION/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def test_low_difficulty_only_translates() -> None:
    for seed in range(200):
        generated = GENERATORS["TRANSFORMATION"](random.Random(seed), 1)
        assert generated.parameters["tier"] == "translate"


def test_translate_image_coordinates() -> None:
    for _ in range(60):
        generated = _gen("translate", difficulty=1)
        p = generated.parameters
        assert generated.canonical_answer == f"({p['x'] + p['dx']}, {p['y'] + p['dy']})"
        assert abs(p["x"] + p["dx"]) <= 8 and abs(p["y"] + p["dy"]) <= 8


def test_reflect_image_coordinates() -> None:
    for _ in range(60):
        generated = _gen("reflect", difficulty=2)
        p = generated.parameters
        if p["axis"] == "x-axis":
            assert generated.canonical_answer == f"({p['x']}, {-p['y']})"
        else:
            assert generated.canonical_answer == f"({-p['x']}, {p['y']})"


def test_rotate_image_coordinates() -> None:
    for _ in range(60):
        generated = _gen("rotate", difficulty=3)
        p = generated.parameters
        x, y = p["x"], p["y"]
        if p["direction"] == "90° clockwise":
            expected = (y, -x)
        elif p["direction"] == "90° counterclockwise":
            expected = (-y, x)
        else:
            expected = (-x, -y)
        assert generated.canonical_answer == f"({expected[0]}, {expected[1]})"


def test_dilate_image_coordinates() -> None:
    for _ in range(60):
        generated = _gen("dilate", difficulty=4)
        p = generated.parameters
        assert generated.canonical_answer == f"({p['k'] * p['x']}, {p['k'] * p['y']})"


def test_identify_renders_both_triangles_and_tags_distractors() -> None:
    for _ in range(60):
        generated = _gen("identify", difficulty=3)
        p = generated.parameters
        assert len(p["preimage"]) == 3 and len(p["image"]) == 3
        texts = {c["text"] for c in generated.choices}
        assert len(texts) == 4
        correct = [c for c in generated.choices if c["id"] == generated.canonical_answer]
        assert correct and "misconception_code" not in correct[0]
        assert any(c.get("misconception_code") == "TR_004" for c in generated.choices)


def test_each_tier_emits_transformation_spec() -> None:
    for tier, difficulty in [
        ("translate", 1), ("reflect", 2), ("rotate", 3),
        ("dilate", 4), ("identify", 3),
    ]:
        generated = _gen(tier, difficulty=difficulty)
        spec = visualization_for(_as_problem(generated))
        assert spec is not None and spec["type"] == "transformation"
        assert spec["preimage"] == generated.parameters["preimage"]
        if tier == "identify":
            assert spec["image"] == generated.parameters["image"]
        else:
            assert "image" not in spec


def test_reflection_wrong_axis_flags_tr_002() -> None:
    prompt = "Point P is shown on the grid. Reflect it over the x-axis. What are the coordinates of P'?"
    assert evaluate_problem(prompt, "(2, 3)", "(-2, -3)").misconception_code == "TR_002"
    prompt = "Point P is shown on the grid. Reflect it over the y-axis. What are the coordinates of P'?"
    assert evaluate_problem(prompt, "(-3, 2)", "(3, -2)").misconception_code == "TR_002"


def test_rotation_errors_flag_tr_001() -> None:
    prompt = "Point P is shown on the grid. Rotate it 90° clockwise about the origin. What are the coordinates of P'?"
    # (2, 3) rotated cw is (3, -2); (-3, 2) turned the wrong way.
    assert evaluate_problem(prompt, "(-3, 2)", "(3, -2)").misconception_code == "TR_001"
    assert evaluate_problem(prompt, "(3, 2)", "(3, -2)").misconception_code == "TR_001"


def test_translation_sign_flip_flags_tr_003() -> None:
    prompt = (
        "Point P is shown on the grid. Translate it 3 units right and 2 "
        "units up. What are the coordinates of P'?"
    )
    # Correct image (5, 5); moving left on x gives (-1, 5).
    assert evaluate_problem(prompt, "(-1, 5)", "(5, 5)").misconception_code == "TR_003"
    assert evaluate_problem(prompt, "(5, 1)", "(5, 5)").misconception_code == "TR_003"


def test_dilation_partial_flags_tr_005() -> None:
    prompt = (
        "Point P is shown on the grid. Dilate it by a scale factor of 3 "
        "centred at the origin. What are the coordinates of P'?"
    )
    # Preimage (2, 1) → (6, 3); scaling one coordinate gives (6, 1).
    assert evaluate_problem(prompt, "(6, 1)", "(6, 3)").misconception_code == "TR_005"
    assert evaluate_problem(prompt, "(5, 4)", "(6, 3)").misconception_code == "TR_005"
