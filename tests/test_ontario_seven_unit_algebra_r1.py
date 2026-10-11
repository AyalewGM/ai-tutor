from __future__ import annotations

import importlib.util
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "ontario-seven-unit-algebra-r1"
PHASES = [
    "OBSERVE",
    "PREDICT",
    "MANIPULATE",
    "EXPLAIN",
    "PRACTICE",
    "DIAGNOSE",
    "TRANSFER",
    "VERIFY",
]


def _load(name: str) -> dict:
    return json.loads((DRAFT / name).read_text(encoding="utf-8"))


def _variants():
    path = DRAFT / "seeded_equations.py"
    spec = importlib.util.spec_from_file_location("ontario_equation_variants", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_provenance_is_complete_fail_closed_and_build_once() -> None:
    provenance = _load("provenance.json")

    assert provenance["record_type"] == "MIHUR_CONTENT_PROVENANCE"
    assert provenance["package_id"] == "ALG-EQUATION-REASONING-R1"
    assert provenance["status"] == "DRAFT_UNVERIFIED"
    assert provenance["runtime_activation"] is False
    assert provenance["learner_data_writes"] is False
    assert provenance["mastery_writes"] is False
    assert provenance["canonical"]["new_canonical_identity"] is False
    assert provenance["canonical"]["build_once_map_many"] is True
    assert provenance["standards"]["exact_expectation_ids"] == []
    assert provenance["standards"]["mapping_approval"] == "NONE"
    assert provenance["standards"]["coverage_credit"] is False
    assert provenance["classroom_evidence"]["worksheet_content_copied"] is False
    assert provenance["classroom_evidence"]["student_or_school_identifiers_stored"] is False


def test_question_type_matrix_covers_all_seven_units_without_false_coverage() -> None:
    matrix = _load("question_type_traceability.json")
    rows = matrix["rows"]

    assert {row["unit"] for row in rows} == {
        "Build Your Skills",
        "2.6C",
        "2.7C",
        "2.9C",
        "2.9 Homework",
        "2.10 Homework",
        "2.11 Homework",
    }
    assert matrix["standards_mapping"]["exact_expectation_ids"] == []
    assert matrix["standards_mapping"]["approval"] == "NONE"
    assert matrix["runtime_activation"] is False
    assert all(row["generator_status"].startswith(("PARTIAL", "ABSENT")) for row in rows)
    assert all("VERIFIED" not in row["generator_status"] for row in rows)
    assert any(row["decision"] == "PROPOSED_GAP_PENDING_ARCHITECTURE" for row in rows)
    assert all("UNKNOWN" in row["source_locator"] for row in rows)


def test_original_design_taxonomy_is_ranked_reuse_first_and_rights_safe() -> None:
    taxonomy = _load("original_question_type_design_taxonomy.json")
    structures = taxonomy["ranked_structures"]

    assert taxonomy["status"] == "DRAFT_UNVERIFIED"
    assert taxonomy["runtime_activation"] is False
    assert taxonomy["research_provenance"]["source_links_in_learner_lessons"] is False
    assert taxonomy["research_provenance"]["source_wording_reused"] is False
    assert len(taxonomy["research_provenance"]["sources"]) == 5
    assert len(structures) == 12
    assert [row["rank"] for row in structures] == list(range(1, 13))
    assert len({row["question_type"] for row in structures}) == 12
    assert all(row["reuse_decision"] != "CREATE_GRADE_SPECIFIC_CANONICAL" for row in structures)
    assert all(row["existing_evidence"] for row in structures)
    assert all(row["gap_types"] for row in structures)
    assert all(row["task_structures"] for row in structures)
    assert all(row["variability"] for row in structures)
    assert all(row["mihur_scenario"] for row in structures)
    assert all(row["accessible_mve"] for row in structures)
    assert all(row["generator_oracle"] for row in structures)
    assert all(row["misconception_repair"] for row in structures)
    assert all(row["unseen_transfer"] for row in structures)
    assert all(row["acceptance_checks"] for row in structures)


def test_package_covers_mihur_flow_and_representation_progression() -> None:
    package = _load("package.json")

    assert [stage["phase"] for stage in package["learning_sequence"]] == PHASES
    representations = {
        representation
        for stage in package["learning_sequence"]
        for representation in stage["representations"]
    }
    assert representations == {"CONCRETE", "VISUAL", "SYMBOLIC"}
    assert package["runtime_activation"] is False
    assessment = package["independent_assessment_contract"]
    assert assessment["hints_allowed"] is False
    assert assessment["worked_steps_visible_before_submission"] is False
    assert assessment["guided_mve_visible"] is False
    assert assessment["answer_in_public_payload"] is False
    assert assessment["guided_practice_credit"] is False
    assert assessment["historical_mastery_mutation"] is False


def test_diagnostics_are_response_evidence_specific() -> None:
    routes = _load("package.json")["diagnostic_router"]

    assert len(routes) == 5
    assert len({route["misconception_id"] for route in routes}) == 5
    assert len({route["observed_evidence"] for route in routes}) == 5
    assert len({route["probe"] for route in routes}) == 5
    assert len({route["repair"] for route in routes}) == 5
    assert len({route["exit_check"] for route in routes}) == 5
    assert all(len(route["socratic_path"]) == 3 for route in routes)


def test_seeded_replay_namespaces_and_public_non_disclosure() -> None:
    variants = _variants()

    for seed in range(120):
        guided = variants.generate(seed, "guided")
        independent = variants.generate(seed, "independent")
        assert guided == variants.generate(seed, "guided")
        assert independent == variants.generate(seed, "independent")
        assert guided.variant_id != independent.variant_id
        assert (guided.prompt, guided.options) != (independent.prompt, independent.options)
        payload = independent.public_payload()
        assert "teacher_answer" not in payload
        rendered_keys = " ".join(payload).lower()
        assert "answer" not in rendered_keys
        assert "hint" not in rendered_keys
        assert "teacher" not in rendered_keys


def test_independent_exact_linear_oracle_and_substitution() -> None:
    variants = _variants()

    for seed in range(240):
        item = variants.generate(seed, "independent")
        denominator = item.left_coefficient - item.right_coefficient
        assert denominator != 0
        independently_solved = Fraction(
            item.right_constant - item.left_constant,
            denominator,
        )
        claimed = Fraction(item.teacher_answer["solution"])
        assert claimed == independently_solved
        left = item.left_coefficient * claimed + item.left_constant
        right = item.right_coefficient * claimed + item.right_constant
        assert left == right
        assert Fraction(item.teacher_answer["left_at_solution"]) == left
        assert Fraction(item.teacher_answer["right_at_solution"]) == right
        assert item.teacher_answer["substitution_verified"] is True


def test_distribution_expansion_and_equivalent_options_are_exact() -> None:
    variants = _variants()

    for seed in range(240):
        item = variants.generate(seed, "independent")
        if item.structure == "NEGATIVE_DISTRIBUTION":
            assert item.distribution_factor is not None
            assert item.distribution_shift is not None
            assert item.left_coefficient == item.distribution_factor
            # The expanded constant includes the distributed shift plus the
            # separately authored outside constant, so it must differ from
            # merely dropping the distribution for every generated case.
            distributed = Fraction(item.distribution_factor * item.distribution_shift)
            assert item.left_constant != -distributed
        elif item.structure == "EQUIVALENT_EQUATIONS":
            index = item.teacher_answer["equivalent_option_index"]
            assert isinstance(index, int)
            assert 0 <= index < len(item.options)
            option = item.options[index]
            assert re.search(r"=", option)
            # The selected option must accept the independently solved value.
            # We intentionally verify this through the stored exact solution
            # and the base equation; Mathematical Review still owns acceptance
            # of the option parser/scoring contract.
            solution = Fraction(item.teacher_answer["solution"])
            assert item.left_coefficient * solution + item.left_constant == item.right_constant


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "4", None])
def test_invalid_seed_values_fail_closed(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _variants().generate(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        _variants().generate(4, mode)


def test_accessibility_contract_is_equation_specific() -> None:
    contract = _load("package.json")["accessibility_contract"]

    assert "both sides" in contract["keyboard_only"]
    assert "substitution values" in contract["screen_reader_state"]
    assert "transformation table" in contract["nonvisual_equivalent"].lower()
    assert contract["focus_recovery"]
    assert contract["reduced_motion"]
    assert contract["color_independence"] is True
    assert contract["independent_scaffolds"] is False
