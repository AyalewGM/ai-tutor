"""GEOMETRY_2D generator: tier answers, misconception-tagged distractors, the
five diagram specs, and the angle-relationship misconception rules."""

import random
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(600):
        generated = GENERATORS["GEOMETRY_2D"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no GEOMETRY_2D/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _correct_text(generated) -> str:
    for choice in generated.choices:
        if choice["id"] == generated.canonical_answer:
            return choice["text"]
    raise AssertionError("canonical answer is not among the choices")


def test_low_difficulty_only_offers_simple_angle_pairs() -> None:
    for seed in range(200):
        generated = GENERATORS["GEOMETRY_2D"](random.Random(seed), 1)
        assert generated.parameters["tier"] in {"complementary", "supplementary"}


def test_complementary_and_supplementary_sums() -> None:
    for _ in range(60):
        comp = _gen("complementary", difficulty=1)
        assert int(comp.canonical_answer) == 90 - comp.parameters["angle"]
        supp = _gen("supplementary", difficulty=2)
        assert int(supp.canonical_answer) == 180 - supp.parameters["angle"]


def test_triangle_angle_sum() -> None:
    for _ in range(60):
        generated = _gen("triangle_angle", difficulty=3)
        params = generated.parameters
        assert int(generated.canonical_answer) == 180 - params["a"] - params["b"]
        assert int(generated.canonical_answer) > 0


def test_vertical_angles_answer_equals_labeled() -> None:
    for _ in range(60):
        generated = _gen("vertical_angles", difficulty=3)
        angle = generated.parameters["angle"]
        assert _correct_text(generated) == str(angle)
        assert generated.parameters["mark"] == "vertical"
        tagged = [c for c in generated.choices if c.get("misconception_code") == "GEO_004"]
        assert tagged and tagged[0]["text"] == str(180 - angle)


def test_circle_area_and_circumference_in_terms_of_pi() -> None:
    for _ in range(60):
        area = _gen("circle_area", difficulty=4)
        r = area.parameters["r"]
        assert _correct_text(area) == f"{r * r}π"
        tags = {c["text"]: c.get("misconception_code") for c in area.choices}
        assert tags[f"{2 * r}π"] == "GEO_001"
        assert tags[f"{4 * r * r}π"] == "GEO_006"

        circ = _gen("circle_circumference", difficulty=4)
        r = circ.parameters["r"]
        assert _correct_text(circ) == f"{2 * r}π"
        tags = {c["text"]: c.get("misconception_code") for c in circ.choices}
        assert tags[f"{r * r}π"] == "GEO_001"
        assert tags[f"{r}π"] == "GEO_006"


def test_composite_area_subtracts_notch() -> None:
    for _ in range(60):
        generated = _gen("composite_area", difficulty=4)
        p = generated.parameters
        area = p["w"] * p["h"] - p["a"] * p["b"]
        assert _correct_text(generated) == str(area)
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        assert tags[str(p["w"] * p["h"])] == "GEO_005"
        assert tags[str(p["w"] * p["h"] + p["a"] * p["b"])] == "GEO_005"


def test_each_tier_emits_its_diagram() -> None:
    expected = {
        ("complementary", 1): "angle_pair",
        ("supplementary", 2): "angle_pair",
        ("linear_pair", 3): "intersecting_lines",
        ("vertical_angles", 3): "intersecting_lines",
        ("triangle_angle", 3): "triangle_angles",
        ("circle_area", 4): "circle_measure",
        ("circle_circumference", 4): "circle_measure",
        ("composite_area", 4): "composite_figure",
    }
    for (tier, difficulty), spec_type in expected.items():
        generated = _gen(tier, difficulty=difficulty)
        spec = visualization_for(_as_problem(generated))
        assert spec is not None
        assert spec["type"] == spec_type


def test_diagrams_never_reveal_answers() -> None:
    generated = _gen("triangle_angle", difficulty=3)
    spec = visualization_for(_as_problem(generated))
    assert generated.canonical_answer not in {str(v) for v in spec.values()}


def test_complement_supplement_swap_flags_geo_002() -> None:
    prompt = "The two angles shown are complementary. What is the measure of the missing angle?"
    assert evaluate_problem(prompt, "145", "55").misconception_code == "GEO_002"
    prompt = "The two angles shown are supplementary. What is the measure of the missing angle?"
    assert evaluate_problem(prompt, "20", "110").misconception_code == "GEO_002"


def test_triangle_360_sum_flags_geo_003() -> None:
    prompt = "What is the measure of the triangle's third angle, labeled ?"
    assert evaluate_problem(prompt, "255", "75").misconception_code == "GEO_003"


def test_linear_pair_answered_with_vertical_flags_geo_004() -> None:
    prompt = "The marked angle and the angle labeled ? form a linear pair. What is the measure of ?"
    assert evaluate_problem(prompt, "70", "110").misconception_code == "GEO_004"
