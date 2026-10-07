"""Deterministic per-student curriculum default resolution.

Location narrows the catalog; grade selects the learner's default.  Resolution
fails closed when there is no unique implemented curriculum (for example,
California Grade 9 pathways) so onboarding can ask the parent to choose rather
than guessing.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum_models import CurriculumVersion
from app.models import Curriculum
from app.parent_models import ParentProfile


@dataclass(frozen=True)
class CurriculumDefaultResolution:
    curriculum: Curriculum | None
    reason: str
    candidates: tuple[Curriculum, ...] = ()

    @property
    def resolved(self) -> bool:
        return self.curriculum is not None


def _normalized_grade(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().upper()
    if value.startswith("GRADE "):
        value = value[6:].strip()
    if value.isdigit():
        return str(int(value))
    return value


def resolve_default_curriculum(
    db: Session,
    *,
    parent: ParentProfile,
    grade_level: str | None,
) -> CurriculumDefaultResolution:
    """Return the unique implemented curriculum for region + grade.

    A curriculum is eligible only when its current CurriculumVersion is
    IMPLEMENTED. Multiple matches are deliberately unresolved: pathway/course
    choice is a parent decision, not something Mihur infers.
    """
    grade = _normalized_grade(grade_level)
    if not parent.country_code or not parent.region_code:
        return CurriculumDefaultResolution(None, "LOCATION_REQUIRED")
    if grade is None:
        return CurriculumDefaultResolution(None, "GRADE_REQUIRED")

    rows = db.execute(
        select(Curriculum, CurriculumVersion)
        .join(
            CurriculumVersion,
            (CurriculumVersion.curriculum_id == Curriculum.id)
            & (CurriculumVersion.version == Curriculum.version),
        )
        .where(
            Curriculum.active.is_(True),
            Curriculum.country_code == parent.country_code,
            Curriculum.region_code == parent.region_code,
            CurriculumVersion.active.is_(True),
            CurriculumVersion.lifecycle_status == "IMPLEMENTED",
        )
        .order_by(Curriculum.code, Curriculum.version)
    ).all()

    candidates = tuple(
        curriculum
        for curriculum, _version in rows
        if _normalized_grade(curriculum.grade_level) == grade
    )
    if not candidates:
        return CurriculumDefaultResolution(None, "NO_IMPLEMENTED_MATCH")
    if len(candidates) > 1:
        return CurriculumDefaultResolution(None, "AMBIGUOUS_PATHWAY", candidates)
    return CurriculumDefaultResolution(candidates[0], "UNIQUE_IMPLEMENTED_MATCH", candidates)
