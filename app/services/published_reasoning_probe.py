"""Server-derived misconception probe for an authenticated published question.

This service never accepts caller-supplied misconception labels or correctness.
It reconstructs a reviewed deterministic task and binds evidence to a stored
wrong Attempt. Diagnosis is feedback-only; no mastery or release gate is set.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attempt, Problem, TutorSession, TutorState, TutorTurn
from app.services.content_publishing import candidates, permitted
from app.services.fraction_assessment_registry import score_fraction
from scripts.author_ontario_linear_depth import (
    _create_target_preserving_guided_retest,
    create_unhinted_transfer,
)


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


# Each confirmed misconception has its own *corrective* reasoning checkpoint.
# IDs are internal and the expected ID must never be returned to the learner.
_TARGETED_REPAIR = {
    "EQ.OMIT_CONSTANT": (
        "Before dividing, what should you do to the additive constant?",
        "REMOVE_CONSTANT_BOTH_SIDES",
        "Remove it from both complete sides", "Ignore it", "Divide first",
    ),
    "EQ.MULTIPLY_INSTEAD_OF_DIVIDE_FRACTION": (
        "What undoes multiplication by a nonzero fractional coefficient?",
        "USE_RECIPROCAL_BOTH_SIDES",
        "Multiply both complete sides by its reciprocal",
        "Multiply by the original coefficient again", "Change only one side",
    ),
    "EQ.DROPPED_BRACKET_CONSTANT": (
        "What happens when distributing a negative factor into parentheses?",
        "DISTRIBUTE_ALL_TERMS",
        "Multiply every term, including the constant",
        "Multiply only the variable", "Change just the sign of the constant",
    ),
    "EQ.IGNORED_RIGHT_VARIABLE": (
        "How can the variable term on the right be removed?",
        "SUBTRACT_RIGHT_TERM_BOTH_SIDES",
        "Subtract the complete right variable term from both sides",
        "Ignore the right variable", "Cancel only one side",
    ),
    "EQ.MOVED_LEFT_CONSTANT_WRONG_SIGN": (
        "How do you remove the original left-side constant?",
        "INVERSE_BOTH_SIDES",
        "Use its inverse operation on both complete sides",
        "Change its sign without balancing", "Move it unchanged",
    ),
    "EQ.OMITTED_LEFT_CONSTANT": (
        "What must happen before dividing by the variable coefficient?",
        "ISOLATE_PRODUCT_FIRST",
        "Remove the additive term on both sides first",
        "Divide while the constant remains", "Drop the constant",
    ),
    "EQ.ADDED_VARIABLE_COEFFICIENTS": (
        "How should variable coefficients on opposite sides be combined?",
        "SUBTRACT_VARIABLE_TERM",
        "Subtract one complete variable term on both sides",
        "Add coefficients without balancing", "Cancel both terms",
    ),
    "EQ.USED_RECIPROCAL_WRONG_DIRECTION": (
        "How do you make the isolated variable coefficient equal one?",
        "UNDO_COEFFICIENT",
        "Divide by the coefficient or multiply by its reciprocal",
        "Multiply by the same coefficient", "Invert only one side",
    ),
}


def server_targeted_repair(
    misconception_code: str, *, task_fingerprint: str,
) -> dict:
    """Neutral, per-task ordered choices with the oracle kept server-private."""
    entry = _TARGETED_REPAIR.get(misconception_code)
    if entry is None or not task_fingerprint:
        raise PublishedProbeUnavailable("No reviewed targeted repair for diagnosis")
    question, _action, correct, wrong_a, wrong_b = entry
    texts = (correct, wrong_a, wrong_b)
    # Deterministic for a persisted task, but neither ID nor position marks
    # the correct choice. Different tasks shuffle choices independently.
    ordered = sorted(range(3), key=lambda i: hashlib.sha256(
        f"{task_fingerprint}|repair|{misconception_code}|{i}".encode()
    ).digest())
    return {
        "prompt": question,
        "choices": tuple(
            {"id": f"OPTION_{position + 1}", "text": texts[item]}
            for position, item in enumerate(ordered)
        ),
        "expected": f"OPTION_{ordered.index(0) + 1}",
    }


def server_repair_coefficients(problem: Problem) -> dict[str, str]:
    """Return exact coefficients from the uniquely matched signed source task."""
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
        raise PublishedProbeUnavailable("Repair source is ambiguous")
    coefficients = sources[0].get("equation_coefficients")
    if not isinstance(coefficients, dict) or {
        "lhs_x", "lhs_constant", "rhs_x", "rhs_constant",
    } - coefficients.keys():
        raise PublishedProbeUnavailable("Reviewable repair coefficients unavailable")
    return coefficients


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


def server_unhinted_transfer(
    problem: Problem, *, misconception_code: str, guided_retry_index: int,
) -> dict:
    """Derive an alternate-family independent task without mastery authority."""
    guided = server_guided_retest(
        problem, misconception_code=misconception_code,
        retry_index=guided_retry_index,
    )
    transfer = create_unhinted_transfer(guided)
    if (
        not transfer["reasoning_structure_changed"]
        or not transfer["task_fingerprint_changed"]
        or transfer["target_family"] == guided["candidate_family"]
        or transfer["private_target_fingerprint_for_review"]
        in {guided["task_fingerprint"], problem.solution["task_fingerprint"]}
        or transfer["learner_task"]["mode"] != "INDEPENDENT"
        or transfer["hints_allowed"]
        or transfer["runtime_credit_authorized"]
    ):
        raise PublishedProbeUnavailable("Independent transfer contract invalid")
    return transfer


def server_distinct_mastery_task(
    problem: Problem, *, misconception_code: str, guided_retry_index: int,
) -> dict:
    """Separate, fresh exact-oracle mastery *verification*, never credit issuance."""
    guided = server_guided_retest(
        problem, misconception_code=misconception_code,
        retry_index=guided_retry_index,
    )
    transfer = server_unhinted_transfer(
        problem, misconception_code=misconception_code,
        guided_retry_index=guided_retry_index,
    )
    mastery = create_unhinted_transfer(guided, target_mode="MASTERY")
    if (
        mastery["target_mode"] != "MASTERY"
        or mastery["learner_task"]["mode"] != "MASTERY"
        or mastery["hints_allowed"] is not False
        or mastery["runtime_credit_authorized"] is not False
        or mastery["target_family"] == guided["candidate_family"]
        or mastery["target_family"] != transfer["target_family"]
        or mastery["private_target_fingerprint_for_review"] in {
            problem.solution["task_fingerprint"],
            guided["task_fingerprint"],
            transfer["private_target_fingerprint_for_review"],
        }
        or mastery["private_exact_oracle_for_review"] in {
            problem.canonical_answer,
            guided["canonical_answer"],
            transfer["private_exact_oracle_for_review"],
        }
    ):
        raise PublishedProbeUnavailable("Mastery verification task is not distinct")
    return mastery
