"""Draft-only shared Grade 8 inverse-operation question depth.

The package reuses the existing ``M8.ALG.INVERSE.ADD`` and
``M8.ALG.INVERSE.MULT`` skill identities.  It is deliberately outside the
application import graph: there is no persistence, selector, scorer, routing,
curriculum-mapping, or mastery authority here.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from fractions import Fraction
from functools import cache
from types import MappingProxyType
from typing import Final

STATUS: Final = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION: Final = False
NAMESPACE: Final = "canonical-grade8:inverse-operations-depth-r1"
MODES: Final = frozenset({"diagnostic", "guided", "independent", "mastery"})
TEACHING_STAGES: Final = (
    "OBSERVE",
    "PREDICT",
    "MANIPULATE",
    "EXPLAIN",
    "PRACTICE",
    "DIAGNOSE",
    "TRANSFER",
    "VERIFY",
)

ADD_SKILL: Final = "M8.ALG.INVERSE.ADD"
MULT_SKILL: Final = "M8.ALG.INVERSE.MULT"
PRIMARY_SEED_COUNT: Final = 192
TRANSFER_SEED_OFFSET: Final = 1_000_003

FAMILIES: Final = (
    "MATH.EQ.INVERSE.ADD.BALANCE",
    "MATH.EQ.INVERSE.SUB.MISSING_ADDEND",
    "MATH.EQ.INVERSE.ADD.VARIABLE_RIGHT",
    "MATH.EQ.INVERSE.ADD.RATIONAL",
    "MATH.EQ.INVERSE.ADD.CHANGE_CONTEXT",
    "MATH.EQ.INVERSE.ADD.ERROR_ANALYSIS",
    "MATH.EQ.INVERSE.MULT.BALANCE",
    "MATH.EQ.INVERSE.DIV.QUOTIENT",
    "MATH.EQ.INVERSE.MULT.NEGATIVE",
    "MATH.EQ.INVERSE.MULT.RATIONAL",
    "MATH.EQ.INVERSE.MULT.SCALE_CONTEXT",
    "MATH.EQ.INVERSE.MULT.ERROR_ANALYSIS",
)

CANONICAL_SKILL: Final = MappingProxyType(
    {family: ADD_SKILL for family in FAMILIES[:6]}
    | {family: MULT_SKILL for family in FAMILIES[6:]}
)

TRANSFER_PARTNER: Final = MappingProxyType(
    {
        FAMILIES[0]: FAMILIES[4],
        FAMILIES[1]: FAMILIES[3],
        FAMILIES[2]: FAMILIES[5],
        FAMILIES[3]: FAMILIES[1],
        FAMILIES[4]: FAMILIES[0],
        FAMILIES[5]: FAMILIES[2],
        FAMILIES[6]: FAMILIES[10],
        FAMILIES[7]: FAMILIES[9],
        FAMILIES[8]: FAMILIES[11],
        FAMILIES[9]: FAMILIES[7],
        FAMILIES[10]: FAMILIES[6],
        FAMILIES[11]: FAMILIES[8],
    }
)

ACCESSIBILITY_CONTRACT: Final = MappingProxyType(
    {
        "keyboard": "Every balance control, number-line step, and response field is reachable and operable without dragging.",
        "screen_reader": "Announce the left expression, equality relation, right expression, operation applied to both sides, and resulting equation in order.",
        "visual": "Use labels, shapes, and text in addition to colour; preserve the equals sign as the visual balance anchor.",
        "motion": "A reduced-motion state presents before/after equations simultaneously instead of animating balance pieces.",
        "input": "Accept integers and any equivalent exact fraction; do not require pointer drawing or decimal approximation.",
        "focus": "After a transformation, focus moves to the resulting equation and its concise live-region summary.",
    }
)

FAMILY_CONTRACT: Final = MappingProxyType(
    {
        FAMILIES[0]: ("signed-number addition", "one inverse step with equality preservation", "signed integer"),
        FAMILIES[1]: ("subtraction and missing-addend meaning", "reconcile subtraction with addition", "signed integer"),
        FAMILIES[2]: ("symmetry of equality", "variable expression appears on the right", "signed integer"),
        FAMILIES[3]: ("exact fraction addition", "inverse addition with rational values", "exact rational"),
        FAMILIES[4]: ("signed change in context", "model an unknown start value", "context-valid exact rational"),
        FAMILIES[5]: ("equality-preserving addition", "analyze, refute, and correct a sign error", "signed integer"),
        FAMILIES[6]: ("multiplication facts and equality", "one inverse division step", "signed integer"),
        FAMILIES[7]: ("division as an equation", "undo a quotient with multiplication", "signed integer"),
        FAMILIES[8]: ("signed multiplication", "isolate from a negative coefficient", "signed integer"),
        FAMILIES[9]: ("fraction multiplication", "undo a rational coefficient with its reciprocal", "exact rational"),
        FAMILIES[10]: ("constant scale in context", "model an unknown per-group quantity", "context-valid exact rational"),
        FAMILIES[11]: ("coefficient meaning", "analyze, refute, and correct coefficient-as-addend reasoning", "signed integer"),
    }
)

_REPAIR: Final = MappingProxyType(
    {
        "EQ_001": (
            "What operation is attached to x in the original equation?",
            "Which opposite operation must be applied to both sides to keep equality?",
            "Show the same signed counter change on both balance pans.",
            "This response repeats the attached operation. Equality is preserved by applying the opposite operation to both complete sides.",
        ),
        "EQ_005": (
            "Which side contains x, and does that change what equality means?",
            "Can you swap the complete left and right expressions before isolating x?",
            "Rotate the whole balance; do not move a term across the equals sign.",
            "Equality is symmetric: the complete sides may exchange positions, but a term cannot move alone and change sign without an operation on both sides.",
        ),
        "EQ_006": (
            "What is the sign of the offset, including its numerator?",
            "What exact opposite fraction added to both sides makes that offset zero?",
            "Partition both sides into the same denominator before cancelling opposites.",
            "The response loses part of the signed fraction. The exact additive opposite must include the original sign, numerator, and denominator.",
        ),
        "EQ_007": (
            "Does the stated change describe the start, the change, or the final value?",
            "What equation reconstructs final = start + change?",
            "Place start, signed change, and final on a labelled number line.",
            "The response confuses the start, signed change, and final value. Reconstructing final = start + change identifies which quantity is unknown.",
        ),
        "EQ_003": (
            "Is the coefficient multiplying x or being added to x?",
            "Which division applied to both sides makes the coefficient equal to 1?",
            "Partition both balance pans into the same number of equal groups.",
            "The response multiplies by the coefficient again. Because the coefficient multiplies x, equal division on both sides is the preserving inverse.",
        ),
        "EQ_008": (
            "What operation does the fraction bar apply to x?",
            "What multiplication on both sides undoes division by the divisor?",
            "Regroup each side into equal sets of the divisor before recombining.",
            "The response divides an already divided quantity again. Multiplication by the divisor recomposes the whole on both sides.",
        ),
        "EQ_009": (
            "What is the sign of the coefficient multiplying x?",
            "After division, what sign results from the quotient of the two signed values?",
            "Label the signed coefficient before partitioning both sides equally.",
            "The response drops the coefficient's negative sign. Dividing by a signed coefficient must preserve both its magnitude and sign.",
        ),
        "EQ_010": (
            "Which exact number multiplies x?",
            "What reciprocal makes that coefficient equal to 1, and what must happen on the other side?",
            "Use equal fraction strips to show reciprocal multiplication on both sides.",
            "The response uses the coefficient again instead of its reciprocal. Only the reciprocal makes the rational coefficient equal to one.",
        ),
        "EQ_011": (
            "Does the total name one group or all equal groups?",
            "Which quotient recovers the amount in one group?",
            "Partition the total into the stated number of equal, labelled groups.",
            "The response treats the total as one group. Equal sharing by the number of groups recovers the amount in each group.",
        ),
        "EQ_004": (
            "In the term ax, what operation connects a and x?",
            "Would subtracting a undo multiplication by a? Test by substitution.",
            "Replace repeated x-groups with equal boxes before choosing the inverse.",
            "The response treats a coefficient as an addend. In ax, a and x are multiplied, so subtraction cannot undo the relationship.",
        ),
    }
)

_STRATEGY_OPTION: Final = MappingProxyType(
    {
        "EQ_001": (
            "REPEATED_ATTACHED_OPERATION",
            "I repeated the operation attached to x on the other value.",
        ),
        "EQ_005": (
            "MOVED_TERM_ACROSS_EQUALS",
            "I moved a term across the equals sign and changed it there.",
        ),
        "EQ_006": (
            "IGNORED_FRACTION_DETAIL",
            "I worked with part of the fraction but not its full signed value.",
        ),
        "EQ_007": (
            "CONFUSED_START_CHANGE_FINAL",
            "I used the final value as the start or treated the change as the final value.",
        ),
        "EQ_003": (
            "MULTIPLIED_BY_COEFFICIENT_AGAIN",
            "I multiplied by the coefficient again.",
        ),
        "EQ_008": (
            "DIVIDED_BY_DIVISOR_AGAIN",
            "I divided by the divisor again.",
        ),
        "EQ_009": (
            "DROPPED_NEGATIVE_COEFFICIENT",
            "I used the coefficient's magnitude but did not keep its negative sign.",
        ),
        "EQ_010": (
            "USED_COEFFICIENT_NOT_RECIPROCAL",
            "I multiplied by the coefficient instead of its reciprocal.",
        ),
        "EQ_011": (
            "USED_TOTAL_AS_ONE_GROUP",
            "I treated the total as the amount in one group.",
        ),
        "EQ_004": (
            "TREATED_COEFFICIENT_AS_ADDEND",
            "I treated the coefficient as though it were added to x.",
        ),
    }
)

_ADD_STRATEGIES: Final = ("EQ_001", "EQ_005", "EQ_006", "EQ_007")
_MULT_STRATEGIES: Final = ("EQ_003", "EQ_008", "EQ_009", "EQ_010", "EQ_011", "EQ_004")


def _fmt(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _signed(value: Fraction) -> str:
    return f"+ {_fmt(value)}" if value >= 0 else f"- {_fmt(-value)}"


def equation_display(variant: Variant) -> str:
    """Return the task equation without revealing an inverse operation."""

    p = dict(variant.parameters)
    coefficient = Fraction(p["coefficient"])
    offset = Fraction(p["offset"])
    rhs = p["rhs"]
    if variant.family == FAMILIES[7]:
        divisor = 1 / coefficient
        left = f"x/{_fmt(divisor)}"
    elif coefficient == 1:
        left = "x"
    elif coefficient == -1:
        left = "-x"
    else:
        left = f"{_fmt(coefficient)}x"
    if offset:
        left = f"{left} {_signed(offset)}"
    if variant.family == FAMILIES[2]:
        return f"{rhs} = {left}"
    return f"{left} = {rhs}"


def _unhinted_prompt(variant: Variant) -> str:
    """Keep independent/mastery wording free of operation or repair cues."""

    p = dict(variant.parameters)
    if variant.family == FAMILIES[4]:
        return (
            f"A quantity changed by {_fmt(Fraction(p['offset']))} and ended at "
            f"{p['rhs']}. Find the starting value and verify it."
        )
    if variant.family == FAMILIES[10]:
        return (
            f"{p['coefficient']} identical groups have total {p['rhs']}. "
            "Find the amount in each group and verify it."
        )
    if variant.family in {FAMILIES[5], FAMILIES[11]}:
        return variant.prompt
    return f"Solve {equation_display(variant)} exactly and verify by substitution."


def _validate(family: str, seed: int, mode: str) -> None:
    if family not in FAMILIES:
        raise ValueError(f"Unsupported family: {family}")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    in_primary_band = 0 <= seed < PRIMARY_SEED_COUNT
    in_transfer_band = (
        TRANSFER_SEED_OFFSET
        <= seed
        < TRANSFER_SEED_OFFSET + PRIMARY_SEED_COUNT
    )
    if not (in_primary_band or in_transfer_band):
        raise ValueError("seed must be in a reviewed nonrepeating seed band")
    if mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode}")


@dataclass(frozen=True)
class Variant:
    variant_id: str
    family: str
    canonical_skill: str
    mode: str
    structure: str
    prompt: str
    parameters: tuple[tuple[str, str], ...]
    answer: str
    prerequisite: str
    difficulty_rationale: str
    equivalence_boundary: str
    representation: tuple[str, str, str]
    misconception_answers: tuple[tuple[str, str], ...]

    def public_payload(self) -> dict[str, object]:
        """Return the answer-free entry contract with mode-specific stages."""

        state = start_learning_path(self)
        payload: dict[str, object] = {
            "variant_id": self.variant_id,
            "family": self.family,
            "mode": self.mode,
            "structure": self.structure,
            "learning_path": list(state.stages),
            "initial_stage": stage_payload(self, state),
            "accessibility": dict(ACCESSIBILITY_CONTRACT),
        }
        if self.mode in {"independent", "mastery"}:
            payload["support"] = "NONE_UNHINTED"
        return payload

    def teacher_oracle(self) -> dict[str, object]:
        """Return exact review evidence; this is never learner payload."""

        return {
            "answer": self.answer,
            "parameters": dict(self.parameters),
            "verification": verification_equation(self),
            "answer_equivalence": "Any exact integer or fraction equal to the oracle is valid.",
            "domain_boundary": self.equivalence_boundary,
        }


@dataclass(frozen=True)
class LearningState:
    """Pure, renderer-neutral evidence state for one learner path."""

    variant_id: str
    mode: str
    stages: tuple[str, ...]
    position: int = 0
    prediction_locked: bool = False
    prediction_choice: str | None = None
    prediction_feedback: str | None = None
    completed: tuple[str, ...] = ()
    practiced_answer: str | None = None
    explanation_evidence: str | None = None
    diagnosis_classification: str | None = None
    diagnosis_feedback: tuple[str, ...] = ()
    repair_completed: bool = False

    @property
    def stage(self) -> str:
        return "COMPLETE" if self.position >= len(self.stages) else self.stages[self.position]


def _mode_stages(mode: str) -> tuple[str, ...]:
    if mode == "guided":
        return TEACHING_STAGES
    if mode == "diagnostic":
        return ("DIAGNOSE", "TRANSFER", "VERIFY")
    return ("PRACTICE", "VERIFY")


def start_learning_path(variant: Variant) -> LearningState:
    return LearningState(
        variant_id=variant.variant_id,
        mode=variant.mode,
        stages=_mode_stages(variant.mode),
    )


def stage_payload(variant: Variant, state: LearningState) -> dict[str, object]:
    """Reveal only the material allowed at the current stage."""

    if state.variant_id != variant.variant_id or state.mode != variant.mode:
        raise ValueError("learning state does not belong to this variant")
    stage = state.stage
    if stage == "COMPLETE":
        return {"stage": stage, "response_fields": []}
    if stage == "OBSERVE":
        return {
            "stage": stage,
            "instruction": "Describe what is equal before choosing an operation.",
            "equation": equation_display(variant),
            "representation": variant.representation[0],
            "response_fields": ["observation"],
            "reveals_inverse_operation": False,
        }
    if stage == "PREDICT":
        payload = {
            "stage": stage,
            "instruction": "Predict which operation should be applied to both complete sides.",
            "response_fields": ["operation_choice"],
            "choices": ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"],
            "lock_before_next": True,
            "reveals_inverse_operation": False,
        }
        if state.prediction_choice is not None:
            payload["recorded_prediction"] = state.prediction_choice
        if state.prediction_feedback is not None:
            payload["socratic_feedback"] = state.prediction_feedback
        return payload
    if stage == "MANIPULATE":
        if not state.prediction_locked:
            raise ValueError("prediction must be locked before manipulation is revealed")
        return {
            "stage": stage,
            "instruction": "Apply one operation to the complete left and right sides.",
            "representation": variant.representation[1],
            "response_fields": ["left_operation", "right_operation", "operation_value", "resulting_x"],
            "same_operation_required": True,
        }
    if stage == "EXPLAIN":
        return {
            "stage": stage,
            "instruction": "Explain why the transformation preserves equality.",
            "representation": variant.representation[2],
            "response_fields": ["reasoning_choice", "equality_justification"],
            "reasoning_choices": [
                {
                    "id": "SAME_OPERATION_BOTH_SIDES",
                    "label": "The same operation was applied to both complete sides.",
                },
                {
                    "id": "MOVE_TERM_CHANGE_SIGN",
                    "label": "A term moved across the equals sign and changed sign.",
                },
                {
                    "id": "ONE_SIDE_ONLY",
                    "label": "Only the side containing x needs to change.",
                },
            ],
        }
    if stage == "PRACTICE":
        return {
            "stage": stage,
            "instruction": (
                variant.prompt if variant.mode == "guided" else _unhinted_prompt(variant)
            ),
            "response_fields": ["exact_answer"],
            "support": "FADING_GUIDED" if variant.mode == "guided" else "NONE_UNHINTED",
        }
    if stage == "DIAGNOSE":
        if variant.mode != "guided":
            return {
                "stage": stage,
                "instruction": "Solve the diagnostic item exactly without guided support.",
                "response_fields": ["exact_answer"],
                "support": "NONE_UNHINTED",
                "guided_repair_available": False,
            }
        if state.practiced_answer is None:
            raise ValueError("guided diagnosis requires the retained practice response")
        if (
            state.diagnosis_classification is not None
            and state.diagnosis_classification.startswith("EQ_")
        ):
            return {
                "stage": stage,
                "phase": "TARGETED_REPAIR_EXIT",
                "instruction": "Use the guided repair, then solve the original equation again without an answer reveal.",
                "guided_support": list(state.diagnosis_feedback),
                "response_fields": [
                    "repair_reflection_choice",
                    "repair_exit_answer",
                ],
                "reflection_choices": [
                    {
                        "id": "APPLY_INVERSE_TO_BOTH_SIDES",
                        "label": "Apply the inverse operation to both complete sides.",
                    },
                    {
                        "id": "CHANGE_ONE_SIDE",
                        "label": "Change only the side containing x.",
                    },
                ],
                "worked_answer_reveal": False,
            }
        probe = guided_probe(variant, state.practiced_answer)
        assert probe is not None
        if probe["classification"] == "CORRECT_NO_REMEDIATION":
            return {
                "stage": stage,
                "phase": "CORRECT_CONFIRMATION",
                "instruction": (
                    "Your retained practice response satisfies the original equation. "
                    "Confirm that you are ready for an unhinted transfer task."
                ),
                "response_fields": ["confirm_ready_for_transfer"],
                "support": "NONE_UNHINTED",
            }
        payload = {
            "stage": stage,
            "instruction": (
                "Use the retained practice response, your strategy, and exact "
                "substitution evidence before selecting a repair."
            ),
            "response_fields": [
                "strategy_choice",
                "substitution_left",
                "substitution_right",
            ],
            "classification_from_one_wrong_answer": False,
        }
        if variant.mode == "guided":
            strategy_codes = (
                _ADD_STRATEGIES
                if variant.canonical_skill == ADD_SKILL
                else _MULT_STRATEGIES
            )
            payload["strategy_choices"] = [
                {
                    "id": _STRATEGY_OPTION[code][0],
                    "label": _STRATEGY_OPTION[code][1],
                }
                for code in strategy_codes
            ] + [
                {
                    "id": "OTHER_OR_UNSURE",
                    "label": "I used a different strategy or I am not sure.",
                }
            ]
        if state.diagnosis_feedback:
            payload["neutral_retry"] = list(state.diagnosis_feedback)
        return payload
    if stage == "TRANSFER":
        return {
            "stage": stage,
            "instruction": "Complete a fresh different-family item without hints.",
            "response_fields": [
                "independent_variant_id",
                "independent_answer",
                "independent_family",
                "independent_mode",
                "support_used",
            ],
            "required_mode": "independent",
        }
    return {
        "stage": "VERIFY",
        "instruction": "Substitute the completed result and compare both sides exactly.",
        "response_fields": ["substitution_left", "substitution_right"],
        "exact_equality_required": True,
    }


def _nonempty(response: dict[str, object], field: str) -> bool:
    value = response.get(field)
    return isinstance(value, str) and bool(value.strip())


def _equivalent_inverse_operations(
    variant: Variant,
) -> tuple[tuple[str, Fraction, Fraction], ...]:
    """Return every exact one-step operation/value pair that isolates x."""

    p = dict(variant.parameters)
    coefficient = Fraction(p["coefficient"])
    offset = Fraction(p["offset"])
    rhs = Fraction(p["rhs"])
    if coefficient == 1 and offset != 0:
        operation = "SUBTRACT" if offset > 0 else "ADD"
        return ((operation, abs(offset), rhs - offset),)
    if coefficient != 1 and offset == 0:
        solution = rhs / coefficient
        return (
            ("DIVIDE", coefficient, solution),
            ("MULTIPLY", 1 / coefficient, solution),
        )
    raise ValueError("unsupported one-step inverse structure")


def _prediction_prompt(variant: Variant) -> str:
    operations = {operation for operation, _, _ in _equivalent_inverse_operations(variant)}
    if operations <= {"ADD", "SUBTRACT"}:
        return (
            "What operation undoes the signed offset on x, and why must it "
            "be applied to both complete sides?"
        )
    return (
        "What operation makes the coefficient of x equal to one, and why "
        "must it be applied to both complete sides?"
    )


def _valid_equality_explanation(response: dict[str, object]) -> bool:
    if response.get("reasoning_choice") != "SAME_OPERATION_BOTH_SIDES":
        return False
    if not _nonempty(response, "equality_justification"):
        return False
    words = str(response["equality_justification"]).casefold()
    mentions_both_sides = "both" in words and "side" in words
    names_preservation = any(
        marker in words for marker in ("equal", "equality", "same value")
    )
    return mentions_both_sides and names_preservation


def advance_learning_path(
    variant: Variant, state: LearningState, response: dict[str, object]
) -> LearningState:
    """Advance only when the current stage's learner evidence is complete."""

    if state.variant_id != variant.variant_id or state.mode != variant.mode:
        raise ValueError("learning state does not belong to this variant")
    stage = state.stage
    prediction_locked = state.prediction_locked
    prediction_choice = state.prediction_choice
    prediction_feedback = state.prediction_feedback
    practiced_answer = state.practiced_answer
    explanation_evidence = state.explanation_evidence
    diagnosis_classification = state.diagnosis_classification
    diagnosis_feedback = state.diagnosis_feedback
    repair_completed = state.repair_completed
    if stage == "COMPLETE":
        raise ValueError("learning path is already complete")
    if stage == "OBSERVE" and not _nonempty(response, "observation"):
        raise ValueError("observation evidence is required")
    if stage == "PREDICT":
        choice = response.get("operation_choice")
        if choice not in {"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"}:
            raise ValueError("a supported operation prediction is required")
        prediction_choice = str(choice)
        allowed_operations = {
            operation
            for operation, _, _ in _equivalent_inverse_operations(variant)
        }
        if choice not in allowed_operations:
            return replace(
                state,
                prediction_choice=prediction_choice,
                prediction_feedback=_prediction_prompt(variant),
                prediction_locked=False,
            )
        prediction_locked = True
        prediction_feedback = None
    if stage == "MANIPULATE":
        left = response.get("left_operation")
        right = response.get("right_operation")
        if not prediction_locked or not isinstance(left, str) or left != right or not left:
            raise ValueError("the same nonempty operation must be applied to both sides")
        try:
            value = Fraction(str(response["operation_value"]))
            resulting_x = Fraction(str(response["resulting_x"]))
        except (KeyError, ValueError, ZeroDivisionError):
            raise ValueError("exact inverse value and resulting x are required") from None
        equivalent_operations = _equivalent_inverse_operations(variant)
        if not any(
            left == operation
            and value == required_value
            and resulting_x == expected_x
            for operation, required_value, expected_x in equivalent_operations
        ):
            raise ValueError("transformation must isolate x with exact inverse arithmetic")
    if stage == "EXPLAIN":
        if not _valid_equality_explanation(response):
            raise ValueError(
                "select the equality-preserving reason and explain both complete sides"
            )
        explanation_evidence = str(response["equality_justification"]).strip()
    if stage == "PRACTICE":
        try:
            practiced_answer = _fmt(Fraction(str(response["exact_answer"])))
        except (KeyError, ValueError, ZeroDivisionError):
            raise ValueError("an exact practice response is required") from None
        if variant.mode != "guided" and practiced_answer != variant.answer:
            raise ValueError("practice answer does not solve the original equation")
    if stage == "DIAGNOSE":
        if variant.mode != "guided":
            try:
                observed = Fraction(str(response["exact_answer"]))
            except (KeyError, ValueError, ZeroDivisionError):
                raise ValueError("an exact diagnostic response is required") from None
            if observed != Fraction(variant.answer):
                raise ValueError(
                    "diagnostic evidence cannot unlock guided repair or transfer"
                )
            practiced_answer = _fmt(observed)
            diagnosis_classification = "CORRECT_NO_REMEDIATION"
            diagnosis_feedback = ()
        elif (
            diagnosis_classification is not None
            and diagnosis_classification.startswith("EQ_")
        ):
            if response.get("repair_reflection_choice") != "APPLY_INVERSE_TO_BOTH_SIDES":
                raise ValueError("repair reflection must preserve both complete sides")
            try:
                exit_answer = Fraction(str(response["repair_exit_answer"]))
            except (KeyError, ValueError, ZeroDivisionError):
                raise ValueError("an exact repair-exit answer is required") from None
            if exit_answer != Fraction(variant.answer):
                raise ValueError("repair exit must solve the original equation")
            practiced_answer = _fmt(exit_answer)
            repair_completed = True
        else:
            if practiced_answer is None:
                raise ValueError("guided diagnosis requires the retained practice response")
            probe = guided_probe(variant, practiced_answer)
            assert probe is not None
            if probe["classification"] == "CORRECT_NO_REMEDIATION":
                if response.get("confirm_ready_for_transfer") is not True:
                    raise ValueError("correct practice must be confirmed before transfer")
                diagnosis_classification = "CORRECT_NO_REMEDIATION"
                diagnosis_feedback = ()
            elif probe["classification"] == "UNPARSEABLE_NEEDS_CLARIFICATION":
                return replace(
                    state,
                    diagnosis_classification="NEUTRAL_RETRY",
                    diagnosis_feedback=tuple(probe["questions"]),
                )
            else:
                required = (
                    "strategy_choice",
                    "substitution_left",
                    "substitution_right",
                )
                if not all(_nonempty(response, field) for field in required):
                    return replace(
                        state,
                        diagnosis_classification="NEUTRAL_RETRY",
                        diagnosis_feedback=tuple(probe["questions"]),
                    )
                repair = guided_repair(
                    variant,
                    practiced_answer,
                    str(response["strategy_choice"]),
                    str(response["substitution_left"]),
                    str(response["substitution_right"]),
                )
                assert repair is not None
                classification = str(repair["classification"])
                if not classification.startswith("EQ_"):
                    return replace(
                        state,
                        diagnosis_classification="NEUTRAL_RETRY",
                        diagnosis_feedback=tuple(repair["questions"]),
                    )
                return replace(
                    state,
                    diagnosis_classification=classification,
                    diagnosis_feedback=(
                        str(repair["guided_explanation"]),
                        *tuple(str(q) for q in repair["questions"]),
                    ),
                    repair_completed=False,
                )
    if stage == "TRANSFER":
        if (
            not _nonempty(response, "independent_variant_id")
            or not _nonempty(response, "independent_family")
            or response.get("independent_mode") != "independent"
            or response.get("independent_family") == variant.family
            or response.get("support_used") is not False
        ):
            raise ValueError("fresh different-family unhinted independent transfer is required")
        expected_transfer = generate_transfer(variant)
        if (response["independent_variant_id"] != expected_transfer.variant_id
                or response["independent_family"] != expected_transfer.family):
            raise ValueError("transfer identifier must match the generated task")
        try:
            transfer_answer = Fraction(str(response["independent_answer"]))
        except (KeyError, ValueError, ZeroDivisionError):
            raise ValueError("exact independent transfer answer is required") from None
        if transfer_answer != Fraction(expected_transfer.answer):
            raise ValueError("independent transfer did not solve the fresh task")
    if stage == "VERIFY":
        try:
            left = Fraction(str(response["substitution_left"]))
            right = Fraction(str(response["substitution_right"]))
        except (KeyError, ValueError, ZeroDivisionError):
            raise ValueError("two exact substitution values are required") from None
        p = dict(variant.parameters)
        if practiced_answer is None:
            raise ValueError("verified practice answer required before verification")
        answer = Fraction(practiced_answer)
        expected_left = Fraction(p["coefficient"]) * answer + Fraction(p["offset"])
        expected_right = Fraction(p["rhs"])
        if left != expected_left or right != expected_right or left != right:
            raise ValueError("verification must reconstruct the original equation exactly")
    return LearningState(
        variant_id=state.variant_id,
        mode=state.mode,
        stages=state.stages,
        position=state.position + 1,
        prediction_locked=prediction_locked,
        prediction_choice=prediction_choice,
        prediction_feedback=prediction_feedback,
        completed=state.completed + (stage,),
        practiced_answer=practiced_answer,
        explanation_evidence=explanation_evidence,
        diagnosis_classification=diagnosis_classification,
        diagnosis_feedback=diagnosis_feedback,
        repair_completed=repair_completed,
    )


