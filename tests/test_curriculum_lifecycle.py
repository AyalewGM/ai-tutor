from app.curriculum_lifecycle import (
    CurriculumLifecycleError,
    is_learner_selectable,
    set_curriculum_lifecycle,
)
from app.curriculum_models import CurriculumVersion


def _version() -> CurriculumVersion:
    return CurriculumVersion(
        curriculum_id=None,
        version="test",
        review_status="PUBLISHED",
        lifecycle_status="DRAFT",
        active=False,
    )


def test_human_review_does_not_make_draft_curriculum_implemented():
    version = _version()
    assert version.review_status == "PUBLISHED"
    assert not is_learner_selectable(version)


def test_pilot_is_not_learner_selectable_by_default():
    version = _version()
    set_curriculum_lifecycle(version, "PILOT")
    assert version.lifecycle_status == "PILOT"
    assert not version.active
    assert not is_learner_selectable(version)


def test_only_implemented_version_is_selectable():
    version = _version()
    set_curriculum_lifecycle(version, "IMPLEMENTED")
    assert version.active
    assert is_learner_selectable(version)


def test_retired_version_is_not_selectable():
    version = _version()
    set_curriculum_lifecycle(version, "RETIRED")
    assert not version.active
    assert not is_learner_selectable(version)


def test_unknown_lifecycle_fails_closed():
    version = _version()
    try:
        set_curriculum_lifecycle(version, "CURRENTISH")
    except CurriculumLifecycleError:
        pass
    else:
        raise AssertionError("Unknown lifecycle status must fail closed")
