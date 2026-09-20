import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_learner_entry_uses_server_validated_session_creation() -> None:
    response = client.get("/learn")

    assert response.status_code == 200
    assert "Start a learning session" in response.text
    assert "learnerSelect" in response.text
    assert "skillSelect" in response.text
    assert "Pick a learner and a skill" in response.text
    assert "'/adaptive-tutor/sessions'" in response.text
    assert "window.location.assign(`/learn/${body.session_id}`)" in response.text
    assert "/onboarding/learners" in response.text
    assert "/login?next=/learn" in response.text


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


def test_learner_workspace_has_explicit_application_owned_mastery_result() -> None:
    response = client.get(f"/learn/{uuid.uuid4()}")

    assert response.status_code == 200
    assert 'id="completionPanel"' in response.text
    assert "Skill complete" in response.text
    assert "independently in the mastery check" in response.text
    assert "Help and hints do not count as mastery evidence" in response.text
    assert "const complete = data.state === 'COMPLETE';" in response.text
    assert "q('completionPanel').hidden = !complete;" in response.text
    assert "q('problemPanel').hidden = complete;" in response.text
    assert "data.state === 'COMPLETE'" in response.text


def test_learner_surfaces_use_goozam_tokens_and_surface_reviews() -> None:
    entry = client.get("/learn")
    workspace = client.get(f"/learn/{uuid.uuid4()}")
    login = client.get("/login")
    assert login.status_code == 200
    for html in (entry.text, workspace.text, login.text):
        assert "--goozam-blue" in html
        assert "--goozam-indigo" in html
        assert "--goozam-purple" in html
        assert "linear-gradient" in html
    assert "data.reviews_due" in workspace.text
    assert "data.recommended_next" in workspace.text
    assert "reviewBanner" in workspace.text


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

    assert '<label for="learnerSelect">Learner</label>' in entry.text
    assert '<label for="skillSelect">Skill</label>' in entry.text
    assert '<label for="answer"><strong>Your answer</strong></label>' in workspace.text
    assert 'role="status" aria-live="polite"' in workspace.text
    assert '@media (max-width: 600px)' in workspace.text
    assert '.actions button { flex: 1 1 100%; }' in workspace.text
