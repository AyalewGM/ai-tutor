import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationResult:
    correct: bool
    confidence: float
    normalized_answer: str
    misconception_code: str | None = None
    misconception_confidence: float | None = None


def _normalize(expression: str) -> str:
    return re.sub(r"\s+", "", expression.lower())


def _partial_distribution_error(prompt: str, normalized_answer: str) -> bool:
    normalized_prompt = _normalize(prompt)
    match = re.search(r"(-?\d+)\(x([+-]\d+)\)", normalized_prompt)
    if not match:
        return False

    multiplier = int(match.group(1))
    constant = int(match.group(2))
    correct_fragment = f"{multiplier}x{multiplier * constant:+d}"
    incorrect_fragment = f"{multiplier}x{constant:+d}"

    if incorrect_fragment not in normalized_answer:
        return False
    return correct_fragment not in normalized_answer


def evaluate_problem(prompt: str, answer: str, canonical_answer: str) -> EvaluationResult:
    normalized = _normalize(answer)
    canonical = _normalize(canonical_answer)

    if normalized == canonical:
        return EvaluationResult(True, 0.99, normalized)

    if _partial_distribution_error(prompt, normalized):
        return EvaluationResult(
            False,
            0.99,
            normalized,
            misconception_code="DIST_001",
            misconception_confidence=0.97,
        )

    return EvaluationResult(False, 0.90, normalized)


def evaluate_distributive_property(
    prompt: str,
    answer: str,
    canonical_answer: str,
) -> EvaluationResult:
    return evaluate_problem(prompt, answer, canonical_answer)
