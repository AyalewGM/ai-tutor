"""Independent exact-answer oracles and safety contracts for draft generators."""
from __future__ import annotations

import math
from collections import Counter
from fractions import Fraction

import pytest

from scripts.draft_word_problem_generators import STRUCTURES, generate


def oracle(operation: str, a: dict[str, int]) -> Fraction:
    """Calculate results independently of generator wording and expected fields."""
    if operation == "subtract":
        if "end" in a:
            return Fraction(a["end"] - a["change"])
        return Fraction(a["larger"] - a["smaller"])
    if operation == "add_subtract":
        return Fraction(a["start"] + a["added"] - a["removed"])
    if operation == "multiply":
        return Fraction(a["groups"] * a["each"])
    if operation == "ceil_divide":
        return Fraction(math.ceil(Fraction(a["people"], a["capacity"])))
    if operation == "multiply_three":
        return Fraction(a["shelves"] * a["boxes"] * a["each"])
    if operation == "fraction_of_set":
        return Fraction(a["numerator"] * a["whole"], a["denominator"])
    if operation == "fraction_unknown_whole":
        return Fraction(a["part"] * a["denominator"], a["numerator"])
    if operation == "fraction_like_add":
        return Fraction(a["a"] + a["b"], a["denominator"])
    if operation == "unit_price":
        return Fraction(a["total_dollars"], a["units"])
    if operation == "percent_discount":
        return Fraction(a["price"] * (100 - a["percent"]), 100)
    if operation == "fixed_fee":
        return Fraction(a["fee"] + a["hourly"] * a["hours"])
    if operation == "perimeter":
        return Fraction(2 * (a["length"] + a["width"]))
    if operation == "area":
        return Fraction(a["length"] * a["width"])
    if operation == "volume":
        return Fraction(a["length"] * a["width"] * a["height"])
    if operation == "linear_one":
        return Fraction(a["total"] - a["fee"], a["multiplier"])
    if operation == "linear_pattern":
        return Fraction(a["first"] + (a["position"] - 1) * a["step"])
    if operation == "ticket_system":
        return Fraction(
            a["revenue"] - a["count"] * a["child_price"],
            a["adult_price"] - a["child_price"],
        )
    raise AssertionError(f"Unknown operation: {operation}")


def test_generator_reproducibility_and_seed_diversity() -> None:
    assert generate(123) == generate(123)
    assert generate(123) != generate(124)
    assert generate(123, 3)["items"] != generate(123, 4)["items"]


def test_six_domains_eighteen_distinct_structures_and_108_variants() -> None:
    data = generate()
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["review_status"] == "PENDING"
    assert data["runtime_activation"] is False
    assert data["canonical_skill_ids"] == []
    assert data["curriculum_mappings"] == []
    assert len(STRUCTURES) == len(set(STRUCTURES)) == 18
    assert data["structure_count"] == 18
    assert len(data["items"]) == 108
    assert len({x["item_id"] for x in data["items"]}) == 108
    assert len({x["provisional_skill"] for x in data["items"]}) == 6
    assert Counter(x["problem_structure"] for x in data["items"]) == {
        structure: 6 for structure in STRUCTURES
    }


@pytest.mark.parametrize("seed", [0, 1, 17, 20261009, 99999])
def test_every_generated_answer_is_exact_and_distractors_are_wrong(seed: int) -> None:
    for item in generate(seed, 12)["items"]:
        answer = Fraction(item["expected"])
        independently_calculated = oracle(item["operation"], item["operands"])
        assert answer == independently_calculated, item["item_id"]
        assert item["review_status"] == "PENDING"
        assert item["status"] == "DRAFT_UNVERIFIED"
        assert item["runtime_activation"] is False
        assert item["question"] and item["worked_solution"]
        assert len(item["hints"]) == 3
        assert all(item["hints"])
        assert item["visual_model_prompt"] and item["independent_check"]
        assert item["misconception"]["tag"]
        assert item["misconception"]["feedback"]
        wrong = Fraction(item["misconception"]["plausible_wrong_answer"])
        assert wrong != answer, item["item_id"]
        assert answer >= 0


@pytest.mark.parametrize("seed", [0, 42, 20261009])
def test_domain_specific_mathematical_invariants(seed: int) -> None:
    for item in generate(seed, 15)["items"]:
        a = item["operands"]
        structure = item["problem_structure"]
        if structure == "multiply-remainder-capacity":
            assert a["people"] % a["capacity"] > 0
            assert (int(item["expected"]) - 1) * a["capacity"] < a["people"]
            assert int(item["expected"]) * a["capacity"] >= a["people"]
        elif structure == "fraction-of-set":
            assert 0 < a["numerator"] < a["denominator"]
            assert a["whole"] % a["denominator"] == 0
        elif structure == "fraction-unknown-whole":
            assert 0 < a["numerator"] < a["denominator"]
            assert a["part"] % a["numerator"] == 0
            assert int(item["expected"]) > a["part"]
        elif structure == "fraction-like-addition":
            assert a["denominator"] > a["a"] > 0
            assert a["denominator"] > a["b"] > 0
        elif structure == "ratio-percent-discount":
            assert 0 < a["percent"] < 100
            assert 0 < int(item["expected"]) < a["price"]
        elif structure == "algebra-two-ticket-types":
            adults = int(item["expected"])
            children = a["count"] - adults
            assert adults > 0 and children > 0
            assert adults * a["adult_price"] + children * a["child_price"] == a["revenue"]
        elif structure == "geometry-volume":
            assert int(item["expected"]) > a["length"] * a["width"]


@pytest.mark.parametrize("bad", [-1, 0, 51, 1.5, "6", None])
def test_invalid_variant_count_fails_closed(bad: object) -> None:
    with pytest.raises(ValueError):
        generate(7, bad)


@pytest.mark.parametrize("bad", [True, "7", 1.5, None])
def test_invalid_seed_fails_closed(bad: object) -> None:
    with pytest.raises(ValueError):
        generate(bad)
