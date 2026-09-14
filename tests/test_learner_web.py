import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_learner_entry_uses_server_validated_session_creation() -> None:
    response = client.get("/learn")

    assert response.status_code == 200
    assert "Start a learning session" in response.text
    assert "Learner ID" in response.text
    assert "Skill ID" in response.text
    assert "Curriculum scope and the first diagnostic problem are validated by the server" in response.text
    assert "'/api/v1/adaptive-tutor/sessions'" in response.text
    assert "window.location.assign(`/learn/${body.session_id}`)" in response.text


def test_learner_workspace_web_surface_is_problem_first() -> None:
    session_id = uuid.uuid4()
    response = client.get(f"/learn/{session_id}")

    assert response.status_code == 200
    assert "Current problem" in response.text
    assert "Submit answer" in response.text
    assert "I don't understand" in response.text
    assert "Assisted successes" in response.text
    assert "assisted success is not counted as independent mastery evidence" in response.text
    assert f'const sessionId = "{session_id}"' in response.text
