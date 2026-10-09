"""Independent arithmetic and reasoning-structure checks for draft word problems."""
from __future__ import annotations

import json
import math
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/draft-word-problem-structures-v0/content.draft.json"
)
DATA = json.loads(PATH.read_text(encoding="utf-8"))


def exact_answer(item: dict) -> str:
    op = item["operation"]
    a = item["operands"]
    if op == "add":
        value = a[0] + a[1]
    elif op == "subtract":
        value = a[0] - a[1]
    elif op == "add_subtract":
        value = a[0] + a[1] - a[2]
    elif op == "subtract_three":
        value = a[0] - a[1] - a[2]
    elif op == "multiply":
        value = a[0] * a[1]
    elif op == "divide":
        value = Fraction(a[0], a[1])
    elif op == "ceil_divide":
        value = math.ceil(Fraction(a[0], a[1]))
    elif op == "multiply_three":
        value = math.prod(a)
    elif op == "fraction_of":
        value = Fraction(a[0] * a[2], a[1])
    elif op == "fraction_remaining":
        value = Fraction((a[1] - a[0]) * a[2], a[1])
    elif op in {"fraction_times", "whole_from_part"}:
        value = Fraction(a[0] * a[2], a[1])
    elif op == "fraction_part_total":
        value = Fraction(a[0], a[1])
    elif op == "fraction_difference":
        value = Fraction(a[0], a[1]) - Fraction(a[2], a[3])
    elif op == "fraction_add_subtract":
        value = (
            Fraction(a[0], a[1]) - Fraction(a[2], a[3])
            + Fraction(a[4], a[5])
        )
    elif op == "cents_unit":
        value = Decimal(a[0]) / Decimal(a[1] * 100)
    elif op == "scale":
        value = Fraction(a[0] * a[2], a[1])
    elif op == "ratio_share":
        value = Fraction(a[0] * a[2], a[1] + a[2])
    elif op == "discount":
        value = Fraction(a[0] * (100 - a[1]), 100)
    elif op == "increase":
        value = Fraction(a[0] * (100 + a[1]), 100)
    elif op == "rate_time":
        value = Fraction(a[0] * a[1], a[2])
    elif op == "fixed_rate":
        value = a[0] + a[1] * a[2]
    elif op == "inverse_rate":
        value = Fraction(a[2] * a[1], a[0])
    elif op == "perimeter_missing":
        value = Fraction(a[0], 2) - a[1]
    elif op == "composite_area":
        value = a[0] * a[1] + a[2] * a[3]
    elif op == "area_difference":
        value = a[0] * a[1] - a[2] * a[3]
    elif op == "metres_cm":
        value = a[0] * 100 + a[1]
    elif op == "elapsed_after_three":
        value = a[0] + a[1] - 60
    elif op == "volume":
        value = math.prod(a)
    elif op == "square_area_increase":
        value = a[1] ** 2 - a[0] ** 2
    elif op == "linear_one":
        value = Fraction(a[2] - a[1], a[0])
    elif op == "two_plans":
        value = Fraction(a[2] - a[0], a[1] - a[3])
    elif op == "consecutive_three":
        value = Fraction(a[0] - 3, 3) + 2
    elif op == "arithmetic_pattern":
        value = a[0] + a[1] * (a[2] - 1)
    elif op == "linear_decrease":
        value = Fraction(a[0] - a[2], a[1])
    elif op == "ticket_system":
        value = Fraction(a[3] - a[0] * a[2], a[1] - a[2])
    elif op == "ceil_threshold":
        value = math.ceil(Fraction(a[2] - a[0], a[1]))
    elif op == "slope":
        value = Fraction(a[2] - a[0], a[3] - a[1])
    else:
        raise AssertionError(f"Unrecognized operation: {op}")
    if item["answer_contract"] == "decimal_2_places":
        assert isinstance(value, Decimal)
        return f"{value:.2f}"
    if item["answer_contract"] == "simplest_fraction":
        assert isinstance(value, Fraction)
        assert value.denominator > 1
        return f"{value.numerator}/{value.denominator}"
    assert Fraction(value).denominator == 1
    return str(int(value))


def test_draft_structure_and_isolation() -> None:
    assert DATA["status"] == "DRAFT_UNVERIFIED"
    assert DATA["review_status"] == "PENDING"
    assert DATA["runtime_activation"] is False
    assert DATA["canonical_skill_ids"] == []
    assert DATA["curriculum_mappings"] == []
    items = DATA["practice_items"]
    assert len(items) == 48
    assert len({item["item_id"] for item in items}) == 48
    assert len({item["question"] for item in items}) == 48
    assert len(DATA["coverage"]) == 6
    for item in items:
        assert len(item["hints"]) == 3
        assert all(item["hints"])
        assert item["worked_solution"]
        assert item["misconception_tag"]
        assert item["review_status"] == "PENDING"


def test_distinct_reasoning_structures_per_family() -> None:
    for coverage in DATA["coverage"]:
        items = [
            x for x in DATA["practice_items"]
            if x["provisional_skill"] == coverage["provisional_skill"]
        ]
        assert len(items) == 8
        assert len(set(coverage["structures"])) == 8
        assert {x["problem_structure"] for x in items} == set(
            coverage["structures"]
        )


def test_exact_oracle_for_every_word_problem() -> None:
    for item in DATA["practice_items"]:
        assert item["expected"] == exact_answer(item)


