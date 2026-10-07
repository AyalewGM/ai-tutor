import re
from fractions import Fraction

import pytest

from app.canonical_problem_families import FAMILIES, LearningMode, generate

BATCH_CODES = [
    code
    for code in FAMILIES
    if code.startswith(("MATH.GEO.", "MATH.DATA.", "MATH.PROB."))
]


def test_geometry_data_batch_has_expected_depth() -> None:
    assert len(BATCH_CODES) >= 28
    types = {FAMILIES[code].problem_type for code in BATCH_CODES}
    assert {
        "MEASUREMENT",
        "ANGLE_REASONING",
        "COORDINATE_GEOMETRY",
        "TRANSFORMATION",
        "DATA_ANALYSIS",
        "TABLE_REASONING",
        "PROBABILITY",
    } <= types


@pytest.mark.parametrize("code", BATCH_CODES)
def test_batch_is_deterministic_and_mihur_authored(code: str) -> None:
    spec = FAMILIES[code]
    first = generate(code, seed=73, difficulty=spec.min_difficulty)
    second = generate(code, seed=73, difficulty=spec.min_difficulty)
    assert first == second
    assert first.provenance["origin"] == "MIHUR_AUTHORED"


@pytest.mark.parametrize("code", BATCH_CODES)
def test_batch_supports_all_learning_modes(code: str) -> None:
    spec = FAMILIES[code]
    for mode in LearningMode:
        problem = generate(code, seed=19, difficulty=spec.min_difficulty, mode=mode)
        assert problem.mode == mode


@pytest.mark.parametrize("code", BATCH_CODES)
def test_misconceptions_never_collide_with_canonical_answer(code: str) -> None:
    spec = FAMILIES[code]
    for seed in range(30):
        problem = generate(code, seed=seed, difficulty=spec.min_difficulty)
        answer = "".join(problem.canonical_answer.lower().split())
        misconception_values = {
            "".join(value.lower().split())
            for value in problem.misconception_answers.values()
        }
        assert answer not in misconception_values


@pytest.mark.parametrize("seed", range(30))
def test_rectangle_area_oracle(seed: int) -> None:
    problem = generate("MATH.GEO.AREA.RECT", seed=seed, difficulty=2)
    match = re.search(r"rectangle is (\d+) units long and (\d+) units wide", problem.prompt)
    assert match
    length, width = map(int, match.groups())
    assert int(problem.canonical_answer) == length * width


@pytest.mark.parametrize("seed", range(30))
def test_triangle_area_oracle(seed: int) -> None:
    problem = generate("MATH.GEO.AREA.TRI", seed=seed, difficulty=3)
    match = re.search(r"base (\d+) units and perpendicular height (\d+) units", problem.prompt)
    assert match
    base, height = map(int, match.groups())
    assert int(problem.canonical_answer) * 2 == base * height


@pytest.mark.parametrize("seed", range(30))
def test_prism_surface_area_oracle(seed: int) -> None:
    problem = generate("MATH.GEO.SURFACE.PRISM", seed=seed, difficulty=3)
    values = list(map(int, re.findall(r"\d+", problem.prompt)))
    length, width, height = values[-3:]
    expected = 2 * (length * width + length * height + width * height)
    assert int(problem.canonical_answer) == expected


@pytest.mark.parametrize("seed", range(30))
def test_triangle_angle_oracle(seed: int) -> None:
    problem = generate("MATH.GEO.TRIANGLE.MISSING_ANGLE", seed=seed, difficulty=3)
    angles = list(map(int, re.findall(r"\d+", problem.prompt)))
    assert sum(angles[:2]) + int(problem.canonical_answer) == 180


@pytest.mark.parametrize("seed", range(30))
def test_translation_oracle(seed: int) -> None:
    problem = generate("MATH.GEO.TRANSFORM.TRANSLATE_POINT", seed=seed, difficulty=3)
    values = list(map(int, re.findall(r"-?\d+", problem.prompt)))
    x, y, dx, dy = values
    assert problem.canonical_answer == f"({x + dx},{y + dy})"


@pytest.mark.parametrize("seed", range(30))
def test_mean_oracle(seed: int) -> None:
    problem = generate("MATH.DATA.MEAN", seed=seed, difficulty=2)
    values = list(map(int, re.findall(r"-?\d+", problem.prompt)))
    assert sum(values) == int(problem.canonical_answer) * len(values)


@pytest.mark.parametrize("seed", range(30))
def test_range_oracle(seed: int) -> None:
    problem = generate("MATH.DATA.RANGE", seed=seed, difficulty=2)
    values = list(map(int, re.findall(r"\d+", problem.prompt)))
    assert int(problem.canonical_answer) == max(values) - min(values)


@pytest.mark.parametrize("seed", range(30))
def test_simple_probability_oracle(seed: int) -> None:
    problem = generate("MATH.PROB.SIMPLE", seed=seed, difficulty=2)
    total, favorable = map(int, re.findall(r"\d+", problem.prompt))
    assert Fraction(problem.canonical_answer) == Fraction(favorable, total)


@pytest.mark.parametrize("seed", range(30))
def test_independent_probability_oracle(seed: int) -> None:
    problem = generate("MATH.PROB.INDEPENDENT.AND", seed=seed, difficulty=3)
    fractions = re.findall(r"(\d+/\d+)", problem.prompt)
    assert len(fractions) == 2
    assert Fraction(problem.canonical_answer) == Fraction(fractions[0]) * Fraction(fractions[1])


def test_curriculum_neutrality() -> None:
    forbidden = {"california", "texas", "florida", "maryland", "virginia", "ontario", "alberta"}
    for code in BATCH_CODES:
        problem = generate(code, seed=5, difficulty=FAMILIES[code].min_difficulty)
        text = (code + " " + problem.prompt + " " + str(problem.provenance)).lower()
        assert not any(word in text for word in forbidden)
