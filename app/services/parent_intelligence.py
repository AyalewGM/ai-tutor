from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.models import SkillStatus


class EvidenceStatus(StrEnum):
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    EVIDENCE_AVAILABLE = "EVIDENCE_AVAILABLE"


class ParentLearningState(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    ASSISTED_SUCCESS = "ASSISTED_SUCCESS"
    INDEPENDENT_PROGRESS = "INDEPENDENT_PROGRESS"
    INDEPENDENT_MASTERY = "INDEPENDENT_MASTERY"
    NEEDS_PRACTICE = "NEEDS_PRACTICE"


class AssistanceSignal(StrEnum):
    NONE_OBSERVED = "NONE_OBSERVED"
    ASSISTANCE_OBSERVED = "ASSISTANCE_OBSERVED"
    MIXED_INDEPENDENT_AND_ASSISTED = "MIXED_INDEPENDENT_AND_ASSISTED"


class ParentActionCode(StrEnum):
    COLLECT_MORE_EVIDENCE = "COLLECT_MORE_EVIDENCE"
    CONTINUE_CURRENT_LEARNING = "CONTINUE_CURRENT_LEARNING"
    ENCOURAGE_INDEPENDENT_ATTEMPT = "ENCOURAGE_INDEPENDENT_ATTEMPT"
    RECOGNIZE_INDEPENDENT_PROGRESS = "RECOGNIZE_INDEPENDENT_PROGRESS"
    RECOGNIZE_MASTERY = "RECOGNIZE_MASTERY"
    FOLLOW_EXISTING_REVIEW_PLAN = "FOLLOW_EXISTING_REVIEW_PLAN"


@dataclass(frozen=True)
class ParentSkillEvidence:
    attempt_count: int
    independent_attempt_count: int
    independent_correct_count: int
    hinted_correct_count: int
    status: SkillStatus


@dataclass(frozen=True)
class ParentSkillInsight:
    evidence_status: EvidenceStatus
    learning_state: ParentLearningState
    assistance_signal: AssistanceSignal
    reason_code: str
    action_code: ParentActionCode


class EvidenceSufficiencyPolicy(Protocol):
    """F-010-owned seam for deciding whether evidence supports a conclusion."""

    def is_sufficient(self, evidence: ParentSkillEvidence) -> bool: ...


class ObservationOnlyEvidencePolicy:
    """Safe F-009 default until F-010 supplies the shared threshold policy.

    This policy only distinguishes no evidence from observed evidence. It must not
    be used to infer weakness, trigger remediation, or alter mastery.
    """

    def is_sufficient(self, evidence: ParentSkillEvidence) -> bool:
        return evidence.attempt_count > 0


def _assistance_signal(evidence: ParentSkillEvidence) -> AssistanceSignal:
    if evidence.hinted_correct_count <= 0:
        return AssistanceSignal.NONE_OBSERVED
    if evidence.independent_correct_count > 0:
        return AssistanceSignal.MIXED_INDEPENDENT_AND_ASSISTED
    return AssistanceSignal.ASSISTANCE_OBSERVED


def classify_parent_skill_progress(
    evidence: ParentSkillEvidence,
    *,
    policy: EvidenceSufficiencyPolicy | None = None,
) -> ParentSkillInsight:
    """Create a deterministic parent-facing projection from persisted evidence.

    This projection never changes tutoring state or mastery. Action codes are
    bounded communication guidance for the parent dashboard, not intervention
    decisions. F-010 may replace the evidence-sufficiency policy, but it cannot
    override existing mastery semantics through this read model.
    """

    active_policy = policy or ObservationOnlyEvidencePolicy()
    assistance = _assistance_signal(evidence)

    if evidence.attempt_count <= 0 or not active_policy.is_sufficient(evidence):
        return ParentSkillInsight(
            evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
            learning_state=ParentLearningState.NOT_STARTED,
            assistance_signal=assistance,
            reason_code="COLLECT_MORE_EVIDENCE",
            action_code=ParentActionCode.COLLECT_MORE_EVIDENCE,
        )

    if evidence.status == SkillStatus.MASTERED and evidence.independent_correct_count > 0:
        return ParentSkillInsight(
            evidence_status=EvidenceStatus.EVIDENCE_AVAILABLE,
            learning_state=ParentLearningState.INDEPENDENT_MASTERY,
            assistance_signal=assistance,
            reason_code="INDEPENDENT_MASTERY_EVIDENCE",
            action_code=ParentActionCode.RECOGNIZE_MASTERY,
        )

    if evidence.status == SkillStatus.REVIEW_DUE:
        return ParentSkillInsight(
            evidence_status=EvidenceStatus.EVIDENCE_AVAILABLE,
            learning_state=ParentLearningState.NEEDS_PRACTICE,
            assistance_signal=assistance,
            reason_code="EXISTING_REVIEW_DUE_STATE",
            action_code=ParentActionCode.FOLLOW_EXISTING_REVIEW_PLAN,
        )

    if evidence.independent_correct_count > 0:
        return ParentSkillInsight(
            evidence_status=EvidenceStatus.EVIDENCE_AVAILABLE,
            learning_state=ParentLearningState.INDEPENDENT_PROGRESS,
            assistance_signal=assistance,
            reason_code="INDEPENDENT_SUCCESS_OBSERVED",
            action_code=ParentActionCode.RECOGNIZE_INDEPENDENT_PROGRESS,
        )

    if evidence.hinted_correct_count > 0:
        return ParentSkillInsight(
            evidence_status=EvidenceStatus.EVIDENCE_AVAILABLE,
            learning_state=ParentLearningState.ASSISTED_SUCCESS,
            assistance_signal=assistance,
            reason_code="ASSISTED_SUCCESS_OBSERVED",
            action_code=ParentActionCode.ENCOURAGE_INDEPENDENT_ATTEMPT,
        )

    return ParentSkillInsight(
        evidence_status=EvidenceStatus.EVIDENCE_AVAILABLE,
        learning_state=ParentLearningState.IN_PROGRESS,
        assistance_signal=assistance,
        reason_code="ACTIVITY_OBSERVED_NO_NEGATIVE_INFERENCE",
        action_code=ParentActionCode.CONTINUE_CURRENT_LEARNING,
    )
