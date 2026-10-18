"""Deterministic Grade 4 question-depth contract.

This draft wrapper reuses existing canonical fraction, decimal, and whole-number
word-problem generators.  It is deliberately not imported by application code,
seeded, routed, or authorized for mastery.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

from app.domains import addition, division, fraction_decimal_depth, multiplication, subtraction

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
MASTERY_WRITES = False
NAMESPACE = "grade4-gap-closure-wave1:question-depth-r2"
MODES = ("diagnostic", "guided", "independent", "mastery")

CONCEPT_FAMILIES: dict[str, tuple[str, ...]] = {
    "G4-FRACTIONS": (
        "MATH.FRAC.UNIT.MEANING",
        "MATH.FRAC.NUMBER_LINE",
        "MATH.FRAC.COMPARE.SAME_NUMERATOR",
        "MATH.FRAC.ERROR.BIGGER_DENOM",
    ),
    "G4-DECIMAL-FRACTIONS": (
        "MATH.DEC.FRACTION.TENTHS",
        "MATH.DEC.FRACTION.HUNDREDTHS",
        "MATH.DEC.ORDER",
        "MATH.DEC.ERROR.ALIGN",
    ),
    "G4-MULTISTEP-WORD": (
        "MATH.ADD.WORD.MULTISTEP",
        "MATH.SUB.WORD.MULTISTEP",
        "MATH.MUL.WORD.MULTISTEP",
        "MATH.DIV.WORD.MULTISTEP",
    ),
}

_BUILDERS = {
    "MATH.FRAC.UNIT.MEANING": fraction_decimal_depth.build,
    "MATH.FRAC.NUMBER_LINE": fraction_decimal_depth.build,
    "MATH.FRAC.COMPARE.SAME_NUMERATOR": fraction_decimal_depth.build,
    "MATH.FRAC.ERROR.BIGGER_DENOM": fraction_decimal_depth.build,
    "MATH.DEC.FRACTION.TENTHS": fraction_decimal_depth.build,
    "MATH.DEC.FRACTION.HUNDREDTHS": fraction_decimal_depth.build,
    "MATH.DEC.ORDER": fraction_decimal_depth.build,
    "MATH.DEC.ERROR.ALIGN": fraction_decimal_depth.build,
    "MATH.ADD.WORD.MULTISTEP": addition.build,
    "MATH.SUB.WORD.MULTISTEP": subtraction.build,
    "MATH.MUL.WORD.MULTISTEP": multiplication.build,
    "MATH.DIV.WORD.MULTISTEP": division.build,
}

_RESPONSE_FIELDS = {
    "G4-FRACTIONS": (
        "model_or_number_line",
        "comparison_or_equation",
        "answer",
        "same_whole_explanation",
    ),
    "G4-DECIMAL-FRACTIONS": (
        "place_value_model",
        "decimal_or_order",
        "answer",
        "place_value_explanation",
    ),
    "G4-MULTISTEP-WORD": (
        "quantity_map",
        "operation_sequence",
        "intermediate_quantity_with_unit",
        "answer_with_unit",
        "reasonableness_check",
    ),
}

_REPRESENTATIONS = {
    "G4-FRACTIONS": (
        "concrete equal-share tiles",
        "fraction bar or number line",
        "fraction notation and comparison statement",
    ),
    "G4-DECIMAL-FRACTIONS": (
        "base-ten grid pieces",
        "hundred grid or place-value chart",
        "fraction-decimal notation",
    ),
    "G4-MULTISTEP-WORD": (
        "countable groups in the context",
        "tape diagram with labelled quantities and units",
        "ordered equations with intermediate units",
    ),
}

_SOCRATIC_QUESTIONS = {
    "FRAC.UNIT.USE_WHOLE": "If one part is selected, which number names the selected parts and which names all equal parts in the whole?",
    "FRAC.NUMBER_LINE.COUNT_MARKS": "Are you counting tick marks or equal intervals from 0, and how many intervals make one whole?",
    "FRAC.COMPARE.BIGGER_DENOM": "When the numerators match, which fraction uses larger pieces of the same whole? How can a bar prove it?",
    "DEC.FRACTION.DIVIDE_WRONG_WAY": "Does the fraction ask for numerator divided by denominator, or the reverse? What value should stay between 0 and 1?",
    "DEC.ORDER.REVERSE": "Which place is the first place where these decimals differ when their decimal points are aligned?",
    "DEC.ALIGN.LAST_DIGITS": "Which digits represent ones, tenths, and hundredths after the decimal points are aligned?",
    "ADD.WORD.MULTISTEP.TWO_ONLY": "Which third quantity in the story has not yet been represented in your running total?",
    "SUB.WORD.MULTISTEP.SUBTRACT_ONCE": "After the first amount is removed, what later change still has to act on the intermediate quantity?",
    "SUB.WORD.MULTISTEP.ADD_INSTEAD": "Does each event increase the starting amount or remove from it? What sign matches the story?",
    "MUL.MULTISTEP.FORGOT_ADD": "What quantity comes from equal groups, and what separate extra quantity must be combined afterward?",
    "DIV.WORD.MULTISTEP.ONE_STEP": "After combining both source amounts, what equal-sharing step is still required?",
}


@dataclass(frozen=True)
class Variant:
    concept_id: str
    mode: str
    seed: int
    item_id: str
    family_code: str
    prompt: str
    response_fields: tuple[str, ...]
    representations: tuple[str, ...]
    visual_contract: dict[str, Any]
    canonical_answer: str
    misconceptions: tuple[tuple[str, str], ...]

    def public_payload(self) -> dict[str, Any]:
        """Return the answer-free learner contract."""

        return {
            "concept_id": self.concept_id,
            "mode": self.mode,
            "item_id": self.item_id,
            "family_code": self.family_code,
            "prompt": self.prompt,
            "response_fields": list(self.response_fields),
            "representations": list(self.representations),
            "visual_contract": dict(self.visual_contract),
            "support_prompts": [],
        }

    def teacher_oracle(self) -> dict[str, Any]:
        """Return exact evidence reserved for independent verification."""

        return {
            "family_code": self.family_code,
            "canonical_answer": self.canonical_answer,
            "misconception_answers": dict(self.misconceptions),
            "verification_required": "RECONSTRUCT_FROM_PROMPT",
        }


def _validate(concept_id: str, seed: int, mode: str) -> None:
    if concept_id not in CONCEPT_FAMILIES:
        raise ValueError("unknown Grade 4 depth concept")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if mode not in MODES:
        raise ValueError("unsupported mode")


def _family_for(concept_id: str, seed: int, mode: str) -> str:
    families = CONCEPT_FAMILIES[concept_id]
    return families[(seed + MODES.index(mode)) % len(families)]


def _visual_contract(concept_id: str, canonical_visual: dict[str, Any] | None) -> dict[str, Any]:
    # Canonical builders may return solved visual values for guided teaching.
    # This wrapper intentionally publishes only the representation type and
    # learner action so independent/mastery payloads cannot expose an answer.
    return {
        "type": (canonical_visual or {}).get("type", "structured_math_model"),
        "learner_action": "construct the model from the prompt; no values are prefilled",
        "keyboard_order": list(_RESPONSE_FIELDS[concept_id]),
        "screen_reader_order": ["prompt", "model", "response fields", "feedback"],
        "announce_changed_quantity_and_unit": True,
        "focus_after_feedback": "first field requiring revision",
        "reduced_motion": "instant state change with text announcement",
        "non_colour_equivalent": "labels, boundaries, and patterns",
    }


def _build(concept_id: str, family_code: str, seed: int, mode: str, purpose: str) -> Variant:
    rng = Random(f"{NAMESPACE}:{concept_id}:{family_code}:{mode}:{purpose}:{seed}")
    built = _BUILDERS[family_code](family_code, rng, 3)
    prompt, answer, _canonical_hints, misconceptions = built[:4]
    canonical_visual = built[4] if len(built) == 5 else None
    item_id = f"{NAMESPACE}:{concept_id}:{mode}:{purpose}:{seed}:{family_code}"
    return Variant(
        concept_id=concept_id,
        mode=mode,
        seed=seed,
        item_id=item_id,
        family_code=family_code,
        prompt=prompt,
        response_fields=_RESPONSE_FIELDS[concept_id],
        representations=_REPRESENTATIONS[concept_id],
        visual_contract=_visual_contract(concept_id, canonical_visual),
        canonical_answer=str(answer),
        misconceptions=tuple(
            sorted((str(code), str(value)) for code, value in misconceptions.items())
        ),
    )


def generate(concept_id: str, seed: int, mode: str) -> Variant:
    """Generate one deterministic, mode-separated draft variant."""

    _validate(concept_id, seed, mode)
    return _build(concept_id, _family_for(concept_id, seed, mode), seed, mode, "base")


def _different_family(concept_id: str, family_code: str, seed: int, purpose: str) -> str:
    families = CONCEPT_FAMILIES[concept_id]
    offset = Random(f"{NAMESPACE}:{purpose}:{concept_id}:{seed}").randrange(1, len(families))
    return families[(families.index(family_code) + offset) % len(families)]


def guided_support_for_response(
    variant: Variant, observed_response: object
) -> dict[str, Any] | None:
    """Return misconception-specific, answer-hidden guided repair or fail closed."""

    if variant.mode != "guided" or not isinstance(observed_response, (str, int, float)):
        return None
    normalized = "".join(str(observed_response).lower().split())
    matches = [
        code
        for code, value in variant.misconceptions
        if "".join(value.lower().split()) == normalized
    ]
    if len(matches) != 1:
        return None
    code = matches[0]
    question = _SOCRATIC_QUESTIONS.get(code)
    if question is None:
        return None
    family_code = _different_family(variant.concept_id, variant.family_code, variant.seed, "repair")
    repair = _build(
        variant.concept_id,
        family_code,
        variant.seed + 1_000_003,
        "guided",
        "repair",
    )
    return {
        "misconception_code": code,
        "socratic_question": question,
        "repair_task": repair.public_payload(),
    }


def independent_transfer(source: Variant, seed: int) -> Variant:
    """Generate a structurally different, hint-free independent exit."""

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    family_code = _different_family(source.concept_id, source.family_code, seed, "transfer")
    return _build(source.concept_id, family_code, seed, "independent", "transfer")
