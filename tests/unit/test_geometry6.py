"""GEOMETRY_MEASURE generator: triangle, parallelogram and trapezoid
area, prism volume and surface area, and shared-axis coordinate
distance, plus the GEO6 misconception rules."""

import random
from types import SimpleNamespace

from app.services.evaluation import MISCONCEPTION_RULES, _normalize
from app.services.problem_generation import GENERATORS
from app.services.visualization import visualization_for


def _gen(tier: str, *, difficulty: int) -> object:
    for seed in range(2500):
        generated = GENERATORS["GEOMETRY_MEASURE"](random.Random(seed), difficulty)
        if generated.parameters.get("tier") == tier:
            return generated
    raise AssertionError(f"no GEOMETRY_MEASURE/{tier} at difficulty {difficulty}")


def _as_problem(generated) -> SimpleNamespace:
    return SimpleNamespace(
        prompt=generated.prompt,
        problem_type=generated.problem_type,
        difficulty=generated.difficulty,
        solution={"parameters": generated.parameters},
    )


def _rule(prompt: str, answer: str, canonical: str):
    rule = next(
        r for r in MISCONCEPTION_RULES if r.__name__ == "_geometry6_errors")
    return rule(_normalize(prompt), answer, canonical)


def test_tier_coverage() -> None:
    assert _gen("triangle_area", difficulty=1)
    assert _gen("parallelogram_area", difficulty=1)
    assert _gen("distance", difficulty=2)
    assert _gen("volume", difficulty=2)
    assert _gen("trapezoid_area", difficulty=3)
    assert _gen("surface_area", difficulty=3)


def test_area_answers_are_deterministic() -> None:
    tri = _gen("triangle_area", difficulty=1)
    b, h = tri.parameters["base"], tri.parameters["height"]
    assert int(tri.canonical_answer) == b * h // 2
    para = _gen("parallelogram_area", difficulty=1)
    assert int(para.canonical_answer) == para.parameters["base"] * para.parameters["height"]
    trap = _gen("trapezoid_area", difficulty=3)
    assert int(trap.canonical_answer) == (
        (trap.parameters["base"] + trap.parameters["top"]) * trap.parameters["height"] // 2)


def test_distance_uses_a_shared_axis() -> None:
    generated = _gen("distance", difficulty=2)
    (x1, y1), (x2, y2) = generated.parameters["points"]
    assert x1 == x2 or y1 == y2
    assert int(generated.canonical_answer) == abs(x1 - x2) + abs(y1 - y2)
    spec = visualization_for(_as_problem(generated))
    assert spec is not None and spec["type"] == "distance_segment"


def test_volume_and_surface_area() -> None:
    vol = _gen("volume", difficulty=2)
    l, w, h = vol.parameters["length"], vol.parameters["width"], vol.parameters["height"]
    assert int(vol.canonical_answer) == l * w * h
    surf = _gen("surface_area", difficulty=3)
    l, w, h = surf.parameters["length"], surf.parameters["width"], surf.parameters["height"]
    assert int(surf.canonical_answer) == 2 * (l * w + l * h + w * h)


def test_shape_specs_and_text_only_tiers() -> None:
    for tier, difficulty in (("triangle_area", 1), ("parallelogram_area", 1), ("trapezoid_area", 3)):
        spec = visualization_for(_as_problem(_gen(tier, difficulty=difficulty)))
        assert spec is not None and spec["type"] == "shape_area"
    for tier, difficulty in (("volume", 2), ("surface_area", 3)):
        assert visualization_for(_as_problem(_gen(tier, difficulty=difficulty))) is None


def test_all_answers_are_integer_kind() -> None:
    for seed in range(80):
        generated = GENERATORS["GEOMETRY_MEASURE"](random.Random(seed), 3)
        assert generated.answer_kind == "INTEGER"


def test_unhalved_triangle_and_trapezoid_are_geo6_001() -> None:
    tri = _gen("triangle_area", difficulty=1)
    b, h = tri.parameters["base"], tri.parameters["height"]
    match = _rule(tri.prompt, str(b * h), tri.canonical_answer)
    assert match is not None and match.code == "GEO6_001"
    trap = _gen("trapezoid_area", difficulty=3)
    t = (trap.parameters["base"] + trap.parameters["top"]) * trap.parameters["height"]
    match = _rule(trap.prompt, str(t), trap.canonical_answer)
    assert match is not None and match.code == "GEO6_001"


def test_perimeter_and_slant_errors() -> None:
    para = _gen("parallelogram_area", difficulty=1)
    b, slant = para.parameters["base"], para.parameters["slant"]
    match = _rule(para.prompt, str(2 * (b + slant)), para.canonical_answer)
    assert match is not None and match.code == "GEO6_002"
    match = _rule(para.prompt, str(b * slant), para.canonical_answer)
    assert match is not None and match.code == "GEO6_004"


def test_volume_surface_swap_is_geo6_003() -> None:
    surf = _gen("surface_area", difficulty=3)
    l, w, h = surf.parameters["length"], surf.parameters["width"], surf.parameters["height"]
    match = _rule(surf.prompt, str(l * w * h), surf.canonical_answer)
    assert match is not None and match.code == "GEO6_003"
    vol = _gen("volume", difficulty=2)
    l, w, h = vol.parameters["length"], vol.parameters["width"], vol.parameters["height"]
    match = _rule(vol.prompt, str(2 * (l * w + l * h + w * h)), vol.canonical_answer)
    assert match is not None and match.code == "GEO6_003"


def test_distance_miscount_is_geo6_004() -> None:
    generated = _gen("distance", difficulty=2)
    (x1, y1), (x2, y2) = generated.parameters["points"]
    if x1 == x2:
        miscount = abs(abs(y1) - abs(y2))
        if miscount == int(generated.canonical_answer):
            miscount = abs(y1) + abs(y2)
    else:
        miscount = abs(abs(x1) - abs(x2))
        if miscount == int(generated.canonical_answer):
            miscount = abs(x1) + abs(x2)
    match = _rule(generated.prompt, str(miscount), generated.canonical_answer)
    assert match is not None and match.code == "GEO6_004"


def test_prompt_variety() -> None:
    prompts = {
        GENERATORS["GEOMETRY_MEASURE"](random.Random(seed), 3).prompt
        for seed in range(60)
    }
    assert len(prompts) > 40
