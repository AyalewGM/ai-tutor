from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1]
    / "docs/curriculum/drafts/canonical-grade8-multistep-equations-depth-r1/generator.py"
)
PACKAGE_PATH = (
    Path(__file__).parents[1]
    / "docs/curriculum/drafts/canonical-grade8-multistep-equations-depth-r1/package.json"
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


def test_first_invalid_step_accepts_equivalent_fractions_in_every_mode():
    # Independent Math counterexample: seed 1 is 3(x+4)+3=14, x=-1/3.
    reproduced = generator.create_variant(
        "ERROR_ANALYSIS_FIRST_INVALID_STEP", seed=1, mode="diagnostic"
    )
    assert reproduced.canonical_answer == "STEP_1|x=-1/3"
    assert reproduced.response_is_correct("STEP_1|x=-2/6")
    for mode in generator.MODES:
        for seed in generator.PRIMARY_SEEDS:
            variant = generator.create_variant(
                "ERROR_ANALYSIS_FIRST_INVALID_STEP", seed=seed, mode=mode
            )
            step, solution = variant.canonical_answer.split("|", 1)
            exact = Fraction(solution.removeprefix("x="))
            scaled = f"{2 * exact.numerator}/{2 * exact.denominator}"
            assert variant.response_is_correct(f" {step.lower()} | X = {scaled} ")
            assert variant.response_is_correct(variant.canonical_answer)
            for wrong in (
                f"STEP_2|x={scaled}",
                f"NO_ERROR|x={scaled}",
                f"{step}|x={_fraction(solution) + 1}",
                f"{step}|x=1/0",
                f"{step}|x=not-a-number",
                f"{step}|x=",
                f"{step}|{scaled}",
                f"{step}|x={scaled}|extra",
                f"|x={scaled}",
            ):
                assert not variant.response_is_correct(wrong), (mode, seed, wrong)


def test_first_invalid_step_guided_probe_normalizes_composite_wrong_answers():
    for seed in generator.PRIMARY_SEEDS:
        variant = generator.create_variant(
            "ERROR_ANALYSIS_FIRST_INVALID_STEP", seed=seed, mode="guided"
        )
        for signal in variant.misconception_signals:
            step, solution = signal["candidate_response"].split("|", 1)
            exact = Fraction(solution.removeprefix("x="))
            scaled = f"{3 * exact.numerator}/{3 * exact.denominator}"
            observed = f"{step.lower()}|x={scaled}"
            matched = variant.guided_repair(observed, signal["reasoning_choice"])
            assert matched["status"] == "TARGETED_REPAIR"
            assert matched["misconception_code"] == signal["code"]
            mismatched = variant.guided_repair(observed, "OTHER")
            assert mismatched["status"] == "NEUTRAL_RETRY"
            assert variant.guided_repair(f"{step}|x=1/0", signal["reasoning_choice"])[
                "status"
            ] == "NEUTRAL_RETRY"


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


def test_public_payload_is_mode_isolated_accessible_and_leakage_safe():
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
            if mode == "guided":
                assert payload["stage"] == "OBSERVE"
                assert "prompt" not in payload
                assert "first_step_choices" not in payload
                assert payload["guided_session_required"] is True
            else:
                assert payload["response_fields"] == ["answer"]
                assert payload["guided_support_available"] is False
                assert "first_step_choices" not in payload
                assert "representation_sequence" not in payload

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


def test_contextual_domains_hold_for_every_mode_seed_and_transfer():
    contextual_variants = 0
    for mode in generator.MODES:
        for seed in generator.PRIMARY_SEEDS:
            perimeter = generator.create_variant("PERIMETER_MODEL", seed=seed, mode=mode)
            perimeter_domain = perimeter.oracle["context_domain"]
            assert perimeter_domain["kind"] == "RECTANGLE_DIMENSIONS"
            assert Fraction(perimeter_domain["length"]) > 0
            assert Fraction(perimeter_domain["width"]) > 0
            assert Fraction(perimeter_domain["perimeter"]) > 0
            assert perimeter_domain["strictly_positive"] is True

            plans = generator.create_variant("COMPETING_PLANS_MODEL", seed=seed, mode=mode)
            plan_domain = plans.oracle["context_domain"]
            uses = Fraction(plan_domain["use_count"])
            assert plan_domain["kind"] == "DISCRETE_USE_COUNT"
            assert uses >= 0 and uses.denominator == 1
            assert Fraction(plan_domain["plan_a_fixed"]) >= 0
            assert Fraction(plan_domain["plan_b_fixed"]) >= 0
            assert plan_domain["nonnegative_integers"] is True
            contextual_variants += 2
    assert contextual_variants == 128

    checked_transfers = 0
    for family in generator.FAMILIES:
        for seed in generator.PRIMARY_SEEDS:
            source = generator.create_variant(family, seed=seed, mode="guided")
            transfer = generator.create_unhinted_transfer(source)
            if transfer.family_code == "PERIMETER_MODEL":
                domain = transfer.oracle["context_domain"]
                assert Fraction(domain["length"]) > 0
                assert Fraction(domain["width"]) > 0
                assert Fraction(domain["perimeter"]) > 0
            elif transfer.family_code == "COMPETING_PLANS_MODEL":
                domain = transfer.oracle["context_domain"]
                uses = Fraction(domain["use_count"])
                assert uses >= 0 and uses.denominator == 1
                assert Fraction(domain["plan_a_fixed"]) >= 0
                assert Fraction(domain["plan_b_fixed"]) >= 0
            checked_transfers += 1
    assert checked_transfers == 192


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


def _advance_to_practice(variant):
    state = generator.start_guided_learning(variant)
    assert state.stage == "OBSERVE"
    skipped = generator.advance_guided_learning(state, {"first_step_id": "PRESERVE_EQUALITY"})
    assert skipped.stage == "OBSERVE"
    state = generator.advance_guided_learning(
        state, {"observation_choice": "STRUCTURE_NOTICED"}
    )
    assert state.stage == "PREDICT"
    wrong = generator.advance_guided_learning(
        state, {"first_step_id": "CHANGE_ONE_SIDE"}
    )
    assert wrong.stage == "PREDICT"
    state = generator.advance_guided_learning(
        state, {"first_step_id": "PRESERVE_EQUALITY"}
    )
    assert state.stage == "MANIPULATE"
    one_side = generator.advance_guided_learning(
        state,
        {
            "operation_choice": "PRESERVE_EQUALITY",
            "applied_to": ["LEFT_COMPLETE_SIDE"],
        },
    )
    assert one_side.stage == "MANIPULATE"
    state = generator.advance_guided_learning(
        state,
        {
            "operation_choice": "PRESERVE_EQUALITY",
            "applied_to": ["LEFT_COMPLETE_SIDE", "RIGHT_COMPLETE_SIDE"],
        },
    )
    assert state.stage == "EXPLAIN"
    unsupported = generator.advance_guided_learning(
        state, {"claim_choice": "MOVE_AND_CHANGE_SIGN"}
    )
    assert unsupported.stage == "EXPLAIN"
    state = generator.advance_guided_learning(
        state, {"claim_choice": "SAME_OPERATION_BOTH_COMPLETE_SIDES"}
    )
    assert state.stage == "PRACTICE"
    return state


def test_guided_learning_flow_requires_math_evidence_transfer_binding_and_verification():
    variant = generator.create_variant(
        "VARIABLES_BOTH_SIDES", seed=6, mode="guided"
    )
    state = _advance_to_practice(variant)
    signal = variant.misconception_signals[0]
    state = generator.advance_guided_learning(
        state, {"answer": signal["candidate_response"]}
    )
    assert state.stage == "DIAGNOSE"
    unsupported = generator.advance_guided_learning(
        state, {"reasoning_choice": "OTHER"}
    )
    assert unsupported.stage == "DIAGNOSE"
    assert unsupported.feedback_code == "DIAGNOSIS_NOT_CORROBORATED"
    state = generator.advance_guided_learning(
        state, {"reasoning_choice": signal["reasoning_choice"]}
    )
    assert state.stage == "DIAGNOSE"
    assert state.diagnosis_route == signal["code"]
    state = generator.advance_guided_learning(
        state, {"corrected_response": variant.canonical_answer}
    )
    assert state.stage == "TRANSFER"
    transfer = state.transfer_variant
    assert transfer is not None
    fabricated = generator.advance_guided_learning(
        state,
        {"variant_id": "fabricated", "answer": transfer.canonical_answer},
    )
    assert fabricated.stage == "TRANSFER"
    state = generator.advance_guided_learning(
        state,
        {"variant_id": transfer.variant_id, "answer": transfer.canonical_answer},
    )
    assert state.stage == "VERIFY"
    invalid = generator.advance_guided_learning(
        state,
        {
            "answer": variant.canonical_answer,
            "substitution_left": "5/2",
            "substitution_right": "5/2",
        },
    )
    assert invalid.stage == "VERIFY"
    state = generator.advance_guided_learning(
        state,
        {
            "answer": variant.canonical_answer,
            "substitution_left": variant.oracle["substitution_left"],
            "substitution_right": variant.oracle["substitution_right"],
        },
    )
    assert state.complete is True
    assert state.stage == generator.COMPLETE_STAGE


def test_correct_guided_practice_bypasses_repair_but_not_unhinted_transfer():
    variant = generator.create_variant(
        "FRACTIONAL_COEFFICIENTS", seed=4, mode="guided"
    )
    state = _advance_to_practice(variant)
    state = generator.advance_guided_learning(
        state, {"answer": variant.canonical_answer}
    )
    assert state.stage == "DIAGNOSE"
    assert "reasoning_choices" not in generator.learning_stage_payload(state)
    blocked = generator.advance_guided_learning(
        state, {"readiness_choice": "NOT_READY"}
    )
    assert blocked.stage == "DIAGNOSE"
    state = generator.advance_guided_learning(
        state, {"readiness_choice": "READY_UNHINTED"}
    )
    assert state.stage == "TRANSFER"
    transfer_payload = generator.learning_stage_payload(state)["transfer"]
    assert transfer_payload["mode"] == "independent"
    assert "first_step_choices" not in transfer_payload
    assert "representation_sequence" not in transfer_payload

def test_maryland_lettered_subparts_are_separate_partial_provisional_relations():
    package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    maryland = {
        row["standard_id"]: row
        for row in package["source_provenance"]
        if row["publisher"] == "Maryland State Department of Education"
    }
    assert set(maryland) == {"8.AT.B.3a", "8.AT.B.3b"}
    for row in maryland.values():
        assert row["mapping_status"] == "PROVISIONAL_NOT_ACCEPTED"
        assert row["coverage_relation"] == "PARTIAL_NON_EXHAUSTIVE"

    assert set(maryland["8.AT.B.3a"]["family_codes"]) == {
        "IDENTITY_ALL_REAL",
        "CONTRADICTION_NO_SOLUTION",
        "SOLUTION_CLASS_COMPARE",
    }
    assert set(maryland["8.AT.B.3b"]["family_codes"]) == set(generator.FAMILIES) - {
        "IDENTITY_ALL_REAL",
        "CONTRADICTION_NO_SOLUTION",
        "SOLUTION_CLASS_COMPARE",
    }
    excluded_3a = " ".join(maryland["8.AT.B.3a"]["excluded_from_coverage_credit"])
    assert "construction of examples" in excluded_3a
    assert "x = a, a = a, or a = b" in excluded_3a
    assert package["runtime_activation"] is False

def test_dc_lettered_subparts_are_separate_partial_provisional_relations():
    package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    dc = {
        row["standard_id"]: row
        for row in package["source_provenance"]
        if row["publisher"] == "CCSSO/NGA"
    }
    assert set(dc) == {"8.EE.C.7a", "8.EE.C.7b"}
    for row in dc.values():
        assert row["mapping_status"] == "DC_PROVISIONAL_NOT_ACCEPTED"
        assert row["coverage_relation"] == "PARTIAL_NON_EXHAUSTIVE"
        assert row["page"] == "printed page 54"
        assert row["version_date"].startswith("2010 publication")
        assert row["adoption_date"] == "2010-07-28"
        assert row["adoption_url"].startswith("https://osse.dc.gov/")

    class_families = {
        "IDENTITY_ALL_REAL",
        "CONTRADICTION_NO_SOLUTION",
        "SOLUTION_CLASS_COMPARE",
    }
    assert set(dc["8.EE.C.7a"]["family_codes"]) == class_families
    assert set(dc["8.EE.C.7b"]["family_codes"]) == set(generator.FAMILIES) - class_families
    assert set(dc["8.EE.C.7a"]["family_codes"]).isdisjoint(
        dc["8.EE.C.7b"]["family_codes"]
    )
    excluded_7a = " ".join(dc["8.EE.C.7a"]["excluded_from_coverage_credit"])
    assert "construction of examples" in excluded_7a
    assert "successive transformation" in excluded_7a
    assert "x = a, a = a, or a = b" in excluded_7a
    assert package["runtime_activation"] is False

