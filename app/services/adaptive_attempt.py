import uuid
from dataclasses import dataclass

from app.models import Misconception, Problem, StudentSkill, TutorSession
from app.services.evaluation import EvaluationResult
from app.services.state_machine import Transition


@dataclass(frozen=True)
class AdaptiveAttemptOutcome:
    session: TutorSession
    problem: Problem
    next_problem: Problem | None
    progress: StudentSkill
    evaluation: EvaluationResult
    transition: Transition
    misconception: Misconception | None
    active_skill_id: uuid.UUID
