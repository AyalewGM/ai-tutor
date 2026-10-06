"""Machine-readable U.S. Grade 1-9 curriculum coverage registry.

Coverage is intentionally conservative: a state/grade is incomplete until every
authoritative-source, ingestion, mapping-review, and publication gate is true.
A proof slice never implies complete grade coverage.
"""

from dataclasses import dataclass

GRADES = tuple(range(1, 10))
STATE_CODES = (
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
)


@dataclass(frozen=True)
class CoverageCell:
    state_code: str
    grade: int
    authority_code: str | None = None
    source_uri: str | None = None
    curriculum_version: str | None = None
    lifecycle_status: str | None = None
    source_verified: bool = False
    standards_ingested: bool = False
    mappings_reviewed: bool = False
    published: bool = False

    @property
    def complete(self) -> bool:
        return (
            bool(self.authority_code)
            and bool(self.source_uri)
            and bool(self.curriculum_version)
            and self.lifecycle_status == "IMPLEMENTED"
            and self.source_verified
            and self.standards_ingested
            and self.mappings_reviewed
            and self.published
        )


def national_coverage_matrix() -> tuple[CoverageCell, ...]:
    return tuple(CoverageCell(state_code=state, grade=grade) for state in STATE_CODES for grade in GRADES)


def completed_cells(cells: tuple[CoverageCell, ...]) -> int:
    return sum(cell.complete for cell in cells)


def state_complete(cells: tuple[CoverageCell, ...], state_code: str) -> bool:
    state_cells = [cell for cell in cells if cell.state_code == state_code]
    return len(state_cells) == len(GRADES) and all(cell.complete for cell in state_cells)
