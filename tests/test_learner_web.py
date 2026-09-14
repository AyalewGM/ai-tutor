import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_learner_workspace_web_surface_is_problem_first() -> None:
    session_id = uuid.uuid4()
    response = client.get(f"/learn/{session_id}")

    assert response.status_code == 200
    assert "Current problem" in response.text
    assert "Submit answer" in response.text
    assert "I don't understand" in response.text
    assert "Assisted successes" in response.text
    assert "assisted success is not counted as independent mastery evidence" in response.text
    assert f"const sessionId = '{session_id}'" in response.text
