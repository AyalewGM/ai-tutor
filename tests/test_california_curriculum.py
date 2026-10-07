import pytest

from app.california_curriculum import (
    CA_AUTHORITY_CODE,
    CA_CURRICULUM_VERSION,
    CA_LIFECYCLE_STATUS,
    CA_SOURCE_URI,
    CaliforniaCoverageTarget,
    california_coverage_targets,
)


def test_california_metadata_is_authoritative_and_implemented():
    assert CA_AUTHORITY_CODE == "CDE"
    assert CA_CURRICULUM_VERSION == "CA-CCSSM-2013"
    assert CA_LIFECYCLE_STATUS == "IMPLEMENTED"
    assert CA_SOURCE_URI.startswith("https://www.cde.ca.gov/")


def test_california_targets_cover_grades_1_8_and_both_grade_9_pathways():
    targets = california_coverage_targets()
    assert {target.grade for target in targets} == set(range(1, 10))
    assert {target.pathway for target in targets if target.grade == 9} == {
        "ALGEBRA_I",
        "MATHEMATICS_I",
    }


def test_grade_9_cannot_be_claimed_without_pathway():
    with pytest.raises(ValueError, match="Grade 9 requires"):
        CaliforniaCoverageTarget(9)


def test_elementary_and_middle_grades_cannot_take_high_school_pathway():
    with pytest.raises(ValueError, match="Grades 1-8"):
        CaliforniaCoverageTarget(8, "ALGEBRA_I")
