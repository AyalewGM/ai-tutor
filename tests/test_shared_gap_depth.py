"""Independent mathematical oracles for proposed shared-gap canonical families."""

import math
import random
import re
from decimal import Decimal
from fractions import Fraction

import pytest

from app.domains.shared_gap_depth import FAMILIES, build


@pytest.mark.parametrize("code", sorted(FAMILIES))
def test_seeded_build_is_stable_and_has_learning_metadata(code: str) -> None:
    spec = FAMILIES[code]
    assert spec.canonical_skill_code.startswith("MATH.")
    assert len(spec.modes) == 5
    assert spec.min_difficulty <= spec.max_difficulty
    for difficulty in range(spec.min_difficulty, spec.max_difficulty + 1):
        for seed in range(20):
            a = build(code, random.Random(seed), difficulty)
            b = build(code, random.Random(seed), difficulty)
            assert a == b
            assert len(a) in (4, 5)
            assert a[0] and a[1] and all(a[2])


@pytest.mark.parametrize("seed", range(60))
@pytest.mark.parametrize("difficulty", [2, 3, 4])
def test_mad_compute_matches_independent_fraction_oracle(
    seed: int, difficulty: int
) -> None:
    prompt, answer, *_ = build(
        "MATH.DATA.MAD.COMPUTE", random.Random(seed), difficulty
    )
    values = [int(v) for v in re.findall(r"-?\d+", prompt.split(". Find")[0])]
    mean = Fraction(sum(values), len(values))
    expected = sum((abs(Fraction(v) - mean) for v in values), Fraction()) / len(values)
    assert Fraction(answer) == expected


@pytest.mark.parametrize("seed", range(60))
def test_mad_comparison_oracle(seed: int) -> None:
    prompt, answer, *_ = build("MATH.DATA.MAD.COMPARE", random.Random(seed), 3)
    match = re.search(r"Set A: ([\d, -]+)\. Set B: ([\d, -]+)\.", prompt)
    assert match
    a, b = ([int(x) for x in group.split(", ")] for group in match.groups())
    def mad(values: list[int]) -> Fraction:
        mean = Fraction(sum(values), len(values))
        return sum((abs(Fraction(v) - mean) for v in values), Fraction()) / len(values)
    assert answer == ("A" if mad(a) > mad(b) else "B")


@pytest.mark.parametrize("seed", range(80))
def test_square_root_classification_oracle(seed: int) -> None:
    prompt, answer, *_ = build(
        "MATH.NS.IRRATIONAL.CLASSIFY", random.Random(seed), 3
    )
    n = int(re.search(r"sqrt\((\d+)\)", prompt).group(1))
    assert answer == ("rational" if math.isqrt(n) ** 2 == n else "irrational")


@pytest.mark.parametrize("seed", range(80))
def test_irrational_approximation_oracle(seed: int) -> None:
    prompt, answer, *_ = build(
        "MATH.NS.IRRATIONAL.APPROX", random.Random(seed), 3
    )
    n = int(re.search(r"sqrt\((\d+)\)", prompt).group(1))
    assert math.isqrt(n) ** 2 != n
    assert Decimal(answer) == Decimal(str(round(math.sqrt(n), 1)))


@pytest.mark.parametrize("seed", range(80))
def test_unit_price_oracle(seed: int) -> None:
    prompt, answer, *_ = build("MATH.FIN.UNIT_PRICE", random.Random(seed), 3)
    a = re.search(r"Pack A has (\d+) notebooks for (\d+\.\d+) dollars", prompt)
    b = re.search(r"Pack B has (\d+) notebooks for (\d+\.\d+) dollars", prompt)
    assert a and b
    unit_a = Decimal(a[2]) / int(a[1])
    unit_b = Decimal(b[2]) / int(b[1])
    assert unit_a != unit_b
    assert answer == ("A" if unit_a < unit_b else "B")


@pytest.mark.parametrize("seed", range(80))
def test_budget_arithmetic_oracle(seed: int) -> None:
    prompt, answer, *_ = build("MATH.FIN.BUDGET", random.Random(seed), 3)
    amounts = [int(x) for x in re.findall(r"(\d+) dollars", prompt)]
    assert len(amounts) == 4
    assert int(answer) == amounts[0] - sum(amounts[1:])


@pytest.mark.parametrize("seed", range(80))
def test_savings_goal_requires_ceiling_not_truncation(seed: int) -> None:
    prompt, answer, *_ = build(
        "MATH.FIN.SAVINGS_GOAL", random.Random(seed), 3
    )
    starting, weekly, goal = (
        int(x) for x in re.findall(r"(\d+) dollars", prompt)
    )
    assert (goal - starting) % weekly != 0
    assert int(answer) == (goal - starting + weekly - 1) // weekly


@pytest.mark.parametrize("seed", range(80))
def test_discount_oracle(seed: int) -> None:
    prompt, answer, *_ = build("MATH.FIN.DISCOUNT", random.Random(seed), 3)
    price, percent = (
        int(x) for x in re.search(r"costs (\d+) dollars before a (\d+)%", prompt).groups()
    )
    assert int(answer) == price * (100 - percent) // 100
