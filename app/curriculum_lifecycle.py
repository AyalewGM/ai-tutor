"""Lifecycle rules for authoritative curriculum versions."""

from app.curriculum_models import CurriculumVersion

LIFECYCLE_DRAFT = "DRAFT"
LIFECYCLE_PILOT = "PILOT"
LIFECYCLE_IMPLEMENTED = "IMPLEMENTED"
LIFECYCLE_RETIRED = "RETIRED"

ALLOWED_LIFECYCLE_STATUSES = frozenset(
    {LIFECYCLE_DRAFT, LIFECYCLE_PILOT, LIFECYCLE_IMPLEMENTED, LIFECYCLE_RETIRED}
)


class CurriculumLifecycleError(ValueError):
    pass


def set_curriculum_lifecycle(version: CurriculumVersion, status: str) -> CurriculumVersion:
    normalized = status.strip().upper()
    if normalized not in ALLOWED_LIFECYCLE_STATUSES:
        raise CurriculumLifecycleError(f"Unsupported curriculum lifecycle status: {status}")
    version.lifecycle_status = normalized
    # Only an implemented authoritative version is learner-selectable by default.
    version.active = normalized == LIFECYCLE_IMPLEMENTED
    return version


def is_learner_selectable(version: CurriculumVersion) -> bool:
    return version.lifecycle_status == LIFECYCLE_IMPLEMENTED and version.active
