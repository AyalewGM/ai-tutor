from sqlalchemy.orm import Session

from app.models import StudentSkill, TutorSession, TutorState
from app.services.remediation import decide_entry, remediation_ready
from app.services.state_machine import Transition


def apply_focus_policy(
    db: Session,
    *,
    session: TutorSession,
    progress: StudentSkill,
    transition: Transition,
    correct: bool,
    assistance_level: int,
) -> Transition:
    active_skill_id = session.active_skill_id or session.primary_skill_id
    in_remediation = active_skill_id != session.primary_skill_id

    if in_remediation:
        if remediation_ready(progress) and correct and assistance_level == 0:
            session.active_skill_id = session.primary_skill_id
            session.remediation_reason = None
            return Transition(TutorState.GUIDED_PRACTICE, "RESUME_TARGET")
        return Transition(
            TutorState.REMEDIATION,
            "ASK_RETRY" if correct else "GIVE_HINT",
            None if correct else 1,
        )

    if transition.action != "REMEDIATE":
        return transition

    entry = decide_entry(
        db,
        session.student_id,
        session.primary_skill_id,
        requested=True,
    )
    if entry.enter_skill_id is None:
        return transition

    session.active_skill_id = entry.enter_skill_id
    session.remediation_reason = entry.enter_reason
    return Transition(TutorState.REMEDIATION, "REMEDIATE", hint_level=2)
