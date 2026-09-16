import httpx

from app.services.tutor_engine import TutorContext, TutorProviderError


class LLMGatewayAdapter:
    """Stateless constrained-language provider backed by the internal gateway."""

    provider_name = "llm-gateway"
    model_name = "gateway"

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def generate(self, context: TutorContext) -> dict[str, object]:
        payload = {
            "action": context.action,
            "curriculum_name": context.curriculum_name,
            "grade_level": context.grade_level,
            "skill_name": context.skill_name,
            "problem_prompt": context.problem_prompt,
            "hint_level": context.hint_level,
            "hint_constraint": context.hint_constraint,
            "misconception_description": context.misconception_description,
            "next_problem_prompt": context.next_problem_prompt,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/v1/render",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TutorProviderError("LLM Gateway unavailable or invalid") from exc
        if not isinstance(data, dict):
            raise TutorProviderError("LLM Gateway returned invalid payload")
        required_metadata = {"request_id", "provider", "latency_ms"}
        if not required_metadata.issubset(data):
            raise TutorProviderError("LLM Gateway omitted required observability metadata")
        return data
