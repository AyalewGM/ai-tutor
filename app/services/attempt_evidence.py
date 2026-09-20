from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Misconception, Skill, StudentMisconception, StudentSkill
from app.services.evaluation import EvaluationResult, evaluate_problem
from app.services.mastery import update_mastery


@dataclass(frozen=True)
class EvidenceResult:
    evaluation: EvaluationResult
    misconception: Misconception | None
    misconception_count: int
    previous_score: Decimal
    previous_confidence: Decimal


def record_evidence(
    db: Session,
    *,
    progress: StudentSkill,
    prompt: str,
    answer: str,
    canonical_answer: str,
    assistance_level: int,
) -> EvidenceResult:
    previous_score = progress.mastery_score
    previous_confidence = progress.confidence_score
    evaluation = evaluate_problem(prompt, answer, canonical_answer)

    misconception = None
    misconception_count = 0
    if evaluation.misconception_code:
        current_skill = db.get(Skill, progress.skill_id)
        if current_skill is not None:
            misconception = db.scalar(
                select(Misconception)
                .join(Skill, Skill.id == Misconception.skill_id)
                .where(
                    Skill.curriculum_id == current_skill.curriculum_id,
                    Misconception.code == evaluation.misconception_code,
                )
            )
        if misconception:
            key = {
                "student_id": progress.student_id,
                "misconception_id": misconception.id,
            }
            row = db.get(StudentMisconception, key)
            if row is None:
                row = StudentMisconception(
                    student_id=progress.student_id,
                    misconception_id=misconception.id,
                    occurrence_count=1,
                    confidence=Decimal(str(evaluation.misconception_confidence or 0)),
                )
                db.add(row)
            else:
                row.occurrence_count += 1
                row.confidence = Decimal(str(evaluation.misconception_confidence or 0))
            misconception_count = row.occurrence_count

    mastery = update_mastery(
        float(progress.mastery_score),
        progress.attempt_count,
        evaluation.correct,
        assistance_level,
    )
    progress.attempt_count += 1
    if evaluation.correct:
        progress.correct_count += 1
        if assistance_level == 0:
            progress.independent_attempt_count += 1
            progress.independent_correct_count += 1
            progress.last_independent_evidence_at = datetime.now(UTC)
        else:
            progress.hinted_correct_count += 1
    elif assistance_level == 0:
        progress.independent_attempt_count += 1
    progress.mastery_score = Decimal(str(mastery.mastery))
    progress.confidence_score = Decimal(str(mastery.confidence))

    return EvidenceResult(
        evaluation=evaluation,
        misconception=misconception,
        misconception_count=misconception_count,
        previous_score=previous_score,
        previous_confidence=previous_confidence,
    )
