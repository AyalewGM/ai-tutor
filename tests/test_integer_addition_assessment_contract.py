"""Backend-only draft regressions for signed-integer addition assessment.

These tests exercise the existing assessment-item service without production
records, client hints or a newly activated canonical identity.  The isolated
PostgreSQL regression constructs its own tutoring and mastery evidence and
proves an assessment response cannot rewrite it.  They DO NOT verify the full
HTTP journey or cross-endpoint concurrency: those remain owner/QA acceptance
gates.
"""

from __future__ import annotations

import os
import re
import uuid
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from app.canonical_problem_families import LearningMode, generate
from app.diagnostic_models import DiagnosticAttempt, DiagnosticSession
from app.effectiveness_api import AssessmentItemOut, RecordResponseRequest
from app.effectiveness_models import (
    AssessmentItem,
    AssessmentPhase,
    AssessmentStatus,
    LearningAssessment,
)
from app.models import (
    Attempt,
    Curriculum,
    MasteryEvent,
    Problem,
    Skill,
    Student,
    StudentSkill,
    TutorSession,
)
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


def _rows(session: Session, model: type, *criteria: object) -> list[dict]:
    """Return stable, full-row snapshots for exact synthetic evidence rows."""
    table = model.__table__
    statement = select(table).where(*criteria).order_by(*table.primary_key.columns)
    return [dict(row) for row in session.execute(statement).mappings()]


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


