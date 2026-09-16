import json
import os
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="AI Tutor LLM Gateway", version="0.2.0")


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
    next_problem_prompt: str | None = Field(default=None, max_length=4000)


class RenderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=1200)
    expects_student_response: bool = True


def _provider() -> str:
    return os.getenv("LLM_GATEWAY_PROVIDER", "fallback").strip().lower()


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


def _fallback(request: RenderRequest) -> RenderResponse:
    if request.action == "GIVE_HINT" and request.hint_constraint:
        message = f"Use this hint constraint: {request.hint_constraint}"
    elif request.next_problem_prompt:
        message = f"Try this next problem on your own: {request.next_problem_prompt}"
    else:
        message = f"Continue with this problem: {request.problem_prompt}"
    return RenderResponse(message=message)


def _openai_render(request: RenderRequest) -> RenderResponse:
    from openai import OpenAI

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    response = OpenAI().responses.create(
        model=model,
        input=_prompt(request),
        text={
            "format": {
                "type": "json_schema",
                "name": "tutor_generation",
                "strict": True,
                "schema": RenderResponse.model_json_schema(),
            }
        },
    )
    if not response.output_text:
        raise RuntimeError("OpenAI returned no language output")
    return RenderResponse.model_validate_json(response.output_text)


def _gemini_render(request: RenderRequest) -> RenderResponse:
    from google import genai
    from google.genai import types

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = genai.Client().models.generate_content(
        model=model,
        contents=_prompt(request),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RenderResponse,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned no language output")
    return RenderResponse.model_validate_json(response.text)


def _render_with_provider(request: RenderRequest) -> RenderResponse:
    renderers: dict[str, Any] = {
        "fallback": _fallback,
        "none": _fallback,
        "openai": _openai_render,
        "gemini": _gemini_render,
    }
    provider = _provider()
    renderer = renderers.get(provider)
    if renderer is None:
        raise RuntimeError(f"Unsupported LLM gateway provider: {provider}")
    return renderer(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "provider": _provider()}


@app.post("/v1/render", response_model=RenderResponse)
def render_language(request: RenderRequest) -> RenderResponse:
    """Render constrained language without acquiring pedagogical authority."""

    return _render_with_provider(request)
