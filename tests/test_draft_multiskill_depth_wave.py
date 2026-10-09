"""Exact independent oracle for the draft multi-skill content-depth wave."""
from __future__ import annotations

import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/draft-multiskill-depth-wave-v0/content.draft.json"
)
DATA = json.loads(PATH.read_text(encoding="utf-8"))
LEVELS = [
    "fluency", "guided-representation", "contextual-transfer", "error-analysis"
]
OPERATIONS = {
    "add", "subtract", "multiply", "divide", "fraction_add",
    "decimal_cents_add", "perimeter", "area"
}


def expected_from_operands(item: dict) -> str:
    op = item["operation"]
    v = item["operands"]
    if op == "add":
        return str(v["a"] + v["b"])
    if op == "subtract":
        return str(v["a"] - v["b"])
    if op == "multiply":
        return str(v["a"] * v["b"])
    if op == "divide":
        quotient, remainder = divmod(v["a"], v["b"])
        assert remainder == 0
        return str(quotient)
    if op == "fraction_add":
        value = Fraction(v["a"] + v["b"], v["d"])
        return f"{value.numerator}/{value.denominator}"
    if op == "decimal_cents_add":
        value = Decimal(v["a_cents"] + v["b_cents"]) / Decimal(100)
        return f"{value:.2f}"
    if op == "perimeter":
        return str(2 * (v["length"] + v["width"]))
    if op == "area":
        return str(v["length"] * v["width"])
    raise AssertionError(f"Unknown operation: {op}")


def test_draft_isolation_and_depth_inventory() -> None:
    assert DATA["status"] == "DRAFT_UNVERIFIED"
    assert DATA["review_status"] == "PENDING"
    assert DATA["runtime_activation"] is False
    assert DATA["canonical_skill_ids"] == []
    assert DATA["curriculum_mappings"] == []
    items = DATA["practice_items"]
    assert len(items) == 64
    assert len({x["item_id"] for x in items}) == 64
    assert len({x["question"] for x in items}) == 64
    assert {x["operation"] for x in items} == OPERATIONS
    assert len(DATA["difficulty_ladders"]) == 8
    assert len(DATA["misconceptions"]) == 8
    assert all(
        len(x["hints"]) == 3
        and all(x["hints"])
        and x["worked_solution"]
        and x["misconception_tag"]
        and x["review_status"] == "PENDING"
        for x in items
    )


def test_exact_oracles_for_every_draft_problem() -> None:
    for item in DATA["practice_items"]:
        assert item["expected"] == expected_from_operands(item)
        if item["operation"] == "fraction_add":
            assert item["answer_contract"] == "simplest_fraction"
            assert Fraction(item["expected"]) > 0
        elif item["operation"] == "decimal_cents_add":
            assert item["answer_contract"] == "decimal_2_places"
            assert len(item["expected"].split(".")[1]) == 2
        else:
            assert item["answer_contract"] == "integer"


def test_every_skill_has_complete_difficulty_progression() -> None:
    by_id = {x["item_id"]: x for x in DATA["practice_items"]}
    for ladder in DATA["difficulty_ladders"]:
        assert ladder["levels"] == LEVELS
        assert len(ladder["items"]) == 8
        assert [
            by_id[item_id]["level"] for item_id in ladder["items"]
        ] == [level for level in LEVELS for _ in range(2)]
        assert all(
            by_id[item_id]["provisional_skill"] == ladder["provisional_skill"]
            for item_id in ladder["items"]
        )


MVE = json.loads(
    (PATH.parent / "interactive_mve.draft.json").read_text(encoding="utf-8")
)


def test_interactive_storyboards_are_accessible_and_draft_only() -> None:
    assert MVE["status"] == "DRAFT_UNVERIFIED"
    assert MVE["review_status"] == "PENDING"
    specs = MVE["specs"]
    assert len(specs) == 8
    assert len({spec["spec_id"] for spec in specs}) == 8
    assert {spec["provisional_skill"] for spec in specs} == {
        x["provisional_skill"] for x in DATA["difficulty_ladders"]
    }
    for spec in specs:
        assert spec["activation"] is False
        assert spec["review_status"] == "PENDING"
        assert len(spec["states"]) == 3
        assert [state["name"] for state in spec["states"]] == [
            "observe", "manipulate", "reflect"
        ]
        assert all(state["narration"] for state in spec["states"])
        assert spec["mathematical_invariant"]
        assert spec["misconception_feedback"]
        assert spec["assessment_prompt"]
        assert all(spec["accessibility"].values())


