"""Draft cross-domain gap-probe exact answer and review-gate checks."""
import json
from fractions import Fraction
from pathlib import Path

PATH = Path("docs/curriculum/drafts/draft-standards-gap-probes-v0/content.draft.json")


def test_cross_domain_probes() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["review_status"] == "PENDING"
    assert data["runtime_activation"] is False
    assert data["mastery_updater"] is False
    assert data["canonical_skill_ids"] == []
    assert data["curriculum_mappings"] == []
    items = data["items"]
    assert len(items) == 16
    assert len({item["item_id"] for item in items}) == 16
    oracles = [
        "no", Fraction(45 - 42), Fraction(4 + 5 + 6 + 5 + 30, 5),
        Fraction(1, 2) ** 2, Fraction(3, 5) * Fraction(2, 4),
        Fraction(18, 60), Fraction(180 - 47 - 68), Fraction(112),
        Fraction(8 * 5), Fraction(3 * 4 * 5), Fraction(75 - 28 - 19),
        "B", Fraction(200 * 5, 100), Fraction(2 + 4 * 3),
        Fraction(8 * 6 - 3), Fraction(4),
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
        assert item["worked_reasoning"]
        assert item["transfer_prompt"]
        assert len(item["socratic_hints"]) == 3
