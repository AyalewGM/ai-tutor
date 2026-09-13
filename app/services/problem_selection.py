import uuid

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.models import Problem, TutorState


def select_next_problem(
    db: Session,
    *,
    skill_id: uuid.UUID,
    current_problem_id: uuid.UUID | None,
    current_difficulty: int,
    state: TutorState,
    correct: bool | None = None,
) -> Problem | None:
    target_difficulty = current_difficulty
    if correct and state in {TutorState.INDEPENDENT_PRACTICE, TutorState.MASTERY_CHECK}:
        target_difficulty = min(10, current_difficulty + 1)
    elif correct is False and state == TutorState.REMEDIATION:
        target_difficulty = max(1, current_difficulty - 1)

    stmt = select(Problem).where(Problem.primary_skill_id == skill_id)
    if current_problem_id is not None:
        stmt = stmt.where(Problem.id != current_problem_id)

    stmt = stmt.order_by(
        case((Problem.difficulty == target_difficulty, 0), else_=1),
        abs(Problem.difficulty - target_difficulty),
        Problem.id,
    )
    return db.scalar(stmt.limit(1))
