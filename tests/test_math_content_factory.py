"""Synthetic, side-effect-free test suite for the first Mihur content factory."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.canonical_problem_families import LearningMode, generate
from scripts.math_content_factory import (
    FAMILIES_IN_SLICE,
    _exact_expected,
    _learner_payload,
    _reviewable_blueprint,
    _submitted_answer,
    run_factory,
)

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "docs/content_factory/mth1w_eq3_factory.v1.json"


@pytest.fixture
def contract() -> dict:
    return json.loads(BLUEPRINT.read_text(encoding="utf-8"))


def test_existing_canonical_ids_and_source_guards(contract: dict) -> None:
    _reviewable_blueprint(contract)
    assert {item["family_code"] for item in contract["families"]} == FAMILIES_IN_SLICE
    assert all(
        source["reuse_policy"] == "REFERENCE_ONLY_DO_NOT_COPY"
        and source["permission_to_rehost_items"] is False
        for source in contract["research_sources"]
    )
    assert contract["runtime_activation"] is False
    assert contract["status"] == "DRAFT_UNVERIFIED"


@pytest.mark.parametrize(("field", "replacement"), [
    ("runtime_activation", True),
    ("status", "VERIFIED"),
    ("canonical_skill", "MTH1W.C.ALG.EQ3"),
    ("official_expectation_mapping", "APPROVED"),
])
def test_blueprint_cannot_self_authorize(
    contract: dict, field: str, replacement: object
) -> None:
    altered = copy.deepcopy(contract)
    altered[field] = replacement
    with pytest.raises(ValueError):
        _reviewable_blueprint(altered)


def test_unknown_family_or_source_license_fails_closed(contract: dict) -> None:
    bad_family = copy.deepcopy(contract)
    bad_family["families"][0]["family_code"] = "MTH1W.NEW.MATH.ENGINE"
    with pytest.raises(ValueError):
        _reviewable_blueprint(bad_family)
    bad_source = copy.deepcopy(contract)
    bad_source["research_sources"][0]["permission_to_rehost_items"] = True
    with pytest.raises(ValueError):
        _reviewable_blueprint(bad_source)


@pytest.mark.parametrize("family", sorted(FAMILIES_IN_SLICE))
@pytest.mark.parametrize("mode", (LearningMode.GUIDED, LearningMode.INDEPENDENT))
def test_exact_sympy_equivalence_and_leak_free_student_projection(
    family: str, mode: LearningMode
) -> None:
    seen = set()
    for seed in range(64):
        item = generate(family, seed=seed, difficulty=3, mode=mode)
        expected, signature = _exact_expected(item)
        assert _submitted_answer(item) == expected
        assert item.is_correct(item.canonical_answer)
        assert signature
        assert item.variant_id not in seen
        seen.add(item.variant_id)
        assert item == generate(family, seed=seed, difficulty=3, mode=mode)
        public = _learner_payload(item)
        encoded = json.dumps(public, sort_keys=True)
        assert public["runtime_activation"] is False
        assert public["mastery_credit"] is False
        assert "canonical_answer" not in encoded
        assert "misconception_answers" not in encoded
        if mode == LearningMode.INDEPENDENT:
            assert public["guidance"] == []


def test_seed_replay_and_unique_mathematical_tasks(contract: dict) -> None:
    report = run_factory(contract, seeds=64)
    assert report["factory_revision"] == "MATH_CONTENT_FACTORY_V1"
    assert report["registered_reused_families"] == 3
    assert report["sampled_generated_questions"] <= 3 * 2 * 64
    assert report["quality_gates"]["seeded_mathematical_variety"]
    assert report["status"] == "DRAFT_UNVERIFIED"
    assert report["runtime_activation"] is False
    assert report["pilot_skill_ready"] is False
    assert report["release_authority"] == "NONE"
    assert report["quality_gates"]["approved_mapping"] is False
    assert report["quality_gates"]["backend_family_scoring_and_mode_grants"] is False


def test_student_error_simulator_detects_correct_answer_collision() -> None:
    """Known original legacy word-family risk: ignoring start may be correct."""
    witnessed = False
    for seed in range(256):
        problem = generate(
            "MATH.ALG.EQ.WORD.TARGET",
            seed=seed, difficulty=3, mode=LearningMode.GUIDED,
        )
        answer = problem.misconception_answers.get("ALG.WORD.IGNORE_START")
        if answer is not None and problem.is_correct(answer):
            witnessed = True
            break
    assert witnessed, "adversarial simulator should expose known signature collision"


def test_bad_seed_budget_fails_closed(contract: dict) -> None:
    for count in (0, -1, True, 5_001, "8"):
        with pytest.raises(ValueError):
            run_factory(contract, seeds=count)


def test_factory_detects_misconception_defects_without_granting_release(contract: dict) -> None:
    report = run_factory(contract, seeds=256)
    assert report["observed_mathematical_failures"]
    assert any("collides with correct answer" in issue for issue in report["observed_mathematical_failures"])
    assert report["automated_math_checks_passed"] is False
    assert report["pilot_skill_ready"] is False
