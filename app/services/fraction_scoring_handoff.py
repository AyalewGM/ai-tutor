"""Fail-closed scoring handoff for a *trusted* persisted rational item.

The application must resolve the problem, learner identity and stored oracle
before calling this service. Client requests must never supply the answer key,
reviewed family identity or content revision as authority. No persistence here.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.fraction_assessment_registry import (
    AssessmentMode,
    is_registered_for_mode,
    score_fraction,
)


@dataclass(frozen=True)
class TrustedRationalItem:
    """Server-owned assessment provenance, never built from a client payload."""

    family_id: str
    canonical_skill_code: str
    content_sha: str
    canonical_answer: str
    variable: str | None = None


@dataclass(frozen=True)
class ScoringDecision:
    accepted: bool
    correct: bool
    independent_evidence_eligible: bool


DENIED = ScoringDecision(False, False, False)


def score_registered_item(
    item: TrustedRationalItem, submitted_answer: str, mode: AssessmentMode, *,
    assisted: bool = False,
) -> ScoringDecision:
    """Score only a registered exact family/mode; never write mastery.

    Whether a *correct* independent answer yields a MasteryEvent is separately
    governed by the canonical assessment state machine and attempt persistence.
    """
    if (
        not isinstance(item, TrustedRationalItem)
        or not isinstance(submitted_answer, str)
        or not isinstance(mode, AssessmentMode)
        or type(assisted) is not bool
        or not is_registered_for_mode(
            item.family_id, item.canonical_skill_code, item.content_sha, mode
        )
    ):
        return DENIED
    correct = score_fraction(
        submitted_answer, item.canonical_answer, variable=item.variable
    )
    return ScoringDecision(
        accepted=True,
        correct=correct,
        independent_evidence_eligible=(
            correct and not assisted and mode in {
                AssessmentMode.INDEPENDENT, AssessmentMode.MASTERY
            }
        ),
    )
