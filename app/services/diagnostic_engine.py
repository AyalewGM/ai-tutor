import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class SkillEstimate:
    skill_id: uuid.UUID
    mastery: float
    confidence: float
    evidence_count: int
    prerequisite_importance: float = 0.5
    target_proximity: float = 0.5

    @property
    def uncertainty(self) -> float:
        return max(0.0, 1.0 - self.confidence)


@dataclass(frozen=True)
class DiagnosticDecision:
    next_skill_id: uuid.UUID | None
    should_stop: bool
    placement_skill_id: uuid.UUID | None = None
    placement_confidence: float = 0.0


def evidence_weight(correct: bool, assistance_level: int) -> float:
    assistance_factor = {0: 1.0, 1: 0.85, 2: 0.65, 3: 0.4, 4: 0.2}[assistance_level]
    return assistance_factor if correct else 0.0


def update_estimate(
    mastery: float,
    confidence: float,
    evidence_count: int,
    *,
    correct: bool,
    assistance_level: int,
) -> tuple[float, float]:
    evidence = evidence_weight(correct, assistance_level)
    alpha = 0.30 if evidence_count < 3 else 0.20
    new_mastery = (1 - alpha) * mastery + alpha * evidence
    new_confidence = min(0.95, confidence + (0.22 if assistance_level == 0 else 0.12))
    return round(new_mastery, 3), round(new_confidence, 3)


def priority(estimate: SkillEstimate) -> float:
    return (
        0.50 * estimate.uncertainty
        + 0.30 * estimate.prerequisite_importance
        + 0.20 * estimate.target_proximity
    )


def select_next_skill(estimates: list[SkillEstimate]) -> uuid.UUID | None:
    if not estimates:
        return None
    ordered = sorted(estimates, key=lambda item: (-priority(item), str(item.skill_id)))
    return ordered[0].skill_id


def decide_placement(
    estimates: list[SkillEstimate],
    *,
    min_confidence: float = 0.70,
    readiness_threshold: float = 0.75,
) -> DiagnosticDecision:
    if not estimates:
        return DiagnosticDecision(next_skill_id=None, should_stop=True)

    unresolved = [item for item in estimates if item.confidence < min_confidence]
    if unresolved:
        return DiagnosticDecision(next_skill_id=select_next_skill(unresolved), should_stop=False)

    ordered = sorted(estimates, key=lambda item: (item.target_proximity, str(item.skill_id)))
    weak = [item for item in ordered if item.mastery < readiness_threshold]
    placement = weak[0] if weak else ordered[-1]
    confidence = min(item.confidence for item in estimates)
    return DiagnosticDecision(
        next_skill_id=None,
        should_stop=True,
        placement_skill_id=placement.skill_id,
        placement_confidence=round(confidence, 3),
    )
