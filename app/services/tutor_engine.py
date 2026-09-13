from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class TutorGeneration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=1200)
    expects_student_response: bool = True


@dataclass(frozen=True)
class TutorContext:
    grade_level: str
    curriculum_name: str
    state: str
    skill_name: str
    action: str
    hint_level: int | None
    problem_prompt: str
    student_answer: str | None = None
    misconception_description: str | None = None
    next_problem_prompt: str | None = None


@dataclass(frozen=True)
class TutorEngineResult:
    message: str
    source: str
    model: str | None = None
    provider: str | None = None
    latency_ms: int | None = None
    expects_student_response: bool = True


class TutorProvider(Protocol):
    model_name: str
    provider_name: str

    def generate(self, context: TutorContext) -> dict[str, object]:
        raise NotImplementedError


class TutorEngine:
    def __init__(self, provider: TutorProvider | None = None) -> None:
        self.provider = provider

    def generate(self, context: TutorContext) -> TutorEngineResult:
        if self.provider is not None:
            started = perf_counter()
            try:
                generation = TutorGeneration.model_validate(self.provider.generate(context))
                return TutorEngineResult(
                    message=generation.message,
                    source="llm",
                    model=self.provider.model_name,
                    provider=self.provider.provider_name,
                    latency_ms=int((perf_counter() - started) * 1000),
                    expects_student_response=generation.expects_student_response,
                )
            except Exception:
                pass

        return TutorEngineResult(
            message=fallback_message(context),
            source="fallback",
            expects_student_response=True,
        )


def fallback_message(context: TutorContext) -> str:
    if context.action == "ASK_DIAGNOSTIC":
        return "Let us start with a quick problem so I can see what you already know."
    if context.action == "EXPLAIN_CONCEPT":
        return "A number outside parentheses multiplies every term inside. Let us work through that idea before trying again."
    if context.action == "GIVE_HINT":
        if context.hint_level == 1:
            return "Look at the number immediately outside the parentheses. What must it multiply?"
        if context.hint_level == 2:
            return "The multiplier must multiply every term inside the parentheses. Which term have you not multiplied yet?"
        if context.hint_level == 3:
            return "Write the multiplication separately for each term inside the parentheses, then simplify."
        return "Let us model the distribution step explicitly, then you can finish the problem."
    if context.action == "REMEDIATE":
        return "This same pattern has appeared more than once. Let us return to the distributive property before continuing."
    if context.action == "START_MASTERY_CHECK":
        return "Now solve the next problem independently without hints so we can check mastery."
    if context.action == "MARK_MASTERED":
        return "Good work. This independent attempt supports mastery of the skill."
    if context.action == "INCREASE_DIFFICULTY":
        return "You are solving these independently, so let us increase the difficulty."
    if context.next_problem_prompt:
        return f"Try this next problem on your own: {context.next_problem_prompt}"
    return f"Try the next step on your own: {context.problem_prompt}"


tutor_engine = TutorEngine()
