import hashlib
import json
import random
import uuid
from collections.abc import Sequence

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.content_models import ProblemContentMetadata
from app.diagnostic_models import DiagnosticAttempt, DiagnosticSession
from app.models import Attempt, Problem, Skill, TutorSession, TutorState
from app.services.problem_generation import generate_problem


def select_next_problem(
    db: Session,
    *,
    skill_id: uuid.UUID,
    current_problem_id: uuid.UUID | None,
    current_difficulty: int,
    state: TutorState,
    correct: bool | None = None,
    student_id: uuid.UUID | None = None,
    session_id: uuid.UUID | None = None,
    offer_extension: bool = False,
    allow_published: bool = True,
) -> Problem | None:
    """Pick the next problem for a skill.

    Difficulty ladders within the authored/generated pool: +1 on success in
    independent/mastery states, -1 on failure in remediation.

    Extension problems are never served through the normal ladder — they are
    excluded unless ``offer_extension`` is true, which is the explicit
    student opt-in for the optional challenge tier.
    """
    resolved_student_id = _resolve_student_id(db, student_id=student_id, session_id=session_id)
    eligibility_column = _eligibility_column(state)
    if not offer_extension and eligibility_column is None:
        return None

    target_difficulty = current_difficulty
    if correct and state in {TutorState.INDEPENDENT_PRACTICE, TutorState.MASTERY_CHECK}:
        target_difficulty = min(10, current_difficulty + 1)
    elif correct is False and state == TutorState.REMEDIATION:
        target_difficulty = max(1, current_difficulty - 1)

    stmt = (
        select(Problem)
        .outerjoin(
            ProblemContentMetadata,
            ProblemContentMetadata.problem_id == Problem.id,
        )
        .where(Problem.primary_skill_id == skill_id)
    )
    if not allow_published:
        stmt = stmt.where(Problem.source_type != "PUBLISHED")
    if offer_extension:
        # Optional stretch tier only: hardest first, no gating semantics.
        stmt = stmt.where(ProblemContentMetadata.extension_eligible.is_(True))
    else:
        # Ordinary learning states fail closed: a stored candidate must carry
        # explicit metadata for the requested mode.  Metadata-free legacy rows
        # are neither learner-visible candidates nor generator authorities.
        stmt = stmt.where(
            ProblemContentMetadata.extension_eligible.is_(False),
            eligibility_column.is_(True),
        )

    if current_problem_id is not None:
        stmt = stmt.where(Problem.id != current_problem_id)

    authorized_problem_types = _authorized_problem_types(
        db,
        skill_id=skill_id,
        state=state,
        extension=offer_extension,
    )
    last_family = _last_attempt_family(db, session_id) if session_id is not None else None
    attempted_ids = _attempted_problem_ids(
        db,
        skill_id=skill_id,
        student_id=resolved_student_id,
        session_id=session_id,
    )
    unseen_stmt = stmt
    if attempted_ids:
        unseen_stmt = unseen_stmt.where(Problem.id.not_in(attempted_ids))
    from app.services.content_publishing import permitted

    mode = eligibility_column.key.removesuffix("_eligible") if eligibility_column is not None else "extension"
    for problem in db.scalars(_ordered(
        unseen_stmt, target_difficulty, avoid_family=last_family,
        hardest_first=offer_extension,
    )):
        if permitted(db, problem, mode):
            return problem

    # Exhausted authored pools generate a deterministic variant.  A stable
    # selection key makes a retry before an Attempt write idempotent, while the
    # attempted-ID fingerprint changes after genuine learner evidence.
    selection_key = _generation_selection_key(
        skill_id=skill_id,
        student_id=resolved_student_id,
        session_id=session_id,
        state=state,
        target_difficulty=target_difficulty,
        current_problem_id=current_problem_id,
        offer_extension=offer_extension,
        attempted_ids=attempted_ids,
    )
    generated = _generated_for_selection_key(db, skill_id=skill_id, selection_key=selection_key)
    if generated is None:
        generated = _generate_authorized_problem(
            db,
            skill_id=skill_id,
            difficulty=(
                min(10, max(current_difficulty + 2, 6))
                if offer_extension
                else target_difficulty
            ),
            avoid_family=last_family,
            student_id=resolved_student_id,
            session_id=session_id,
            selection_key=selection_key,
            extension=offer_extension,
            authorized_problem_types=authorized_problem_types,
        )
        if generated is not None:
            generated.solution = {**(generated.solution or {}), "selection_key": selection_key}
    if generated is not None:
        if not _ensure_generated_metadata(
            db,
            problem=generated,
            skill_id=skill_id,
            state=state,
            extension=offer_extension,
        ):
            return None
        db.flush()
        return generated

    # No explicit authorized unseen item and no authorized generator means the
    # pool is exhausted.  Do not silently recycle prior evidence.
    return None


