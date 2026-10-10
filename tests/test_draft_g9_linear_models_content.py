"""Draft-only exact mathematical checks for Grade 9 linear-model content."""
from __future__ import annotations

import json
from pathlib import Path

PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/draft-g9-linear-models-pilot-v0/content.draft.json"
)
DATA = json.loads(PATH.read_text(encoding="utf-8"))
ORACLES = {
    "LINEAR_EQUATIONS": [5, 8, 6, 12, 6, 9],
    "LINEAR_RELATIONS": [13, 2, 3, 2, 40, 5],
    "INEQUALITIES": [8, 6, -4, 4, 6, 3],
    "LINEAR_MODELING": [26, 115, 8, 10, 6, 3],
    "ERROR_ANALYSIS": [6, 2, -5, 9, 22, 9],
}


def test_draft_isolation_and_content_inventory() -> None:
    assert DATA["status"] == "DRAFT_UNVERIFIED"
    assert DATA["review_status"] == "PENDING"
    assert DATA["runtime_activation"] is False
    assert DATA["canonical_skill_ids"] == []
    assert DATA["curriculum_mappings"] == []
    items = DATA["practice_items"]
    assert len(items) == 30
    assert len({item["item_id"] for item in items}) == 30
    assert len({item["question"] for item in items}) == 30
    assert len(DATA["worked_examples"]) == 5
    assert len(DATA["misconceptions"]) == 5
    assert all(
        item["answer_contract"] == "integer"
        and item["review_status"] == "PENDING"
        and len(item["hints"]) == 3
        and all(item["hints"])
        and item["worked_solution"]
        and item["misconception_tag"]
        for item in items
    )


def test_independent_answer_oracles() -> None:
    for skill, expected in ORACLES.items():
        items = [
            item for item in DATA["practice_items"]
            if item["provisional_skill"] == skill
        ]
        assert len(items) == len(expected) == 6
        for item, answer in zip(items, expected):
            assert int(item["expected"]) == answer


def test_linear_equations_by_substitution() -> None:
    assert 3 * 5 + 7 == 22
    assert 5 * (8 - 2) == 30
    assert 4 * 6 + 9 == 2 * 6 + 21
    assert 12 / 3 + 5 == 9
    assert 2 * (3 * 6 - 1) == 4 * 6 + 10
    assert 4 + 3 * 9 == 31


def test_linear_relations_and_models() -> None:
    assert 2 * 5 + 3 == 13
    assert -3 * 2 + 8 == 2
    assert (10 - 4) / (2 - 0) == 3
    assert 3 * 1 + 2 == 5
    assert 3 * 3 + 2 == 11
    assert 12 + 4 * 7 == 40
    assert 5 * 5 - 7 == 18
    assert 12 + 2 * 7 == 26
    assert 25 + 15 * 6 == 115
    assert 40 + 10 * 8 == 120
    assert 90 - 6 * 10 == 30
    assert 20 + 3 * 6 == 8 + 5 * 6
    assert 15 + 12 * 3 == 17 * 3


def test_inequalities_at_boundaries() -> None:
    assert 8 + 5 > 12
    assert not (7 + 5 > 12)
    assert 3 * 6 <= 18
    assert not (3 * 7 <= 18)
    assert -2 * (-4) < 10
    assert not (-2 * (-5) < 10)
    assert 4 * 4 - 3 >= 13
    assert not (4 * 3 - 3 >= 13)
    assert 8 * 6 <= 50
    assert not (8 * 7 <= 50)
    assert 5 - 3 >= 2
    assert not (5 - 4 >= 2)


def test_error_analysis_corrections() -> None:
    assert 2 * 6 + 3 == 15
    assert (10 - 2) / 4 == 2
    assert -3 * (-5) > 12
    assert 4 * 0 + 9 == 9
    assert 10 + 3 * 4 == 22
    assert 2 * (9 + 1) == 20
