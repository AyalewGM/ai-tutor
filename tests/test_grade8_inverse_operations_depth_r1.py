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
        "misconception_answers",
        "verification",
        "strategy_probe",
    }
    for family in MODULE.FAMILIES:
        for mode in MODULE.MODES:
            variant = MODULE.generate(family, 73, mode)
            payload = variant.public_payload()
            assert forbidden.isdisjoint(payload)
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

            mismatched = MODULE.guided_repair(guided, answer, "DIFFERENT_STRATEGY")
            assert mismatched["classification"] == "UNCLASSIFIED_NO_ANSWER_REVEAL"

            support = MODULE.guided_repair(
                guided, answer, MODULE.strategy_probe_token(code)
            )
            assert support["classification"] == code
            assert len(support["questions"]) == 2
            assert support["fresh_exit_family"] == MODULE.TRANSFER_PARTNER[family]

        assert MODULE.guided_probe(guided, guided.answer) == {
            "classification": "CORRECT_NO_REMEDIATION",
            "questions": (),
        }


def test_support_isolated_from_diagnostic_independent_and_mastery_modes() -> None:
    for family in MODULE.FAMILIES:
        for mode in ("diagnostic", "independent", "mastery"):
            variant = MODULE.generate(family, 113, mode)
            observed = variant.misconception_answers[0][1]
            code = variant.misconception_answers[0][0]
            assert MODULE.guided_probe(variant, observed) is None
            assert MODULE.guided_repair(
                variant, observed, MODULE.strategy_probe_token(code)
            ) is None


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
