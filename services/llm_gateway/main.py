import json
import os
import time
import uuid
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="AI Tutor LLM Gateway", version="0.3.0")


class RenderRequest(BaseModel):
    """Application-computed language-rendering request.

    The gateway deliberately receives no mastery mutation, prerequisite routing,
    curriculum selection, or assessment-control fields. Those remain Tutor API
    responsibilities.
    """

    model_config = ConfigDict(extra="forbid")

    action: str = Field(min_length=1, max_length=80)
    curriculum_name: str = Field(min_length=1, max_length=200)
    grade_level: str = Field(min_length=1, max_length=80)
    skill_name: str = Field(min_length=1, max_length=200)
    problem_prompt: str = Field(min_length=1, max_length=4000)
    hint_level: int | None = Field(default=None, ge=1, le=4)
    hint_constraint: str | None = Field(default=None, max_length=1000)
    misconception_description: str | None = Field(default=None, max_length=2000)
    remediation_strategy: str | None = Field(default=None, max_length=2000)
    next_problem_prompt: str | None = Field(default=None, max_length=4000)


class ContextualizeRequest(BaseModel):
    """Narrative-writing request for a generated math problem.

    The gateway only writes the story skin: parameters and the canonical
    answer are application-computed and must appear verbatim in the output.
    """

    model_config = ConfigDict(extra="forbid")

    template: str = Field(min_length=1, max_length=80)
    parameters: dict[str, Any]
    canonical_answer: str = Field(min_length=1, max_length=200)
    grade_level: str | None = Field(default=None, max_length=80)


class ContextualizeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(default="", max_length=800)
    request_id: str
    provider: str
    model: str | None = None
    latency_ms: int = Field(ge=0)


class RenderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=1200)
    expects_student_response: bool = True
    request_id: str
    provider: str
    model: str | None = None
    latency_ms: int = Field(ge=0)


def _provider() -> str:
    return os.getenv("LLM_GATEWAY_PROVIDER", "fallback").strip().lower()


def _model_name(provider: str) -> str | None:
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return None


def _prompt(request: RenderRequest) -> str:
    payload = json.dumps(request.model_dump(), ensure_ascii=False)
    return (
        "You are only the language-rendering layer of an adaptive math tutor. "
        "The application has already selected the pedagogical action. Follow it exactly. "
        "Do not change curriculum, prerequisite routing, hint level, assessment state, "
        "intervention state, or mastery. Do not declare mastery. Keep language concise, "
        "age-appropriate, and bounded by the supplied context. Return only the requested "
        "JSON response.\n\n"
        f"Application-computed context:\n{payload}"
    )


def _fallback(request: RenderRequest) -> dict[str, object]:
    if request.action == "GIVE_HINT" and request.hint_constraint:
        message = f"Use this hint constraint: {request.hint_constraint}"
    elif request.next_problem_prompt:
        message = f"Try this next problem on your own: {request.next_problem_prompt}"
    else:
        message = f"Continue with this problem: {request.problem_prompt}"
    return {"message": message, "expects_student_response": True}


def _openai_render(request: RenderRequest) -> dict[str, object]:
    from openai import OpenAI

    model = _model_name("openai")
    response = OpenAI().responses.create(
        model=model,
        input=_prompt(request),
        text={
            "format": {
                "type": "json_schema",
                "name": "tutor_generation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "maxLength": 1200},
                        "expects_student_response": {"type": "boolean"},
                    },
                    "required": ["message", "expects_student_response"],
                    "additionalProperties": False,
                },
            }
        },
    )
    if not response.output_text:
        raise RuntimeError("OpenAI returned no language output")
    data = json.loads(response.output_text)
    if not isinstance(data, dict):
        raise TypeError("OpenAI returned invalid language output")
    return data


_gemini_client = None


def _gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai

        _gemini_client = genai.Client()
    return _gemini_client


def _gemini_render(request: RenderRequest) -> dict[str, object]:
    from google.genai import types

    model = _model_name("gemini")
    response = _gemini().models.generate_content(
        model=model,
        contents=_prompt(request),
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    if not response.text:
        raise RuntimeError("Gemini returned no language output")
    data = json.loads(response.text)
    if not isinstance(data, dict):
        raise TypeError("Gemini returned invalid language output")
    return data


def _render_with_provider(request: RenderRequest, provider: str) -> dict[str, object]:
    renderers: dict[str, Any] = {
        "fallback": _fallback,
        "none": _fallback,
        "openai": _openai_render,
        "gemini": _gemini_render,
    }
    renderer = renderers.get(provider)
    if renderer is None:
        raise RuntimeError(f"Unsupported LLM gateway provider: {provider}")
    return renderer(request)


def _contextualize_prompt(request: ContextualizeRequest) -> str:
    payload = json.dumps(request.model_dump(), ensure_ascii=False)
    return (
        "You write short, age-appropriate math word problems. The application "
        "has already computed every number and the answer. Use EVERY numeric "
        "value in parameters verbatim — never change, add, compute, or drop a "
        "number. Do not state or hint at the answer. Do not ask multiple "
        "questions. Return JSON only: {\"prompt\": \"<one or two sentences "
        "ending in a single question>\"}.\n\n"
        f"Application-computed context:\n{payload}"
    )


def _contextualize_fallback(request: ContextualizeRequest) -> dict[str, object]:
    return {"prompt": ""}


def _contextualize_with_provider(
    request: ContextualizeRequest, provider: str
) -> dict[str, object]:
    if provider in {"fallback", "none"}:
        return _contextualize_fallback(request)
    if provider == "openai":
        from openai import OpenAI

        response = OpenAI().responses.create(
            model=_model_name("openai"),
            input=_contextualize_prompt(request),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "contextualized_problem",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {"prompt": {"type": "string", "maxLength": 800}},
                        "required": ["prompt"],
                        "additionalProperties": False,
                    },
                }
            },
        )
        if not response.output_text:
            raise RuntimeError("OpenAI returned no contextualization output")
        return json.loads(response.output_text)
    if provider == "gemini":
        from google.genai import types

        response = _gemini().models.generate_content(
            model=_model_name("gemini"),
            contents=_contextualize_prompt(request),
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        if not response.text:
            raise RuntimeError("Gemini returned no contextualization output")
        return json.loads(response.text)
    raise RuntimeError(f"Unsupported LLM gateway provider: {provider}")


@app.post("/v1/contextualize", response_model=ContextualizeResponse)
def contextualize_problem(request: ContextualizeRequest) -> ContextualizeResponse:
    """Render a word-problem narrative; numbers and answers stay app-computed."""
    request_id = str(uuid.uuid4())
    provider = _provider()
    started = time.perf_counter()
    generation = _contextualize_with_provider(request, provider)
    latency_ms = max(0, int((time.perf_counter() - started) * 1000))
    return ContextualizeResponse(
        prompt=str(generation["prompt"]),
        request_id=request_id,
        provider=provider,
        model=_model_name(provider),
        latency_ms=latency_ms,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "provider": _provider()}


@app.post("/v1/render", response_model=RenderResponse)
def render_language(request: RenderRequest) -> RenderResponse:
    """Render constrained language and return metadata safe for observational telemetry."""
    request_id = str(uuid.uuid4())
    provider = _provider()
    started = time.perf_counter()
    generation = _render_with_provider(request, provider)
    latency_ms = max(0, int((time.perf_counter() - started) * 1000))
    return RenderResponse(
        message=str(generation["message"]),
        expects_student_response=bool(generation.get("expects_student_response", True)),
        request_id=request_id,
        provider=provider,
        model=_model_name(provider),
        latency_ms=latency_ms,
    )
