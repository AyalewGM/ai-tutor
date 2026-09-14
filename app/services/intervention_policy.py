from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class InterventionState(StrEnum):
    NO_INTERVENTION = "NO_INTERVENTION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    PREREQUISITE_GAP_CONFIRMED = "PREREQUISITE_GAP_CONFIRMED"


@dataclass(frozen=True)
class IndependentAttemptEvidence:
    """Minimal persisted evidence required by the deterministic policy.

    The policy intentionally consumes structured application evidence only. It does
    not accept free-form LLM judgments or inferred skill equivalences.
    """

    evidence_id: uuid.UUID
    curriculum_id: uuid.UUID
    skill_id: uuid.UUID
    problem_id: uuid.UUID
    correct: bool
    assistance_level: int
    occurred_at: datetime

    @property
    def is_independent(self) -> bool:
        return self.assistance_level == 0


@dataclass(frozen=True)
class DeclaredPrerequisiteEdge:
    curriculum_id: uuid.UUID
    skill_id: uuid.UUID
    prerequisite_skill_id: uuid.UUID


@dataclass(frozen=True)
class InterventionPolicy:
    """Versioned pilot policy hypothesis, never a learner-facing truth."""

    version: str = "pilot-v1"
    target_independent_failure_threshold: int = 2
    prerequisite_independent_failure_threshold: int = 2

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("policy version is required")
        if self.target_independent_failure_threshold < 2:
            raise ValueError("target failure threshold must be at least 2")
        if self.prerequisite_independent_failure_threshold < 2:
            raise ValueError("prerequisite failure threshold must be at least 2")


@dataclass(frozen=True)
class InterventionDecision:
    state: InterventionState
    reason_code: str
    policy_version: str
    evidence_ids: tuple[uuid.UUID, ...]
    selected_prerequisite_skill_id: uuid.UUID | None
    return_condition: str | None


def _qualifying_failures(
    evidence: list[IndependentAttemptEvidence],
    *,
    curriculum_id: uuid.UUID,
    skill_id: uuid.UUID,
    window_start: datetime,
    superseded_before: datetime | None = None,
) -> list[IndependentAttemptEvidence]:
    cutoff = max(window_start, superseded_before) if superseded_before is not None else window_start
    candidates = [
        item
        for item in evidence
        if item.curriculum_id == curriculum_id
        and item.skill_id == skill_id
        and item.is_independent
        and not item.correct
        and item.occurred_at > cutoff
    ]

    # Multiple retries on the same problem do not manufacture independent breadth.
    latest_by_problem: dict[uuid.UUID, IndependentAttemptEvidence] = {}
    for item in candidates:
        existing = latest_by_problem.get(item.problem_id)
        if existing is None or item.occurred_at > existing.occurred_at:
            latest_by_problem[item.problem_id] = item
    return sorted(latest_by_problem.values(), key=lambda item: (item.occurred_at, str(item.evidence_id)))


def decide_intervention(
    *,
    policy: InterventionPolicy,
    curriculum_id: uuid.UUID,
    target_skill_id: uuid.UUID,
    prerequisite_edge: DeclaredPrerequisiteEdge | None,
    evidence: list[IndependentAttemptEvidence],
    evidence_window_start: datetime,
    prerequisite_mastery_at: datetime | None = None,
) -> InterventionDecision:
    """Return an auditable deterministic intervention recommendation.

    This function does not mutate tutoring/mastery state. The caller may use the
    structured decision to drive application-owned routing. Any LLM may only
    verbalize the returned decision and must not alter it.
    """

    target_failures = _qualifying_failures(
        evidence,
        curriculum_id=curriculum_id,
        skill_id=target_skill_id,
        window_start=evidence_window_start,
    )
    if len(target_failures) < policy.target_independent_failure_threshold:
        return InterventionDecision(
            state=InterventionState.NO_INTERVENTION,
            reason_code="TARGET_STRUGGLE_THRESHOLD_NOT_MET",
            policy_version=policy.version,
            evidence_ids=tuple(item.evidence_id for item in target_failures),
            selected_prerequisite_skill_id=None,
            return_condition=None,
        )

    if prerequisite_edge is None:
        return InterventionDecision(
            state=InterventionState.INSUFFICIENT_EVIDENCE,
            reason_code="NO_DECLARED_PREREQUISITE_EDGE",
            policy_version=policy.version,
            evidence_ids=tuple(item.evidence_id for item in target_failures),
            selected_prerequisite_skill_id=None,
            return_condition="COLLECT_CURRICULUM_LOCAL_PREREQUISITE_EVIDENCE",
        )

    if (
        prerequisite_edge.curriculum_id != curriculum_id
        or prerequisite_edge.skill_id != target_skill_id
    ):
        raise ValueError("prerequisite edge must belong to the selected curriculum and target skill")

    prerequisite_failures = _qualifying_failures(
        evidence,
        curriculum_id=curriculum_id,
        skill_id=prerequisite_edge.prerequisite_skill_id,
        window_start=evidence_window_start,
        superseded_before=prerequisite_mastery_at,
    )
    combined_ids = tuple(
        item.evidence_id for item in [*target_failures, *prerequisite_failures]
    )

    if len(prerequisite_failures) < policy.prerequisite_independent_failure_threshold:
        return InterventionDecision(
            state=InterventionState.INSUFFICIENT_EVIDENCE,
            reason_code="PREREQUISITE_EVIDENCE_INSUFFICIENT",
            policy_version=policy.version,
            evidence_ids=combined_ids,
            selected_prerequisite_skill_id=prerequisite_edge.prerequisite_skill_id,
            return_condition="COLLECT_FRESH_INDEPENDENT_PREREQUISITE_EVIDENCE",
        )

    return InterventionDecision(
        state=InterventionState.PREREQUISITE_GAP_CONFIRMED,
        reason_code="DECLARED_PREREQUISITE_GAP_CONFIRMED",
        policy_version=policy.version,
        evidence_ids=combined_ids,
        selected_prerequisite_skill_id=prerequisite_edge.prerequisite_skill_id,
        return_condition="REQUIRE_FRESH_INDEPENDENT_SUCCESS_BEFORE_RETURN_TO_TARGET",
    )
