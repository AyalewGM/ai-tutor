import importlib.util
import json
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "middle-grades-rational-scale-v1"
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


def load(name: str) -> dict:
    return json.loads((DRAFT / name).read_text())


def load_variants_module():
    path = DRAFT / "seeded_variants.py"
    spec = importlib.util.spec_from_file_location("middle_grades_rational_variants", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provenance_is_complete_and_fail_closed() -> None:
    provenance = load("provenance.v1.json")

    assert provenance["package_id"] == "MG-G7-RATIONAL-SCALE-INVERSE"
    assert provenance["revision"] == "middle-grades-rational-scale-v1-r2"
    assert provenance["status"] == "DRAFT_UNVERIFIED"
    assert provenance["runtime_activation"] is False
    assert provenance["mastery_writes"] is False
    assert provenance["learner_data_writes"] is False
    assert provenance["standards"]["mapping_status"] == "PROVISIONAL_NOT_ACCEPTED"
    assert provenance["standards"]["mapping_approval"] == "NONE"
    assert provenance["canonical"]["canonical_identity_change"] is False
    assert provenance["source_heads"] == {
        "main": "13f1cf7bfcdbaa73bb248319b1ece1be649e59df",
        "standards_pr_325": "c1fa26a560ebea022202bace38d51e91ca5d08fa",
        "learning_packages_pr_327": "5d4e613b4aa241384809e048c60ee082e6f14fe4",
        "learning_packages_pr_328": "2445f197259ff27b5c99dd2b45c4bcbc2e5292f8",
    }
    assert provenance["approvals"] == {
        "standards": "PENDING",
        "mathematics": "PENDING",
        "pedagogy": "PENDING",
        "muse_accessibility_and_assessment": "PENDING",
        "engineering_integration": "NOT_REQUESTED",
        "release": "NOT_APPROVED",
    }


def test_package_has_full_phase_and_representation_progression() -> None:
    package = load("package.v1.json")
    sequence = package["learning_sequence"]

    assert [stage["phase"] for stage in sequence] == PHASES
    representations = {
        representation for stage in sequence for representation in stage["representations"]
    }
    assert representations == {"CONCRETE", "VISUAL", "SYMBOLIC"}
    assert package["status"] == "DRAFT_UNVERIFIED"
    assert package["runtime_activation"] is False
    assert package["mastery_writes"] is False


def test_scope_does_not_claim_signed_integer_addition_or_other_owned_packages() -> None:
    provenance = load("provenance.v1.json")
    boundary = provenance["coverage"]["scope_boundary"]

    assert boundary["included"] == [
        "signed rational multiplication as direction and scale",
        "signed rational division as a missing scale factor",
        "inverse verification",
    ]
    assert "signed-integer addition or subtraction" in boundary["excluded"]
    assert "ratio or double-number-line instruction" in boundary["excluded"]
    assert provenance["canonical"]["reused_generators"] == ["MATH.RAT.MUL", "MATH.RAT.DIV"]


def test_misconception_paths_are_reasoning_specific() -> None:
    pathways = load("package.v1.json")["misconception_pathways"]

    assert len(pathways) == 4
    assert len({path["id"] for path in pathways}) == 4
    assert len({path["diagnostic_probe"] for path in pathways}) == 4
    assert all(len(path["socratic_prompts"]) == 3 for path in pathways)
    assert all(path["observed_reasoning"] != path["repair"] for path in pathways)


def test_authored_oracles_are_exact() -> None:
    package = load("package.v1.json")
    examples = {item["id"]: item["answer_teacher_only"] for item in package["guided_examples"]}

    assert Fraction(examples["guided-positive-shrink"]) == Fraction(-4, 3) * Fraction(1, 2)
    assert Fraction(examples["guided-double-negative"]) == Fraction(-3, 4) * Fraction(-2, 3)
    assert Fraction(examples["guided-missing-scale"]) * Fraction(3, 4) == Fraction(-3, 2)
    transfer = package["transfer_oracle_teacher_only"]
    assert Fraction(transfer["answer"]) == Fraction(-3, 2) * Fraction(-4, 5)


def test_seeded_variants_are_deterministic_and_use_exact_oracles() -> None:
    variants = load_variants_module()

    for mode in ("guided", "independent"):
        for seed in range(40):
            first = variants.generate(seed, mode)
            second = variants.generate(seed, mode)
            assert first == second
            if first.structure == "MULTIPLY_DIRECTION_SCALE":
                assert first.answer == first.left * first.right
            else:
                assert first.answer * first.right == first.left


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "7", None])
def test_seeded_variants_reject_invalid_seed_values(seed: object) -> None:
    variants = load_variants_module()

    with pytest.raises((TypeError, ValueError)):
        variants.generate(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_seeded_variants_reject_invalid_modes(mode: object) -> None:
    variants = load_variants_module()

    with pytest.raises(ValueError, match="Unsupported mode"):
        variants.generate(7, mode)


def test_independent_namespace_and_payload_do_not_leak_answers_or_hints() -> None:
    variants = load_variants_module()
    package = load("package.v1.json")
    contract = package["independent_assessment_contract"]

    assert contract["hints_allowed"] is False
    assert contract["answer_in_client_payload"] is False
    assert contract["guided_practice_credit"] is False
    assert contract["historical_mastery_mutation"] is False
    for seed in contract["reserved_seeds"]:
        guided = variants.generate(seed, "guided")
        independent = variants.generate(seed, "independent")
        assert guided.variant_id != independent.variant_id
        assert (guided.left, guided.right) != (independent.left, independent.right)
        payload = independent.public_payload()
        assert "answer" not in payload
        assert "hint" not in " ".join(payload).lower()


def test_accessibility_contract_has_nonvisual_state_and_recovery() -> None:
    accessibility = load("package.v1.json")["accessibility_contract"]

    assert accessibility["keyboard_only"]
    assert accessibility["screen_reader_state"]
    assert accessibility["nonvisual_equivalent"]
    assert accessibility["focus_recovery"]
    assert accessibility["reduced_motion"]
    assert accessibility["color_independence"] is True
    assert accessibility["independent_scaffolds"] is False
