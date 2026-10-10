"""Draft Grade 4–5 fraction-depth content contracts (no runtime activation)."""
import json
from fractions import Fraction
from pathlib import Path

PACKAGE = Path("docs/curriculum/drafts/draft-g45-fractions-pilot-v0/fraction_depth_wave.draft.json")


def test_fraction_depth_inventory_and_review_gates() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert package["status"] == "DRAFT_UNVERIFIED"
    assert package["review_status"] == "PENDING"
    assert package["runtime_activation"] is False
    assert package["canonical_skill_ids"] == []
    assert package["curriculum_mappings"] == []
    assert len(package["items"]) == 8
    assert len({item["id"] for item in package["items"]}) == 8
    assert len({item["provisional_topic"] for item in package["items"]}) == 8
    for item in package["items"]:
        assert item["review_status"] == "PENDING"
        assert item["mastery_write_allowed"] is False
        assert item["worked_example"]["model"]
        assert len(item["socratic_hints"]) == 3
        assert item["remediation"]["follow_up"]
        assert item["transfer_assessment"]["review_mode"] == "human_mathematical_reasoning_review"
        assert Fraction(item["diagnostic"]["expected"]) != Fraction(
            item["misconception"]["plausible_wrong_answer"]
        )


def test_independent_exact_diagnostic_answers() -> None:
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    expected = {
        "fraction-unit-whole": Fraction(3, 6),
        "fraction-number-line": Fraction(5, 8),
        "fraction-equivalence": Fraction(3 * 3, 4 * 3),
        "fraction-same-denominator-add": Fraction(3 + 4, 8),
        "fraction-same-denominator-subtract": Fraction(8 - 5, 9),
        "fraction-compare-unlike": Fraction(2, 3),
        "fraction-of-set": Fraction(28 * 3, 7),
        "fraction-unknown-whole": Fraction(18 * 4, 3),
    }
    for item in package["items"]:
        assert Fraction(item["diagnostic"]["expected"]) == expected[item["provisional_topic"]]
