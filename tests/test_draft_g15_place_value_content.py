"""Draft-only mathematical checks for original Grades 1–5 place-value items."""
from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/draft-g15-place-value-pilot-v0/content.draft.json"
)
DATA = json.loads(DATA_PATH.read_text(encoding="utf-8"))
ORACLES = {
    "DIGIT_VALUE": [40, 3, 60, 200, 8000, 7000],
    "COMPOSE_DECOMPOSE": [36, 50, 427, 6342, 70905, 340608],
    "COMPARE_ORDER": [85, 307, 4109, 2405, 20001, 305004],
    "ROUNDING": [50, 70, 300, 700, 49000, 305000],
    "ERROR_ANALYSIS": [20, 305, 5900, 24000, 30, 70050],
}


def test_place_value_draft_is_isolated_and_complete() -> None:
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
    assert {item["grade_suggestion"] for item in items} == {1, 2, 3, 4, 5}
    assert all(
        item["answer_contract"] == "nonnegative_integer"
        and item["review_status"] == "PENDING"
        and len(item["hints"]) == 3
        and all(item["hints"])
        and item["worked_solution"]
        and item["misconception_tag"]
        for item in items
    )


def test_place_value_item_answers_match_independent_oracles() -> None:
    for skill, expected in ORACLES.items():
        items = [
            item for item in DATA["practice_items"]
            if item["provisional_skill"] == skill
        ]
        assert len(items) == len(expected) == 6
        for item, answer in zip(items, expected):
            assert int(item["expected"]) == answer
            assert answer >= 0


def test_place_value_mathematical_properties() -> None:
    assert 4 * 10 == 40
    assert 6 * 10 == 60
    assert 2 * 100 == 200
    assert 8 * 1000 == 8000
    assert 7 * 1000 == 7000
    assert 3 * 10 + 6 == 36
    assert 4 * 100 + 2 * 10 + 7 == 427
    assert 6000 + 300 + 40 + 2 == 6342
    assert 70000 + 900 + 5 == 70905
    assert 300000 + 40000 + 600 + 8 == 340608
    assert 85 > 58
    assert 307 < 370
    assert 4109 > 4091
    assert 2405 < 2450 < 2540
    assert 20001 > 19999
    assert 305004 < 305040
    assert 46 < 50 and 46 - 40 > 50 - 46
    assert 72 - 70 < 80 - 72
    assert 349 - 300 < 400 - 349
    assert 650 - 600 == 700 - 650
    assert 48760 - 48000 > 49000 - 48760
    assert 305499 - 305000 < 306000 - 305499
    assert 300 + 5 == 305
    assert 5900 > 5090
    assert 70000 + 50 == 70050
