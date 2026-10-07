"""Verified authoritative source registry for Wave-1 U.S. mathematics coverage.

This module records source identity and structural facts only.  A verified source
MUST NOT be interpreted as completed standards ingestion or reviewed canonical
mapping.  Coverage remains fail-closed until the national completion gate passes.
"""

from dataclasses import dataclass
from enum import StrEnum


class Grade9Structure(StrEnum):
    GRADE = "GRADE"
    COURSE = "COURSE"
    PATHWAY = "PATHWAY"


@dataclass(frozen=True)
class StateMathSource:
    state_code: str
    authority_code: str
    authority_name: str
    version: str
    source_uri: str
    lifecycle_status: str
    grades: tuple[int, ...]
    grade9_structure: Grade9Structure
    effective_note: str

    def __post_init__(self) -> None:
        if len(self.state_code) != 2:
            raise ValueError("state_code must be a two-letter code")
        if self.lifecycle_status not in {"DRAFT", "PILOT", "IMPLEMENTED", "RETIRED"}:
            raise ValueError("invalid lifecycle_status")
        if self.grades != tuple(range(1, 10)):
            raise ValueError("national pre-launch sources must address Grades 1-9")


WAVE1_VERIFIED_SOURCES: tuple[StateMathSource, ...] = (
    StateMathSource(
        state_code="CA",
        authority_code="CDE",
        authority_name="California Department of Education",
        version="CA-CCSSM-2013",
        source_uri="https://www.cde.ca.gov/be/st/ss/documents/ccssmathstandardaug2013.pdf",
        lifecycle_status="IMPLEMENTED",
        grades=tuple(range(1, 10)),
        grade9_structure=Grade9Structure.PATHWAY,
        effective_note="Grade-specific through 8; high school uses traditional/integrated pathways.",
    ),
    StateMathSource(
        state_code="NY",
        authority_code="NYSED",
        authority_name="New York State Education Department",
        version="NGMLS-2017",
        source_uri="https://www.nysed.gov/standards-instruction/mathematics",
        lifecycle_status="IMPLEMENTED",
        grades=tuple(range(1, 10)),
        grade9_structure=Grade9Structure.COURSE,
        effective_note="Next Generation Mathematics Learning Standards; high school is course-organized.",
    ),
    StateMathSource(
        state_code="NJ",
        authority_code="NJDOE",
        authority_name="New Jersey Department of Education",
        version="NJSLS-M-2023",
        source_uri="https://www.nj.gov/education/standards/math/2023/",
        lifecycle_status="IMPLEMENTED",
        grades=tuple(range(1, 10)),
        grade9_structure=Grade9Structure.COURSE,
        effective_note="2023 NJSLS-M; K-8 grade domains and high-school conceptual categories.",
    ),
    StateMathSource(
        state_code="VA",
        authority_code="VDOE",
        authority_name="Virginia Department of Education",
        version="SOL-MATH-2023",
        source_uri="https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics",
        lifecycle_status="IMPLEMENTED",
        grades=tuple(range(1, 10)),
        grade9_structure=Grade9Structure.COURSE,
        effective_note="Approved August 31, 2023; fully implemented in the 2024-2025 school year.",
    ),
)


def source_for(state_code: str) -> StateMathSource | None:
    code = state_code.strip().upper()
    return next((source for source in WAVE1_VERIFIED_SOURCES if source.state_code == code), None)
