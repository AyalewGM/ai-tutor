"""Synthetic issuance evidence checks; no production question issuance or writes."""
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.models import TutorState
from app.services.fraction_assessment_registry import AssessmentMode
from app.services.issued_rational_evidence import (
    ISSUANCE_VERSION,
    verify_fresh_issuance,
)


def fixture():
    student_id, session_id, problem_id = uuid4(), uuid4(), uuid4()
    problem = SimpleNamespace(
        id=problem_id, solution={
            "variant_id": "v1", "task_fingerprint": "unique-fp",
        },
    )
    turn = SimpleNamespace(
        role="SYSTEM", pedagogical_action="ISSUE_ASSESSMENT",
        state=TutorState.INDEPENDENT_PRACTICE,
        metadata_json={
            "issuance_contract": ISSUANCE_VERSION,
            "student_id": str(student_id), "problem_id": str(problem_id),
            "variant_id": "v1", "task_fingerprint": "unique-fp",
            "mode": "independent",
        },
    )
    db = Mock()
    db.scalar.side_effect = [None, None]
    db.scalars.return_value.all.return_value = [turn]
    return db, student_id, session_id, problem, turn


def check(db, student, session, problem, mode=AssessmentMode.INDEPENDENT):
    return verify_fresh_issuance(
        db, student_id=student, session_id=session,
        problem=problem, mode=mode,
    )


def test_single_fresh_issued_item_matches():
    db, student, session, problem, _ = fixture()
    assert check(db, student, session, problem)
    assert db.scalar.call_count == 2


def test_cross_session_attempt_or_diagnostic_replay_denied():
    for previous in ([uuid4()], [None, uuid4()]):
        db, student, session, problem, _ = fixture()
        db.scalar.side_effect = previous
        assert not check(db, student, session, problem)


def test_missing_duplicate_or_wrong_issuance_denied():
    for change in ("none", "duplicate", "wrong_mode", "wrong_fingerprint", "hint"):
        db, student, session, problem, turn = fixture()
        if change == "none":
            db.scalars.return_value.all.return_value = []
        elif change == "duplicate":
            db.scalars.return_value.all.return_value = [turn, turn]
        elif change == "wrong_mode":
            turn.metadata_json["mode"] = "guided"
        elif change == "wrong_fingerprint":
            turn.metadata_json["task_fingerprint"] = "reused"
        else:
            turn.pedagogical_action = "HINT"
        assert not check(db, student, session, problem)


def test_guided_mode_cannot_be_fresh_independent_evidence():
    db, student, session, problem, _ = fixture()
    assert not check(db, student, session, problem, AssessmentMode.GUIDED)
    db.scalar.assert_not_called()


def test_non_assisted_learner_turn_does_not_hide_issuance():
    db, student, session, problem, issued = fixture()
    learner_turn = SimpleNamespace(
        role="STUDENT", pedagogical_action="ANSWER_INPUT",
        state=TutorState.INDEPENDENT_PRACTICE, metadata_json={},
    )
    db.scalars.return_value.all.return_value = [issued, learner_turn]
    assert check(db, student, session, problem)


def test_assistance_turn_blocks_independent_scoring():
    for action in ("HINT", "GUIDED_REPAIR", "SHOW_SOLUTION", "SCAFFOLD"):
        db, student, session, problem, issued = fixture()
        assistance = SimpleNamespace(
            role="ASSISTANT", pedagogical_action=action,
            state=TutorState.GUIDED_PRACTICE, metadata_json={},
        )
        db.scalars.return_value.all.return_value = [issued, assistance]
        assert not check(db, student, session, problem)
