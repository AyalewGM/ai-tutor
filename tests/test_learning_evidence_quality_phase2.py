"""Regression tests for evidence-quality gates in learning effectiveness Phase 2.

No real learner data, LLM scoring, or database fixtures are required.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from app.effectiveness_models import AssessmentPhase, AssessmentStatus, LearningAssessment
from app.services.learning_effectiveness import (
    SkillEffectivenessReport,
    compute_effectiveness,
    parent_summary,
)


def _assessment(
    *,
    score: str | None = "0.600",
    independent: str | None = "0.600",
    difficulty: str | None = "2.00",
    items: int = 5,
    answered: int | None = 5,
    status: AssessmentStatus = AssessmentStatus.COMPLETED,
    phase: AssessmentPhase = AssessmentPhase.BASELINE,
) -> LearningAssessment:
    return LearningAssessment(
        id=uuid.uuid4(),
        student_id=uuid.uuid4(),
        skill_id=uuid.uuid4(),
        phase=phase,
        status=status,
        items_total=items,
        items_answered=answered,
        score=Decimal(score) if score is not None else None,
        independent_score=Decimal(independent) if independent is not None else None,
        difficulty_mean=Decimal(difficulty) if difficulty is not None else None,
        assessment_mode="INDEPENDENT",
        coverage_sufficient=True,
    )


def _measure(
    baseline: LearningAssessment | None,
    comparison: LearningAssessment,
    kind: str = "GROWTH",
):
    return compute_effectiveness(
        baseline=baseline,
        comparison=comparison,
        measurement_type=kind,
        student_id=uuid.uuid4(),
        skill_id=uuid.uuid4(),
    )


def test_valid_parallel_independent_evidence_can_be_high_confidence():
    metrics = _measure(_assessment(), _assessment())
    assert metrics.evidence_sufficient is True
    assert metrics.evidence_count == 10
    assert metrics.confidence_level == "HIGH"


def test_missing_growth_baseline_never_claims_high_confidence():
    metrics = _measure(None, _assessment())
    assert metrics.observed_improvement is None
    assert metrics.evidence_sufficient is False
    assert metrics.confidence_level == "INSUFFICIENT"


@pytest.mark.parametrize("status", [AssessmentStatus.CANCELLED, AssessmentStatus.IN_PROGRESS])
def test_invalid_status_cannot_be_rescued_by_stale_scores(status):
    metrics = _measure(_assessment(), _assessment(status=status))
    assert metrics.evidence_sufficient is False
    assert metrics.confidence_level == "INSUFFICIENT"


def test_compromised_assessment_cannot_be_rescued_by_stale_independent_score():
    comparison = _assessment()
    comparison.assessment_mode = "COMPROMISED"
    metrics = _measure(_assessment(), comparison)
    assert metrics.evidence_sufficient is False
    assert metrics.confidence_level == "INSUFFICIENT"


def test_unanswered_items_do_not_inflate_evidence_count():
    baseline = _assessment(items=20, answered=20)
    comparison = _assessment(items=20, answered=1)
    metrics = _measure(baseline, comparison)
    assert metrics.evidence_count == 21
    assert metrics.evidence_sufficient is False
    assert metrics.confidence_level == "INSUFFICIENT"


@pytest.mark.parametrize("difficulty", [None, "4.00"])
def test_unknown_or_noncomparable_difficulty_blocks_confidence(difficulty):
    metrics = _measure(_assessment(difficulty="2.00"), _assessment(difficulty=difficulty))
    assert metrics.difficulty_comparable is False
    assert metrics.evidence_sufficient is False
    assert metrics.confidence_level == "INSUFFICIENT"


def test_insufficient_family_coverage_blocks_confidence():
    comparison = _assessment()
    comparison.coverage_sufficient = False
    metrics = _measure(_assessment(), comparison)
    assert metrics.evidence_sufficient is False
    assert metrics.confidence_level == "INSUFFICIENT"


def test_missing_independent_score_blocks_confidence_but_preserves_observed_delta():
    comparison = _assessment(score="0.800", independent=None)
    metrics = _measure(_assessment(score="0.400", independent="0.400"), comparison)
    assert metrics.observed_improvement == Decimal("0.400")
    assert metrics.independent_improvement is None
    assert metrics.evidence_sufficient is False
    assert metrics.confidence_level == "INSUFFICIENT"


def test_valid_transfer_needs_no_source_baseline():
    metrics = _measure(None, _assessment(phase=AssessmentPhase.TRANSFER), "TRANSFER")
    assert metrics.evidence_sufficient is True
    assert metrics.transfer_performance == Decimal("0.600")
    assert metrics.confidence_level == "MODERATE"


def test_parent_does_not_label_insufficient_growth_as_no_improvement():
    growth = _measure(None, _assessment())
    report = SkillEffectivenessReport(
        student_id=uuid.uuid4(),
        skill_id=uuid.uuid4(),
        skill_code="TEST",
        skill_name="Test",
        has_post_instruction=True,
        growth=growth,
    )
    assert parent_summary(report).has_improved == "Not enough evidence"


def test_parent_does_not_report_unvalidated_retention_or_transfer():
    retention = _measure(_assessment(), _assessment(difficulty=None), "RETENTION")
    transfer = _measure(None, _assessment(difficulty=None), "TRANSFER")
    report = SkillEffectivenessReport(
        student_id=uuid.uuid4(),
        skill_id=uuid.uuid4(),
        skill_code="TEST",
        skill_name="Test",
        has_retention=True,
        has_transfer=True,
        retention_metrics=retention,
        transfer_metrics=transfer,
    )
    summary = parent_summary(report)
    assert summary.remembers_after_days == "Not enough evidence"
    assert summary.applies_to_new_problems == "Not enough evidence"


def test_guided_mastery_cannot_substitute_for_independent_assessment():
    report = SkillEffectivenessReport(
        student_id=uuid.uuid4(),
        skill_id=uuid.uuid4(),
        skill_code="TEST",
        skill_name="Test",
        current_mastery=Decimal("0.990"),
    )
    assert parent_summary(report).can_solve_independently == "Not assessed"
