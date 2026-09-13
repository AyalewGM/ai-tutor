from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Student
from app.parent_models import ChildLinkClaim
from app.services.child_link_claims import issue_child_link_claim
from app.services.parent_dashboard import hash_claim_token


def test_issue_child_link_claim_persists_only_hash() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        assert curriculum is not None
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Claim Service Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()

        token = issue_child_link_claim(db, student_id=student.id)
        db.commit()

        claim = db.scalar(
            select(ChildLinkClaim).where(ChildLinkClaim.student_id == student.id)
        )
        assert claim is not None
        assert len(token) >= 32
        assert claim.token_hash == hash_claim_token(token)
        assert token != claim.token_hash
        assert claim.consumed_at is None
