"""Independent mathematical checks for seeded draft fraction remediation."""
from fractions import Fraction

import pytest

from scripts.draft_g45_fraction_remediation_variants import FAMILIES, PHASES, generate


def _independent_oracle(item: dict[str, str]) -> Fraction:
    import re

    q = item["question"]
    nums = [int(n) for n in re.findall(r"\d+", q)]
    family = item["family"]
    if family == "reference-whole":
        total, selected = nums
        return Fraction(selected, total)
    if family == "number-line-intervals":
        _, end, intervals, jump = nums
        return Fraction(end * jump, intervals)
    if family == "equivalence":
        numerator, denominator, target_denominator = nums
        return Fraction(numerator * target_denominator, denominator)
    if family == "fraction-addition":
        a, d1, b, d2 = nums
        assert d1 == d2
        return Fraction(a + b, d1)
    if family == "compare-size":
        a, b, c, d = nums
        return max(Fraction(a, b), Fraction(c, d))
    if family == "remaining-whole":
        total, _, first, _, second = nums
        after_first = Fraction(total) * (1 - Fraction(1, first))
        return after_first * (1 - Fraction(1, second))
    raise AssertionError(family)


@pytest.mark.parametrize("seed", [0, 1, 42, 20261009, 999999])
def test_reproducible_unique_exact_and_draft_only(seed: int) -> None:
    result = generate(seed=seed, variants_per_phase=4)
    assert result == generate(seed=seed, variants_per_phase=4)
    assert result["status"] == "DRAFT_UNVERIFIED"
    assert result["review_status"] == "PENDING"
    assert result["runtime_activation"] is False
    assert result["mastery_updater"] is False
    assert result["canonical_skill_ids"] == []
    assert result["curriculum_mappings"] == []
    variants = result["variants"]
    assert len(variants) == len(FAMILIES) * len(PHASES) * 4
    assert len({item["question"] for item in variants}) == len(variants)
    assert len({item["variant_id"] for item in variants}) == len(variants)
    for item in variants:
        assert item["family"] in FAMILIES
        assert item["phase"] in PHASES
        assert item["review_status"] == "PENDING"
        assert Fraction(item["expected"]) == _independent_oracle(item), item
        assert Fraction(item["expected"]) != Fraction(item["misconception_answer"]), item
        assert item["mathematical_reasoning"]


@pytest.mark.parametrize("invalid", [0, -1, 31, 1.5, True])
def test_invalid_counts_fail_closed(invalid: object) -> None:
    with pytest.raises(ValueError):
        generate(variants_per_phase=invalid)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid", [True, 1.5, "3"])
def test_invalid_seed_fail_closed(invalid: object) -> None:
    with pytest.raises(ValueError):
        generate(seed=invalid)  # type: ignore[arg-type]
