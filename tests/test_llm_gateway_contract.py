from fastapi.testclient import TestClient

from services.llm_gateway.main import app

client = TestClient(app)


def test_gateway_health_and_readiness() -> None:
    assert client.get("/health").json() == {"status": "ok"}
    readiness = client.get("/ready").json()
    assert readiness["status"] == "ready"
    assert readiness["provider"] in {"fallback", "none", "openai", "gemini"}


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
    body = response.json()
    assert body["expects_student_response"] is True
    assert body["request_id"]
    assert body["provider"] in {"fallback", "none", "openai", "gemini"}
    assert isinstance(body["latency_ms"], int)
    assert set(body) == {
        "message",
        "expects_student_response",
        "request_id",
        "provider",
        "model",
        "latency_ms",
    }


def test_gateway_accepts_cpa_level_and_prompt_carries_cpa_contract() -> None:
    from services.llm_gateway.main import RenderRequest, _prompt

    response = client.post(
        "/v1/render",
        json={
            "action": "GIVE_HINT",
            "curriculum_name": "Ontario Grade 9 Mathematics",
            "grade_level": "9",
            "skill_name": "Linear relations",
            "problem_prompt": "Solve 2x + 3 = 11.",
            "hint_level": 1,
            "cpa_level": "PICTORIAL",
        },
    )
    assert response.status_code == 200
    request = RenderRequest(
        action="GIVE_HINT",
        curriculum_name="c",
        grade_level="8",
        skill_name="s",
        problem_prompt="p",
        cpa_level="PICTORIAL",
    )
    prompt = _prompt(request)
    assert "json:cpa" in prompt
    assert "PICTORIAL" in prompt
    assert "lean toward" in prompt


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
