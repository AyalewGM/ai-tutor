import json
from dataclasses import asdict
from typing import Any

from app.core.settings import settings
from app.services.tutor_engine import TutorContext, TutorGeneration, TutorProvider


def build_prompt(context: TutorContext) -> str:
    payload = json.dumps(asdict(context), ensure_ascii=False)
    return (
        "You are the language layer of an adaptive math tutor. "
        "Follow the pedagogical action already selected by the application. "
        "Do not change tutoring state or independently declare mastery. "
        "Keep the response concise and age-appropriate.\n\n"
        f"Tutor context:\n{payload}"
    )


class OpenAIAdapter:
    provider_name = "openai"

    def __init__(self, model_name: str, client: Any) -> None:
        self.model_name = model_name
        self.client = client

    def generate(self, context: TutorContext) -> dict[str, object]:
        response = self.client.responses.create(
            model=self.model_name,
            input=build_prompt(context),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "tutor_generation",
                    "strict": True,
                    "schema": TutorGeneration.model_json_schema(),
                }
            },
        )
        if not response.output_text:
            raise ValueError("OpenAI response contained no tutor output")
        return json.loads(response.output_text)


class GeminiAdapter:
    provider_name = "gemini"

    def __init__(self, model_name: str, client: Any, config_factory: Any) -> None:
        self.model_name = model_name
        self.client = client
        self.config_factory = config_factory

    def generate(self, context: TutorContext) -> dict[str, object]:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=build_prompt(context),
            config=self.config_factory(
                response_mime_type="application/json",
                response_schema=TutorGeneration,
            ),
        )
        if not response.text:
            raise ValueError("Gemini response contained no tutor output")
        return json.loads(response.text)


def build_adapter() -> TutorProvider | None:
    provider = settings.ai_provider.strip().lower()
    if provider in {"", "fallback", "none"}:
        return None
    raise RuntimeError("Configured provider requires client bootstrap")
