"""Curriculum-wide diagnostic campaigns (F-002 extension).

A campaign samples anchor skills across strands using the same per-skill
probe machinery as single-target placement sessions, then aggregates the
per-skill verdicts into a strand-level readiness report.
"""

import math
import uuid
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.content_models import (
    CurriculumExpectation,
    ExpectationSkillMapping,
    ProblemContentMetadata,
)
from app.diagnostic_models import DiagnosticAttempt, DiagnosticCampaign, DiagnosticSession
from app.models import Problem, Skill, SkillPrerequisite, SkillStatus, StudentSkill
from app.services.problem_generation import GENERATORS

QUESTION_BUDGET = 24
TARGET_CAP = 10
FALLBACK_STRAND = "General"


def strand_index(db: Session, curriculum_id: uuid.UUID) -> dict[uuid.UUID, str]:
    """Map each skill to its curriculum strand via expectation mappings."""
    rows = db.execute(
        select(ExpectationSkillMapping.skill_id, CurriculumExpectation.strand)
        .join(
            CurriculumExpectation,
            CurriculumExpectation.id == ExpectationSkillMapping.expectation_id,
        )
        .where(ExpectationSkillMapping.curriculum_id == curriculum_id)
    ).all()
    index: dict[uuid.UUID, str] = {}
    for skill_id, strand in rows:
        index.setdefault(skill_id, strand or FALLBACK_STRAND)
    return index


def dependent_counts(db: Session, curriculum_id: uuid.UUID) -> dict[uuid.UUID, int]:
    """How many curriculum skills list each skill as a direct prerequisite —
    a proxy for how much of the graph a gap blocks."""
    rows = db.execute(
        select(SkillPrerequisite.prerequisite_skill_id, func.count())
        .join(Skill, Skill.id == SkillPrerequisite.skill_id)
        .where(Skill.curriculum_id == curriculum_id)
        .group_by(SkillPrerequisite.prerequisite_skill_id)
    ).all()
    return {skill_id: int(count) for skill_id, count in rows}


