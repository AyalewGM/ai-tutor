"""Independent synthetic arithmetic checks for teacher-evidenced draft depth."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

MODULE = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/learning-packages-wave2/ontario_center_reasoning_depth.py"
)
spec = importlib.util.spec_from_file_location("ontario_center_reasoning_depth", MODULE)
assert spec is not None and spec.loader is not None
depth = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = depth
spec.loader.exec_module(depth)


def _correct(item):
    oracle = item.teacher_oracle
    reason = oracle["reason"]
    if item.structure == "FAIR_RATE_COMPARISON":
        return {
            "rates": [depth._wire(value) for value in oracle["rates"]],
            "winner": oracle["winner"],
            "reason": reason,
        }
    if item.structure == "DISTINCT_FIVE_VALUE_MAXIMUM":
        return {
            "values": list(oracle["values"]),
            "largest": oracle["largest"],
            "reason": reason,
        }
    return {
        "largest": oracle["largest"],
        "total": depth._wire(oracle["total"]),
        "reason": reason,
    }


@pytest.mark.parametrize("mode", ["guided", "independent"])
@pytest.mark.parametrize("index", range(36))
def test_deterministic_exact_and_mode_isolation(index, mode):
    item = depth.generate(index, mode)
    assert item == depth.generate(index, mode)
    assert item.mode == mode
    assert item.structure == depth.STRUCTURES[index % 3]
    assert item.variant_id != depth.generate(index, "independent" if mode == "guided" else "guided").variant_id

    if item.structure == "FAIR_RATE_COMPARISON":
        counts, totals = item.values["participants"], item.values["totals"]
        rates = tuple(Fraction(total, count) for count, total in zip(counts, totals, strict=True))
        assert rates == item.teacher_oracle["rates"]
        assert rates.index(max(rates)) == 0
        assert totals.index(max(totals)) == 1
        assert item.teacher_oracle["winner"] == "A"
    elif item.structure == "DISTINCT_FIVE_VALUE_MAXIMUM":
        values = item.teacher_oracle["values"]
        middle = item.values["median"]
        assert all(type(x) is int and x > 0 for x in values)
        assert len(values) == len(set(values)) == 5
        assert values == tuple(sorted(values))
        assert Fraction(sum(values), 5) == item.values["mean"] == middle
        assert values[2] == middle
        # Independently derived upper bound: other values must total >= 1+2+m+(m+1).
        assert values[-1] == 5 * middle - (1 + 2 + middle + middle + 1)
    else:
        minimum = item.values["minimum"]
        median = item.values["median"]
        maximum = item.teacher_oracle["largest"]
        mean = item.values["mean"]
        assert minimum < median < maximum
        assert Fraction(minimum + median + maximum, 3) == mean
        assert Fraction(3) * mean - minimum - median == maximum

    public = item.public_payload()
    encoded = json.dumps(public)
    assert public["status"] == "DRAFT_UNVERIFIED"
    assert public["runtime_activation"] is False
    assert public["mastery_credit"] is False
    assert "teacher_oracle" not in encoded
    assert "rates" not in encoded or "response_fields" in public
    if mode == "independent":
        assert "variant_id" not in public
        assert public["hints"] == public["worked_steps"] == []
        assert public["guided_feedback_available"] is False
        assert "phases" not in public
        with pytest.raises(PermissionError):
            depth.diagnose_guided(item, _correct(item))
    else:
        assert public["phases"] == list(depth.PHASES)
        assert depth.diagnose_guided(item, _correct(item)) == {
            "correct": True,
            "misconception_id": None,
            "socratic_questions": [],
            "mastery_credit": False,
        }


def test_guided_diagnoses_derived_response_errors_not_client_flags():
    fair = depth.generate(0, "guided")
    response = _correct(fair)
    response["winner"] = fair.teacher_oracle["raw_total_winner"]
    assert depth.diagnose_guided(fair, response)["misconception_id"] == "STAT.CENTER.RAW_TOTAL_BIAS"
    response = _correct(fair)
    response["rates"] = [str(x) for x in fair.values["totals"]]
    assert depth.diagnose_guided(fair, response)["misconception_id"] == "STAT.CENTER.FORGOT_DENOMINATOR"

    maximum = depth.generate(1, "guided")
    response = _correct(maximum)
    response["values"][1] = response["values"][0]
    assert depth.diagnose_guided(maximum, response)["misconception_id"] == "STAT.CENTER.DUPLICATED_DISTINCT_VALUE"
    response = _correct(maximum)
    response["largest"] -= 1
    assert depth.diagnose_guided(maximum, response)["misconception_id"] == "STAT.CENTER.NOT_MAXIMAL"

    inverse = depth.generate(2, "guided")
    response = _correct(inverse)
    response["total"] = depth._wire(inverse.values["mean"])
    assert depth.diagnose_guided(inverse, response)["misconception_id"] == "STAT.CENTER.MEAN_AS_TOTAL"


@pytest.mark.parametrize("index", range(9))
def test_repair_requires_corrected_original_and_fresh_different_structure(index):
    item = depth.generate(index, "guided")
    correct = _correct(item)
    failed = copy.deepcopy(correct)
    failed["reason"] = "WRONG_REASON"
    fresh = depth.fresh_repair_exit(item)
    assert fresh.structure != item.structure
    fresh_correct = _correct(fresh)
    result = depth.evaluate_repair_progress(item, failed, correct, fresh, fresh_correct)
    assert result["original_repaired"] is True
    assert result["fresh_verified"] is True
    assert result["ready_to_fade"] is True
    assert result["mastery_credit"] is False

    not_repaired = depth.evaluate_repair_progress(item, failed, failed, fresh, fresh_correct)
    assert not_repaired["ready_to_fade"] is False

    fresh_wrong = copy.deepcopy(fresh_correct)
    fresh_wrong["reason"] = "WRONG_REASON"
    not_fresh = depth.evaluate_repair_progress(item, failed, correct, fresh, fresh_wrong)
    assert not_fresh["ready_to_fade"] is False


def test_no_client_truth_fields_or_fake_exit_and_independent_repair():
    item = depth.generate(0, "guided")
    response = _correct(item)
    response["client_says_correct"] = True
    with pytest.raises(ValueError):
        depth.diagnose_guided(item, response)

    good = _correct(item)
    failed = copy.deepcopy(good)
    failed["reason"] = "WRONG_REASON"
    with pytest.raises(ValueError, match="fresh attempt"):
        depth.evaluate_repair_progress(item, failed, good, item, good)

    independent = depth.generate(0, "independent")
    with pytest.raises(PermissionError):
        depth.fresh_repair_exit(independent)
    with pytest.raises(PermissionError):
        depth.evaluate_repair_progress(independent, good, good, item, good)


@pytest.mark.parametrize("bad", [-1, True, 1.2, "4"])
def test_invalid_seed_fail_closed(bad):
    with pytest.raises(ValueError):
        depth.generate(bad, "guided")


def test_source_policy_no_new_authority_or_activation():
    source = MODULE.read_text()
    assert "DRAFT_UNVERIFIED" in source
    assert "RUNTIME_ACTIVATION = False" in source
    assert "MATH.DATA.MEAN" in source
    assert "MATH.DATA.MEDIAN" in source
    assert "MATH.DATA.MISSING_MEAN" in source
    assert "CREATE TABLE" not in source
    assert "original teacher PDF" not in source