def _variant(
    *,
    family: str,
    seed: int,
    mode: str,
    structure: str,
    prompt: str,
    coefficient: Fraction,
    offset: Fraction,
    rhs: Fraction,
    solution: Fraction,
    wrong: dict[str, Fraction],
    representation: tuple[str, str, str],
) -> Variant:
    if coefficient == 0:
        raise AssertionError("A one-variable inverse-operation item needs a nonzero coefficient")
    if coefficient * solution + offset != rhs:
        raise AssertionError("Oracle does not satisfy its authored equation")
    answer = _fmt(solution)
    misconceptions = {
        code: _fmt(value) for code, value in wrong.items() if value != solution
    }
    if not misconceptions:
        raise AssertionError("Every variant needs a non-colliding misconception signature")
    prerequisite, rationale, boundary = FAMILY_CONTRACT[family]
    return Variant(
        variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
        family=family,
        canonical_skill=CANONICAL_SKILL[family],
        mode=mode,
        structure=structure,
        prompt=prompt,
        parameters=tuple(
            sorted(
                {
                    "coefficient": _fmt(coefficient),
                    "offset": _fmt(offset),
                    "rhs": _fmt(rhs),
                }.items()
            )
        ),
        answer=answer,
        prerequisite=prerequisite,
        difficulty_rationale=rationale,
        equivalence_boundary=boundary,
        representation=representation,
        misconception_answers=tuple(sorted(misconceptions.items())),
    )


