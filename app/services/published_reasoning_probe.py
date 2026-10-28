"""Server-derived misconception probe for an authenticated published question.

This service never accepts caller-supplied misconception labels or correctness.
It reconstructs a reviewed deterministic task and binds evidence to a stored
wrong Attempt. Diagnosis is feedback-only; no mastery or release gate is set.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attempt, Problem, TutorSession, TutorState, TutorTurn
from app.services.content_publishing import candidates, permitted
from app.services.fraction_assessment_registry import score_fraction
from scripts.author_ontario_linear_depth import _create_target_preserving_guided_retest


class PublishedProbeUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class PublishedReasoningProbe:
    attempt_id: object
    problem_id: object
    prompt: str
    choices: tuple[dict[str, str], ...]
    # Server-only evidence; never serialize the dataclass as an API response.
    misconception_code: str
    confirming_choice_id: str
    repair_questions: tuple[str, ...]


def resolve_published_reasoning_probe(
    db: Session, *, session: TutorSession, problem: Problem,
) -> PublishedReasoningProbe:
    if (
        session.status != "ACTIVE"
        or problem.source_type != "PUBLISHED"
        or problem.primary_skill_id not in {session.primary_skill_id, session.active_skill_id}
        or not isinstance(problem.solution, dict)
    ):
        raise PublishedProbeUnavailable("No eligible published reasoning probe")
    item_mode = problem.solution.get("mode")
    if item_mode not in {"guided", "diagnostic"} or not permitted(db, problem, item_mode):
        raise PublishedProbeUnavailable("Reasoning probes are restricted to guided learning")
    attempt = db.scalar(
        select(Attempt).where(
            Attempt.session_id == session.id,
            Attempt.student_id == session.student_id,
            Attempt.problem_id == problem.id,
        ).order_by(Attempt.created_at.desc(), Attempt.id.desc()).limit(1)
    )
    if (
        attempt is None
        or attempt.is_correct is not False
        or attempt.state_at_attempt not in {TutorState.DIAGNOSE, TutorState.GUIDED_PRACTICE}
        or attempt.state_at_attempt != (
            TutorState.DIAGNOSE if item_mode == "diagnostic" else TutorState.GUIDED_PRACTICE
        )
    ):
        raise PublishedProbeUnavailable("A stored wrong guided answer is required")
    prior = db.scalar(
        select(TutorTurn.id).where(
            TutorTurn.session_id == session.id,
            TutorTurn.problem_id == problem.id,
            TutorTurn.attempt_id == attempt.id,
            TutorTurn.pedagogical_action.in_(
                ("PUBLISHED_REASONING_CONFIRMED", "PUBLISHED_REASONING_SUBMITTED")
            ),
        ).limit(1)
    )
    if prior is not None:
        raise PublishedProbeUnavailable("Reasoning probe already confirmed")
    manifest = problem.solution.get("manifest")
    if not isinstance(manifest, dict):
        raise PublishedProbeUnavailable("Missing reviewed package provenance")
    matching = [
        item for mode, item in candidates(manifest)
        if mode == item_mode
        and item["variant_id"] == problem.solution.get("variant_id")
        and item["task_fingerprint"] == problem.solution.get("task_fingerprint")
        and item["canonical_answer"] == problem.canonical_answer
    ]
    if len(matching) != 1:
        raise PublishedProbeUnavailable("Issued variant is ambiguous")
    signals = [
        signal for signal in matching[0]["diagnostic_contract_for_author_review"]["signals"]
        if score_fraction(
            attempt.student_answer, signal["candidate_response"], variable="x"
        )
    ]
    if len(signals) != 1:
        raise PublishedProbeUnavailable("Wrong response has no unambiguous error signal")
    signal = signals[0]
    return PublishedReasoningProbe(
        attempt_id=attempt.id,
        problem_id=problem.id,
        prompt=signal["confirmation_probe_for_author_review"],
        choices=tuple(signal["confirmation_choices_for_learner"]),
        misconception_code=signal["misconception_code"],
        confirming_choice_id=signal["confirmation_evidence_choice_for_author_review"],
        repair_questions=tuple(signal["socratic_repair_for_author_review"]),
    )


def server_guided_retest(
    problem: Problem, *, misconception_code: str, retry_index: int = 0,
) -> dict:
    """Reconstruct the same-family guided retest; keep oracle server-private.

    The source comes from an approved, already-persisted publisher manifest.
    Client-supplied family, seed, fingerprint and misconception are never used.
    """
    if not isinstance(problem.solution, dict):
        raise PublishedProbeUnavailable("Missing published source")
    manifest = problem.solution.get("manifest")
    if not isinstance(manifest, dict):
        raise PublishedProbeUnavailable("Missing signed package")
    sources = [
        item for mode, item in candidates(manifest)
        if mode == problem.solution.get("mode")
        and item["variant_id"] == problem.solution.get("variant_id")
        and item["task_fingerprint"] == problem.solution.get("task_fingerprint")
        and item["canonical_answer"] == problem.canonical_answer
    ]
    if len(sources) != 1:
        raise PublishedProbeUnavailable("Published source is ambiguous")
    source = sources[0]
    valid_codes = {
        signal["misconception_code"]
        for signal in source["diagnostic_contract_for_author_review"]["signals"]
    }
    if misconception_code not in valid_codes:
        raise PublishedProbeUnavailable("Unknown diagnosis for issued task")
    if not 0 <= retry_index <= 2:
        raise PublishedProbeUnavailable("Guided retest retry limit reached")
    # Deterministic server-owned retry identity, never supplied by the learner.
    retry_source = dict(source)
    if retry_index:
        retry_source["variant_id"] = f"{source['variant_id']}|retry|{retry_index}"
    target, _signal = _create_target_preserving_guided_retest(
        retry_source, misconception_code,
    )
    prior_fingerprints = {source["task_fingerprint"]}
    for previous_index in range(retry_index):
        prior_fingerprints.add(server_guided_retest(
            problem, misconception_code=misconception_code,
            retry_index=previous_index,
        )["task_fingerprint"])
    if target["task_fingerprint"] in prior_fingerprints:
        raise PublishedProbeUnavailable("Guided retry task is not distinct")
    if (
        target["candidate_family"] != source["candidate_family"]
        or target["canonical_skill_hint"] != source["canonical_skill_hint"]
        or target["task_fingerprint"] == source["task_fingerprint"]
        or target["canonical_answer"] == source["canonical_answer"]
        or target["mode"] != "GUIDED"
    ):
        raise PublishedProbeUnavailable("Guided retest was not fresh")
    return target
