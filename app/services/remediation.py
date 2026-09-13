import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import StudentSkill
from app.services.prerequisite_readiness import find_unready_prerequisite


@dataclass(frozen=True)
class RemediationDecision:
    enter_skill_id: uuid.UUID | None = None
    enter_reason: str | None = None
    exit_to_target: bool = False


def decide_entry(
    db: Session,
    student_id: uuid.UUID,
    target_skill_id: uuid.UUID,
    requested: bool,
) -> RemediationDecision:
    if not requested:
        return RemediationDecision()
    prerequisite = find_unready_prerequisite(
        db,
        student_id=student_id,
        target_skill_id=target_skill_id,
    )
    return RemediationDecision(
        enter_skill_id=prerequisite.prerequisite_skill_id,
        enter_reason=prerequisite.reason,
    )


def remediation_ready(
    progress: StudentSkill,
    *,
    mastery_threshold: Decimal = Decimal("0.700"),
    confidence_threshold: Decimal = Decimal("0.350"),
    independent_successes_required: int = 2,
) -> bool:
    return (
        progress.mastery_score >= mastery_threshold
        and progress.confidence_score >= confidence_threshold
        and progress.independent_correct_count >= independent_successes_required
    )
