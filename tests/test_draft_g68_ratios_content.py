"""Draft-only exact arithmetic oracle for Grade 6–8 ratio content."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/draft-g68-ratios-pilot-v0/content.draft.json"
)
DATA = json.loads(PATH.read_text(encoding="utf-8"))
ORACLES = {
    "RATIO_INTERPRETATION": ["2:3", "3/5", "2:3", "15", "2:5"],
    "UNIT_RATE": ["4", "14", "12", "15/2", "63"],
    "EQUIVALENT_RATIOS": ["35", "15", "60", "24", "36"],
    "PERCENT_AS_RATIO": ["20", "30", "10", "25", "1/8"],
    "PROPORTIONAL_REASONING": ["42", "27", "20", "15", "5/2"],
}


def test_isolated_draft_inventory_and_scaffolding() -> None:
    assert DATA["status"] == "DRAFT_UNVERIFIED"
    assert DATA["review_status"] == "PENDING"
    assert DATA["runtime_activation"] is False
    assert DATA["mastery_updater"] is False
    assert DATA["canonical_skill_ids"] == []
    assert DATA["curriculum_mappings"] == []
    items = DATA["practice_items"]
    assert len(items) == 25
    assert len({x["item_id"] for x in items}) == 25
    assert len({x["question"] for x in items}) == 25
    assert len(DATA["worked_examples"]) == 5
    assert len(DATA["misconceptions"]) == 5
    assert all(
        len(x["hints"]) == 3
        and all(x["hints"])
        and x["solution_summary"]
        and x["misconception_tag"]
        and x["review_status"] == "PENDING"
        for x in items
    )


def test_independent_expected_answer_oracles() -> None:
    for skill, expected in ORACLES.items():
        items = [x for x in DATA["practice_items"] if x["provisional_skill"] == skill]
        assert len(items) == len(expected) == 5
        for item, answer in zip(items, expected):
            if ":" in answer:
                assert item["answer_contract"] == "ratio_pair"
                assert item["expected"] == answer
                a, b = (int(v) for v in answer.split(":"))
                assert a > 0 and b > 0
                assert Fraction(a, b).denominator == b
            else:
                value = Fraction(answer)
                assert Fraction(item["expected"]) == value
                assert value >= 0
                if item["answer_contract"] == "simplest_fraction":
                    assert str(value) == answer


def test_original_math_relations_exact() -> None:
    assert Fraction(12, 18) == Fraction(2, 3)
    assert Fraction(15, 25) == Fraction(3, 5)
    assert Fraction(6, 15) == Fraction(2, 5)
    assert Fraction(3, 5) * 25 == 15
    assert Fraction(45, 6) == Fraction(15, 2)
    assert Fraction(35, 5) * 9 == 63
    assert Fraction(4, 7) == Fraction(20, 35)
    assert Fraction(3, 8) == Fraction(15, 40)
    assert Fraction(15, 2) * 8 == 60
    assert Fraction(9, 3) * 8 == 24
    assert Fraction(12, 5) * 15 == 36
    assert Fraction(25, 100) * 80 == 20
    assert Fraction(18, 60) * 100 == 30
    assert Fraction(20, 100) * 50 == 10
    assert Fraction(50 - 40, 40) * 100 == 25
    assert Fraction(125, 1000) == Fraction(1, 8)
    assert 6 * 7 == 42
    assert Fraction(9, 2) * 6 == 27
    assert Fraction(8, 100) * 250 == 20
    assert Fraction(45, Fraction(18, 6)) == 15
    assert Fraction(10, 4) == Fraction(5, 2)


ENRICHMENT = json.loads(
    (PATH.parent / "enrichment.draft.json").read_text(encoding="utf-8")
)
ENRICHMENT_ORACLES = {
    "RATIO_INTERPRETATION": ["2:3", "2/5", "64", "2/5"],
    "UNIT_RATE": ["3", "6", "15", "3/2"],
    "EQUIVALENT_RATIOS": ["27", "12", "44", "12"],
    "PERCENT_AS_RATIO": ["30", "25", "90", "25"],
    "PROPORTIONAL_REASONING": ["36", "35", "8", "15"],
}


def test_enrichment_original_ladders_and_isolation() -> None:
    assert ENRICHMENT["status"] == "DRAFT_UNVERIFIED"
    assert ENRICHMENT["review_status"] == "PENDING"
    assert ENRICHMENT["runtime_activation"] is False
    assert ENRICHMENT["canonical_skill_ids"] == []
    assert ENRICHMENT["curriculum_mappings"] == []
    items = ENRICHMENT["practice_items"]
    assert len(items) == 20
    assert len({x["item_id"] for x in items}) == 20
    assert len({x["question"] for x in items}) == 20
    assert len(ENRICHMENT["difficulty_ladders"]) == 5
    assert all(
        len(x["hints"]) == 3
        and x["worked_solution"]
        and x["diagnostic_misconception"]
        and x["review_status"] == "PENDING"
        for x in items
    )
    for ladder in ENRICHMENT["difficulty_ladders"]:
        assert ladder["progression"] == [
            "Fluency", "Conceptual", "Transfer", "Error analysis"
        ]
        assert len(ladder["items"]) == 4


def test_enrichment_independent_exact_answers() -> None:
    for skill, expected in ENRICHMENT_ORACLES.items():
        items = [
            x for x in ENRICHMENT["practice_items"]
            if x["provisional_skill"] == skill
        ]
        assert len(items) == len(expected) == 4
        for item, answer in zip(items, expected):
            assert item["expected"] == answer
            if ":" in answer:
                assert item["answer_contract"] == "ratio_pair"
                a, b = (int(v) for v in answer.split(":"))
                assert a > 0 and b > 0
                assert Fraction(a, b).denominator == b
            else:
                assert Fraction(item["expected"]) == Fraction(answer)
                if item["answer_contract"] == "simplest_fraction":
                    assert str(Fraction(answer)) == answer


def test_enrichment_transfer_and_error_analysis_oracles() -> None:
    assert 40 + Fraction(3, 5) * 40 == 64
    assert Fraction(8, 20) == Fraction(2, 5)
    assert Fraction(9, Fraction(3, 2)) == 6
    assert Fraction(12, 8) == Fraction(3, 2)
    assert Fraction(12, 3) * 11 == 44
    assert Fraction(4, 6) == Fraction(8, 12)
    assert 120 - Fraction(25, 100) * 120 == 90
    assert Fraction(100 - 80, 80) * 100 == 25
    assert Fraction(6, Fraction(3, 4)) == 8
    assert Fraction(6, 2) * 5 == 15
