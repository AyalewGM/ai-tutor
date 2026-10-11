"""Independent, exact verification of 48 draft unseen transfer assessment exits.

This validates authored content only. Production response projection and
trusted mastery scoring remain Assessment Backend/Muse responsibilities.
"""
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs/curriculum/drafts/draft-word-problem-structures-v0"


def _data(name: str) -> dict:
    return json.loads((DRAFT / name).read_text(encoding="utf-8"))


def _exact(operation: str, v: list[int]) -> Fraction:
    """Independent Fraction-based oracle that does not invoke draft generators."""
    a = v[0]
    b = v[1] if len(v) > 1 else None
    c = v[2] if len(v) > 2 else None
    d = v[3] if len(v) > 3 else None
    if operation == "add":
        return Fraction(a + b)
    if operation == "subtract":
        return Fraction(a - b)
    if operation == "add_subtract":
        return Fraction(a + b - c)
    if operation == "subtract_three":
        return Fraction(a - b - c)
    if operation == "multiply":
        return Fraction(a * b)
    if operation == "divide":
        return Fraction(a, b)
    if operation == "ceil_divide":
        return Fraction(-(-a // b))
    if operation == "multiply_three":
        return Fraction(a * b * c)
    if operation == "fraction_of":
        return Fraction(a * c, b)
    if operation == "fraction_remaining":
        return Fraction((b - a) * c, b)
    if operation == "fraction_times":
        return Fraction(a * c, b)
    if operation == "whole_from_part":
        return Fraction(a * c, b)
    if operation == "fraction_part_total":
        return Fraction(a, b)
    if operation == "fraction_difference":
        return Fraction(a, b) - Fraction(c, d)
    if operation == "fraction_add_subtract":
        return Fraction(a, b) - Fraction(c, d) + Fraction(v[4], v[5])
    if operation == "cents_unit":
        return Fraction(a, b * 100)
    if operation == "scale":
        return Fraction(a * c, b)
    if operation == "ratio_share":
        return Fraction(a * c, b + c)
    if operation == "discount":
        return Fraction(a * (100 - b), 100)
    if operation == "increase":
        return Fraction(a * (100 + b), 100)
    if operation == "rate_time":
        return Fraction(a * b, c)
    if operation == "fixed_rate":
        return Fraction(a + b * c)
    if operation == "inverse_rate":
        return Fraction(b * c, a)
    if operation == "perimeter_missing":
        return Fraction(a, 2) - b
    if operation == "composite_area":
        return Fraction(a * b + c * d)
    if operation == "area_difference":
        return Fraction(a * b - c * d)
    if operation == "metres_cm":
        return Fraction(a * 100 + b)
    if operation == "elapsed_after_three":
        # Scenario explicitly begins in the 2 PM hour.
        return Fraction(b - (60 - a))
    if operation == "volume":
        return Fraction(a * b * c)
    if operation == "square_area_increase":
        return Fraction(b * b - a * a)
    if operation == "linear_one":
        return Fraction(c - b, a)
    if operation == "two_plans":
        return Fraction(c - a, b - d)
    if operation == "consecutive_three":
        return Fraction(a, 3) + 1
    if operation == "arithmetic_pattern":
        return Fraction(a + b * (c - 1))
    if operation == "linear_decrease":
        return Fraction(a - c, b)
    if operation == "ticket_system":
        # Solve adult+child=total, adultPrice*adult+childPrice*child=revenue.
        return Fraction(d - a * c, b - c)
    if operation == "ceil_threshold":
        return Fraction(max(0, -(-(c - a) // b)))
    if operation == "slope":
        return Fraction(c - a, d - b)
    raise AssertionError(f"Unknown draft operation: {operation}")


def test_all_48_unseen_exits_exact_and_no_assessment_setup_leakage():
    original = _data("content.draft.json")["practice_items"]
    document = _data("adaptive_pathways.draft.json")
    paths = document["pathways"]
    assert len(paths) == len(original) == 48
    assert document["runtime_activation"] is False
    assert document["assessment_exit_correction"]["backend_trusted_scoring"] == (
        "PENDING_ASSESSMENT_BACKEND_IMPLEMENTATION"
    )
    for source, path in zip(original, paths, strict=True):
        assert path["linked_item_id"] == source["item_id"]
        exit_item = path["mastery_exit"]
        oracle = exit_item["teacher_oracle_server_only"]
        numbers = exit_item["variant_operands_server_only"]
        assert numbers != source["operands"]
        assert exit_item["prompt"] != source["question"]
        assert source["question"] not in exit_item["prompt"]
        assert source["worked_solution"] not in exit_item["prompt"]
        assert "correct setup" not in exit_item["prompt"].lower()
        assert "=" not in exit_item["prompt"]
        assert Fraction(oracle["exact_answer"]) == _exact(source["operation"], numbers)
        assert Fraction(exit_item["expected_answer"]) == _exact(source["operation"], numbers)
        assert exit_item["status"] == "DRAFT_UNVERIFIED"
        assert exit_item["runtime_activation"] is False
        assert exit_item["independent_review_required"] is True
        assert len(exit_item["required_evidence"]) >= 3
        fields = set(exit_item["learner_payload_contract"]["fields"])
        omit = set(exit_item["learner_payload_contract"]["omit"])
        assert fields <= {"assessment_item_id", "question", "response_contract"}
        assert {"expected_answer", "teacher_oracle_server_only", "variant_operands_server_only",
                "worked_solution", "hints", "correct_setup"} <= omit
        assert fields.isdisjoint(omit)


def test_geometry_and_remaining_fraction_hints_are_semantically_correct():
    generator = (ROOT / "scripts/draft_word_problem_generators.py").read_text()
    wave2 = (ROOT / "scripts/draft_depth_generators_wave2.py").read_text()
    assert "square centimetres per layer." not in generator
    assert "base area (cm²)" in generator
    assert "Find the number used, not the remainder." not in wave2
    assert "problem asks for the remainder" in wave2