@cache
def _candidate_pool(family: str) -> tuple[tuple[Fraction, ...], ...]:
    """Enumerate normalized parameter tuples before deterministic shuffling."""

    xs = tuple(Fraction(n) for n in range(-12, 13) if n)
    if family == FAMILIES[0]:
        pool = {(x, Fraction(offset)) for x in xs for offset in range(-11, 12) if offset}
    elif family == FAMILIES[1]:
        pool = {(x, Fraction(amount)) for x in xs for amount in range(2, 13)}
    elif family == FAMILIES[2]:
        pool = {(x, Fraction(offset)) for x in xs for offset in range(-10, 11) if offset}
    elif family == FAMILIES[3]:
        solutions = {
            Fraction(n, denominator)
            for n in range(-15, 16)
            if n
            for denominator in (2, 3, 4)
        }
        offsets = {
            Fraction(n, denominator)
            for n in range(-9, 10)
            if n
            for denominator in (2, 3, 4, 5, 6)
        }
        pool = {(solution, offset) for solution in solutions for offset in offsets}
    elif family == FAMILIES[4]:
        pool = {(x, Fraction(change)) for x in xs for change in range(-9, 10) if change}
    elif family == FAMILIES[5]:
        pool = {(x, Fraction(offset)) for x in xs for offset in range(2, 12)}
    elif family == FAMILIES[6]:
        pool = {(x, Fraction(coefficient)) for x in xs for coefficient in range(2, 13)}
    elif family == FAMILIES[7]:
        pool = {(x, Fraction(divisor)) for x in xs for divisor in range(2, 11)}
    elif family == FAMILIES[8]:
        pool = {(x, Fraction(magnitude)) for x in xs for magnitude in range(2, 11)}
    elif family == FAMILIES[9]:
        coefficients = {
            Fraction(numerator, denominator)
            for numerator in range(2, 9)
            for denominator in range(2, 10)
            if numerator != denominator
        }
        pool = {(solution, coefficient) for solution in xs for coefficient in coefficients}
    elif family == FAMILIES[10]:
        per_group_values = {
            Fraction(numerator, denominator)
            for numerator in range(1, 13)
            for denominator in (1, 2, 4)
        }
        pool = {
            (per_group, Fraction(groups))
            for per_group in per_group_values
            for groups in range(2, 13)
        }
    else:
        pool = {(x, Fraction(coefficient)) for x in xs for coefficient in range(2, 12)}
    ordered = tuple(sorted(pool))
    if len(ordered) < PRIMARY_SEED_COUNT:
        raise AssertionError("family needs at least one normalized task per reviewed seed")
    return ordered


