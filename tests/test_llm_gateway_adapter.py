import httpx
import pytest

from app.services.llm_gateway_adapter import LLMGatewayAdapter
from app.services.tutor_engine import TutorContext, TutorEngine, TutorProviderError


def _context() -> TutorContext:
    return TutorContext(
        grade_level="9",
        curriculum_name="Ontario Grade 9 Mathematics",
        state="GUIDED_PRACTICE",
        skill_name="Linear relations",
        action="GIVE_HINT",
        hint_level=1,
        problem_prompt="3(x+4)",
    )


def test_gateway_adapter_sends_only_rendering_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, *, json: dict[str, object], timeout: float) -> httpx.Response:
        captured.update(json)
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            request=request,
            json={
                "message": "Look at the two coordinate pairs.",
                "expects_student_response": True,
                "request_id": "req-123",
                "provider": "openai",
                "model": "gpt-test",
                "latency_ms": 12,
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    adapter = LLMGatewayAdapter("http://llm-gateway:8001", 2.0)
    result = adapter.generate(_context())

    assert result["message"] == "Look at the two coordinate pairs."
    assert result["request_id"] == "req-123"
    assert result["provider"] == "openai"
    assert result["model"] == "gpt-test"
    assert result["latency_ms"] == 12
    assert captured["action"] == "GIVE_HINT"
    assert "state" not in captured
    assert "student_answer" not in captured
    assert "promote_mastery" not in captured
    assert "selected_prerequisite_id" not in captured


def test_gateway_failure_preserves_deterministic_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_post(*args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectError("gateway down")

    monkeypatch.setattr(httpx, "post", fail_post)
    engine = TutorEngine(LLMGatewayAdapter("http://llm-gateway:8001", 0.1))

    result = engine.generate(_context())

    assert result.source == "fallback"
    assert result.provider is None
    assert "outside the parentheses" in result.message


def test_gateway_adapter_converts_invalid_payload_to_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid_post(url: str, *, json: dict[str, object], timeout: float) -> httpx.Response:
        request = httpx.Request("POST", url)
        return httpx.Response(200, request=request, content=b"not-json")

    monkeypatch.setattr(httpx, "post", invalid_post)
    adapter = LLMGatewayAdapter("http://llm-gateway:8001", 2.0)

    with pytest.raises(TutorProviderError):
        adapter.generate(_context())


def test_gateway_adapter_rejects_missing_observability_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def incomplete_post(url: str, *, json: dict[str, object], timeout: float) -> httpx.Response:
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            request=request,
            json={"message": "Rendered language", "expects_student_response": True},
        )

    monkeypatch.setattr(httpx, "post", incomplete_post)
    adapter = LLMGatewayAdapter("http://llm-gateway:8001", 2.0)

    with pytest.raises(TutorProviderError):
        adapter.generate(_context())
