from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.pii_sanitizer import PIISanitizerMiddleware, sanitize_text


def test_sanitize_text_redacts_common_student_pii() -> None:
    raw = (
        "My name is Mary Jones. Email mary.jones@example.com, call (301) 555-0199, "
        "SSN 123-45-6789, and I live at 123 Main Street."
    )
    sanitized = sanitize_text(raw)

    assert "Mary Jones" not in sanitized
    assert "mary.jones@example.com" not in sanitized
    assert "301" not in sanitized
    assert "123-45-6789" not in sanitized
    assert "123 Main Street" not in sanitized
    assert "[REDACTED_NAME]" in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "[REDACTED_GOV_ID]" in sanitized
    assert "[REDACTED_ADDRESS]" in sanitized


def test_middleware_only_rewrites_free_text_fields() -> None:
    app = FastAPI()
    app.add_middleware(PIISanitizerMiddleware)

    @app.post("/echo")
    async def echo(payload: dict) -> dict:
        return payload

    client = TestClient(app)
    response = client.post(
        "/echo",
        json={
            "email": "parent@example.com",
            "prompt": "My email is child@example.com and phone is 301-555-0123.",
            "metadata": {"message": "SSN 111-22-3333"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "parent@example.com"
    assert "child@example.com" not in body["prompt"]
    assert "301-555-0123" not in body["prompt"]
    assert "111-22-3333" not in body["metadata"]["message"]
