from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/curriculum/drafts/canonical-grade8-inverse-operations-depth-r1"
SPEC = importlib.util.spec_from_file_location(
    "grade8_inverse_operations_depth_r1", PACKAGE / "generator.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _recompute(variant) -> Fraction:
    p = dict(variant.parameters)
    coefficient = Fraction(p["coefficient"])
    offset = Fraction(p["offset"])
    rhs = Fraction(p["rhs"])
    return (rhs - offset) / coefficient


def _substitution_values(variant, observed_answer: str) -> tuple[str, str]:
    p = dict(variant.parameters)
    left = (
        Fraction(p["coefficient"]) * Fraction(observed_answer)
        + Fraction(p["offset"])
    )
    return str(left), p["rhs"]


def test_package_is_draft_reuse_only_and_history_neutral() -> None:
    manifest = json.loads((PACKAGE / "package.json").read_text())
    assert manifest["status"] == "DRAFT_UNVERIFIED"
    assert manifest["runtime_activation"] is False
    assert manifest["mastery_writes"] is False
    assert manifest["scope"]["existing_skills"] == [
        "M8.ALG.INVERSE.ADD",
        "M8.ALG.INVERSE.MULT",
    ]
    assert manifest["scope"]["new_canonical_identity_created"] is False
    assert manifest["scope"]["jurisdiction_bank_created"] is False
    assert manifest["scope"]["curriculum_mapping_changed"] is False
    assert manifest["scope"]["dc_or_virginia_grade8_mapping_activated"] is False
    for key in (
        "registered_by_app",
        "seeded",
        "selector_or_scorer_changed",
        "learner_records_changed",
        "attempt_records_changed",
        "diagnostic_attempt_records_changed",
        "mastery_events_changed",
        "variant_history_changed",
    ):
        assert manifest["persistence_boundary"][key] is False


def test_current_versioned_provenance_and_license_rationale_are_explicit() -> None:
    manifest = json.loads((PACKAGE / "package.json").read_text())
    sources = manifest["source_provenance"]
    assert len(sources) == 4
    assert sources[0]["standard_id"] == "8.AT.B.3b"
    assert (
        sources[0]["version_date"]
        == "Version 1, February 2026; standards adopted July 29, 2025"
    )
    assert sources[0]["page"] == 24
    assert sources[0]["coverage_relation"] == "PARTIAL_NON_EXHAUSTIVE"
    assert len(sources[0]["excluded_from_coverage_credit"]) == 2
    assert manifest["scope"]["maryland_mapping_status"] == "PROVISIONAL_NOT_ACCEPTED"
    assert manifest["scope"]["maryland_full_standard_coverage"] is False
    assert sources[1]["standard_id"] == "CURRENT_LOCAL_CURRICULUM_QUALIFIER_ONLY"
    assert "Amplify Desmos Math" in sources[1]["use"]
    assert (
        sources[2]["standard_id"]
        == "LEGACY_OPEN_RESOURCE_STRUCTURE_REFERENCE_ONLY_NOT_CURRENT_ALIGNMENT"
    )
    assert "not current local sequence or alignment evidence" in sources[2]["use"]
    assert all(source["access_date"] == "2026-10-25" for source in sources)
    assert all(source["license_adaptation"] for source in sources)
    assert "PREREQUISITE" in sources[3]["standard_id"]


@pytest.mark.parametrize("mode", sorted(MODULE.MODES))
def test_all_twelve_families_are_deterministic_diverse_exact_and_nondegenerate(mode: str) -> None:
    assert len(MODULE.FAMILIES) == 12
    for family in MODULE.FAMILIES:
        variants = [MODULE.generate(family, seed, mode) for seed in range(192)]
        assert variants == [MODULE.generate(family, seed, mode) for seed in range(192)]
        assert len({variant.variant_id for variant in variants}) == 192
        assert len({variant.parameters for variant in variants}) >= 12
        for variant in variants:
            assert Fraction(variant.answer) == _recompute(variant)
            assert Fraction(dict(variant.parameters)["coefficient"]) != 0
            assert variant.answer not in dict(variant.misconception_answers).values()
            assert variant.prerequisite
            assert variant.difficulty_rationale
            assert variant.equivalence_boundary
            assert MODULE.verification_equation(variant).endswith(dict(variant.parameters)["rhs"])


def test_families_are_structurally_distinct_and_cover_both_existing_skills() -> None:
    variants = [MODULE.generate(family, 41, "guided") for family in MODULE.FAMILIES]
    assert len({variant.structure for variant in variants}) == 12
    assert {variant.canonical_skill for variant in variants} == {
        "M8.ALG.INVERSE.ADD",
        "M8.ALG.INVERSE.MULT",
    }
    assert [variant.canonical_skill for variant in variants[:6]] == [
        "M8.ALG.INVERSE.ADD"
    ] * 6
    assert [variant.canonical_skill for variant in variants[6:]] == [
        "M8.ALG.INVERSE.MULT"
    ] * 6
    assert all("Concrete:" in variant.representation[0] for variant in variants)
    assert all("Visual:" in variant.representation[1] for variant in variants)
    assert all("Symbolic:" in variant.representation[2] for variant in variants)


def test_public_payload_is_answer_free_accessible_and_unhinted_when_independent() -> None:
    forbidden = {
        "answer",
        "oracle",
        "parameters",
        "prompt",
        "misconception_answers",
        "verification",
        "strategy_probe",
    }
    for family in MODULE.FAMILIES:
        for mode in MODULE.MODES:
            variant = MODULE.generate(family, 73, mode)
            payload = variant.public_payload()
            assert forbidden.isdisjoint(payload)
            assert payload["learning_path"] == list(
                MODULE.start_learning_path(variant).stages
            )
            assert payload["initial_stage"]["stage"] == payload["learning_path"][0]
            assert set(payload["accessibility"]) == {
                "keyboard",
                "screen_reader",
                "visual",
                "motion",
                "input",
                "focus",
            }
            if mode in {"independent", "mastery"}:
                assert payload["support"] == "NONE_UNHINTED"
            else:
                assert "support" not in payload


def test_guided_diagnosis_requires_answer_and_strategy_evidence() -> None:
    for family in MODULE.FAMILIES:
        guided = MODULE.generate(family, 97, "guided")
        for code, answer in guided.misconception_answers:
            first_probe = MODULE.guided_probe(guided, answer)
            assert first_probe["classification"] == "EVIDENCE_INCOMPLETE_NEEDS_STRATEGY_PROBE"
            assert len(first_probe["questions"]) == 2
            assert first_probe["response_fields"] == (
                "strategy_choice",
                "substitution_left",
                "substitution_right",
            )
            assert all(
                set(choice) == {"id", "label"}
                for choice in first_probe["strategy_choices"]
            )
            left, right = _substitution_values(guided, answer)

            mismatched = MODULE.guided_repair(
                guided, answer, "OTHER_OR_UNSURE", left, right
            )
            assert mismatched["classification"] == "UNCLASSIFIED_NO_ANSWER_REVEAL"

            routed = [
                MODULE.guided_repair(
                    guided, answer, choice["id"], left, right
                )
                for choice in first_probe["strategy_choices"]
            ]
            matches = [result for result in routed if result["classification"] == code]
            assert len(matches) == 1
            support = matches[0]
            assert support["classification"] == code
            assert len(support["questions"]) == 2
            assert support["guided_explanation"]
            assert support["fresh_exit_family"] == MODULE.TRANSFER_PARTNER[family]

            inconsistent = MODULE.guided_repair(
                guided, answer, first_probe["strategy_choices"][0]["id"], "999", right
            )
            assert inconsistent["classification"] == "UNCLASSIFIED_NO_ANSWER_REVEAL"

        assert MODULE.guided_probe(guided, guided.answer) == {
            "classification": "CORRECT_NO_REMEDIATION",
            "questions": (),
        }


def test_ambiguous_and_unparseable_probe_evidence_fails_closed() -> None:
    ambiguous = None
    for seed in range(4_096):
        candidate = MODULE.generate(MODULE.FAMILIES[3], seed, "guided")
        for _, answer in candidate.misconception_answers:
            probe = MODULE.guided_probe(candidate, answer)
            if probe["candidate_count"] > 1:
                ambiguous = (candidate, answer, probe)
                break
        if ambiguous:
            break

    assert ambiguous is not None
    variant, answer, probe = ambiguous
    assert probe["classification"] == "EVIDENCE_INCOMPLETE_NEEDS_STRATEGY_PROBE"
    left, right = _substitution_values(variant, answer)
    neutral = MODULE.guided_repair(
        variant, answer, "OTHER_OR_UNSURE", left, right
    )
    assert neutral["classification"] == "UNCLASSIFIED_NO_ANSWER_REVEAL"

    unparseable = MODULE.guided_probe(variant, "not-a-number")
    assert unparseable["classification"] == "UNPARSEABLE_NEEDS_CLARIFICATION"
    assert "answer" not in unparseable


def test_support_isolated_from_diagnostic_independent_and_mastery_modes() -> None:
    for family in MODULE.FAMILIES:
        for mode in ("diagnostic", "independent", "mastery"):
            variant = MODULE.generate(family, 113, mode)
            observed = variant.misconception_answers[0][1]
            assert MODULE.guided_probe(variant, observed) is None
            assert MODULE.guided_repair(variant, observed, "ANY", "0", "0") is None


def test_diagnostic_path_is_unhinted_and_retains_verified_answer() -> None:
    variant = MODULE.generate(MODULE.FAMILIES[3], 137, "diagnostic")
    state = MODULE.start_learning_path(variant)
    payload = MODULE.stage_payload(variant, state)
    assert payload == {
        "stage": "DIAGNOSE",
        "instruction": "Solve the diagnostic item exactly without guided support.",
        "response_fields": ["exact_answer"],
        "support": "NONE_UNHINTED",
        "guided_repair_available": False,
    }

    with pytest.raises(ValueError, match="cannot unlock guided repair"):
        MODULE.advance_learning_path(variant, state, {"exact_answer": "999"})

    state = MODULE.advance_learning_path(
        variant, state, {"exact_answer": variant.answer}
    )
    assert state.stage == "TRANSFER"
    assert state.practiced_answer == variant.answer
    assert state.diagnosis_classification == "CORRECT_NO_REMEDIATION"

    transfer = MODULE.generate_transfer(variant)
    state = MODULE.advance_learning_path(
        variant,
        state,
        {
            "independent_variant_id": transfer.variant_id,
            "independent_answer": transfer.answer,
            "independent_family": transfer.family,
            "independent_mode": transfer.mode,
            "support_used": False,
        },
    )
    assert state.stage == "VERIFY"
    rhs = dict(variant.parameters)["rhs"]
    state = MODULE.advance_learning_path(
        variant,
        state,
        {"substitution_left": rhs, "substitution_right": rhs},
    )
    assert state.stage == "COMPLETE"


def test_guided_learning_path_locks_prediction_and_enforces_every_stage() -> None:
    guided = MODULE.generate(MODULE.FAMILIES[0], 211, "guided")
    state = MODULE.start_learning_path(guided)
    assert state.stages == MODULE.TEACHING_STAGES
    assert MODULE.stage_payload(guided, state)["stage"] == "OBSERVE"
    assert MODULE.stage_payload(guided, state)["reveals_inverse_operation"] is False

    state = MODULE.advance_learning_path(guided, state, {"observation": "Both sides are equal."})
    assert state.stage == "PREDICT"
    offset = Fraction(dict(guided.parameters)["offset"])
    operation = "SUBTRACT" if offset > 0 else "ADD"
    state = MODULE.advance_learning_path(guided, state, {"operation_choice": operation})
    assert state.stage == "MANIPULATE"
    assert state.prediction_locked is True
    with pytest.raises(ValueError, match="same nonempty operation"):
        MODULE.advance_learning_path(
            guided,
            state,
            {"left_operation": "SUBTRACT", "right_operation": "ADD"},
        )
    state = MODULE.advance_learning_path(
        guided,
        state,
        {
            "left_operation": operation,
            "right_operation": operation,
            "operation_value": str(abs(offset)),
            "resulting_x": guided.answer,
        },
    )
    state = MODULE.advance_learning_path(
        guided,
        state,
        {
            "reasoning_choice": "SAME_OPERATION_BOTH_SIDES",
            "equality_justification": (
                "The same operation on both complete sides keeps the values equal."
            ),
        },
    )
    state = MODULE.advance_learning_path(
        guided, state, {"exact_answer": guided.answer}
    )
    state = MODULE.advance_learning_path(
        guided,
        state,
        {"confirm_ready_for_transfer": True},
    )
    transfer = MODULE.generate_transfer(guided)
    state = MODULE.advance_learning_path(
        guided,
        state,
        {
            "independent_variant_id": transfer.variant_id,
            "independent_answer": transfer.answer,
            "independent_family": transfer.family,
            "independent_mode": transfer.mode,
            "support_used": False,
        },
    )
    state = MODULE.advance_learning_path(
        guided, state, {
            "substitution_left": dict(guided.parameters)["rhs"],
            "substitution_right": dict(guided.parameters)["rhs"],
        }
    )
    assert state.stage == "COMPLETE"
    assert state.completed == MODULE.TEACHING_STAGES


def test_independent_and_mastery_have_only_unhinted_practice_and_verify() -> None:
    for mode in ("independent", "mastery"):
        variant = MODULE.generate(MODULE.FAMILIES[9], 223, mode)
        state = MODULE.start_learning_path(variant)
        assert state.stages == ("PRACTICE", "VERIFY")
        first = MODULE.stage_payload(variant, state)
        assert first["support"] == "NONE_UNHINTED"
        assert "representation" not in first


def test_transfer_changes_structure_and_is_independent_unhinted() -> None:
    for family in MODULE.FAMILIES:
        for source_mode in ("diagnostic", "guided"):
            source = MODULE.generate(family, 127, source_mode)
            transfer = MODULE.generate_transfer(source)
            assert transfer.family == MODULE.TRANSFER_PARTNER[family]
            assert transfer.family != source.family
            assert transfer.structure != source.structure
            assert transfer.canonical_skill == source.canonical_skill
            assert transfer.mode == "independent"
            assert transfer.public_payload()["support"] == "NONE_UNHINTED"
            assert Fraction(transfer.answer) == _recompute(transfer)
        for blocked_mode in ("independent", "mastery"):
            with pytest.raises(ValueError, match="diagnostic or guided"):
                MODULE.generate_transfer(MODULE.generate(family, 127, blocked_mode))


def test_generation_has_no_persistence_or_application_imports() -> None:
    source = (PACKAGE / "generator.py").read_text()
    forbidden = (
        "SessionLocal",
        "sqlalchemy",
        "app.models",
        "Attempt",
        "DiagnosticAttempt",
        "MasteryEvent",
        "VariantHistory",
    )
    assert all(token not in source for token in forbidden)


@pytest.mark.parametrize(
    ("family", "seed", "mode", "error"),
    [
        ("UNKNOWN", 1, "guided", ValueError),
        (MODULE.FAMILIES[0], -1, "guided", ValueError),
        (MODULE.FAMILIES[0], True, "guided", TypeError),
        (MODULE.FAMILIES[0], 1, "production", ValueError),
    ],
)
def test_invalid_generation_fails_closed(
    family: str, seed: int, mode: str, error: type[Exception]
) -> None:
    with pytest.raises(error):
        MODULE.generate(family, seed, mode)



def test_fake_transfer_id_and_wrong_independent_answer_are_rejected() -> None:
    guided = MODULE.generate(MODULE.FAMILIES[0], 211, "guided")
    state = MODULE.LearningState(
        variant_id=guided.variant_id,
        mode="guided",
        stages=MODULE.TEACHING_STAGES,
        position=6,
        prediction_locked=True,
        practiced_answer=guided.answer,
    )
    transfer = MODULE.generate_transfer(guided)
    valid = {
        "independent_variant_id": transfer.variant_id,
        "independent_family": transfer.family,
        "independent_mode": "independent",
        "support_used": False,
        "independent_answer": transfer.answer,
    }
    with pytest.raises(ValueError, match="identifier"):
        MODULE.advance_learning_path(
            guided, state, valid | {"independent_variant_id": "fabricated-id"}
        )
    with pytest.raises(ValueError, match="did not solve"):
        MODULE.advance_learning_path(
            guided, state, valid | {"independent_answer": "999999"}
        )
    assert MODULE.advance_learning_path(guided, state, valid).stage == "VERIFY"


def test_equal_fabricated_verification_does_not_pass() -> None:
    guided = MODULE.generate(MODULE.FAMILIES[0], 211, "guided")
    state = MODULE.LearningState(
        variant_id=guided.variant_id,
        mode="guided",
        stages=MODULE.TEACHING_STAGES,
        position=7,
        prediction_locked=True,
        practiced_answer=guided.answer,
    )
    with pytest.raises(ValueError, match="original equation"):
        MODULE.advance_learning_path(
            guided, state, {"substitution_left": "5/2", "substitution_right": "5/2"}
        )


def test_fake_inverse_operation_and_wrong_result_are_rejected() -> None:
    guided = MODULE.generate(MODULE.FAMILIES[0], 211, "guided")
    state = MODULE.LearningState(
        variant_id=guided.variant_id,
        mode="guided",
        stages=MODULE.TEACHING_STAGES,
        position=2,
        prediction_locked=True,
    )
    offset = Fraction(dict(guided.parameters)["offset"])
    operation = "SUBTRACT" if offset > 0 else "ADD"
    base = {
        "left_operation": operation,
        "right_operation": operation,
        "operation_value": str(abs(offset)),
        "resulting_x": guided.answer,
    }
    with pytest.raises(ValueError, match="exact inverse"):
        MODULE.advance_learning_path(
            guided, state, base | {"operation_value": "not-a-rational"}
        )
    with pytest.raises(ValueError, match="exact inverse arithmetic"):
        MODULE.advance_learning_path(
            guided, state, base | {"resulting_x": "999"}
        )
    assert MODULE.advance_learning_path(guided, state, base).stage == "EXPLAIN"


def test_invalid_practice_answer_is_rejected() -> None:
    v = MODULE.generate(MODULE.FAMILIES[9], 223, "independent")
    state = MODULE.start_learning_path(v)
    with pytest.raises(ValueError, match="does not solve"):
        MODULE.advance_learning_path(v, state, {"exact_answer": "999"})
    state = MODULE.advance_learning_path(v, state, {"exact_answer": v.answer})
    p = dict(v.parameters)
    assert MODULE.advance_learning_path(
        v, state, {"substitution_left": p["rhs"], "substitution_right": p["rhs"]}
    ).stage == "COMPLETE"


def test_guided_practice_error_is_retained_as_diagnosis_evidence() -> None:
    guided = MODULE.generate(MODULE.FAMILIES[0], 211, "guided")
    state = MODULE.LearningState(
        variant_id=guided.variant_id,
        mode="guided",
        stages=MODULE.TEACHING_STAGES,
        position=4,
        prediction_locked=True,
    )
    code, wrong_answer = guided.misconception_answers[0]
    state = MODULE.advance_learning_path(
        guided, state, {"exact_answer": wrong_answer}
    )
    assert state.stage == "DIAGNOSE"
    assert state.practiced_answer == wrong_answer
    payload = MODULE.stage_payload(guided, state)
    assert "exact_answer" not in payload["response_fields"]

    observed = Fraction(wrong_answer)
    p = dict(guided.parameters)
    left = Fraction(p["coefficient"]) * observed + Fraction(p["offset"])
    repair = MODULE.advance_learning_path(
        guided,
        state,
        {
            "strategy_choice": MODULE._STRATEGY_OPTION[code][0],
            "substitution_left": str(left),
            "substitution_right": p["rhs"],
        },
    )
    assert repair.stage == "DIAGNOSE"
    assert repair.diagnosis_classification == code
    assert repair.practiced_answer == wrong_answer

    exited = MODULE.advance_learning_path(
        guided,
        repair,
        {
            "repair_reflection_choice": "APPLY_INVERSE_TO_BOTH_SIDES",
            "repair_exit_answer": guided.answer,
        },
    )
    assert exited.stage == "TRANSFER"
    assert exited.practiced_answer == guided.answer


def test_wrong_prediction_is_recorded_and_gets_socratic_retry() -> None:
    guided = MODULE.generate(MODULE.FAMILIES[0], 211, "guided")
    state = MODULE.start_learning_path(guided)
    state = MODULE.advance_learning_path(
        guided, state, {"observation": "The two expressions are equal."}
    )
    p = dict(guided.parameters)
    correct = "SUBTRACT" if Fraction(p["offset"]) > 0 else "ADD"
    wrong = next(
        choice
        for choice in ("ADD", "SUBTRACT", "MULTIPLY", "DIVIDE")
        if choice != correct
    )
    retry = MODULE.advance_learning_path(
        guided, state, {"operation_choice": wrong}
    )
    assert retry.stage == "PREDICT"
    assert retry.prediction_choice == wrong
    assert retry.prediction_locked is False
    payload = MODULE.stage_payload(guided, retry)
    assert payload["recorded_prediction"] == wrong
    assert "both complete sides" in payload["socratic_feedback"]
    corrected = MODULE.advance_learning_path(
        guided, retry, {"operation_choice": correct}
    )
    assert corrected.stage == "MANIPULATE"
    assert corrected.prediction_choice == correct
    assert corrected.prediction_locked is True


def test_irrelevant_explanation_cannot_complete_explain_stage() -> None:
    guided = MODULE.generate(MODULE.FAMILIES[0], 211, "guided")
    state = MODULE.LearningState(
        variant_id=guided.variant_id,
        mode="guided",
        stages=MODULE.TEACHING_STAGES,
        position=3,
        prediction_locked=True,
    )
    with pytest.raises(ValueError, match="both complete sides"):
        MODULE.advance_learning_path(
            guided,
            state,
            {
                "reasoning_choice": "MOVE_TERM_CHANGE_SIGN",
                "equality_justification": "I moved it because that is the rule.",
            },
        )
    advanced = MODULE.advance_learning_path(
        guided,
        state,
        {
            "reasoning_choice": "SAME_OPERATION_BOTH_SIDES",
            "equality_justification": (
                "Applying the same operation to both sides preserves equality."
            ),
        },
    )
    assert advanced.stage == "PRACTICE"
    assert "both sides" in advanced.explanation_evidence


def test_arbitrary_diagnosis_strings_remain_neutral_and_do_not_advance() -> None:
    guided = MODULE.generate(MODULE.FAMILIES[0], 211, "guided")
    _, wrong_answer = guided.misconception_answers[0]
    state = MODULE.LearningState(
        variant_id=guided.variant_id,
        mode="guided",
        stages=MODULE.TEACHING_STAGES,
        position=5,
        prediction_locked=True,
        practiced_answer=wrong_answer,
    )
    retry = MODULE.advance_learning_path(
        guided,
        state,
        {
            "strategy_choice": "nonsense",
            "substitution_left": "left",
            "substitution_right": "right",
        },
    )
    assert retry.stage == "DIAGNOSE"
    assert retry.diagnosis_classification == "NEUTRAL_RETRY"
    assert retry.diagnosis_feedback
    assert MODULE.stage_payload(guided, retry)["neutral_retry"]


def test_matched_diagnosis_requires_targeted_repair_exit() -> None:
    guided = MODULE.generate(MODULE.FAMILIES[0], 211, "guided")
    code, wrong_answer = guided.misconception_answers[0]
    state = MODULE.LearningState(
        variant_id=guided.variant_id,
        mode="guided",
        stages=MODULE.TEACHING_STAGES,
        position=5,
        prediction_locked=True,
        practiced_answer=wrong_answer,
    )
    observed = Fraction(wrong_answer)
    p = dict(guided.parameters)
    left = Fraction(p["coefficient"]) * observed + Fraction(p["offset"])
    right = Fraction(p["rhs"])
    repair = MODULE.advance_learning_path(
        guided,
        state,
        {
            "strategy_choice": MODULE._STRATEGY_OPTION[code][0],
            "substitution_left": str(left),
            "substitution_right": str(right),
        },
    )
    assert repair.stage == "DIAGNOSE"
    assert repair.diagnosis_classification == code
    repair_payload = MODULE.stage_payload(guided, repair)
    assert repair_payload["phase"] == "TARGETED_REPAIR_EXIT"
    assert repair_payload["guided_support"]
    with pytest.raises(ValueError, match="repair exit"):
        MODULE.advance_learning_path(
            guided,
            repair,
            {
                "repair_reflection_choice": "APPLY_INVERSE_TO_BOTH_SIDES",
                "repair_exit_answer": wrong_answer,
            },
        )
    exited = MODULE.advance_learning_path(
        guided,
        repair,
        {
            "repair_reflection_choice": "APPLY_INVERSE_TO_BOTH_SIDES",
            "repair_exit_answer": guided.answer,
        },
    )
    assert exited.stage == "TRANSFER"
    assert exited.repair_completed is True
    assert exited.practiced_answer == guided.answer


