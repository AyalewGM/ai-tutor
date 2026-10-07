import random
import re
from fractions import Fraction

from app.domains import proportional_representation as domain

CODES = sorted(domain.FAMILIES)


def _build(code: str, seed: int = 43):
    return domain.build(code, random.Random(seed), 3)


def test_proportional_representation_batch_has_eight_families() -> None:
    assert len(CODES) == 8
    expected = {"DIAGNOSTIC", "GUIDED", "INDEPENDENT", "MASTERY", "REVIEW"}
    assert all(
        {mode.value for mode in domain.FAMILIES[code].modes} == expected for code in CODES
    )


def test_proportional_representation_is_deterministic() -> None:
    for code in CODES:
        assert _build(code, 79) == _build(code, 79), code


def test_proportional_misconceptions_do_not_collide_with_truth() -> None:
    for code in CODES:
        for seed in range(15):
            _, answer, _, misconceptions = _build(code, seed)
            truth = "".join(answer.lower().split())
            for candidate in misconceptions.values():
                assert "".join(candidate.lower().split()) != truth, (code, seed)


def test_table_constant_matches_y_over_x() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.PROP.CONSTANT.TABLE", seed)
        pairs = [
            tuple(map(int, pair))
            for pair in re.findall(r"\((\d+), (\d+)\)", prompt)
        ]
        assert pairs
        assert all(Fraction(y, x) == int(answer) for x, y in pairs)


def test_equation_from_rate_uses_y_equals_kx() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.PROP.EQUATION.FROM_RATE", seed)
        rate = int(re.search(r"unit rate (\d+)", prompt).group(1))
        assert answer == f"y={rate}x"


def test_table_equation_comparison_uses_unit_rates() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.PROP.COMPARE.TABLE_EQUATION", seed)
        pairs = [
            tuple(map(int, pair))
            for pair in re.findall(r"\((\d+), (\d+)\)", prompt)
        ]
        equation_rate = int(re.search(r"Relationship B is y=(\d+)x", prompt).group(1))
        table_rate = Fraction(pairs[0][1], pairs[0][0])
        expected = "table" if table_rate > equation_rate else "equation"
        assert answer == expected


def test_complex_unit_rate_matches_fraction_division() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.RATE.COMPLEX.UNIT", seed)
        match = re.fullmatch(
            r"A machine processes ([0-9/]+) units in ([0-9/]+) hour\. "
            r"How many units does it process per hour\?",
            prompt,
        )
        assert match
        quantity, time = map(Fraction, match.groups())
        assert Fraction(answer) == quantity / time


def test_context_point_interpretation_preserves_axis_meaning() -> None:
    for seed in range(20):
        prompt, answer, _, _ = _build("MATH.PROP.POINT.INTERPRET", seed)
        x, y = map(int, re.search(r"contains \((\d+),(\d+)\)", prompt).groups())
        assert answer == f"{y} miles in {x} hours"


def test_proportional_representation_metadata_is_curriculum_neutral() -> None:
    forbidden = {"california", "texas", "florida", "maryland", "virginia", "ontario"}
    for code, spec in domain.FAMILIES.items():
        metadata = f"{code} {spec.name} {spec.canonical_skill_code}".lower()
        assert not any(name in metadata for name in forbidden)
