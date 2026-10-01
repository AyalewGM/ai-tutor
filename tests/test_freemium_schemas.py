import pytest
from pydantic import ValidationError

from app.schemas import ParentRegisterSchema, PINVerifySchema, StudentCreateSchema


def test_parent_registration_requires_terms_and_coppa_attestation() -> None:
    valid = {
        "email": "parent@example.test",
        "password": "synthetic-password-123",
        "display_name": "Synthetic Parent",
        "parent_pin": "4821",
        "terms_accepted": True,
        "coppa_consent_given": True,
    }
    parsed = ParentRegisterSchema.model_validate(valid)
    assert parsed.coppa_consent_given is True
    assert parsed.terms_accepted is True

    for field in ("terms_accepted", "coppa_consent_given"):
        invalid = dict(valid)
        invalid[field] = False
        with pytest.raises(ValidationError):
            ParentRegisterSchema.model_validate(invalid)


def test_parent_pin_is_exactly_four_digits() -> None:
    assert PINVerifySchema(parent_pin="4821").parent_pin == "4821"
    for value in ("123", "12345", "12a4"):
        with pytest.raises(ValidationError):
            PINVerifySchema(parent_pin=value)


def test_student_profile_requires_non_contact_nickname_and_safe_avatar_id() -> None:
    parsed = StudentCreateSchema(
        display_name="MathStar",
        grade_level="8",
        avatar_id="owl_2",
    )
    assert parsed.display_name == "MathStar"

    with pytest.raises(ValidationError):
        StudentCreateSchema(
            display_name="student@example.com",
            grade_level="8",
            avatar_id="owl_2",
        )
