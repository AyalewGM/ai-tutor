"""Contract tests for the draft Grade 8 distributive-expression package."""

from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/curriculum/drafts/canonical-grade8-distributive-expressions-depth-r1"


def _load_generator():
    path = PACKAGE / "generator.py"
    spec = importlib.util.spec_from_file_location("grade8_distributive_depth", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


g = _load_generator()


def _variants():
    return [
        g.generate(family, seed, mode)
        for family in g.FAMILIES
        for mode in g.MODES
        for seed in g.PRIMARY_SEEDS
    ]


def test_manifest_preserves_draft_identity_source_and_history_boundaries():
    manifest = json.loads((PACKAGE / "package.json").read_text())
    assert manifest["status"] == "DRAFT_UNVERIFIED"
    assert manifest["runtime_activation"] is False
    assert manifest["canonical_skill"] == "MATH.EE.EXPR"
    assert manifest["families"] == 12
    assert manifest["scope"]["new_canonical_identity_created"] is False
    assert manifest["scope"]["jurisdiction_bank_created"] is False
    assert manifest["scope"]["curriculum_mapping_changed"] is False
    assert all(value is False for value in manifest["persistence_boundary"].values())
    assert {item["standard_id"] for item in manifest["source_provenance"]} >= {
        "8.AT.B.3b",
        "8.EE.C.7b",
        "8.PFA.4",
    }
    for source in manifest["source_provenance"]:
        assert all(
            source[field]
            for field in (
                "publisher",
                "url",
                "document_title",
                "version_date",
                "page",
                "standard_id",
                "access_date",
                "license_adaptation",
            )
        )


def test_all_primary_variants_are_deterministic_complete_and_nonrepeating():
    first = _variants()
    second = _variants()
    assert len(first) == 12 * 4 * 32 == 1_536
    assert first == second
    assert len({variant.variant_id for variant in first}) == 1_536
    assert len({variant.task_fingerprint for variant in first}) == 1_536
    assert {variant.family_code for variant in first} == set(g.FAMILIES)
    for variant in first:
        assert variant.prerequisites
        assert variant.difficulty_rationale
        assert variant.answer_boundary
        assert len(variant.representation_sequence) == 3
        assert len(variant.misconception_signals) == 2
        assert all(
            g._normalized_response(signal["candidate_response"])
            != variant.oracle_response
            for signal in variant.misconception_signals
        )


def test_exact_oracles_accept_equivalent_fractions_and_reject_near_misses():
    for variant in _variants():
        oracle = dict(variant.oracle_response)
        equivalent = {
            key: (f"{value.numerator * 7}/{value.denominator * 7}" if isinstance(value, Fraction) else value)
            for key, value in oracle.items()
        }
        assert variant.response_is_correct(equivalent)
        first_numeric = next(
            (key for key, value in oracle.items() if isinstance(value, Fraction)), None
        )
        if first_numeric:
            near_miss = dict(oracle)
            near_miss[first_numeric] += Fraction(1, 1_000)
            assert not variant.response_is_correct(near_miss)
        assert not variant.response_is_correct({})


def test_special_family_oracles_and_domain_boundaries_hold_for_every_seed():
    for variant in _variants():
        response = dict(variant.oracle_response)
        x_coefficient, constant = variant.affine_oracle
        for x in (Fraction(-3, 2), Fraction(0), Fraction(7, 3)):
            assert g.normalized_affine_value(variant, x) == x_coefficient * x + constant

        if variant.family_code == g.FAMILIES[6]:
            assert response["outer_factor"] == g.greatest_positive_common_factor(variant)
            assert response["outer_factor"] > 0
            assert response["outer_factor"] * response["inner_x_coefficient"] == x_coefficient
            assert response["outer_factor"] * response["inner_constant"] == constant
        elif variant.family_code == g.FAMILIES[7]:
            original_constant = x_coefficient * g._parameters(variant.mode, variant.seed)[2]
            assert response["equivalent"] is (constant == original_constant)
        elif variant.family_code == g.FAMILIES[8]:
            assert response["left_value"] != response["right_value"]
        elif variant.family_code == g.FAMILIES[9]:
            assert response["first_invalid_step"] == "STEP_1"
        elif variant.family_code == g.FAMILIES[10]:
            assert response["missing_constant"] == constant


def test_two_probe_guided_repairs_are_targeted_and_isolated():
    signatures = {}
    routes = 0
    for family in g.FAMILIES:
        for seed in g.PRIMARY_SEEDS:
            guided = g.generate(family, seed, "guided")
            for signal in guided.misconception_signals:
                routes += 1
                targeted = guided.guided_repair(
                    signal["candidate_response"], signal["reasoning_choice"]
                )
                assert targeted["status"] == "TARGETED_REPAIR"
                assert targeted["misconception_code"] == signal["code"]
                assert len(targeted["questions"]) == 2
                assert targeted["worked_answer_revealed"] is False
                assert targeted["mastery_credit"] is False
                signatures.setdefault(
                    signal["code"],
                    (
                        tuple(targeted["questions"]),
                        targeted["representation_move"],
                        targeted["explanation"],
                    ),
                )
                mismatch = guided.guided_repair(
                    signal["candidate_response"], "UNRELATED_REASON"
                )
                assert mismatch == {
                    "status": "NEUTRAL_RETRY",
                    "reason": "EVIDENCE_NOT_CORROBORATED",
                }
    assert routes == 12 * 32 * 2 == 768
    assert set(signatures) == set(g.REPAIRS)
    assert len(set(signatures.values())) == 10


def test_support_accessibility_and_answer_evidence_do_not_leak_across_modes():
    for variant in _variants():
        payload = variant.public_payload()
        assert payload["runtime_activation"] is False
        assert payload["mastery_credit"] is False
        assert set(payload["accessibility"]) == {
            "keyboard",
            "screen_reader",
            "non_color",
            "reduced_motion",
            "exact_input",
            "focus",
        }
        assert "oracle" not in payload
        assert "misconception_signals" not in payload
        if variant.mode == "guided":
            assert payload["learning_sequence"] == [
                "OBSERVE",
                "PREDICT",
                "MANIPULATE",
                "EXPLAIN",
                "PRACTICE",
                "DIAGNOSE",
                "TRANSFER",
                "VERIFY",
            ]
            assert payload["diagnosis_requires"] == [
                "observed_response",
                "reasoning_choice",
            ]
            assert "support" not in payload
        else:
            assert payload["support"] == "NONE_UNHINTED"
            assert "learning_sequence" not in payload
            assert variant.guided_repair({}, "ANY") == {
                "status": "SUPPORT_NOT_AVAILABLE"
            }


def test_unhinted_transfer_uses_a_fresh_family_structure_and_seed_band():
    fingerprints = set()
    for source_mode in ("diagnostic", "guided"):
        for family in g.FAMILIES:
            for seed in g.PRIMARY_SEEDS:
                source = g.generate(family, seed, source_mode)
                transfer = g.create_unhinted_transfer(source)
                assert transfer.mode == "independent"
                assert transfer.seed == seed + g.TRANSFER_SEED_OFFSET
                assert transfer.family_code != source.family_code
                assert transfer.structure_code != source.structure_code
                assert transfer.task_fingerprint != source.task_fingerprint
                assert transfer.public_payload()["support"] == "NONE_UNHINTED"
                fingerprints.add(transfer.task_fingerprint)
    # The same source seed intentionally maps to the same transfer task from
    # diagnostic and guided; each of 12 families still gets 32 unseen tasks.
    assert len(fingerprints) == 12 * 32 == 384


def test_pack_is_idempotent_history_neutral_and_fails_closed():
    assert g.create_pack() == g.create_pack()
    pack = g.create_pack()
    assert pack["status"] == "DRAFT_UNVERIFIED"
    assert pack["runtime_activation"] is False
    assert pack["local_mapping_activation"] is False
    assert len(pack["variant_ids"]) == 1_536
    assert len(set(pack["task_fingerprints"])) == 1_536
    assert pack["learner_history_writes"] is False
    assert pack["attempt_writes"] is False
    assert pack["mastery_writes"] is False
    for bad in (
        ("UNKNOWN", 0, "guided"),
        (g.FAMILIES[0], -1, "guided"),
        (g.FAMILIES[0], 0, "unsupported"),
    ):
        try:
            g.generate(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid generation input did not fail: {bad}")
