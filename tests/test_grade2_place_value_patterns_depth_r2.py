"""Exact deterministic checks for the bounded Grade 2 depth revision."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs/curriculum/drafts/grade2-gap-closure-wave1"
MODULE_PATH = DRAFT / "place_value_patterns_depth_r2.py"
SPEC = importlib.util.spec_from_file_location("g2_place_pattern_depth_r2", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_revision_and_provenance_remain_fail_closed() -> None:
    manifest = json.loads((DRAFT / "question_depth_r2.package.json").read_text())
    assert MODULE.STATUS == manifest["status"] == "DRAFT_UNVERIFIED"
    assert MODULE.RUNTIME_ACTIVATION is manifest["runtime_activation"] is False
    assert manifest["mastery_writes"] is False
    assert manifest["audit_evidence"]["stored_distinct_tasks_per_local_row"] == 3
    assert manifest["audit_evidence"]["learner_visible_integrated_status"] == "NOT_VERIFIED"
    assert {item["authority"] for item in manifest["canonical_boundaries"]} == {
        "UNKNOWN_NOT_APPROVED"
    }
    assert all(status != "APPROVED" for status in manifest["review_gates"].values())


@pytest.mark.parametrize("concept", MODULE.CONCEPTS)
@pytest.mark.parametrize("mode", MODULE.MODES)
def test_all_modes_are_deterministic_varied_and_answer_isolated(concept, mode) -> None:
    families = set()
    prompts = set()
    for seed in range(84):
        first = MODULE.generate(concept, seed, mode)
        assert first == MODULE.generate(concept, seed, mode)
        assert first.teacher_oracle()
        assert set(first.misconception_responses) == set(first.socratic_repairs)
        public = first.public_payload()
        assert "oracle" not in public
        assert "misconception_responses" not in public
        assert "socratic_repairs" not in public
        assert "answer" not in public
        families.add(first.family_code)
        prompts.add(first.prompt)
    expected = set(
        MODULE.PLACE_FAMILIES if concept == MODULE.PLACE_CONCEPT else MODULE.PATTERN_FAMILIES
    )
    assert families == expected
    assert len(prompts) >= 40


def test_mode_namespaces_change_family_and_identity() -> None:
    for concept in MODULE.CONCEPTS:
        for seed in range(84):
            variants = [MODULE.generate(concept, seed, mode) for mode in MODULE.MODES]
            assert len({item.item_id for item in variants}) == len(MODULE.MODES)
            assert len({item.family_code for item in variants}) == len(MODULE.MODES)
            assert len({item.prompt for item in variants}) == len(MODULE.MODES)


def test_place_value_oracles_reconstruct_exact_quantities() -> None:
    for mode in MODULE.MODES:
        for seed in range(280):
            item = MODULE.generate(MODULE.PLACE_CONCEPT, seed, mode)
            oracle = item.teacher_oracle()
            if item.family_code == "COMPOSE_NONSTANDARD_COUNTS":
                h, t, o = oracle["given_inventory"]
                assert oracle["value"] == oracle["reconstruction"] == 100 * h + 10 * t + o
                ch, ct, co = oracle["canonical_inventory"]
                assert oracle["value"] == 100 * ch + 10 * ct + co
                assert 0 <= ct < 10 and 0 <= co < 10
            elif item.family_code == "REPRESENTATION_TRANSLATION":
                assert sum(oracle["expanded_terms"]) == oracle["standard"]
                h, t, o = oracle["inventory"]
                assert oracle["reconstruction"] == 100 * h + 10 * t + o == oracle["standard"]
            elif item.family_code == "REPEATED_DIGIT_VALUE":
                assert oracle["left_value"] == 100 * oracle["right_value"]
                assert oracle["factor"] == 100
            elif item.family_code == "EXCHANGE_HUNDRED_TENS":
                before_h, before_t, before_o = oracle["before"]
                after_h, after_t, after_o = oracle["after"]
                assert (after_h, after_t, after_o) == (before_h - 1, before_t + 10, before_o)
                assert oracle["before_total"] == oracle["after_total"]
            elif item.family_code == "COMPARE_FIRST_DIFFERENCE":
                expected = ">" if oracle["left"] > oracle["right"] else "<"
                assert oracle["relation"] == expected
                assert oracle["first_differing_place"] == "tens"
                assert item.misconception_responses["COMPARE_ONES_FIRST"] != expected
            elif item.family_code == "ORDER_RETAIN_DUPLICATES":
                assert tuple(sorted(oracle["ordered"])) == oracle["ordered"]
                assert oracle["input_count"] == oracle["output_count"] == 4
                assert len(item.misconception_responses["DROP_DUPLICATE"]) < 4
            else:
                h, t, o = oracle["canonical_inventory"]
                assert oracle["total"] == oracle["substitution_total"] == 100 * h + 10 * t + o


def test_pattern_oracles_reconstruct_exact_sequences_and_transfer() -> None:
    for mode in MODULE.MODES:
        for seed in range(280):
            item = MODULE.generate(MODULE.PATTERN_CONCEPT, seed, mode)
            oracle = item.teacher_oracle()
            if item.family_code == "EXTEND_FORWARD":
                sequence = oracle["sequence"]
                assert all(sequence[i + 1] - sequence[i] == oracle["step"] for i in range(5))
            elif item.family_code == "EXTEND_BACKWARD":
                sequence = oracle["sequence"]
                assert all(sequence[i + 1] - sequence[i] == oracle["signed_step"] for i in range(5))
                assert oracle["signed_step"] < 0
                assert min(sequence) >= 0
                assert item.visual_model["direction"] == "backward"
                assert item.visual_model["step_size"] == abs(oracle["signed_step"])
                assert "signed_step" not in item.response_fields
            elif item.family_code == "MISSING_INTERNAL_TERM":
                assert oracle["missing_term"] == oracle["left_check"] == oracle["right_check"]
            elif item.family_code == "INFER_CONSTANT_STEP":
                assert len(set(oracle["differences"])) == 1
                assert oracle["differences"][0] == oracle["step"]
            elif item.family_code == "REPAIR_BROKEN_TERM":
                assert oracle["left_difference"] == oracle["right_difference"]
                assert oracle["incorrect_term"] != oracle["corrected_term"]
            elif item.family_code == "PLACE_VALUE_CHANGE":
                sequence = oracle["sequence"]
                assert all(sequence[i + 1] - sequence[i] == 100 for i in range(4))
                assert oracle["changing_place"] == "hundreds"
            else:
                arrivals = oracle["arrivals"]
                assert oracle["previous_arrival"] == arrivals[-2]
                assert oracle["elapsed_first_to_last"] == arrivals[-1] - arrivals[0]
                assert oracle["interval_count"] == len(arrivals) - 1


def test_misconception_responses_never_collide_with_scored_answers() -> None:
    for mode in MODULE.MODES:
        for seed in range(210):
            place = MODULE.generate(MODULE.PLACE_CONCEPT, seed, mode)
            place_oracle = place.teacher_oracle()
            place_wrong = next(iter(place.misconception_responses.values()))
            if place.family_code == "COMPOSE_NONSTANDARD_COUNTS":
                assert place_wrong != place_oracle["value"]
            elif place.family_code == "REPRESENTATION_TRANSLATION":
                assert place_wrong != place_oracle["standard"]
            elif place.family_code == "REPEATED_DIGIT_VALUE":
                assert place_wrong != (
                    place_oracle["left_value"],
                    place_oracle["right_value"],
                )
            elif place.family_code == "EXCHANGE_HUNDRED_TENS":
                assert place_wrong not in {
                    place_oracle["before_total"],
                    place_oracle["after_total"],
                }
            elif place.family_code == "COMPARE_FIRST_DIFFERENCE":
                assert place_wrong != place_oracle["relation"]
            elif place.family_code == "ORDER_RETAIN_DUPLICATES":
                assert place_wrong != place_oracle["ordered"]
            else:
                assert place_wrong != place_oracle["total"]

            pattern = MODULE.generate(MODULE.PATTERN_CONCEPT, seed, mode)
            pattern_oracle = pattern.teacher_oracle()
            pattern_wrong = next(iter(pattern.misconception_responses.values()))
            if pattern.family_code in {"EXTEND_FORWARD", "EXTEND_BACKWARD"}:
                assert pattern_wrong != pattern_oracle["sequence"]
            elif pattern.family_code == "MISSING_INTERNAL_TERM":
                assert pattern_wrong != pattern_oracle["missing_term"]
            elif pattern.family_code == "INFER_CONSTANT_STEP":
                assert pattern_wrong != pattern_oracle["step"]
            elif pattern.family_code == "REPAIR_BROKEN_TERM":
                assert pattern_wrong != pattern_oracle["left_difference"]
            elif pattern.family_code == "PLACE_VALUE_CHANGE":
                assert pattern_wrong != pattern_oracle["changing_place"]
            else:
                assert pattern_wrong != pattern_oracle["elapsed_first_to_last"]


def test_guided_support_routes_only_matching_misconceptions() -> None:
    for concept in MODULE.CONCEPTS:
        for seed in range(84):
            guided = MODULE.generate(concept, seed, "guided")
            code, response = next(iter(guided.misconception_responses.items()))
            support = guided.guided_support_for_response(response)
            assert support == {
                "misconception_code": code,
                "socratic_prompt": guided.socratic_repairs[code],
            }
            assert guided.guided_support_for_response(object()) is None
            assert "oracle" not in support
            assert "answer" not in support


@pytest.mark.parametrize("mode", ("diagnostic", "independent", "mastery"))
def test_non_guided_modes_never_expose_support(mode) -> None:
    for concept in MODULE.CONCEPTS:
        for seed in range(84):
            item = MODULE.generate(concept, seed, mode)
            response = next(iter(item.misconception_responses.values()))
            assert item.guided_support_for_response(response) is None
            public = item.public_payload()
            assert "support" not in public
            assert "socratic_prompt" not in public


def test_backward_sequences_remain_in_grade2_whole_number_domain() -> None:
    for mode in MODULE.MODES:
        for seed in range(10_000):
            item = MODULE.generate(MODULE.PATTERN_CONCEPT, seed, mode)
            if item.family_code != "EXTEND_BACKWARD":
                continue
            sequence = item.teacher_oracle()["sequence"]
            assert min(sequence) >= 0
            assert "-" not in item.prompt
            assert all(value >= 0 for value in item.visual_model.values() if isinstance(value, int))


def test_accessibility_contract_is_explicit_for_every_family() -> None:
    for concept in MODULE.CONCEPTS:
        for seed in range(84):
            interaction = MODULE.generate(concept, seed, "guided").interaction
            assert "Tab" in interaction["keyboard"]
            assert "arrow keys" in interaction["keyboard"]
            assert interaction["screen_reader_state_template"]
            assert interaction["focus_after_feedback"]
            assert interaction["reduced_motion"] is True
            assert interaction["color_only_meaning"] is False


@pytest.mark.parametrize(
    ("concept", "seed", "mode", "error"),
    [
        ("UNKNOWN", 0, "guided", ValueError),
        (MODULE.PLACE_CONCEPT, -1, "guided", ValueError),
        (MODULE.PATTERN_CONCEPT, True, "guided", TypeError),
        (MODULE.PATTERN_CONCEPT, 0, "assessment", ValueError),
    ],
)
def test_invalid_generation_fails_closed(concept, seed, mode, error) -> None:
    with pytest.raises(error):
        MODULE.generate(concept, seed, mode)


def test_draft_module_is_not_imported_by_runtime() -> None:
    for path in (ROOT / "app").rglob("*.py"):
        assert "place_value_patterns_depth_r2" not in path.read_text()
