"""Fail-closed mathematical checks for external, non-authoritative fraction drafts.

These tests validate exact arithmetic, not human reasoning quality or curriculum
coverage. This file is deliberately independent of the canonical skill registry.
"""

from __future__ import annotations

import json
import re
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs/curriculum/drafts/draft-g45-fractions-pilot-v0"
PRACTICE = json.loads((DRAFT / "practice.normalized.json").read_text(encoding="utf-8"))
SUPPORT = json.loads((DRAFT / "supporting.normalized.json").read_text(encoding="utf-8"))

_FRACTION = re.compile(r"^[1-9][0-9]*/[1-9][0-9]*$")
_INTEGER = re.compile(r"^[1-9][0-9]*$")
_EXPECTED = {
    "q-rep-01": Fraction(4, 6),
    "q-rep-02": Fraction(3, 5),
    "q-rep-03": Fraction(10 - 7, 10),
    "q-rep-04": Fraction(5, 8),
    "q-rep-05": Fraction(4 - 1, 4),
    "q-rep-06": Fraction(2, 3),
    "q-eq-01": Fraction(1, 3),
    "q-eq-02": True,
    "q-eq-03": Fraction(2, 5),
    "q-eq-04": Fraction(8, 12),
    "q-eq-05": Fraction(3, 4),
    "q-eq-06": True,
    "q-eq-07": 12,
    "q-cmp-01": "<",
    "q-cmp-02": Fraction(2, 3),
    "q-cmp-03": [Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)],
    "q-cmp-04": ">",
    "q-cmp-05": ">",
    "q-cmp-06": Fraction(7, 8),
    "q-add-01": Fraction(2, 7) + Fraction(3, 7),
    "q-add-02": Fraction(5, 9) - Fraction(2, 9),
    "q-add-03": Fraction(3, 8) + Fraction(2, 8),
    "q-add-04": Fraction(4, 5) + Fraction(3, 5),
    "q-add-05": Fraction(11, 12) - Fraction(5, 12),
    "q-add-06": Fraction(7, 10) - Fraction(3, 10),
}


def parse_fraction(text: str) -> Fraction:
    """Accept only positive numerator/denominator notation, never eval or floats."""
    if not _FRACTION.fullmatch(text):
        raise ValueError(f"invalid fraction notation: {text!r}")
    numerator, denominator = map(int, text.split("/"))
    return Fraction(numerator, denominator)


def is_simplest(text: str) -> bool:
    parsed = parse_fraction(text)
    return str(parsed) == text


def test_draft_metadata_is_not_authoritative() -> None:
    assert PRACTICE["content_status"] == "DRAFT_UNVERIFIED"
    assert PRACTICE["review_status"] == "PENDING"
    assert PRACTICE["runtime_activation"] is False
    assert PRACTICE["canonical_skill_ids"] == []
    assert PRACTICE["curriculum_mappings"] == []
    assert SUPPORT["status"] == "DRAFT_UNVERIFIED"


def test_complete_unique_inventory() -> None:
    items = PRACTICE["practice_items"]
    assert len(items) == len(_EXPECTED) == 25
    assert {x["item_id"] for x in items} == set(_EXPECTED)
    assert len({x["question"] for x in items}) == 25
    assert len(SUPPORT["worked_examples"]) == 5
    assert len(SUPPORT["misconceptions"]) == 5
    assert len(SUPPORT["visualization_specs"]) == 1
    assert all(x["review_status"] == "PENDING" for x in items)


def test_all_answers_match_independent_exact_oracles() -> None:
    for item in PRACTICE["practice_items"]:
        code, contract, text = item["item_id"], item["answer_contract"], item["expected"]
        expected = _EXPECTED[code]
        if contract == "human_rubric":
            assert parse_fraction(text) == expected
        elif contract == "two_distinct_equivalent_fractions":
            answers = text.split(";")
            assert len(answers) == len(set(answers)) == 2
            assert all(parse_fraction(x) == expected for x in answers)
            assert {int(x.split("/")[1]) for x in answers} == {10, 15}
        elif contract == "ordered_fraction_sequence":
            assert [parse_fraction(x) for x in text.split(";")] == expected
        elif contract in {"boolean_with_human_justification"}:
            assert (text == "true") is expected
        elif contract == "positive_integer":
            assert _INTEGER.fullmatch(text)
            assert int(text) == expected
        elif contract == "comparison_symbol":
            assert text == expected
        else:
            assert parse_fraction(text) == expected, code
            if contract == "simplest_fraction":
                assert is_simplest(text), code
            if contract == "fixed_denominator_fraction":
                assert text == "3/9", code


