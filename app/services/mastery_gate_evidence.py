from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Attempt, Problem


@dataclass(frozen=True)
class MasteryGateEvidence:
    independent_correct_count: int
    strong_help_seen: bool
    independent_successes_after_strong_help: int


def load_mastery_gate_evidence(
    db: Session,
    *,
    student_id,
    skill_id,
) -> MasteryGateEvidence:
    """Derive mastery-gate evidence from persisted attempts only.

    Independent evidence is counted by distinct problem so repeatedly answering the
    same item cannot manufacture mastery eligibility. Strong help is represented by
    effective assistance level >= 2, which already incorporates persisted L3/L4 hint
    exposure in the response pipeline. Recovery after strong help must occur on a
    different problem than the latest strongly-assisted attempt.
    """
    attempts = list(
        db.scalars(
            select(Attempt)
            .join(Problem, Problem.id == Attempt.problem_id)
            .where(
                Attempt.student_id == student_id,
                Problem.primary_skill_id == skill_id,
            )
            .order_by(Attempt.created_at.asc(), Attempt.id.asc())
        )
    )

    independent_problem_ids = {
        attempt.problem_id
        for attempt in attempts
        if attempt.is_correct is True and attempt.assistance_level == 0
    }

    latest_strong_help_index = None
    for index, attempt in enumerate(attempts):
        if attempt.assistance_level >= 2:
            latest_strong_help_index = index

    if latest_strong_help_index is None:
        return MasteryGateEvidence(
            independent_correct_count=len(independent_problem_ids),
            strong_help_seen=False,
            independent_successes_after_strong_help=0,
        )

    strong_help_problem_id = attempts[latest_strong_help_index].problem_id
    recovered_problem_ids = {
        attempt.problem_id
        for attempt in attempts[latest_strong_help_index + 1 :]
        if (
            attempt.is_correct is True
            and attempt.assistance_level == 0
            and attempt.problem_id != strong_help_problem_id
        )
    }

    return MasteryGateEvidence(
        independent_correct_count=len(independent_problem_ids),
        strong_help_seen=True,
        independent_successes_after_strong_help=len(recovered_problem_ids),
    )
