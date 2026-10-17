# ruff: noqa: I001

import uuid

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.content_models import ProblemContentMetadata
from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Attempt,
    Curriculum,
    MasteryEvent,
    Problem,
    Skill,
    Student,
    StudentSkill,
    TutorState,
)
from tests.auth_helpers import authenticate_parent_for_student


client = TestClient(app)


def _seed_student_with_extension_problem():
    """A student on M8.ALG.DIST plus one opt-in extension problem."""
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_MATH_8")
        )
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.DIST"))
        assert curriculum is not None and skill is not None

        student = Student(
            curriculum_id=curriculum.id,
            first_name="Extension Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        db.refresh(student)

        prompt = (
            "Challenge: distribute across a two-step context: "
            "3(x + 2) - (x - 4) = 20. Solve for x."
        )
        ext = db.scalar(
            select(Problem).where(
                Problem.primary_skill_id == skill.id,
                Problem.prompt == prompt,
            )
        )
        if ext is None:
            ext = Problem(
                primary_skill_id=skill.id,
                problem_type="WORD_PROBLEM",
                difficulty=9,
                prompt=prompt,
                canonical_answer="5",
                source_type="CURATED",
                solution={
                    "provenance": {
                        "origin": "AUTHORED",
                        "author": "Mihur test suite",
                        "license": "Internal test fixture",
                        "source_uri": "https://github.com/AyalewGM/ai-tutor",
                    }
                },
            )
            db.add(ext)
            db.flush()
            db.add(
                ProblemContentMetadata(
                    problem_id=ext.id,
                    curriculum_id=curriculum.id,
                    objective="Stretch: multi-step distribution above mastery band.",
                    evaluation_type="DETERMINISTIC",
                    extension_eligible=True,
                )
            )
        db.commit()
        return student.id, skill.id, ext.id


def test_extension_opt_in_and_evidence_isolation() -> None:
    student_id, skill_id, _ = _seed_student_with_extension_problem()

    session_response = client.post(
        "/api/v1/tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert session_response.status_code == 200
    session_payload = session_response.json()
    session_id = session_payload["session_id"]

    # Explicit opt-in serves an extension problem; normal selection did not.
    ext_response = client.post(f"/api/v1/tutor/sessions/{session_id}/extension")
    assert ext_response.status_code == 200
    ext_id = uuid.UUID(ext_response.json()["id"])
    assert session_payload["problem"]["id"] != str(ext_id)
    with SessionLocal() as db:
        meta = db.scalar(
            select(ProblemContentMetadata).where(
                ProblemContentMetadata.problem_id == ext_id
            )
        )
        assert meta is not None and meta.extension_eligible is True

    with SessionLocal() as db:
        progress_before = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        assert progress_before is not None
        mastery_before = progress_before.mastery_score
        attempts_before = progress_before.attempt_count
        state_before = db.scalar(
            select(func.count()).select_from(Attempt).where(
                Attempt.session_id == uuid.UUID(session_id)
            )
        )

    response = client.post(
        f"/api/v1/tutor/sessions/{session_id}/respond",
        json={
            "problem_id": str(ext_id),
            "answer": "5",
            "assistance_level": 0,
        },
    )
    assert response.status_code == 200
    assert response.json()["evaluation"]["correct"] is True

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        # No mastery movement, no evidence counters.
        assert progress.mastery_score == mastery_before
        assert progress.attempt_count == attempts_before

        # Attempt persisted for audit, tagged EXTENSION.
        attempt = db.scalar(
            select(Attempt).where(
                Attempt.session_id == uuid.UUID(session_id),
                Attempt.problem_id == ext_id,
            )
        )
        assert attempt is not None
        assert attempt.state_at_attempt == TutorState.EXTENSION
        assert db.scalar(
            select(func.count()).select_from(Attempt).where(
                Attempt.session_id == uuid.UUID(session_id)
            )
        ) == state_before + 1

        # No mastery events were created for the extension attempt.
        assert db.scalar(
            select(func.count()).select_from(MasteryEvent).where(
                MasteryEvent.attempt_id == attempt.id
            )
        ) == 0


def test_extension_falls_back_to_generated_problem() -> None:
    """When the authored extension pool is empty for a skill, opt-in should
    still serve a generated stretch item tagged extension_eligible so fast
    learners never hit a ceiling."""
    from decimal import Decimal

    code = f"TEST.EXT.GEN.{uuid.uuid4().hex[:8]}"
    with SessionLocal() as db:
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == "MCPS_MATH_8")
        )
        assert curriculum is not None
        skill = Skill(
            curriculum_id=curriculum.id,
            code=code,
            name="Extension generation fallback probe",
            description="Test skill with no authored extension problems",
            difficulty_level=Decimal("1.0"),
            mastery_threshold=Decimal("0.850"),
        )
        db.add(skill)
        db.flush()
        # A generator-capable problem type is what makes the fallback work.
        db.add(
            Problem(
                primary_skill_id=skill.id,
                problem_type="SOLVE_EQUATION",
                difficulty=3,
                prompt="Solve for x: x + 4 = 11.",
                canonical_answer="x=7",
                source_type="CURATED",
                solution={
                    "provenance": {
                        "origin": "AUTHORED",
                        "author": "Mihur synthetic test fixture",
                        "license": "Internal test fixture",
                        "source_uri": "https://github.com/AyalewGM/ai-tutor",
                    }
                },
            )
        )
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Extension Gen Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        db.refresh(student)
        db.commit()
        student_id, skill_id = student.id, skill.id

    session_response = client.post(
        "/api/v1/tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]

    ext_response = client.post(f"/api/v1/tutor/sessions/{session_id}/extension")
    assert ext_response.status_code == 200
    ext_id = uuid.UUID(ext_response.json()["id"])

    with SessionLocal() as db:
        problem = db.get(Problem, ext_id)
        assert problem is not None
        assert problem.source_type == "GENERATED"
        assert problem.primary_skill_id == skill_id
        meta = db.scalar(
            select(ProblemContentMetadata).where(
                ProblemContentMetadata.problem_id == ext_id
            )
        )
        assert meta is not None and meta.extension_eligible is True


def test_extension_endpoint_on_adaptive_router() -> None:
    """The frontend talks to /adaptive-tutor — the same opt-in must work,
    and answering through the adaptive router must stay evidence-free."""
    student_id, skill_id, _ = _seed_student_with_extension_problem()

    session_response = client.post(
        "/api/v1/adaptive-tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]

    ext_response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/extension"
    )
    assert ext_response.status_code == 200
    ext_id = uuid.UUID(ext_response.json()["id"])
    with SessionLocal() as db:
        meta = db.scalar(
            select(ProblemContentMetadata).where(
                ProblemContentMetadata.problem_id == ext_id
            )
        )
        assert meta is not None and meta.extension_eligible is True
        progress_before = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        mastery_before = progress_before.mastery_score
        attempts_before = progress_before.attempt_count

    respond = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/respond",
        json={"problem_id": str(ext_id), "answer": "5", "assistance_level": 0},
    )
    assert respond.status_code == 200

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        assert progress.mastery_score == mastery_before
        assert progress.attempt_count == attempts_before
        attempt = db.scalar(
            select(Attempt).where(
                Attempt.session_id == uuid.UUID(session_id),
                Attempt.problem_id == ext_id,
            )
        )
        assert attempt is not None
        assert attempt.state_at_attempt == TutorState.EXTENSION
        # The adaptive respond path must not write a MasteryEvent either.
        assert db.scalar(
            select(func.count()).select_from(MasteryEvent).where(
                MasteryEvent.attempt_id == attempt.id
            )
        ) == 0


