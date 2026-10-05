"""SOLID_VOLUME generator: tiers, canonical answers, distractor tags, the
solid visual spec, and the VOLUME spec's move to the shared solid model."""

import random
from types import SimpleNamespace

from app.services.evaluation import evaluate_problem
from app.services.problem_generation import _SOLID_PROPERTIES, GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(400):
        generated = GENERATORS["SOLID_VOLUME"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no SOLID_VOLUME/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def test_prism_volume_is_lwh() -> None:
    for seed in range(200):
        generated = GENERATORS["SOLID_VOLUME"](random.Random(seed), 2)
        p = generated.parameters
        if p["tier"] != "prism_volume":
            continue
        assert p["solid"] == "rectangular_prism"
        assert generated.canonical_answer == str(p["l"] * p["w"] * p["h"])


def test_pyramid_volume_is_third_bh() -> None:
    for seed in range(200):
        generated = GENERATORS["SOLID_VOLUME"](random.Random(seed), 3)
        p = generated.parameters
        if p["tier"] != "pyramid_volume":
            continue
        assert p["solid"] == "square_pyramid"
        assert (p["b"] * p["b"] * p["h"]) % 3 == 0
        assert generated.canonical_answer == str(p["b"] * p["b"] * p["h"] // 3)


def test_pyramid_forgot_third_rule() -> None:
    prompt = "The square pyramid shown has a base with side length 3 and height 6. What is its volume in cubic units?"
    result = evaluate_problem(prompt, "54", "18")
    assert not result.correct
    assert result.misconception_code == "SOLID_001"
    assert evaluate_problem(prompt, "18", "18").correct


def test_count_faces_and_edges_use_solid_properties() -> None:
    for seed in range(300):
        generated = GENERATORS["SOLID_VOLUME"](random.Random(seed), 4)
        p = generated.parameters
        if p["tier"] not in {"count_faces", "count_edges"}:
            continue
        faces, _, edges = _SOLID_PROPERTIES[p["solid"]]
        correct = next(
            c for c in generated.choices if c["id"] == generated.canonical_answer
        )
        expected = faces if p["tier"] == "count_faces" else edges
        assert correct["text"] == str(expected)
        assert any(
            c.get("misconception_code") == "SOLID_003" for c in generated.choices
        )


def test_surface_area_is_two_each_pair() -> None:
    generated = _gen("surface_area", difficulty=3)
    p = generated.parameters
    correct = next(c for c in generated.choices if c["id"] == generated.canonical_answer)
    l, w, h = p["l"], p["w"], p["h"]
    assert correct["text"] == str(2 * (l * w + l * h + w * h))
    codes = {c.get("misconception_code") for c in generated.choices}
    assert {"SOLID_002", "SOLID_003"} <= codes


def test_cylinder_and_cone_volumes_in_terms_of_pi() -> None:
    for seed in range(300):
        generated = GENERATORS["SOLID_VOLUME"](random.Random(seed), 4)
        p = generated.parameters
        if p["tier"] == "cylinder_volume":
            correct = next(
                c for c in generated.choices if c["id"] == generated.canonical_answer
            )
            assert correct["text"] == f"{p['r'] * p['r'] * p['h']}π"
            codes = {c.get("misconception_code") for c in generated.choices}
            assert "SOLID_001" in codes or "SOLID_002" in codes
        elif p["tier"] == "cone_volume":
            correct = next(
                c for c in generated.choices if c["id"] == generated.canonical_answer
            )
            assert correct["text"] == f"{p['r'] * p['r'] * p['h'] // 3}π"
            codes = {c.get("misconception_code") for c in generated.choices}
            assert "SOLID_001" in codes


def test_solid_visual_spec_per_solid() -> None:
    for tier, difficulty in (("prism_volume", 2), ("count_faces", 4), ("cone_volume", 4)):
        generated = _gen(tier, difficulty=difficulty)
        visual = visualization_for(_as_problem(generated))
        assert visual["type"] == "solid"
        assert visual["solid"] == generated.parameters["solid"]
        assert "aria_label" in visual
        # The spec must never carry the answer.
        assert "volume" not in visual and "surface_area" not in visual


def test_solid_spec_rejects_unknown_or_incomplete() -> None:
    bad = SimpleNamespace(
        prompt="?", problem_type="SOLID_VOLUME", difficulty=3,
        solution={"parameters": {"tier": "prism_volume", "solid": "torus"}},
    )
    assert visualization_for(bad) is None
    missing = SimpleNamespace(
        prompt="?", problem_type="SOLID_VOLUME", difficulty=3,
        solution={"parameters": {"tier": "prism_volume", "solid": "cone", "r": 2}},
    )
    assert visualization_for(missing) is None


def test_legacy_volume_uses_solid_spec_without_answer() -> None:
    problem = SimpleNamespace(
        prompt="A rectangular prism has length 2, width 3, and height 4. What is its volume?",
        problem_type="VOLUME",
        difficulty=2,
        solution={"parameters": {"length": 2, "width": 3, "height": 4}},
    )
    visual = visualization_for(problem)
    assert visual["type"] == "solid"
    assert visual["solid"] == "rectangular_prism"
    assert (visual["l"], visual["w"], visual["h"]) == (2, 3, 4)
    assert "24" not in str(visual)
