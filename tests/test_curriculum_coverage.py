from dataclasses import replace

from app.curriculum_coverage import (
    GRADES,
    STATE_CODES,
    completed_cells,
    national_coverage_matrix,
    state_complete,
)


def _complete(cell):
    return replace(
        cell,
        authority_code="TEST_AUTHORITY",
        source_uri="https://example.edu/official",
        curriculum_version="implemented-version",
        lifecycle_status="IMPLEMENTED",
        source_verified=True,
        standards_ingested=True,
        mappings_reviewed=True,
        published=True,
    )


def test_matrix_has_exactly_50_states_times_nine_grades():
    cells = national_coverage_matrix()
    assert len(STATE_CODES) == 50
    assert GRADES == tuple(range(1, 10))
    assert len(cells) == 450
    assert len({(cell.state_code, cell.grade) for cell in cells}) == 450


def test_proof_or_partial_work_never_counts_as_complete():
    cells = national_coverage_matrix()
    virginia_grade_9 = next(
        cell for cell in cells if cell.state_code == "VA" and cell.grade == 9
    )
    proof = replace(
        virginia_grade_9,
        authority_code="VDOE",
        source_uri="https://www.doe.virginia.gov/",
        curriculum_version="2023",
        lifecycle_status="IMPLEMENTED",
        source_verified=True,
        standards_ingested=True,
        mappings_reviewed=False,
        published=False,
    )
    assert not proof.complete
    assert completed_cells((proof,)) == 0


def test_state_requires_all_nine_complete_grade_cells():
    cells = national_coverage_matrix()
    california = tuple(_complete(cell) for cell in cells if cell.state_code == "CA")
    assert state_complete(california, "CA")

    missing_grade_9 = tuple(cell for cell in california if cell.grade != 9)
    assert not state_complete(missing_grade_9, "CA")


def test_nonimplemented_lifecycle_cannot_count_as_complete():
    cell = _complete(national_coverage_matrix()[0])
    assert not replace(cell, lifecycle_status="PILOT").complete
