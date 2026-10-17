from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_models import ProblemContentMetadata
from app.models import Problem, TutorSession, TutorState, TutorTurn

EXTENSION_OFFER_ACTION = "OFFER_EXTENSION"


class ExtensionOfferError(ValueError):
    """Raised when an extension-eligible response lacks a server-owned offer."""


def record_extension_offer(
    db: Session, *, session: TutorSession, problem: Problem
) -> None:
    """Persist the server-authoritative session/problem extension offer."""

    active_skill_id = session.active_skill_id or session.primary_skill_id
    if problem.primary_skill_id != active_skill_id:
        raise ExtensionOfferError("Extension problem does not match the active skill")

    eligible = db.scalar(
        select(ProblemContentMetadata.problem_id).where(
            ProblemContentMetadata.problem_id == problem.id,
            ProblemContentMetadata.extension_eligible.is_(True),
        )
    )
    if eligible is None:
        raise ExtensionOfferError("Problem is not eligible for extension mode")

    db.add(
        TutorTurn(
            session_id=session.id,
            role="TUTOR",
            message="Optional extension problem offered.",
            state=TutorState.EXTENSION,
            pedagogical_action=EXTENSION_OFFER_ACTION,
            problem_id=problem.id,
            metadata_json={
                "student_id": str(session.student_id),
                "skill_id": str(active_skill_id),
                "extension_eligible": True,
            },
        )
    )


def extension_response_is_authorized(
    db: Session, *, session: TutorSession, problem: Problem
) -> bool:
    """Classify extension responses only from a matching server-owned offer.

    Non-extension problems return False. An extension-eligible problem that
    was not explicitly offered to this authenticated session fails closed.
    """

    eligible = db.scalar(
        select(ProblemContentMetadata.problem_id).where(
            ProblemContentMetadata.problem_id == problem.id,
            ProblemContentMetadata.extension_eligible.is_(True),
        )
    )
    if eligible is None:
        return False

    active_skill_id = session.active_skill_id or session.primary_skill_id
    if problem.primary_skill_id != active_skill_id:
        raise ExtensionOfferError("Extension problem does not match the active skill")

    offered = db.scalar(
        select(TutorTurn.id).where(
            TutorTurn.session_id == session.id,
            TutorTurn.problem_id == problem.id,
            TutorTurn.state == TutorState.EXTENSION,
            TutorTurn.pedagogical_action == EXTENSION_OFFER_ACTION,
        )
    )
    if offered is None:
        raise ExtensionOfferError(
            "Extension problem was not offered to this learning session"
        )
    return True
