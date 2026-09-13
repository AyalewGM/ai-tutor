from app.models import TutorState
from app.services.hint_policy import assistance_level_for_hint, hint_constraint, select_hint


def test_first_explicit_help_is_level_one():
    decision = select_hint(state=TutorState.GUIDED_PRACTICE, explicit_request=True)
    assert decision.allowed is True
    assert decision.level == 1


def test_explicit_help_escalates_one_level_only():
    for used in range(4):
        decision = select_hint(
            state=TutorState.GUIDED_PRACTICE,
            highest_level_used=used,
            explicit_request=True,
        )
        assert decision.level == used + 1


def test_level_four_is_ceiling():
    decision = select_hint(
        state=TutorState.REMEDIATION,
        highest_level_used=4,
        explicit_request=True,
    )
    assert decision.level == 4


def test_assessment_states_reject_help():
    for state in (TutorState.DIAGNOSE, TutorState.MASTERY_CHECK):
        decision = select_hint(state=state, explicit_request=True)
        assert decision.allowed is False
        assert decision.level == 0


def test_confident_misconception_starts_with_minimal_jit_cue():
    decision = select_hint(
        state=TutorState.GUIDED_PRACTICE,
        misconception_confidence=0.91,
    )
    assert decision.allowed is True
    assert decision.level == 1
    assert decision.trigger == "MISCONCEPTION_JIT"


def test_repeated_struggle_escalates_gradually():
    decision = select_hint(
        state=TutorState.GUIDED_PRACTICE,
        highest_level_used=2,
        repeated_unsuccessful_attempts=3,
    )
    assert decision.level == 3


def test_high_hints_are_strong_assistance():
    assert assistance_level_for_hint(0) == 0
    assert assistance_level_for_hint(1) == 1
    assert assistance_level_for_hint(2) == 1
    assert assistance_level_for_hint(3) == 2
    assert assistance_level_for_hint(4) == 2


def test_hint_constraints_preserve_productive_struggle():
    assert "Do not" in hint_constraint(1)
    assert "Do not solve" in hint_constraint(2)
    assert "meaningful" in hint_constraint(3)
    assert "near-transfer" in hint_constraint(4)
