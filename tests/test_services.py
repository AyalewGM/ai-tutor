from app.models import TutorState
from app.services.evaluation import evaluate_distributive_property
from app.services.mastery import attempt_evidence, update_mastery
from app.services.state_machine import TutorContext, determine_next_action


def test_detects_partial_distribution_misconception() -> None:
    result = evaluate_distributive_property("3(x+4)", "3x+4", "3x+12")
    assert result.correct is False
    assert result.misconception_code == "DIST_001"
    assert result.misconception_confidence == 0.97


def test_correct_distribution_is_accepted() -> None:
    result = evaluate_distributive_property("3(x+4)", "3x + 12", "3x+12")
    assert result.correct is True
    assert result.misconception_code is None


def test_assistance_reduces_learning_evidence() -> None:
    assert attempt_evidence(True, 0) == 1.0
    assert attempt_evidence(True, 2) == 0.65
    assert attempt_evidence(True, 4) == 0.20
    assert attempt_evidence(False, 0) == 0.0


def test_mastery_uses_recent_evidence() -> None:
    update = update_mastery(0.60, meaningful_attempts=4, correct=True, assistance_level=0)
    assert update.mastery == 0.70
    assert 0 < update.confidence < 1


def test_guided_practice_gives_hint_after_wrong_answer() -> None:
    transition = determine_next_action(
        TutorContext(
            state=TutorState.GUIDED_PRACTICE,
            correct=False,
            assistance_level=0,
            misconception_count=1,
        )
    )
    assert transition.state == TutorState.GUIDED_PRACTICE
    assert transition.action == "GIVE_HINT"
    assert transition.hint_level == 1


def test_repeated_misconception_triggers_remediation() -> None:
    transition = determine_next_action(
        TutorContext(
            state=TutorState.GUIDED_PRACTICE,
            correct=False,
            misconception_count=2,
        )
    )
    assert transition.state == TutorState.REMEDIATION
    assert transition.action == "REMEDIATE"
