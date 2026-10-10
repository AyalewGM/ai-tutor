"""Backend-only draft regressions for signed-integer addition assessment.

These tests exercise the existing assessment-item service without a database,
production records, client hints or a newly activated canonical identity.
They DO NOT verify the full HTTP journey, cross-endpoint concurrency, or
mastery-ledger isolation: those remain owner/QA acceptance gates.
"""

from __future__ import annotations

import re
import uuid
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.canonical_problem_families import LearningMode, generate
from app.effectiveness_api import AssessmentItemOut, RecordResponseRequest
from app.effectiveness_models import AssessmentItem
from app.services.learning_assessment import record_item_response


FAMILY = "MATH.INT.ADD"
# The independent oracle parses integer operands from the actual prompt;
# it does not read the generated canonical_answer to compute its expectation.
INTEGER_SUM = re.compile(r"Compute (-?\d+) \+ (?:\((-?\d+)\)|(-?\d+))\.")


def _make_item(seed: str) -> tuple[AssessmentItem, object]:
    problem = generate(FAMILY, seed=seed, difficulty=2, mode=LearningMode.DIAGNOSTIC)
    item = AssessmentItem(
        id=uuid.uuid4(),
        assessment_id=uuid.uuid4(),
        sequence_number=1,
        family_code=FAMILY,
        variant_id=problem.variant_id,
        generation_seed=seed,
        difficulty=2,
        prompt=problem.prompt,
        canonical_answer=problem.canonical_answer,
        student_answer=None,
    )
    return item, problem


@pytest.mark.parametrize("seed", [
    "int-assess-0", "int-assess-1", "int-assess-2", "int-assess-3",
    "int-assess-7", "int-assess-17", "int-assess-97", "int-assess-113",
])
def test_integer_addition_exact_oracle_independently_recomputes_sum(seed: str) -> None:
    item, _ = _make_item(seed)
    match = INTEGER_SUM.fullmatch(item.prompt)
    assert match is not None, f"Unrecognized addition form: {item.prompt}"
    left = int(match.group(1))
    right = int(match.group(2) or match.group(3))
    assert int(item.canonical_answer) == left + right


def test_new_seed_is_replayable_without_exposing_generation_seed_to_client() -> None:
    a, _ = _make_item("unseen-eval-a")
    again, _ = _make_item("unseen-eval-a")
    b, _ = _make_item("unseen-eval-b")
    assert (a.prompt, a.canonical_answer, a.variant_id) == (
        again.prompt, again.canonical_answer, again.variant_id
    )
    assert a.variant_id != b.variant_id
    fields = AssessmentItemOut.model_fields
    assert "canonical_answer" not in fields
    assert "generation_seed" not in fields
    assert "variant_id" not in fields
    assert "hints" not in fields
    assert set(RecordResponseRequest.model_fields) == {"student_answer"}


def test_backend_records_correct_answer_as_unassisted_without_mastery_writes() -> None:
    item, _ = _make_item("correct-path")
    db = Mock(spec=Session)
    result = record_item_response(
        db, item=item, student_answer=item.canonical_answer
    )
    assert result.is_correct is True
    assert result.assistance_level == 0
    assert result.student_answer == item.canonical_answer
    assert result.answered_at is not None
    # This is service-level evidence only; HTTP/mastery endpoints need DB E2E.
    db.add.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize("invalid_answer", ["not-a-number", "NaN", "3.14159", ""])
def test_backend_rejects_invalid_integer_responses(invalid_answer: str) -> None:
    item, _ = _make_item("invalid-answer-case")
    record_item_response(Mock(spec=Session), item=item, student_answer=invalid_answer)
    assert item.is_correct is False
    assert item.assistance_level == 0


def test_signed_integer_misconception_is_scored_not_tutored() -> None:
    item, problem = _make_item("wrong-sign-case")
    misconception_answer = problem.misconception_answers["INT.ADD.WRONG_SIGN"]
    record_item_response(
        Mock(spec=Session), item=item, student_answer=misconception_answer
    )
    assert item.is_correct is False
    assert item.misconception_code == "INT.ADD.WRONG_SIGN"
    assert item.assistance_level == 0


def test_repeated_item_submission_fails_closed_in_sequential_service_use() -> None:
    item, _ = _make_item("sequential-replay")
    db = Mock(spec=Session)
    record_item_response(db, item=item, student_answer=item.canonical_answer)
    snapshot = (item.student_answer, item.is_correct, item.answered_at)
    with pytest.raises(ValueError, match="already answered"):
        record_item_response(db, item=item, student_answer="999999")
    assert (item.student_answer, item.is_correct, item.answered_at) == snapshot


def test_tampered_persisted_answer_fails_before_grading_or_mutation() -> None:
    item, _ = _make_item("tampered-answer")
    item.canonical_answer = "obviously-invalid"
    db = Mock(spec=Session)
    with pytest.raises(RuntimeError, match="reconstruction mismatch"):
        record_item_response(db, item=item, student_answer="42")
    assert item.student_answer is None
    assert item.is_correct is None
    db.add.assert_not_called()
    db.commit.assert_not_called()
