"""Exact-answer and review boundary checks for draft Grades 1–5 foundations."""
import json
from pathlib import Path

PATH = Path("docs/curriculum/drafts/draft-g15-place-value-pilot-v0/foundations_reasoning_wave.draft.json")


def test_foundations_reasoning_wave() -> None:
    package = json.loads(PATH.read_text(encoding="utf-8"))
    assert package["status"] == "DRAFT_UNVERIFIED"
    assert package["review_status"] == "PENDING"
    assert package["runtime_activation"] is False
    assert package["mastery_updater"] is False
    assert package["canonical_skill_ids"] == []
    assert package["curriculum_mappings"] == []
    items = package["items"]
    assert len(items) == 24
    assert len({item["item_id"] for item in items}) == 24
    expected = [
        47, 80, 349, 134, 470, 290, 27, 375, 227, 25, 42, 36,
        4, 8, 4, 41, 27, 9, 3, 5, 21, 13, 14, 26,
    ]
    for item, oracle in zip(items, expected, strict=True):
        assert int(item["expected"]) == oracle, item["item_id"]
        assert int(item["misconception"]["plausible_wrong_answer"]) != oracle
        assert item["review_status"] == "PENDING"
        assert item["runtime_activation"] is False
        assert item["reasoning_review"] == "HUMAN_REQUIRED"
        assert len(item["socratic_hints"]) == 3
        assert item["transfer_prompt"]
        assert item["worked_reasoning"]
