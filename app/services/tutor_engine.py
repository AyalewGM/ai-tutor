from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.services.hint_policy import hint_constraint


class TutorProviderError(RuntimeError):
    pass


class TutorGeneration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=1200)
    expects_student_response: bool = True
    request_id: str | None = None
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)


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
    remediation_strategy: str | None = None
    next_problem_prompt: str | None = None
    hint_constraint: str | None = None


@dataclass(frozen=True)
class TutorEngineResult:
    message: str
    source: str
    model: str | None = None
    provider: str | None = None
    latency_ms: int | None = None
    request_id: str | None = None
    expects_student_response: bool = True


class TutorProvider(Protocol):
    model_name: str
    provider_name: str

    def generate(self, context: TutorContext) -> dict[str, object]:
        raise NotImplementedError


class TutorEngine:
    def __init__(self, provider: TutorProvider | None = None) -> None:
        self.provider = provider

    def generate(
        self, context: TutorContext, *, use_llm: bool = True
    ) -> TutorEngineResult:
        if context.action == "GIVE_HINT" and context.hint_level is not None:
            context = TutorContext(
                **{
                    **context.__dict__,
                    "hint_constraint": hint_constraint(context.hint_level),
                }
            )
        if self.provider is not None and use_llm:
            started = perf_counter()
            try:
                generation = TutorGeneration.model_validate(self.provider.generate(context))
                elapsed_ms = int((perf_counter() - started) * 1000)
                return TutorEngineResult(
                    message=generation.message,
                    source="llm",
                    model=generation.model or self.provider.model_name,
                    provider=generation.provider or self.provider.provider_name,
                    latency_ms=(
                        generation.latency_ms
                        if generation.latency_ms is not None
                        else elapsed_ms
                    ),
                    request_id=generation.request_id,
                    expects_student_response=generation.expects_student_response,
                )
            except (TutorProviderError, RuntimeError, ValueError, TimeoutError):
                pass

        return TutorEngineResult(
            message=fallback_message(context),
            source="fallback",
            expects_student_response=True,
        )


_DISTRIBUTION_LADDER = (
    "Look at the number immediately outside the parentheses. What must it multiply?",
    "The multiplier must multiply every term inside the parentheses. Which term have you not multiplied yet?",
    "Write the multiplication separately for each term inside the parentheses, then simplify.",
    "Let us model the distribution step explicitly, then you can finish the problem.",
)
_EQUATION_LADDER = (
    "What is being done to the variable? Think about which operation would undo it.",
    "Whatever you do to one side of the equation, you must do to the other side. Which operation undoes what is next to the variable?",
    "Undo the operations around the variable one at a time: first undo any addition or subtraction, then undo multiplication or division.",
    "Let us isolate the variable step by step together, then you can finish the problem.",
)
_LIKE_TERMS_LADDER = (
    "This expression has more than one term. Which terms have the same variable part?",
    "Combine the x terms together and the plain numbers together. They are separate groups.",
    "Add the coefficients of x to get one x term, and add the constants to get one number.",
    "Let us group the like terms together, then you can finish simplifying.",
)
_FRACTION_LADDER = (
    "Fractions can only be added when their denominators match. Are these denominators the same?",
    "You cannot add the numerators across different denominators. What denominator do both fractions share?",
    "Rewrite each fraction with a common denominator first, then add the new numerators.",
    "Let us find a common denominator together, then you can finish the addition.",
)
_LINEAR_FUNCTION_LADDER = (
    "In slope-intercept form y = mx + b, which number is the slope and which is the intercept?",
    "The slope multiplies x; the intercept is the number added on its own. Match each given value to m or b.",
    "Substitute the slope for m and the intercept for b in y = mx + b — or substitute x in if you are evaluating.",
    "Let us identify m and b together, then you can finish the problem.",
)
_GENERIC_LADDER = (
    "Break the problem into one small step. What is the very first thing you can do?",
    "Look carefully at each number in the problem. What operation connects them?",
    "Try writing the first step on scratch paper, even if you are not sure it is right.",
    "Let us work through the first step together, then you can finish the problem.",
)


def _hint_ladder(problem_prompt: str) -> tuple[str, ...]:
    normalized = problem_prompt.lower()
    if "slope" in normalized or "y-intercept" in normalized or "y =" in normalized:
        return _LINEAR_FUNCTION_LADDER
    if "=" in normalized and "x" in normalized:
        return _EQUATION_LADDER
    if "/" in normalized:
        return _FRACTION_LADDER
    if "(" in normalized and ")" in normalized:
        return _DISTRIBUTION_LADDER
    if normalized.count("x") > 1:
        return _LIKE_TERMS_LADDER
    return _GENERIC_LADDER


def _concept_explanation(problem_prompt: str) -> str:
    ladder = _hint_ladder(problem_prompt)
    if ladder is _DISTRIBUTION_LADDER:
        return "A number outside parentheses multiplies every term inside. Let us work through that idea before trying again."
    if ladder is _EQUATION_LADDER:
        return "An equation stays balanced only if you do the same thing to both sides. Let us work through that idea before trying again."
    if ladder is _FRACTION_LADDER:
        return "Fractions need a common denominator before you can add them. Let us work through that idea before trying again."
    if ladder is _LINEAR_FUNCTION_LADDER:
        return "In y = mx + b, m is the slope and b is the y-intercept. Let us work through that idea before trying again."
    if ladder is _LIKE_TERMS_LADDER:
        return "Terms can only be combined when they have the same variable part. Let us work through that idea before trying again."
    return "Let us slow down and look at what the problem is asking, one step at a time."


def fallback_message(context: TutorContext) -> str:
    if context.action == "ASK_DIAGNOSTIC":
        return "Let us start with a quick problem so I can see what you already know."
    if context.action == "EXPLAIN_CONCEPT":
        return _concept_explanation(context.problem_prompt)
    if context.action == "GIVE_HINT":
        ladder = _hint_ladder(context.problem_prompt)
        level = context.hint_level or 1
        return ladder[min(level, len(ladder)) - 1]
    if context.action == "REMEDIATE":
        return (
            "This same pattern has appeared more than once. "
            f"Let us return to {context.skill_name} before continuing."
        )
    if context.action == "START_REVIEW":
        return "Before we learn something new, let us check whether an earlier skill is still strong. Try this problem on your own."
    if context.action == "RESUME_TARGET":
        return "That review is solid. Let us return to what we were learning."
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
