import random
import re

from app.domains import measurement_spatial as domain
from app.canonical_problem_families import LearningMode


CODES = sorted(domain.FAMILIES)


def _build(code: str, seed: int = 17):
    return domain.build(code, random.Random(seed), 3)


def test_measurement_spatial_batch_has_twenty_families() -> None:
    assert len(CODES) == 20
    skills = {domain.FAMILIES[code].canonical_skill_code for code in CODES}
    assert {
        "MATH.MEAS.UNIT_CONVERSION",
        "MATH.MEAS.TIME",
        "MATH.GEO.ANGLES",
        "MATH.GEO.COORDINATE",
        "MATH.GEO.TRANSFORMATIONS",
        "MATH.GEO.SIMILARITY",
    } <= skills


def test_measurement_spatial_generation_is_deterministic() -> None:
    for code in CODES:
        assert _build(code, 91) == _build(code, 91), code
        assert domain.FAMILIES[code].modes == frozenset(LearningMode), code


def test_measurement_spatial_misconceptions_do_not_collide_with_truth() -> None:
    for code in CODES:
        for seed in range(12):
            _, answer, _, misconceptions = _build(code, seed)
            truth = "".join(answer.lower().split())
            for candidate in misconceptions.values():
                assert "".join(candidate.lower().split()) != truth, (code, seed)


def test_metric_length_conversion_uses_base_ten_units() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.MEAS.LENGTH.METRIC", seed)
        meters = int(re.search(r"Convert (\d+) meters", prompt).group(1))
        assert int(answer) == meters * 100


def test_elapsed_time_matches_minute_difference() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.MEAS.TIME.ELAPSED", seed)
        match = re.fullmatch(
            r"An activity starts at (\d+):(\d+) and ends at (\d+):(\d+)\. How many minutes does it last\?",
            prompt,
        )
        assert match
        sh, sm, eh, em = map(int, match.groups())
        assert int(answer) == (eh * 60 + em) - (sh * 60 + sm)


def test_coordinate_midpoint_matches_average_oracle() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.GEO.COORD.MIDPOINT", seed)
        match = re.fullmatch(
            r"Find the midpoint of \((-?\d+),(-?\d+)\) and \((-?\d+),(-?\d+)\)\. Give x,y\.",
            prompt,
        )
        assert match
        x1, y1, x2, y2 = map(int, match.groups())
        mx, my = map(int, answer.split(","))
        assert 2 * mx == x1 + x2
        assert 2 * my == y1 + y2


def test_coordinate_distance_matches_pythagorean_oracle() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.GEO.COORD.DISTANCE", seed)
        match = re.fullmatch(
            r"Find the distance between \((-?\d+),(-?\d+)\) and \((-?\d+),(-?\d+)\)\.",
            prompt,
        )
        assert match
        x1, y1, x2, y2 = map(int, match.groups())
        distance = int(answer)
        assert distance * distance == (x2 - x1) ** 2 + (y2 - y1) ** 2


def test_rotation_90_counterclockwise_uses_negative_y_x_rule() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.GEO.TRANSFORM.ROTATE_90", seed)
        match = re.fullmatch(
            r"Rotate \((-?\d+),(-?\d+)\) 90 degrees counterclockwise about the origin\. Give x,y\.",
            prompt,
        )
        assert match
        x, y = map(int, match.groups())
        assert answer == f"{-y},{x}"


def test_similarity_uses_one_multiplicative_scale_factor() -> None:
    for seed in range(15):
        prompt, answer, _, _ = _build("MATH.GEO.SIMILAR.SCALE", seed)
        match = re.fullmatch(
            r"Two figures are similar\. A side of length (\d+) corresponds to (\d+)\. "
            r"If another original side is (\d+), what is its corresponding length\?",
            prompt,
        )
        assert match
        original, image, other = map(int, match.groups())
        scale = image // original
        assert int(answer) == other * scale


def test_measurement_spatial_metadata_is_curriculum_neutral() -> None:
    forbidden = {"california", "texas", "florida", "maryland", "virginia", "ontario", "alberta"}
    for code, spec in domain.FAMILIES.items():
        metadata = f"{code} {spec.name} {spec.canonical_skill_code}".lower()
        assert not any(name in metadata for name in forbidden)
