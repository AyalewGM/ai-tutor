"""Draft taxonomy scope-card invariants."""
import json
from pathlib import Path

from app.canonical_skill_taxonomy import SkillReviewState
from app.canonical_taxonomy_candidates import CANDIDATE_TAXONOMY


def test_candidate_scope_cards():
    path = Path(__file__).resolve().parents[1] / "docs/curriculum/taxonomy_candidate_scope.v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["authority"] == "NONE_NOT_FOR_RUNTIME"
    cards = data["skills"]
    assert len(cards) == 4
    assert {c["code"] for c in cards} == set(CANDIDATE_TAXONOMY.skills)
    for card in cards:
        assert card["identity_decision"].startswith("PENDING_")
        assert CANDIDATE_TAXONOMY.skills[card["code"]].review_state == SkillReviewState.DRAFT
        for field in ("components", "inclusions", "exclusions", "examples", "assessment_criteria", "misconception_probes", "possible_overlaps"):
            assert card[field]
        assert not CANDIDATE_TAXONOMY.contains(card["code"])