def _seed_band(seed: int) -> tuple[str, int]:
    if seed < PRIMARY_SEED_COUNT:
        return "PRIMARY", seed
    return "TRANSFER", seed - TRANSFER_SEED_OFFSET


@cache
def _seeded_candidate(family: str, mode: str, seed: int) -> tuple[Fraction, ...]:
    band, slot = _seed_band(seed)
    candidates = list(_candidate_pool(family))
    random.Random(f"{NAMESPACE}:{family}:{mode}:{band}").shuffle(candidates)
    return candidates[slot]


def generate(family: str, seed: int, mode: str) -> Variant:
    """Generate one deterministic original task for a declared structure."""

    _validate(family, seed, mode)
    candidate = _seeded_candidate(family, mode, seed)

    if family == FAMILIES[0]:
        x, offset = candidate
        rhs = x + offset
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="SIGNED_ADDITIVE_BALANCE",
            prompt=f"Solve x {_signed(offset)} = {_fmt(rhs)}. Show the same inverse operation on both sides and verify by substitution.",
            coefficient=Fraction(1), offset=offset, rhs=rhs, solution=x,
            wrong={"EQ_001": rhs + offset},
            representation=(
                "Concrete: place x and signed counters on one balance pan and the total on the other.",
                "Visual: cross out opposite counter pairs after changing both pans equally.",
                f"Symbolic: add {_fmt(-offset)} to both sides, then substitute the result.",
            ),
        )

    if family == FAMILIES[1]:
        x, amount = candidate
        rhs = x - amount
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="SUBTRACTION_AS_MISSING_ADDEND",
            prompt=f"A number minus {_fmt(amount)} equals {_fmt(rhs)}. Find the number, rewrite the statement as a missing-addend equation, and verify it.",
            coefficient=Fraction(1), offset=-amount, rhs=rhs, solution=x,
            wrong={"EQ_001": rhs - amount},
            representation=(
                "Concrete: remove the stated number of signed counters from an unknown collection.",
                "Visual: reverse the leftward number-line displacement to recover the start.",
                f"Symbolic: x - {_fmt(amount)} = {_fmt(rhs)} is equivalent to {_fmt(rhs)} + {_fmt(amount)} = x.",
            ),
        )

    if family == FAMILIES[2]:
        x, offset = candidate
        rhs = x + offset
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="VARIABLE_EXPRESSION_ON_RIGHT_OF_EQUALITY",
            prompt=f"Solve {_fmt(rhs)} = x {_signed(offset)}. Explain why swapping the two complete sides preserves equality before isolating x.",
            coefficient=Fraction(1), offset=offset, rhs=rhs, solution=x,
            wrong={"EQ_005": rhs + offset, "EQ_001": -rhs - offset},
            representation=(
                "Concrete: rotate a balanced scale so the unknown pan appears first.",
                "Visual: bracket each complete side before exchanging their positions.",
                f"Symbolic: use equality symmetry, then add {_fmt(-offset)} to both sides.",
            ),
        )

    if family == FAMILIES[3]:
        solution, offset = candidate
        rhs = solution + offset
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="RATIONAL_OFFSET_EXACT_BALANCE",
            prompt=f"Solve x {_signed(offset)} = {_fmt(rhs)} exactly. Use fraction strips or a common denominator, and verify without a decimal approximation.",
            coefficient=Fraction(1), offset=offset, rhs=rhs, solution=solution,
            wrong={"EQ_006": rhs + offset, "EQ_001": rhs - abs(offset)},
            representation=(
                "Concrete: model both rational values with same-denominator fraction strips.",
                "Visual: remove or add the same signed fraction strip on both balance pans.",
                f"Symbolic: x = {_fmt(rhs)} - ({_fmt(offset)}), kept as an exact fraction.",
            ),
        )

    if family == FAMILIES[4]:
        x, change = candidate
        final = x + change
        direction = "rose" if change > 0 else "fell"
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="UNKNOWN_START_SIGNED_CHANGE_CONTEXT",
            prompt=f"A sensor reading {direction} by {_fmt(abs(change))} units and ended at {_fmt(final)}. Find the starting reading, write final = start + signed change, and check the context.",
            coefficient=Fraction(1), offset=change, rhs=final, solution=x,
            wrong={"EQ_007": final + change, "EQ_001": final - abs(change)},
            representation=(
                "Concrete: label cards for start, signed change, and final instead of relying on keywords.",
                "Visual: draw the signed displacement from the unknown start to the known final.",
                f"Symbolic: start {_signed(change)} = {_fmt(final)}.",
            ),
        )

    if family == FAMILIES[5]:
        x, offset = candidate
        rhs = x + offset
        claimed = rhs + offset
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="ADDITIVE_INVERSE_ERROR_ANALYSIS_AND_COUNTEREXAMPLE",
            prompt=f"A learner says x + {_fmt(offset)} = {_fmt(rhs)} gives x = {_fmt(claimed)} because the {_fmt(offset)} 'moves across' and stays positive. Test the claim by substitution, identify the equality error, and solve correctly.",
            coefficient=Fraction(1), offset=offset, rhs=rhs, solution=x,
            wrong={"EQ_001": claimed},
            representation=(
                "Concrete: compare changing one balance pan with changing both pans equally.",
                "Visual: mark the claimed value on a number line and test whether the forward change reaches the target.",
                f"Symbolic: substitute {_fmt(claimed)} for a counterexample, then subtract {_fmt(offset)} from both sides.",
            ),
        )

    if family == FAMILIES[6]:
        x, coefficient = candidate
        rhs = coefficient * x
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="INTEGER_COEFFICIENT_EQUAL_GROUP_BALANCE",
            prompt=f"Solve {_fmt(coefficient)}x = {_fmt(rhs)}. Partition both sides into the same number of equal groups and verify by multiplication.",
            coefficient=coefficient, offset=Fraction(0), rhs=rhs, solution=x,
            wrong={"EQ_003": rhs * coefficient, "EQ_004": rhs - coefficient},
            representation=(
                f"Concrete: arrange each balance pan into {_fmt(coefficient)} equal groups.",
                "Visual: pair each x-box with one equal share of the total.",
                f"Symbolic: divide both sides by {_fmt(coefficient)}.",
            ),
        )

    if family == FAMILIES[7]:
        x, divisor = candidate
        rhs = x / divisor
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="QUOTIENT_EQUATION_RECOMPOSITION",
            prompt=f"Solve x/{_fmt(divisor)} = {_fmt(rhs)}. Recompose the whole from equal shares, then verify the quotient.",
            coefficient=Fraction(1, divisor), offset=Fraction(0), rhs=rhs, solution=x,
            wrong={"EQ_008": rhs / divisor, "EQ_004": rhs + divisor},
            representation=(
                f"Concrete: combine {_fmt(divisor)} equal groups, each worth {_fmt(rhs)}.",
                "Visual: join equal tape-diagram sections to reconstruct the whole.",
                f"Symbolic: multiply both sides by {_fmt(divisor)}.",
            ),
        )

    if family == FAMILIES[8]:
        x, magnitude = candidate
        coefficient = -magnitude
        rhs = coefficient * x
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="NEGATIVE_COEFFICIENT_SIGNED_QUOTIENT",
            prompt=f"Solve {_fmt(coefficient)}x = {_fmt(rhs)}. Track the coefficient's sign, divide both sides, and verify the signed product.",
            coefficient=coefficient, offset=Fraction(0), rhs=rhs, solution=x,
            wrong={"EQ_009": -x, "EQ_003": rhs * coefficient},
            representation=(
                "Concrete: use signed equal groups, with each group representing the same unknown.",
                "Visual: label both magnitude and sign before making equal partitions.",
                f"Symbolic: x = {_fmt(rhs)} / ({_fmt(coefficient)}).",
            ),
        )

    if family == FAMILIES[9]:
        solution, coefficient = candidate
        rhs = coefficient * solution
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="RATIONAL_COEFFICIENT_RECIPROCAL",
            prompt=f"Solve ({_fmt(coefficient)})x = {_fmt(rhs)} exactly. Explain why multiplying both sides by {_fmt(1 / coefficient)} isolates x, then verify.",
            coefficient=coefficient, offset=Fraction(0), rhs=rhs, solution=solution,
            wrong={"EQ_010": rhs * coefficient, "EQ_003": rhs / (1 / coefficient)},
            representation=(
                "Concrete: use fraction strips to show the coefficient as part of one x-strip.",
                "Visual: scale both balance pans by the reciprocal with matched arrows.",
                f"Symbolic: ({_fmt(1 / coefficient)})({_fmt(coefficient)})x = ({_fmt(1 / coefficient)})({_fmt(rhs)}).",
            ),
        )

    if family == FAMILIES[10]:
        per_group, groups = candidate
        total = groups * per_group
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="UNKNOWN_PER_GROUP_SCALE_CONTEXT",
            prompt=f"{_fmt(groups)} identical kits use {_fmt(total)} metres of cord altogether. How many metres are in each kit? Model {_fmt(groups)}x = {_fmt(total)} and check that equal groups reconstruct the total.",
            coefficient=groups, offset=Fraction(0), rhs=total, solution=per_group,
            wrong={"EQ_011": total, "EQ_004": total - groups},
            representation=(
                f"Concrete: share {_fmt(total)} metres equally among {_fmt(groups)} labelled kits.",
                "Visual: partition one total-length tape into equal kit sections.",
                f"Symbolic: x = {_fmt(total)} / {_fmt(groups)}.",
            ),
        )

    x, coefficient = candidate
    rhs = coefficient * x
    claimed = rhs - coefficient
    return _variant(
        family=family, seed=seed, mode=mode,
        structure="COEFFICIENT_AS_ADDEND_ERROR_ANALYSIS",
        prompt=f"A learner solves {_fmt(coefficient)}x = {_fmt(rhs)} by subtracting {_fmt(coefficient)} and claims x = {_fmt(claimed)}. Explain what {_fmt(coefficient)}x means, test the claim, and solve with an equality-preserving inverse.",
        coefficient=coefficient, offset=Fraction(0), rhs=rhs, solution=x,
        wrong={"EQ_004": claimed, "EQ_003": rhs * coefficient},
        representation=(
            f"Concrete: build {_fmt(coefficient)} equal x-groups, not x plus {_fmt(coefficient)} counters.",
            "Visual: contrast repeated equal boxes with an additive counter strip.",
            f"Symbolic: divide both sides by {_fmt(coefficient)} and substitute to refute the claim.",
        ),
    )


