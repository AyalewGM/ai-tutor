"""Independent answer contracts for draft Grades 6–8 ratios depth wave."""
import json
from fractions import Fraction
from pathlib import Path

PATH = Path("docs/curriculum/drafts/draft-g68-ratios-pilot-v0/depth_reasoning_wave.draft.json")


def test_ratios_depth_wave() -> None:
    package = json.loads(PATH.read_text(encoding="utf-8"))
    assert package["status"] == "DRAFT_UNVERIFIED"
    assert package["review_status"] == "PENDING"
    assert package["runtime_activation"] is False
    assert package["mastery_updater"] is False
    assert package["canonical_skill_ids"] == []
    assert package["curriculum_mappings"] == []
    items = package["items"]
    assert len(items) == 16
    assert len({item["item_id"] for item in items}) == 16
    oracles = [
        Fraction(12, 30), Fraction(8), Fraction(84, 4), "B",
        "no", Fraction(80) * Fraction(75, 100),
        Fraction(240) * Fraction(115, 100), Fraction(18) / Fraction(60, 100),
        Fraction(5 * 7), Fraction(7, 2), Fraction(28 * 2, 7),
        Fraction(5 * 3), Fraction(900 * 5, 3 * 1000),
        Fraction(100 * 80 * 110, 100 * 100), Fraction(48, 6),
        Fraction(28 * 11, 7),
    ]
    for item, answer in zip(items, oracles, strict=True):
        actual = item["expected"]
        if isinstance(answer, Fraction):
            assert Fraction(actual) == answer, item["item_id"]
            assert Fraction(item["misconception"]["plausible_wrong_answer"]) != answer
        else:
            assert actual == answer
            assert item["misconception"]["plausible_wrong_answer"] != answer
        assert item["reasoning_review"] == "HUMAN_REQUIRED"
        assert item["runtime_activation"] is False
        assert len(item["socratic_hints"]) == 3
        assert item["transfer_prompt"]
        assert item["worked_reasoning"]
