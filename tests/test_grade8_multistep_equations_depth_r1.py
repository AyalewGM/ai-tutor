from __future__ import annotations

import importlib.util
import sys
from fractions import Fraction
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1]
    / "docs/curriculum/drafts/canonical-grade8-multistep-equations-depth-r1/generator.py"
)
SPEC = importlib.util.spec_from_file_location("grade8_multistep_depth_r1", MODULE_PATH)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)


def _fraction(text: str) -> Fraction:
    return Fraction(text.removeprefix("x="))


def test_all_families_modes_and_seed_bands_are_deterministic_and_unique():
    seen_ids: set[str] = set()
    for family in generator.FAMILIES:
        family_fingerprints: set[str] = set()
        for mode in generator.MODES:
            for seed in generator.PRIMARY_SEEDS:
                first = generator.create_variant(family, seed=seed, mode=mode)
                second = generator.create_variant(family, seed=seed, mode=mode)
                assert first == second
                assert first.variant_id not in seen_ids
                seen_ids.add(first.variant_id)
                assert first.task_fingerprint not in family_fingerprints
                family_fingerprints.add(first.task_fingerprint)
                assert first.canonical_skill_code == generator.CANONICAL_SKILL
                assert first.mode == mode
        assert len(family_fingerprints) == 64


def test_exact_affine_oracles_and_solution_classes():
    checked = 0
    for family in generator.FAMILIES[:-2]:
        for mode in generator.MODES:
            for seed in generator.PRIMARY_SEEDS:
                variant = generator.create_variant(family, seed=seed, mode=mode)
                a, b, c, d = map(Fraction, variant.oracle["coefficients"])
                solution_class = variant.oracle["solution_class"]
                if solution_class == "UNIQUE":
                    x = _fraction(variant.canonical_answer)
                    assert a * x + b == c * x + d
                    assert variant.oracle["substitution_left"] == variant.oracle["substitution_right"]
                    assert variant.response_is_correct(f"x={x.numerator * 3}/{x.denominator * 3}")
                elif solution_class == "ALL_REAL":
                    assert a == c and b == d
                    assert variant.response_is_correct("all_real")
                else:
                    assert solution_class == "NO_SOLUTION"
                    assert a == c and b != d
                    assert variant.response_is_correct("no_solution")
                checked += 1
    assert checked == 10 * 4 * 16


def test_error_analysis_and_solution_class_compare_oracles():
    for seed in generator.PRIMARY_SEEDS:
        error = generator.create_variant(
            "ERROR_ANALYSIS_FIRST_INVALID_STEP", seed=seed, mode="independent"
        )
        assert error.canonical_answer.startswith("STEP_1|x=")
        assert error.response_is_correct(error.canonical_answer.lower())
        compare = generator.create_variant(
            "SOLUTION_CLASS_COMPARE", seed=seed, mode="mastery"
        )
        assert compare.response_is_correct("a=one|b=all_real|c=no_solution")
        assert compare.oracle["solution_classes"] == ["ONE", "ALL_REAL", "NO_SOLUTION"]


def test_guided_diagnosis_requires_matching_answer_and_reasoning_probe():
    routes = 0
    for family in generator.FAMILIES:
        for seed in range(16):
            guided = generator.create_variant(family, seed=seed, mode="guided")
            assert guided.guided_repair("not a value", None)["status"] == "NEUTRAL_RETRY"
            for signal in guided.misconception_signals:
                uncorroborated = guided.guided_repair(signal["candidate_response"], "OTHER")
                assert uncorroborated == {
                    "status": "NEUTRAL_RETRY",
                    "reason": "EVIDENCE_NOT_CORROBORATED",
                }
                repair = guided.guided_repair(
                    signal["candidate_response"], signal["reasoning_choice"]
                )
                assert repair["status"] == "TARGETED_REPAIR"
                assert repair["misconception_code"] == signal["code"]
                assert len(repair["questions"]) == 2
                assert repair["worked_answer_revealed"] is False
                assert repair["mastery_credit"] is False
                routes += 1
    assert routes >= 384


def test_support_is_unavailable_outside_guided_mode():
    for mode in ("diagnostic", "independent", "mastery"):
        for family in generator.FAMILIES:
            variant = generator.create_variant(family, seed=7, mode=mode)
            signal = variant.misconception_signals[0]
            assert variant.guided_repair(
                signal["candidate_response"], signal["reasoning_choice"]
            ) == {"status": "SUPPORT_NOT_AVAILABLE"}


def test_public_payload_has_accessibility_contract_and_no_private_evidence():
    forbidden = (
        "canonical_answer",
        "oracle",
        "misconception",
        "socratic",
        "guided_explanation",
    )
    for family in generator.FAMILIES:
        for mode in generator.MODES:
            variant = generator.create_variant(family, seed=11, mode=mode)
            payload = variant.public_payload()
            flattened = repr(payload).lower()
            assert all(term not in flattened for term in forbidden)
            assert all(set(item) == {"id", "label"} for item in payload["first_step_choices"])
            assert set(payload["interaction_requirements"]) == {
                "keyboard",
                "screen_reader",
                "focus",
                "non_color",
                "reduced_motion",
                "exact_input",
            }
            assert payload["runtime_activation"] is False
            assert payload["mastery_credit"] is False


def test_unhinted_transfer_changes_family_structure_task_and_answer():
    for family in generator.FAMILIES:
        for seed in generator.PRIMARY_SEEDS:
            source = generator.create_variant(family, seed=seed, mode="guided")
            transfer = generator.create_unhinted_transfer(source)
            assert transfer.mode == "independent"
            assert transfer.family_code != source.family_code
            assert transfer.structure_code != source.structure_code
            assert transfer.task_fingerprint != source.task_fingerprint
            assert transfer.canonical_answer != source.canonical_answer
            assert transfer.public_payload()["mastery_credit"] is False


def test_pack_is_bounded_runtime_disabled_and_idempotent():
    first = generator.create_pack(seeds_per_family_mode=8)
    second = generator.create_pack(seeds_per_family_mode=8)
    assert first == second
    assert first["status"] == "DRAFT_UNVERIFIED"
    assert first["runtime_activation"] is False
    assert first["family_count"] == 12
    assert len(first["variants"]) == 12 * 4 * 8


def test_invalid_inputs_fail_closed():
    for bad_seed in (-1, 16, 1_000_002, 1_000_019, "1", True):
        try:
            generator.create_variant(generator.FAMILIES[0], seed=bad_seed, mode="guided")
        except ValueError:
            pass
        else:
            raise AssertionError(f"seed should fail closed: {bad_seed!r}")
    for bad_count in (0, 17, True, 1.5):
        try:
            generator.create_pack(seeds_per_family_mode=bad_count)
        except ValueError:
            pass
        else:
            raise AssertionError(f"count should fail closed: {bad_count!r}")