def verification_equation(variant: Variant) -> str:
    p = dict(variant.parameters)
    return f"({_fmt(Fraction(p['coefficient']) * Fraction(variant.answer) + Fraction(p['offset']))}) = {p['rhs']}"


def guided_probe(variant: Variant, observed_answer: str) -> dict[str, object] | None:
    """Expose a learner-facing second probe without inferring from one answer."""

    if variant.mode != "guided":
        return None
    try:
        observed_value = Fraction(observed_answer)
        observed = _fmt(observed_value)
    except (ValueError, ZeroDivisionError):
        return {
            "classification": "UNPARSEABLE_NEEDS_CLARIFICATION",
            "questions": (
                "What exact integer or fraction does your response represent?",
                "Which operation did you apply to both sides?",
            ),
        }
    if observed == variant.answer:
        return {"classification": "CORRECT_NO_REMEDIATION", "questions": ()}
    candidates = tuple(
        code for code, answer in variant.misconception_answers if answer == observed
    )
    strategy_codes = (
        _ADD_STRATEGIES if variant.canonical_skill == ADD_SKILL else _MULT_STRATEGIES
    )
    return {
        "classification": "EVIDENCE_INCOMPLETE_NEEDS_STRATEGY_PROBE",
        "questions": (
            "Which operation did you apply to the complete left side and the complete right side?",
            "Substitute your result: what value does each side become?",
        ),
        "candidate_count": len(candidates),
        "response_fields": (
            "strategy_choice",
            "substitution_left",
            "substitution_right",
        ),
        "strategy_choices": tuple(
            {
                "id": _STRATEGY_OPTION[code][0],
                "label": _STRATEGY_OPTION[code][1],
            }
            for code in strategy_codes
        )
        + (
            {
                "id": "OTHER_OR_UNSURE",
                "label": "I used a different strategy or I am not sure.",
            },
        ),
    }


