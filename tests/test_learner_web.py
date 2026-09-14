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


def test_learner_surfaces_include_accessibility_and_responsive_baseline() -> None:
    entry = client.get("/learn")
    workspace = client.get(f"/learn/{uuid.uuid4()}")

    assert entry.status_code == 200
    assert workspace.status_code == 200

    for html in (entry.text, workspace.text):
        assert 'name="viewport" content="width=device-width, initial-scale=1"' in html
        assert ":focus-visible" in html
        assert "min-height: 44px" in html
        assert 'role="alert" aria-live="assertive"' in html

    assert '<label for="studentId">Learner ID</label>' in entry.text
    assert '<label for="skillId">Skill ID</label>' in entry.text
    assert '<label for="answer"><strong>Your answer</strong></label>' in workspace.text
    assert 'role="status" aria-live="polite"' in workspace.text
    assert '@media (max-width: 600px)' in workspace.text
    assert '.actions button { flex: 1 1 100%; }' in workspace.text
