from __future__ import annotations

import importlib.util
import json
import sys
from collections import deque
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WAVE = ROOT / "docs" / "curriculum" / "drafts" / "learning-packages-wave2"
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "middle-grades-cube-nets-r1"


def _module():
    path = WAVE / "data_spatial_depth_draft.py"
    spec = importlib.util.spec_from_file_location("middle_grades_cube_nets_r1", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _independent_fold(cells: tuple[tuple[int, int], ...]) -> tuple[bool, int]:
    squares = set(cells)
    if len(squares) != 6:
        return False, 0

    def neg(vector: tuple[int, int, int]) -> tuple[int, int, int]:
        return tuple(-entry for entry in vector)

    start = min(squares)
    frames = {start: ((1, 0, 0), (0, 1, 0), (0, 0, 1))}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        right, up, normal = frames[(x, y)]
        neighbors = (
            ((x + 1, y), (neg(normal), up, right)),
            ((x - 1, y), (normal, up, neg(right))),
            ((x, y + 1), (right, neg(normal), up)),
            ((x, y - 1), (right, normal, neg(up))),
        )
        for cell, frame in neighbors:
            if cell not in squares:
                continue
            if cell in frames and frames[cell] != frame:
                return False, len({value[2] for value in frames.values()})
            if cell not in frames:
                frames[cell] = frame
                queue.append(cell)
    directions = len({frame[2] for frame in frames.values()})
    return len(frames) == 6 and directions == 6, directions


def _items_by_structure(module, mode: str = "guided") -> dict[str, object]:
    items = {}
    for seed in range(100):
        item = module.generate_cube_net_evidence(seed, mode)
        items.setdefault(item.structure, item)
    assert set(items) == set(module.CUBE_NET_STRUCTURES)
    return items


def test_package_and_provenance_remain_fail_closed() -> None:
    package = json.loads((DRAFT / "package.v1.json").read_text())
    provenance = json.loads((DRAFT / "provenance.v1.json").read_text())
    assert package["package_id"] == provenance["package_id"] == "W2-G8-CUBE-NETS"
    assert package["revision"] == provenance["revision"] == "middle-grades-cube-nets-r1"
    for artifact in (package, provenance):
        assert artifact["status"] == "DRAFT_UNVERIFIED"
        assert artifact["runtime_activation"] is False
        assert artifact["mastery_writes"] is False
    assert provenance["standards"]["official_url"] == "UNKNOWN"
    assert provenance["standards"]["expectation_ids"] == []
    assert provenance["standards"]["mapping_approval"] == "NONE"
    assert provenance["canonical"]["canonical_identity_change"] is False
    assert provenance["approvals"]["release"] == "NOT_APPROVED"


def test_complete_mihur_and_representation_progression() -> None:
    package = json.loads((DRAFT / "package.v1.json").read_text())
    assert [step["phase"] for step in package["learning_sequence"]] == [
        "OBSERVE",
        "PREDICT",
        "MANIPULATE",
        "EXPLAIN",
        "PRACTICE",
        "DIAGNOSE",
        "TRANSFER",
        "VERIFY",
    ]
    used = {
        representation
        for step in package["learning_sequence"]
        for representation in step["representations"]
    }
    assert used == {"CONCRETE", "VISUAL", "SYMBOLIC"}
    assert package["scope_contract"]["one_primary_role_per_variant"] is True
    assert package["scope_contract"]["cross_objective_back_credit"] is False


def test_existing_35_shape_oracle_is_reused_and_independently_reconstructed() -> None:
    module = _module()
    assert len(module.SHAPES) == 35
    assert len(module.VALID) == 11
    assert len(module.INVALID) == 24
    for shape in module.SHAPES:
        expected, directions = _independent_fold(shape)
        trace = module.fold_trace(shape)
        assert trace["foldable"] is expected
        assert module.foldable(shape) is expected
        if expected:
            assert trace["distinct_face_directions"] == directions == 6
            assert trace["reason_code"] == "SIX_DISTINCT_FACE_DIRECTIONS"


def test_seed_replay_mode_separation_all_structures_and_public_non_disclosure() -> None:
    module = _module()
    guided = _items_by_structure(module, "guided")
    independent = _items_by_structure(module, "independent")
    assert set(guided) == set(independent) == set(module.CUBE_NET_STRUCTURES)
    for seed in range(200):
        item = module.generate_cube_net_evidence(seed, "guided")
        unseen = module.generate_cube_net_evidence(seed, "independent")
        assert item == module.generate_cube_net_evidence(seed, "guided")
        assert unseen == module.generate_cube_net_evidence(seed, "independent")
        assert item.variant_id != unseen.variant_id
        assert item.structure != unseen.structure
        assert item.primary_scope_role == module.CUBE_NET_PRIMARY_ROLES[item.structure]
        payload = unseen.public_payload()
        for forbidden in (
            "seed",
            "expected_evidence",
            "teacher_parameters",
            "answer",
            "hint",
            "trace",
        ):
            assert forbidden not in payload


def test_generated_foldability_and_surface_area_oracles_are_exact() -> None:
    module = _module()
    for mode in ("guided", "independent"):
        for seed in range(500):
            item = module.generate_cube_net_evidence(seed, mode)
            expected = item.expected_evidence
            parameters = item.teacher_parameters
            if item.structure == "CLASSIFY_SINGLE":
                folded, directions = _independent_fold(parameters["cells"])
                assert expected["decision"] == ("foldable" if folded else "not_foldable")
                assert expected["distinct_face_directions"] == directions
            elif item.structure in {"CONTRAST_PAIR", "PACKAGING_TRANSFER"}:
                a, _ = _independent_fold(parameters["a"])
                b, _ = _independent_fold(parameters["b"])
                assert a is not b
                correct = "A" if a else "B"
                field = "foldable_label" if item.structure == "CONTRAST_PAIR" else "usable_template"
                assert expected[field] == correct
                if item.structure == "PACKAGING_TRANSFER":
                    rejected = parameters["b"] if correct == "A" else parameters["a"]
                    assert (
                        module.fold_trace(rejected)["reason_code"]
                        == "INCONSISTENT_HINGE_CYCLE"
                    )
            elif item.structure == "INVARIANCE_TRANSFER":
                original, _ = _independent_fold(parameters["original"])
                transformed, _ = _independent_fold(parameters["transformed"])
                assert original is transformed is True
            else:
                edge = parameters["edge"]
                assert isinstance(edge, Fraction)
                assert Fraction(expected["face_area"]) == edge * edge
                assert Fraction(expected["total_surface_area"]) == 6 * edge * edge
                assert expected["unit"] == "cm²"


def test_guided_success_is_practice_only_and_independent_is_refused() -> None:
    module = _module()
    for seed in range(100):
        guided = module.generate_cube_net_evidence(seed, "guided")
        assert (
            module.diagnose_cube_net_guided(guided, dict(guided.expected_evidence))
            == "CORRECT_STRUCTURED_PRACTICE_ONLY"
        )
        independent = module.generate_cube_net_evidence(seed, "independent")
        assert (
            module.diagnose_cube_net_guided(
                independent, dict(independent.expected_evidence)
            )
            == "INDEPENDENT_ASSESSMENT_NOT_SCORED_HERE"
        )


def test_adversarial_evidence_routes_to_structure_specific_diagnosis() -> None:
    module = _module()
    items = _items_by_structure(module)

    single = items["CLASSIFY_SINGLE"]
    response = dict(single.expected_evidence)
    response["decision"] = (
        "not_foldable" if response["decision"] == "foldable" else "foldable"
    )
    assert module.diagnose_cube_net_guided(single, response) in {
        "ANY_SIX_CONNECTED_IS_NET",
        "VALID_NET_REJECTED",
    }

    pair = items["CONTRAST_PAIR"]
    response = dict(pair.expected_evidence)
    response["foldable_label"], response["rejected_label"] = (
        response["rejected_label"],
        response["foldable_label"],
    )
    assert module.diagnose_cube_net_guided(pair, response) == "PAIR_CLASSIFICATION_REVERSED"

    invariant = items["INVARIANCE_TRANSFER"]
    response = dict(invariant.expected_evidence)
    response["transformed_decision"] = "not_foldable"
    assert (
        module.diagnose_cube_net_guided(invariant, response)
        == "PAPER_ORIENTATION_CHANGES_FOLDABILITY"
    )

    area = items["SURFACE_AREA"]
    response = dict(area.expected_evidence)
    response["face_area"] = str(area.teacher_parameters["edge"])
    assert module.diagnose_cube_net_guided(area, response) == "EDGE_NOT_SQUARED"
    response = dict(area.expected_evidence)
    response["total_surface_area"] = response["face_area"]
    assert module.diagnose_cube_net_guided(area, response) == "ONE_FACE_ONLY"
    response = dict(area.expected_evidence)
    response["unit"] = "cm³"
    assert module.diagnose_cube_net_guided(area, response) == "SQUARE_UNIT_MISSING"

    transfer = items["PACKAGING_TRANSFER"]
    response = dict(transfer.expected_evidence)
    response["usable_template"], response["rejected_template"] = (
        response["rejected_template"],
        response["usable_template"],
    )
    assert (
        module.diagnose_cube_net_guided(transfer, response)
        == "PACKAGING_TEMPLATE_SELECTION_ERROR"
    )
    assert module.diagnose_cube_net_guided(transfer, {}) == "INCOMPLETE_EVIDENCE"


def test_every_diagnosis_has_a_socratic_repair_and_fresh_exit() -> None:
    module = _module()
    package = json.loads((DRAFT / "package.v1.json").read_text())
    covered = {
        code
        for route in package["diagnostic_contract"]["misconception_routes"]
        for code in route["codes"]
    }
    assert covered == set(module.CUBE_NET_DIAGNOSIS_CODES)
    for item in _items_by_structure(module).values():
        fresh = module.fresh_cube_net_exit(item)
        assert fresh.structure == item.structure
        assert fresh.mode == item.mode
        assert fresh.variant_id != item.variant_id
        assert fresh.prompt != item.prompt


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "4", None])
def test_invalid_seeds_fail_closed(seed: object) -> None:
    with pytest.raises(ValueError):
        _module().generate_cube_net_evidence(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError):
        _module().generate_cube_net_evidence(4, mode)
