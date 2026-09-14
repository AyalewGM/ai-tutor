import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.services.intervention_policy import (
    DeclaredPrerequisiteEdge,
    IndependentAttemptEvidence,
    InterventionPolicy,
    InterventionState,
    decide_intervention,
)


NOW = datetime(2026, 9, 14, 16, 0, tzinfo=UTC)
WINDOW_START = NOW - timedelta(days=7)
CURRICULUM_ID = uuid.UUID("00000000-0000-0000-0000-000000000101")
OTHER_CURRICULUM_ID = uuid.UUID("00000000-0000-0000-0000-000000000102")
TARGET_SKILL_ID = uuid.UUID("00000000-0000-0000-0000-000000000201")
PREREQUISITE_SKILL_ID = uuid.UUID("00000000-0000-0000-0000-000000000202")


def _attempt(
    *,
    skill_id: uuid.UUID,
    problem_number: int,
    correct: bool = False,
    assistance_level: int = 0,
    curriculum_id: uuid.UUID = CURRICULUM_ID,
    occurred_at: datetime | None = None,
) -> IndependentAttemptEvidence:
    return IndependentAttemptEvidence(
        evidence_id=uuid.uuid5(uuid.NAMESPACE_URL, f"evidence-{skill_id}-{problem_number}-{occurred_at}"),
        curriculum_id=curriculum_id,
        skill_id=skill_id,
        problem_id=uuid.uuid5(uuid.NAMESPACE_URL, f"problem-{skill_id}-{problem_number}"),
        correct=correct,
        assistance_level=assistance_level,
        occurred_at=occurred_at or NOW,
    )


def _edge(*, curriculum_id: uuid.UUID = CURRICULUM_ID) -> DeclaredPrerequisiteEdge:
    return DeclaredPrerequisiteEdge(
        curriculum_id=curriculum_id,
        skill_id=TARGET_SKILL_ID,
        prerequisite_skill_id=PREREQUISITE_SKILL_ID,
    )


def test_single_target_failure_does_not_trigger_intervention() -> None:
    decision = decide_intervention(
        policy=InterventionPolicy(),
        curriculum_id=CURRICULUM_ID,
        target_skill_id=TARGET_SKILL_ID,
        prerequisite_edge=_edge(),
        evidence=[_attempt(skill_id=TARGET_SKILL_ID, problem_number=1)],
        evidence_window_start=WINDOW_START,
    )

    assert decision.state == InterventionState.NO_INTERVENTION
    assert decision.reason_code == "TARGET_STRUGGLE_THRESHOLD_NOT_MET"
    assert len(decision.evidence_ids) == 1


def test_target_struggle_without_prerequisite_evidence_is_insufficient() -> None:
    evidence = [
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=1),
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=2),
    ]
    decision = decide_intervention(
        policy=InterventionPolicy(version="pilot-v1"),
        curriculum_id=CURRICULUM_ID,
        target_skill_id=TARGET_SKILL_ID,
        prerequisite_edge=_edge(),
        evidence=evidence,
        evidence_window_start=WINDOW_START,
    )

    assert decision.state == InterventionState.INSUFFICIENT_EVIDENCE
    assert decision.reason_code == "PREREQUISITE_EVIDENCE_INSUFFICIENT"
    assert decision.selected_prerequisite_skill_id == PREREQUISITE_SKILL_ID
    assert decision.policy_version == "pilot-v1"


def test_two_plus_two_distinct_independent_failures_confirm_gap() -> None:
    evidence = [
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=1),
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=2),
        _attempt(skill_id=PREREQUISITE_SKILL_ID, problem_number=1),
        _attempt(skill_id=PREREQUISITE_SKILL_ID, problem_number=2),
    ]
    decision = decide_intervention(
        policy=InterventionPolicy(),
        curriculum_id=CURRICULUM_ID,
        target_skill_id=TARGET_SKILL_ID,
        prerequisite_edge=_edge(),
        evidence=evidence,
        evidence_window_start=WINDOW_START,
    )

    assert decision.state == InterventionState.PREREQUISITE_GAP_CONFIRMED
    assert decision.reason_code == "DECLARED_PREREQUISITE_GAP_CONFIRMED"
    assert len(decision.evidence_ids) == 4
    assert decision.return_condition == "REQUIRE_FRESH_INDEPENDENT_SUCCESS_BEFORE_RETURN_TO_TARGET"