def test_word_problem_interpretation_edge_cases() -> None:
    by_structure = {
        x["problem_structure"]: x for x in DATA["practice_items"]
    }
    assert by_structure["remainder-interpretation"]["expected"] == "10"
    assert by_structure["fraction-multi-step"]["expected"] == "3/4"
    assert by_structure["elapsed-time"]["expected"] == "80"
    assert by_structure["inequality-minimum"]["expected"] == "8"
    assert by_structure["fraction-of-unknown-whole"]["expected"] == "28"
    assert by_structure["two-unknowns"]["expected"] == "20"


PATHWAYS = json.loads(
    (PATH.parent / "adaptive_pathways.draft.json").read_text(encoding="utf-8")
)


def test_every_word_problem_has_a_diagnostic_and_mastery_path() -> None:
    assert PATHWAYS["status"] == "DRAFT_UNVERIFIED"
    assert PATHWAYS["review_status"] == "PENDING"
    assert PATHWAYS["runtime_activation"] is False
    assert PATHWAYS["canonical_skill_ids"] == []
    assert PATHWAYS["curriculum_mappings"] == []
    by_id = {item["item_id"]: item for item in DATA["practice_items"]}
    paths = PATHWAYS["pathways"]
    assert len(paths) == 48
    assert len({path["pathway_id"] for path in paths}) == 48
    assert {path["linked_item_id"] for path in paths} == set(by_id)
    for path in paths:
        item = by_id[path["linked_item_id"]]
        diagnostic = path["diagnostic"]
        learning = path["learning_path"]
        mastery = path["mastery_exit"]
        assert path["review_status"] == "PENDING"
        assert path["provisional_skill"] == item["provisional_skill"]
        assert path["problem_structure"] == item["problem_structure"]
        assert len(diagnostic["choices"]) == 3
        assert len(set(diagnostic["choices"])) == 3
        assert diagnostic["correct_index"] in {0, 1, 2}
        correct_setup = diagnostic["choices"][diagnostic["correct_index"]]
        assert correct_setup in diagnostic["explanation"]
        assert correct_setup in learning["remediation_sequence"][1]
        assert len(diagnostic["misconception_distractors"]) == 2
        assert {x["choice_index"] for x in diagnostic["misconception_distractors"]} == (
            {0, 1, 2} - {diagnostic["correct_index"]}
        )
        assert all(x["feedback"] for x in diagnostic["misconception_distractors"])
        assert item["question"] in diagnostic["prompt"]
        assert item["worked_solution"] in diagnostic["explanation"]
        assert len(learning["remediation_sequence"]) == 3
        assert all(learning["remediation_sequence"])
        assert learning["remediation_trigger"] == item["misconception_tag"]
        assert learning["concrete_visual_model"]
        assert learning["alternative_method"]
        assert mastery["expected_answer"] == item["expected"]
        assert mastery["independent_review_required"] is True
        assert len(mastery["required_evidence"]) == 3


def test_diagnostics_use_distinct_setups_for_every_structure() -> None:
    correct = [
        path["diagnostic"]["choices"][path["diagnostic"]["correct_index"]]
        for path in PATHWAYS["pathways"]
    ]
    assert len(set(correct)) == len(correct)


def test_diagnostic_answer_positions_are_balanced() -> None:
    positions = [
        path["diagnostic"]["correct_index"]
        for path in PATHWAYS["pathways"]
    ]
    assert [positions.count(i) for i in range(3)] == [16, 16, 16]


LESSONS = json.loads(
    (PATH.parent / "teaching_lessons.draft.json").read_text(encoding="utf-8")
)


def test_six_concrete_visual_symbolic_teaching_lessons() -> None:
    assert LESSONS["status"] == "DRAFT_UNVERIFIED"
    assert LESSONS["runtime_activation"] is False
    assert LESSONS["canonical_skill_ids"] == []
    assert LESSONS["curriculum_mappings"] == []
    lessons = LESSONS["lessons"]
    assert len(lessons) == 6
    assert len({x["lesson_id"] for x in lessons}) == 6
    assert {x["skill"] for x in lessons} == {
        x["provisional_skill"] for x in DATA["coverage"]
    }
    for lesson in lessons:
        assert lesson["status"] == "DRAFT_UNVERIFIED"
        assert lesson["review_status"] == "PENDING"
        assert lesson["activation"] is False
        assert lesson["concrete"] and lesson["visual"] and lesson["symbolic"]
        assert lesson["alternative"] and lesson["self_check"]
        assert lesson["diagnosis"] and lesson["remediation"]
        assert len(lesson["socratic"]) == 3
        assert lesson["mastery"] and lesson["mastery_answer"]


def test_teaching_lesson_mastery_exits_have_independent_oracles() -> None:
    answers = {
        "ADDITIVE_WORD_PROBLEMS": 121 - 78,
        "MULTIPLICATIVE_WORD_PROBLEMS": math.ceil(Fraction(65, 12)),
        "FRACTION_WORD_PROBLEMS": Fraction(15 * 8, 3),
        "RATIO_RATE_WORD_PROBLEMS": 6 + 5 * 8,
        "GEOMETRY_MEASUREMENT_WORD_PROBLEMS": Fraction(68, 2) - 14,
        "ALGEBRA_REASONING_WORD_PROBLEMS": Fraction(303 - 25 * 9, 15 - 9),
    }
    for lesson in LESSONS["lessons"]:
        assert lesson["mastery_answer"] == str(int(answers[lesson["skill"]]))
