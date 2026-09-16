from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="AI Tutor LLM Gateway", version="0.1.0")


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/v1/render", response_model=RenderResponse)
def render_language(request: RenderRequest) -> RenderResponse:
    """Render constrained language without acquiring pedagogical authority.

    Provider integration follows in the next slice. This deterministic renderer
    establishes and tests the service boundary first, keeping Tutor API behavior
    safe while the extracted path remains reversible.
    """

    if request.action == "GIVE_HINT" and request.hint_constraint:
        message = f"Use this hint constraint: {request.hint_constraint}"
    elif request.next_problem_prompt:
        message = f"Try this next problem on your own: {request.next_problem_prompt}"
    else:
        message = f"Continue with this problem: {request.problem_prompt}"
    return RenderResponse(message=message)
