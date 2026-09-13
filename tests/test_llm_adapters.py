from types import SimpleNamespace

from app.services.llm_adapters import GeminiAdapter, OpenAIAdapter
from app.services.tutor_engine import TutorContext


def context() -> TutorContext:
    return TutorContext(
        grade_level="8",
        curriculum_name="MCPS Grade 8 Mathematics",
        state="GUIDED_PRACTICE",
        skill_name="Distributive Property",
        action="GIVE_HINT",
        hint_level=2,
        problem_prompt="3(x+4)",
        student_answer="3x+4",
        misconception_description="Partial distribution",
    )


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            output_text='{"message":"Multiply 3 by every term inside the parentheses.","expects_student_response":true}'
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class FakeModels:
    def __init__(self) -> None:
        self.kwargs = None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            text='{"message":"Which term still needs to be multiplied by 3?","expects_student_response":true}'
        )


class FakeGeminiClient:
    def __init__(self) -> None:
        self.models = FakeModels()


def test_openai_adapter_requests_structured_output() -> None:
    client = FakeOpenAIClient()
    adapter = OpenAIAdapter("test-openai", client)

    result = adapter.generate(context())

    assert result["expects_student_response"] is True
    assert "every term" in str(result["message"])
    assert client.responses.kwargs["model"] == "test-openai"
    assert client.responses.kwargs["text"]["format"]["type"] == "json_schema"


def test_gemini_adapter_requests_json_output() -> None:
    client = FakeGeminiClient()

    def config_factory(**kwargs):
        return kwargs

    adapter = GeminiAdapter("test-gemini", client, config_factory)
    result = adapter.generate(context())

    assert result["expects_student_response"] is True
    assert "multiplied" in str(result["message"])
    assert client.models.kwargs["model"] == "test-gemini"
    assert client.models.kwargs["config"]["response_mime_type"] == "application/json"
