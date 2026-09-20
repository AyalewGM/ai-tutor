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
        last_family = _last_attempt_family(db, session_id)
        seen = (
            select(Attempt.problem_id)
            .where(Attempt.session_id == session_id)
            .scalar_subquery()
        )
        problem = db.scalar(
            _ordered(
                stmt.where(Problem.id.not_in(seen)),
                target_difficulty,
                avoid_family=last_family,
            ).limit(1)
        )
        if problem is not None:
            return problem
        generated = generate_problem(
            db,
            skill_id=skill_id,
            difficulty=target_difficulty,
            avoid_family=last_family,
        )
        if generated is not None:
            return generated
    return db.scalar(_ordered(stmt, target_difficulty).limit(1))


def _last_attempt_family(db: Session, session_id: uuid.UUID) -> str | None:
    """Family of the most recently attempted problem in the session, if the
    problem carries generator family metadata."""
    row = db.execute(
        select(Problem.solution)
        .join(Attempt, Attempt.problem_id == Problem.id)
        .where(Attempt.session_id == session_id)
        .order_by(Attempt.created_at.desc())
        .limit(1)
    ).first()
    if row is None or not isinstance(row[0], dict):
        return None
    return row[0].get("family")


def _ordered(stmt, target_difficulty: int, avoid_family: str | None = None):
    ordering = [
        case((Problem.difficulty == target_difficulty, 0), else_=1),
        func.abs(Problem.difficulty - target_difficulty),
        Problem.id,
    ]
    if avoid_family is not None:
        # Prefer a different problem family than the one just served; family is
        # stored in solution metadata for generated problems (NULL → preferred).
        ordering.insert(
            0,
            case(
                (Problem.solution["family"].astext == avoid_family, 1),
                else_=0,
            ),
        )
    return stmt.order_by(*ordering)
