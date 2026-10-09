"""Independent arithmetic and reasoning-structure checks for draft word problems."""
from __future__ import annotations

import json
import math
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/draft-word-problem-structures-v0/content.draft.json"
)
DATA = json.loads(PATH.read_text(encoding="utf-8"))


def exact_answer(item: dict) -> str:
    op = item["operation"]
    a = item["operands"]
    if op == "add":
        value = a[0] + a[1]
    elif op == "subtract":
        value = a[0] - a[1]
    elif op == "add_subtract":
        value = a[0] + a[1] - a[2]
    elif op == "subtract_three":
        value = a[0] - a[1] - a[2]
    elif op == "multiply":
        value = a[0] * a[1]
    elif op == "divide":
        value = Fraction(a[0], a[1])
    elif op == "ceil_divide":
        value = math.ceil(Fraction(a[0], a[1]))
    elif op == "multiply_three":
        value = math.prod(a)
    elif op == "fraction_of":
        value = Fraction(a[0] * a[2], a[1])
    elif op == "fraction_remaining":
        value = Fraction((a[1] - a[0]) * a[2], a[1])
    elif op in {"fraction_times", "whole_from_part"}:
        value = Fraction(a[0] * a[2], a[1])
    elif op == "fraction_part_total":
        value = Fraction(a[0], a[1])
    elif op == "fraction_difference":
        value = Fraction(a[0], a[1]) - Fraction(a[2], a[3])
    elif op == "fraction_add_subtract":
        value = (
            Fraction(a[0], a[1]) - Fraction(a[2], a[3])
            + Fraction(a[4], a[5])
        )
    elif op == "cents_unit":
        value = Decimal(a[0]) / Decimal(a[1] * 100)
    elif op == "scale":
        value = Fraction(a[0] * a[2], a[1])
    elif op == "ratio_share":
        value = Fraction(a[0] * a[2], a[1] + a[2])
    elif op == "discount":
        value = Fraction(a[0] * (100 - a[1]), 100)
    elif op == "increase":
        value = Fraction(a[0] * (100 + a[1]), 100)
    elif op == "rate_time":
        value = Fraction(a[0] * a[1], a[2])
    elif op == "fixed_rate":
        value = a[0] + a[1] * a[2]
    elif op == "inverse_rate":
        value = Fraction(a[2] * a[1], a[0])
    elif op == "perimeter_missing":
        value = Fraction(a[0], 2) - a[1]
    elif op == "composite_area":
        value = a[0] * a[1] + a[2] * a[3]
    elif op == "area_difference":
        value = a[0] * a[1] - a[2] * a[3]
    elif op == "metres_cm":
        value = a[0] * 100 + a[1]
    elif op == "elapsed_after_three":
        value = a[0] + a[1] - 60
    elif op == "volume":
        value = math.prod(a)
    elif op == "square_area_increase":
        value = a[1] ** 2 - a[0] ** 2
    elif op == "linear_one":
        value = Fraction(a[2] - a[1], a[0])
    elif op == "two_plans":
        value = Fraction(a[2] - a[0], a[1] - a[3])
    elif op == "consecutive_three":
        value = Fraction(a[0] - 3, 3) + 2
    elif op == "arithmetic_pattern":
        value = a[0] + a[1] * (a[2] - 1)
    elif op == "linear_decrease":
        value = Fraction(a[0] - a[2], a[1])
    elif op == "ticket_system":
        value = Fraction(a[3] - a[0] * a[2], a[1] - a[2])
    elif op == "ceil_threshold":
        value = math.ceil(Fraction(a[2] - a[0], a[1]))
    elif op == "slope":
        value = Fraction(a[2] - a[0], a[3] - a[1])
    else:
        raise AssertionError(f"Unrecognized operation: {op}")
    if item["answer_contract"] == "decimal_2_places":
        assert isinstance(value, Decimal)
        return f"{value:.2f}"
    if item["answer_contract"] == "simplest_fraction":
        assert isinstance(value, Fraction)
        assert value.denominator > 1
        return f"{value.numerator}/{value.denominator}"
    assert Fraction(value).denominator == 1
    return str(int(value))


def test_draft_structure_and_isolation() -> None:
    assert DATA["status"] == "DRAFT_UNVERIFIED"
    assert DATA["review_status"] == "PENDING"
    assert DATA["runtime_activation"] is False
    assert DATA["canonical_skill_ids"] == []
    assert DATA["curriculum_mappings"] == []
    items = DATA["practice_items"]
    assert len(items) == 48
    assert len({item["item_id"] for item in items}) == 48
    assert len({item["question"] for item in items}) == 48
    assert len(DATA["coverage"]) == 6
    for item in items:
        assert len(item["hints"]) == 3
        assert all(item["hints"])
        assert item["worked_solution"]
        assert item["misconception_tag"]
        assert item["review_status"] == "PENDING"


def test_distinct_reasoning_structures_per_family() -> None:
    for coverage in DATA["coverage"]:
        items = [
            x for x in DATA["practice_items"]
            if x["provisional_skill"] == coverage["provisional_skill"]
        ]
        assert len(items) == 8
        assert len(set(coverage["structures"])) == 8
        assert {x["problem_structure"] for x in items} == set(
            coverage["structures"]
        )


def test_exact_oracle_for_every_word_problem() -> None:
    for item in DATA["practice_items"]:
        assert item["expected"] == exact_answer(item)


def test_word_problem_interpretation_edge_cases() -> None:
    by_structure = {
        x["problem_structure"]: x for x in DATA["practice_items"]
    }
    assert by_structure["remainder-interpretation"]["expected"] == "10"
    assert by_structure["fraction-multi-step"]["expected"] == "3/4"
    assert by_structure["elapsed-time"]["expected"] == "80"
    assert by_structure["inequality-minimum"]["expected"] == "8"
    assert by_structure["fraction-of-unknown-whole"]["expected"] == "28"
    assert by_structure["two-unknowns"]["expected"] == "20"
