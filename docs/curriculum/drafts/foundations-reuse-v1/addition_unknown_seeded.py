"""Draft-only seeded variants for unknown-position addition reasoning.

The module is intentionally outside the runtime registry.  It gives reviewers
replayable guided and independent items without activating a lesson or writing
learner/mastery evidence.
"""

from __future__ import annotations

import random
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
