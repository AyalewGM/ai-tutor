"""SIMILARITY generator: scale factors, proportional sides, the k versus
k² trap, congruence classification, and the similar-figures visual spec."""

import random
from types import SimpleNamespace

from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(600):
        generated = GENERATORS["SIMILARITY"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no SIMILARITY/{tier} at difficulty {difficulty}")


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


def test_low_difficulty_offers_simple_tiers() -> None:
    for seed in range(200):
        generated = GENERATORS["SIMILARITY"](random.Random(seed), 1)
        assert generated.parameters["tier"] in {"scale_factor", "missing_side"}


def test_scale_factor_matches_labeled_edges() -> None:
    for _ in range(60):
        generated = _gen("scale_factor", difficulty=1)
        p = generated.parameters
        a = int(p["pre_edge_labels"][0])
        image_a = int(p["image_edge_labels"][0])
        expected = image_a / a
        correct = _correct_text(generated)
        if "/" in correct:
            num, den = correct.split("/")
            assert int(num) / int(den) == expected
        else:
            assert int(correct) == expected
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        reciprocal = f"{p['k_den']}/{p['k_num']}"
        assert tags[reciprocal] == "SIM_003"


def test_missing_side_scales_proportionally() -> None:
    for _ in range(60):
        generated = _gen("missing_side", difficulty=1)
        p = generated.parameters
        a = int(p["pre_edge_labels"][0])
        b = int(p["pre_edge_labels"][1])
        image_a = int(p["image_edge_labels"][0])
        k = image_a // a
        assert image_a == a * k
        assert _correct_text(generated) == str(b * k)
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        assert tags[str(b + a * (k - 1))] == "SIM_001"


def test_perimeter_area_effect_uses_the_right_power() -> None:
    for _ in range(60):
        generated = _gen("perimeter_area_effect", difficulty=3)
        p = generated.parameters
        k = p["k"]
        expected = k if p["measure"] == "perimeter" else k * k
        wrong = k * k if p["measure"] == "perimeter" else k
        assert _correct_text(generated) == f"multiplied by {expected}"
        tags = {c["text"]: c.get("misconception_code") for c in generated.choices}
        assert tags[f"multiplied by {wrong}"] == "SIM_002"


def test_classify_answers_match_the_figures() -> None:
    for _ in range(60):
        generated = _gen("classify", difficulty=3)
        p = generated.parameters
        correct = _correct_text(generated)
        assert correct in {
            "congruent", "similar but not congruent", "neither congruent nor similar"
        }
        if correct == "congruent":
            assert p["preimage"] == p["image"]
        else:
            assert p["preimage"] != p["image"]
        tagged = [c for c in generated.choices if c["id"] != generated.canonical_answer]
        assert all(c.get("misconception_code") == "SIM_004" for c in tagged)


def test_every_tier_emits_similar_figures_spec() -> None:
    for tier, difficulty in [
        ("scale_factor", 1), ("missing_side", 2),
        ("perimeter_area_effect", 3), ("classify", 3),
    ]:
        generated = _gen(tier, difficulty=difficulty)
        spec = visualization_for(_as_problem(generated))
        assert spec is not None and spec["type"] == "similar_figures"
        assert spec["preimage"] and spec["image"]
