from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_parent_dashboard_web_surface_exposes_required_controls() -> None:
    response = client.get("/parent")
    assert response.status_code == 200
    assert "Parent Dashboard" in response.text
    assert "childSelect" in response.text
    assert "claimToken" in response.text
    assert "Remove selected child" in response.text
    assert "evidence-backed learning progress" in response.text


def test_parent_dashboard_is_summary_first_and_keeps_evidence_distinctions_visible() -> None:
    response = client.get("/parent")
    assert response.status_code == 200
    assert "Learning summary" in response.text
    assert "Independent mastery" in response.text
    assert "Independent progress" in response.text
    assert "Assisted success" in response.text
    assert "Insufficient evidence" in response.text
    assert "Limited observations are shown as insufficient evidence rather than as a weakness" in response.text
    assert "learning_state === 'INDEPENDENT_MASTERY'" in response.text
    assert "evidence_status === 'INSUFFICIENT_EVIDENCE'" in response.text


def test_parent_dashboard_renders_only_bounded_backend_action_codes() -> None:
    response = client.get("/parent")
    assert response.status_code == 200
    assert "Skill progress and next steps" in response.text
    assert "Suggested next step:" in response.text
    assert "COLLECT_MORE_EVIDENCE" in response.text
    assert "ENCOURAGE_INDEPENDENT_ATTEMPT" in response.text
    assert "RECOGNIZE_INDEPENDENT_PROGRESS" in response.text
    assert "RECOGNIZE_MASTERY" in response.text
    assert "FOLLOW_EXISTING_REVIEW_PLAN" in response.text
    assert "View supporting evidence" in response.text
    assert "Reason:" in response.text


def test_parent_dashboard_surfaces_reviews_due_and_recommendation() -> None:
    response = client.get("/parent")
    assert response.status_code == 200
    assert "Reviews due" in response.text
    assert "Recommended next" in response.text
    assert "d.reviews_due" in response.text
    assert "d.recommended_next" in response.text
    assert "projected_mastery_score" in response.text


def test_parent_dashboard_uses_goozam_derived_visual_tokens_and_accessible_interactions() -> None:
    response = client.get("/parent")
    assert response.status_code == 200
    assert "--goozam-blue" in response.text
    assert "--goozam-indigo" in response.text
    assert "--goozam-purple" in response.text
    assert "linear-gradient" in response.text
    assert "min-height: 44px" in response.text
    assert ":focus-visible" in response.text
    assert 'aria-live="assertive"' in response.text
    assert 'aria-labelledby="summaryHeading"' in response.text


def test_parent_settings_web_surface_exposes_profile_controls() -> None:
    response = client.get("/parent/settings")
    assert response.status_code == 200
    assert "Parent Settings" in response.text
    assert "displayName" in response.text
    assert "Save" in response.text
