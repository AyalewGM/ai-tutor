import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

SOCRATIC_REDIRECT = (
    "I see what you're asking, but I'm here to help you solve it yourself! "
    "What do you think the very first step should be?"
)

class SafetyIntent(StrEnum):
    SAFE = "SAFE"
    DIRECT_ANSWER = "DIRECT_ANSWER"
    HOMEWORK_COMPLETION = "HOMEWORK_COMPLETION"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    OFF_TOPIC = "OFF_TOPIC"

@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    intent: SafetyIntent
    response: Optional[str] = None

_PATTERNS: tuple[tuple[SafetyIntent, re.Pattern[str]], ...] = (
    (SafetyIntent.PROMPT_INJECTION, re.compile(
        r"\b(ignore|forget|override|bypass)\b.{0,40}\b(previous|prior|system|developer|instructions?|rules?|prompt)\b"
        r"|\b(system prompt|developer message|jailbreak|do anything now|DAN)\b",
        re.IGNORECASE | re.DOTALL,
    )),
    (SafetyIntent.HOMEWORK_COMPLETION, re.compile(
        r"\b(do|finish|complete|write|solve)\b.{0,30}\b(my|this|the)\b.{0,20}\b(homework|assignment|worksheet|essay|project)\b"
        r"|\bdo (?:it|this) for me\b",
        re.IGNORECASE | re.DOTALL,
    )),
    (SafetyIntent.DIRECT_ANSWER, re.compile(
        r"\b(give|tell|show) me (?:just |only )?(?:the )?(?:final )?answer\b"
        r"|\bwhat(?:'s| is) (?:just |only )?(?:the )?answer\b"
        r"|\bno (?:steps|explanation),? (?:just|only) (?:the )?answer\b",
        re.IGNORECASE,
    )),
)

# High-confidence non-learning requests only. Ambiguous prompts remain allowed so the
# tutor can redirect them pedagogically rather than over-blocking learners.
_OFF_TOPIC = re.compile(
    r"^\s*(?:write me a song|tell me a celebrity gossip|book me a flight|buy me|"
    r"generate malware|hack (?:a|the)|sports score)\b",
    re.IGNORECASE,
)

def inspect_student_input(prompt: str) -> GuardrailDecision:
    normalized = " ".join(prompt.split())
    if not normalized:
        return GuardrailDecision(True, SafetyIntent.SAFE)
    for intent, pattern in _PATTERNS:
        if pattern.search(normalized):
            return GuardrailDecision(False, intent, SOCRATIC_REDIRECT)
    if _OFF_TOPIC.search(normalized):
        return GuardrailDecision(False, SafetyIntent.OFF_TOPIC, SOCRATIC_REDIRECT)
    return GuardrailDecision(True, SafetyIntent.SAFE)

async def validate_pedagogical_safety(prompt: str) -> tuple[bool, Optional[str]]:
    """Fast, local pre-flight guardrail. No learner text leaves the process."""
    decision = inspect_student_input(prompt)
    return decision.allowed, decision.response
