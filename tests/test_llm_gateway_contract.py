from fastapi.testclient import TestClient

from services.llm_gateway.main import app

client = TestClient(app)


def test_gateway_health_and_readiness() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_gateway_accepts_application_computed_render_request() -> None:
    response = client.post(
        "/v1/render",
        json={
            "action": "GIVE_HINT",
            "curriculum_name": "Ontario Grade 9 Mathematics",
            "grade_level": "9",
            "skill_name": "Linear relations",
            "problem_prompt": "Find the rate of change.",
            "hint_level": 1,
            "hint_constraint": "Point to the two coordinate pairs without solving.",
        },
    )
    assert response.status_code == 200
    assert response.json()["expects_student_response"] is True


def test_gateway_rejects_pedagogical_authority_fields() -> None:
    payload = {
        "action": "GIVE_HINT",
        "curriculum_name": "Ontario Grade 9 Mathematics",
        "grade_level": "9",
        "skill_name": "Linear relations",
        "problem_prompt": "Find the rate of change.",
        "promote_mastery": True,
        "selected_prerequisite_id": "forbidden",
        "assessment_override": True,
    }
    response = client.post("/v1/render", json=payload)
    assert response.status_code == 422
