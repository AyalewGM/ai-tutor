import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Student
from app.parent_models import ChildLinkClaim
from app.services.parent_dashboard import hash_claim_token


def issue_child_link_claim(
    db: Session,
    *,
    student_id: uuid.UUID,
    lifetime_minutes: int = 30,
) -> str:
    """Create a one-time claim token for a child and return its plaintext once.

    This service is intentionally not exposed as a public parent endpoint. Pilot/admin
    workflows may invoke it from trusted server-side code. Only the SHA-256 hash is
    persisted, and the consumer enforces expiry plus single use.
    """

    if lifetime_minutes < 1 or lifetime_minutes > 24 * 60:
        raise ValueError("Claim lifetime must be between 1 minute and 24 hours")
    if db.get(Student, student_id) is None:
        raise ValueError("Student not found")

    token = secrets.token_urlsafe(32)
    claim = ChildLinkClaim(
        student_id=student_id,
        token_hash=hash_claim_token(token),
        expires_at=datetime.now(UTC) + timedelta(minutes=lifetime_minutes),
    )
    db.add(claim)
    db.flush()
    return token
