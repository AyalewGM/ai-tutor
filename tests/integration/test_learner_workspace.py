import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.auth import SESSION_COOKIE
from app.auth import create_session as create_auth_session
from app.core.database import SessionLocal
from app.hint_models import HintEvent
from app.main import app
from app.models import (
    Attempt,
    Curriculum,
    LearnerAward,
    MasteryEvent,
    Misconception,
    Problem,
    Skill,
    SkillStatus,
    Student,
    StudentSkill,
    TutorSession,
    TutorState,
    TutorTurn,
    User,
)
from app.parent_models import ParentProfile
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _create_session() -> tuple[uuid.UUID, uuid.UUID]:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None
        assert skill is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Workspace Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        db.refresh(student)
        student_id = student.id
        skill_id = skill.id

    response = client.post(
        "/api/v1/tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert response.status_code == 200
    payload = response.json()
    return uuid.UUID(payload["session_id"]), student_id


def _evidence_counts(
    session_id: uuid.UUID,
    student_id: uuid.UUID,
) -> tuple[int, int, int]:
    with SessionLocal() as db:
        attempts = (
            db.scalar(select(func.count(Attempt.id)).where(Attempt.session_id == session_id)) or 0
        )
        mastery_events = (
            db.scalar(
                select(func.count(MasteryEvent.id)).where(MasteryEvent.student_id == student_id)
            )
            or 0
        )
        turns = (
            db.scalar(select(func.count(TutorTurn.id)).where(TutorTurn.session_id == session_id))
            or 0
        )
    return int(attempts), int(mastery_events), int(turns)


def test_workspace_refresh_is_read_only_and_assessment_safe() -> None:
    session_id, student_id = _create_session()
    before = _evidence_counts(session_id, student_id)

    first = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")
    second = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    payload = first.json()
    assert payload["state"] == "DIAGNOSE"
    assert payload["allowed_actions"] == ["SUBMIT_ANSWER"]
    assert payload["problem"] is not None
    assert payload["curriculum"]["id"]
    assert payload["focus"]["in_remediation"] is False
    assert _evidence_counts(session_id, student_id) == before


def test_workspace_derives_help_actions_from_backend_state() -> None:
    session_id, _ = _create_session()
    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        assert session is not None
        session.current_state = TutorState.GUIDED_PRACTICE
        db.commit()

    response = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["allowed_actions"] == [
        "SUBMIT_ANSWER",
        "REQUEST_HINT",
        "I_DONT_UNDERSTAND",
    ]


def test_i_dont_understand_is_recorded_as_assistance() -> None:
    session_id, _ = _create_session()
    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        assert session is not None
        session.current_state = TutorState.GUIDED_PRACTICE
        problem_id = db.scalar(
            select(TutorTurn.problem_id)
            .where(TutorTurn.session_id == session_id, TutorTurn.role == "TUTOR")
            .order_by(TutorTurn.created_at.desc())
            .limit(1)
        )
        assert problem_id is not None
        db.commit()

    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/hint",
        json={"problem_id": str(problem_id), "reason": "I_DONT_UNDERSTAND"},
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is True
    assert response.json()["trigger"] == "I_DONT_UNDERSTAND"

    with SessionLocal() as db:
        event = db.scalar(
            select(HintEvent)
            .where(HintEvent.session_id == session_id, HintEvent.problem_id == problem_id)
            .order_by(HintEvent.created_at.desc())
            .limit(1)
        )
        assert event is not None
        assert event.trigger == "I_DONT_UNDERSTAND"


def test_workspace_exposes_smartscore_streak_and_level() -> None:
    session_id, student_id = _create_session()
    now = datetime.now(UTC)
    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        skill_id = session.active_skill_id or session.primary_skill_id
        problem = db.scalar(select(Problem).where(Problem.primary_skill_id == skill_id).limit(1))
        assert problem is not None
        progress = db.get(StudentSkill, {"student_id": student_id, "skill_id": skill_id})
        if progress is None:
            progress = StudentSkill(student_id=student_id, skill_id=skill_id)
            db.add(progress)
        progress.mastery_score = 0.72
        progress.status = SkillStatus.PRACTICING
        for offset, correct in [(0, False), (1, True), (2, True), (3, True)]:
            db.add(
                Attempt(
                    session_id=session_id,
                    student_id=student_id,
                    problem_id=problem.id,
                    student_answer="x",
                    is_correct=correct,
                    attempt_number=offset + 1,
                    created_at=now + timedelta(seconds=offset),
                )
            )
        db.commit()

    evidence = client.get(f"/api/v1/learner-workspace/sessions/{session_id}").json()["evidence"]
    assert evidence["smartscore"] == 72
    assert evidence["streak_count"] == 3  # trailing correct run; earlier miss ignored
    assert evidence["mastery_level"] == "proficient"

    with SessionLocal() as db:
        db.add(
            Attempt(
                session_id=session_id,
                student_id=student_id,
                problem_id=problem.id,
                student_answer="y",
                is_correct=False,
                attempt_number=5,
                created_at=now + timedelta(seconds=4),
            )
        )
        db.commit()
    evidence = client.get(f"/api/v1/learner-workspace/sessions/{session_id}").json()["evidence"]
    assert evidence["streak_count"] == 0


def test_other_family_cannot_read_hint_or_respond_to_session() -> None:
    session_id, _ = _create_session()
    with SessionLocal() as db:
        outsider = User(
            email=f"synthetic-outsider-{uuid.uuid4()}@example.com",
            display_name="Synthetic Unrelated Parent",
            role="PARENT",
        )
        db.add(outsider)
        db.flush()
        db.add(ParentProfile(user_id=outsider.id))
        token, _ = create_auth_session(db, outsider.id)
        db.commit()
        client.cookies.set(SESSION_COOKIE, token)

        session = db.get(TutorSession, session_id)
        assert session is not None
        problem_id = db.scalar(
            select(TutorTurn.problem_id)
            .where(TutorTurn.session_id == session_id, TutorTurn.role == "TUTOR")
            .order_by(TutorTurn.created_at.desc())
            .limit(1)
        )
        assert problem_id is not None

    workspace = client.get(f"/api/v1/learner-workspace/sessions/{session_id}")
    hint = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/hint",
        json={"problem_id": str(problem_id)},
    )
    respond = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": str(problem_id), "answer": "synthetic", "assistance_level": 0},
    )

    assert workspace.status_code == 404
    assert hint.status_code == 404
    assert respond.status_code == 404
    assert workspace.json()["detail"] == "Learner not found"
    assert hint.json()["detail"] == "Learner not found"
    assert respond.json()["detail"] == "Learner not found"


