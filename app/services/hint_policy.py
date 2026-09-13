from dataclasses import dataclass

from app.models import TutorState

ASSESSMENT_STATES = {TutorState.DIAGNOSE, TutorState.MASTERY_CHECK}


@dataclass(frozen=True)
class HintDecision:
    allowed: bool
    level: int = 0
    trigger: str = "NONE"
    reason: str | None = None


def select_hint(
    *,
    state: TutorState,
    highest_level_used: int = 0,
    explicit_request: bool = False,
    misconception_confidence: float | None = None,
    repeated_unsuccessful_attempts: int = 0,
) -> HintDecision:
    """Choose support level deterministically; generation never owns pedagogy."""
    if state in ASSESSMENT_STATES:
        return HintDecision(False, reason="Hints are disabled during assessment.")

    used = max(0, min(4, highest_level_used))

    if explicit_request:
        return HintDecision(True, min(4, used + 1), "EXPLICIT_REQUEST")

    if misconception_confidence is not None and misconception_confidence >= 0.75:
        # A confident misconception can justify a focused conceptual cue, but
        # never skip more than one rung beyond support already provided.
        target = 2 if used >= 1 else 1
        return HintDecision(True, min(target, used + 1), "MISCONCEPTION_JIT")

    if repeated_unsuccessful_attempts >= 2:
        return HintDecision(True, min(4, used + 1), "REPEATED_STRUGGLE")

    return HintDecision(False)


def assistance_level_for_hint(hint_level: int) -> int:
    """Map hint exposure to existing mastery-evidence assistance weights."""
    if hint_level <= 0:
        return 0
    if hint_level <= 2:
        return 1
    return 2


def hint_constraint(level: int) -> str:
    constraints = {
        1: "Give only a directional cue. Do not name or perform the complete next step.",
        2: "State the governing concept and ask one focused question. Do not solve the step.",
        3: "Provide a partial scaffold or template, leaving meaningful algebra for the learner.",
        4: "Model only the blocked step, then require the learner to continue or solve a near-transfer item.",
    }
    return constraints.get(level, "Do not provide a hint.")
