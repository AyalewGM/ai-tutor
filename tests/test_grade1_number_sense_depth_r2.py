"""Exact, deterministic checks for the bounded Grade 1 depth revision."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "docs/curriculum/drafts/grade1-gap-closure-wave1/number_sense_depth_r2.py"
SPEC = importlib.util.spec_from_file_location("g1_number_place_depth_r2", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_revision_is_draft_only_and_not_runtime_activated() -> None:
    assert MODULE.STATUS == "DRAFT_UNVERIFIED"
    assert MODULE.RUNTIME_ACTIVATION is False
    assert set(MODULE.CONCEPTS) == {
        "G1-COUNT-REPRESENT",
        "G1-PLACE-VALUE",
    }


@pytest.mark.parametrize("concept", MODULE.CONCEPTS)
@pytest.mark.parametrize("mode", MODULE.MODES)
def test_all_modes_are_deterministic_varied_and_answer_isolated(concept, mode) -> None:
    prompts = set()
    families = set()
    for seed in range(72):
        first = MODULE.generate(concept, seed, mode)
        retry = MODULE.generate(concept, seed, mode)
        assert first == retry
        assert first.teacher_oracle()
        assert set(first.socratic_repairs) == set(first.misconception_responses)
        public = first.public_payload()
        assert "oracle" not in public
        assert "misconception_responses" not in public
        assert "socratic_repairs" not in public
        assert "answer" not in public
        prompts.add(first.prompt)
        families.add(first.family_code)
    expected = (
        set(MODULE.COUNT_FAMILIES)
        if concept == MODULE.COUNT_CONCEPT
        else set(MODULE.PLACE_FAMILIES)
    )
    assert families == expected
    assert len(prompts) >= 24


def test_mode_namespaces_and_fresh_transfer_change_structure() -> None:
    for concept in MODULE.CONCEPTS:
        for seed in range(72):
            guided = MODULE.generate(concept, seed, "guided")
            independent = MODULE.generate(concept, seed, "independent")
            mastery = MODULE.generate(concept, seed, "mastery")
            assert len({guided.item_id, independent.item_id, mastery.item_id}) == 3
            assert guided.family_code != independent.family_code
            assert independent.family_code != mastery.family_code
            assert guided.prompt != independent.prompt


def test_count_family_oracles_reconstruct_exact_requested_results() -> None:
    for mode in MODULE.MODES:
        for seed in range(180):
            item = MODULE.generate(MODULE.COUNT_CONCEPT, seed, mode)
            oracle = item.teacher_oracle()
            if item.family_code == "QUANTITY_TO_NUMERAL":
                assert (
                    oracle["reconstruction"]["tens_value"] + oracle["reconstruction"]["ones_value"]
                    == oracle["numeral"]
                )
            elif item.family_code == "COUNT_ON_CROSS_DECADE":
                sequence = oracle["sequence"]
                assert all(step == 1 for step in oracle["step_checks"])
                assert oracle["missing_number"] in sequence[1:-1]
            elif item.family_code == "COMPARE_BY_PLACE":
                left = 10 * oracle["left_tens"] + oracle["left_ones"]
                right = 10 * oracle["right_tens"] + oracle["right_ones"]
                assert oracle["relation"] == (">" if left > right else "<")
                assert item.misconception_responses["COMPARE_DIGITS_ONLY"] != oracle["relation"]
            elif item.family_code == "ORDER_RETAIN_DUPLICATES":
                ordered = oracle["ordered"]
                assert list(ordered) == sorted(ordered)
                assert len(ordered) == oracle["input_count"] == oracle["output_count"] == 4
                assert len(item.misconception_responses["ORDER_DROPS_DUPLICATE"]) < 4
            else:
                assert oracle["one_less"] + 1 == oracle["center"]
                assert oracle["one_more"] - 1 == oracle["center"]
                assert item.misconception_responses["BOUNDARY_DIGIT_RESET"] != {
                    "one_less": oracle["one_less"],
                    "one_more": oracle["one_more"],
                }


def test_place_value_family_oracles_reconstruct_exact_requested_results() -> None:
    for mode in MODULE.MODES:
        for seed in range(216):
            item = MODULE.generate(MODULE.PLACE_CONCEPT, seed, mode)
            oracle = item.teacher_oracle()
            if item.family_code == "COMPOSE_BASE_TEN":
                visual = item.visual_model
                assert 10 * visual["tens"] + visual["ones"] == oracle["numeral"]
            elif item.family_code == "DECOMPOSE_BASE_TEN":
                assert 10 * oracle["tens"] + oracle["ones"] == oracle["reconstruction"]
                assert item.misconception_responses["TEEN_TEN"] != {
                    "tens": oracle["tens"],
                    "ones": oracle["ones"],
                }
            elif item.family_code == "DIGIT_VALUE":
                expected = oracle["digit"] * (10 if oracle["place"] == "tens" else 1)
                assert oracle["digit_value"] == expected
                assert item.misconception_responses["FACE_VALUE_ONLY"] != expected
            elif item.family_code == "EXCHANGE_INVARIANCE":
                assert oracle["before"]["total"] == oracle["after"]["total"]
                assert oracle["before"]["tens"] - 1 == oracle["after"]["tens"]
                assert oracle["before"]["ones"] + 10 == oracle["after"]["ones"]
                assert oracle["difference"] == 0
            elif item.family_code == "TEEN_VS_MULTIPLE_TEN":
                assert oracle["teen"]["value"] == 10 + oracle["teen"]["ones"]
                assert oracle["multiple_ten"]["value"] == 10 * oracle["multiple_ten"]["tens"]
                assert oracle["teen"]["value"] != oracle["multiple_ten"]["value"]
            else:
                assert oracle["value"] == 10 * oracle["tens"]
                assert oracle["ones"] == 0
                assert oracle["zero_placeholder"] is True


def test_accessibility_contract_is_explicit_for_every_family() -> None:
    for concept in MODULE.CONCEPTS:
        for seed in range(72):
            interaction = MODULE.generate(concept, seed, "guided").interaction
            assert "Tab" in interaction["keyboard"]
            assert "arrow keys" in interaction["keyboard"]
            assert interaction["screen_reader_state_template"]
            assert interaction["reduced_motion"] is True
            assert interaction["color_only_meaning"] is False
            assert interaction["focus_after_feedback"]


@pytest.mark.parametrize(
    ("concept", "seed", "mode", "error"),
    [
        ("UNKNOWN", 0, "guided", ValueError),
        (MODULE.COUNT_CONCEPT, -1, "guided", ValueError),
        (MODULE.COUNT_CONCEPT, True, "guided", TypeError),
        (MODULE.PLACE_CONCEPT, 0, "assessment", ValueError),
    ],
)
def test_invalid_generation_fails_closed(concept, seed, mode, error) -> None:
    with pytest.raises(error):
        MODULE.generate(concept, seed, mode)
