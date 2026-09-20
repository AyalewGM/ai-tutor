import re
from typing import Any, Protocol

import httpx

_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


class Contextualizer(Protocol):
    def contextualize(
        self,
        *,
        template: str,
        parameters: dict[str, Any],
        canonical_answer: str,
    ) -> str | None:
        """Return a narrative word-problem prompt, or None when unavailable."""
        raise NotImplementedError


class GatewayContextualizer:
    """LLM narrative provider backed by the internal gateway.

    The model writes only the story skin. Every numeric parameter must appear
    verbatim in the returned prompt or the narrative is rejected.
    """

    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def contextualize(
        self,
        *,
        template: str,
        parameters: dict[str, Any],
        canonical_answer: str,
    ) -> str | None:
        try:
            response = httpx.post(
                f"{self.base_url}/v1/contextualize",
                json={
                    "template": template,
                    "parameters": parameters,
                    "canonical_answer": canonical_answer,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError):
            return None
        prompt = data.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            return None
        prompt = prompt.strip()
        required = {
            token
            for value in parameters.values()
            for token in _NUMBER.findall(str(value))
        }
        present = set(_NUMBER.findall(prompt))
        if not required.issubset(present):
            return None
        return prompt


contextualizer: Contextualizer | None = None
