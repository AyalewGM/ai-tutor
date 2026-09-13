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
    assert "Curriculum and learning decisions are read-only here" in response.text