def test_daily_goal_patch_and_progress() -> None:
    session_id, student_id = _create_session()

    workspace = client.get(f"/api/v1/learner-workspace/sessions/{session_id}").json()
    assert workspace["daily_goal"] is None

    patched = client.patch(
        f"/api/v1/learner-workspace/sessions/{session_id}/daily-goal",
        json={"questions_per_day": 3},
    )
    assert patched.status_code == 200
    assert patched.json() == {"target": 3, "done": 0, "reached": False}

    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        problem = db.scalar(
            select(Problem).where(
                Problem.primary_skill_id == (session.active_skill_id or session.primary_skill_id)
            )
        )
        for n in range(3):
            db.add(
                Attempt(
                    session_id=session_id,
                    student_id=student_id,
                    problem_id=problem.id,
                    student_answer="x",
                    is_correct=True,
                    attempt_number=n + 1,
                )
            )
        db.commit()

    workspace = client.get(f"/api/v1/learner-workspace/sessions/{session_id}").json()
    assert workspace["daily_goal"] == {"target": 3, "done": 3, "reached": True}

    cleared = client.patch(
        f"/api/v1/learner-workspace/sessions/{session_id}/daily-goal",
        json={"questions_per_day": None},
    )
    assert cleared.status_code == 200
    assert cleared.json() is None
    workspace = client.get(f"/api/v1/learner-workspace/sessions/{session_id}").json()
    assert workspace["daily_goal"] is None


def test_session_summary_aggregates_evidence() -> None:
    session_id, student_id = _create_session()
    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        assert session is not None
        session.starting_mastery = 0.40
        skill_id = session.active_skill_id or session.primary_skill_id
        problem = db.scalar(select(Problem).where(Problem.primary_skill_id == skill_id).limit(1))
        assert problem is not None
        code = f"TEST_{uuid.uuid4().hex[:8]}"
        misconception = Misconception(
            skill_id=skill_id,
            code=code,
            name="Test slip",
            description="synthetic",
        )
        db.add(misconception)
        db.flush()
        db.add_all(
            [
                Attempt(
                    session_id=session_id,
                    student_id=student_id,
                    problem_id=problem.id,
                    student_answer="wrong",
                    is_correct=False,
                    attempt_number=1,
                    misconception_id=misconception.id,
                ),
                Attempt(
                    session_id=session_id,
                    student_id=student_id,
                    problem_id=problem.id,
                    student_answer="right",
                    is_correct=True,
                    attempt_number=2,
                ),
            ]
        )
        db.add(
            LearnerAward(
                student_id=student_id,
                badge_code="FIRST_CORRECT",
                skill_id=skill_id,
                session_id=session_id,
            )
        )
        progress = db.get(StudentSkill, {"student_id": student_id, "skill_id": skill_id})
        if progress is None:
            progress = StudentSkill(student_id=student_id, skill_id=skill_id)
            db.add(progress)
        progress.mastery_score = 0.55
        db.commit()

    response = client.get(f"/api/v1/learner-workspace/sessions/{session_id}/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["attempts"] == 2
    assert summary["correct"] == 1
    assert summary["independent_correct"] == 1
    assert summary["smartscore_start"] == 40
    assert summary["smartscore_now"] == 55
    assert summary["xp_earned"] > 0
    assert summary["minutes"] >= 0
    assert summary["misconceptions"] == [
        {"code": code, "name": "Test slip", "resolved": True}
    ]
    assert [a["code"] for a in summary["awards"]] == ["FIRST_CORRECT"]
    with SessionLocal() as db:
        skill_name = db.get(Skill, skill_id_for(session_id)).name
    assert summary["skills_practiced"] == [skill_name]


def skill_id_for(session_id: uuid.UUID) -> uuid.UUID:
    with SessionLocal() as db:
        session = db.get(TutorSession, session_id)
        return session.active_skill_id or session.primary_skill_id
