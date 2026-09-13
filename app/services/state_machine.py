from dataclasses import dataclass

from app.models import TutorState


@dataclass(frozen=True)
class TutorContext:
    state: TutorState
    correct: bool
    assistance_level: int = 0
    misconception_count: int = 0
    consecutive_independent_successes: int = 0
    mastery_gate_eligible: bool = False


@dataclass(frozen=True)
class Transition:
    state: TutorState
    action: str
    hint_level: int | None = None


def determine_next_action(context: TutorContext) -> Transition:
    if context.state == TutorState.DIAGNOSE:
        if context.correct:
            return Transition(TutorState.GUIDED_PRACTICE, "ASK_GUIDING_QUESTION")
        return Transition(TutorState.INTRODUCE, "EXPLAIN_CONCEPT")

    if context.state in {TutorState.INTRODUCE, TutorState.MODEL}:
        return Transition(TutorState.GUIDED_PRACTICE, "ASK_GUIDING_QUESTION")

    if context.state == TutorState.GUIDED_PRACTICE:
        if context.correct and context.assistance_level == 0:
            if context.consecutive_independent_successes >= 2:
                return Transition(TutorState.INDEPENDENT_PRACTICE, "INCREASE_DIFFICULTY")
            return Transition(TutorState.GUIDED_PRACTICE, "ASK_GUIDING_QUESTION")
        if context.misconception_count >= 2:
            return Transition(TutorState.REMEDIATION, "REMEDIATE", hint_level=3)
        hint_level = min(max(context.assistance_level + 1, 1), 4)
        return Transition(TutorState.GUIDED_PRACTICE, "GIVE_HINT", hint_level=hint_level)

    if context.state == TutorState.INDEPENDENT_PRACTICE:
        if context.correct and context.assistance_level == 0:
            if context.mastery_gate_eligible:
                return Transition(TutorState.MASTERY_CHECK, "START_MASTERY_CHECK")
            return Transition(TutorState.INDEPENDENT_PRACTICE, "CONTINUE_INDEPENDENT_PRACTICE")
        return Transition(TutorState.GUIDED_PRACTICE, "GIVE_HINT", hint_level=1)

    if context.state == TutorState.MASTERY_CHECK:
        if context.correct and context.assistance_level == 0:
            return Transition(TutorState.COMPLETE, "MARK_MASTERED")
        return Transition(TutorState.REMEDIATION, "REMEDIATE", hint_level=2)

    if context.state in {TutorState.REMEDIATION, TutorState.REVIEW}:
        return Transition(TutorState.GUIDED_PRACTICE, "ASK_RETRY")

    return Transition(TutorState.COMPLETE, "MARK_MASTERED")
