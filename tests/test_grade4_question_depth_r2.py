from __future__ import annotations

import importlib.util
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "docs/curriculum/drafts/grade4-gap-closure-wave1"
PACKAGE = json.loads((PACKAGE_DIR / "package.json").read_text(encoding="utf-8"))
SPEC = importlib.util.spec_from_file_location(
    "grade4_question_depth_r2", PACKAGE_DIR / "question_depth_r2.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _numbers(prompt: str) -> list[int]:
    return [int(value.replace(",", "")) for value in re.findall(r"\d[\d,]*", prompt)]


def _fraction_value(text: str) -> Fraction:
    return Fraction(text)


def _reconstruct_answer(variant) -> str:
    prompt = variant.prompt
    family = variant.family_code
    if family == "MATH.FRAC.UNIT.MEANING":
        denominator = _numbers(prompt)[0]
        return f"1/{denominator}"
    if family == "MATH.FRAC.NUMBER_LINE":
        match = re.search(r"divided into (\d+) equal parts.*mark (\d+) after 0", prompt)
        assert match
        denominator, numerator = map(int, match.groups())
        return f"{numerator}/{denominator}"
    if family == "MATH.FRAC.COMPARE.SAME_NUMERATOR":
        n1, d1, n2, d2 = _numbers(prompt)[:4]
        return f"{n1}/{d1}" if Fraction(n1, d1) > Fraction(n2, d2) else f"{n2}/{d2}"
    if family == "MATH.FRAC.ERROR.BIGGER_DENOM":
        return "A"
    if family in {"MATH.DEC.FRACTION.TENTHS", "MATH.DEC.FRACTION.HUNDREDTHS"}:
        numerator, denominator = _numbers(prompt)[:2]
        return f"{float(Fraction(numerator, denominator)):g}"
    if family == "MATH.DEC.ORDER":
        values = [float(value) for value in re.findall(r"\d+\.\d+", prompt)]
        return ",".join(f"{value:.2f}" for value in sorted(values))
    if family == "MATH.DEC.ERROR.ALIGN":
        return "A"
    values = _numbers(prompt)
    if family == "MATH.ADD.WORD.MULTISTEP":
        return f"{sum(values[:3]):,}"
    if family == "MATH.SUB.WORD.MULTISTEP":
        return f"{values[0] - values[1] - values[2]:,}"
    if family == "MATH.MUL.WORD.MULTISTEP":
        packs, per_pack, extra = values[:3]
        return str(packs * per_pack + extra)
    if family == "MATH.DIV.WORD.MULTISTEP":
        first, second, groups = values[:3]
        return str((first + second) // groups)
    raise AssertionError(f"unhandled family {family}")


def test_manifest_records_measured_gap_provenance_and_fail_closed_state() -> None:
    depth = PACKAGE["question_depth_r2"]
    assert depth["revision"] == "R2.0"
    assert depth["audit_evidence"]["source_pr"] == 447
    assert depth["audit_evidence"]["source_sha"] == "195806169943268a5d2d7878a34834c39d92f7a7"
    assert depth["audit_evidence"]["stored_distinct_tasks_per_local_skill"] == 4
    assert depth["mapping_approval"] == "UNKNOWN_NOT_REASSESSED"
    assert depth["runtime_activation"] is False
    assert depth["learner_visible_availability"] == "NOT_VERIFIED"
    assert PACKAGE["runtime_activation"] is False
    assert PACKAGE["mastery_writes"] is False


@pytest.mark.parametrize("concept_id", MODULE.CONCEPT_FAMILIES)
@pytest.mark.parametrize("mode", MODULE.MODES)
def test_two_pass_generation_is_idempotent_and_exact(concept_id: str, mode: str) -> None:
    first = [MODULE.generate(concept_id, seed, mode) for seed in range(128)]
    second = [MODULE.generate(concept_id, seed, mode) for seed in range(128)]
    assert first == second
    for variant in first:
        assert _reconstruct_answer(variant) == variant.teacher_oracle()["canonical_answer"]
        assert variant.canonical_answer not in dict(variant.misconceptions).values()


def test_all_twelve_families_are_sampled_in_every_mode() -> None:
    for concept_id, families in MODULE.CONCEPT_FAMILIES.items():
        for mode in MODULE.MODES:
            observed = {MODULE.generate(concept_id, seed, mode).family_code for seed in range(12)}
            assert observed == set(families)


def test_same_seed_modes_use_different_mathematics_and_item_ids() -> None:
    for concept_id in MODULE.CONCEPT_FAMILIES:
        for seed in range(64):
            variants = [MODULE.generate(concept_id, seed, mode) for mode in MODULE.MODES]
            assert len({variant.family_code for variant in variants}) == 4
            assert len({variant.item_id for variant in variants}) == 4
            assert len({variant.prompt for variant in variants}) == 4


def test_public_payload_is_answer_free_and_accessible() -> None:
    forbidden = {"canonical_answer", "answer", "oracle", "misconception_answers", "seed"}
    for concept_id in MODULE.CONCEPT_FAMILIES:
        for mode in MODULE.MODES:
            payload = MODULE.generate(concept_id, 23, mode).public_payload()
            assert not forbidden.intersection(payload)
            assert payload["support_prompts"] == []
            contract = payload["visual_contract"]
            assert not {
                "answer",
                "value",
                "numerator",
                "denominator",
                "aria_label",
            }.intersection(contract)
            assert "no values are prefilled" in contract["learner_action"]
            assert contract["keyboard_order"] == payload["response_fields"]
            assert contract["focus_after_feedback"]
            assert contract["reduced_motion"]
            assert contract["non_colour_equivalent"]


def test_guided_observed_errors_receive_specific_fresh_repairs_only() -> None:
    seen_codes = set()
    for concept_id in MODULE.CONCEPT_FAMILIES:
        for seed in range(48):
            guided = MODULE.generate(concept_id, seed, "guided")
            for code, response in guided.misconceptions:
                support = MODULE.guided_support_for_response(guided, response)
                assert support is not None
                assert support["misconception_code"] == code
                assert "?" in support["socratic_question"]
                repair = support["repair_task"]
                assert repair["family_code"] != guided.family_code
                assert repair["prompt"] != guided.prompt
                assert repair["mode"] == "guided"
                assert repair["support_prompts"] == []
                assert not {"answer", "oracle", "seed"}.intersection(repair)
                seen_codes.add(code)
            assert MODULE.guided_support_for_response(guided, "not a declared response") is None
            for mode in ("diagnostic", "independent", "mastery"):
                variant = MODULE.generate(concept_id, seed, mode)
                if variant.misconceptions:
                    assert (
                        MODULE.guided_support_for_response(variant, variant.misconceptions[0][1])
                        is None
                    )
    assert seen_codes == set(MODULE._SOCRATIC_QUESTIONS)


def test_independent_transfer_changes_family_and_hides_support() -> None:
    for concept_id in MODULE.CONCEPT_FAMILIES:
        for seed in range(96):
            source = MODULE.generate(concept_id, seed, "guided")
            transfer = MODULE.independent_transfer(source, seed + 50_000)
            assert transfer.mode == "independent"
            assert transfer.family_code != source.family_code
            assert transfer.prompt != source.prompt
            assert transfer.public_payload()["support_prompts"] == []
            assert _reconstruct_answer(transfer) == transfer.canonical_answer


@pytest.mark.parametrize(
    "args,error",
    [
        (("UNKNOWN", 0, "guided"), ValueError),
        (("G4-FRACTIONS", -1, "guided"), ValueError),
        (("G4-FRACTIONS", True, "guided"), TypeError),
        (("G4-FRACTIONS", 0, "review"), ValueError),
    ],
)
def test_invalid_generation_fails_closed(args, error) -> None:
    with pytest.raises(error):
        MODULE.generate(*args)


def test_no_runtime_or_history_write_surface() -> None:
    source = (PACKAGE_DIR / "question_depth_r2.py").read_text(encoding="utf-8")
    forbidden = (
        "from app.models",
        "import app.models",
        "Session(",
        ".add(",
        ".commit(",
        "Attempt(",
        "DiagnosticAttempt(",
        "MasteryEvent(",
    )
    assert not any(token in source for token in forbidden)
    assert MODULE.RUNTIME_ACTIVATION is False
    assert MODULE.MASTERY_WRITES is False
