"""Versioned fail-closed scoring registration. No runtime activation or mastery grant.

Only separately signed release declarations may become trusted approved-family
records. This pure adapter cannot issue independent evidence or modify history.
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
_VARIABLE = re.compile(r"[A-Za-z]\Z")
SCHEMA_VERSION = "mihur.family-registration.v1"


@dataclass(frozen=True)
class FamilyRegistration:
    """Signed content, scorer, schema and jurisdiction-scoped standards contract."""

    family: ReviewedFamily
    evidence: PackageReleaseEvidence
    scorer_revision: str
    source_mapping_revision: str
    answer_variable: str | None = None
    standards_manifest_sha: str = ""
    jurisdiction_code: str = ""
    curriculum_code: str = ""
    local_skill_code: str = ""
    mapping_disposition: str = ""
    coverage_credit: bool = False


@dataclass(frozen=True)
class RegistrationDecision:
    eligible: bool
    correct: bool
    independent_evidence_eligible: bool


DENIED = RegistrationDecision(False, False, False)


def compile_registration(
    schema_version: str, registrations: tuple[FamilyRegistration, ...]
) -> Mapping[str, FamilyRegistration]:
    """Preserve all signed evidence; never populate the production registry."""
    if schema_version != SCHEMA_VERSION or not isinstance(registrations, tuple):
        raise ValueError("unsupported registration schema")
    result: dict[str, FamilyRegistration] = {}
    for entry in registrations:
        if not isinstance(entry, FamilyRegistration):
            raise TypeError("invalid family registration")
        family = entry.family
        if (
            not isinstance(family, ReviewedFamily)
            or not isinstance(family.family_id, str)
            or not isinstance(family.canonical_skill_code, str)
            or not isinstance(family.content_sha, str)
            or _NAME.fullmatch(family.family_id) is None
            or _NAME.fullmatch(family.canonical_skill_code) is None
            or _SHA.fullmatch(family.content_sha) is None
            or not isinstance(entry.scorer_revision, str)
            or _SHA.fullmatch(entry.scorer_revision) is None
            or not isinstance(entry.source_mapping_revision, str)
            or _SHA.fullmatch(entry.source_mapping_revision) is None
            or not isinstance(entry.standards_manifest_sha, str)
            or _SHA.fullmatch(entry.standards_manifest_sha) is None
            or entry.mapping_disposition != "ACCEPTED"
            or entry.coverage_credit is not True
            or not isinstance(entry.jurisdiction_code, str)
            or not isinstance(entry.curriculum_code, str)
            or _NAME.fullmatch(entry.jurisdiction_code) is None
            or _NAME.fullmatch(entry.curriculum_code) is None
            or not isinstance(entry.local_skill_code, str)
            or _NAME.fullmatch(entry.local_skill_code) is None
            or family.answer_kind not in {AnswerKind.RATIONAL, AnswerKind.VARIABLE_VALUE}
            or not isinstance(family.modes, frozenset)
            or not family.modes
            or not all(isinstance(mode, AssessmentMode) for mode in family.modes)
            or family.content_sha != entry.evidence.package_sha
            or not release_preflight_passes(entry.evidence)
            or family.family_id in result
        ):
            raise ValueError("unapproved, ambiguous or duplicate family registration")
        if family.answer_kind is AnswerKind.VARIABLE_VALUE:
            if not isinstance(entry.answer_variable, str) or _VARIABLE.fullmatch(
                entry.answer_variable
            ) is None:
                raise ValueError("variable-value family must bind reviewed variable")
        elif entry.answer_variable is not None:
            raise ValueError("bare-rational family may not declare variable")
        result[family.family_id] = entry
    return MappingProxyType(result)


def score_registered_rational(
    registry: Mapping[str, FamilyRegistration],
    *,
    family_id: str,
    canonical_skill_code: str,
    content_sha: str,
    mode: AssessmentMode,
    canonical_answer: str,
    submitted_answer: str,
    variable: str | None = None,
    source_mapping_revision: str = "",
    standards_manifest_sha: str = "",
    jurisdiction_code: str = "",
    curriculum_code: str = "",
    local_skill_code: str = "",
    assisted: bool = False,
) -> RegistrationDecision:
    """Check a *signed* reviewed response schema; never award mastery evidence."""
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
        not isinstance(entry, FamilyRegistration)
        or entry.family.family_id != family_id
        or entry.family.canonical_skill_code != canonical_skill_code
        or entry.family.content_sha != content_sha
        or mode not in entry.family.modes
        or source_mapping_revision != entry.source_mapping_revision
        or standards_manifest_sha != entry.standards_manifest_sha
        or jurisdiction_code != entry.jurisdiction_code
        or curriculum_code != entry.curriculum_code
        or local_skill_code != entry.local_skill_code
        or entry.mapping_disposition != "ACCEPTED"
        or entry.coverage_credit is not True
    ):
        return DENIED
    if entry.family.answer_kind is AnswerKind.RATIONAL:
        if variable is not None or entry.answer_variable is not None:
            return DENIED
    elif entry.family.answer_kind is AnswerKind.VARIABLE_VALUE:
        if (
            not isinstance(variable, str)
            or not isinstance(entry.answer_variable, str)
            or variable.casefold() != entry.answer_variable.casefold()
        ):
            return DENIED
    else:
        return DENIED
    correct = score_fraction(submitted_answer, canonical_answer, variable=variable)
    # A correct, unassisted reply cannot prove a fresh, server-issued attempt.
    # Independent mastery requires a separate issuance/journey evidence gate.
    return RegistrationDecision(eligible=True, correct=correct, independent_evidence_eligible=False)
