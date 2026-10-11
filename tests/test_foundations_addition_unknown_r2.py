from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "foundations-reuse-v1"


def _module():
    path = DRAFT / "addition_unknown_seeded.py"
    spec = importlib.util.spec_from_file_location("foundations_addition_unknown", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_package_is_fail_closed_and_covers_mihur_flow() -> None:
    package = json.loads((DRAFT / "addition_unknown.depth.v1.json").read_text())

    assert package["status"] == "DRAFT_UNVERIFIED"
    assert package["runtime_activation"] is False
    assert package["mastery_writes"] is False
    assert package["implementation"] == "DRAFT_EXECUTABLE_CONTENT_NOT_WIRED"
    assert [stage["phase"] for stage in package["stages"]] == [
        "OBSERVE",
        "PREDICT",
        "MANIPULATE",
        "EXPLAIN",
        "PRACTICE",
        "DIAGNOSE",
        "TRANSFER",
        "VERIFY",
    ]
    assert package["assessment_contract"]["guided_practice_credit"] is False
    assert package["assessment_contract"]["hints_allowed"] is False
    assert package["assessment_contract"]["backend_status"] == "NOT_IMPLEMENTED"


def test_provenance_is_current_fail_closed_and_hands_fraction_work_to_pr_336() -> None:
    provenance = json.loads((DRAFT / "provenance.v1.json").read_text())
    packages = {package["package_id"]: package for package in provenance["packages"]}
    addition = packages["W2-G1-ADDITION-UNKNOWN"]

    assert provenance["runtime_activation"] is False
    assert provenance["mastery_writes"] is False
    assert 336 in provenance["inspected_prs"]
    assert addition["proposed_revision"] == "foundations-reuse-r2"
    assert addition["upstream_draft"]["pinned_head_sha"] == (
        "2445f197259ff27b5c99dd2b45c4bcbc2e5292f8"
    )
    assert addition["standards"]["mapping_status"] == "UNKNOWN"
    assert addition["approvals"]["release"] == "NOT_APPROVED"
    assert all(
        package["upstream_draft"]["pinned_head_sha"]
        == "2445f197259ff27b5c99dd2b45c4bcbc2e5292f8"
        for package in provenance["packages"]
        if package["upstream_draft"]["pull_request"] == 328
    )
    fraction_audit = provenance["existing_work_gap_improvement_verification"][1]
    assert "PR #336" in fraction_audit["planned_improvement"]


def test_seeded_replay_mode_separation_and_public_non_disclosure() -> None:
    variants = _module()

    for seed in range(100):
        guided = variants.generate(seed, "guided")
        independent = variants.generate(seed, "independent")
        assert guided == variants.generate(seed, "guided")
        assert independent == variants.generate(seed, "independent")
        assert guided.variant_id != independent.variant_id
        assert guided.structure != independent.structure
        payload = independent.public_payload()
        assert "answer" not in payload
        assert "balanced_equation" not in payload
        assert "check_equation" not in payload
        assert "hint" not in payload


def test_all_unknown_positions_and_distinct_transfer_structure_are_generated() -> None:
    variants = _module()
    guided_structures = {variants.generate(seed, "guided").structure for seed in range(20)}
    independent_structures = {variants.generate(seed, "independent").structure for seed in range(20)}

    assert guided_structures == set(variants.STRUCTURES)
    assert independent_structures == set(variants.STRUCTURES)
    assert "COMPARE_LARGER_UNKNOWN" in independent_structures
    assert {variants.generate(seed, "independent").unknown_role for seed in range(20)} >= {
        "result",
        "change",
        "start",
        "part",
        "larger quantity",
    }


def test_independent_integer_oracle_reconstructs_each_relation() -> None:
    variants = _module()

    for seed in range(200):
        item = variants.generate(seed, "independent")
        first, second = item.known_values
        if item.unknown_role in {"result", "larger quantity"}:
            independently_computed = first + second
        else:
            independently_computed = second - first
        assert item.answer == independently_computed
        assert 0 < item.answer <= 20


def test_diagnosis_uses_observed_response_evidence() -> None:
    variants = _module()
    change_item = next(
        variants.generate(seed, "guided")
        for seed in range(20)
        if variants.generate(seed, "guided").unknown_role == "change"
    )

    assert (
        variants.diagnose_numeric_response(change_item, change_item.answer, "result")
        == "UNKNOWN_ROLE_CONFUSION"
    )
    assert (
        variants.diagnose_numeric_response(
            change_item,
            change_item.known_values[1],
            change_item.unknown_role,
        )
        == "RESULT_AS_CHANGE"
    )
    assert (
        variants.diagnose_numeric_response(
            change_item,
            sum(change_item.known_values),
            change_item.unknown_role,
        )
        == "ADDED_VISIBLE_VALUES"
    )
    assert (
        variants.diagnose_numeric_response(
            change_item,
            change_item.known_values[0],
            change_item.unknown_role,
        )
        == "COPIED_KNOWN_QUANTITY"
    )
    assert (
        variants.diagnose_numeric_response(change_item, change_item.answer, change_item.unknown_role)
        == "CORRECT_PRACTICE_ONLY"
    )


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "4", None])
def test_invalid_seeds_fail_closed(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _module().generate(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        _module().generate(4, mode)
