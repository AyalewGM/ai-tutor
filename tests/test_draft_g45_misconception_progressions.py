"""Exact oracles and draft-only contracts for fraction misconception progressions."""
import json
from fractions import Fraction
from pathlib import Path

PATH = Path("docs/curriculum/drafts/draft-g45-fractions-pilot-v0/misconception_progressions.draft.json")


def test_fraction_misconception_progressions() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["review_status"] == "PENDING"
    assert data["runtime_activation"] is False
    assert data["canonical_skill_ids"] == []
    assert data["curriculum_mappings"] == []
    assert len(data["pathways"]) == 6
    assert len({p["id"] for p in data["pathways"]}) == 6
    expected = [
        ["3/8", "1/3", "3/4", "2/5", "13/20"],
        ["3/5", "1/4", "2/3", "5/8", "3/2"],
        ["8", "4", "12", "12", "2"],
        ["5/7", "1/2", "2/3", "3/2", "3/2"],
        ["3/4", "1/3", "2/5", "3/4", "4/5"],
        ["12", "4", "18", "24", "30"],
    ]
    for pathway, answers in zip(data["pathways"], expected, strict=True):
        assert pathway["review_status"] == "PENDING"
        assert pathway["mastery_write_allowed"] is False
        assert pathway["visual_model_handoff_spec"]
        assert len(pathway["progression"]) == 4
        assert [s["phase"] for s in pathway["progression"]] == [
            "concrete", "guided", "independent", "transfer"
        ]
        assert set(pathway["adaptive_routes"]) == {
            "diagnostic_incorrect", "guided_incorrect",
            "independent_correct_no_reason", "transfer_incorrect"
        }
        stages = [pathway["diagnostic"], *pathway["progression"]]
        for stage, answer in zip(stages, answers, strict=True):
            assert Fraction(stage["expected"]) == Fraction(answer)
            assert Fraction(stage["misconception_answer"]) != Fraction(answer)
            assert stage["question"]
