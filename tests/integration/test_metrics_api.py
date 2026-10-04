"""Admin metrics API: active users, sign-ups, activity by region/curriculum."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.auth import SESSION_COOKIE, create_session
from app.core.database import SessionLocal
from app.main import app
from app.models import Attempt, Curriculum, Problem, Skill, Student, TutorSession, User
from app.parent_models import ParentProfile

client = TestClient(app)

_CODE = f"METRICS_{uuid.uuid4().hex[:8].upper()}"


@pytest.fixture()
def metric_family():
    """A family with a region-saved profile, an enrolled curriculum, and one
    recent + one stale (10-day-old) attempt. Cleaned up after the test."""
    with SessionLocal() as db:
        user = User(email=f"m-{uuid.uuid4().hex[:8]}@example.com", role="PARENT")
        db.add(user)
        db.flush()
        db.add(
            ParentProfile(user_id=user.id, country_code="US", region_code="MD")
        )
        curriculum = Curriculum(
            code=_CODE, name="Metrics Test Curriculum", jurisdiction="Maryland",
            country_code="US", region_code="MD",
        )
        db.add(curriculum)
        db.flush()
        skill = Skill(
            curriculum_id=curriculum.id, code="S1", name="Skill", difficulty_level=1
        )
        db.add(skill)
        db.flush()
        problem = Problem(
            primary_skill_id=skill.id, problem_type="NUMERIC", difficulty=1,
            prompt="1+1", canonical_answer="2",
        )
        db.add(problem)
        student = Student(
            parent_id=user.id, first_name="L", grade_level="8",
            curriculum_id=curriculum.id,
        )
        db.add(student)
        db.flush()
        session = TutorSession(
            student_id=student.id, primary_skill_id=skill.id,
            curriculum_id=curriculum.id,
        )
        db.add(session)
        db.flush()
        recent = Attempt(
            session_id=session.id, student_id=student.id, problem_id=problem.id,
            student_answer="2", is_correct=True, created_at=datetime.now(UTC),
        )
        stale = Attempt(
            session_id=session.id, student_id=student.id, problem_id=problem.id,
            student_answer="3", is_correct=False, attempt_number=2,
            created_at=datetime.now(UTC) - timedelta(days=10),
        )
        db.add_all((recent, stale))
        db.commit()
        db.refresh(user)
        db.refresh(student)
        db.refresh(curriculum)
        yield user, student, curriculum
        db2 = SessionLocal()
        db2.query(Attempt).filter(Attempt.student_id == student.id).delete()
        db2.query(TutorSession).filter(TutorSession.student_id == student.id).delete()
        db2.query(Problem).filter(Problem.primary_skill_id == skill.id).delete()
        db2.query(Skill).filter(Skill.id == skill.id).delete()
        db2.query(Student).filter(Student.id == student.id).delete()
        db2.query(ParentProfile).filter(ParentProfile.user_id == user.id).delete()
        db2.query(Curriculum).filter(Curriculum.id == curriculum.id).delete()
        db2.query(User).filter(User.id == user.id).delete()
        db2.commit()
        db2.close()


@pytest.fixture(autouse=True)
def _clear_cookies():
    yield
    client.cookies.clear()


def _staff_cookie() -> None:
    with SessionLocal() as db:
        user = User(email=f"adm-{uuid.uuid4().hex[:8]}@example.com", role="ADMIN")
        db.add(user)
        db.flush()
        token, session = create_session(db, user.id)
        session.mfa_verified_at = datetime.now(UTC)
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)


def test_metrics_requires_staff():
    assert client.get("/api/v1/admin/metrics/overview").status_code == 401
    assert client.get("/api/v1/admin/metrics/by-region").status_code == 401
    assert client.get("/api/v1/admin/metrics/by-curriculum").status_code == 401
    with SessionLocal() as db:
        user = User(email=f"par-{uuid.uuid4().hex[:8]}@example.com", role="PARENT")
        db.add(user)
        db.flush()
        token, _ = create_session(db, user.id)
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get("/api/v1/admin/metrics/overview").status_code == 404


def test_metrics_overview(metric_family):
    _staff_cookie()
    resp = client.get("/api/v1/admin/metrics/overview")
    assert resp.status_code == 200
    data = resp.json()
    for window in ("active_learners", "active_families", "attempts", "tutor_sessions"):
        assert set(data[window]) == {"1d", "7d", "30d"}
    # Recent attempt counts everywhere; the 10-day-old attempt only in 30d.
    assert data["active_learners"]["1d"] >= 1
    assert data["active_learners"]["7d"] >= data["active_learners"]["1d"]
    assert data["active_learners"]["30d"] >= data["active_learners"]["7d"]
    assert data["attempts"]["30d"] >= data["attempts"]["7d"] + 1
    assert data["active_families"]["1d"] >= 1
    assert set(data["signups"]) == {"1d", "7d", "30d", "total"}
    assert data["signups"]["total"] >= data["signups"]["1d"] >= 1
    assert isinstance(data["signups_daily"], list)
    assert data["learners_total"] >= 1


def test_metrics_by_region(metric_family):
    _staff_cookie()
    resp = client.get("/api/v1/admin/metrics/by-region")
    assert resp.status_code == 200
    row = next(
        r for r in resp.json()
        if r["country_code"] == "US" and r["region_code"] == "MD"
    )
    assert row["families"] >= 1
    assert row["active_learners"] >= 1
    assert row["attempts"] >= 1


def test_metrics_by_curriculum(metric_family):
    _, _, curriculum = metric_family
    _staff_cookie()
    resp = client.get("/api/v1/admin/metrics/by-curriculum")
    assert resp.status_code == 200
    row = next(r for r in resp.json() if r["code"] == _CODE)
    assert row["name"] == curriculum.name
    assert row["learners_total"] == 1
    assert row["active_learners"] == 1
    assert row["attempts"] == 2  # recent + 10-day-old attempt both in the 30d window


def test_metrics_conversion(metric_family):
    _staff_cookie()
    from app.admin_models import AdminAuditEvent
    from app.parent_models import ParentProfile as _PP

    email = f"cv-{uuid.uuid4().hex[:8]}@example.com"
    with SessionLocal() as db:
        user = User(email=email, role="PARENT")
        db.add(user)
        db.flush()
        db.add(
            ParentProfile(
                user_id=user.id, subscription_tier="pro",
                subscription_status="trialing",
            )
        )
        db.add(
            AdminAuditEvent(
                actor_user_id=None, actor_label="stripe-webhook",
                action="CUSTOMER_SUBSCRIPTION_UPDATED", target_type="subscription",
                target_id=str(user.id), after_json={"status": "trialing", "tier": "pro"},
            )
        )
        db.commit()
        user_id = user.id

    resp = client.get("/api/v1/admin/metrics/conversion")
    assert resp.status_code == 200
    data = resp.json()
    tiers = {row["tier"]: row["families"] for row in data["plan_breakdown"]}
    assert tiers.get("pro", 0) >= 1
    assert data["paid_families"] >= 1
    assert data["trialing_now"] >= 1
    assert data["families_total"] >= data["paid_families"]
    assert data["funnel"]["trials_started"]["total"] >= 1
    assert data["funnel"]["trials_started"]["30d"] >= 1
    assert "activations" in data["funnel"] and "cancellations" in data["funnel"]

    with SessionLocal() as db:
        db.query(AdminAuditEvent).filter(
            AdminAuditEvent.target_id == str(user_id)
        ).delete()
        db.query(_PP).filter(_PP.user_id == user_id).delete()
        db.flush()
        db.delete(db.get(User, user_id))
        db.commit()
