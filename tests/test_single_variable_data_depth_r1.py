"""Author-only verification; no production or Muse-owned tests changed."""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
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
        assert "structure" not in public and "constraints" not in public
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
        outlier = answer["outliers"][0]
        q1, q3, iqr = (M.exact(answer[k]) for k in ("q1", "q3", "iqr"))
        assert M.exact(answer["upper_fence"]) == q3 + Fraction(3, 2) * iqr
        assert M.exact(answer["lower_fence"]) == q1 - Fraction(3, 2) * iqr
        if item["private"]["structure"] == "HIGH_OUTLIER":
            assert M.exact(answer["right_whisker"]) < outlier
            assert M.exact(answer["upper_fence"]) < outlier
        else:
            assert M.exact(answer["left_whisker"]) > outlier
            assert M.exact(answer["lower_fence"]) > outlier


def test_inverse_dataset_accepts_unordered_valid_alternatives():
    for seed in range(100):
        item = M.generate("CONSTRUCT_SET", seed, "independent")
        original = item["private"]["answer"]["values"]
        assert M.review_equivalent(item, {"values": original[::-1]})
        invalid = list(original)
        invalid[-1] += 1
        assert not M.review_equivalent(item, {"values": invalid})
        m = original[2]
        symmetric = [m - 1, m, m, m, m + 1]
        if item["private"]["structure"] != "MEAN_EQUALS_MEDIAN":
            assert not M.review_equivalent(item, {"values": symmetric})
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


@pytest.mark.parametrize("family", ["DATA_TYPE", "GRAPH_CHOICE"])
def test_classification_families_vary_beyond_fixed_case_tables(family):
    for mode in M.MODES:
        items = [M.generate(family, seed, mode) for seed in range(80)]
        assert len({item["public"]["prompt"] for item in items}) >= 70
        answers = {next(iter(item["private"]["answer"].values())) for item in items}
        assert answers == ({"CATEGORICAL", "DISCRETE", "CONTINUOUS"} if family == "DATA_TYPE"
                           else {"BAR", "HISTOGRAM", "BOXPLOT", "CIRCLE"})


TASK_STRUCTURES = {
    "DATA_TYPE": {"CATEGORICAL", "CATEGORICAL_CODED", "COUNT", "STEPPED", "MEASURED"},
    "GRAPH_CHOICE": {"BAR", "HISTOGRAM", "BOXPLOT", "CIRCLE"},
    "CENTER_CHOICE": {f"{side}_EXTREME_{rep}" for side in ("HIGH", "LOW")
                      for rep in ("REPEATED_VALUE", "NO_REPEAT")},
    "CONSTRUCT_SET": {"MEAN_EQUALS_MEDIAN", "MEAN_ABOVE_MEDIAN", "MEAN_BELOW_MEDIAN"},
    "QUARTILES": {f"{layout}_{parity}_N" for layout in ("LIST", "FREQUENCY_TABLE") for parity in ("ODD", "EVEN")},
    "ORDINARY_BOX": {f"{layout}_{parity}_N" for layout in ("LIST", "FREQUENCY_TABLE") for parity in ("ODD", "EVEN")},
    "MODIFIED_BOX": {"HIGH_OUTLIER", "LOW_OUTLIER"},
    "COMPARE_BOXES": {"RAW_BOTH", "RAW_AND_SUMMARY"},
}


@pytest.mark.parametrize("family", M.FAMILIES)
def test_task_structure_fingerprints_and_transfer_changes_structure(family):
    for mode in M.MODES:
        seen = {M.generate(family, seed, mode)["private"]["structure"] for seed in range(200)}
        assert seen == TASK_STRUCTURES[family]
    for seed in range(80):
        for source_mode in ("guided", "diagnostic"):
            source = M.generate(family, seed, source_mode)
            exit_item = M.independent_transfer(source, seed)
            assert exit_item["private"]["structure"] != source["private"]["structure"]


def test_center_choice_mode_and_extreme_side_are_exact():
    for seed in range(200):
        item = M.generate("CENTER_CHOICE", seed, "independent")
        values = [int(v) for v in item["public"]["prompt"].split("[")[1].split("]")[0].split(",")]
        answer = item["private"]["answer"]
        counts = Counter(values)
        top = max(counts.values())
        assert answer["mode"] == (str(max(counts, key=counts.get)) if top >= 2 else "NONE")
        mean, med = M.exact(answer["mean"]), M.exact(answer["median"])
        assert (mean > med) == item["private"]["structure"].startswith("HIGH")


@pytest.mark.parametrize("family", ["QUARTILES", "ORDINARY_BOX"])
def test_frequency_table_layout_reproduces_oracle(family):
    checked = 0
    for seed in range(200):
        item = M.generate(family, seed, "independent")
        if not item["private"]["structure"].startswith("FREQUENCY_TABLE"):
            continue
        table = item["public"]["prompt"].split("(value: count) ")[1].split(". Give")[0]
        values = []
        for pair in table.split(", "):
            value, count = pair.split(": ")
            values += [int(value)] * int(count)
        assert any(int(pair.split(": ")[1]) >= 2 for pair in table.split(", "))
        expected = M.box(values)
        assert all(item["private"]["answer"][k] == expected[k] for k in item["private"]["answer"])
        checked += 1
    assert checked >= 50


def test_compare_summary_layout_matches_group_b_oracle():
    for seed in range(200):
        item = M.generate("COMPARE_BOXES", seed, "independent")
        if item["private"]["structure"] != "RAW_AND_SUMMARY":
            continue
        answer = item["private"]["answer"]
        prompt = item["public"]["prompt"]
        assert f"median {answer['median_b']}" in prompt
        q1 = M.exact(prompt.split("Q1 ")[1].split(",")[0])
        q3 = M.exact(prompt.split("Q3 ")[1].split(",")[0])
        assert q3 - q1 == M.exact(answer["iqr_b"])