ADAPTIVE = json.loads(
    (PATH.parent / "adaptive_teaching.draft.json").read_text(encoding="utf-8")
)


def test_every_skill_item_has_a_linked_adaptive_pathway() -> None:
    assert ADAPTIVE["status"] == "DRAFT_UNVERIFIED"
    assert ADAPTIVE["review_status"] == "PENDING"
    assert ADAPTIVE["runtime_activation"] is False
    assert ADAPTIVE["canonical_skill_ids"] == []
    assert ADAPTIVE["curriculum_mappings"] == []
    items = {x["item_id"]: x for x in DATA["practice_items"]}
    paths = ADAPTIVE["pathways"]
    assert len(paths) == 64
    assert len({x["pathway_id"] for x in paths}) == 64
    assert {x["linked_item_id"] for x in paths} == set(items)
    for path in paths:
        item = items[path["linked_item_id"]]
        assert path["provisional_skill"] == item["provisional_skill"]
        assert path["level"] == item["level"]
        assert path["misconception_trigger"] == item["misconception_tag"]
        assert [x["id"] for x in path["adaptive_stages"]] == [
            "diagnose", "represent", "visualize", "symbolize", "verify"
        ]
        assert all(x["instruction"] for x in path["adaptive_stages"])
        assert len(path["branch_on_incorrect"]) == 3
        assert all(path["branch_on_incorrect"].values())
        assert all(path["branch_on_correct"].values())
        assert path["mastery_evidence"]["correct_answer"] == item["expected"]
        assert path["mastery_evidence"]["require_explanation"] is True
        assert path["mastery_evidence"]["require_independent_check"] is True
        assert path["mastery_evidence"]["require_unseen_transfer"] is True


def test_diagnostic_answer_keys_and_misconception_feedback() -> None:
    diagnostics = ADAPTIVE["diagnostics"]
    assert len(diagnostics) == 8
    assert {x["provisional_skill"] for x in diagnostics} == {
        x["provisional_skill"] for x in DATA["difficulty_ladders"]
    }
    for diag in diagnostics:
        assert diag["review_status"] == "PENDING"
        assert len(diag["choices"]) == 3
        assert len(set(diag["choices"])) == 3
        assert diag["choices"][diag["correct_index"]] == diag["expected"]
        assert {x["choice_index"] for x in diag["incorrect_feedback"]} == (
            {0, 1, 2} - {diag["correct_index"]}
        )
        assert all(x["feedback"] for x in diag["incorrect_feedback"])
        assert diag["concrete"] and diag["visual"] and diag["symbolic"]
        assert diag["alternative_method"] and diag["independent_check"]
        assert diag["transfer"]["question"]
    assert {x["correct_index"] for x in diagnostics} == {0, 1, 2}


def test_diagnostics_and_unseen_transfer_exact_oracles() -> None:
    diagnostic_expected = {
        "ADDITION_REGROUP": ("125", "124"),
        "SUBTRACTION_REGROUP": ("145", "236"),
        "MULTIPLICATION_GROUPS": ("104", "112"),
        "DIVISION_GROUPS": ("12", "12"),
        "LIKE_FRACTION_ADDITION": ("1", "1"),
        "DECIMAL_ADDITION": ("8.43", "9.61"),
        "RECTANGLE_PERIMETER": ("46", "54"),
        "RECTANGLE_AREA": ("126", "180"),
    }
    for diag in ADAPTIVE["diagnostics"]:
        key = diag["provisional_skill"]
        expected, transfer = diagnostic_expected[key]
        assert diag["expected"] == expected
        assert diag["transfer"]["expected"] == transfer
        operands = diag["operands"]
        op = diag["operation"]
        if op == "fraction_add":
            from fractions import Fraction

            actual = Fraction(operands["a"] + operands["b"], operands["d"])
            assert str(actual) == expected
        else:
            item = {"operation": op, "operands": operands}
            assert expected_from_operands(item) == expected


def test_unseen_transfer_questions_are_not_repeated_practice_items() -> None:
    existing = {x["question"] for x in DATA["practice_items"]}
    transfers = [x["transfer"]["question"] for x in ADAPTIVE["diagnostics"]]
    assert len(set(transfers)) == 8
    assert not (set(transfers) & existing)