def _eligibility_column(state: TutorState):
    if state == TutorState.DIAGNOSE:
        return ProblemContentMetadata.diagnostic_eligible
    if state in {
        TutorState.INTRODUCE,
        TutorState.MODEL,
        TutorState.GUIDED_PRACTICE,
        TutorState.REMEDIATION,
    }:
        return ProblemContentMetadata.guided_eligible
    if state in {TutorState.INDEPENDENT_PRACTICE, TutorState.REVIEW}:
        return ProblemContentMetadata.independent_eligible
    if state == TutorState.MASTERY_CHECK:
        return ProblemContentMetadata.mastery_eligible
    return None


def _resolve_student_id(
    db: Session,
    *,
    student_id: uuid.UUID | None,
    session_id: uuid.UUID | None,
) -> uuid.UUID | None:
    if session_id is None:
        return student_id
    session = db.get(TutorSession, session_id)
    if session is None:
        raise ValueError("tutor session does not exist")
    if student_id is not None and student_id != session.student_id:
        raise ValueError("student_id does not match the tutor session")
    return session.student_id


def _attempted_problem_ids(
    db: Session,
    *,
    skill_id: uuid.UUID,
    student_id: uuid.UUID | None,
    session_id: uuid.UUID | None,
) -> tuple[uuid.UUID, ...]:
    stmt = select(Attempt.problem_id).join(Problem, Problem.id == Attempt.problem_id)
    if student_id is not None:
        stmt = stmt.where(
            Attempt.student_id == student_id,
            Problem.primary_skill_id == skill_id,
        )
    elif session_id is not None:
        stmt = stmt.where(
            Attempt.session_id == session_id,
            Problem.primary_skill_id == skill_id,
        )
    else:
        return ()
    attempted = set(db.scalars(stmt).all())
    if student_id is not None:
        diagnostic_stmt = (
            select(DiagnosticAttempt.problem_id)
            .join(
                DiagnosticSession,
                DiagnosticSession.id == DiagnosticAttempt.diagnostic_session_id,
            )
            .join(Problem, Problem.id == DiagnosticAttempt.problem_id)
            .where(
                DiagnosticSession.student_id == student_id,
                Problem.primary_skill_id == skill_id,
            )
        )
        attempted.update(db.scalars(diagnostic_stmt).all())
    return tuple(sorted(attempted, key=str))


def _authorized_problem_types(
    db: Session,
    *,
    skill_id: uuid.UUID,
    state: TutorState,
    extension: bool,
) -> tuple[str, ...]:
    """Problem types explicitly authorized to seed a generated fallback."""
    stmt = (
        select(Problem.problem_type)
        .join(ProblemContentMetadata, ProblemContentMetadata.problem_id == Problem.id)
        .where(Problem.primary_skill_id == skill_id)
    )
    if extension:
        stmt = stmt.where(ProblemContentMetadata.extension_eligible.is_(True))
    else:
        eligibility_column = _eligibility_column(state)
        if eligibility_column is None:
            return ()
        stmt = stmt.where(
            ProblemContentMetadata.extension_eligible.is_(False),
            eligibility_column.is_(True),
        )
    return tuple(sorted(set(db.scalars(stmt).all())))


