from app.services.mastery import decayed_mastery
from app.services.review_schedule import REVIEW_INTERVALS_DAYS


def test_decayed_mastery_no_elapsed_time() -> None:
    assert decayed_mastery(0.9, days_since_evidence=0, confidence=0.9) == 0.9


def test_decayed_mastery_halves_at_effective_half_life() -> None:
    # confidence 1.0 -> effective half-life = 21 days
    assert decayed_mastery(0.9, days_since_evidence=21, confidence=1.0) == 0.45


def test_decayed_mastery_decays_faster_with_low_confidence() -> None:
    # confidence 0.0 -> effective half-life = 10.5 days -> two half-lives in 21 days
    assert decayed_mastery(0.9, days_since_evidence=21, confidence=0.0) == 0.225


def test_decayed_mastery_monotonic_in_time() -> None:
    recent = decayed_mastery(0.9, days_since_evidence=5, confidence=0.5)
    distant = decayed_mastery(0.9, days_since_evidence=30, confidence=0.5)
    assert recent > distant


def test_review_intervals_are_increasing() -> None:
    assert REVIEW_INTERVALS_DAYS == tuple(sorted(REVIEW_INTERVALS_DAYS))
    assert REVIEW_INTERVALS_DAYS[0] >= 1
