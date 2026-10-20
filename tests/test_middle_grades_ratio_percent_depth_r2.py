from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/curriculum/drafts/canonical-middle-grades-ratio-percent-depth-r2"
SPEC = importlib.util.spec_from_file_location(
    "middle_grades_ratio_percent_r2", PACKAGE / "generator.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _fraction(value: str) -> Fraction:
    return Fraction(value)


def _independent_answer(variant) -> str:
    p = dict(variant.parameters)
    family = variant.family
    if family == "MATH.RATIO.EQUIVALENT":
        return str(p["b"] * p["scale"])
    if family == "MATH.RATIO.PART_WHOLE":
        return str(Fraction(p["first_parts"], p["first_parts"] + p["second_parts"]) * p["total"])
    if family == "MATH.RATIO.TABLE.MISSING":
        return str(p["b"] * p["target_scale"])
    if family == "MATH.RATIO.RECIPE":
        return str(p["cups_per_batch"] * p["batches"])
    if family == "MATH.RATE.UNIT":
        return str(Fraction(p["total"], p["quantity"]))
    if family == "MATH.RATE.COMPARE":
        rate_a = Fraction(p["cost_a_numerator"], p["cost_a_denominator"]) / p["quantity_a"]
        rate_b = Fraction(p["cost_b_numerator"], p["cost_b_denominator"]) / p["quantity_b"]
        return "A" if rate_a < rate_b else "B"
    if family == "MATH.PCT.OF_QUANTITY":
        return str(Fraction(p["percent"], 100) * p["whole"])
    if family == "MATH.PCT.FIND_WHOLE":
        return str(Fraction(p["part"] * 100, p["percent"]))
    if family == "MATH.PCT.DISCOUNT":
        return str(Fraction(p["original"] * (100 - p["percent"]), 100))
    if family == "MATH.PCT.INCREASE":
        return str(Fraction(p["original"] * (100 + p["percent"]), 100))
    raise AssertionError(family)


def test_package_is_draft_runtime_disabled_and_history_neutral() -> None:
    manifest = json.loads((PACKAGE / "package.json").read_text())
    assert manifest["status"] == "DRAFT_UNVERIFIED"
    assert manifest["runtime_activation"] is False
    assert manifest["mastery_writes"] is False
    assert manifest["scope"]["jurisdiction_identity_created"] is False
    assert manifest["scope"]["local_mapping_changed"] is False
    assert manifest["reuse_first_audit"]["learner_visible_availability"] == "NOT_VERIFIED"
    assert manifest["canonical_reuse"]["dc_va_grade8_mapping_activated"] is False
    assert set(manifest["persistence_boundary"].values()) >= {False}
    assert all(
        manifest["persistence_boundary"][key] is False
        for key in (
            "registered_by_app",
            "seeded",
            "selector_or_scorer_changed",
            "learner_records_changed",
            "attempt_records_changed",
            "diagnostic_attempt_records_changed",
            "mastery_events_changed",
            "variant_history_changed",
        )
    )


def test_registered_family_skill_relationships_are_reused_exactly() -> None:
    from app.domains.percent import FAMILIES as PERCENT_FAMILIES
    from app.domains.ratios import FAMILIES as RATIO_FAMILIES

    registry = RATIO_FAMILIES | PERCENT_FAMILIES
    assert set(MODULE.FAMILIES) == set(MODULE.CANONICAL_SKILL)
    for family in MODULE.FAMILIES:
        assert family in registry
        assert registry[family].canonical_skill_code == MODULE.CANONICAL_SKILL[family]


@pytest.mark.parametrize("mode", sorted(MODULE.MODES))
def test_generation_is_deterministic_diverse_and_exact(mode: str) -> None:
    for family in MODULE.FAMILIES:
        variants = [MODULE.generate(family, seed, mode) for seed in range(128)]
        assert variants == [MODULE.generate(family, seed, mode) for seed in range(128)]
        assert len({variant.variant_id for variant in variants}) == 128
        assert len({variant.parameters for variant in variants}) >= 8
        for variant in variants:
            assert variant.answer == _independent_answer(variant)
            assert variant.structure
            assert len(variant.representation) == 3
            assert MODULE.verification_equation(variant)
            assert variant.answer not in dict(variant.misconception_answers).values()


def test_ten_families_have_distinct_structures_and_three_stage_representations() -> None:
    variants = [MODULE.generate(family, 41, "guided") for family in MODULE.FAMILIES]
    assert len({variant.structure for variant in variants}) == len(MODULE.FAMILIES) == 10
    assert all(
        tuple(map(bool, variant.representation)) == (True, True, True) for variant in variants
    )
    assert all("Concrete:" in variant.representation[0] for variant in variants)
    assert all("Visual:" in variant.representation[1] for variant in variants)
    assert all("Symbolic:" in variant.representation[2] for variant in variants)


def test_public_payload_is_answer_free_and_accessible() -> None:
    forbidden = {"answer", "oracle", "parameters", "misconception_answers", "verification"}
    for family in MODULE.FAMILIES:
        for mode in MODULE.MODES:
            variant = MODULE.generate(family, 73, mode)
            public = variant.public_payload()
            assert forbidden.isdisjoint(public)
            assert public["response_fields"] == ["exact_answer", "unit", "reasoning"]
            assert set(public["accessibility"]) == {
                "keyboard",
                "screen_reader",
                "visual",
                "motion",
                "input",
            }


def test_guided_observed_answers_select_specific_support_only() -> None:
    for family in MODULE.FAMILIES:
        guided = MODULE.generate(family, 97, "guided")
        for code, answer in guided.misconception_answers:
            support = MODULE.guided_repair(guided, answer)
            assert support and support["classification"] == code
            assert len(support["questions"]) == 2
            assert support["fresh_exit_family"] == MODULE.TRANSFER_PARTNER[family]
        assert MODULE.guided_repair(guided, guided.answer) == {
            "classification": "CORRECT_NO_REMEDIATION",
            "questions": (),
        }
        for mode in ("diagnostic", "independent", "mastery"):
            isolated = MODULE.generate(family, 97, mode)
            assert MODULE.guided_repair(isolated, "not-the-answer") is None


def test_ambiguous_guided_signatures_use_neutral_fail_closed_support() -> None:
    ambiguous_counts = {}

    for family in MODULE.FAMILIES:
        count = 0
        for seed in range(2_048):
            guided = MODULE.generate(family, seed, "guided")
            grouped = {}
            for code, answer in guided.misconception_answers:
                normalized = answer.upper() if guided.answer_kind == "choice" else answer
                grouped.setdefault(normalized, []).append(code)

            for submitted, codes in grouped.items():
                support = MODULE.guided_repair(guided, submitted)
                assert support is not None
                if len(codes) == 1:
                    assert support["classification"] == codes[0]
                else:
                    count += 1
                    assert support["classification"] == "AMBIGUOUS_RESPONSE_NEEDS_REASONING"
                    assert len(support["questions"]) == 2
                    assert support["fresh_exit_family"] == MODULE.TRANSFER_PARTNER[family]
                    assert all(code not in support.values() for code in codes)

        if count:
            ambiguous_counts[family] = count

    assert ambiguous_counts == {
        "MATH.RATIO.TABLE.MISSING": 97,
        "MATH.RATE.COMPARE": 790,
    }



def test_transfer_changes_family_and_is_independent_hint_free() -> None:
    for family in MODULE.FAMILIES:
        for source_mode in ("diagnostic", "guided"):
            source = MODULE.generate(family, 113, source_mode)
            transfer = MODULE.generate_transfer(source)
            assert transfer.family == MODULE.TRANSFER_PARTNER[family]
            assert transfer.family != source.family
            assert transfer.mode == "independent"
            assert transfer.answer == _independent_answer(transfer)
            assert "questions" not in transfer.public_payload()
        for blocked_mode in ("independent", "mastery"):
            with pytest.raises(ValueError, match="diagnostic or guided"):
                MODULE.generate_transfer(MODULE.generate(family, 113, blocked_mode))


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
