"""Shared problem-family spec types.

Leaf module — imports nothing from ``app.domains`` or
``app.canonical_problem_families`` so domain modules can import these types
without a circular dependency on the family registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.answer_contracts import AnswerContract


class LearningMode(StrEnum):
    DIAGNOSTIC = "DIAGNOSTIC"
    GUIDED = "GUIDED"
    INDEPENDENT = "INDEPENDENT"
    MASTERY = "MASTERY"
    REVIEW = "REVIEW"
    # Optional stretch tier above the mastery band. Extension problems are
    # served only on explicit opt-in, never gate mastery, and never count as
    # learner evidence.
    EXTENSION = "EXTENSION"


@dataclass(frozen=True)
class ProblemFamilySpec:
    code: str
    name: str
    canonical_skill_code: str
    problem_type: str
    min_difficulty: int
    max_difficulty: int
    modes: frozenset[LearningMode]
    evidence_dimensions: frozenset[str]
    answer_contract: AnswerContract | None = None


ALL_MODES = frozenset(LearningMode)
