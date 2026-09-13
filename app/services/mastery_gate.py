from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MasteryGateDecision:
    eligible: bool
    reason: str


def evaluate_mastery_gate(
    *,
    mastery_score: Decimal,
    mastery_threshold: Decimal,
    independent_correct_count: int,
    strong_help_seen: bool,
    independent_successes_after_strong_help: int,
    minimum_independent_correct: int = 2,
) -> MasteryGateDecision:
    """Decide mastery-check eligibility using application-owned evidence only.

    Strong help creates a recovery requirement only when it actually occurred.
    This keeps the policy deterministic while allowing learners who never used
    strong help to qualify from independent evidence alone.
    """
    if mastery_score < mastery_threshold:
        return MasteryGateDecision(False, "MASTERY_SCORE_BELOW_THRESHOLD")
    if independent_correct_count < minimum_independent_correct:
        return MasteryGateDecision(False, "INSUFFICIENT_INDEPENDENT_EVIDENCE")
    if strong_help_seen and independent_successes_after_strong_help < 1:
        return MasteryGateDecision(False, "INDEPENDENT_EVIDENCE_REQUIRED_AFTER_STRONG_HELP")
    return MasteryGateDecision(True, "ELIGIBLE_FOR_MASTERY_CHECK")