def probeable_skills(db: Session, skill_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    """Skills that can serve diagnostic items: either stored diagnostic-
    eligible problems exist, or a generator-capable problem type can make
    deterministic variants on demand."""
    if not skill_ids:
        return set()
    eligible = set(
        db.scalars(
            select(Problem.primary_skill_id)
            .join(
                ProblemContentMetadata,
                ProblemContentMetadata.problem_id == Problem.id,
            )
            .where(
                Problem.primary_skill_id.in_(skill_ids),
                ProblemContentMetadata.diagnostic_eligible.is_(True),
            )
        ).all()
    )
    typed = db.execute(
        select(Problem.primary_skill_id, Problem.problem_type).where(
            Problem.primary_skill_id.in_(skill_ids)
        )
    ).all()
    generatable = {skill_id for skill_id, ptype in typed if ptype in GENERATORS}
    return eligible | generatable


def plan_targets(db: Session, *, student_id: uuid.UUID, curriculum_id: uuid.UUID) -> list[uuid.UUID]:
    """Rank anchor skills by information value (uncertainty x prerequisite
    centrality) and spread picks across strands."""
    skills = db.scalars(select(Skill).where(Skill.curriculum_id == curriculum_id)).all()
    if not skills:
        return []
    skill_ids = [skill.id for skill in skills]
    progress = {
        row.skill_id: row
        for row in db.scalars(
            select(StudentSkill).where(
                StudentSkill.student_id == student_id,
                StudentSkill.skill_id.in_(skill_ids),
            )
        ).all()
    }
    probeable = probeable_skills(db, skill_ids)
    deps = dependent_counts(db, curriculum_id)
    strands = strand_index(db, curriculum_id)

    by_strand: dict[str, list[tuple[float, Skill]]] = defaultdict(list)
    for skill in skills:
        row = progress.get(skill.id)
        if row is not None and row.status == SkillStatus.MASTERED:
            continue  # established evidence; no diagnostic value in re-probing
        if skill.id not in probeable:
            continue
        uncertainty = 1.0 - (float(row.confidence_score) if row else 0.0)
        score = uncertainty * (1.0 + math.log1p(deps.get(skill.id, 0)))
        by_strand[strands.get(skill.id, FALLBACK_STRAND)].append((score, skill))

    for ranked in by_strand.values():
        ranked.sort(key=lambda item: (-item[0], item[1].code))

    plan: list[uuid.UUID] = []
    while len(plan) < TARGET_CAP and any(by_strand.values()):
        for strand in sorted(by_strand):
            ranked = by_strand[strand]
            if ranked and len(plan) < TARGET_CAP:
                plan.append(ranked.pop(0)[1].id)
    return plan


@dataclass(frozen=True)
class SkillVerdict:
    verdict: str  # READY | PARTIAL | NOT_READY
    correct_count: int
    incorrect_count: int


def campaign_verdicts(db: Session, campaign_id: uuid.UUID) -> dict[uuid.UUID, SkillVerdict]:
    """Classify each skill attempted during the campaign using the same rule
    the per-skill controller applies: two consecutive independent correct
    answers mean ready."""
    attempts = db.scalars(
        select(DiagnosticAttempt)
        .join(
            DiagnosticSession,
            DiagnosticAttempt.diagnostic_session_id == DiagnosticSession.id,
        )
        .where(DiagnosticSession.campaign_id == campaign_id)
        .order_by(DiagnosticAttempt.sequence_number)
    ).all()
    by_skill: dict[uuid.UUID, list[DiagnosticAttempt]] = defaultdict(list)
    for attempt in attempts:
        by_skill[attempt.skill_id].append(attempt)

    verdicts: dict[uuid.UUID, SkillVerdict] = {}
    for skill_id, rows in by_skill.items():
        correct = sum(1 for row in rows if row.is_correct)
        incorrect = len(rows) - correct
        tail = rows[-2:]
        if len(tail) >= 2 and all(row.is_correct for row in tail):
            verdict = "READY"
        elif incorrect == 0:
            verdict = "PARTIAL"
        else:
            verdict = "NOT_READY"
        verdicts[skill_id] = SkillVerdict(
            verdict=verdict, correct_count=correct, incorrect_count=incorrect
        )
    return verdicts


def attempted_skill_ids(db: Session, campaign_id: uuid.UUID) -> set[uuid.UUID]:
    return set(
        db.scalars(
            select(DiagnosticAttempt.skill_id)
            .join(
                DiagnosticSession,
                DiagnosticAttempt.diagnostic_session_id == DiagnosticSession.id,
            )
            .where(DiagnosticSession.campaign_id == campaign_id)
            .distinct()
        ).all()
    )


def active_probe_session(db: Session, campaign_id: uuid.UUID) -> DiagnosticSession | None:
    return db.scalar(
        select(DiagnosticSession)
        .where(
            DiagnosticSession.campaign_id == campaign_id,
            DiagnosticSession.status == "ACTIVE",
        )
        .order_by(DiagnosticSession.started_at.desc())
    )


def next_unprobed_target(db: Session, campaign: DiagnosticCampaign) -> uuid.UUID | None:
    """Next planned anchor not yet launched and not already covered by a
    prerequisite descent during an earlier probe."""
    probed = set(campaign.probed_target_ids or [])
    covered = attempted_skill_ids(db, campaign.id)
    for raw in campaign.target_skill_ids or []:
        skill_id = uuid.UUID(raw)
        if raw not in probed and skill_id not in covered:
            return skill_id
    return None


def overall_recommendation(
    db: Session, campaign: DiagnosticCampaign, verdicts: dict[uuid.UUID, SkillVerdict]
) -> uuid.UUID | None:
    """The deepest meaningful gap: among NOT_READY skills, the one the most
    curriculum skills depend on. Falls back to live placement when every
    probed skill came back ready."""
    not_ready = [sid for sid, v in verdicts.items() if v.verdict == "NOT_READY"]
    if not_ready:
        deps = dependent_counts(db, campaign.curriculum_id) if campaign.curriculum_id else {}
        return max(not_ready, key=lambda sid: deps.get(sid, 0))
    partial = [sid for sid, v in verdicts.items() if v.verdict == "PARTIAL"]
    if partial:
        deps = dependent_counts(db, campaign.curriculum_id) if campaign.curriculum_id else {}
        return max(partial, key=lambda sid: deps.get(sid, 0))
    # Everything probed came back ready — ask the placement engine what's next.
    from app.services.placement import recommend_next_skill

    placement = (
        recommend_next_skill(
            db, student_id=campaign.student_id, curriculum_id=campaign.curriculum_id
        )
        if campaign.curriculum_id
        else None
    )
    return placement.skill.id if placement else None