def test_exact_equivalence_and_comparison_are_consistent() -> None:
    assert Fraction(2, 4) == Fraction(3, 6)
    assert Fraction(4, 6) == Fraction(10, 15)
    assert Fraction(6, 8) == Fraction(3, 4) != Fraction(6, 12)
    assert Fraction(3, 8) < Fraction(5, 8)
    assert Fraction(2, 3) > Fraction(3, 5)
    assert Fraction(5, 6) > Fraction(5, 8)
    assert Fraction(7, 10) > Fraction(2, 3)
    assert 1 - Fraction(7, 8) < 1 - Fraction(5, 6)


def test_intermediate_forms_are_exactly_equivalent() -> None:
    for item in PRACTICE["practice_items"]:
        if item["intermediate_form"] is not None:
            assert parse_fraction(item["intermediate_form"]) == parse_fraction(
                item["expected"]
            ), item["item_id"]


def test_denominator_exceptions_are_explicit() -> None:
    policies = PRACTICE["policies"]
    assert 7 in policies["operational_denominators"]
    assert 9 in policies["operational_denominators"]
    assert {9, 15, 20, 25} <= set(policies["equivalence_derived_denominators"])
    assert policies["mixed_number_answers"] is False
    assert policies["unlike_denominator_add_sub"] is False
    assert policies["fraction_multiplication_division"] is False


def test_no_unsafe_or_ambiguous_answer_contracts() -> None:
    allowed = {
        "fraction_value", "simplest_fraction", "fixed_denominator_fraction",
        "human_rubric", "boolean_with_human_justification",
        "two_distinct_equivalent_fractions", "choice_with_human_justification",
        "positive_integer", "comparison_symbol", "fraction_choice",
        "ordered_fraction_sequence",
    }
    for item in PRACTICE["practice_items"]:
        assert item["answer_contract"] in allowed
        assert " or " not in item["expected"]
        assert item["review_status"] == "PENDING"
    assert not any("mixed" in item["expected"] for item in PRACTICE["practice_items"])


def test_visual_spec_deterministic_invariants() -> None:
    viz = SUPPORT["visualization_specs"][0]
    assert viz["implementation_status"] == "DESIGN_ONLY"
    assert set(viz["denominators"]) <= set(PRACTICE["policies"]["operational_denominators"])
    for n in viz["denominators"]:
        for a in range(n + 1):
            for b in range(n + 1):
                assert Fraction(a, n) + Fraction(b, n) == Fraction(a + b, n)
                assert (a + b > n) == (Fraction(a + b, n) > 1)


