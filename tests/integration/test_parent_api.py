from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.identity import current_user
from app.main import app
from app.models import Curriculum, Skill, SkillStatus, Student, StudentSkill, User
from app.parent_models import (
    ChildLinkClaim,
    ParentStudentRelationship,
    ParentStudentRelationshipEvent,
)
from app.services.parent_dashboard import hash_claim_token

client = TestClient(app)


def _override_user(user: User) -> None:
    app.dependency_overrides[current_user] = lambda: user


def _clear_override() -> None:
    app.dependency_overrides.pop(current_user, None)


def test_parent_link_dashboard_isolation_and_non_destructive_unlink() -> None:
    token = "integration-parent-claim-token-0001"
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        assert curriculum is not None
        skill = db.scalar(select(Skill).where(Skill.curriculum_id == curriculum.id).limit(1))
        assert skill is not None

        parent_user = User(
            email="parent-f005@example.test",
            display_name="Parent F005",
            role="PARENT",
        )
        other_parent_user = User(
            email="other-parent-f005@example.test",
            display_name="Other Parent F005",
            role="PARENT",
        )
        child = Student(
            curriculum_id=curriculum.id,
            first_name="F005 Child",
            grade_level="8",
            school_system="MCPS",
        )
        db.add_all([parent_user, other_parent_user, child])
        db.flush()
        db.add(
            StudentSkill(
                student_id=child.id,
                skill_id=skill.id,
                attempt_count=2,
                independent_attempt_count=1,
                independent_correct_count=1,
                hinted_correct_count=1,
                status=SkillStatus.PRACTICING,
            )
        )
        claim = ChildLinkClaim(
            student_id=child.id,
            token_hash=hash_claim_token(token),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        db.add(claim)
        db.commit()
        db.refresh(parent_user)
        db.refresh(other_parent_user)
        db.refresh(child)
        parent_user_id = parent_user.id
        other_parent_user_id = other_parent_user.id
        child_id = child.id
        curriculum_name = curriculum.name
        skill_code = skill.code

    try:
        with SessionLocal() as db:
            parent_user = db.get(User, parent_user_id)
            assert parent_user is not None
            _override_user(parent_user)

            profile = client.post("/api/v1/parents/profile")
            assert profile.status_code == 200
            assert profile.json()["email"] == "parent-f005@example.test"

            linked = client.post(
                "/api/v1/parents/children/link",
                json={"claim_token": token},
            )
            assert linked.status_code == 200
            assert linked.json()["child"]["id"] == str(child_id)
            assert linked.json()["child"]["curriculum_name"] == curriculum_name

            replay = client.post(
                "/api/v1/parents/children/link",
                json={"claim_token": token},
            )
            assert replay.status_code == 400

            children = client.get("/api/v1/parents/children")
            assert children.status_code == 200
            assert [row["id"] for row in children.json()] == [str(child_id)]

            dashboard = client.get(f"/api/v1/parents/children/{child_id}/dashboard")
            assert dashboard.status_code == 200
            payload = dashboard.json()
            assert payload["child"]["id"] == str(child_id)
            projected = next(row for row in payload["skills"] if row["skill_code"] == skill_code)
            assert projected["evidence_status"] == "EVIDENCE_AVAILABLE"
            assert projected["learning_state"] == "INDEPENDENT_PROGRESS"
            assert projected["assistance_signal"] == "MIXED_INDEPENDENT_AND_ASSISTED"
            assert projected["reason_code"] == "INDEPENDENT_SUCCESS_OBSERVED"

        with SessionLocal() as db:
            other_parent_user = db.get(User, other_parent_user_id)
            assert other_parent_user is not None
            _override_user(other_parent_user)
            assert client.post("/api/v1/parents/profile").status_code == 200
            denied = client.get(f"/api/v1/parents/children/{child_id}/dashboard")
            assert denied.status_code == 403

        with SessionLocal() as db:
            parent_user = db.get(User, parent_user_id)
            assert parent_user is not None
            _override_user(parent_user)
            removed = client.delete(f"/api/v1/parents/children/{child_id}")
            assert removed.status_code == 204

        with SessionLocal() as db:
            assert db.get(Student, child_id) is not None
            relationship = db.scalar(
                select(ParentStudentRelationship).where(
                    ParentStudentRelationship.student_id == child_id,
                    ParentStudentRelationship.active.is_(False),
                )
            )
            assert relationship is not None
            actions = db.scalars(
                select(ParentStudentRelationshipEvent.action)
                .where(ParentStudentRelationshipEvent.relationship_id == relationship.id)
                .order_by(ParentStudentRelationshipEvent.created_at)
            ).all()
            assert actions == ["LINKED", "UNLINKED"]
    finally:
        _clear_override()


def test_parent_routes_fail_closed_without_authenticated_identity() -> None:
    _clear_override()
    response = client.get("/api/v1/parents/children")
    assert response.status_code == 401
