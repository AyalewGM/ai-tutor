"""Strict offline authoring-journey verifier, NEVER a learner mastery/release gate.

The earlier metadata-only trace shape could claim false diagnostic corroboration.
The strict verifier instead reconstructs author-side exact rational oracles,
reasoning-choice confirmation, fresh guided retest and unhinted transfer using
the existing #489 authoring model. It neither authenticates real learners nor
grants scoring modes or release authority.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from scripts.author_ontario_linear_depth import (
    create_candidate,
    simulate_authored_learning_journey,
)


@dataclass(frozen=True)
class JourneyEvent:
    """Legacy metadata-only shape; insufficient as mathematical evidence."""

    stage: str
    family: str
    fingerprint: str
    correct: bool
    misconception: str | None = None
    assisted: bool = False


@dataclass(frozen=True)
class AuthorJourneyInputs:
    """Original author-side task and responses, not trusted learner records."""

    family: str
    seed: str | int
    practice_response: str
    reasoning_choice: str
    guided_retest_response: str
    independent_response: str


@dataclass(frozen=True)
class AuthorJourneyReport:
    verified_math: bool
    source_fingerprint: str
    guided_retest_fingerprint: str
    transfer_fingerprint: str
    changed_reasoning_family: bool
    runtime_credit_authorized: bool = False


class JourneyNotVerified(ValueError):
    pass


def verify_journey(events: Sequence[JourneyEvent]) -> None:
    """Legacy metadata-only events cannot justify release or mathematical QA."""
    raise JourneyNotVerified(
        "Metadata labels and correctness booleans are not validated response "
        "or independent learner-issuance evidence"
    )


def verify_authored_journey(inputs: AuthorJourneyInputs) -> AuthorJourneyReport:
    """Reconstruct a complete *author-side* original-source practice journey.

    Every mathematical equality is checked by the existing generator's
    deterministic oracle. This is not independent production certification.
    """
    if not isinstance(inputs, AuthorJourneyInputs) or not all(
        isinstance(value, str) and 0 < len(value) <= 64
        for value in (
            inputs.practice_response,
            inputs.reasoning_choice,
            inputs.guided_retest_response,
            inputs.independent_response,
        )
    ):
        raise JourneyNotVerified("Responses and reasoning must be supplied")
    try:
        source = create_candidate(inputs.family, seed=inputs.seed, mode="GUIDED")
        diagnosis = simulate_authored_learning_journey(
            source,
            practice_response=inputs.practice_response,
            follow_up_reasoning_response=inputs.reasoning_choice,
        )
        if diagnosis.get("stage") != "GUIDED_RETEST":
            raise JourneyNotVerified("Wrong response and reasoning not corroborated")
        guided = diagnosis["private_guided_retest_for_author_review"]
        if guided["candidate_family"] != source["candidate_family"]:
            raise JourneyNotVerified("Guided retest family changed")
        if guided["task_fingerprint"] == source["task_fingerprint"]:
            raise JourneyNotVerified("Guided retest not mathematically fresh")

        readiness = simulate_authored_learning_journey(
            source,
            practice_response=inputs.practice_response,
            follow_up_reasoning_response=inputs.reasoning_choice,
            guided_retest_response=inputs.guided_retest_response,
        )
        if readiness.get("stage") != "READY_FOR_TRANSFER_CONFIRMATION":
            raise JourneyNotVerified("Fresh guided retest not completed correctly")

        exit_task = simulate_authored_learning_journey(
            source,
            practice_response=inputs.practice_response,
            follow_up_reasoning_response=inputs.reasoning_choice,
            guided_retest_response=inputs.guided_retest_response,
            readiness_confirmed=True,
        )
        if exit_task.get("stage") != "INDEPENDENT_EXIT":
            raise JourneyNotVerified("Unhinted independent exit was not issued")
        transfer = exit_task["private_transfer_for_author_review"]
        independent = exit_task["independent_task"]
        if (
            transfer["hints_allowed"] is not False
            or transfer["runtime_credit_authorized"] is not False
            or transfer["target_family"] == guided["candidate_family"]
            or transfer["private_target_fingerprint_for_review"]
            in {source["task_fingerprint"], guided["task_fingerprint"]}
            or transfer["reasoning_structure_changed"] is not True
            or independent["mode"] != "INDEPENDENT"
        ):
            raise JourneyNotVerified("Independent transfer is not fresh or unassisted")

        completed = simulate_authored_learning_journey(
            source,
            practice_response=inputs.practice_response,
            follow_up_reasoning_response=inputs.reasoning_choice,
            guided_retest_response=inputs.guided_retest_response,
            readiness_confirmed=True,
            independent_response=inputs.independent_response,
        )
        if completed.get("stage") != "COMPLETE" or completed.get("runtime_credit_authorized") is not False:
            raise JourneyNotVerified("Independent answer not mathematically correct")
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, JourneyNotVerified):
            raise
        raise JourneyNotVerified("Author-side journey reconstruction failed") from exc

    return AuthorJourneyReport(
        verified_math=True,
        source_fingerprint=source["task_fingerprint"],
        guided_retest_fingerprint=guided["task_fingerprint"],
        transfer_fingerprint=transfer["private_target_fingerprint_for_review"],
        changed_reasoning_family=True,
    )
