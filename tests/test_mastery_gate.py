from decimal import Decimal

from app.models import TutorState
from app.services.mastery_gate import evaluate_mastery_gate
from app.services.state_machine import TutorContext, determine_next_action


def test_assisted_or_low_independent_evidence_is_not_eligible() -> None:
    decision = evaluate_mastery_gate(
        mastery_score=Decimal("0.90"),
        mastery_threshold=Decimal("0.85"),
        independent_correct_count=1,
        strong_help_seen=True,
        independent_successes_after_strong_help=1,
    )
    assert decision.eligible is False
    assert decision.reason == "INSUFFICIENT_INDEPENDENT_EVIDENCE"


def test_strong_help_requires_new_independent_success() -> None:
    decision = evaluate_mastery_gate(
        mastery_score=Decimal("0.90"),
        mastery_threshold=Decimal("0.85"),
        independent_correct_count=3,
        strong_help_seen=True,
        independent_successes_after_strong_help=0,
    )
    assert decision.eligible is False
    assert decision.reason == "INDEPENDENT_EVIDENCE_REQUIRED_AFTER_STRONG_HELP"


def test_independent_evidence_after_strong_help_can_unlock_mastery_check() -> None:
    decision = evaluate_mastery_gate(
        mastery_score=Decimal("0.90"),
        mastery_threshold=Decimal("0.85"),
        independent_correct_count=3,
        strong_help_seen=True,
        independent_successes_after_strong_help=1,
    )
    assert decision.eligible is True
    assert decision.reason == "ELIGIBLE_FOR_MASTERY_CHECK"


def test_no_strong_help_does_not_create_recovery_requirement() -> None:
    decision = evaluate_mastery_gate(
        mastery_score=Decimal("0.90"),
        mastery_threshold=Decimal("0.85"),
        independent_correct_count=2,
        strong_help_seen=False,
        independent_successes_after_strong_help=0,
    )
    assert decision.eligible is True
    assert decision.reason == "ELIGIBLE_FOR_MASTERY_CHECK"


def test_score_threshold_is_required() -> None:
    decision = evaluate_mastery_gate(
        mastery_score=Decimal("0.84"),
        mastery_threshold=Decimal("0.85"),
        independent_correct_count=5,
        strong_help_seen=True,
        independent_successes_after_strong_help=2,
    )
    assert decision.eligible is False
    assert decision.reason == "MASTERY_SCORE_BELOW_THRESHOLD"


def test_independent_practice_does_not_enter_mastery_check_when_gate_denies() -> None:
    transition = determine_next_action(
        TutorContext(
            state=TutorState.INDEPENDENT_PRACTICE,
            correct=True,
            assistance_level=0,
            mastery_gate_eligible=False,
        )
    )
    assert transition.state == TutorState.INDEPENDENT_PRACTICE
    assert transition.action == "CONTINUE_INDEPENDENT_PRACTICE"


def test_independent_practice_enters_mastery_check_when_gate_allows() -> None:
    transition = determine_next_action(
        TutorContext(
            state=TutorState.INDEPENDENT_PRACTICE,
            correct=True,
            assistance_level=0,
            mastery_gate_eligible=True,
        )
    )
    assert transition.state == TutorState.MASTERY_CHECK
    assert transition.action == "START_MASTERY_CHECK"


def test_mastery_check_pass_and_fail_are_application_owned() -> None:
    passed = determine_next_action(
        TutorContext(
            state=TutorState.MASTERY_CHECK,
            correct=True,
            assistance_level=0,
        )
    )
    failed = determine_next_action(
        TutorContext(
            state=TutorState.MASTERY_CHECK,
            correct=False,
            assistance_level=0,
        )
    )
    assert passed.state == TutorState.COMPLETE
    assert passed.action == "MARK_MASTERED"
    assert failed.state == TutorState.REMEDIATION
    assert failed.action == "REMEDIATE"
