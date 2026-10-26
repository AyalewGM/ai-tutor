"""Read-only, server-resolved assessment boundary for reviewed rational families.

No HTTP route, seed/activation operation, mode grants or learner-history writes.
The caller must obtain principal/student IDs from trusted authentication, never
from submitted answer payloads. Approvals must come from an independent service.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_models import ProblemContentMetadata
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.models import Curriculum, Problem, Skill, TutorSession, TutorState
from app.services.family_activation_adapter import (
    DENIED,
    SCHEMA_VERSION,
    FamilyRegistration,
    RegistrationDecision,
    compile_registration,
    score_registered_rational,
)
from app.services.fraction_assessment_registry import AssessmentMode
from app.services.issued_rational_evidence import verify_fresh_issuance


class AuthenticatedApprovalSource(Protocol):
    """Only a separately authenticated release authority may implement this."""

    def approved_records(self, *, service_principal: str) -> tuple[FamilyRegistration, ...]: ...


@dataclass(frozen=True)
class TrustedAssessmentContext:
    student_id: uuid.UUID
    session_id: uuid.UUID
    problem_id: uuid.UUID
    mode: AssessmentMode
    assisted: bool = False


_STATE_MODES = {
    TutorState.DIAGNOSE: AssessmentMode.DIAGNOSTIC,
    TutorState.GUIDED_PRACTICE: AssessmentMode.GUIDED,
    TutorState.INDEPENDENT_PRACTICE: AssessmentMode.INDEPENDENT,
    TutorState.MASTERY_CHECK: AssessmentMode.MASTERY,
}


def score_persisted_rational(
    db: Session,
    *,
    context: TrustedAssessmentContext,
    submission: str,
    approval_source: AuthenticatedApprovalSource | None = None,
    service_principal: str | None = None,
) -> RegistrationDecision:
    """Fail closed until authenticated source, stored provenance and ownership exist.

    The approval source is an injected trusted service credential boundary,
    not a self-declared URL/reviewer field. This module does NOT implement
    production authentication or authorization and cannot enable learners.
    """
    if (
        not isinstance(context, TrustedAssessmentContext)
        or not isinstance(submission, str)
        or not isinstance(context.student_id, uuid.UUID)
        or not isinstance(context.session_id, uuid.UUID)
        or not isinstance(context.problem_id, uuid.UUID)
        or not isinstance(context.mode, AssessmentMode)
        or type(context.assisted) is not bool
        or approval_source is None
        or not isinstance(service_principal, str)
        or not service_principal.strip()
    ):
        return DENIED
    session = db.scalar(
        select(TutorSession).where(
            TutorSession.id == context.session_id,
            TutorSession.student_id == context.student_id,
            TutorSession.status == "ACTIVE",
        )
    )
    if session is None or _STATE_MODES.get(session.current_state) != context.mode:
        return DENIED
    problem = db.scalar(select(Problem).where(Problem.id == context.problem_id))
    if (
        problem is None
        or problem.primary_skill_id not in {session.primary_skill_id, session.active_skill_id}
        or not problem.canonical_answer
    ):
        return DENIED
    if context.mode in {AssessmentMode.INDEPENDENT, AssessmentMode.MASTERY} and not verify_fresh_issuance(
        db, student_id=context.student_id, session_id=context.session_id,
        problem=problem, mode=context.mode,
    ):
        return DENIED
    skill = db.scalar(select(Skill).where(Skill.id == problem.primary_skill_id))
    metadata = db.scalar(select(ProblemContentMetadata).where(
        ProblemContentMetadata.problem_id == problem.id,
    ))
    if (
        skill is None
        or metadata is None
        or skill.curriculum_id != session.curriculum_id
        or metadata.curriculum_id != session.curriculum_id
    ):
        return DENIED
    mapping = db.scalar(select(CurriculumSkillMapping).where(
        CurriculumSkillMapping.skill_id == skill.id,
        CurriculumSkillMapping.mapping_type == "EQUIVALENT",
    ))
    if mapping is None:
        return DENIED
    canonical = db.scalar(select(CanonicalSkill).where(
        CanonicalSkill.id == mapping.canonical_skill_id,
    ))
    curriculum = db.scalar(select(Curriculum).where(
        Curriculum.id == session.curriculum_id,
    ))
    if (
        canonical is None or curriculum is None
        or not curriculum.country_code or not curriculum.region_code
    ):
        return DENIED
    mapping_evidence = mapping.provenance_json
    if (
        not isinstance(mapping_evidence, dict)
        or set(mapping_evidence) != {
            "source_mapping_revision", "standards_manifest_sha",
            "disposition", "coverage_credit",
        }
        or mapping_evidence.get("disposition") != "ACCEPTED"
        or mapping_evidence.get("coverage_credit") is not True
    ):
        return DENIED
    eligible_fields = {
        AssessmentMode.DIAGNOSTIC: metadata.diagnostic_eligible,
        AssessmentMode.GUIDED: metadata.guided_eligible,
        AssessmentMode.INDEPENDENT: metadata.independent_eligible,
        AssessmentMode.MASTERY: metadata.mastery_eligible,
    }
    if eligible_fields.get(context.mode) is not True:
        return DENIED
    # Provenance must originate in persisted application-owned metadata.
    provenance = metadata.provenance_json
    if not isinstance(provenance, dict) or set(provenance) != {
        "family_id", "content_sha", "source_mapping_revision", "standards_manifest_sha",
    }:
        return DENIED
    family = provenance.get("family_id")
    revision = provenance.get("content_sha")
    if (
        not isinstance(family, str) or not isinstance(revision, str)
        or not isinstance(provenance["source_mapping_revision"], str)
        or not isinstance(provenance["standards_manifest_sha"], str)
        or provenance["source_mapping_revision"] != mapping_evidence["source_mapping_revision"]
        or provenance["standards_manifest_sha"] != mapping_evidence["standards_manifest_sha"]
    ):
        return DENIED
    try:
        entries = approval_source.approved_records(service_principal=service_principal)
        registry = compile_registration(SCHEMA_VERSION, entries)
    except (ValueError, TypeError, PermissionError):
        return DENIED
    variable = None
    if problem.answer_kind == "VARIABLE_VALUE":
        match = re.fullmatch(
            r"\s*([A-Za-z])\s*=\s*[+-]?\d+(?:/[+-]?\d+)?\s*",
            problem.canonical_answer,
        )
        if match is None:
            return DENIED
        variable = match.group(1)
    elif problem.answer_kind != "RATIONAL":
        return DENIED
    return score_registered_rational(
        registry, family_id=family, canonical_skill_code=canonical.code,
        content_sha=revision, mode=context.mode,
        source_mapping_revision=provenance["source_mapping_revision"],
        standards_manifest_sha=provenance["standards_manifest_sha"],
        jurisdiction_code=f"{curriculum.country_code}.{curriculum.region_code}",
        curriculum_code=curriculum.code,
        local_skill_code=skill.code,
        canonical_answer=problem.canonical_answer,
        submitted_answer=submission, variable=variable, assisted=context.assisted,
    )