def guided_repair(
    variant: Variant,
    observed_answer: str,
    strategy_choice: str,
    substitution_left: str,
    substitution_right: str,
) -> dict[str, object] | None:
    """Return targeted repair only when three learner evidence fields agree."""

    if variant.mode != "guided":
        return None
    try:
        observed_value = Fraction(observed_answer)
        observed = _fmt(observed_value)
    except (ValueError, ZeroDivisionError):
        return {
            "classification": "UNCLASSIFIED_NO_ANSWER_REVEAL",
            "questions": ("Restate your exact value and the operation used on both sides.",),
        }
    if observed == variant.answer:
        return {"classification": "CORRECT_NO_REMEDIATION", "questions": ()}
    p = dict(variant.parameters)
    try:
        reported_left = Fraction(substitution_left)
        reported_right = Fraction(substitution_right)
    except (ValueError, ZeroDivisionError):
        return {
            "classification": "UNCLASSIFIED_NO_ANSWER_REVEAL",
            "questions": (
                "Substitute your value and report both sides as exact integers or fractions.",
            ),
        }
    expected_left = (
        Fraction(p["coefficient"]) * observed_value + Fraction(p["offset"])
    )
    expected_right = Fraction(p["rhs"])
    if reported_left != expected_left or reported_right != expected_right:
        return {
            "classification": "UNCLASSIFIED_NO_ANSWER_REVEAL",
            "questions": (
                "Recalculate the complete left and right sides after substitution.",
                "Keep each signed fraction exact before comparing them.",
            ),
        }
    candidates = tuple(
        code for code, answer in variant.misconception_answers
        if answer == observed and _STRATEGY_OPTION[code][0] == strategy_choice
    )
    if len(candidates) != 1:
        return {
            "classification": "UNCLASSIFIED_NO_ANSWER_REVEAL",
            "questions": (
                "Show the same operation on both complete sides.",
                "Then substitute your value before deciding what to revise.",
            ),
        }
    code = candidates[0]
    q1, q2, move, explanation = _REPAIR[code]
    return {
        "classification": code,
        "questions": (q1, q2),
        "representation_move": move,
        "guided_explanation": explanation,
        "fresh_exit_family": TRANSFER_PARTNER[variant.family],
    }


def source_seed(variant: Variant) -> int:
    return int(variant.variant_id.rsplit(":", 1)[-1])


def generate_transfer(
    source: Variant, *, seed_offset: int = TRANSFER_SEED_OFFSET
) -> Variant:
    """Generate a different-structure, unhinted independent transfer item."""

    if source.mode not in {"diagnostic", "guided"}:
        raise ValueError("transfer source must be diagnostic or guided")
    if source_seed(source) >= PRIMARY_SEED_COUNT:
        raise ValueError("transfer source must come from the primary reviewed seed band")
    if seed_offset != TRANSFER_SEED_OFFSET:
        raise ValueError("transfer seed offset is fixed by the reviewed contract")
    return generate(
        TRANSFER_PARTNER[source.family], source_seed(source) + seed_offset, "independent"
    )


