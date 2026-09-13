from decimal import Decimal

from app.services.mastery_gate import evaluate_mastery_gate


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
