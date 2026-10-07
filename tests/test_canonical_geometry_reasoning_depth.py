import random
import re

from app.domains import geometry_reasoning_depth as domain

CODES = sorted(domain.FAMILIES)


def _build(code: str, seed: int = 41):
    return domain.build(code, random.Random(seed), 3)


def test_geometry_reasoning_batch_has_fourteen_families() -> None:
    assert len(CODES) == 14
    expected = {"DIAGNOSTIC", "GUIDED", "INDEPENDENT", "MASTERY", "REVIEW"}
    assert all(
        {mode.value for mode in domain.FAMILIES[code].modes} == expected for code in CODES
    )


def test_geometry_reasoning_generation_is_deterministic() -> None:
    for code in CODES:
        assert _build(code, 73) == _build(code, 73), code


def test_geometry_misconceptions_do_not_collide_with_truth() -> None:
    for code in CODES:
        for seed in range(15):
            _, answer, _, misconceptions = _build(code, seed)
            truth = "".join(answer.lower().split())
            for candidate in misconceptions.values():
                assert "".join(candidate.lower().split()) != truth, (code, seed)


def test_triangle_inequality_matches_side_length_oracle() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.TRIANGLE.INEQUALITY", seed)
        match = re.fullmatch(
            r"Can side lengths (\d+), (\d+), and (\d+) form a triangle\? Answer yes or no\.",
            prompt,
        )
        assert match
        sides = sorted(map(int, match.groups()))
        expected = "yes" if sides[0] + sides[1] > sides[2] else "no"
        assert answer == expected


def test_missing_leg_satisfies_pythagorean_theorem() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.PYTHAGOREAN.LEG", seed)
        match = re.fullmatch(
            r"A right triangle has hypotenuse (\d+) and one leg (\d+)\. "
            r"Find the other leg\.",
            prompt,
        )
        assert match
        hypotenuse, known = map(int, match.groups())
        missing = int(answer)
        assert missing**2 + known**2 == hypotenuse**2


def test_pythagorean_converse_matches_square_sum() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.PYTHAGOREAN.CONVERSE", seed)
        match = re.fullmatch(
            r"Do side lengths (\d+), (\d+), and (\d+) form a right triangle\? "
            r"Answer yes or no\.",
            prompt,
        )
        assert match
        a, b, c = sorted(map(int, match.groups()))
        assert answer == ("yes" if a * a + b * b == c * c else "no")


def test_composed_translation_adds_both_vectors() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.TRANSFORM.COMPOSE", seed)
        match = re.fullmatch(
            r"Point \((-?\d+),(-?\d+)\) is translated by \((-?\d+),(-?\d+)\) "
            r"and then by \((-?\d+),(-?\d+)\)\. Give the final point as x,y\.",
            prompt,
        )
        assert match
        x, y, dx1, dy1, dx2, dy2 = map(int, match.groups())
        assert answer == f"{x + dx1 + dx2},{y + dy1 + dy2}"


def test_area_scale_factor_is_square_of_linear_factor() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.SIMILAR.AREA_SCALE", seed)
        match = re.fullmatch(
            r"Two similar figures have linear scale factor (\d+)\. "
            r"If the smaller figure has area (\d+), what is the larger area\?",
            prompt,
        )
        assert match
        factor, area = map(int, match.groups())
        assert int(answer) == area * factor**2


def test_cylinder_volume_matches_formula() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.VOLUME.CYLINDER", seed)
        match = re.fullmatch(
            r"A cylinder has radius (\d+) and height (\d+)\. "
            r"Give its volume in terms of pi\.",
            prompt,
        )
        assert match
        radius, height = map(int, match.groups())
        assert answer == f"{radius**2 * height}pi"


def test_cone_volume_matches_formula() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.VOLUME.CONE", seed)
        match = re.fullmatch(
            r"A cone has radius (\d+) and height (\d+)\. Give its volume in terms of pi\.",
            prompt,
        )
        assert match
        radius, height = map(int, match.groups())
        assert answer == f"{radius**2 * height // 3}pi"


def test_sphere_volume_matches_formula() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.VOLUME.SPHERE", seed)
        match = re.fullmatch(
            r"A sphere has radius (\d+)\. Give its volume in terms of pi\.",
            prompt,
        )
        assert match
        radius = int(match.group(1))
        assert answer == f"{4 * radius**3 // 3}pi"


def test_geometry_reasoning_metadata_is_curriculum_neutral() -> None:
    forbidden = {"california", "texas", "florida", "maryland", "virginia", "ontario"}
    for code, spec in domain.FAMILIES.items():
        metadata = f"{code} {spec.name} {spec.canonical_skill_code}".lower()
        assert not any(name in metadata for name in forbidden)
