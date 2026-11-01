"""Draft-only Grade 8 distributive-expression depth.

This sidecar reuses the existing ``MATH.EE.EXPR`` canonical identity.  It is
deliberately outside the application import graph and owns no persistence,
selection, scoring, mapping, mastery, or runtime authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Final

STATUS: Final = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION: Final = False
NAMESPACE: Final = "canonical-grade8:distributive-expressions-depth-r1"
CANONICAL_SKILL: Final = "MATH.EE.EXPR"
LOCAL_CANDIDATES: Final = (
    "M8.ALG.DIST",
    "M8.ALG.DIST.POS",
    "M8.ALG.DIST.NEG",
)
MODES: Final = ("diagnostic", "guided", "independent", "mastery")
PRIMARY_SEEDS: Final = tuple(range(32))
TRANSFER_SEED_OFFSET: Final = 1_000_003
TRANSFER_SEEDS: Final = tuple(
    TRANSFER_SEED_OFFSET + seed for seed in PRIMARY_SEEDS
)

FAMILIES: Final = (
    "DIST.POSITIVE.SUM.AREA",
    "DIST.POSITIVE.DIFFERENCE.TAPE",
    "DIST.NEGATIVE.SUM.SIGN",
    "DIST.NEGATIVE.DIFFERENCE.OPPOSITE",
    "DIST.RATIONAL.FACTOR.EXACT",
    "DIST.THEN.COMBINE.LIKE_TERMS",
    "DIST.REVERSE.GCF.FACTOR",
    "DIST.EQUIVALENCE.DECISION",
    "DIST.COUNTEREXAMPLE.NON_EQUIVALENCE",
    "DIST.ERROR.FIRST_INVALID_STEP",
    "DIST.MISSING.TERM.COMPLETION",
    "DIST.CONTEXT.RECTANGLE.PERIMETER",
)

TRANSFER_PARTNER: Final = MappingProxyType(
    {
        FAMILIES[0]: FAMILIES[6],
        FAMILIES[1]: FAMILIES[7],
        FAMILIES[2]: FAMILIES[8],
        FAMILIES[3]: FAMILIES[9],
        FAMILIES[4]: FAMILIES[10],
        FAMILIES[5]: FAMILIES[11],
        FAMILIES[6]: FAMILIES[0],
        FAMILIES[7]: FAMILIES[1],
        FAMILIES[8]: FAMILIES[2],
        FAMILIES[9]: FAMILIES[3],
        FAMILIES[10]: FAMILIES[4],
        FAMILIES[11]: FAMILIES[5],
    }
)

ACCESSIBILITY_CONTRACT: Final = MappingProxyType(
    {
        "keyboard": "All choices and exact-value fields are keyboard operable; no dragging is required.",
        "screen_reader": "Read the outside factor, grouped expression, operation, and resulting terms in mathematical order.",
        "non_color": "Area and tape regions use text labels and boundaries in addition to colour.",
        "reduced_motion": "Show before and after expressions simultaneously instead of animating tiles.",
        "exact_input": "Accept signed integers and equivalent exact fractions without decimal approximation.",
        "focus": "After a rewrite, move focus to the complete resulting expression and its live summary.",
    }
)

FAMILY_METADATA: Final = MappingProxyType(
    {
        FAMILIES[0]: (
            "positive distribution over a sum",
            "connect area decomposition to two products",
            "AFFINE_PAIR",
        ),
        FAMILIES[1]: (
            "positive distribution over a difference",
            "preserve subtraction while scaling both terms",
            "AFFINE_PAIR",
        ),
        FAMILIES[2]: (
            "signed multiplication",
            "track a negative factor across both terms",
            "AFFINE_PAIR",
        ),
        FAMILIES[3]: (
            "opposites and subtraction",
            "interpret a leading minus as multiplication by negative one",
            "AFFINE_PAIR",
        ),
        FAMILIES[4]: (
            "exact rational multiplication",
            "distribute a rational factor without decimal approximation",
            "AFFINE_PAIR",
        ),
        FAMILIES[5]: (
            "distribution and like terms",
            "sequence expansion before combining only like terms",
            "AFFINE_PAIR",
        ),
        FAMILIES[6]: (
            "common factors",
            "reverse distribution using the greatest positive integer factor",
            "FACTOR_FORM",
        ),
        FAMILIES[7]: (
            "equivalent expressions",
            "justify equivalence from structure rather than appearance",
            "EQUIVALENCE_DECISION",
        ),
        FAMILIES[8]: (
            "counterexamples",
            "disprove a false rewrite with an exact witness",
            "COUNTEREXAMPLE",
        ),
        FAMILIES[9]: (
            "error analysis",
            "locate the first invalid distributive step and repair it",
            "ERROR_STEP",
        ),
        FAMILIES[10]: (
            "missing-term reasoning",
            "complete an equivalent expression from coefficient structure",
            "MISSING_TERM",
        ),
        FAMILIES[11]: (
            "perimeter modeling",
            "write and normalize an expression from a rectangle context",
            "AFFINE_PAIR",
        ),
    }
)

REPAIRS: Final = MappingProxyType(
    {
        "DIST_001": (
            "Which terms are inside the group multiplied by the outside factor?",
            "Where should a second product appear in your expanded expression?",
            "Split one labelled rectangle into two regions sharing the outside side length.",
            "The outside factor multiplies every term in the group, not only the first term.",
        ),
        "DIST_002": (
            "What sign belongs to the second term before multiplication?",
            "What is the product of the outside factor and that signed term?",
            "Attach a sign label to each partial product before combining anything.",
            "Distributing scales each signed term; the sign is part of the term being multiplied.",
        ),
        "DIST_003": (
            "Does the outside factor multiply, or is it an addend?",
            "How could an area or equal-group model distinguish those operations?",
            "Show repeated equal groups instead of appending a loose counter.",
            "A factor creates products with the grouped terms; adding it changes the expression differently.",
        ),
        "DIST_004": (
            "Which terms have identical variable parts after expansion?",
            "Can a constant combine with an x-term without changing its meaning?",
            "Sort x-tiles and unit tiles into separate labelled collections.",
            "Only like terms combine: coefficients of x combine with coefficients of x, while constants stay separate.",
        ),
        "DIST_005": (
            "What common factor divides every coefficient?",
            "Is your factor the greatest positive common factor requested by the task?",
            "Arrange all terms into the largest number of identical groups.",
            "Reverse distribution is exact when the outside factor multiplies every inside coefficient back to the original expression.",
        ),
        "DIST_006": (
            "Does one matching input prove two expressions agree for every input?",
            "How do the x-coefficients and constants compare after normalization?",
            "Use a two-column table with more than one input, then compare the affine structures.",
            "Equivalent affine expressions have the same x-coefficient and constant, not merely one coincidental value.",
        ),
        "DIST_007": (
            "Which exact input makes the two claimed forms produce different values?",
            "Have you evaluated both complete expressions at that same input?",
            "Place both evaluations on parallel number lines with the same scale.",
            "A single exact counterexample is sufficient to disprove an all-input equivalence claim.",
        ),
        "DIST_008": (
            "At which numbered step did a factor first fail to reach a grouped term?",
            "What complete affine expression should replace that step?",
            "Trace one arrow from the outside factor to each grouped term.",
            "The first invalid step is where distribution stops being applied to every signed term.",
        ),
        "DIST_009": (
            "Which product determines the missing constant term?",
            "What sign must that product have?",
            "Cover the missing region in an area model and compute its signed area.",
            "The missing term is the exact product of the outside factor and the grouped constant.",
        ),
        "DIST_010": (
            "How many copies of the variable side and fixed side occur in the perimeter?",
            "Which terms represent lengths, and which operation combines all four sides?",
            "Label all four rectangle sides before grouping equal lengths.",
            "Perimeter adds two lengths and two widths; distribution and like terms normalize that sum.",
        ),
    }
)


def _fmt(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _affine_text(x_coefficient: Fraction, constant: Fraction) -> str:
    if x_coefficient == 0:
        return _fmt(constant)
    if x_coefficient == 1:
        variable = "x"
    elif x_coefficient == -1:
        variable = "-x"
    else:
        variable = f"{_fmt(x_coefficient)}x"
    if constant == 0:
        return variable
    sign = "+" if constant > 0 else "-"
    return f"{variable} {sign} {_fmt(abs(constant))}"


def _fraction(value: Any) -> Fraction:
    if isinstance(value, bool):
        raise TypeError("boolean is not an exact number")
    return Fraction(str(value).strip())


def _seed_position(seed: int) -> tuple[int, int]:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed in PRIMARY_SEEDS:
        return 0, seed
    if seed in TRANSFER_SEEDS:
        return 1, seed - TRANSFER_SEED_OFFSET
    raise ValueError("seed must be in a reviewed primary or transfer band")


def _parameters(mode: str, seed: int) -> tuple[int, int, int, int]:
    band, slot = _seed_position(seed)
    if mode not in MODES:
        raise ValueError(f"unsupported mode: {mode}")
    mode_index = MODES.index(mode)
    index = mode_index * 64 + band * 32 + slot
    factor = 2 + slot % 8
    magnitude = 1 + slot // 8 + 4 * band + 8 * mode_index
    signed_term = magnitude * (1 if (mode_index + band) % 2 == 0 else -1)
    offset = 1 + mode_index + 4 * band
    return index, factor, signed_term, offset


def _normalized_response(response: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    normalized: list[tuple[str, Any]] = []
    for key, value in sorted(response.items()):
        if isinstance(value, bool):
            normalized.append((key, value))
        elif key in {"first_invalid_step", "reasoning_choice"}:
            normalized.append((key, str(value)))
        else:
            try:
                normalized.append((key, _fraction(value)))
            except (ValueError, ZeroDivisionError):
                normalized.append((key, str(value).strip()))
    return tuple(normalized)


def _response_matches(
    response: dict[str, Any],
    expected: dict[str, Any] | tuple[tuple[str, Any], ...],
) -> bool:
    """Compare exact responses while preserving Boolean versus numeric domains."""

    expected_fields = dict(expected)
    if set(response) != set(expected_fields):
        return False
    for key, value in response.items():
        expected_value = expected_fields[key]
        if isinstance(expected_value, bool):
            if type(value) is not bool:
                return False
        elif isinstance(value, bool):
            return False
    return _normalized_response(response) == _normalized_response(expected_fields)


@dataclass(frozen=True)
class Variant:
    variant_id: str
    family_code: str
    structure_code: str
    mode: str
    seed: int
    prompt: str
    response_kind: str
    response_fields: tuple[str, ...]
    oracle_response: tuple[tuple[str, Any], ...]
    affine_oracle: tuple[Fraction, Fraction]
    prerequisites: tuple[str, ...]
    difficulty_rationale: str
    answer_boundary: str
    representation_sequence: tuple[str, str, str]
    misconception_signals: tuple[dict[str, Any], ...]
    task_fingerprint: str

    def response_is_correct(self, response: dict[str, Any]) -> bool:
        try:
            return _response_matches(response, self.oracle_response)
        except (TypeError, ValueError, ZeroDivisionError):
            return False

    def public_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "variant_id": self.variant_id,
            "canonical_skill": CANONICAL_SKILL,
            "family_code": self.family_code,
            "structure_code": self.structure_code,
            "mode": self.mode,
            "prompt": self.prompt,
            "response_kind": self.response_kind,
            "response_fields": list(self.response_fields),
            "accessibility": dict(ACCESSIBILITY_CONTRACT),
            "runtime_activation": False,
            "mastery_credit": False,
        }
        if self.mode == "guided":
            payload["learning_sequence"] = [
                "OBSERVE",
                "PREDICT",
                "MANIPULATE",
                "EXPLAIN",
                "PRACTICE",
                "DIAGNOSE",
                "TRANSFER",
                "VERIFY",
            ]
            payload["representation_sequence"] = list(self.representation_sequence)
            payload["diagnosis_requires"] = [
                "observed_response",
                "reasoning_choice",
            ]
        else:
            payload["support"] = "NONE_UNHINTED"
        return payload

    def teacher_oracle(self) -> dict[str, Any]:
        return {
            "response": dict(self.oracle_response),
            "affine_coefficients": [
                _fmt(self.affine_oracle[0]),
                _fmt(self.affine_oracle[1]),
            ],
            "answer_boundary": self.answer_boundary,
        }

    def guided_repair(
        self, observed_response: dict[str, Any], reasoning_choice: str
    ) -> dict[str, Any]:
        if self.mode != "guided":
            return {"status": "SUPPORT_NOT_AVAILABLE"}
        response_matched = False
        for signal in self.misconception_signals:
            if not _response_matches(
                observed_response, signal["candidate_response"]
            ):
                continue
            response_matched = True
            if reasoning_choice != signal["reasoning_choice"]:
                # More than one misconception can produce the same numerical
                # response, so inspect every matching two-probe route before
                # deciding that the evidence is not corroborated.
                continue
            q1, q2, move, explanation = REPAIRS[signal["code"]]
            return {
                "status": "TARGETED_REPAIR",
                "misconception_code": signal["code"],
                "questions": [q1, q2],
                "representation_move": move,
                "explanation": explanation,
                "worked_answer_revealed": False,
                "mastery_credit": False,
            }
        if response_matched:
            return {
                "status": "NEUTRAL_RETRY",
                "reason": "EVIDENCE_NOT_CORROBORATED",
            }
        return {"status": "NEUTRAL_RETRY", "reason": "NO_UNIQUE_MATCH"}


def _signal(
    code: str, candidate_response: dict[str, Any], reasoning_choice: str
) -> dict[str, Any]:
    return {
        "code": code,
        "candidate_response": candidate_response,
        "reasoning_choice": reasoning_choice,
    }


def _affine_variant(
    *,
    family: str,
    structure: str,
    mode: str,
    seed: int,
    prompt: str,
    x_coefficient: Fraction,
    constant: Fraction,
    wrong: tuple[dict[str, Any], ...],
    representations: tuple[str, str, str],
) -> Variant:
    prerequisite, rationale, response_kind = FAMILY_METADATA[family]
    correct = {
        "x_coefficient": _fmt(x_coefficient),
        "constant": _fmt(constant),
    }
    signals = tuple(
        _signal(item["code"], item["response"], item["reasoning_choice"])
        for item in wrong
        if _normalized_response(item["response"]) != _normalized_response(correct)
    )
    if len(signals) < 2:
        raise AssertionError("each family needs two non-colliding misconception routes")
    fingerprint = (
        f"{family}|{structure}|{_fmt(x_coefficient)}|{_fmt(constant)}|{prompt}"
    )
    return Variant(
        variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
        family_code=family,
        structure_code=structure,
        mode=mode,
        seed=seed,
        prompt=prompt,
        response_kind=response_kind,
        response_fields=("x_coefficient", "constant"),
        oracle_response=_normalized_response(correct),
        affine_oracle=(x_coefficient, constant),
        prerequisites=(prerequisite,),
        difficulty_rationale=rationale,
        answer_boundary=(
            "Accept any exact signed integer or equivalent fraction for both affine "
            "coefficients; reject decimal approximations and omitted zero terms."
        ),
        representation_sequence=representations,
        misconception_signals=signals,
        task_fingerprint=fingerprint,
    )


def generate(family: str, seed: int, mode: str) -> Variant:
    """Generate one deterministic original distributive-expression task."""

    if family not in FAMILIES:
        raise ValueError(f"unsupported family: {family}")
    index, a, b, c = _parameters(mode, seed)
    signed_b = Fraction(b)
    factor = Fraction(a)

    if family == FAMILIES[0]:
        x_coeff, constant = factor, factor * abs(signed_b)
        prompt = f"Expand {a}(x + {abs(b)}). Report the x-coefficient and constant."
        return _affine_variant(
            family=family,
            structure="POSITIVE_SUM_AREA_DECOMPOSITION",
            mode=mode,
            seed=seed,
            prompt=prompt,
            x_coefficient=x_coeff,
            constant=constant,
            wrong=(
                {"code": "DIST_001", "response": {"x_coefficient": a, "constant": abs(b)}, "reasoning_choice": "FACTOR_REACHED_FIRST_TERM_ONLY"},
                {"code": "DIST_003", "response": {"x_coefficient": 1, "constant": a + abs(b)}, "reasoning_choice": "OUTSIDE_VALUE_WAS_ADDED"},
            ),
            representations=(
                "Concrete: build one rectangle with side a and split the other side into x and b.",
                "Visual: label the two partial areas ax and ab.",
                "Symbolic: rewrite a(x + b) as ax + ab.",
            ),
        )

    if family == FAMILIES[1]:
        amount = abs(b)
        x_coeff, constant = factor, -factor * amount
        prompt = f"Expand {a}(x - {amount}) exactly."
        return _affine_variant(
            family=family,
            structure="POSITIVE_DIFFERENCE_SIGNED_TAPE",
            mode=mode,
            seed=seed,
            prompt=prompt,
            x_coefficient=x_coeff,
            constant=constant,
            wrong=(
                {"code": "DIST_001", "response": {"x_coefficient": a, "constant": -amount}, "reasoning_choice": "FACTOR_REACHED_FIRST_TERM_ONLY"},
                {"code": "DIST_002", "response": {"x_coefficient": a, "constant": a * amount}, "reasoning_choice": "SUBTRACTION_SIGN_WAS_LOST"},
            ),
            representations=(
                "Concrete: mark a copies of a signed tape x minus b.",
                "Visual: scale both the x segment and the negative b segment by a.",
                "Symbolic: a(x - b) = ax - ab.",
            ),
        )

    if family == FAMILIES[2]:
        outer = -factor
        amount = abs(b)
        x_coeff, constant = outer, outer * amount
        prompt = f"Expand -{a}(x + {amount}) and preserve both signs."
        return _affine_variant(
            family=family,
            structure="NEGATIVE_FACTOR_SUM_SIGN_TRACKING",
            mode=mode,
            seed=seed,
            prompt=prompt,
            x_coefficient=x_coeff,
            constant=constant,
            wrong=(
                {"code": "DIST_001", "response": {"x_coefficient": -a, "constant": amount}, "reasoning_choice": "FACTOR_REACHED_FIRST_TERM_ONLY"},
                {"code": "DIST_002", "response": {"x_coefficient": a, "constant": -a * amount}, "reasoning_choice": "NEGATIVE_FACTOR_REACHED_ONE_TERM"},
            ),
            representations=(
                "Concrete: pair each positive region with its opposite signed region.",
                "Visual: draw a negative-factor arrow to both grouped terms.",
                "Symbolic: -a(x + b) = -ax - ab.",
            ),
        )

    if family == FAMILIES[3]:
        # The primary index makes every mode/seed a genuinely new expression,
        # while the outside factor remains the conceptual bare negative one.
        amount = index + 2
        x_coeff, constant = Fraction(-a), Fraction(amount)
        prompt = f"Rewrite -({a}x - {amount}) as an affine expression."
        return _affine_variant(
            family=family,
            structure="BARE_NEGATIVE_DIFFERENCE_OPPOSITE",
            mode=mode,
            seed=seed,
            prompt=prompt,
            x_coefficient=x_coeff,
            constant=constant,
            wrong=(
                {"code": "DIST_002", "response": {"x_coefficient": -a, "constant": -amount}, "reasoning_choice": "INNER_SIGN_WAS_COPIED"},
                {"code": "DIST_001", "response": {"x_coefficient": -a, "constant": amount - 1}, "reasoning_choice": "NEGATIVE_ONE_WAS_NOT_DISTRIBUTED"},
            ),
            representations=(
                "Concrete: take the opposite of the complete signed tile group.",
                "Visual: show that a leading minus is a factor of negative one.",
                "Symbolic: -1(ax - b) = -ax + b.",
            ),
        )

    if family == FAMILIES[4]:
        denominator = 2 + c
        rational = Fraction(a, denominator)
        x_coeff, constant = rational, rational * signed_b
        prompt = (
            f"Expand ({_fmt(rational)})(x {'+' if b > 0 else '-'} {abs(b)}) "
            "using exact fractions."
        )
        return _affine_variant(
            family=family,
            structure="RATIONAL_FACTOR_EXACT_DISTRIBUTION",
            mode=mode,
            seed=seed,
            prompt=prompt,
            x_coefficient=x_coeff,
            constant=constant,
            wrong=(
                {
                    "code": "DIST_001",
                    "response": {
                        "x_coefficient": rational,
                        "constant": signed_b
                        if signed_b != constant
                        else signed_b + 1,
                    },
                    "reasoning_choice": "FRACTION_REACHED_FIRST_TERM_ONLY",
                },
                {"code": "DIST_003", "response": {"x_coefficient": 1, "constant": rational + b}, "reasoning_choice": "FRACTION_WAS_ADDED"},
            ),
            representations=(
                "Concrete: scale both labelled fraction-strip regions by the same rational factor.",
                "Visual: use a common partition for both partial products.",
                "Symbolic: multiply the rational factor by each signed term exactly.",
            ),
        )

    if family == FAMILIES[5]:
        outer = Fraction(a)
        extra = Fraction(c)
        constant_part = signed_b
        x_coeff = outer + extra
        constant = outer * constant_part + Fraction(c - 2)
        prompt = (
            f"Simplify {a}(x {'+' if b > 0 else '-'} {abs(b)}) + "
            f"{c}x {'+' if c - 2 >= 0 else '-'} {abs(c - 2)}."
        )
        return _affine_variant(
            family=family,
            structure="DISTRIBUTE_THEN_COMBINE_LIKE_TERMS",
            mode=mode,
            seed=seed,
            prompt=prompt,
            x_coefficient=x_coeff,
            constant=constant,
            wrong=(
                {"code": "DIST_004", "response": {"x_coefficient": a + c + b, "constant": c - 2}, "reasoning_choice": "CONSTANT_COMBINED_WITH_X_TERM"},
                {"code": "DIST_001", "response": {"x_coefficient": a + c, "constant": b + c - 2}, "reasoning_choice": "FACTOR_REACHED_FIRST_TERM_ONLY"},
            ),
            representations=(
                "Concrete: sort expanded x-tiles and unit tiles into separate groups.",
                "Visual: use arrows for distribution, then brackets for like terms.",
                "Symbolic: expand before combining x-coefficients and constants separately.",
            ),
        )

    if family == FAMILIES[6]:
        common = 2 + c
        inner_x = a
        # gcd(a, a*k + 1) is always 1, so ``common`` is provably the
        # greatest positive integer factor rather than merely a common one.
        inner_constant = (1 if b > 0 else -1) * (a * (abs(b) + 1) + 1)
        x_coeff = Fraction(common * inner_x)
        constant = Fraction(common * inner_constant)
        correct = {
            "outer_factor": common,
            "inner_x_coefficient": inner_x,
            "inner_constant": inner_constant,
        }
        prerequisite, rationale, response_kind = FAMILY_METADATA[family]
        signals = (
            _signal("DIST_005", {"outer_factor": 1, "inner_x_coefficient": common * inner_x, "inner_constant": common * inner_constant}, "NO_COMMON_FACTOR_TAKEN"),
            _signal("DIST_005", {"outer_factor": common, "inner_x_coefficient": inner_x, "inner_constant": -inner_constant}, "CONSTANT_SIGN_CHANGED_WHILE_FACTORING"),
        )
        return Variant(
            variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
            family_code=family,
            structure_code="REVERSE_DISTRIBUTION_GREATEST_COMMON_FACTOR",
            mode=mode,
            seed=seed,
            prompt=(
                f"Factor {_affine_text(x_coeff, constant)} using the greatest "
                "positive integer common factor."
            ),
            response_kind=response_kind,
            response_fields=tuple(correct),
            oracle_response=_normalized_response(correct),
            affine_oracle=(x_coeff, constant),
            prerequisites=(prerequisite,),
            difficulty_rationale=rationale,
            answer_boundary="Require the greatest positive integer common factor; reject equivalent non-greatest or negative factorizations.",
            representation_sequence=(
                "Concrete: make the largest possible number of identical tile groups.",
                "Visual: outline the common dimension shared by both term rectangles.",
                "Symbolic: divide every coefficient by the positive GCF.",
            ),
            misconception_signals=signals,
            task_fingerprint=f"{family}|{x_coeff}|{constant}|{common}",
        )

    if family == FAMILIES[7]:
        true_claim = index % 2 == 0
        x_coeff = factor
        constant = factor * signed_b
        candidate_constant = constant if true_claim else constant + c
        correct: dict[str, Any] = {
            "equivalent": true_claim,
            "x_coefficient": _fmt(x_coeff),
            "constant": _fmt(candidate_constant),
        }
        prerequisite, rationale, response_kind = FAMILY_METADATA[family]
        prompt = (
            f"Decide whether {a}(x {'+' if b > 0 else '-'} {abs(b)}) and "
            f"{_affine_text(x_coeff, candidate_constant)} are equivalent for every x. "
            "Report the candidate's normalized coefficients."
        )
        signals = (
            _signal("DIST_006", {"equivalent": not true_claim, "x_coefficient": x_coeff, "constant": candidate_constant}, "DECIDED_FROM_APPEARANCE"),
            _signal(
                "DIST_001",
                {
                    "equivalent": False,
                    "x_coefficient": x_coeff,
                    "constant": signed_b
                    if not (not true_claim and signed_b == candidate_constant)
                    else signed_b + 1,
                },
                "FACTOR_REACHED_FIRST_TERM_ONLY",
            ),
        )
        return Variant(
            variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
            family_code=family,
            structure_code="ALL_INPUT_EQUIVALENCE_DECISION",
            mode=mode,
            seed=seed,
            prompt=prompt,
            response_kind=response_kind,
            response_fields=tuple(correct),
            oracle_response=_normalized_response(correct),
            affine_oracle=(x_coeff, candidate_constant),
            prerequisites=(prerequisite,),
            difficulty_rationale=rationale,
            answer_boundary="Equivalence is an all-input claim; normalized affine coefficients must agree exactly.",
            representation_sequence=(
                "Concrete: compare matching tile collections for the two expressions.",
                "Visual: normalize both forms into x-regions and unit regions.",
                "Symbolic: compare exact x-coefficients and constants.",
            ),
            misconception_signals=signals,
            task_fingerprint=f"{family}|{true_claim}|{x_coeff}|{candidate_constant}",
        )

    if family == FAMILIES[8]:
        left_x = factor
        left_constant = factor * signed_b
        right_constant = left_constant + c
        witness = Fraction(c + 1)
        left_value = left_x * witness + left_constant
        right_value = left_x * witness + right_constant
        correct = {
            "witness_input": _fmt(witness),
            "left_value": _fmt(left_value),
            "right_value": _fmt(right_value),
        }
        prerequisite, rationale, response_kind = FAMILY_METADATA[family]
        signals = (
            _signal("DIST_007", {"witness_input": witness, "left_value": left_value, "right_value": left_value}, "EVALUATED_ONLY_ONE_FORM"),
            _signal("DIST_006", {"witness_input": 0, "left_value": 0, "right_value": 0}, "ASSUMED_ONE_MATCH_PROVES_ALL_INPUTS"),
        )
        return Variant(
            variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
            family_code=family,
            structure_code="EXACT_COUNTEREXAMPLE_TO_FALSE_REWRITE",
            mode=mode,
            seed=seed,
            prompt=(
                f"A claim says {a}(x {'+' if b > 0 else '-'} {abs(b)}) equals "
                f"{_affine_text(left_x, right_constant)} for every x. Use x = {_fmt(witness)} "
                "to give both exact values and disprove the claim."
            ),
            response_kind=response_kind,
            response_fields=tuple(correct),
            oracle_response=_normalized_response(correct),
            affine_oracle=(left_x, left_constant),
            prerequisites=(prerequisite,),
            difficulty_rationale=rationale,
            answer_boundary="Use the required witness and evaluate both complete expressions exactly; the values must differ.",
            representation_sequence=(
                "Concrete: build both tile collections at the same assigned x-value.",
                "Visual: compare two same-scale evaluation bars.",
                "Symbolic: substitute one exact witness into both complete expressions.",
            ),
            misconception_signals=signals,
            task_fingerprint=f"{family}|{left_x}|{left_constant}|{right_constant}|{witness}",
        )

    if family == FAMILIES[9]:
        x_coeff = -factor
        constant = -factor * abs(signed_b)
        correct = {
            "first_invalid_step": "STEP_1",
            "x_coefficient": _fmt(x_coeff),
            "constant": _fmt(constant),
        }
        prerequisite, rationale, response_kind = FAMILY_METADATA[family]
        signals = (
            _signal("DIST_008", {"first_invalid_step": "STEP_2", "x_coefficient": -a, "constant": abs(b)}, "MISSED_FIRST_DISTRIBUTION_ERROR"),
            _signal("DIST_002", {"first_invalid_step": "STEP_1", "x_coefficient": -a, "constant": a * abs(b)}, "NEGATIVE_SIGN_WAS_LOST"),
        )
        return Variant(
            variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
            family_code=family,
            structure_code="FIRST_INVALID_DISTRIBUTIVE_STEP",
            mode=mode,
            seed=seed,
            prompt=(
                f"A learner rewrites -{a}(x + {abs(b)}) as -{a}x + {abs(b)} in STEP_1, "
                "then combines signs in STEP_2. Identify the first invalid step and give the corrected affine coefficients."
            ),
            response_kind=response_kind,
            response_fields=tuple(correct),
            oracle_response=_normalized_response(correct),
            affine_oracle=(x_coeff, constant),
            prerequisites=(prerequisite,),
            difficulty_rationale=rationale,
            answer_boundary="Identify the earliest invalid step and provide both exact corrected affine coefficients.",
            representation_sequence=(
                "Concrete: trace the negative group count to each tile type.",
                "Visual: mark the first missing factor arrow, not a later consequence.",
                "Symbolic: repair the earliest invalid equality before simplifying.",
            ),
            misconception_signals=signals,
            task_fingerprint=f"{family}|{x_coeff}|{constant}|STEP_1",
        )

    if family == FAMILIES[10]:
        constant = factor * signed_b
        correct = {
            "missing_constant": _fmt(constant),
            "x_coefficient": _fmt(factor),
        }
        prerequisite, rationale, response_kind = FAMILY_METADATA[family]
        signals = (
            _signal("DIST_009", {"missing_constant": b, "x_coefficient": factor}, "GROUPED_CONSTANT_WAS_COPIED"),
            _signal("DIST_002", {"missing_constant": -constant, "x_coefficient": factor}, "MISSING_TERM_SIGN_WAS_IGNORED"),
        )
        return Variant(
            variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
            family_code=family,
            structure_code="MISSING_DISTRIBUTED_TERM_COMPLETION",
            mode=mode,
            seed=seed,
            prompt=(
                f"Complete {a}(x {'+' if b > 0 else '-'} {abs(b)}) = {a}x + __. "
                "Give the missing constant and the x-coefficient."
            ),
            response_kind=response_kind,
            response_fields=tuple(correct),
            oracle_response=_normalized_response(correct),
            affine_oracle=(factor, constant),
            prerequisites=(prerequisite,),
            difficulty_rationale=rationale,
            answer_boundary="The missing term must be the exact signed product of the outside factor and grouped constant.",
            representation_sequence=(
                "Concrete: cover the unknown partial area while keeping its side labels visible.",
                "Visual: follow the second distribution arrow to the missing region.",
                "Symbolic: multiply the outside factor by the signed constant.",
            ),
            misconception_signals=signals,
            task_fingerprint=f"{family}|{factor}|{signed_b}|{constant}",
        )

    length_offset = abs(b)
    width = Fraction(index + 2) + Fraction(c, 10)
    x_coeff = Fraction(2)
    constant = Fraction(2 * length_offset) + 2 * width
    prompt = (
        f"A rectangle has length x + {length_offset} units and width {_fmt(width)} units. "
        "Write its perimeter as a normalized affine expression."
    )
    return _affine_variant(
        family=family,
        structure="RECTANGLE_PERIMETER_DISTRIBUTIVE_MODEL",
        mode=mode,
        seed=seed,
        prompt=prompt,
        x_coefficient=x_coeff,
        constant=constant,
        wrong=(
            {"code": "DIST_010", "response": {"x_coefficient": 1, "constant": length_offset + width}, "reasoning_choice": "COUNTED_ONE_LENGTH_AND_ONE_WIDTH"},
            {"code": "DIST_001", "response": {"x_coefficient": 2, "constant": length_offset + 2 * width}, "reasoning_choice": "FACTOR_REACHED_VARIABLE_TERM_ONLY"},
        ),
        representations=(
            "Concrete: label all four rectangle sides with matching length and width cards.",
            "Visual: group two lengths and two widths before distributing the factor two.",
            "Symbolic: P = 2(x + b) + 2w, then normalize like terms.",
        ),
    )


def create_unhinted_transfer(source: Variant) -> Variant:
    if source.mode not in {"guided", "diagnostic"}:
        raise ValueError("transfer source must be guided or diagnostic")
    if source.seed not in PRIMARY_SEEDS:
        raise ValueError("transfer source must use a primary seed")
    target = generate(
        TRANSFER_PARTNER[source.family_code],
        source.seed + TRANSFER_SEED_OFFSET,
        "independent",
    )
    if target.family_code == source.family_code:
        raise AssertionError("transfer must change family")
    if target.structure_code == source.structure_code:
        raise AssertionError("transfer must change structure")
    if target.task_fingerprint == source.task_fingerprint:
        raise AssertionError("transfer must be a fresh mathematical task")
    return target


def create_pack() -> dict[str, Any]:
    variants = [
        generate(family, seed, mode)
        for family in FAMILIES
        for mode in MODES
        for seed in PRIMARY_SEEDS
    ]
    return {
        "namespace": NAMESPACE,
        "status": STATUS,
        "runtime_activation": RUNTIME_ACTIVATION,
        "canonical_skill": CANONICAL_SKILL,
        "local_mapping_activation": False,
        "family_count": len(FAMILIES),
        "variant_ids": [variant.variant_id for variant in variants],
        "task_fingerprints": [variant.task_fingerprint for variant in variants],
        "learner_history_writes": False,
        "attempt_writes": False,
        "mastery_writes": False,
    }


def normalized_affine_value(variant: Variant, x: Fraction) -> Fraction:
    return variant.affine_oracle[0] * x + variant.affine_oracle[1]


def greatest_positive_common_factor(variant: Variant) -> int:
    a, b = variant.affine_oracle
    if a.denominator != 1 or b.denominator != 1:
        raise ValueError("integer coefficients required")
    return math.gcd(abs(a.numerator), abs(b.numerator))
