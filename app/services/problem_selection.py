import uuid

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Attempt, Problem, TutorState
from app.services.problem_generation import generate_problem


def select_next_problem(
    db: Session,
    *,
    skill_id: uuid.UUID,
    current_problem_id: uuid.UUID | None,
    current_difficulty: int,
    state: TutorState,
    correct: bool | None = None,
    session_id: uuid.UUID | None = None,
) -> Problem | None:
    target_difficulty = current_difficulty
    if correct and state in {TutorState.INDEPENDENT_PRACTICE, TutorState.MASTERY_CHECK}:
        target_difficulty = min(10, current_difficulty + 1)
    elif correct is False and state == TutorState.REMEDIATION:
        target_difficulty = max(1, current_difficulty - 1)

    stmt = select(Problem).where(Problem.primary_skill_id == skill_id)
    if current_problem_id is not None:
        stmt = stmt.where(Problem.id != current_problem_id)

    if session_id is not None:
        seen = (
            select(Attempt.problem_id)
            .where(Attempt.session_id == session_id)
            .scalar_subquery()
        )
        problem = db.scalar(
            _ordered(stmt.where(Problem.id.not_in(seen)), target_difficulty).limit(1)
        )
        if problem is not None:
            return problem
        generated = generate_problem(db, skill_id=skill_id, difficulty=target_difficulty)
        if generated is not None:
            return generated
    return db.scalar(_ordered(stmt, target_difficulty).limit(1))


def _ordered(stmt, target_difficulty: int):
    return stmt.order_by(
        case((Problem.difficulty == target_difficulty, 0), else_=1),
        func.abs(Problem.difficulty - target_difficulty),
        Problem.id,
    )