def test_parser_rejects_mixed_numbers_and_ambiguous_inputs() -> None:
    for invalid in ("1 2/5", "3/9 or 1/3", "0/4", "2/0", "1/2+1/3", "1.5", "-1/3"):
        try:
            parse_fraction(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe answer accepted: {invalid!r}")

def test_human_reasoning_rubrics_are_complete_and_fail_closed() -> None:
    rubrics = json.loads(
        (DRAFT / "reasoning_rubrics.draft.json").read_text(encoding="utf-8")
    )
    assert rubrics["status"] == "DRAFT_UNVERIFIED"
    assert rubrics["review_status"] == "PENDING"
    assert rubrics["auto_grade"] is False
    required_ids = {
        item["item_id"]
        for item in PRACTICE["practice_items"]
        if item["answer_contract"]
        in {"human_rubric", "boolean_with_human_justification", "choice_with_human_justification"}
    }
    indexed = {rubric["item_id"]: rubric for rubric in rubrics["rubrics"]}
    assert len(indexed) == len(rubrics["rubrics"])
    assert set(indexed) == required_ids
    for rubric in indexed.values():
        assert rubric["assessment_mode"] == "human_only"
        assert rubric["decision"]
        assert rubric["acceptable_evidence"]
        assert rubric["non_evidence"]
        assert rubric["common_errors"]
        assert len(rubric["criteria"]) >= 2
        assert all(c["required"] and c["description"] for c in rubric["criteria"])


def test_equivalence_pair_multiplier_constraints() -> None:
    pair = next(
        item for item in PRACTICE["practice_items"] if item["item_id"] == "q-eq-03"
    )
    answers = pair["expected"].split(";")
    multipliers = []
    for answer in answers:
        numerator, denominator = map(int, answer.split("/"))
        assert numerator % 2 == 0 and denominator % 5 == 0
        multiplier = numerator // 2
        assert denominator // 5 == multiplier
        assert multiplier in PRACTICE["policies"]["equivalence_multipliers"]
        multipliers.append(multiplier)
    assert len(multipliers) == len(set(multipliers)) == 2

def test_source_fidelity_crosswalk_covers_every_draft_asset() -> None:
    crosswalk = json.loads(
        (DRAFT / "source_fidelity_review.draft.json").read_text(encoding="utf-8")
    )
    assert crosswalk["status"] == "DRAFT_UNVERIFIED"
    assert crosswalk["review_status"] == "PENDING"
    practice_ids = {item["item_id"] for item in PRACTICE["practice_items"]}
    support_ids = {
        item["example_id"] for item in SUPPORT["worked_examples"]
    } | {
        item["misconception_id"] for item in SUPPORT["misconceptions"]
    } | {
        item["spec_id"] for item in SUPPORT["visualization_specs"]
    }
    practice = crosswalk["practice_revisions"]
    supporting = crosswalk["supporting_revisions"]
    assert len(practice) == crosswalk["practice_item_count"] == 25
    assert len(supporting) == crosswalk["supporting_item_count"] == 11
    assert {item["item_id"] for item in practice} == practice_ids
    assert {item["source_id"] for item in supporting} == support_ids
    assert all(item["review_status"] == "PENDING" for item in practice + supporting)
    assert all(item["normalization"] and item["review_note"] for item in supporting)
    assert all(item["normalization"] and item["review_note"] for item in practice)


def test_worked_examples_exact_math_and_required_forms() -> None:
    examples = {x["example_id"]: x for x in SUPPORT["worked_examples"]}
    assert parse_fraction(examples["we-01"]["final_answer"]) == Fraction(5, 8)
    # The specified denominator 20 is essential; 3/5 alone does not answer it.
    assert examples["we-02"]["final_answer"] == "12/20"
    assert parse_fraction(examples["we-02"]["final_answer"]) == Fraction(3, 5)
    left, right = examples["we-03"]["final_answer"].split(" < ")
    assert parse_fraction(left) == Fraction(3, 4)
    assert parse_fraction(right) == Fraction(5, 6)
    assert parse_fraction(left) < parse_fraction(right)
    assert parse_fraction(examples["we-04"]["final_answer"]) == (
        Fraction(4, 9) + Fraction(2, 9)
    )
    assert is_simplest(examples["we-04"]["final_answer"])
    assert parse_fraction(examples["we-05"]["final_answer"]) == (
        Fraction(9, 10) - Fraction(4, 10)
    )
    assert is_simplest(examples["we-05"]["final_answer"])
    assert all(example["steps"] for example in examples.values())


def test_misconception_examples_are_mathematically_false() -> None:
    # The examples must demonstrate actual wrong reasoning, not a true statement.
    assert Fraction(1, 5) + Fraction(2, 5) != Fraction(3, 10)
    assert Fraction(2, 3) != Fraction(4, 3)
    assert not (Fraction(1, 8) > Fraction(1, 3))
    assert Fraction(1, 4) != Fraction(1, 5)
    assert not (Fraction(4, 5) > Fraction(5, 6))
    misconceptions = SUPPORT["misconceptions"]
    assert len({x["misconception_id"] for x in misconceptions}) == 5
    assert all(
        x["incorrect"] and x["diagnostic"] and x["correct"] and x["remediation"]
        and x["review_status"] == "PENDING"
        for x in misconceptions
    )


def test_misconception_diagnostics_exact_oracles() -> None:
    assert Fraction(2, 6) + Fraction(3, 6) == Fraction(5, 6)
    assert Fraction(3, 4) != Fraction(6, 4)
    assert Fraction(1, 4) > Fraction(1, 6)
    assert Fraction(3, 5) == 3 * Fraction(1, 5)
    assert 1 - Fraction(7, 8) < 1 - Fraction(5, 6)
