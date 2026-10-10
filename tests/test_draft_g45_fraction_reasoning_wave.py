"""Independent exact answers and safety gates for fractions reasoning wave."""
import json
from fractions import Fraction
from pathlib import Path

PATH = Path("docs/curriculum/drafts/draft-g45-fractions-pilot-v0/reasoning_transfer_wave.draft.json")


def test_reasoning_wave_exact_answers_and_review_boundaries() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["review_status"] == "PENDING"
    assert data["runtime_activation"] is False
    assert data["canonical_skill_ids"] == []
    assert data["curriculum_mappings"] == []
    assert len(data["items"]) == 16
    assert len({item["item_id"] for item in data["items"]}) == 16
    expected = [
        Fraction(5, 8), Fraction(12), Fraction(20), Fraction(15),
        Fraction(18), Fraction(7, 8), Fraction(3, 2), Fraction(3, 4),
        Fraction(3, 5), Fraction(4, 6), Fraction(5), Fraction(2, 5),
        Fraction(3, 2), Fraction(8), Fraction(3), Fraction(3, 5),
    ]
    for item, answer in zip(data["items"], expected, strict=True):
        assert Fraction(item["expected"]) == answer, item["item_id"]
        assert Fraction(item["misconception"]["plausible_wrong_answer"]) != answer
        assert item["reasoning_review"] == "HUMAN_REQUIRED"
        assert item["runtime_activation"] is False
        assert item["reasoning_prompt"] and item["transfer_prompt"]
        assert item["explanation"] and item["misconception"]["feedback"]
