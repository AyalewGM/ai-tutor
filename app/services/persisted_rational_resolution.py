"""Read-only, server-resolved assessment boundary for reviewed rational families.

No HTTP route, seed/activation operation, mode grants or learner-history writes.
The caller must obtain principal/student IDs from trusted authentication, never
from submitted answer payloads. Approvals must come from an independent service.
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Problem, Skill, TutorSession, TutorState
from app.services.family_activation_adapter import (
    DENIED,
    FamilyRegistration,
    RegistrationDecision,
    compile_registration,
    score_registered_rational,
    SCHEMA_VERSION,
)
from app.services.fraction_assessment_registry import AssessmentMode


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
    # Trusted server-provided immutable problem provenance, not a request field.
    stored_provenance: Mapping[str, str] | None = None,
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
        or not isinstance(stored_provenance, Mapping)
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
    skill = db.scalar(select(Skill).where(Skill.id == problem.primary_skill_id))
    if skill is None or len(stored_provenance) != 2:
        return DENIED
    # Independently persisted family identity + exact source revision.
    family = stored_provenance.get("family_id")
    revision = stored_provenance.get("content_sha")
    if not isinstance(family, str) or not isinstance(revision, str):
        return DENIED
    try:
        entries = approval_source.approved_records(service_principal=service_principal)
        registry = compile_registration(SCHEMA_VERSION, entries)
    except (ValueError, TypeError, PermissionError):
        return DENIED
    return score_registered_rational(
        registry, family_id=family, canonical_skill_code=skill.code,
        content_sha=revision, mode=context.mode,
        canonical_answer=problem.canonical_answer,
        submitted_answer=submission, assisted=context.assisted,
    )
