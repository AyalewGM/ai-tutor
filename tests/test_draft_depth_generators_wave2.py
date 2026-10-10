"""Independent exact-arithmetic checks for second-wave draft teaching content."""
from __future__ import annotations

from collections import Counter
from fractions import Fraction

import pytest

from scripts.draft_depth_generators_wave2 import STRUCTURES, generate


def independent_answer(structure: str, a: dict[str, int]) -> Fraction:
    """Oracle derives answers from operands, never from generator's answer field."""
    if structure == "place-value-compose":
        return Fraction(100 * a["hundreds"] + 10 * a["tens"] + a["ones"])
    if structure == "place-value-digit-value":
        return Fraction(100 * a["hundreds"])
    if structure == "addition-missing-addend":
        return Fraction(a["total"] - a["first"])
    if structure == "subtraction-regroup":
        return Fraction(a["top"] - a["bottom"])
    if structure == "fraction-equivalent":
        return Fraction(a["numerator"] * a["factor"])
    if structure == "fraction-compare":
        return Fraction(a["b"] - a["a"], a["denominator"])
    if structure == "fraction-unlike-add":
        return Fraction(a["a"], a["d1"]) + Fraction(a["b"], a["d2"])
    if structure == "fraction-of-remaining":
        return Fraction(a["whole"] * (a["denominator"] - a["numerator"]), a["denominator"])
    if structure == "ratio-equivalent":
        return Fraction(a["right"] * a["factor"])
    if structure == "ratio-proportional-table":
        return Fraction(a["unit"] * a["quantity"])
    if structure == "ratio-percent-change":
        return Fraction(a["original"] * (100 + a["percent"]), 100)
    if structure == "ratio-scale-drawing":
        return Fraction(a["scale"] * a["drawing"])
    if structure == "algebra-distributive":
        return Fraction(a["factor"] * (a["x"] + a["offset"]))
    if structure == "algebra-two-step":
        return Fraction(a["total"] - a["offset"], a["coefficient"])
    if structure == "algebra-inequality":
        return Fraction((a["budget"] - a["fee"]) // a["price"])
    if structure == "algebra-slope":
        return Fraction(a["y2"] - a["y1"], a["x2"] - a["x1"])
    raise AssertionError(f"Unknown structure: {structure}")


def test_wave2_is_draft_only_and_has_128_variants() -> None:
    result = generate()
    assert result["status"] == "DRAFT_UNVERIFIED"
    assert result["review_status"] == "PENDING"
    assert result["runtime_activation"] is False
    assert result["canonical_skill_ids"] == []
    assert result["curriculum_mappings"] == []
    assert len(STRUCTURES) == len(set(STRUCTURES)) == 16
    assert len(result["items"]) == 128
    assert len({item["item_id"] for item in result["items"]}) == 128
    assert Counter(item["structure"] for item in result["items"]) == {
        structure: 8 for structure in STRUCTURES
    }
    assert len({item["provisional_skill"] for item in result["items"]}) == 4


def test_reproducible_seed_and_different_seed() -> None:
    assert generate(73, 3) == generate(73, 3)
    assert generate(73, 3)["items"] != generate(74, 3)["items"]


@pytest.mark.parametrize("seed", [0, 1, 17, 20261009, 99999])
def test_exact_oracles_misconceptions_and_teaching_scaffolds(seed: int) -> None:
    for item in generate(seed, 20)["items"]:
        structure, a = item["structure"], item["operands"]
        answer = Fraction(item["expected"])
        assert answer == independent_answer(structure, a), item["item_id"]
        assert answer >= 0
        assert Fraction(item["misconception"]["plausible_wrong_answer"]) != answer, item["item_id"]
        assert item["misconception"]["tag"] and item["misconception"]["feedback"]
        assert item["status"] == "DRAFT_UNVERIFIED"
        assert item["review_status"] == "PENDING"
        assert item["runtime_activation"] is False
        assert len(item["hints"]) == 3 and all(item["hints"])
        assert [step["phase"] for step in item["teaching_sequence"]] == [
            "concrete", "visual", "symbolic",
        ]
        assert all(step["instruction"] for step in item["teaching_sequence"])
        assert item["teaching_sequence"][1]["visual_model"]
        assert item["transfer_check"]
        if structure == "subtraction-regroup":
            assert a["bottom"] % 10 > a["top"] % 10
        if structure == "fraction-equivalent":
            assert 0 < a["numerator"] < a["denominator"]
        if structure == "fraction-compare":
            assert 0 < a["a"] < a["b"] < a["denominator"]
        if structure == "fraction-unlike-add":
            assert a["d1"] != a["d2"]
        if structure == "fraction-of-remaining":
            assert 0 < a["numerator"] < a["denominator"]
            assert a["whole"] % a["denominator"] == 0
        if structure == "algebra-inequality":
            maximum = int(answer)
            assert a["fee"] + a["price"] * maximum <= a["budget"]
            assert a["fee"] + a["price"] * (maximum + 1) > a["budget"]
        if structure == "algebra-slope":
            assert a["x2"] > a["x1"]


@pytest.mark.parametrize("bad", [True, None, 1.5, "42"])
def test_seed_type_guard(bad: object) -> None:
    with pytest.raises(TypeError):
        generate(bad)


@pytest.mark.parametrize("bad", [True, None, 1.5, "8"])
def test_variant_type_guard(bad: object) -> None:
    with pytest.raises(TypeError):
        generate(1, bad)


@pytest.mark.parametrize("bad", [-1, 0, 51])
def test_variant_bounds_guard(bad: int) -> None:
    with pytest.raises(ValueError):
        generate(1, bad)
