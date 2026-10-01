"""Deterministic assessment helpers for the existing adaptive tutor.

AI Tutor already owns assessment through Problem, Attempt, StudentSkill and the
mastery gate. This module deliberately does not let an LLM author answer keys
or directly mark mastery. It provides typed quiz-shaped projections for UI/API
work while preserving the authoritative evidence pipeline.
"""
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.services.evaluation import evaluate_problem


class QuizQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quiz_id: str
    question: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)
    correct_index: int | None = Field(default=None, ge=0)
    explanation: str = ""


class QuizSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quiz_id: str
    selected_index: int | None = Field(default=None, ge=0)
    answer: str | None = None


def verify_selected_index(*, selected_index: int, correct_index: int, option_count: int) -> bool:
    """Pure deterministic multiple-choice verification."""
    if option_count < 2:
        raise ValueError("quiz must contain at least two options")
    if not 0 <= correct_index < option_count:
        raise ValueError("correct_index is outside the option range")
    if not 0 <= selected_index < option_count:
        return False
    return selected_index == correct_index


def verify_free_response(*, answer: str, canonical_answer: str):
    """Delegate to the same deterministic evaluator used by tutor attempts."""
    return evaluate_problem("", answer, canonical_answer)


def quiz_id_for_problem(problem_id: uuid.UUID) -> str:
    return f"problem:{problem_id}"
