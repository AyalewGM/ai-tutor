from app.models import SkillStatus
from app.services.parent_intelligence import (
    AssistanceSignal,
    EvidenceStatus,
    ParentLearningState,
    ParentSkillEvidence,
    classify_parent_skill_progress,
)


def _evidence(**overrides: object) -> ParentSkillEvidence:
    values: dict[str, object] = {
        "attempt_count": 0,
        "independent_attempt_count": 0,
        "independent_correct_count": 0,
        "hinted_correct_count": 0,
        "status": SkillStatus.NOT_STARTED,
    }
    values.update(overrides)
    return ParentSkillEvidence(**values)  # type: ignore[arg-type]


def test_no_observations_are_insufficient_evidence() -> None:
    insight = classify_parent_skill_progress(_evidence())

    assert insight.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert insight.learning_state == ParentLearningState.NOT_STARTED
    assert insight.reason_code == "COLLECT_MORE_EVIDENCE"


def test_single_failure_does_not_become_a_weakness_label() -> None:
    insight = classify_parent_skill_progress(
        _evidence(attempt_count=1, independent_attempt_count=1, status=SkillStatus.LEARNING)
    )

    assert insight.evidence_status == EvidenceStatus.EVIDENCE_AVAILABLE
    assert insight.learning_state == ParentLearningState.IN_PROGRESS
    assert insight.reason_code == "ACTIVITY_OBSERVED_NO_NEGATIVE_INFERENCE"


def test_assisted_success_stays_distinct_from_independent_progress() -> None:
    assisted = classify_parent_skill_progress(
        _evidence(attempt_count=2, hinted_correct_count=1, status=SkillStatus.PRACTICING)
    )
    independent = classify_parent_skill_progress(
        _evidence(
            attempt_count=2,
            independent_attempt_count=1,
            independent_correct_count=1,
            status=SkillStatus.PRACTICING,
        )
    )

    assert assisted.learning_state == ParentLearningState.ASSISTED_SUCCESS
    assert assisted.assistance_signal == AssistanceSignal.ASSISTANCE_OBSERVED
    assert independent.learning_state == ParentLearningState.INDEPENDENT_PROGRESS


def test_mastery_requires_existing_mastered_state_and_independent_success() -> None:
    insight = classify_parent_skill_progress(
        _evidence(
            attempt_count=4,
            independent_attempt_count=2,
            independent_correct_count=2,
            hinted_correct_count=1,
            status=SkillStatus.MASTERED,
        )
    )

    assert insight.learning_state == ParentLearningState.INDEPENDENT_MASTERY
    assert insight.assistance_signal == AssistanceSignal.MIXED_INDEPENDENT_AND_ASSISTED
    assert insight.reason_code == "INDEPENDENT_MASTERY_EVIDENCE"


def test_custom_policy_can_require_more_evidence_without_changing_mastery_semantics() -> None:
    class TwoIndependentAttemptsPolicy:
        def is_sufficient(self, evidence: ParentSkillEvidence) -> bool:
            return evidence.independent_attempt_count >= 2

    insight = classify_parent_skill_progress(
        _evidence(
            attempt_count=3,
            independent_attempt_count=1,
            independent_correct_count=1,
            status=SkillStatus.PRACTICING,
        ),
        policy=TwoIndependentAttemptsPolicy(),
    )

    assert insight.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert insight.reason_code == "COLLECT_MORE_EVIDENCE"
