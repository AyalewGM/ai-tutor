"""Photo intake: OCR suggests lines, the deterministic checker still grades.

The scan endpoint returns reviewable lines only — nothing is persisted and
no step is graded until the learner confirms and the client submits each
line through the ordinary /work-step endpoint.
"""

import uuid
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.main import app
from app.models import (
    Curriculum,
    Problem,
    Skill,
    Student,
)
from app.services import photo_ocr
from app.services.photo_ocr import DisabledProvider, ScanResult, StubProvider
from tests.auth_helpers import authenticate_parent_for_student

client = TestClient(app)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@contextmanager
def _provider(provider):
    app.dependency_overrides[photo_ocr.get_ocr_provider] = lambda: provider
    try:
        yield
    finally:
        app.dependency_overrides.pop(photo_ocr.get_ocr_provider, None)


def _setup() -> tuple[str, uuid.UUID]:
    """A learner, an authenticated parent, a session, and a step-able problem."""
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(select(Skill).where(Skill.code == "M8.ALG.MULTI_STEP"))
        assert curriculum is not None and skill is not None
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Photo Learner",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        authenticate_parent_for_student(client, db, student)
        problem = Problem(
            primary_skill_id=skill.id,
            problem_type="SOLVE_EQUATION",
            difficulty=3,
            prompt="Solve 3x + 12 = 30.",
            canonical_answer="x=6",
            answer_kind="FREE_TEXT",
            source_type="TEST",
        )
        db.add(problem)
        db.commit()
        created = client.post(
            "/api/v1/adaptive-tutor/sessions",
            json={"student_id": str(student.id), "skill_id": str(skill.id)},
        )
        assert created.status_code == 200
        return created.json()["session_id"], problem.id


def _scan(session_id: str, problem_id: uuid.UUID, content_type: str = "image/png"):
    return client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/work-photo/scan",
        files={"file": ("work.png", PNG, content_type)},
        data={"problem_id": str(problem_id)},
    )


def test_scan_returns_editable_lines_without_grading() -> None:
    session_id, problem_id = _setup()
    with _provider(StubProvider()):
        response = _scan(session_id, problem_id)
    assert response.status_code == 200
    body = response.json()
    assert body["problem_id"] == str(problem_id)
    assert body["engine"] == "stub"
    assert [l["text"] for l in body["lines"]] == ["3x + 12 = 30", "3x = 18"]
    assert body["lines"][1]["needs_review"] is True

    # No WORK_STEP turns are written by the scan itself.
    with SessionLocal() as db:
        from app.models import TutorTurn

        turns = db.scalars(
            select(TutorTurn).where(
                TutorTurn.session_id == uuid.UUID(session_id),
                TutorTurn.pedagogical_action == "WORK_STEP",
            )
        ).all()
        assert turns == []

    # Confirmed lines grade through the ordinary work-step endpoint. The
    # first scanned line restates the problem (duplicate of the seed line);
    # the next line is a real step.
    restated = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/work-step",
        json={"problem_id": str(problem_id), "line": "3x + 12 = 30"},
    )
    assert restated.status_code == 200 and restated.json()["status"] == "duplicate"
    checked = client.post(
        f"/api/v1/adaptive-tutor/sessions/{session_id}/work-step",
        json={"problem_id": str(problem_id), "line": "3x = 18"},
    )
    assert checked.status_code == 200 and checked.json()["status"] == "valid"


def test_scan_rejects_bad_content_type_and_foreign_problem() -> None:
    session_id, problem_id = _setup()
    with _provider(StubProvider()):
        bad_type = _scan(session_id, problem_id, content_type="text/plain")
        assert bad_type.status_code == 415

        with SessionLocal() as db:
            curriculum_id = db.scalar(
                select(Skill.curriculum_id).where(Skill.code == "M8.ALG.MULTI_STEP")
            )
            assert curriculum_id is not None
            # Test-owned skill — fixture problems must never sit on a real
            # seeded skill's selection pool.
            foreign_skill = Skill(
                curriculum_id=curriculum_id,
                code=f"TEST.FOREIGN.{uuid.uuid4().hex[:8]}",
                name="Foreign test skill",
                difficulty_level=1,
            )
            db.add(foreign_skill)
            db.flush()
            foreign = Problem(
                primary_skill_id=foreign_skill.id,
                problem_type="SOLVE_EQUATION",
                difficulty=1,
                prompt="x + 1 = 2",
                canonical_answer="x=1",
                source_type="TEST",
            )
            db.add(foreign)
            db.commit()
            foreign_id = foreign.id
        assert _scan(session_id, foreign_id).status_code == 400


def test_scan_empty_read_is_422_and_disabled_is_503() -> None:
    class EmptyProvider:
        def scan(self, image: bytes, content_type: str) -> ScanResult:
            return ScanResult(lines=[], engine="stub")

    session_id, problem_id = _setup()
    with _provider(EmptyProvider()):
        assert _scan(session_id, problem_id).status_code == 422

    with _provider(DisabledProvider()):
        assert _scan(session_id, problem_id).status_code == 503


def test_scan_requires_auth() -> None:
    client.cookies.clear()
    response = client.post(
        f"/api/v1/adaptive-tutor/sessions/{uuid.uuid4()}/work-photo/scan",
        files={"file": ("work.png", PNG, "image/png")},
        data={"problem_id": str(uuid.uuid4())},
    )
    assert response.status_code in (401, 403)
