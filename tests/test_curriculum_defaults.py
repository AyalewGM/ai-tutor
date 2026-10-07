import uuid

from app.core.database import SessionLocal
from app.curriculum_models import CurriculumVersion
from app.models import Curriculum, User
from app.parent_models import ParentProfile
from app.services.curriculum_defaults import resolve_default_curriculum


def _family(db, *, country="US", region="MD"):
    user = User(email=f"default-{uuid.uuid4()}@example.test", role="PARENT")
    db.add(user)
    db.flush()
    parent = ParentProfile(
        user_id=user.id,
        country_code=country,
        region_code=region,
        coppa_consent_given=True,
    )
    db.add(parent)
    db.flush()
    return parent


def _curriculum(db, *, code, grade, lifecycle="IMPLEMENTED", region="MD"):
    curriculum = Curriculum(
        code=code,
        name=code,
        jurisdiction=region,
        grade_level=grade,
        country_code="US",
        region_code=region,
        version="2026",
        active=True,
    )
    db.add(curriculum)
    db.flush()
    db.add(
        CurriculumVersion(
            curriculum_id=curriculum.id,
            version=curriculum.version,
            review_status="PUBLISHED",
            lifecycle_status=lifecycle,
            active=True,
        )
    )
    db.flush()
    return curriculum


def test_unique_region_grade_implemented_curriculum_resolves():
    db = SessionLocal()
    try:
        parent = _family(db)
        expected = _curriculum(db, code="MD_G7", grade="7")
        result = resolve_default_curriculum(db, parent=parent, grade_level="Grade 7")
        assert result.resolved
        assert result.curriculum.id == expected.id
        assert result.reason == "UNIQUE_IMPLEMENTED_MATCH"
    finally:
        db.rollback()
        db.close()


def test_pilot_curriculum_never_becomes_automatic_default():
    db = SessionLocal()
    try:
        parent = _family(db)
        _curriculum(db, code="MD_G7_PILOT", grade="7", lifecycle="PILOT")
        result = resolve_default_curriculum(db, parent=parent, grade_level="7")
        assert not result.resolved
        assert result.reason == "NO_IMPLEMENTED_MATCH"
    finally:
        db.rollback()
        db.close()


def test_multiple_pathways_fail_closed_for_parent_choice():
    db = SessionLocal()
    try:
        parent = _family(db, region="CA")
        first = _curriculum(db, code="CA_ALGEBRA_I", grade="9", region="CA")
        second = _curriculum(db, code="CA_MATHEMATICS_I", grade="9", region="CA")
        result = resolve_default_curriculum(db, parent=parent, grade_level="9")
        assert not result.resolved
        assert result.reason == "AMBIGUOUS_PATHWAY"
        assert {item.id for item in result.candidates} == {first.id, second.id}
    finally:
        db.rollback()
        db.close()


def test_location_and_grade_are_required():
    db = SessionLocal()
    try:
        parent = _family(db)
        assert (
            resolve_default_curriculum(db, parent=parent, grade_level=None).reason
            == "GRADE_REQUIRED"
        )
        parent.region_code = None
        assert (
            resolve_default_curriculum(db, parent=parent, grade_level="7").reason
            == "LOCATION_REQUIRED"
        )
    finally:
        db.rollback()
        db.close()
