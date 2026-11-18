from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import Curriculum, Problem, Student
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)


def _curriculum() -> Curriculum:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        assert curriculum is not None
        db.expunge(curriculum)
        return curriculum


def _student(curriculum_id) -> str:
    with SessionLocal() as db:
        student = Student(
            curriculum_id=curriculum_id,
            first_name="Campaign Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        db.commit()
        db.refresh(student)
        return str(student.id)


def _problem(problem_id: str) -> Problem:
    with SessionLocal() as db:
        problem = db.get(Problem, problem_id)
        assert problem is not None
        db.expunge(problem)
        return problem


def _answer(problem: Problem) -> str:
    if problem.choices:
        for choice in problem.choices:
            if choice["id"] == problem.canonical_answer:
                return choice["id"]
    return problem.canonical_answer or ""


def _drive_campaign(campaign_id: str, *, always_correct: bool = True, limit: int = 40):
    """Answer questions until the campaign completes or the safety limit hits."""
    payload = None
    for _ in range(limit):
        state = client.get(f"/api/v1/diagnostics/campaigns/{campaign_id}")
        assert state.status_code == 200
        payload = state.json()
        if payload["status"] == "COMPLETED":
            return payload
        problem = _problem(payload["problem"]["id"])
        answer = _answer(problem) if always_correct else "I do not know"
        response = client.post(
            f"/api/v1/diagnostics/campaigns/{campaign_id}/respond",
            json={"problem_id": str(problem.id), "answer": answer},
        )
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] == "COMPLETED":
            return payload
    return payload


def test_campaign_start_is_idempotent_and_serves_a_problem() -> None:
    curriculum = _curriculum()
    student_id = _student(curriculum.id)

    created = client.post("/api/v1/diagnostics/campaigns", json={"student_id": student_id})
    assert created.status_code == 200
    payload = created.json()
    assert payload["status"] == "ACTIVE"
    assert payload["problem"] is not None
    assert payload["targets_planned"] > 0
    assert payload["current_skill"] is not None

    resumed = client.post("/api/v1/diagnostics/campaigns", json={"student_id": student_id})
    assert resumed.status_code == 200
    assert resumed.json()["campaign_id"] == payload["campaign_id"]


def test_campaign_completes_and_reports_strands() -> None:
    curriculum = _curriculum()
    student_id = _student(curriculum.id)

    created = client.post("/api/v1/diagnostics/campaigns", json={"student_id": student_id})
    assert created.status_code == 200
    campaign_id = created.json()["campaign_id"]

    payload = _drive_campaign(campaign_id)
    assert payload["status"] == "COMPLETED"
    assert payload["problem"] is None

    report = client.get(f"/api/v1/diagnostics/campaigns/{campaign_id}/report")
    assert report.status_code == 200
    body = report.json()
    assert body["question_count"] > 0
    assert body["strands"], "report should classify at least one strand"
    assert body["skills"], "report should list probed skills"

    for strand in body["strands"]:
        assert strand["readiness"] in {"STRONG", "DEVELOPING", "EMERGING", "NOT_PROBED"}
        assert strand["skills_probed"] >= 1
        assert strand["skills_total"] >= strand["skills_probed"]
    for skill in body["skills"]:
        assert skill["verdict"] in {"READY", "PARTIAL", "NOT_READY"}
        assert skill["correct_count"] + skill["incorrect_count"] >= 1

    # An all-correct run must never produce a gap verdict. Skills thin on
    # diagnostic items come back PARTIAL (inconclusive) rather than READY.
    assert all(skill["verdict"] in {"READY", "PARTIAL"} for skill in body["skills"])
    assert all(strand["readiness"] in {"STRONG", "DEVELOPING"} for strand in body["strands"])


def test_campaign_flags_gap_and_recommends_deepest_gap() -> None:
    curriculum = _curriculum()
    student_id = _student(curriculum.id)

    created = client.post("/api/v1/diagnostics/campaigns", json={"student_id": student_id})
    assert created.status_code == 200
    campaign_id = created.json()["campaign_id"]

    payload = _drive_campaign(campaign_id, always_correct=False)
    assert payload["status"] == "COMPLETED"

    report = client.get(f"/api/v1/diagnostics/campaigns/{campaign_id}/report")
    assert report.status_code == 200
    body = report.json()
    assert any(skill["verdict"] == "NOT_READY" for skill in body["skills"])
    assert body["recommended"] is not None

    gapped = [s for s in body["strands"] if s["readiness"] == "EMERGING"]
    for strand in gapped:
        assert strand["deepest_gap"] is not None
