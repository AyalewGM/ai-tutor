"""Exercise the running staging API with a new synthetic family; never print tokens/oracles.

Uses the actual selector, authenticated respond route, feedback and evidence writes.
This is HTTP evidence, not browser/accessibility acceptance. Synthetic history is retained.
"""
import json
import uuid

import httpx
from sqlalchemy import select, text

from app.auth import SESSION_COOKIE, create_session
from app.core.database import SessionLocal
from app.models import Attempt, Problem, Student, StudentSkill, User
from app.parent_models import ParentProfile
from app.services.content_publishing import resolve_skill, validate
from scripts.ops.publish_content import MANIFEST


def assert_public(payload):
    forbidden = {"canonical_answer", "solution", "manifest", "equation_coefficients",
                 "misconception_answers", "review_evidence", "canonical_source_key"}
    if isinstance(payload, dict):
        assert not forbidden.intersection(payload), "Private assessment fields leaked"
        for value in payload.values():
            assert_public(value)
    elif isinstance(payload, list):
        for value in payload:
            assert_public(value)


def probe():
    manifest = json.loads(MANIFEST.read_text())
    package_digest = validate(manifest)
    with SessionLocal.begin() as db:
        assert db.scalar(text("select current_database()")) == "mihur_staging"
        skill, _ = resolve_skill(db, manifest)
        skill_id, curriculum_id = skill.id, skill.curriculum_id
        parent = User(email=f"publisher-{uuid.uuid4().hex}@example.invalid", role="PARENT",
                      display_name="Publisher synthetic QA")
        db.add(parent)
        db.flush()
        db.add(ParentProfile(user_id=parent.id, approval_status="APPROVED",
                             coppa_consent_given=True, country_code="CA", region_code="ON"))
        student = Student(parent_id=parent.id, curriculum_id=curriculum_id,
                          first_name="Publisher synthetic QA", grade_level="9")
        db.add(student)
        db.flush()
        student_id = student.id
        db.add(StudentSkill(student_id=student.id, skill_id=skill_id, current_difficulty=3))
        token, _ = create_session(db, parent.id)
    seen, successful_modes, published_ids = set(), set(), []
    with httpx.Client(base_url="http://127.0.0.1:8000/api/v1", timeout=30,
                      headers={"Cookie": f"{SESSION_COOKIE}={token}"}) as client:
        response = client.post("/adaptive-tutor/sessions", json={
            "student_id": str(student_id), "skill_id": str(skill_id)})
        response.raise_for_status()
        payload = response.json()
        session_id, problem = payload["session_id"], payload["problem"]
        for _ in range(100):
            assert_public(payload)
            assert problem is not None, "Question pool exhausted before probe completion"
            problem_id = uuid.UUID(problem["id"])
            assert problem_id not in seen, "Practice repeated a previously answered problem"
            seen.add(problem_id)
            with SessionLocal() as db:
                row = db.get(Problem, problem_id)
                answer = row.canonical_answer
                published = row.source_type == "PUBLISHED"
                mode = (row.solution or {}).get("mode")
                if published:
                    assert row.solution["package_digest"] == package_digest
            response = client.post(f"/adaptive-tutor/sessions/{session_id}/respond", json={
                "problem_id": str(problem_id), "answer": answer, "assistance_level": 0})
            response.raise_for_status()
            payload = response.json()
            assert_public(payload)
            assert payload["evaluation"]["correct"] is True, "Exact answer rejected"
            assert payload["tutor"]["message"], "Missing learner feedback"
            if published:
                successful_modes.add(mode)
                published_ids.append(str(problem_id))
                replay = client.post(f"/adaptive-tutor/sessions/{session_id}/respond", json={
                    "problem_id": str(problem_id), "answer": answer})
                assert replay.status_code == 409, "Published replay accepted"
            if {"guided", "independent"} <= successful_modes and len(published_ids) >= 3:
                break
            problem = payload.get("next_problem")
        else:
            raise AssertionError("No completed guided and independent package practice within bound")
    with SessionLocal() as db:
        attempts = db.scalars(select(Attempt).where(Attempt.student_id == student_id)).all()
        assert len(attempts) == len(seen), "Missing or duplicate persisted attempts"
    return {"passed": True, "transport": "live authenticated HTTP",
            "browser_verified": False, "package_digest": package_digest,
            "synthetic_student_id": str(student_id), "questions_completed": len(seen),
            "published_questions_completed": len(published_ids), "modes": sorted(successful_modes)}


if __name__ == "__main__":
    try:
        print(json.dumps(probe()))
    except Exception:  # noqa: BLE001 - rollback/redact at command boundary
        # HTTP exceptions may include session URLs; keep operator output redacted.
        print(json.dumps({"passed": False, "reason": "Synthetic learner assertion failed"}))
        raise SystemExit(1) from None
