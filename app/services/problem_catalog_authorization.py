"""Explicit compatibility authorization for the active authored catalog.

The legacy seeders predate ``ProblemContentMetadata``.  This module is the
single bounded bridge for those already-supported, learner-visible rows.  It
does not infer authority from a curriculum or problem type alone: a problem
must be curated and carry the exact authored provenance emitted by the
repository's production seeders.  Draft, generated, QA-only, inactive, and
unknown-provenance rows remain fail closed.

The compatibility policy preserves the historical availability of approved
catalog rows in every ordinary tutor mode.  Cross-session selection still
prevents a learner from receiving the same problem in a later mode/session.
New packages must continue to provide their own narrower mode metadata.
"""

from collections.abc import Collection

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_models import ProblemContentMetadata
from app.models import Curriculum, Problem, Skill

ACTIVE_CATALOG_POLICY_VERSION = "ACTIVE_AUTHORED_CATALOG_V1_20261018"
_AUTHORIZED_ORIGIN = "AUTHORED"
_AUTHORIZED_AUTHOR = "AI Tutor curriculum team"
_AUTHORIZED_LICENSES = frozenset({"proprietary"})
_QA_ONLY_SKILL_CODES = frozenset({"M8.PROB.MARBLE_QA"})


def authorize_active_authored_catalog(
    db: Session,
    *,
    curriculum_codes: Collection[str] | None = None,
) -> int:
    """Add explicit mode metadata to eligible legacy authored rows.

    Existing metadata is authoritative and is never widened or replaced.
    The caller owns the transaction so seed scripts can commit catalog rows
    and their authorization atomically.
    """

    stmt = (
        select(Problem, Skill, Curriculum)
        .join(Skill, Skill.id == Problem.primary_skill_id)
        .join(Curriculum, Curriculum.id == Skill.curriculum_id)
        .outerjoin(
            ProblemContentMetadata,
            ProblemContentMetadata.problem_id == Problem.id,
        )
        .where(
            Curriculum.active.is_(True),
            Problem.source_type == "CURATED",
            ProblemContentMetadata.id.is_(None),
        )
    )
    if curriculum_codes is not None:
        codes = tuple(sorted(set(curriculum_codes)))
        if not codes:
            return 0
        stmt = stmt.where(Curriculum.code.in_(codes))

    authorized = 0
    for problem, skill, curriculum in db.execute(stmt):
        if skill.code in _QA_ONLY_SKILL_CODES:
            continue
        provenance = (problem.solution or {}).get("provenance")
        if not _is_authorized_provenance(provenance):
            continue
        db.add(
            ProblemContentMetadata(
                problem_id=problem.id,
                curriculum_id=curriculum.id,
                objective="Legacy active authored catalog compatibility authorization.",
                evaluation_type="EXACT_OR_DECLARED_CANONICAL",
                diagnostic_eligible=True,
                guided_eligible=True,
                independent_eligible=True,
                mastery_eligible=True,
                extension_eligible=False,
                llm_solution_required=False,
                provenance_json={
                    "policy": ACTIVE_CATALOG_POLICY_VERSION,
                    "scope": "EXISTING_ACTIVE_AUTHORED_CATALOG",
                    "source_problem_type": problem.problem_type,
                    "source_curriculum_code": curriculum.code,
                    "history_policy": "INSERT_METADATA_ONLY",
                    "new_draft_authorization": False,
                },
            )
        )
        authorized += 1

    if authorized:
        db.flush()
    return authorized


def _is_authorized_provenance(provenance: object) -> bool:
    if not isinstance(provenance, dict):
        return False
    return (
        provenance.get("origin") == _AUTHORIZED_ORIGIN
        and provenance.get("author") == _AUTHORIZED_AUTHOR
        and provenance.get("license") in _AUTHORIZED_LICENSES
    )
