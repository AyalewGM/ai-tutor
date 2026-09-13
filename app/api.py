import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Attempt, Misconception, Problem, Skill, Student, StudentMisconception, StudentSkill, TutorSession, TutorState
from app.schemas import EvaluationOut, MasteryOut, ProblemOut, RespondIn, RespondOut, SessionCreate, SessionOut, TutorOut
from app.services.evaluation import evaluate_distributive_property
from app.services.mastery import update_mastery
from app.services.state_machine import TutorContext, determine_next_action

router = APIRouter(prefix="/tutor", tags=["tutor"])


def _student_skill(db: Session, student_id: uuid.UUID, skill_id: uuid.UUID) -> StudentSkill:
    row = db.get(StudentSkill, {"student_id": student_id, "skill_id": skill_id})
    if row is None:
        row = StudentSkill(student_id=student_id, skill_id=skill_id)
        db.add(row)
        db.flush()
    return row


def _first_problem(db: Session, skill_id: uuid.UUID, difficulty: int = 1) -> Problem:
    problem = db.scalar(
        select(Problem)
        .where(Problem.primary_skill_id == skill_id, Problem.difficulty >= difficulty)
        .order_by(Problem.difficulty, Problem.id)
    )
    if problem is None:
        raise HTTPException(404, "No problem configured for this skill")
    return problem


def _message_for(action: str, hint_level: int | None, problem: Problem) -> str:
    if action == "EXPLAIN_CONCEPT":
        return "A number outside parentheses multiplies every term inside. Let us work through that idea before trying again."
    if action == "GIVE_HINT":
        if hint_level == 1:
            return "Look at the number immediately outside the parentheses. What must it multiply?"
        if hint_level == 2:
            return "The multiplier must multiply every term inside the parentheses. Which term have you not multiplied yet?"
        if hint_level == 3:
            return "Write the multiplication separately for each term inside the parentheses, then simplify."
        return "Let us model the distribution step explicitly, then you can finish the problem."
    if action == "REMEDIATE":
        return "This same pattern has appeared more than once. Let us return to the distributive property before continuing."
    if action == "START_MASTERY_CHECK":
        return "Now solve the next problem independently without hints so we can check mastery."
    if action == "MARK_MASTERED":
        return "Good work. This independent attempt supports mastery of the skill."
    if action == "INCREASE_DIFFICULTY":
        return "You are solving these independently, so let us increase the difficulty."
    return f"Try the next step on your own: {problem.prompt}"


@router.post("/sessions", response_model=SessionOut)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionOut:
    student = db.get(Student, payload.student_id)
    skill = db.get(Skill, payload.skill_id)
    if student is None or skill is None:
        raise HTTPException(404, "Student or skill not found")

    progress = _student_skill(db, student.id, skill.id)
    problem = _first_problem(db, skill.id)
    session = TutorSession(
        student_id=student.id,
        primary_skill_id=skill.id,
        current_state=TutorState.DIAGNOSE,
        starting_mastery=progress.mastery_score,
        session_goal=f"Diagnose and practice {skill.name}",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionOut(
        session_id=session.id,
        state=session.current_state,
        mastery=MasteryOut(score=progress.mastery_score, confidence=progress.confidence_score),
        problem=ProblemOut(id=problem.id, prompt=problem.prompt, difficulty=problem.difficulty),
        message="Let us start with a quick problem so I can see what you already know.",
    )


@router.post("/sessions/{session_id}/respond", response_model=RespondOut)
def respond(session_id: uuid.UUID, payload: RespondIn, db: Session = Depends(get_db)) -> RespondOut:
    session = db.get(TutorSession, session_id)
    problem = db.get(Problem, payload.problem_id)
    if session is None or session.status != "ACTIVE":
        raise HTTPException(404, "Active tutor session not found")
    if problem is None or problem.primary_skill_id != session.primary_skill_id:
        raise HTTPException(400, "Problem does not belong to the active skill")

    progress = _student_skill(db, session.student_id, session.primary_skill_id)
    evaluation = evaluate_distributive_property(problem.prompt, payload.answer, problem.canonical_answer or "")

    misconception = None
    misconception_count = 0
    if evaluation.misconception_code:
        misconception = db.scalar(select(Misconception).where(Misconception.code == evaluation.misconception_code))
        if misconception:
            sm = db.get(StudentMisconception, {"student_id": session.student_id, "misconception_id": misconception.id})
            if sm is None:
                sm = StudentMisconception(
                    student_id=session.student_id,
                    misconception_id=misconception.id,
                    occurrence_count=1,
                    confidence=Decimal(str(evaluation.misconception_confidence or 0)),
                )
                db.add(sm)
            else:
                sm.occurrence_count += 1
                sm.confidence = Decimal(str(evaluation.misconception_confidence or 0))
            misconception_count = sm.occurrence_count

    previous_attempts = progress.attempt_count
    mastery = update_mastery(
        float(progress.mastery_score),
        previous_attempts,
        evaluation.correct,
        payload.assistance_level,
    )

    progress.attempt_count += 1
    if evaluation.correct:
        progress.correct_count += 1
        if payload.assistance_level == 0:
            progress.independent_attempt_count += 1
            progress.independent_correct_count += 1
        else:
            progress.hinted_correct_count += 1
    elif payload.assistance_level == 0:
        progress.independent_attempt_count += 1
    progress.mastery_score = Decimal(str(mastery.mastery))
    progress.confidence_score = Decimal(str(mastery.confidence))

    consecutive_successes = db.scalar(
        select(func.count(Attempt.id)).where(
            Attempt.session_id == session.id,
            Attempt.is_correct.is_(True),
            Attempt.assistance_level == 0,
        )
    ) or 0

    transition = determine_next_action(
        TutorContext(
            state=session.current_state,
            correct=evaluation.correct,
            assistance_level=payload.assistance_level,
            misconception_count=misconception_count,
            consecutive_independent_successes=int(consecutive_successes),
        )
    )

    attempt_number = (db.scalar(select(func.count(Attempt.id)).where(Attempt.session_id == session.id, Attempt.problem_id == problem.id)) or 0) + 1
    db.add(
        Attempt(
            session_id=session.id,
            student_id=session.student_id,
            problem_id=problem.id,
            student_answer=payload.answer,
            normalized_answer=evaluation.normalized_answer,
            is_correct=evaluation.correct,
            attempt_number=attempt_number,
            assistance_level=payload.assistance_level,
            misconception_id=misconception.id if misconception else None,
            misconception_confidence=Decimal(str(evaluation.misconception_confidence)) if evaluation.misconception_confidence else None,
            evaluation_confidence=Decimal(str(evaluation.confidence)),
            state_at_attempt=session.current_state,
        )
    )
    session.current_state = transition.state
    db.commit()

    return RespondOut(
        session_id=session.id,
        state=transition.state,
        evaluation=EvaluationOut(
            correct=evaluation.correct,
            confidence=evaluation.confidence,
            misconception_code=evaluation.misconception_code,
            misconception_confidence=evaluation.misconception_confidence,
        ),
        tutor=TutorOut(
            action=transition.action,
            hint_level=transition.hint_level,
            message=_message_for(transition.action, transition.hint_level, problem),
        ),
        mastery=MasteryOut(score=progress.mastery_score, confidence=progress.confidence_score),
    )
