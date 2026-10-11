"""Review-gated conceptual depth and independent transfer for 18 draft generators."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from scripts.draft_word_problem_generators import STRUCTURES, generate

LESSONS_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/curriculum/drafts/draft-word-problem-structures-v0"
    / "seeded_teaching_depth.draft.json"
)


def _load() -> dict:
    return json.loads(LESSONS_PATH.read_text(encoding="utf-8"))


def test_every_generator_has_a_distinct_review_gated_teaching_blueprint() -> None:
    data = _load()
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["review_status"] == "PENDING"
    assert data["runtime_activation"] is False
    assert data["canonical_skill_ids"] == []
    assert data["curriculum_mappings"] == []
    lessons = data["lessons"]
    assert len(lessons) == len(STRUCTURES) == 18
    assert {x["problem_structure"] for x in lessons} == set(STRUCTURES)
    assert len({x["lesson_id"] for x in lessons}) == len(lessons)
    assert len({x["conceptual_invariant"] for x in lessons}) == len(lessons)
    assert len({x["misconception_intervention"] for x in lessons}) == len(lessons)
    families = {
        item["problem_structure"]: item["provisional_skill"]
        for item in generate(17, 1)["items"]
    }
    assert len({x["provisional_skill"] for x in lessons}) == 6
    for lesson in lessons:
        assert lesson["provisional_skill"] == families[lesson["problem_structure"]]
        assert lesson["status"] == "DRAFT_UNVERIFIED"
        assert lesson["review_status"] == "PENDING"
        assert lesson["runtime_activation"] is False
        assert lesson["independent_review_required"] is True
        assert all(lesson["representations"].values())
        assert lesson["alternative_strategy"]
        assert lesson["misconception_intervention"]
        assert len(lesson["socratic_questions"]) == 3
        assert all(lesson["socratic_questions"])
        assert len(lesson["adaptive_path"]) == 5
        assert all(lesson["adaptive_path"].values())
        assert lesson["accessibility"]["text_alternative"]
        assert lesson["transfer_mastery"]["separate_from_generator"] is True
        assert len(lesson["transfer_mastery"]["required_evidence"]) == 3


def test_transfer_items_are_independent_of_generated_training_examples() -> None:
    lessons = _load()["lessons"]
    questions = [x["transfer_mastery"]["question"] for x in lessons]
    assert len(set(questions)) == 18
    for seed in (0, 1, 17, 20261009):
        training = {x["question"] for x in generate(seed, 6)["items"]}
        assert not (training & set(questions))


def test_independent_transfer_answer_oracles() -> None:
    # Calculate answers from separately authored problem statements, not the
    # generator output, to catch errors in lesson transfer answer keys.
    independently_computed = {
        "add-start-unknown": Fraction(187 - 68),
        "add-comparison": Fraction(236 - 179),
        "add-two-changes": Fraction(230 + 95 - 78),
        "multiply-equal-groups": Fraction(9 * 17),
        "multiply-remainder-capacity": Fraction((83 + 9 - 1) // 9),
        "multiply-two-stage": Fraction(5 * 6 * 8),
        "fraction-of-set": Fraction(5 * 64, 8),
        "fraction-unknown-whole": Fraction(21 * 7, 3),
        "fraction-like-addition": Fraction(7 + 5, 12),
        "ratio-unit-price": Fraction(104, 8),
        "ratio-percent-discount": Fraction(160 * (100 - 25), 100),
        "ratio-fixed-fee": Fraction(14 + 6 * 9),
        "geometry-perimeter": Fraction(2 * (23 + 8)),
        "geometry-area": Fraction(17 * 12),
        "geometry-volume": Fraction(8 * 5 * 7),
        "algebra-unknown-start": Fraction(95 - 18, 7),
        "algebra-linear-pattern": Fraction(11 + (14 - 1) * 6),
        "algebra-two-ticket-types": Fraction(276 - 24 * 9, 15 - 9),
    }
    lessons = _load()["lessons"]
    assert set(independently_computed) == {x["problem_structure"] for x in lessons}
    for lesson in lessons:
        actual = Fraction(lesson["transfer_mastery"]["expected"])
        assert actual == independently_computed[lesson["problem_structure"]]
        assert actual >= 0
