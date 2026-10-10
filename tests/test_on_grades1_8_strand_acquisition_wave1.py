"""Fail-closed tests for Ontario Grades 1–8 strand acquisition."""

import json
from pathlib import Path

MANIFEST = (
    Path(__file__).parents[1]
    / "docs"
    / "curriculum"
    / "standards"
    / "on_grades1_8_2020.strand_acquisition.wave1.v1.json"
)


def test_ontario_strand_grid_is_complete_but_not_approved_coverage() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cells = data["cells"]
    assert data["counts"] == {
        "grades": 8,
        "strands_per_grade": 6,
        "strand_grade_cells": 48,
        "expectation_ids_verified": 0,
        "accepted_mappings": 0,
    }
    assert len(cells) == 48
    assert {(x["grade"], x["strand_id"]) for x in cells} == {
        (grade, strand)
        for grade in range(1, 9)
        for strand in "ABCDEF"
    }
    for cell in cells:
        assert cell["official_expectation_ids"] == []
        assert cell["expectation_level_source_verified"] is False
        assert cell["existing_mihur_mapping"] == (
            "NOT_AUDITED_FOR_THIS_EXACT_EXPECTATION"
        )
        if cell["government_overview_example"]:
            assert cell["example_source"] == (
                "https://www.ontario.ca/page/math-curriculum-grades-1-8"
            )


def test_ontario_strand_inventory_never_promotes_mastery() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["status"] == (
        "DRAFT_ONTARIO_GRADES1_8_STRAND_COVERAGE_ACQUISITION_MATRIX"
    )
    assert data["safety"] == {
        "auto_create_canonical_ids": False,
        "auto_approve_coverage": False,
        "auto_infer_mastery": False,
        "production_activation": "FORBIDDEN",
        "historical_student_records_unchanged": True,
    }
