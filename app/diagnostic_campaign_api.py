import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.diagnostic_api import (
    _next_problem,
    _problem_out,
    _publish_diagnostic_event,
    run_diagnostic_response,
)
from app.diagnostic_models import DiagnosticCampaign, DiagnosticSession
from app.diagnostic_schemas import (
    CampaignOut,
    CampaignReportOut,
    CampaignSkillRef,
    CampaignSkillResultOut,
    CampaignStartIn,
    CampaignStrandOut,
    DiagnosticRespondIn,
)
from app.identity import CurrentLearningAccess, require_learning_owns_student
from app.models import Problem, Skill, Student
from app.services.curriculum_scope import (
    CurriculumScope,
    CurriculumScopeError,
    resolve_student_curriculum_scope,
)
from app.services.diagnostic_campaign import (
    FALLBACK_STRAND,
    QUESTION_BUDGET,
    active_probe_session,
    campaign_verdicts,
    dependent_counts,
    next_unprobed_target,
    overall_recommendation,
    plan_targets,
    strand_index,
)

router = APIRouter(prefix="/diagnostics/campaigns", tags=["diagnostics"])
DbSession = Annotated[Session, Depends(get_db)]

PER_TARGET_QUESTIONS = 8


def _skill_ref(skill: Skill | None) -> CampaignSkillRef | None:
    if skill is None:
        return None
    return CampaignSkillRef(id=skill.id, code=skill.code, name=skill.name)


def _launch_target_probe(
    db: Session,
    *,
    campaign: DiagnosticCampaign,
    student_id: uuid.UUID,
    scope: CurriculumScope,
    target_skill_id: uuid.UUID,
) -> tuple[DiagnosticSession, Problem] | None:
    """Open a per-skill probe session under the campaign. Returns None when
    the target unexpectedly has no diagnostic-servable problem."""
    problem = _next_problem(db, student_id, target_skill_id)
    if problem is None:
        return None
    remaining = campaign.max_questions - campaign.question_count
    session = DiagnosticSession(
        student_id=student_id,
        campaign_id=campaign.id,
        target_skill_id=target_skill_id,
        current_skill_id=target_skill_id,
        curriculum_id=scope.curriculum_id,
        curriculum_enrollment_id=scope.enrollment_id,
        status="ACTIVE",
        max_questions=max(1, min(PER_TARGET_QUESTIONS, remaining)),
    )
    db.add(session)
    db.flush()
    campaign.probed_target_ids = [*(campaign.probed_target_ids or []), str(target_skill_id)]
    return session, problem


