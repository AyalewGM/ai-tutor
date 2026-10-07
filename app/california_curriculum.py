"""Authoritative California Grade 1-9 curriculum onboarding metadata.

California's state standards are grade-specific through Grade 8. High-school
mathematics is organized by conceptual categories and may be delivered through
traditional or integrated pathways, so Mihur must not invent a Grade 9 standard
set. Grade 9 coverage is therefore represented as a pathway-selection gate.
"""

from dataclasses import dataclass

CA_AUTHORITY_CODE = "CDE"
CA_CURRICULUM_CODE = "CA_CCSSM_2013"
CA_CURRICULUM_VERSION = "CA-CCSSM-2013"
CA_SOURCE_URI = (
    "https://www.cde.ca.gov/be/st/ss/documents/ccssmathstandardaug2013.pdf"
)
CA_LIFECYCLE_STATUS = "IMPLEMENTED"

GRADE_LEVELS = tuple(range(1, 9))
GRADE_9_PATHWAYS = ("ALGEBRA_I", "MATHEMATICS_I")


@dataclass(frozen=True)
class CaliforniaCoverageTarget:
    """State coverage target without claiming unreviewed standards are complete."""

    grade: int
    pathway: str | None = None

    def __post_init__(self) -> None:
        if self.grade not in range(1, 10):
            raise ValueError("California coverage grade must be 1 through 9")
        if self.grade < 9 and self.pathway is not None:
            raise ValueError("Grades 1-8 do not use a high-school pathway")
        if self.grade == 9 and self.pathway not in GRADE_9_PATHWAYS:
            raise ValueError(
                "Grade 9 requires an explicit Algebra I or Mathematics I pathway"
            )


def california_coverage_targets() -> tuple[CaliforniaCoverageTarget, ...]:
    """Return conservative targets; Grade 9 remains pathway-aware."""

    grade_targets = tuple(CaliforniaCoverageTarget(grade) for grade in GRADE_LEVELS)
    high_school_targets = tuple(
        CaliforniaCoverageTarget(9, pathway) for pathway in GRADE_9_PATHWAYS
    )
    return grade_targets + high_school_targets
