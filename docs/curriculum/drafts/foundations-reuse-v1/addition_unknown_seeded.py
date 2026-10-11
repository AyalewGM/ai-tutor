"""Draft-only seeded variants for unknown-position addition reasoning.

The module is intentionally outside the runtime registry.  It gives reviewers
replayable guided and independent items without activating a lesson or writing
learner/mastery evidence.
"""

from __future__ import annotations

import random
import re
from collections.abc import Mapping
from dataclasses import dataclass

NAMESPACE = "foundations-addition-unknown-r2"
MODES = frozenset({"guided", "independent"})
STRUCTURES = (
    "JOIN_RESULT_UNKNOWN",
    "JOIN_CHANGE_UNKNOWN",
    "JOIN_START_UNKNOWN",
    "PART_WHOLE_PART_UNKNOWN",
    "COMPARE_LARGER_UNKNOWN",
)


@dataclass(frozen=True)
class AdditionUnknownVariant:
    variant_id: str
    mode: str
    structure: str
    story: str
    unknown_role: str
    answer: int
    known_values: tuple[int, int]
    balanced_equation: str
    check_equation: str

    def public_payload(self) -> dict[str, object]:
        """Return learner-visible fields without an answer, hint, or worked step."""

        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "story": self.story,
            "response_fields": [
                "unknown_role",
                "model_equation",
                "answer",
                "check_equation",
                "explanation",
            ],
        }


def _values(rng: random.Random) -> tuple[int, int, int]:
    result = rng.randint(8, 20)
    start = rng.randint(1, result - 1)
    return start, result - start, result


def generate(seed: int, mode: str) -> AdditionUnknownVariant:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")

    rng = random.Random(f"{NAMESPACE}:{mode}:{seed}")
    structure = STRUCTURES[(seed + (2 if mode == "independent" else 0)) % len(STRUCTURES)]
    start, change, result = _values(rng)

    if structure == "JOIN_RESULT_UNKNOWN":
        story = f"{start} birds are at a feeder. {change} more arrive. How many birds are there now?"
        role = "result"
        answer = result
        known = (start, change)
        equation = f"{start} + {change} = □"
        check = f"{result} - {change} = {start}"
    elif structure == "JOIN_CHANGE_UNKNOWN":
        story = f"{start} shells are in a tray. Some more are added, making {result}. How many were added?"
        role = "change"
        answer = change
        known = (start, result)
        equation = f"{start} + □ = {result}"
        check = f"{result} - {start} = {change}"
    elif structure == "JOIN_START_UNKNOWN":
        story = f"Some counters are hidden. After {change} more are added, there are {result}. How many were hidden?"
        role = "start"
        answer = start
        known = (change, result)
        equation = f"□ + {change} = {result}"
        check = f"{result} - {change} = {start}"
    elif structure == "PART_WHOLE_PART_UNKNOWN":
        story = f"A box has {result} crayons. {start} are blue and the rest are green. How many are green?"
        role = "part"
        answer = change
        known = (start, result)
        equation = f"{start} + □ = {result}"
        check = f"{result} - {start} = {change}"
    else:
        story = f"Mina has {start} beads. Tessa has {change} more than Mina. How many beads does Tessa have?"
        role = "larger quantity"
        answer = result
        known = (start, change)
        equation = f"{start} + {change} = □"
        check = f"{result} - {start} = {change}"

    return AdditionUnknownVariant(
        variant_id=f"{NAMESPACE}:{mode}:{seed}",
        mode=mode,
        structure=structure,
        story=story,
        unknown_role=role,
        answer=answer,
        known_values=known,
        balanced_equation=equation,
        check_equation=check,
    )


def diagnose_numeric_response(
    item: AdditionUnknownVariant,
    response: int,
    claimed_role: str,
) -> str:
    """Classify observable response evidence without awarding mastery."""

    if isinstance(response, bool) or not isinstance(response, int):
        return "INVALID_RESPONSE"
    if claimed_role != item.unknown_role:
        return "UNKNOWN_ROLE_CONFUSION"
    if response == item.answer:
        return "CORRECT_PRACTICE_ONLY"
    if item.unknown_role == "change" and response == item.known_values[1]:
        return "RESULT_AS_CHANGE"
    if response == sum(item.known_values):
        return "ADDED_VISIBLE_VALUES"
    if response in item.known_values:
        return "COPIED_KNOWN_QUANTITY"
    return "RELATION_NOT_ESTABLISHED"