def _campaign_scope(db: Session, campaign: DiagnosticCampaign) -> CurriculumScope:
    if campaign.curriculum_id is not None:
        return CurriculumScope(
            curriculum_id=campaign.curriculum_id,
            enrollment_id=campaign.curriculum_enrollment_id,
            local_authority_id=None,
        )
    student = db.get(Student, campaign.student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    try:
        return resolve_student_curriculum_scope(db, student)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc


def _finish_campaign(db: Session, campaign: DiagnosticCampaign) -> None:
    campaign.status = "COMPLETED"
    campaign.completed_at = datetime.now(UTC)
    verdicts = campaign_verdicts(db, campaign.id)
    campaign.recommended_skill_id = overall_recommendation(db, campaign, verdicts)


def _campaign_out(
    db: Session,
    campaign: DiagnosticCampaign,
    *,
    problem: Problem | None,
    message: str,
    last_answer_correct: bool | None = None,
) -> CampaignOut:
    current_skill = None
    session = active_probe_session(db, campaign.id)
    if session is not None:
        current_skill = _skill_ref(db.get(Skill, session.current_skill_id))
    return CampaignOut(
        campaign_id=campaign.id,
        status=campaign.status,
        question_count=campaign.question_count,
        max_questions=campaign.max_questions,
        targets_planned=len(campaign.target_skill_ids or []),
        targets_probed=len(campaign.probed_target_ids or []),
        problem=_problem_out(problem),
        current_skill=current_skill,
        last_answer_correct=last_answer_correct,
        message=message,
    )


@router.post("", response_model=CampaignOut)
def start_campaign(
    payload: CampaignStartIn, access: CurrentLearningAccess, db: DbSession
) -> CampaignOut:
    student = require_learning_owns_student(access, db.get(Student, payload.student_id))
    try:
        scope = resolve_student_curriculum_scope(db, student)
    except CurriculumScopeError as exc:
        raise HTTPException(409, str(exc)) from exc
    if scope.curriculum_id is None:
        raise HTTPException(409, "Learner curriculum is unavailable")

    # Idempotent: an in-flight campaign resumes instead of stacking.
    existing = db.scalar(
        select(DiagnosticCampaign).where(
            DiagnosticCampaign.student_id == student.id,
            DiagnosticCampaign.status == "ACTIVE",
        )
    )
    if existing is not None:
        session = active_probe_session(db, existing.id)
        problem = (
            _next_problem(db, student.id, session.current_skill_id) if session else None
        )
        return _campaign_out(
            db,
            existing,
            problem=problem,
            message="Resuming your knowledge check.",
        )

    targets = plan_targets(db, student_id=student.id, curriculum_id=scope.curriculum_id)
    if not targets:
        raise HTTPException(409, "No diagnostic-ready skills in the enrolled curriculum")

    campaign = DiagnosticCampaign(
        student_id=student.id,
        curriculum_id=scope.curriculum_id,
        curriculum_enrollment_id=scope.enrollment_id,
        status="ACTIVE",
        target_skill_ids=[str(skill_id) for skill_id in targets],
        max_questions=QUESTION_BUDGET,
    )
    db.add(campaign)
    db.flush()

    problem = None
    launched_session = None
    for target in targets:
        launched = _launch_target_probe(
            db, campaign=campaign, student_id=student.id, scope=scope, target_skill_id=target
        )
        if launched is not None:
            launched_session, problem = launched
            break
    if problem is None or launched_session is None:
        raise HTTPException(409, "No diagnostic-ready skills in the enrolled curriculum")

    db.commit()
    _publish_diagnostic_event(
        event_type="diagnostic.started", session=launched_session, skill_id=launched_session.target_skill_id
    )
    return _campaign_out(
        db,
        campaign,
        problem=problem,
        message="Answer on your own — this maps what you already know across the course.",
    )


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: uuid.UUID, access: CurrentLearningAccess, db: DbSession
) -> CampaignOut:
    campaign = db.get(DiagnosticCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(404, "Diagnostic campaign not found")
    require_learning_owns_student(access, db.get(Student, campaign.student_id))

    problem = None
    message = "Your knowledge map is ready."
    if campaign.status == "ACTIVE":
        session = active_probe_session(db, campaign.id)
        if session is not None:
            problem = _next_problem(db, campaign.student_id, session.current_skill_id)
        message = "Answer on your own — this maps what you already know."
    return _campaign_out(db, campaign, problem=problem, message=message)


@router.post("/{campaign_id}/respond", response_model=CampaignOut)
def respond_to_campaign(
    campaign_id: uuid.UUID,
    payload: DiagnosticRespondIn,
    access: CurrentLearningAccess,
    db: DbSession,
) -> CampaignOut:
    campaign = db.get(DiagnosticCampaign, campaign_id)
    if campaign is None or campaign.status != "ACTIVE":
        raise HTTPException(404, "Active diagnostic campaign not found")
    require_learning_owns_student(access, db.get(Student, campaign.student_id))

    session = active_probe_session(db, campaign.id)
    if session is None:
        raise HTTPException(409, "Campaign has no active probe session")

    turn = run_diagnostic_response(
        db, session=session, problem_id=payload.problem_id, answer=payload.answer
    )
    campaign.question_count += 1

    scope = _campaign_scope(db, campaign)
    next_problem = turn.next_problem
    message = turn.message
    new_probe_session = None
    if turn.completed:
        if campaign.question_count >= campaign.max_questions:
            _finish_campaign(db, campaign)
            next_problem = None
            message = "Knowledge check complete — your map is ready."
        else:
            next_problem = None
            next_target = next_unprobed_target(db, campaign)
            while next_target is not None:
                launched = _launch_target_probe(
                    db,
                    campaign=campaign,
                    student_id=campaign.student_id,
                    scope=scope,
                    target_skill_id=next_target,
                )
                if launched is not None:
                    new_probe_session, next_problem = launched
                    break
                # Launch failed (no servable problem) — mark the target probed
                # so the planner skips it, then try the next candidate.
                campaign.probed_target_ids = [
                    *(campaign.probed_target_ids or []), str(next_target)
                ]
                next_target = next_unprobed_target(db, campaign)
            if next_problem is None:
                _finish_campaign(db, campaign)
                message = "Knowledge check complete — your map is ready."
            else:
                message = "That topic is mapped. Moving to the next area."

    db.commit()
    if turn.completed:
        _publish_diagnostic_event(
            event_type="diagnostic.completed",
            session=session,
            skill_id=session.recommended_skill_id or session.current_skill_id,
            payload={"question_count": session.question_count},
        )
    if new_probe_session is not None:
        _publish_diagnostic_event(
            event_type="diagnostic.started",
            session=new_probe_session,
            skill_id=new_probe_session.target_skill_id,
        )
    return _campaign_out(
        db,
        campaign,
        problem=next_problem,
        message=message,
        last_answer_correct=turn.correct,
    )


@router.get("/{campaign_id}/report", response_model=CampaignReportOut)
def campaign_report(
    campaign_id: uuid.UUID, access: CurrentLearningAccess, db: DbSession
) -> CampaignReportOut:
    campaign = db.get(DiagnosticCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(404, "Diagnostic campaign not found")
    require_learning_owns_student(access, db.get(Student, campaign.student_id))
    if campaign.curriculum_id is None:
        raise HTTPException(409, "Learner curriculum is unavailable")

    verdicts = campaign_verdicts(db, campaign.id)
    strands = strand_index(db, campaign.curriculum_id)
    deps = dependent_counts(db, campaign.curriculum_id)
    skills = {
        row.id: row
        for row in db.scalars(
            select(Skill).where(Skill.curriculum_id == campaign.curriculum_id)
        ).all()
    }

    skill_results: list[CampaignSkillResultOut] = []
    strand_rows: dict[str, dict[str, object]] = {}
    for skill_id, verdict in verdicts.items():
        skill = skills.get(skill_id)
        if skill is None:
            continue
        strand = strands.get(skill_id, FALLBACK_STRAND)
        skill_results.append(
            CampaignSkillResultOut(
                skill=_skill_ref(skill),
                strand=strand,
                verdict=verdict.verdict,
                correct_count=verdict.correct_count,
                incorrect_count=verdict.incorrect_count,
            )
        )
        row = strand_rows.setdefault(
            strand, {"probed": 0, "ready": 0, "gaps": []}
        )
        row["probed"] += 1
        if verdict.verdict == "READY":
            row["ready"] += 1
        elif verdict.verdict == "NOT_READY":
            row["gaps"].append(skill_id)

    skill_results.sort(key=lambda row: (row.strand, row.skill.code))
    strand_totals: dict[str, int] = {}
    for skill in skills.values():
        strand = strands.get(skill.id, FALLBACK_STRAND)
        strand_totals[strand] = strand_totals.get(strand, 0) + 1

    strand_outs: list[CampaignStrandOut] = []
    for name in sorted(strand_rows):
        row = strand_rows[name]
        probed, ready = row["probed"], row["ready"]
        gaps = row["gaps"]
        deepest_gap = max(gaps, key=lambda sid: deps.get(sid, 0)) if gaps else None
        readiness = (
            "STRONG"
            if probed == ready
            else "DEVELOPING"
            if ready > 0
            else "EMERGING"
        )
        strand_outs.append(
            CampaignStrandOut(
                name=name,
                readiness=readiness,
                skills_probed=probed,
                skills_ready=ready,
                skills_total=strand_totals.get(name, probed),
                deepest_gap=_skill_ref(
                    db.get(Skill, deepest_gap) if deepest_gap else None
                ),
            )
        )

    return CampaignReportOut(
        campaign_id=campaign.id,
        status=campaign.status,
        question_count=campaign.question_count,
        recommended=_skill_ref(
            db.get(Skill, campaign.recommended_skill_id)
            if campaign.recommended_skill_id
            else None
        ),
        strands=strand_outs,
        skills=skill_results,
    )
