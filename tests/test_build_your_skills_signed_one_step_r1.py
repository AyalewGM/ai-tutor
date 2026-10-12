from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "build-your-skills-signed-one-step-r1"


def _load_json(name: str) -> dict:
    return json.loads((DRAFT / name).read_text(encoding="utf-8"))


def _variants():
    path = DRAFT / "seeded_one_step.py"
    spec = importlib.util.spec_from_file_location("signed_one_step_variants", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_provenance_is_complete_and_fail_closed() -> None:
    provenance = _load_json("provenance.json")

    assert provenance["record_type"] == "MIHUR_CONTENT_PROVENANCE"
    assert provenance["package_id"] == "ALG-SIGNED-ONE-STEP-R1"
    assert provenance["status"] == "DRAFT_UNVERIFIED"
    assert provenance["runtime_activation"] is False
    assert provenance["learner_data_writes"] is False
    assert provenance["mastery_writes"] is False
    assert provenance["standards"]["official_source_url"].startswith("UNKNOWN")
    assert provenance["standards"]["exact_expectation_ids"] == []
    assert provenance["standards"]["mapping_approval"] == "NONE"
    assert provenance["canonical"]["new_canonical_identity"] is False
    assert provenance["canonical"]["build_once_map_many"] is True
    assert all(status in {"PENDING", "PENDING_EXTERNAL_VERIFICATION", "NOT_IMPLEMENTED", "NOT_APPROVED", "NOT_DEPLOYED"} for status in provenance["independent_reviews"].values())


def test_package_covers_mihur_flow_and_safety_boundary() -> None:
    package = _load_json("package.json")

    assert [item["phase"] for item in package["learning_sequence"]] == [
        "OBSERVE", "PREDICT", "MANIPULATE", "EXPLAIN", "PRACTICE", "DIAGNOSE", "TRANSFER", "VERIFY"
    ]
    assert {representation for item in package["learning_sequence"] for representation in item["representations"]} == {"CONCRETE", "VISUAL", "SYMBOLIC"}
    assert package["canonical_family"] == "MATH.EE.EQUATION.ONE"
    assert package["runtime_activation"] is False
    assessment = package["assessment_contract"]
    assert assessment["guided_practice_credit"] is False
    assert assessment["independent_backend_scorer"] == "NOT_IMPLEMENTED"
    assert assessment["hints_in_independent"] is False
    assert assessment["worked_steps_in_independent"] is False
    assert assessment["historical_mastery_mutation"] is False


def test_all_four_structures_are_deterministic_and_exact() -> None:
    variants = _variants()
    seen = set()

    for mode in ("guided", "independent"):
        for seed in range(400):
            item = variants.generate(seed, mode)
            assert item == variants.generate(seed, mode)
            seen.add(item.structure)
            evidence = item.teacher_evidence()
            assert evidence["transformed_left"] == evidence["transformed_right"] == item.solution
            assert evidence["substitution_left"] == evidence["substitution_right"] == item.right_value
            if item.structure == "ADD":
                assert item.solution + item.operand == item.right_value
            elif item.structure == "SUBTRACT":
                assert item.solution - item.operand == item.right_value
            elif item.structure == "MULTIPLY":
                assert item.operand * item.solution == item.right_value
            else:
                assert item.operand != 0
                assert item.solution == item.operand * item.right_value

    assert seen == {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"}


def test_guided_evidence_routes_each_operation_and_independent_refuses_scoring() -> None:
    variants = _variants()
    expected_errors = {
        "ADD": "ADDITION_NOT_UNDONE_BY_SUBTRACTION",
        "SUBTRACT": "SUBTRACTION_NOT_UNDONE_BY_ADDITION",
        "MULTIPLY": "MULTIPLICATION_NOT_UNDONE_BY_DIVISION",
        "DIVIDE": "DIVISION_NOT_UNDONE_BY_MULTIPLICATION",
    }

    for seed in range(40):
        item = variants.generate(seed, "guided")
        evidence = item.teacher_evidence()
        assert variants.diagnose_guided_response(item, evidence) == "CORRECT_GUIDED_PRACTICE_ONLY"
        wrong_operation = dict(evidence)
        wrong_operation["inverse_operation"] = "MOVE_TERM_CHANGE_SIGN"
        assert variants.diagnose_guided_response(item, wrong_operation) == expected_errors[item.structure]

        independent = variants.generate(seed, "independent")
        assert variants.diagnose_guided_response(independent, independent.teacher_evidence()) == "INDEPENDENT_ASSESSMENT_NOT_SCORED_HERE"


def test_right_answer_cannot_hide_one_side_sign_or_substitution_errors() -> None:
    variants = _variants()
    item = variants.generate(5, "guided")
    evidence = item.teacher_evidence()

    one_side = dict(evidence)
    one_side["transformed_right"] = item.solution + 1
    assert variants.diagnose_guided_response(item, one_side) == "ONE_SIDE_CHANGED"

    sign_error = dict(evidence)
    sign_error["transformed_left"] = sign_error["transformed_right"] = -item.solution
    sign_error["exact_solution"] = -item.solution
    assert variants.diagnose_guided_response(item, sign_error) == "SIGNED_INVERSE_RESULT_ERROR"

    bad_check = dict(evidence)
    bad_check["substitution_left"] = item.right_value + 1
    assert variants.diagnose_guided_response(item, bad_check) == "SUBSTITUTION_CHECK_FAILED"

    unexplained = dict(evidence)
    unexplained["equality_reason"] = "MOVED_TO_OTHER_SIDE"
    assert variants.diagnose_guided_response(item, unexplained) == "EQUALITY_PRESERVATION_NOT_EXPLAINED"


def test_teacher_evidence_is_absent_from_public_payload() -> None:
    variants = _variants()

    for seed in range(100):
        item = variants.generate(seed, "independent")
        public = item.public_payload()
        assert "teacher_evidence" not in public
        assert "solution" not in public
        assert "right_value" not in public
        assert "inverse_operation" not in public
        assert "answer" not in public


def test_fresh_repair_exits_are_deterministic_and_distinct() -> None:
    variants = _variants()
    misconceptions = set(variants._INVERSE_ERRORS.values()) | {
        "SIGNED_INVERSE_OPERAND_ERROR",
        "ONE_SIDE_CHANGED",
        "SIGNED_INVERSE_RESULT_ERROR",
        "SUBSTITUTION_CHECK_FAILED",
        "EQUALITY_PRESERVATION_NOT_EXPLAINED",
    }

    for misconception in misconceptions:
        exit_item = variants.generate_repair_exit(misconception, 7)
        assert exit_item == variants.generate_repair_exit(misconception, 7)
        assert exit_item.variant_id.startswith(f"{variants.NAMESPACE}:repair:{misconception}:")
        assert exit_item.variant_id != variants.generate(7, "guided").variant_id


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "3", None])
def test_invalid_seeds_fail_closed(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _variants().generate(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        _variants().generate(3, mode)


def test_draft_is_not_registered_as_a_runtime_family() -> None:
    from app.canonical_problem_families import FAMILIES as CORE_FAMILIES
    from app.domains.algebra_functions import FAMILIES as ALGEBRA_FAMILIES

    assert "ALG-SIGNED-ONE-STEP-R1" not in CORE_FAMILIES
    assert "ALG-SIGNED-ONE-STEP-R1" not in ALGEBRA_FAMILIES
