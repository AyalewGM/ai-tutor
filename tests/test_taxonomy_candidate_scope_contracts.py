"""Draft taxonomy scope-card invariants."""
import json
from pathlib import Path

from app.canonical_skill_taxonomy import SkillReviewState
from app.canonical_taxonomy_candidates import CANDIDATE_TAXONOMY


def test_candidate_scope_cards():
    root = Path(__file__).resolve().parents[1]
    path = root / "docs/curriculum/taxonomy_candidate_scope.v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["authority"] == "NONE_NOT_FOR_RUNTIME"
    cards = data["skills"]
    assert len(cards) == 6
    assert {card["code"] for card in cards} == set(CANDIDATE_TAXONOMY.skills)
    required = (
        "components",
        "inclusions",
        "exclusions",
        "examples",
        "assessment_criteria",
        "misconception_probes",
        "possible_overlaps",
    )
    for card in cards:
        assert card["identity_decision"].startswith("PENDING_")
        definition = CANDIDATE_TAXONOMY.skills[card["code"]]
        assert definition.review_state == SkillReviewState.DRAFT
        assert all(card[field] for field in required)
        assert not CANDIDATE_TAXONOMY.contains(card["code"])


def test_rejected_composites_are_reporting_profiles_only():
    root = Path(__file__).resolve().parents[1]
    data = json.loads(
        (root / "docs/curriculum/taxonomy_candidate_scope.v1.json").read_text(
            encoding="utf-8"
        )
    )
    candidate_codes = set(CANDIDATE_TAXONOMY.skills)
    assert "MATH.ARITHMETIC.ADD_SUB_WITHIN_20" not in candidate_codes
    assert "MATH.NUMBER_SENSE.COUNT_COMPARE_TO_120" not in candidate_codes
    profiles = {profile["label"]: profile for profile in data["noncanonical_profiles"]}
    assert profiles["add_and_subtract_within_20"]["members"] == [
        "MATH.ARITHMETIC.ADD_WITHIN_20",
        "MATH.ARITHMETIC.SUBTRACT_WITHIN_20",
    ]
    assert profiles["count_and_compare_to_120"]["members"] == [
        "MATH.NUMBER_SENSE.COUNT_FORWARD_BY_ONE_TO_120",
        "MATH.NUMBER_SENSE.COMPARE_WHOLE_NUMBERS_TO_120",
    ]
    for profile in profiles.values():
        assert profile["role"] == "REPORTING_ONLY_ALL_OF"
        assert "No canonical row or UUID" in profile["prohibitions"]
        assert "No mastery event" in profile["prohibitions"]
        assert "No duplicate credit" in profile["prohibitions"]