def _generate_authorized_problem(
    db: Session,
    *,
    skill_id: uuid.UUID,
    difficulty: int,
    avoid_family: str | None,
    student_id: uuid.UUID | None,
    session_id: uuid.UUID | None,
    selection_key: str,
    extension: bool,
    authorized_problem_types: Sequence[str],
) -> Problem | None:
    """Generate only from a type explicitly authorized for this mode."""
    for problem_type in authorized_problem_types:
        type_key = hashlib.sha256(f"{selection_key}:{problem_type}".encode()).hexdigest()
        generated = generate_problem(
            db,
            skill_id=skill_id,
            difficulty=difficulty,
            problem_type=problem_type,
            avoid_family=avoid_family,
            student_id=student_id,
            session_id=session_id,
            rng=random.Random(int(type_key[:16], 16)),
            extension=extension,
        )
        if generated is not None:
            return generated
    return None


def _generation_selection_key(
    *,
    skill_id: uuid.UUID,
    student_id: uuid.UUID | None,
    session_id: uuid.UUID | None,
    state: TutorState,
    target_difficulty: int,
    current_problem_id: uuid.UUID | None,
    offer_extension: bool,
    attempted_ids: Sequence[uuid.UUID],
) -> str:
    payload = {
        "skill_id": str(skill_id),
        "student_id": str(student_id) if student_id else None,
        "session_id": str(session_id) if session_id else None,
        "state": state.value,
        "target_difficulty": target_difficulty,
        "current_problem_id": str(current_problem_id) if current_problem_id else None,
        "offer_extension": offer_extension,
        "attempted_ids": [str(problem_id) for problem_id in attempted_ids],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _generated_for_selection_key(
    db: Session,
    *,
    skill_id: uuid.UUID,
    selection_key: str,
) -> Problem | None:
    return db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == skill_id,
            Problem.source_type == "GENERATED",
            Problem.solution["selection_key"].astext == selection_key,
        )
    )


def _ensure_generated_metadata(
    db: Session,
    *,
    problem: Problem,
    skill_id: uuid.UUID,
    state: TutorState,
    extension: bool,
) -> bool:
    existing = db.scalar(
        select(ProblemContentMetadata).where(ProblemContentMetadata.problem_id == problem.id)
    )
    if existing is not None:
        if extension:
            return existing.extension_eligible is True
        mode_column = _eligibility_column(state)
        return (
            mode_column is not None
            and existing.extension_eligible is False
            and getattr(existing, mode_column.key) is True
        )
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise ValueError(f"Skill {skill_id} not found for generated problem")
    mode_column = _eligibility_column(state)
    mode_name = mode_column.key if mode_column is not None else None
    values = {
        "diagnostic_eligible": False,
        "guided_eligible": False,
        "independent_eligible": False,
        "mastery_eligible": False,
    }
    if not extension:
        if mode_name is None:
            raise ValueError(f"generated problem cannot be authorized for state {state.value}")
        values[mode_name] = True
    db.add(
        ProblemContentMetadata(
            problem_id=problem.id,
            curriculum_id=skill.curriculum_id,
            objective="Generated deterministic variant for the requested learning mode.",
            evaluation_type="EXACT",
            extension_eligible=extension,
            **values,
        )
    )
    return True


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
    return row[0].get("problem_family")


def _ordered(
    stmt,
    target_difficulty: int,
    avoid_family: str | None = None,
    hardest_first: bool = False,
):
    if hardest_first:
        ordering = [Problem.difficulty.desc(), Problem.id]
    else:
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
                (Problem.solution["problem_family"].astext == avoid_family, 1),
                else_=0,
            ),
        )
    return stmt.order_by(*ordering)
