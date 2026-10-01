import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import TutorState
from app.services.problem_selection import select_next_problem
from app.services.review_schedule import reviews_due


def fetch_spaced_repetition_prompt(
    db: Session, student_id: uuid.UUID, curriculum_id: uuid.UUID
) -> dict[str, Any] | None:
    """Return the next due warm-up using the authoritative review schedule.

    This intentionally delegates scheduling to SkillReviewSchedule instead of
    introducing a second review_count/three-day policy. It is read-only; the
    adaptive session service owns the REVIEW transition and review outcome.
    """
    due = reviews_due(db, student_id=student_id, curriculum_id=curriculum_id)
    if not due:
        return None

    item = due[0]
    problem = select_next_problem(
        db,
        skill_id=item.skill.id,
        current_problem_id=None,
        current_difficulty=item.progress.current_difficulty,
        state=TutorState.REVIEW,
    )
    if problem is None:
        return None

    return {
        "kind": "warm_up_review",
        "duration_minutes": 2,
        "skill_id": str(item.skill.id),
        "skill_name": item.skill.name,
        "problem_id": str(problem.id),
        "question": problem.prompt,
        "due_at": item.schedule.due_at.isoformat(),
        "review_interval_index": item.schedule.interval_index,
    }
