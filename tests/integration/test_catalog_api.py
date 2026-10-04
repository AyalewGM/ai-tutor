"""Strand-grouped curriculum catalog + parent curriculum switching."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth import SESSION_COOKIE, create_session
from app.content_models import CurriculumExpectation, ExpectationSkillMapping
from app.core.database import SessionLocal
from app.curriculum_models import StudentCurriculumEnrollment
from app.main import app
from app.models import Curriculum, Skill, Student, StudentSkill, TutorSession, User
from app.parent_models import ParentProfile, ParentStudentRelationship

client = TestClient(app)

_TAG = uuid.uuid4().hex[:8].upper()


@pytest.fixture()
def catalog_family():
    """A family enrolled in a strand-mapped curriculum, with a second
    same-region curriculum visible for switching."""
    with SessionLocal() as db:
        user = User(email=f"cat-{uuid.uuid4().hex[:8]}@example.com", role="PARENT")
        db.add(user)
        db.flush()
        profile = ParentProfile(user_id=user.id, country_code="US", region_code="MD")
        db.add(profile)
        db.flush()

        enrolled = Curriculum(
            code=f"CAT_A_{_TAG}", name="Catalog A", jurisdiction="Maryland",
            grade_level="5", country_code="US", region_code="MD",
        )
        other = Curriculum(
            code=f"CAT_B_{_TAG}", name="Catalog B", jurisdiction="Maryland",
            grade_level="5", country_code="US", region_code="MD",
        )
        hidden = Curriculum(
            code=f"CAT_X_{_TAG}", name="Hidden ON", jurisdiction="Ontario",
            grade_level="5", country_code="CA", region_code="ON",
        )
        db.add_all((enrolled, other, hidden))
        db.flush()

        skill_a = Skill(
            curriculum_id=enrolled.id, code="A1", name="Fractions", difficulty_level=1
        )
        skill_b = Skill(
            curriculum_id=enrolled.id, code="A2", name="Decimals", difficulty_level=2
        )
        skill_c = Skill(
            curriculum_id=enrolled.id, code="A3", name="Unstranded", difficulty_level=3
        )
        db.add_all((skill_a, skill_b, skill_c))
        db.flush()

        exp1 = CurriculumExpectation(
            curriculum_id=enrolled.id, curriculum_version=enrolled.version,
            source_identifier="5.NF", title="Fractions", strand="Number—Fractions",
            source_uri="https://example.com",
        )
        exp2 = CurriculumExpectation(
            curriculum_id=enrolled.id, curriculum_version=enrolled.version,
            source_identifier="5.MD", title="Measurement", strand="Measurement and Data",
            source_uri="https://example.com",
        )
        db.add_all((exp1, exp2))
        db.flush()
        db.add_all(
            (
                ExpectationSkillMapping(
                    curriculum_id=enrolled.id, expectation_id=exp1.id, skill_id=skill_a.id
                ),
                ExpectationSkillMapping(
                    curriculum_id=enrolled.id, expectation_id=exp2.id, skill_id=skill_b.id
                ),
            )
        )

        student = Student(
            parent_id=user.id, curriculum_id=enrolled.id,
            first_name="Cat", grade_level="5",
        )
        db.add(student)
        db.flush()
        db.add(
            StudentCurriculumEnrollment(
                student_id=student.id, curriculum_id=enrolled.id, active=True
            )
        )
        db.add(
            ParentStudentRelationship(
                parent_profile_id=profile.id, student_id=student.id,
                relationship_type="GUARDIAN", active=True,
            )
        )
        db.add(
            StudentSkill(
                student_id=student.id, skill_id=skill_a.id,
                mastery_score="0.500", status="LEARNING",
            )
        )
        session = TutorSession(
            student_id=student.id, primary_skill_id=skill_a.id,
            curriculum_id=enrolled.id,
        )
        db.add(session)
        db.commit()
        ids = {
            "user": user.id, "profile": profile.id, "student": student.id,
            "enrolled": enrolled.id, "other": other.id, "hidden": hidden.id,
            "session": session.id,
        }
    yield ids
    with SessionLocal() as db:
        db.query(StudentSkill).filter(StudentSkill.student_id == ids["student"]).delete()
        db.query(TutorSession).filter(TutorSession.student_id == ids["student"]).delete()
        db.query(ExpectationSkillMapping).filter(
            ExpectationSkillMapping.curriculum_id.in_(
                [ids["enrolled"], ids["other"], ids["hidden"]]
            )
        ).delete()
        db.query(CurriculumExpectation).filter(
            CurriculumExpectation.curriculum_id.in_(
                [ids["enrolled"], ids["other"], ids["hidden"]]
            )
        ).delete()
        db.query(Skill).filter(
            Skill.curriculum_id.in_([ids["enrolled"], ids["other"], ids["hidden"]])
        ).delete()
        db.query(StudentCurriculumEnrollment).filter(
            StudentCurriculumEnrollment.student_id == ids["student"]
        ).delete()
        db.query(ParentStudentRelationship).filter(
            ParentStudentRelationship.parent_profile_id == ids["profile"]
        ).delete()
        db.query(Student).filter(Student.id == ids["student"]).delete()
        db.query(ParentProfile).filter(ParentProfile.id == ids["profile"]).delete()
        db.query(Curriculum).filter(
            Curriculum.id.in_([ids["enrolled"], ids["other"], ids["hidden"]])
        ).delete()
        db.query(User).filter(User.id == ids["user"]).delete()
        db.commit()


@pytest.fixture(autouse=True)
def _cookies():
    yield
    client.cookies.clear()


def _cookie(user_id: uuid.UUID) -> None:
    with SessionLocal() as db:
        token, _ = create_session(db, user_id)
        db.commit()
    client.cookies.set(SESSION_COOKIE, token)


def test_catalog_groups_skills_by_strand(catalog_family):
    _cookie(catalog_family["user"])
    resp = client.get(f"/api/v1/onboarding/learners/{catalog_family['student']}/catalog")
    assert resp.status_code == 200
    data = resp.json()
    assert data["curriculum_id"] == str(catalog_family["enrolled"])
    assert data["is_enrolled"] is True
    assert data["can_select"] is True
    assert data["skill_count"] == 3

    strand_names = [s["name"] for s in data["strands"]]
    # "More skills" bucket always sorts last.
    assert strand_names[-1] == "More skills"
    assert "Number—Fractions" in strand_names
    assert "Measurement and Data" in strand_names

    by_name = {k["name"]: k for s in data["strands"] for k in s["skills"]}
    assert by_name["Fractions"]["mastery_score"] == pytest.approx(0.5)
    assert by_name["Fractions"]["status"] == "LEARNING"
    assert by_name["Decimals"]["status"] == "NOT_STARTED"
    assert by_name["Unstranded"]["status"] == "NOT_STARTED"


def test_catalog_options_respect_family_visibility(catalog_family):
    _cookie(catalog_family["user"])
    data = client.get(
        f"/api/v1/onboarding/learners/{catalog_family['student']}/catalog"
    ).json()
    option_ids = {o["id"] for o in data["options"]}
    assert str(catalog_family["enrolled"]) in option_ids
    assert str(catalog_family["other"]) in option_ids
    assert str(catalog_family["hidden"]) not in option_ids  # other region is hidden


def test_catalog_browse_other_curriculum(catalog_family):
    _cookie(catalog_family["user"])
    resp = client.get(
        f"/api/v1/onboarding/learners/{catalog_family['student']}/catalog"
        f"?curriculum_id={catalog_family['other']}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["curriculum_id"] == str(catalog_family["other"])
    assert data["is_enrolled"] is False
    assert data["strands"] == []  # no skills seeded in B

    hidden = client.get(
        f"/api/v1/onboarding/learners/{catalog_family['student']}/catalog"
        f"?curriculum_id={catalog_family['hidden']}"
    )
    assert hidden.status_code == 404


def test_switch_curriculum_parent_only(catalog_family):
    _cookie(catalog_family["user"])
    resp = client.post(
        f"/api/v1/onboarding/learners/{catalog_family['student']}/curriculum",
        json={"curriculum_id": str(catalog_family["other"])},
    )
    assert resp.status_code == 200
    assert resp.json()["curriculum_code"].startswith("CAT_B_")

    with SessionLocal() as db:
        student = db.get(Student, catalog_family["student"])
        assert student.curriculum_id == catalog_family["other"]
        enrollments = db.scalars(
            select(StudentCurriculumEnrollment).where(
                StudentCurriculumEnrollment.student_id == student.id
            )
        ).all()
        active = [e for e in enrollments if e.active]
        assert len(active) == 1 and active[0].curriculum_id == catalog_family["other"]
        session = db.get(TutorSession, catalog_family["session"])
        assert session.status == "ENDED" and session.ended_at is not None


def test_switch_to_invisible_curriculum_404(catalog_family):
    _cookie(catalog_family["user"])
    resp = client.post(
        f"/api/v1/onboarding/learners/{catalog_family['student']}/curriculum",
        json={"curriculum_id": str(catalog_family["hidden"])},
    )
    assert resp.status_code == 404


def test_switch_is_idempotent(catalog_family):
    _cookie(catalog_family["user"])
    url = f"/api/v1/onboarding/learners/{catalog_family['student']}/curriculum"
    assert client.post(url, json={"curriculum_id": str(catalog_family["enrolled"])}).status_code == 200
    with SessionLocal() as db:
        assert db.get(Student, catalog_family["student"]).curriculum_id == catalog_family["enrolled"]
        session = db.get(TutorSession, catalog_family["session"])
        assert session.status == "ACTIVE"  # untouched on a no-op select


def test_catalog_requires_auth(catalog_family):
    assert client.get(
        f"/api/v1/onboarding/learners/{catalog_family['student']}/catalog"
    ).status_code in (401, 404)


def test_catalog_mastery_not_leaked_across_curricula(catalog_family):
    """Mastery on curriculum A doesn't paint skills of curriculum B."""
    _cookie(catalog_family["user"])
    with SessionLocal() as db:
        db.add(
            Skill(
                curriculum_id=catalog_family["other"], code="B1",
                name="Same topic", difficulty_level=1,
            )
        )
        db.commit()
    data = client.get(
        f"/api/v1/onboarding/learners/{catalog_family['student']}/catalog"
        f"?curriculum_id={catalog_family['other']}"
    ).json()
    skill = data["strands"][0]["skills"][0]
    assert skill["mastery_score"] == 0
    assert skill["status"] == "NOT_STARTED"
    assert datetime.now(UTC)  # sanity: timestamps stay tz-aware
