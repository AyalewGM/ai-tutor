import math
from dataclasses import dataclass

DEFAULT_MASTERY_HALF_LIFE_DAYS = 21.0

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


def _difficulty_scaled_alpha(
    alpha: float,
    problem_difficulty: int,
    learner_level: int,
    correct: bool,
) -> float:
    """Scale the learning rate by difficulty surprise.

    Correct answers above level are stronger positive evidence; wrong answers
    below level are stronger negative evidence. The gap flips sign on failure
    so that missing an easy problem is more diagnostic than missing a hard one.
    """
    gap = max(-3, min(3, problem_difficulty - learner_level))
    if not correct:
        gap = -gap
    return max(0.05, min(0.60, alpha * (1 + 0.15 * gap)))


def update_mastery(
    current_mastery: float,
    meaningful_attempts: int,
    correct: bool,
    assistance_level: int,
    alpha: float = 0.25,
    *,
    problem_difficulty: int | None = None,
    learner_level: int | None = None,
) -> MasteryUpdate:
    evidence = attempt_evidence(correct, assistance_level)
    if problem_difficulty is not None and learner_level is not None:
        alpha = _difficulty_scaled_alpha(
            alpha, problem_difficulty, learner_level, correct
        )
    mastery = ((1 - alpha) * current_mastery) + (alpha * evidence)
    confidence = 1 - math.exp(-(meaningful_attempts + 1) / 5)
    return MasteryUpdate(
        mastery=round(max(0.0, min(1.0, mastery)), 3),
        confidence=round(max(0.0, min(1.0, confidence)), 3),
        evidence=evidence,
    )


def decayed_mastery(
    mastery: float,
    *,
    days_since_evidence: float,
    confidence: float = 0.0,
    half_life_days: float = DEFAULT_MASTERY_HALF_LIFE_DAYS,
) -> float:
    """Exponential forgetting decay; higher confidence slows the half-life."""
    bounded = max(0.0, min(1.0, mastery))
    if days_since_evidence <= 0:
        return round(bounded, 3)
    confidence_factor = 0.5 + 0.5 * max(0.0, min(1.0, confidence))
    effective_half_life = half_life_days * confidence_factor
    decayed = bounded * math.pow(0.5, days_since_evidence / effective_half_life)
    return round(max(0.0, min(1.0, decayed)), 3)
