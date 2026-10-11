from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "middle-grades-iqr-boxplot-r1"


def _load(name: str) -> dict:
    return json.loads((DRAFT / name).read_text(encoding="utf-8"))


def _variants():
    path = DRAFT / "seeded_variants.py"
    spec = importlib.util.spec_from_file_location("middle_grades_iqr_variants", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _independent_summary(values: tuple[int, ...]) -> tuple[Fraction, ...]:
    assert len(values) == 8
    ordered = tuple(sorted(values))
    return (
        Fraction(ordered[0]),
        Fraction(ordered[1] + ordered[2], 2),
        Fraction(ordered[3] + ordered[4], 2),
        Fraction(ordered[5] + ordered[6], 2),
        Fraction(ordered[7]),
    )


def test_provenance_is_complete_and_fail_closed() -> None:
    p = _load("provenance.json")
    assert p["record_type"] == "MIHUR_CONTENT_PROVENANCE"
    assert p["package_id"] == "W2-G7-DISTRIBUTIONS-IQR"
    assert p["status"] == "DRAFT_UNVERIFIED"
    assert p["runtime_activation"] is False
    assert p["learner_data_writes"] is False
    assert p["mastery_writes"] is False
    assert p["official_standards"]["exact_expectation_ids"] == []
    assert p["official_standards"]["mapping_status"] == "NONE_NOT_APPROVED"
    assert p["canonical"]["new_canonical_identity"] is False
    assert p["independent_verdicts"]["engineering_release"] == "NOT_APPROVED"


def test_package_covers_mihur_flow_and_assessment_isolation() -> None:
    package = _load("package.json")
    assert [step["phase"] for step in package["learning_sequence"]] == [
        "OBSERVE", "PREDICT", "MANIPULATE", "EXPLAIN", "PRACTICE", "DIAGNOSE", "TRANSFER", "VERIFY"
    ]
    reps = {rep for step in package["learning_sequence"] for rep in step["representations"]}
    assert reps == {"CONCRETE", "VISUAL", "SYMBOLIC"}
    assessment = package["independent_assessment_contract"]
    assert assessment["hints_allowed"] is False
    assert assessment["guided_mve_visible"] is False
    assert assessment["answer_in_public_payload"] is False
    assert assessment["guided_practice_credit"] is False
    assert assessment["historical_mastery_mutation"] is False
    assert assessment["backend_status"] == "NOT_IMPLEMENTED"


def test_seeded_replay_mode_separation_and_public_non_disclosure() -> None:
    variants = _variants()
    for seed in range(100):
        guided = variants.generate(seed, "guided")
        independent = variants.generate(seed, "independent")
        assert guided == variants.generate(seed, "guided")
        assert independent == variants.generate(seed, "independent")
        assert guided.variant_id != independent.variant_id
        payload = independent.public_payload()
        assert "summary_a" not in payload
        assert "summary_b" not in payload
        assert "iqr_a" not in payload
        assert "iqr_b" not in payload
        assert "more_middle_spread" not in payload
        assert "more_consistent_middle" not in payload


def test_independent_exact_quartile_and_comparison_oracles() -> None:
    variants = _variants()
    for seed in range(240):
        item = variants.generate(seed, "independent")
        summary_a = _independent_summary(item.data_a)
        summary_b = _independent_summary(item.data_b)
        assert item.summary_a == summary_a
        assert item.summary_b == summary_b
        assert item.iqr_a == summary_a[3] - summary_a[1]
        assert item.iqr_b == summary_b[3] - summary_b[1]
        assert item.range_a == item.data_a[-1] - item.data_a[0]
        assert item.range_b == item.data_b[-1] - item.data_b[0]
        expected_more_spread = "A" if item.iqr_a > item.iqr_b else "B"
        assert item.more_middle_spread == expected_more_spread
        assert item.more_consistent_middle != expected_more_spread
        range_choice = "A" if item.range_a > item.range_b else "B"
        assert range_choice != expected_more_spread
        assert summary_a[2] == summary_b[2]


def test_response_evidence_routes_to_specific_repairs() -> None:
    variants = _variants()
    item = variants.generate(8, "guided")
    assert variants.diagnose_comparison(item, item.iqr_a, item.iqr_b, item.more_middle_spread) == "CORRECT_PRACTICE_ONLY"
    assert variants.diagnose_comparison(item, item.range_a, item.range_b, item.more_middle_spread) == "RANGE_USED_AS_IQR"
    range_choice = "A" if item.range_a > item.range_b else "B"
    assert variants.diagnose_comparison(item, item.iqr_a, item.iqr_b, range_choice) == "WHOLE_RANGE_CHOSEN_FOR_MIDDLE_SPREAD"
    assert variants.diagnose_comparison(item, -item.iqr_a, item.iqr_b, item.more_middle_spread) == "QUARTILE_ORDER_REVERSED"
    assert variants.diagnose_comparison(item, item.iqr_a + 1, item.iqr_b, item.more_middle_spread) == "IQR_CALCULATION_ERROR"


@pytest.mark.parametrize("seed", [-1, True, False, 2.5, "3", None])
def test_invalid_seeds_fail_closed(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _variants().generate(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        _variants().generate(4, mode)
