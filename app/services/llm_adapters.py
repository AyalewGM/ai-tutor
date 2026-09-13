import json
from dataclasses import asdict
from typing import Any

from google import genai
from google.genai import types
from openai import OpenAI

from app.core.settings import settings
from app.services.tutor_engine import TutorContext, TutorGeneration, TutorProvider


def build_prompt(context: TutorContext) -> str:
    payload = json.dumps(asdict(context), ensure_ascii=False)
    return (
        "You are the language layer of an adaptive math tutor. "
        "Follow the pedagogical action already selected by the application. "
        "Keep the response concise and age-appropriate.\n\n"
        f"Tutor context:\n{payload}"
    )


class OpenAIAdapter:
    provider_name = "openai"

    def __init__(self, model_name: str, client: Any | None = None) -> None:
        self.model_name = model_name
        self._client = client


class GeminiAdapter:
    provider_name = "gemini"

    def __init__(self, model_name: str, client: Any | None = None) -> None:
        self.model_name = model_name
        self._client = client


def build_adapter() -> TutorProvider | None:
    provider = settings.ai_provider.strip().lower()
    if provider in {"", "fallback", "none"}:
        return None
    if provider == "openai":
        return OpenAIAdapter(settings.openai_model)  # type: ignore[return-value]
    if provider == "gemini":
        return GeminiAdapter(settings.gemini_model)  # type: ignore[return-value]
    raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")
