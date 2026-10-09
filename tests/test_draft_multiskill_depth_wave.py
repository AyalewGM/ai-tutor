"""Exact independent oracle for the draft multi-skill content-depth wave."""
from __future__ import annotations

import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/draft-multiskill-depth-wave-v0/content.draft.json"
)
DATA = json.loads(PATH.read_text(encoding="utf-8"))
LEVELS = [
    "fluency", "guided-representation", "contextual-transfer", "error-analysis"
]
OPERATIONS = {
    "add", "subtract", "multiply", "divide", "fraction_add",
    "decimal_cents_add", "perimeter", "area"
}


def expected_from_operands(item: dict) -> str:
    op = item["operation"]
    v = item["operands"]
    if op == "add":
        return str(v["a"] + v["b"])
    if op == "subtract":
        return str(v["a"] - v["b"])
    if op == "multiply":
        return str(v["a"] * v["b"])
    if op == "divide":
        quotient, remainder = divmod(v["a"], v["b"])
        assert remainder == 0
        return str(quotient)
    if op == "fraction_add":
        value = Fraction(v["a"] + v["b"], v["d"])
        return f"{value.numerator}/{value.denominator}"
    if op == "decimal_cents_add":
        value = Decimal(v["a_cents"] + v["b_cents"]) / Decimal(100)
        return f"{value:.2f}"
    if op == "perimeter":
        return str(2 * (v["length"] + v["width"]))
    if op == "area":
        return str(v["length"] * v["width"])
    raise AssertionError(f"Unknown operation: {op}")


def test_draft_isolation_and_depth_inventory() -> None:
    assert DATA["status"] == "DRAFT_UNVERIFIED"
    assert DATA["review_status"] == "PENDING"
    assert DATA["runtime_activation"] is False
    assert DATA["canonical_skill_ids"] == []
    assert DATA["curriculum_mappings"] == []
    items = DATA["practice_items"]
    assert len(items) == 64
    assert len({x["item_id"] for x in items}) == 64
    assert len({x["question"] for x in items}) == 64
    assert {x["operation"] for x in items} == OPERATIONS
    assert len(DATA["difficulty_ladders"]) == 8
    assert len(DATA["misconceptions"]) == 8
    assert all(
        len(x["hints"]) == 3
        and all(x["hints"])
        and x["worked_solution"]
        and x["misconception_tag"]
        and x["review_status"] == "PENDING"
        for x in items
    )


def test_exact_oracles_for_every_draft_problem() -> None:
    for item in DATA["practice_items"]:
        assert item["expected"] == expected_from_operands(item)
        if item["operation"] == "fraction_add":
            assert item["answer_contract"] == "simplest_fraction"
            assert Fraction(item["expected"]) > 0
        elif item["operation"] == "decimal_cents_add":
            assert item["answer_contract"] == "decimal_2_places"
            assert len(item["expected"].split(".")[1]) == 2
        else:
            assert item["answer_contract"] == "integer"


def test_every_skill_has_complete_difficulty_progression() -> None:
    by_id = {x["item_id"]: x for x in DATA["practice_items"]}
    for ladder in DATA["difficulty_ladders"]:
        assert ladder["levels"] == LEVELS
        assert len(ladder["items"]) == 8
        assert [
            by_id[item_id]["level"] for item_id in ladder["items"]
        ] == [level for level in LEVELS for _ in range(2)]
        assert all(
            by_id[item_id]["provisional_skill"] == ladder["provisional_skill"]
            for item_id in ladder["items"]
        )
