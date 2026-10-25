"""Author-only verification; no production or Muse-owned tests changed."""
from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs/curriculum/drafts/learning-packages-wave2"
SPEC = importlib.util.spec_from_file_location("svd_r1", DIR / "single_variable_data_depth_r1.py")
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


@pytest.mark.parametrize("family", M.FAMILIES)
@pytest.mark.parametrize("mode", M.MODES)
def test_deterministic_exact_and_answer_isolation(family, mode):
    for seed in range(128):
        item = M.generate(family, seed, mode)
        assert item == M.generate(family, seed, mode)
        assert M.review_equivalent(item, item["private"]["answer"])
        public = item["public"]
        assert public["status"] == "DRAFT_UNVERIFIED"
        assert public["runtime_activation"] is False
        assert public["mastery_credit"] is False
        assert public["support_prompts"] == []
        assert "answer" not in public and "wrong_signature" not in json.dumps(public)
        if mode == "guided":
            assert M.guided_response(item, item["private"]["answer"])["classification"] == "CORRECT_NO_REPAIR"
            wrong = item["private"]["wrong_signature"]
            assert not M.review_equivalent(item, wrong)
            support = M.guided_response(item, wrong)
            assert support["classification"] == family
            assert support["mastery_credit"] is False
            assert len(support["questions"]) == 1
            assert M.guided_response(item, dict(wrong, client_claims_correct=True)) is None
        else:
            assert M.guided_response(item, item["private"]["wrong_signature"]) is None


@pytest.mark.parametrize("size", (9, 10, 11, 12))
def test_explicit_median_of_halves(size):
    values = list(range(4, 4 + size))
    lo, q1, q2, q3, hi = M.five_number(values)
    h = size // 2
    assert lo == min(values) and hi == max(values)
    assert q1 == M.median(values[:h])
    assert q2 == M.median(values)
    assert q3 == M.median(values[-h:])
    ordinary = M.box(values)
    assert M.exact(ordinary["left_whisker"]) == lo
    assert M.exact(ordinary["right_whisker"]) == hi
    assert M.exact(ordinary["iqr"]) == q3 - q1


def test_modified_fences_whiskers_and_outliers():
    for seed in range(512):
        item = M.generate("MODIFIED_BOX", seed, "independent")
        data = item["public"]["prompt"]
        assert "MODIFIED" in data
        answer = item["private"]["answer"]
        assert len(answer["outliers"]) == 1
        assert M.exact(answer["right_whisker"]) < answer["outliers"][0]
        assert M.exact(answer["upper_fence"]) < answer["outliers"][0]
        assert M.exact(answer["upper_fence"]) == M.exact(answer["q3"]) + Fraction(3, 2) * M.exact(answer["iqr"])


def test_inverse_dataset_accepts_unordered_valid_alternatives():
    for seed in range(100):
        item = M.generate("CONSTRUCT_SET", seed, "independent")
        original = item["private"]["answer"]["values"]
        assert M.review_equivalent(item, {"values": original[::-1]})
        invalid = list(original)
        invalid[-1] += 1
        assert not M.review_equivalent(item, {"values": invalid})
        assert not M.review_equivalent(item, {"values": [True] + original[1:]})
        assert not M.review_equivalent(item, {"values": original + [0]})


def test_equivalent_exact_rationals_and_reject_float():
    item = M.generate("CENTER_CHOICE", 0, "independent")
    response = dict(item["private"]["answer"])
    value = M.exact(response["mean"])
    response["mean"] = f"{2 * value.numerator}/{2 * value.denominator}"
    assert M.review_equivalent(item, response)
    response["mean"] = float(value)
    assert not M.review_equivalent(item, response)


def test_unseen_independent_transfer_same_competency():
    for family in M.FAMILIES:
        for seed in range(80):
            source = M.generate(family, seed, "guided")
            exit_item = M.independent_transfer(source, seed)
            assert exit_item["family"] == source["family"]
            assert exit_item["mode"] == "independent"
            assert exit_item["public"]["prompt"] != source["public"]["prompt"]
            assert exit_item["private"] != source["private"]
            assert exit_item["public"]["support_prompts"] == []
            assert M.review_equivalent(exit_item, exit_item["private"]["answer"])
            with pytest.raises(ValueError):
                M.independent_transfer(exit_item, seed)


def test_invalid_requests_fail_closed_and_scope_cards_are_draft():
    for invalid in (-1, True, "3", 1.2):
        with pytest.raises(ValueError):
            M.generate("QUARTILES", invalid, "guided")
    with pytest.raises(ValueError):
        M.generate("UNKNOWN", 0, "guided")
    with pytest.raises(ValueError):
        M.generate("QUARTILES", 0, "production")
    scope = json.loads((DIR / "single_variable_data_depth_r1.scope.json").read_text())
    assert scope["status"] == "DRAFT_UNVERIFIED"
    assert scope["runtime_activation"] is False
    assert len(scope["scope_cards"]) == len(M.FAMILIES) == 8
    assert {c["family"] for c in scope["scope_cards"]} == set(M.FAMILIES)
    assert all(c["status"] == "DRAFT_UNVERIFIED" for c in scope["scope_cards"])
    assert all(scope["policy"].values())


def test_socratic_prompts_cover_every_family():
    assert set(M.SOCRATIC) == set(M.FAMILIES)


def test_box_prompts_state_quartile_convention_and_transfer_requests_only_scored_fields():
    for family in ("QUARTILES", "ORDINARY_BOX", "MODIFIED_BOX", "COMPARE_BOXES"):
        for seed in range(20):
            prompt = M.generate(family, seed, "independent")["public"]["prompt"]
            assert "excluding the overall median for odd n" in prompt
    for family in M.FAMILIES:
        item = M.independent_transfer(M.generate(family, 0, "guided"), 0)
        assert "Explain" not in item["public"]["prompt"]
