import math
from dataclasses import dataclass

ASSISTANCE_WEIGHTS = {
    0: 1.00,
    1: 0.85,
    2: 0.65,
    3: 0.40,
    4: 0.20,
}


@dataclass(frozen=True)
class MasteryUpdate:
    mastery: float
    confidence: float
    evidence: float


def attempt_evidence(correct: bool, assistance_level: int) -> float:
    if not correct:
        return 0.0
    return ASSISTANCE_WEIGHTS[assistance_level]


def update_mastery(
    current_mastery: float,
    meaningful_attempts: int,
    correct: bool,
    assistance_level: int,
    alpha: float = 0.25,
) -> MasteryUpdate:
    evidence = attempt_evidence(correct, assistance_level)
    mastery = ((1 - alpha) * current_mastery) + (alpha * evidence)
    confidence = 1 - math.exp(-(meaningful_attempts + 1) / 5)
    return MasteryUpdate(
        mastery=round(max(0.0, min(1.0, mastery)), 3),
        confidence=round(max(0.0, min(1.0, confidence)), 3),
        evidence=evidence,
    )