# Draft guided relation-evidence evaluator; never a trusted assessment scorer.
# Reason codes distinguish the *meaning* of the unknown, not just its number.
REASON_CODES = {
    "JOIN_RESULT_UNKNOWN": "JOIN_TOTAL",
    "JOIN_CHANGE_UNKNOWN": "INVERSE_MISSING_CHANGE",
    "JOIN_START_UNKNOWN": "INVERSE_MISSING_START",
    "PART_WHOLE_PART_UNKNOWN": "PART_WHOLE",
    "COMPARE_LARGER_UNKNOWN": "COMPARE_DIFFERENCE",
}
RELATION_FIELDS = frozenset({
    "unknown_role", "model_equation", "answer", "check_equation", "explanation"
})


def diagnose_relation_evidence(
    item: AdditionUnknownVariant, response: Mapping[str, object]
) -> str:
    """Check a complete guided relation, not merely its numeric answer.

    Explanatory prose is captured for independent review but is NOT graded for
    semantic quality by this deterministic author-only checker. Never award
    mastery or persist learner evidence from this function.
    """
    if item.mode != "guided":
        return "INDEPENDENT_ASSESSMENT_NOT_SCORED_HERE"
    if not isinstance(response, Mapping) or set(response) != RELATION_FIELDS:
        return "INCOMPLETE_RELATION_EVIDENCE"
    if response["unknown_role"] != item.unknown_role:
        return "UNKNOWN_ROLE_CONFUSION"
    answer = response["answer"]
    if isinstance(answer, bool) or not isinstance(answer, int):
        return "INVALID_RESPONSE"
    if answer != item.answer:
        return diagnose_numeric_response(item, answer, item.unknown_role)

    model = response["model_equation"]
    expected_model = re.fullmatch(
        r"\s*(□|\d+)\s*\+\s*(□|\d+)\s*=\s*(□|\d+)\s*",
        item.balanced_equation,
    )
    submitted_model = (
        re.fullmatch(r"\s*(□|\d+)\s*\+\s*(□|\d+)\s*=\s*(□|\d+)\s*", model)
        if isinstance(model, str)
        else None
    )
    if (
        expected_model is None
        or submitted_model is None
        or submitted_model.groups() != expected_model.groups()
        or sum(
            int(part) if part != "□" else item.answer
            for part in submitted_model.groups()[:2]
        ) != (
            int(submitted_model.group(3))
            if submitted_model.group(3) != "□"
            else item.answer
        )
    ):
        return "MODEL_EQUATION_INCORRECT"

    check = response["check_equation"]
    expected_check = re.fullmatch(
        r"\s*(\d+)\s*-\s*(\d+)\s*=\s*(\d+)\s*",
        item.check_equation,
    )
    submitted_check = (
        re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*=\s*(\d+)\s*", check)
        if isinstance(check, str)
        else None
    )
    if (
        expected_check is None
        or submitted_check is None
        or submitted_check.groups() != expected_check.groups()
        or int(submitted_check.group(1)) - int(submitted_check.group(2))
        != int(submitted_check.group(3))
    ):
        return "INVERSE_CHECK_INCORRECT"

    explanation = response["explanation"]
    if not isinstance(explanation, Mapping):
        return "EXPLANATION_EVIDENCE_INCOMPLETE"
    if set(explanation) != {"reason_code", "reasoning"}:
        return "EXPLANATION_EVIDENCE_INCOMPLETE"
    reasoning = explanation["reasoning"]
    if (
        explanation["reason_code"] != REASON_CODES[item.structure]
        or not isinstance(reasoning, str)
        or len(reasoning.strip()) < 15
        or reasoning.strip() in {item.story, item.balanced_equation, item.check_equation}
    ):
        return "EXPLANATION_EVIDENCE_INCOMPLETE"

    return "CORRECT_STRUCTURED_PRACTICE_ONLY_EXPLANATION_UNVERIFIED"
