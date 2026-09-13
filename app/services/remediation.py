import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

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
