"""Fail-closed DC 8.EE.A.4 author-source and candidate-scope evidence."""

import json
from pathlib import Path

from app.canonical_problem_families import FAMILIES

ROOT = Path(__file__).resolve().parents[1]
SLICE = (
    ROOT
    / "docs/curriculum/standards"
    / "dc_grade8_eea4_scientific_operations_author_slice.v1.json"
)


def load_slice():
    return json.loads(SLICE.read_text(encoding="utf-8"))


def test_dc_eea4_official_identity_locator_and_complete_material_conditions():
    record = load_slice()
    assert record["jurisdiction"] == "DC"
    assert record["track"] == "GRADE_8"
    assert record["expectation_id"] == "8.EE.A.4"
    assert record["document_version"] == "2010"
    assert record["source_url"] == (
        "https://corestandards.org/wp-content/uploads/2023/09/"
        "ADA-Compliant-Math-Standards.pdf"
    )
    assert record["source_printed_page"] == 54
    assert record["source_pdf_zero_based_page_index"] == 53
    assert record["official_subpart_ids"] == []
    assert record["dc_adoption_date"] == "2010-07-21"
    assert record["access_date"] == "2026-10-27"
    assert set(record["required_material_conditions"]) == {
        "operations on scientific-notation quantities",
        "problems mixing decimal notation and scientific notation",
        "scientific notation used together with appropriately scaled measurement units",
        "both very large and very small quantities",
        "interpretation of technology-generated scientific notation",
    }


def test_dc_eea4_registered_candidates_are_bounded_and_complete_under_rule():
    record = load_slice()
    relations = {
        relation["canonical_family_id"]: relation
        for relation in record["registered_candidate_relations"]
    }
    assert set(relations) == {"MATH.SCI.MULTIPLY", "MATH.SCI.CONVERT"}
    assert set(relations) <= set(FAMILIES)
    assert relations["MATH.SCI.MULTIPLY"]["relation"] == "PARTIAL_NON_EXHAUSTIVE"
    assert relations["MATH.SCI.CONVERT"]["relation"] == (
        "NO_COVERAGE_CLAIM_PREREQUISITE_ONLY"
    )
    for relation in relations.values():
        assert relation["no_coverage_credit_for"]
        assert len(relation["evidence_paths"]) == len(
            relation["evidence_blob_shas"]
        )
        assert all(len(sha) == 40 for sha in relation["evidence_blob_shas"])


def test_dc_eea4_draft_targets_do_not_become_canonical_candidates():
    record = load_slice()
    excluded = {
        label
        for evidence in record["excluded_repository_evidence"]
        for label in evidence["labels"]
    }
    proposed = {
        "MATH.SCIENTIFIC_NOTATION.CONVERT_NORMALIZE",
        "MATH.SCIENTIFIC_NOTATION.MULTIPLY_NORMALIZE",
        "MATH.SCIENTIFIC_NOTATION.DIVIDE_NORMALIZE",
    }
    assert proposed <= excluded
    assert proposed.isdisjoint(FAMILIES)
    assert "learner-facing contract explicitly presents scientific notation" in record[
        "candidate_selection_rule"
    ]


def test_dc_eea4_isolated_slice_preserves_accepted_predecessor_and_fails_closed():
    record = load_slice()
    coordination = record["coordination"]
    assert record["author_pr"] == 513
    assert coordination["based_on_main_sha"] == (
        "cce36cebb9711d5f7a6116c3df2896b2f05dd326"
    )
    assert coordination["accepted_predecessor_pr"] == 512
    assert coordination["accepted_predecessor_head_sha"] == (
        "676442d8494dd16525d02b9e86d4a0ea6325f39e"
    )
    assert "must not overwrite" in coordination["integration_boundary"]
    assert record["independent_source_fidelity"] == "PENDING"
    assert record["canonical_equivalence"] == "UNVERIFIED"
    assert record["generator_coverage"] == "UNVERIFIED"
    assert record["assessment_coverage"] == "UNVERIFIED"
    assert record["mastery_credit"] == "FORBIDDEN"
    assert record["runtime_activation"] is False
    assert record["question_family_authoring"] == (
        "OUT_OF_SCOPE_CURRICULUM_ALGEBRA_OWNED"
    )
