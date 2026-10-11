"""Draft-only exact-answer and review-gate checks for Grade 9 algebra depth."""
import json
from fractions import Fraction
from pathlib import Path

PATH = Path("docs/curriculum/drafts/draft-g9-linear-models-pilot-v0/algebra_reasoning_depth.draft.json")


def test_grade9_algebra_depth_oracles_and_review_gates() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["review_status"] == "PENDING"
    assert data["runtime_activation"] is False
    assert data["mastery_updater"] is False
    assert data["canonical_skill_ids"] == []
    assert data["curriculum_mappings"] == []
    items = data["items"]
    assert len(items) == 20
    assert len({item["item_id"] for item in items}) == 20
    oracles = [
        Fraction(12), Fraction(23), Fraction(0), "infinitely many",
        Fraction(-4), Fraction(4), Fraction(2), Fraction(-3),
        Fraction(-1), Fraction(47), "no", "no", Fraction(7),
        Fraction(0), Fraction(-13), Fraction(9), Fraction(83),
        "no", Fraction(8), Fraction(2),
    ]
    for item, oracle in zip(items, oracles, strict=True):
        if isinstance(oracle, Fraction):
            assert Fraction(item["expected"]) == oracle, item["item_id"]
            assert Fraction(item["misconception"]["plausible_wrong_answer"]) != oracle
        else:
            assert item["expected"] == oracle
            assert item["misconception"]["plausible_wrong_answer"] != oracle
        assert item["review_status"] == "PENDING"
        assert item["runtime_activation"] is False
        assert item["reasoning_review"] == "HUMAN_REQUIRED"
        assert len(item["socratic_hints"]) == 3
        assert item["transfer_prompt"]
        assert item["worked_reasoning"]
