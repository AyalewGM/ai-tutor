from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "foundations-fraction-equivalence-v2"
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


def _load(name: str) -> dict:
    return json.loads((DRAFT / name).read_text(encoding="utf-8"))


def _variants():
    path = DRAFT / "seeded_variants.py"
    spec = importlib.util.spec_from_file_location("foundations_fraction_variants", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_provenance_is_complete_and_fail_closed() -> None:
    provenance = _load("provenance.v2.json")

    assert provenance["record_type"] == "MIHUR_CONTENT_PROVENANCE"
    assert provenance["package_id"] == "W1-G4-FRACTION-EQUIVALENCE"
    assert provenance["revision"] == "foundations-fraction-equivalence-v2-r1"
    assert provenance["status"] == "DRAFT_UNVERIFIED"
    assert provenance["runtime_activation"] is False
    assert provenance["learner_data_writes"] is False
    assert provenance["mastery_writes"] is False
    assert provenance["standards"] == {
        "jurisdiction": "UNKNOWN_PENDING_STANDARDS_MAPPING",
        "official_source_url": "UNKNOWN_PENDING_STANDARDS_MAPPING",
        "publication": "UNKNOWN_PENDING_STANDARDS_MAPPING",
        "publication_version": "UNKNOWN_PENDING_STANDARDS_MAPPING",
        "exact_expectation_ids": [],
        "mapping_status": "UNKNOWN_NOT_PROPOSED",
        "mapping_approval": "NONE",
        "coverage_credit": False,
    }
    assert provenance["canonical"]["identity_change"] is False
    assert provenance["canonical"]["competing_grade_specific_identity_added"] is False
    assert all(
        status.startswith(("PENDING", "NOT_"))
        for status in provenance["independent_reviews"].values()
    )


def test_package_preserves_identity_and_covers_full_learning_progression() -> None:
    package = _load("package.v2.json")

    assert package["package_id"] == "W1-G4-FRACTION-EQUIVALENCE"
    assert package["revision_of"]["pull_request"] == 327
    assert package["runtime_activation"] is False
    assert package["mastery_writes"] is False
    assert [stage["phase"] for stage in package["learning_sequence"]] == PHASES
    representations = {
        representation
        for stage in package["learning_sequence"]
        for representation in stage["representations"]
    }
    assert representations == {"CONCRETE", "VISUAL", "SYMBOLIC"}


def test_diagnosis_routes_observed_evidence_to_distinct_repairs_and_exit_checks() -> None:
    routes = _load("package.v2.json")["diagnostic_router"]

    assert {route["misconception_id"] for route in routes} == {
        "FRAC.EQUIV.ADD_BOTH",
        "FRAC.EQUIV.DENOMINATOR_SIZE",
        "FRAC.EQUIV.DIFFERENT_WHOLES",
    }
    assert len({route["observed_evidence"] for route in routes}) == 3
    assert len({route["probe"] for route in routes}) == 3
    assert len({route["repair"] for route in routes}) == 3
    assert len({route["exit_check"] for route in routes}) == 3
    assert all(len(route["socratic_path"]) == 3 for route in routes)


def test_mve_reuse_is_truthfully_partial_and_assessment_fails_closed() -> None:
    package = _load("package.v2.json")
    mve = package["mve_reuse_contract"]
    assessment = package["independent_assessment_contract"]

    assert mve["reuse_status"] == "PARTIAL_REUSE_NOT_WIRED"
    assert "InteractiveFractionBars.tsx" in mve["guided_component"]
    assert "Paired equal-whole bars" in mve["missing_capability"]
    assert "absent from independent assessment" in mve["assessment_rule"]
    assert assessment["hints_allowed"] is False
    assert assessment["worked_steps_visible_before_submission"] is False
    assert assessment["answer_in_public_payload"] is False
    assert assessment["visual_scaffold_visible"] is False
    assert assessment["guided_practice_credit"] is False
    assert assessment["historical_mastery_mutation"] is False


def test_seeded_variants_replay_and_exact_oracles() -> None:
    variants = _variants()

    for mode in ("guided", "independent"):
        for seed in range(90):
            first = variants.generate(seed, mode)
            assert first == variants.generate(seed, mode)
            base = Fraction(first.numerator, first.denominator)
            if first.structure == "REPARTITION_EQUIVALENCE":
                target = Fraction(first.teacher_answer["fraction"])
                assert target == base
                assert first.teacher_answer["equivalent"] is True
            elif first.structure == "REJECT_ADD_BOTH_CLAIM":
                claimed = Fraction(first.numerator + 1, first.denominator + 1)
                assert claimed != base
                assert first.teacher_answer["equivalent"] is False
            else:
                assert first.whole_a is not None and first.whole_b is not None
                equivalent = Fraction(
                    first.numerator * first.scale,
                    first.denominator * first.scale,
                )
                quantity_a = base * first.whole_a
                quantity_b = equivalent * first.whole_b
                assert equivalent == base
                assert quantity_a != quantity_b
                assert Fraction(first.teacher_answer["quantity_a"]) == quantity_a
                assert Fraction(first.teacher_answer["quantity_b"]) == quantity_b
                assert first.teacher_answer["fractions_equivalent"] is True
                assert first.teacher_answer["quantities_equal"] is False


def test_guided_and_independent_namespaces_are_distinct_and_non_leaking() -> None:
    variants = _variants()

    for seed in range(60):
        guided = variants.generate(seed, "guided")
        independent = variants.generate(seed, "independent")
        assert guided.variant_id != independent.variant_id
        assert (
            guided.numerator,
            guided.denominator,
            guided.scale,
            guided.whole_a,
            guided.whole_b,
        ) != (
            independent.numerator,
            independent.denominator,
            independent.scale,
            independent.whole_a,
            independent.whole_b,
        )
        payload = independent.public_payload()
        assert set(payload) == {"variant_id", "mode", "structure", "prompt"}
        assert "answer" not in " ".join(payload).lower()
        assert "hint" not in " ".join(payload).lower()
        assert "teacher" not in " ".join(payload).lower()


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "4", None])
def test_invalid_seed_values_fail_closed(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _variants().generate(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        _variants().generate(4, mode)


def test_accessibility_contract_has_domain_specific_equivalence() -> None:
    accessibility = _load("package.v2.json")["accessibility_contract"]

    assert "repartition" in accessibility["keyboard_only"]
    assert "whole identifier and length" in accessibility["screen_reader_state"]
    assert "represented quantity" in accessibility["nonvisual_equivalent"]
    assert accessibility["focus_recovery"]
    assert accessibility["reduced_motion"]
    assert accessibility["color_independence"] is True
    assert accessibility["independent_scaffolds"] is False