def test_assessment_submission_preserves_existing_tutoring_and_mastery_evidence() -> None:
    """Commit a response while proving all pre-existing evidence is unchanged.

    The safety opt-in is shared with the repository's isolated PostgreSQL
    evidence regressions.  Every learner row is synthetic and is deleted by
    primary key after the assertion; this test must never target production.
    """
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires TEST_DATABASE_URL for an isolated PostgreSQL DB")
    if os.getenv("MIHUR_GATE4_ISOLATED_DB") != "1":
        pytest.skip("Requires explicit MIHUR_GATE4_ISOLATED_DB=1 safety opt-in")
    assert url.startswith(
        ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
    )
    engine = create_engine(url)
    suffix = uuid.uuid4().hex.upper()
    fixture_ready = False
    ids: dict[str, uuid.UUID] = {}

    try:
        with Session(engine) as db:
            curriculum = db.scalar(select(Curriculum).limit(1))
            assert curriculum is not None, "CI must seed a local curriculum"

            skill = Skill(
                curriculum_id=curriculum.id,
                code=f"ASSESS.INT.ADD.{suffix}",
                name="Synthetic signed-integer assessment skill",
                description="Isolated backend evidence-preservation fixture",
                difficulty_level=2,
            )
            student = Student(
                curriculum_id=curriculum.id,
                first_name="Assessment synthetic",
                grade_level="7",
            )
            db.add_all([skill, student])
            db.flush()

            problem = Problem(
                primary_skill_id=skill.id,
                problem_type="SIGNED_INTEGER_ADDITION",
                difficulty=2,
                prompt="Compute -3 + 5.",
                canonical_answer="2",
                solution={"fixture": "assessment-evidence-preservation"},
            )
            tutor = TutorSession(
                student_id=student.id,
                primary_skill_id=skill.id,
                active_skill_id=skill.id,
                curriculum_id=curriculum.id,
            )
            diagnostic = DiagnosticSession(
                student_id=student.id,
                target_skill_id=skill.id,
                current_skill_id=skill.id,
                curriculum_id=curriculum.id,
            )
            db.add_all([problem, tutor, diagnostic])
            db.flush()

            attempt = Attempt(
                session_id=tutor.id,
                student_id=student.id,
                problem_id=problem.id,
                student_answer="2",
                normalized_answer="2",
                is_correct=True,
                attempt_number=1,
                assistance_level=1,
            )
            diagnostic_attempt = DiagnosticAttempt(
                diagnostic_session_id=diagnostic.id,
                skill_id=skill.id,
                problem_id=problem.id,
                student_answer="2",
                normalized_answer="2",
                is_correct=True,
                evaluation_confidence=Decimal("1.000"),
                sequence_number=1,
            )
            mastery = StudentSkill(
                student_id=student.id,
                skill_id=skill.id,
                mastery_score=Decimal("0.625"),
                confidence_score=Decimal("0.750"),
                attempt_count=4,
                correct_count=3,
                independent_attempt_count=2,
                independent_correct_count=1,
                hinted_correct_count=2,
                current_difficulty=2,
            )
            db.add_all([attempt, diagnostic_attempt, mastery])
            db.flush()

            mastery_event = MasteryEvent(
                student_id=student.id,
                skill_id=skill.id,
                attempt_id=attempt.id,
                previous_score=Decimal("0.500"),
                new_score=Decimal("0.625"),
                previous_confidence=Decimal("0.625"),
                new_confidence=Decimal("0.750"),
                reason="synthetic-historical-evidence",
                metadata_json={"fixture": "assessment-evidence-preservation"},
            )
            assessment = LearningAssessment(
                student_id=student.id,
                skill_id=skill.id,
                phase=AssessmentPhase.POST_INSTRUCTION,
                status=AssessmentStatus.IN_PROGRESS,
                family_codes_used=[FAMILY],
                assessment_mode="INDEPENDENT",
                coverage_sufficient=False,
                requested_item_count=1,
                available_distinct_families=1,
                items_total=1,
            )
            db.add_all([mastery_event, assessment])
            db.flush()

            item, _ = _make_item(f"db-preservation-{suffix}")
            item.assessment_id = assessment.id
            db.add(item)
            db.flush()
            ids = {
                "skill": skill.id,
                "student": student.id,
                "problem": problem.id,
                "tutor": tutor.id,
                "diagnostic": diagnostic.id,
                "attempt": attempt.id,
                "diagnostic_attempt": diagnostic_attempt.id,
                "mastery_event": mastery_event.id,
                "assessment": assessment.id,
                "item": item.id,
            }
            db.commit()
            fixture_ready = True

        with Session(engine) as db:
            filters = {
                "attempts": (Attempt, Attempt.id == ids["attempt"]),
                "diagnostic_attempts": (
                    DiagnosticAttempt,
                    DiagnosticAttempt.id == ids["diagnostic_attempt"],
                ),
                "mastery_events": (
                    MasteryEvent,
                    MasteryEvent.id == ids["mastery_event"],
                ),
                "student_skills": (
                    StudentSkill,
                    StudentSkill.student_id == ids["student"],
                    StudentSkill.skill_id == ids["skill"],
                ),
            }
            before = {
                name: _rows(db, model, *criteria)
                for name, (model, *criteria) in filters.items()
            }
            assert all(len(rows) == 1 for rows in before.values())

            persisted_item = db.get(AssessmentItem, ids["item"])
            assert persisted_item is not None
            record_item_response(
                db,
                item=persisted_item,
                student_answer=persisted_item.canonical_answer,
            )
            db.commit()

            after = {
                name: _rows(db, model, *criteria)
                for name, (model, *criteria) in filters.items()
            }
            assert after == before

            persisted_item = db.get(AssessmentItem, ids["item"])
            assert persisted_item is not None
            assert persisted_item.is_correct is True
            assert persisted_item.assistance_level == 0
            assert persisted_item.answered_at is not None
    finally:
        if fixture_ready:
            with engine.begin() as connection:
                connection.execute(
                    delete(AssessmentItem).where(AssessmentItem.id == ids["item"])
                )
                connection.execute(
                    delete(LearningAssessment).where(
                        LearningAssessment.id == ids["assessment"]
                    )
                )
                connection.execute(
                    delete(MasteryEvent).where(
                        MasteryEvent.id == ids["mastery_event"]
                    )
                )
                connection.execute(
                    delete(DiagnosticAttempt).where(
                        DiagnosticAttempt.id == ids["diagnostic_attempt"]
                    )
                )
                connection.execute(
                    delete(Attempt).where(Attempt.id == ids["attempt"])
                )
                connection.execute(
                    delete(StudentSkill).where(
                        StudentSkill.student_id == ids["student"],
                        StudentSkill.skill_id == ids["skill"],
                    )
                )
                connection.execute(
                    delete(DiagnosticSession).where(
                        DiagnosticSession.id == ids["diagnostic"]
                    )
                )
                connection.execute(
                    delete(TutorSession).where(TutorSession.id == ids["tutor"])
                )
                connection.execute(
                    delete(Problem).where(Problem.id == ids["problem"])
                )
                connection.execute(
                    delete(Student).where(Student.id == ids["student"])
                )
                connection.execute(delete(Skill).where(Skill.id == ids["skill"]))
        engine.dispose()
