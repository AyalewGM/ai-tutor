from google import genai
from google.genai import types
from openai import OpenAI

from app.core.settings import settings
from app.services import problem_contextualizer
from app.services.llm_adapters import GeminiAdapter, OpenAIAdapter
from app.services.llm_gateway_adapter import LLMGatewayAdapter
from app.services.problem_contextualizer import GatewayContextualizer
from app.services.tutor_engine import tutor_engine


def configure_tutor_engine() -> None:
    provider = settings.ai_provider.strip().lower()

    if provider in {"", "fallback", "none"}:
        tutor_engine.provider = None
        problem_contextualizer.contextualizer = None
        return

    if provider == "gateway":
        tutor_engine.provider = LLMGatewayAdapter(
            settings.llm_gateway_url,
            settings.ai_timeout_seconds,
        )
        problem_contextualizer.contextualizer = GatewayContextualizer(
            settings.llm_gateway_url,
            settings.ai_timeout_seconds,
        )
        return

    if provider == "openai":
        tutor_engine.provider = OpenAIAdapter(
            settings.openai_model,
            OpenAI(timeout=settings.ai_timeout_seconds),
        )
        return

    if provider == "gemini":
        tutor_engine.provider = GeminiAdapter(
            settings.gemini_model,
            genai.Client(),
            types.GenerateContentConfig,
        )
        return

    raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")