def test_hinted_failures_do_not_satisfy_independent_thresholds() -> None:
    evidence = [
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=1),
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=2, assistance_level=1),
        _attempt(skill_id=PREREQUISITE_SKILL_ID, problem_number=1),
        _attempt(skill_id=PREREQUISITE_SKILL_ID, problem_number=2),
    ]
    decision = decide_intervention(
        policy=InterventionPolicy(),
        curriculum_id=CURRICULUM_ID,
        target_skill_id=TARGET_SKILL_ID,
        prerequisite_edge=_edge(),
        evidence=evidence,
        evidence_window_start=WINDOW_START,
    )

    assert decision.state == InterventionState.NO_INTERVENTION


def test_retries_on_same_problem_count_once() -> None:
    evidence = [
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=1, occurred_at=NOW - timedelta(minutes=2)),
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=1, occurred_at=NOW - timedelta(minutes=1)),
    ]
    decision = decide_intervention(
        policy=InterventionPolicy(),
        curriculum_id=CURRICULUM_ID,
        target_skill_id=TARGET_SKILL_ID,
        prerequisite_edge=_edge(),
        evidence=evidence,
        evidence_window_start=WINDOW_START,
    )

    assert decision.state == InterventionState.NO_INTERVENTION
    assert len(decision.evidence_ids) == 1


def test_more_recent_prerequisite_mastery_supersedes_older_failures() -> None:
    mastery_at = NOW - timedelta(hours=1)
    evidence = [
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=1),
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=2),
        _attempt(
            skill_id=PREREQUISITE_SKILL_ID,
            problem_number=1,
            occurred_at=NOW - timedelta(hours=3),
        ),
        _attempt(
            skill_id=PREREQUISITE_SKILL_ID,
            problem_number=2,
            occurred_at=NOW - timedelta(hours=2),
        ),
    ]
    decision = decide_intervention(
        policy=InterventionPolicy(),
        curriculum_id=CURRICULUM_ID,
        target_skill_id=TARGET_SKILL_ID,
        prerequisite_edge=_edge(),
        evidence=evidence,
        evidence_window_start=WINDOW_START,
        prerequisite_mastery_at=mastery_at,
    )

    assert decision.state == InterventionState.INSUFFICIENT_EVIDENCE
    assert decision.reason_code == "PREREQUISITE_EVIDENCE_INSUFFICIENT"


def test_cross_curriculum_evidence_cannot_satisfy_policy() -> None:
    evidence = [
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=1),
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=2),
        _attempt(
            skill_id=PREREQUISITE_SKILL_ID,
            problem_number=1,
            curriculum_id=OTHER_CURRICULUM_ID,
        ),
        _attempt(
            skill_id=PREREQUISITE_SKILL_ID,
            problem_number=2,
            curriculum_id=OTHER_CURRICULUM_ID,
        ),
    ]
    decision = decide_intervention(
        policy=InterventionPolicy(),
        curriculum_id=CURRICULUM_ID,
        target_skill_id=TARGET_SKILL_ID,
        prerequisite_edge=_edge(),
        evidence=evidence,
        evidence_window_start=WINDOW_START,
    )

    assert decision.state == InterventionState.INSUFFICIENT_EVIDENCE


def test_cross_curriculum_prerequisite_edge_fails_closed() -> None:
    with pytest.raises(ValueError, match="selected curriculum"):
        decide_intervention(
            policy=InterventionPolicy(),
            curriculum_id=CURRICULUM_ID,
            target_skill_id=TARGET_SKILL_ID,
            prerequisite_edge=_edge(curriculum_id=OTHER_CURRICULUM_ID),
            evidence=[
                _attempt(skill_id=TARGET_SKILL_ID, problem_number=1),
                _attempt(skill_id=TARGET_SKILL_ID, problem_number=2),
            ],
            evidence_window_start=WINDOW_START,
        )


def test_same_evidence_and_policy_replays_identically() -> None:
    evidence = [
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=1),
        _attempt(skill_id=TARGET_SKILL_ID, problem_number=2),
        _attempt(skill_id=PREREQUISITE_SKILL_ID, problem_number=1),
        _attempt(skill_id=PREREQUISITE_SKILL_ID, problem_number=2),
    ]
    args = {
        "policy": InterventionPolicy(version="pilot-v1"),
        "curriculum_id": CURRICULUM_ID,
        "target_skill_id": TARGET_SKILL_ID,
        "prerequisite_edge": _edge(),
        "evidence": evidence,
        "evidence_window_start": WINDOW_START,
    }

    assert decide_intervention(**args) == decide_intervention(**args)
