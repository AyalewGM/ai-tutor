"""Versioned, fail-closed family registration adapter; no content is activated here.

A validated registration is a *candidate* for authorized runtime integration,
not permission to seed a database or grant learner-facing mode metadata.
Caller-supplied review evidence is not authenticated. Production wiring must
resolve independently authenticated approvals, student/session and problem IDs.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.answer_contracts import AnswerKind
from app.services.fraction_assessment_registry import (
    AssessmentMode,
    ReviewedFamily,
    score_fraction,
)
from app.services.question_package_release import (
    PackageReleaseEvidence,
    release_preflight_passes,
)

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_NAME = re.compile(r"[A-Z][A-Z0-9_.]{2,127}\Z")
SCHEMA_VERSION = "mihur.family-registration.v1"


@dataclass(frozen=True)
class FamilyRegistration:
    """One immutable, explicitly scoped reviewed family declaration."""

    family: ReviewedFamily
    evidence: PackageReleaseEvidence
    scorer_revision: str
    source_mapping_revision: str


@dataclass(frozen=True)
class RegistrationDecision:
    eligible: bool
    correct: bool
    independent_evidence_eligible: bool


DENIED = RegistrationDecision(False, False, False)


def compile_registration(
    schema_version: str, registrations: tuple[FamilyRegistration, ...]
) -> Mapping[str, ReviewedFamily]:
    """Validate exact release evidence; never mutate the global mode registry.

    The returned mapping is for isolated synthetic evaluation and later
    authenticated release assembly, not a runtime permission grant by itself.
    """
    if schema_version != SCHEMA_VERSION or not isinstance(registrations, tuple):
        raise ValueError("unsupported registration schema")
    result: dict[str, ReviewedFamily] = {}
    for registration in registrations:
        if not isinstance(registration, FamilyRegistration):
            raise TypeError("invalid family registration")
        family = registration.family
        if (
            not _NAME.fullmatch(family.family_id)
            or not _NAME.fullmatch(family.canonical_skill_code)
            or not _SHA.fullmatch(family.content_sha)
            or not _SHA.fullmatch(registration.scorer_revision)
            or not _SHA.fullmatch(registration.source_mapping_revision)
            or family.answer_kind not in {AnswerKind.RATIONAL, AnswerKind.VARIABLE_VALUE}
            or not family.modes
            or not all(isinstance(mode, AssessmentMode) for mode in family.modes)
            or family.content_sha != registration.evidence.package_sha
            or not release_preflight_passes(registration.evidence)
            or family.family_id in result
        ):
            raise ValueError("unapproved, ambiguous or duplicate family registration")
        result[family.family_id] = family
    return MappingProxyType(result)


def score_registered_rational(
    registry: Mapping[str, ReviewedFamily],
    *,
    family_id: str,
    canonical_skill_code: str,
    content_sha: str,
    mode: AssessmentMode,
    canonical_answer: str,
    submitted_answer: str,
    variable: str | None = None,
    assisted: bool = False,
) -> RegistrationDecision:
    """Pure server-side adapter; caller MUST resolve private oracle and identity.

    Never call with family, skill, revision or oracle taken from client input.
    A correct decision cannot itself write or approve a mastery event.
    """
    if (
        type(assisted) is not bool
        or not isinstance(mode, AssessmentMode)
        or not isinstance(registry, Mapping)
        or not isinstance(canonical_answer, str)
        or not isinstance(submitted_answer, str)
    ):
        return DENIED
    entry = registry.get(family_id)
    if (
        not isinstance(entry, ReviewedFamily)
        or entry.family_id != family_id
        or entry.canonical_skill_code != canonical_skill_code
        or entry.content_sha != content_sha
        or mode not in entry.modes
        or entry.answer_kind not in {AnswerKind.RATIONAL, AnswerKind.VARIABLE_VALUE}
    ):
        return DENIED
    correct = score_fraction(submitted_answer, canonical_answer, variable=variable)
    return RegistrationDecision(
        eligible=True,
        correct=correct,
        independent_evidence_eligible=(
            correct and not assisted and mode in {
                AssessmentMode.INDEPENDENT, AssessmentMode.MASTERY
            }
        ),
    )
