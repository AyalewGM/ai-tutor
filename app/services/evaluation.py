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


def evaluate_distributive_property(prompt: str, answer: str, canonical_answer: str) -> EvaluationResult:
    normalized = _normalize(answer)
    canonical = _normalize(canonical_answer)

    if normalized == canonical:
        return EvaluationResult(True, 0.99, normalized)

    # Sprint 1 rule: detect the characteristic error 3(x+4) -> 3x+4.
    match = re.fullmatch(r"(-?\d+)\(x([+-]\d+)\)", _normalize(prompt))
    if match:
        multiplier = int(match.group(1))
        constant = int(match.group(2))
        undisbtributed_constant = f"{multiplier}x{constant:+d}"
        if normalized in {undisbtributed_constant, undisbtributed_constant.replace("+", "+")}:
            return EvaluationResult(
                False,
                0.99,
                normalized,
                misconception_code="DIST_001",
                misconception_confidence=0.97,
            )

    return EvaluationResult(False, 0.90, normalized)
