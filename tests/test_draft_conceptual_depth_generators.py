"""Independent mathematical and teaching-depth checks for conceptual draft wave."""
from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pytest

from scripts.draft_conceptual_depth_generators import STRUCTURES, generate


def oracle(op: str, a: dict[str, int]) -> Fraction:
    """Compute independently of the generator's authored answer string."""
    if op == "fraction_equivalence":
        return Fraction(a["numerator"] * a["scale"])
    if op == "fraction_compare":
        return Fraction(1 if a["a"] * a["d"] > a["c"] * a["b"] else 2)
    if op == "fraction_unlike_add":
        return Fraction(a["a"], a["b"]) + Fraction(a["c"], a["d"])
    if op == "integer_temperature":
        return Fraction(a["start"] - a["drop"])
    if op == "integer_subtract_negative":
        return Fraction(a["start"] + a["magnitude"])
    if op == "integer_distance":
        return Fraction(abs(a["right"] - a["left"]))
    if op == "ratio_recipe":
        return Fraction(a["ingredient"] * a["target"], a["batches"])
    if op == "ratio_partition":
        return Fraction(a["total"] * a["a"], a["a"] + a["b"])
    if op == "percent_original":
        return Fraction(a["sale"] * 100, 100 - a["discount"])
    if op == "algebra_two_sided":
        return Fraction(a["rhs"] - a["constant"], a["left"] - a["right"])
    if op == "algebra_slope":
        return Fraction(a["y2"] - a["y1"], a["x2"] - a["x1"])
    if op == "algebra_linear_eval":
        return Fraction(a["multiplier"] * a["x"] + a["constant"])
    raise AssertionError(f"Missing independent oracle: {op}")


def test_twelve_structures_have_meaningful_distinct_conceptual_depth() -> None:
    data = generate()
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["review_status"] == "PENDING"
    assert data["runtime_activation"] is False
    assert data["canonical_skill_ids"] == []
    assert data["curriculum_mappings"] == []
    assert len(STRUCTURES) == len(set(STRUCTURES)) == 12
    assert data["structure_count"] == 12
    assert len(data["items"]) == 72
    assert Counter(x["provisional_structure"] for x in data["items"]) == {
        structure: 6 for structure in STRUCTURES
    }
    assert len({x["teaching"]["invariant"] for x in data["items"]}) == 12
    assert len({x["teaching"]["visual_model"] for x in data["items"]}) == 12
    assert len({x["diagnostic"]["misconception"] for x in data["items"]}) == 12


@pytest.mark.parametrize("seed", [0, 1, 7, 19, 20261009, 999999])
def test_exact_oracles_noncolliding_distractors_and_support(seed: int) -> None:
    for item in generate(seed, 15)["items"]:
        answer = Fraction(item["expected"])
        assert answer == oracle(item["operation"], item["operands"]), item["item_id"]
        assert answer != Fraction(item["diagnostic"]["plausible_wrong_answer"])
        assert item["diagnostic"]["feedback"]
        assert item["independent_check"]
        assert item["status"] == "DRAFT_UNVERIFIED"
        assert item["review_status"] == "PENDING"
        assert item["runtime_activation"] is False
        assert len(item["teaching"]["socratic_questions"]) == 3
        assert len(item["teaching"]["hint_sequence"]) == 3
        assert all(item["teaching"]["hint_sequence"])
        assert item["teaching"]["after_first_error"]
        assert item["teaching"]["after_second_error"]
        assert item["teaching"]["after_third_error"]
        assert item["teaching"]["alternative_strategy"]
        assert all(item["mastery_requirement"].values())
        a = item["operands"]
        if item["operation"] == "fraction_compare":
            assert a["a"] * a["d"] != a["c"] * a["b"]
        elif item["operation"] == "fraction_unlike_add":
            assert a["b"] != a["d"]
        elif item["operation"] == "ratio_recipe":
            assert a["batches"] > 1
            assert a["target"] > a["batches"]
        elif item["operation"] == "ratio_partition":
            assert 0 < answer < a["total"]
        elif item["operation"] == "percent_original":
            assert answer > a["sale"] > 0
        elif item["operation"] == "algebra_two_sided":
            assert a["left"] != a["right"]
            assert a["left"] * answer + a["constant"] == a["right"] * answer + a["rhs"]
        elif item["operation"] == "algebra_slope":
            assert a["x1"] != a["x2"]


def test_seed_is_reproducible_and_variants_have_unique_ids() -> None:
    assert generate(7, 4) == generate(7, 4)
    assert generate(7, 4) != generate(8, 4)
    data = generate(7, 20)["items"]
    assert len({x["item_id"] for x in data}) == len(data)


@pytest.mark.parametrize("bad", [True, None, "7", 3.5])
def test_invalid_seed_type_rejected(bad: object) -> None:
    with pytest.raises(TypeError):
        generate(bad)


@pytest.mark.parametrize("bad", [True, None, "7", 3.5])
def test_invalid_variant_type_rejected(bad: object) -> None:
    with pytest.raises(TypeError):
        generate(7, bad)


@pytest.mark.parametrize("bad", [-1, 0, 51])
def test_variant_bounds_rejected(bad: int) -> None:
    with pytest.raises(ValueError):
        generate(7, bad)


def test_independent_unseen_transfer_per_concept() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "docs/curriculum/drafts/draft-word-problem-structures-v0"
        / "conceptual_transfer.draft.json"
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["review_status"] == "PENDING"
    assert data["runtime_activation"] is False
    assert data["mastery_activation"] is False
    assert data["canonical_skill_ids"] == []
    assert data["curriculum_mappings"] == []
    transfers = data["transfers"]
    assert len(transfers) == 12
    assert {x["provisional_structure"] for x in transfers} == set(STRUCTURES)
    assert len({x["question"] for x in transfers}) == 12
    independent_answers = {
        "fraction-equivalence": Fraction(5 * 36, 9),
        "fraction-compare": Fraction(1 if 7 * 8 > 5 * 10 else 2),
        "fraction-unlike-add": Fraction(3, 4) + Fraction(5, 6),
        "integer-temperature-change": Fraction(-9 - 7),
        "integer-subtract-negative": Fraction(-12 + 7),
        "integer-distance": Fraction(abs(9 - (-13))),
        "ratio-recipe-scale": Fraction(7 * 10, 4),
        "ratio-partition": Fraction(168 * 3, 3 + 5),
        "percent-original-price": Fraction(96 * 100, 100 - 20),
        "algebra-two-sided": Fraction(47 - 5, 9 - 3),
        "algebra-slope": Fraction(-1 - 11, 5 - (-3)),
        "algebra-linear-evaluation": Fraction(7 * 9 + 11),
    }
    for transfer in transfers:
        assert transfer["status"] == "DRAFT_UNVERIFIED"
        assert transfer["review_status"] == "PENDING"
        assert Fraction(transfer["expected"]) == independent_answers[
            transfer["provisional_structure"]
        ]
        assert transfer["required_reasoning"]
        assert transfer["independent_check"]
        assert len(transfer["assessment_rubric"]) == 3
    training = {x["question"] for x in generate(20261009, 10)["items"]}
    assert not (training & {x["question"] for x in transfers})
