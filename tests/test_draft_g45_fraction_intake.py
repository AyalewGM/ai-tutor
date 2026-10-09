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
