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
    assert len(cards) == 4
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