def test_extension_attempt_does_not_change_session_state() -> None:
    student_id, skill_id, ext_id = _seed_student_with_extension_problem()

    session_response = client.post(
        "/api/v1/tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert session_response.status_code == 200
    session_payload = session_response.json()
    session_id = session_payload["session_id"]
    state_before = session_payload["state"]

    offered = client.post(f"/api/v1/tutor/sessions/{session_id}/extension")
    assert offered.status_code == 200
    ext_id = uuid.UUID(offered.json()["id"])

    response = client.post(
        f"/api/v1/tutor/sessions/{session_id}/respond",
        json={
            "problem_id": str(ext_id),
            "answer": "5",
            "assistance_level": 0,
        },
    )
    assert response.status_code == 200

    with SessionLocal() as db:
        from app.models import TutorSession

        session = db.get(TutorSession, uuid.UUID(session_id))
        # The optional tier is progression-neutral: a correct stretch answer
        # cannot advance the learner's real session state.
        assert session.current_state.value == state_before

@pytest.mark.parametrize("router", ["tutor", "adaptive-tutor"])
def test_extension_response_requires_server_owned_session_offer(router: str) -> None:
    """Global eligibility cannot make an arbitrary client problem mastery-neutral."""

    student_id, skill_id, ext_id = _seed_student_with_extension_problem()
    session_response = client.post(
        f"/api/v1/{router}/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        assert progress is not None
        snapshot = (
            progress.mastery_score,
            progress.confidence_score,
            progress.attempt_count,
            progress.independent_attempt_count,
        )

    response = client.post(
        f"/api/v1/{router}/sessions/{session_id}/respond",
        json={
            "problem_id": str(ext_id),
            "answer": "5",
            "assistance_level": 0,
        },
    )
    assert response.status_code == 400
    assert "not offered to this learning session" in response.json()["detail"]

    with SessionLocal() as db:
        progress = db.get(
            StudentSkill, {"student_id": student_id, "skill_id": skill_id}
        )
        assert progress is not None
        assert (
            progress.mastery_score,
            progress.confidence_score,
            progress.attempt_count,
            progress.independent_attempt_count,
        ) == snapshot
        assert db.scalar(
            select(func.count()).select_from(Attempt).where(
                Attempt.session_id == uuid.UUID(session_id),
                Attempt.problem_id == ext_id,
            )
        ) == 0


def test_extension_offer_is_bound_to_the_exact_session() -> None:
    student_id, skill_id, _ = _seed_student_with_extension_problem()

    first = client.post(
        "/api/v1/tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    second = client.post(
        "/api/v1/tutor/sessions",
        json={"student_id": str(student_id), "skill_id": str(skill_id)},
    )
    assert first.status_code == second.status_code == 200
    first_session = first.json()["session_id"]
    second_session = second.json()["session_id"]

    offered = client.post(f"/api/v1/tutor/sessions/{first_session}/extension")
    assert offered.status_code == 200
    offered_problem_id = offered.json()["id"]

    replay = client.post(
        f"/api/v1/tutor/sessions/{second_session}/respond",
        json={
            "problem_id": offered_problem_id,
            "answer": "5",
            "assistance_level": 0,
        },
    )
    assert replay.status_code == 400
    assert "not offered to this learning session" in replay.json()["detail"]

    with SessionLocal() as db:
        assert db.scalar(
            select(func.count()).select_from(Attempt).where(
                Attempt.session_id == uuid.UUID(second_session),
                Attempt.problem_id == uuid.UUID(offered_problem_id),
            )
        ) == 0

