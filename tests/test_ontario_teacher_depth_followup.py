"""Focused original draft content tests: #337 scientific transfer and division repair."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs/curriculum/drafts"


def _module(relative: str, name: str):
    path = DRAFT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


scientific = _module(
    "scientific-notation-learning-package-r1/learning_flow.py",
    "ontario_depth_scientific",
)
source = _module(
    "ontario-algebra-family-generators-r1/seeded_family_extensions.py",
    "ontario_depth_source",
)
polynomial = _module(
    "ontario-polynomial-division-package-r1/learning_package.py",
    "ontario_depth_polynomial",
)


def _exact(value: Fraction) -> dict[str, int]:
    number = Fraction(value)
    return {"numerator": number.numerator, "denominator": number.denominator}


@pytest.mark.parametrize("mode", ["guided", "independent"])
def test_context_transfer_is_deterministic_and_shifts_operation_and_context(mode):
    covered = set()
    prompts = set()
    to_scientific_inputs = []
    for index in range(48):
        practice = source.generate(scientific.scientific_seed(index), "guided")
        item = scientific.generate_contextual_transfer(index, mode, source.generate)
        again = scientific.generate_contextual_transfer(index, mode, source.generate)
        operation = item.parameters["operation"]
        covered.add(operation)
        prompts.add(item.prompt)
        assert item == again
        assert operation != practice.parameters["operation"]
        assert item.variant_id != practice.variant_id
        assert scientific.verify_teacher_oracle(item)
        assert "State why the resulting units" in item.prompt
        if operation == "TO_SCIENTIFIC":
            exact_input = Fraction(item.teacher_oracle["ordinary_value"])
            to_scientific_inputs.append(exact_input)
            assert f"exact value {exact_input} in normalized" in item.prompt
        if mode == "independent":
            public = scientific.independent_public_task(item)
            serialized = json.dumps(public)
            assert "teacher_oracle" not in serialized
            assert "parameters" not in serialized
            assert "variant_id" not in public
            assert public["hints"] == public["worked_steps"] == []
            assert public["mastery_credit"] is False
        else:
            oracle = item.teacher_oracle
            evidence = {
                "normalized_coefficient": _exact(oracle["coefficient"]),
                "power_of_ten": oracle["exponent"],
                "exact_ordinary_value": _exact(oracle["ordinary_value"]),
                "normalization_explanation": scientific.EXPLANATION_CODES[operation],
            }
            assert scientific.evaluate_guided_response(item, evidence)["correct"] is True
    assert covered == {"TO_SCIENTIFIC", "TO_ORDINARY", "MULTIPLY", "DIVIDE"}
    assert len(prompts) == 48
    assert any(abs(value) < 1 for value in to_scientific_inputs)
    assert any(value.denominator != 1 for value in to_scientific_inputs)


@pytest.mark.parametrize("invalid_index", [-1, True, 1.5, "2"])
def test_context_transfer_rejects_invalid_seed(invalid_index):
    with pytest.raises(ValueError):
        scientific.generate_contextual_transfer(invalid_index, "guided", source.generate)


def test_context_transfer_refuses_wrong_mode_or_generator():
    with pytest.raises(ValueError):
        scientific.generate_contextual_transfer(1, "assessment", source.generate)
    with pytest.raises(TypeError):
        scientific.generate_contextual_transfer(1, "guided", None)


@pytest.mark.parametrize(
    ("damage", "diagnosis"),
    [
        (
            lambda evidence: evidence.update(
                coefficient_reason="DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT"
            ),
            "POLY.DIV.COEFFICIENT_RECIPROCAL",
        ),
        (
            lambda evidence: evidence.update(
                exponent_reason="DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT"
            ),
            "POLY.DIV.ADD_EXPONENTS",
        ),
        (
            lambda evidence: (
                evidence.update(terms=evidence["terms"][:1]),
                evidence.update(reconstruction=evidence["reconstruction"][:1]),
            ),
            "POLY.DIV.ONE_TERM_ONLY",
        ),
        (
            lambda evidence: evidence.update(domain_restrictions=[]),
            "POLY.DIV.DOMAIN_OMITTED",
        ),
    ],
)
def test_polynomial_repair_requires_both_complete_original_and_fresh(
    damage, diagnosis
):
    item = polynomial.generate(7, "guided")
    repaired = copy.deepcopy(item.teacher_oracle["structured_response"])
    failed = copy.deepcopy(repaired)
    damage(failed)
    assert polynomial.diagnose_response(failed, item) == diagnosis

    fresh = polynomial.fresh_exit(7, "guided", diagnosis)
    fresh_response = copy.deepcopy(fresh.teacher_oracle["structured_response"])
    valid = polynomial.evaluate_repair_progress(
        failed, repaired, fresh_response, item, fresh
    )
    assert valid == {
        "misconception_id": diagnosis,
        "original_repaired": True,
        "fresh_exit_verified": True,
        "ready_to_fade": True,
        "mastery_credit": False,
    }

    unreconstructed = copy.deepcopy(repaired)
    unreconstructed["reconstruction"][0]["product_term"]["coefficient"] = "999"
    blocked = polynomial.evaluate_repair_progress(
        failed, unreconstructed, fresh_response, item, fresh
    )
    assert blocked["original_repaired"] is False
    assert blocked["ready_to_fade"] is False

    fresh_wrong_domain = copy.deepcopy(fresh_response)
    fresh_wrong_domain["domain_restrictions"] = []
    blocked_fresh = polynomial.evaluate_repair_progress(
        failed, repaired, fresh_wrong_domain, item, fresh
    )
    assert blocked_fresh["ready_to_fade"] is False


@pytest.mark.parametrize(
    ("seed", "diagnosis"),
    [
        (5700, "POLY.DIV.DOMAIN_OMITTED"),
        (44685, "POLY.DIV.ONE_TERM_ONLY"),
    ],
)
def test_polynomial_fresh_exit_avoids_published_semantic_collisions(seed, diagnosis):
    original = polynomial.generate(seed, "guided")
    fresh = polynomial.fresh_exit(seed, "guided", diagnosis)

    assert fresh == polynomial.fresh_exit(seed, "guided", diagnosis)
    assert fresh.variant_id != original.variant_id
    assert polynomial._semantic_contract(fresh) != polynomial._semantic_contract(original)
    assert (
        fresh.teacher_oracle["structured_response"]
        != original.teacher_oracle["structured_response"]
    )
    assert (
        polynomial.evaluate_structured_response(
            original.teacher_oracle["structured_response"], fresh
        )
        is False
    )


def test_one_term_only_collision_keeps_multi_term_target_and_blocks_omission():
    seed = 44685
    diagnosis = "POLY.DIV.ONE_TERM_ONLY"
    original = polynomial.generate(seed, "guided")
    fresh = polynomial.fresh_exit(seed, "guided", diagnosis)

    assert original.structure == fresh.structure == "POLYNOMIAL_BY_MONOMIAL"
    assert len(fresh.teacher_oracle["dividend_terms"]) >= 2
    assert len(fresh.teacher_oracle["quotient_terms"]) >= 2
    assert polynomial._semantic_contract(fresh) != polynomial._semantic_contract(
        original
    )

    corrected = copy.deepcopy(original.teacher_oracle["structured_response"])
    failed_original = copy.deepcopy(corrected)
    failed_original["terms"] = failed_original["terms"][:1]
    failed_original["reconstruction"] = failed_original["reconstruction"][:1]
    assert polynomial.diagnose_response(failed_original, original) == diagnosis

    complete_fresh = copy.deepcopy(fresh.teacher_oracle["structured_response"])
    verified = polynomial.evaluate_repair_progress(
        failed_original, corrected, complete_fresh, original, fresh
    )
    assert verified["ready_to_fade"] is True
    assert verified["mastery_credit"] is False

    incomplete_fresh = copy.deepcopy(complete_fresh)
    incomplete_fresh["terms"] = incomplete_fresh["terms"][:1]
    incomplete_fresh["reconstruction"] = incomplete_fresh["reconstruction"][:1]
    blocked = polynomial.evaluate_repair_progress(
        failed_original, corrected, incomplete_fresh, original, fresh
    )
    assert blocked["original_repaired"] is True
    assert blocked["fresh_exit_verified"] is False
    assert blocked["ready_to_fade"] is False
    assert blocked["mastery_credit"] is False


@pytest.mark.parametrize(
    "misconception",
    [
        "POLY.DIV.COEFFICIENT_RECIPROCAL",
        "POLY.DIV.ADD_EXPONENTS",
        "POLY.DIV.ONE_TERM_ONLY",
        "POLY.DIV.DOMAIN_OMITTED",
    ],
)
def test_fresh_exit_preserves_its_diagnosed_mathematical_target(misconception):
    original = polynomial.generate(7, "guided")
    fresh = polynomial.fresh_exit(7, "guided", misconception)
    assert polynomial._preserves_misconception_target(fresh, misconception)
    assert polynomial._semantic_contract(fresh) != polynomial._semantic_contract(
        original
    )
    assert (
        fresh.teacher_oracle["structured_response"]
        != original.teacher_oracle["structured_response"]
    )


def test_polynomial_no_diagnosis_does_not_claim_repair_and_rejects_wrong_exit():
    item = polynomial.generate(7, "guided")
    correct = copy.deepcopy(item.teacher_oracle["structured_response"])
    fresh = polynomial.generate(11, "guided")
    outcome = polynomial.evaluate_repair_progress(
        correct, correct, fresh.teacher_oracle["structured_response"], item, fresh
    )
    assert outcome["ready_to_fade"] is False
    assert outcome["misconception_id"] == "NO_REMEDIATION"

    failed = copy.deepcopy(correct)
    failed["domain_restrictions"] = []
    with pytest.raises(ValueError, match="diagnosed exit"):
        polynomial.evaluate_repair_progress(
            failed, correct, fresh.teacher_oracle["structured_response"], item, fresh
        )


def test_polynomial_guided_repair_refuses_independent_assessment():
    guided = polynomial.generate(7, "guided")
    independent = polynomial.generate(9, "independent")
    correct = copy.deepcopy(guided.teacher_oracle["structured_response"])
    with pytest.raises(PermissionError):
        polynomial.evaluate_repair_progress(
            correct,
            correct,
            independent.teacher_oracle["structured_response"],
            guided,
            independent,
        )


def test_both_content_contracts_remain_draft_and_runtime_off():
    assert scientific.STATUS == polynomial.STATUS == "DRAFT_UNVERIFIED"
    assert scientific.RUNTIME_ACTIVATION is polynomial.RUNTIME_ACTIVATION is False
