import uuid

from app.services.diagnostic_engine import (
    SkillEstimate,
    decide_placement,
    evidence_weight,
    select_next_skill,
    update_estimate,
)


def make_estimate(
    mastery: float,
    confidence: float,
    *,
    prerequisite_importance: float = 0.5,
    target_proximity: float = 0.5,
) -> SkillEstimate:
    return SkillEstimate(
        skill_id=uuid.uuid4(),
        mastery=mastery,
        confidence=confidence,
        evidence_count=2,
        prerequisite_importance=prerequisite_importance,
        target_proximity=target_proximity,
    )


def test_independent_correct_has_full_evidence_weight() -> None:
    assert evidence_weight(True, 0) == 1.0
    assert evidence_weight(True, 3) == 0.4
    assert evidence_weight(False, 0) == 0.0


def test_assisted_success_increases_mastery_less_than_independent_success() -> None:
    independent = update_estimate(0.5, 0.2, 1, correct=True, assistance_level=0)
    assisted = update_estimate(0.5, 0.2, 1, correct=True, assistance_level=3)
    assert independent[0] > assisted[0]
    assert independent[1] > assisted[1]


def test_lower_confidence_relevant_skill_gets_priority() -> None:
    certain = make_estimate(0.6, 0.85, prerequisite_importance=0.8, target_proximity=0.8)
    uncertain = make_estimate(0.6, 0.2, prerequisite_importance=0.8, target_proximity=0.8)
    assert select_next_skill([certain, uncertain]) == uncertain.skill_id


def test_diagnostic_stays_open_while_any_relevant_skill_is_uncertain() -> None:
    estimates = [make_estimate(0.8, 0.8), make_estimate(0.7, 0.4)]
    decision = decide_placement(estimates)
    assert decision.should_stop is False
    assert decision.next_skill_id == estimates[1].skill_id


def test_diagnostic_places_at_first_weak_skill_when_confident() -> None:
    ready = make_estimate(0.85, 0.8, target_proximity=0.2)
    weak = make_estimate(0.6, 0.82, target_proximity=0.6)
    target = make_estimate(0.5, 0.9, target_proximity=1.0)
    decision = decide_placement([target, weak, ready])
    assert decision.should_stop is True
    assert decision.placement_skill_id == weak.skill_id
    assert decision.placement_confidence == 0.8
