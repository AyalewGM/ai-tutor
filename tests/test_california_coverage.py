from app.curriculum_coverage import (
    completed_cells,
    national_coverage_matrix,
    state_complete,
    with_verified_california_source,
)


def test_verified_california_source_does_not_overstate_grade_completion():
    cells = with_verified_california_source(national_coverage_matrix())
    california = tuple(cell for cell in cells if cell.state_code == "CA")

    assert len(california) == 9
    assert all(cell.source_verified for cell in california)
    assert all(cell.lifecycle_status == "IMPLEMENTED" for cell in california)
    assert completed_cells(california) == 0
    assert not state_complete(california, "CA")
