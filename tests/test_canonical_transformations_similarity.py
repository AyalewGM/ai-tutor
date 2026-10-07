import random
import re

from app.domains import transformations_similarity as domain

CODES = sorted(domain.FAMILIES)


def _build(code: str, seed: int = 41):
    return domain.build(code, random.Random(seed), 3)[:4]


def _parse_point(text: str) -> tuple[int, int]:
    x, y = text.split(",")
    return int(x), int(y)


def test_transform_similarity_batch_has_twelve_families() -> None:
    assert len(CODES) == 12
    expected = {"DIAGNOSTIC", "GUIDED", "INDEPENDENT", "MASTERY", "REVIEW"}
    assert all(
        {mode.value for mode in domain.FAMILIES[code].modes} == expected for code in CODES
    )


def test_transform_similarity_is_deterministic() -> None:
    for code in CODES:
        assert domain.build(code, random.Random(73), 3) == domain.build(
            code, random.Random(73), 3
        ), code


def test_misconceptions_do_not_equal_truth() -> None:
    for code in CODES:
        for seed in range(20):
            _, answer, _, misconceptions = _build(code, seed)
            truth = "".join(answer.lower().split())
            for candidate in misconceptions.values():
                assert "".join(candidate.lower().split()) != truth, (code, seed)


def test_reflection_y_equals_x_swaps_coordinates() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.TRANSFORM.REFLECT_Y_EQ_X", seed)
        x, y = map(int, re.search(r"Reflect \((-?\d+),(-?\d+)\)", prompt).groups())
        assert _parse_point(answer) == (y, x)


def test_clockwise_rotation_matches_coordinate_rule() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.TRANSFORM.ROTATE_90_CW", seed)
        x, y = map(int, re.search(r"Rotate \((-?\d+),(-?\d+)\)", prompt).groups())
        assert _parse_point(answer) == (y, -x)


def test_half_turn_matches_coordinate_rule() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.TRANSFORM.ROTATE_180", seed)
        x, y = map(int, re.search(r"Rotate \((-?\d+),(-?\d+)\)", prompt).groups())
        assert _parse_point(answer) == (-x, -y)


def test_composition_applies_translation_before_reflection() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.TRANSFORM.COMPOSE", seed)
        match = re.fullmatch(
            r"Start at \((-?\d+),(-?\d+)\)\. Translate by <(-?\d+),(-?\d+)>, "
            r"then reflect across the x-axis\. Give the final x,y\.",
            prompt,
        )
        assert match
        x, y, dx, dy = map(int, match.groups())
        assert _parse_point(answer) == (x + dx, -(y + dy))


def test_perimeter_area_and_volume_use_correct_scale_powers() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.SIMILAR.PERIMETER_SCALE", seed)
        perimeter, scale = map(
            int, re.search(r"perimeter (\d+).*scale factor (\d+)", prompt).groups()
        )
        assert int(answer) == perimeter * scale

        prompt, answer, _, _ = _build("MATH.GEO.SIMILAR.AREA_SCALE", seed)
        area, scale = map(
            int, re.search(r"area (\d+).*scale factor (\d+)", prompt).groups()
        )
        assert int(answer) == area * scale**2

        prompt, answer, _, _ = _build("MATH.GEO.SIMILAR.VOLUME_SCALE", seed)
        volume, scale = map(
            int, re.search(r"volume (\d+).*scale factor (\d+)", prompt).groups()
        )
        assert int(answer) == volume * scale**3


def test_dilation_preserves_angle_measure() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.GEO.SIMILAR.ANGLE_INVARIANT", seed)
        angle = int(re.search(r"measures (\d+) degrees", prompt).group(1))
        assert int(answer) == angle


def test_transform_similarity_content_is_curriculum_neutral() -> None:
    forbidden = {
        "california",
        "texas",
        "florida",
        "maryland",
        "virginia",
        "ontario",
        "alberta",
    }
    for code, spec in domain.FAMILIES.items():
        metadata = f"{code} {spec.name} {spec.canonical_skill_code}".lower()
        assert not any(name in metadata for name in forbidden)


def test_coordinate_visual_specs_are_accessibility_described() -> None:
    for code in (
        "MATH.GEO.TRANSFORM.REFLECT_Y_EQ_X",
        "MATH.GEO.TRANSFORM.ROTATE_90_CW",
        "MATH.GEO.TRANSFORM.ROTATE_180",
    ):
        built = domain.build(code, random.Random(91), 3)
        assert len(built) == 5
        visual = built[4]
        assert visual["type"] == "coordinate_point"
        assert isinstance(visual["aria_label"], str)
        assert visual["aria_label"]
