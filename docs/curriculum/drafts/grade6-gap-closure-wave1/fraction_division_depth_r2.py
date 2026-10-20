"""Draft-only deterministic Grade 6 fraction-division reasoning variants.

This module deliberately lives outside ``app`` and every seed entry point.  It
is author evidence for independent review, not a learner route or a mastery
scorer.  Exact answers and diagnostic signatures are available only through
``teacher_oracle``; ``public_payload`` never returns them.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from math import lcm

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
NAMESPACE = "grade6-gap-closure-wave1:fraction-division-depth-r2"
MODES = ("diagnostic", "guided", "independent", "mastery")
FAMILIES = (
    "MEASUREMENT_GROUPS",
    "FAIR_SHARE",
    "NUMBER_LINE_PARTIAL_JUMPS",
    "COMMON_DENOMINATOR_COUNTS",
    "MISSING_FACTOR",
    "RECIPE_BATCHES",
    "RECIPROCAL_ERROR_ANALYSIS",
    "DIMENSIONAL_TRANSFER",
)
_MODE_OFFSETS = {"diagnostic": 0, "guided": 1, "independent": 3, "mastery": 5}

MISCONCEPTION_SUPPORT = {
    "MULTIPLY_INSTEAD_OF_DIVIDE": {
        "socratic_question": "What missing-factor equation must your quotient satisfy when it is multiplied by the divisor?",
        "representation_move": "Build divisor-sized groups inside the dividend, then compare the group count with the product you wrote.",
    },
    "REVERSE_DIVISION_ORDER": {
        "socratic_question": "Which quantity is being split or measured, and which quantity names one group?",
        "representation_move": "Label the dividend as the total and the divisor as one group before drawing any groups.",
    },
    "MULTIPLY_TOTAL_BY_SHARES": {
        "socratic_question": "If the total is shared among the containers, should one share be greater than the whole total?",
        "representation_move": "Partition one bar for the total into the stated number of equal container regions.",
    },
    "DROP_PARTIAL_GROUP": {
        "socratic_question": "Where is the remaining distance after the last full jump, and what fraction of one jump does it represent?",
        "representation_move": "Mark the leftover segment and compare its length with one complete divisor-sized jump.",
    },
    "ADD_COMMON_UNIT_COUNTS": {
        "socratic_question": "Once both quantities use the same-size pieces, do you add their counts or ask how many divisor counts fit in the dividend count?",
        "representation_move": "Align the two common-unit bars and group the dividend pieces in sets equal to the divisor-piece count.",
    },
    "REVERSE_COMMON_UNIT_COUNTS": {
        "socratic_question": "Which common-unit count belongs first when you ask how many divisor-sized sets fit inside the dividend?",
        "representation_move": "Label the dividend-piece count as the amount being measured and the divisor-piece count as one set.",
    },
    "ADD_FACTOR_INSTEAD_OF_DIVIDE": {
        "socratic_question": "What inverse operation undoes multiplying q by the known factor while keeping the equation balanced?",
        "representation_move": "Divide both sides of the balance by the known factor and keep each side visible.",
    },
    "REVERSE_RATE_DIRECTION": {
        "socratic_question": "Which quantity is available in total, and which quantity is used for exactly one batch?",
        "representation_move": "Label a double number line with total cups on one side and batches on the other before forming the quotient.",
    },
    "MULTIPLY_AVAILABLE_BY_RATE": {
        "socratic_question": "What equation must the batch count satisfy when it is multiplied by the cups used per batch?",
        "representation_move": "Make equal per-batch groups from the available cups and count the groups.",
    },
    "RECIPROCATE_DIVIDEND": {
        "socratic_question": "In the related missing-factor equation, which factor must be undone to isolate the quotient?",
        "representation_move": "Write quotient times divisor equals dividend, then mark the factor being undone.",
    },
    "MULTIPLY_WITHOUT_RECIPROCAL": {
        "socratic_question": "What number multiplied by the divisor equals one, so division can be rewritten as multiplication?",
        "representation_move": "Pair the divisor with its multiplicative inverse before multiplying by the dividend.",
    },
    "MULTIPLY_AREA_BY_WIDTH": {
        "socratic_question": "If area equals length times width, which operation isolates the missing length?",
        "representation_move": "Label the rectangle area and width, leave length unknown, and write their multiplication relationship.",
    },
    "KEEP_SQUARE_UNIT_AFTER_DIVISION": {
        "socratic_question": "How do the metre units simplify in square metres divided by metres?",
        "representation_move": "Write square metres as metre times metre and cancel the width unit explicitly.",
    },
}

_UNCLASSIFIED_SUPPORT = {
    "misconception_code": "UNCLASSIFIED_WRONG_ANSWER",
    "socratic_question": "Which multiplication check would show whether your quotient reconstructs the original dividend?",
    "representation_move": "Return to the model, label the total and one group, and compare the represented groups with your quotient.",
}


def _text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _proper(rng: random.Random) -> Fraction:
    denominator = rng.choice((2, 3, 4, 5, 6, 8))
    return Fraction(rng.randint(1, denominator - 1), denominator)


def _non_unit_fraction(rng: random.Random) -> Fraction:
    value = _proper(rng)
    while value == 1:
        value = _proper(rng)
    return value


@dataclass(frozen=True)
class FractionDivisionVariant:
    variant_id: str
    seed: int
    mode: str
    family: str
    prompt: str
    dividend: Fraction
    divisor: Fraction
    quotient: Fraction
    quotient_unit: str
    representation_prompt: str
    explanation_code: str
    misconceptions: tuple[tuple[str, Fraction], ...]

    def public_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "family": self.family,
            "prompt": self.prompt,
            "representation_prompt": self.representation_prompt,
            "response_fields": [
                "estimate_and_size_relation",
                "model_or_equation",
                "exact_quotient",
                "quotient_unit_or_interpretation",
                "multiplication_check",
                "explanation",
            ],
            "interaction_contract": {
                "keyboard": "Move among partition marks, groups, and response fields without drag.",
                "screen_reader": "Announce the dividend, divisor, current partition count, selected groups, and response-field errors in reading order.",
                "reduced_motion": "Use discrete partition and group states; animation is optional and suppressible.",
                "focus_recovery": "Return focus to the first inconsistent response field after feedback.",
                "color_independence": "Every group and remainder has a text label or pattern in addition to color.",
            },
        }
        if self.mode == "guided":
            payload["socratic_support_contract"] = {
                "trigger": "AFTER_EXACT_QUOTIENT_SUBMISSION",
                "selection": "MATCH_OBSERVED_ANSWER_TO_MISCONCEPTION_PATHWAY",
                "ambiguous_match": "RETURN_EACH_SUPPORTED_HYPOTHESIS_WITHOUT_CHOOSING_FOR_THE_LEARNER",
                "fallback": "UNCLASSIFIED_WRONG_ANSWER",
                "answer_reveal": False,
            }
        return payload

    def guided_support_for_answer(
        self, learner_answer: Fraction | int | str
    ) -> dict[str, object] | None:
        """Return answer-free, observed-error support only for guided variants.

        One numeric response can be consistent with more than one misconception.
        In that case every plausible pathway is returned rather than inventing a
        diagnosis.  Non-guided modes have no remediation surface.
        """

        if self.mode != "guided":
            return None
        answer = _parse_exact_answer(learner_answer)
        if answer == self.quotient:
            return {
                "status": "CORRECT_NO_REMEDIATION",
                "observed_answer": _text(answer),
                "pathways": [],
                "answer_reveal": False,
            }
        matched_codes = tuple(code for code, wrong in self.misconceptions if wrong == answer)
        if not matched_codes:
            pathways = [dict(_UNCLASSIFIED_SUPPORT)]
            status = "UNCLASSIFIED_WRONG_ANSWER"
        else:
            pathways = [
                {"misconception_code": code, **MISCONCEPTION_SUPPORT[code]}
                for code in matched_codes
            ]
            status = "MATCHED_MISCONCEPTION" if len(pathways) == 1 else "AMBIGUOUS_MATCH"
        return {
            "status": status,
            "observed_answer": _text(answer),
            "pathways": pathways,
            "answer_reveal": False,
            "focus_target": "model_or_equation",
            "screen_reader_announcement": (
                "Your response does not reconstruct the original quantity. "
                "Review the question and representation move."
            ),
        }

    def teacher_oracle(self) -> dict[str, object]:
        if self.divisor < 1:
            size_relation = "QUOTIENT_GREATER_THAN_DIVIDEND"
        elif self.divisor > 1:
            size_relation = "QUOTIENT_LESS_THAN_DIVIDEND"
        else:
            size_relation = "QUOTIENT_EQUALS_DIVIDEND"
        return {
            "dividend": _text(self.dividend),
            "divisor": _text(self.divisor),
            "exact_quotient": _text(self.quotient),
            "quotient_unit": self.quotient_unit,
            "reciprocal_product": {
                "left_factor": _text(self.dividend),
                "right_factor": _text(Fraction(self.divisor.denominator, self.divisor.numerator)),
                "result": _text(self.quotient),
            },
            "multiplication_check": {
                "quotient": _text(self.quotient),
                "divisor": _text(self.divisor),
                "reconstructed_dividend": _text(self.quotient * self.divisor),
            },
            "size_relation": size_relation,
            "explanation_code": self.explanation_code,
            "misconception_answers": {code: _text(answer) for code, answer in self.misconceptions},
        }


def _validate(seed: int, mode: str, family: str | None) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if mode not in MODES:
        raise ValueError(f"unsupported mode: {mode!r}")
    if family is not None and family not in FAMILIES:
        raise ValueError(f"unsupported family: {family!r}")


def _parse_exact_answer(value: Fraction | int | str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (Fraction, int, str)):
        raise TypeError("learner answer must be an exact Fraction, integer, or fraction string")
    if isinstance(value, str) and not value.strip():
        raise ValueError("learner answer cannot be blank")
    try:
        return Fraction(value.strip() if isinstance(value, str) else value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("learner answer must be an exact integer or fraction") from error


def _family(seed: int, mode: str) -> str:
    return FAMILIES[(seed + _MODE_OFFSETS[mode]) % len(FAMILIES)]


def _variant(
    *,
    seed: int,
    mode: str,
    family: str,
    prompt: str,
    dividend: Fraction,
    divisor: Fraction,
    quotient_unit: str,
    representation_prompt: str,
    explanation_code: str,
    misconceptions: dict[str, Fraction],
) -> FractionDivisionVariant:
    quotient = dividend / divisor
    clean = tuple(
        sorted((code, answer) for code, answer in misconceptions.items() if answer != quotient)
    )
    if len(clean) != len(misconceptions):
        raise AssertionError("misconception answer collided with exact quotient")
    unknown_codes = {code for code, _answer in clean} - MISCONCEPTION_SUPPORT.keys()
    if unknown_codes:
        raise AssertionError(
            f"missing Socratic support for misconception codes: {sorted(unknown_codes)}"
        )
    return FractionDivisionVariant(
        variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
        seed=seed,
        mode=mode,
        family=family,
        prompt=prompt,
        dividend=dividend,
        divisor=divisor,
        quotient=quotient,
        quotient_unit=quotient_unit,
        representation_prompt=representation_prompt,
        explanation_code=explanation_code,
        misconceptions=clean,
    )


def generate(seed: int, mode: str, family: str | None = None) -> FractionDivisionVariant:
    """Generate one exact, replayable variant.

    Selecting by ``seed`` and ``mode`` deliberately changes family between modes
    for the same seed.  Passing ``family`` is an author/reviewer aid and does not
    grant that family any runtime or mastery eligibility.
    """

    _validate(seed, mode, family)
    selected = family or _family(seed, mode)
    rng = random.Random(f"{NAMESPACE}:{mode}:{selected}:{seed}")

    if selected == "MEASUREMENT_GROUPS":
        divisor = _non_unit_fraction(rng)
        groups = Fraction(rng.randint(2, 9))
        dividend = divisor * groups
        return _variant(
            seed=seed,
            mode=mode,
            family=selected,
            prompt=(
                f"A roll has {_text(dividend)} m of ribbon. Each equal piece is "
                f"{_text(divisor)} m. How many complete pieces can be measured? "
                "Model the groups and verify by multiplication."
            ),
            dividend=dividend,
            divisor=divisor,
            quotient_unit="pieces",
            representation_prompt="Partition a bar for the total ribbon into divisor-sized groups; label every group boundary.",
            explanation_code="MEASUREMENT_DIVISION_COUNTS_GROUPS",
            misconceptions={
                "MULTIPLY_INSTEAD_OF_DIVIDE": dividend * divisor,
                "REVERSE_DIVISION_ORDER": divisor / dividend,
            },
        )

    if selected == "FAIR_SHARE":
        containers = Fraction(rng.randint(2, 6))
        share = _proper(rng)
        dividend = containers * share
        return _variant(
            seed=seed,
            mode=mode,
            family=selected,
            prompt=(
                f"Share {_text(dividend)} L equally among {_text(containers)} containers. "
                "How many litres are in each container? Show equal shares and check the total."
            ),
            dividend=dividend,
            divisor=containers,
            quotient_unit="litres per container",
            representation_prompt="Split one total-volume bar into the stated number of equal container regions.",
            explanation_code="PARTITIVE_DIVISION_FINDS_ONE_SHARE",
            misconceptions={
                "MULTIPLY_TOTAL_BY_SHARES": dividend * containers,
                "REVERSE_DIVISION_ORDER": containers / dividend,
            },
        )

    if selected == "NUMBER_LINE_PARTIAL_JUMPS":
        divisor = _proper(rng)
        jumps = Fraction(rng.choice((3, 5, 7, 9)), 2)
        dividend = divisor * jumps
        return _variant(
            seed=seed,
            mode=mode,
            family=selected,
            prompt=(
                f"Starting at 0, how many jumps of length {_text(divisor)} reach "
                f"{_text(dividend)}? Include the final partial jump and explain its fraction of a full jump."
            ),
            dividend=dividend,
            divisor=divisor,
            quotient_unit="jumps",
            representation_prompt="Mark equal divisor-length jumps on a number line and represent the terminal half-jump explicitly.",
            explanation_code="FRACTIONAL_QUOTIENT_COUNTS_PARTIAL_GROUP",
            misconceptions={
                "DROP_PARTIAL_GROUP": Fraction(jumps.numerator // jumps.denominator),
                "MULTIPLY_INSTEAD_OF_DIVIDE": dividend * divisor,
            },
        )

    if selected == "COMMON_DENOMINATOR_COUNTS":
        divisor = _proper(rng)
        quotient = rng.choice(
            (Fraction(3, 2), Fraction(2), Fraction(5, 2), Fraction(3), Fraction(7, 2))
        )
        dividend = divisor * quotient
        common = lcm(dividend.denominator, divisor.denominator)
        dividend_units = dividend.numerator * (common // dividend.denominator)
        divisor_units = divisor.numerator * (common // divisor.denominator)
        return _variant(
            seed=seed,
            mode=mode,
            family=selected,
            prompt=(
                f"Rewrite {_text(dividend)} ÷ {_text(divisor)} using pieces of size 1/{common}. "
                "Compare the two piece counts, find the quotient, and connect the count ratio to reciprocal multiplication."
            ),
            dividend=dividend,
            divisor=divisor,
            quotient_unit="groups",
            representation_prompt=f"Use two aligned bars partitioned into {common} equal pieces; do not prefill either piece count.",
            explanation_code="COMMON_UNIT_COUNTS_FORM_A_RATIO",
            misconceptions={
                "ADD_COMMON_UNIT_COUNTS": Fraction(dividend_units + divisor_units, divisor_units),
                "REVERSE_COMMON_UNIT_COUNTS": Fraction(divisor_units, dividend_units),
            },
        )

    if selected == "MISSING_FACTOR":
        denominator = rng.choice((2, 3, 4))
        divisor = Fraction(rng.randint(denominator + 1, denominator + 5), denominator)
        quotient = _proper(rng) + rng.randint(1, 3)
        dividend = divisor * quotient
        return _variant(
            seed=seed,
            mode=mode,
            family=selected,
            prompt=(
                f"Find q in q × {_text(divisor)} = {_text(dividend)}. "
                "Use the equation to explain why division isolates q, then substitute to verify both sides."
            ),
            dividend=dividend,
            divisor=divisor,
            quotient_unit="dimensionless factor",
            representation_prompt="Use a balance or missing-factor rectangle; preserve equality while undoing multiplication.",
            explanation_code="DIVISION_IS_INVERSE_OF_MULTIPLICATION",
            misconceptions={
                "ADD_FACTOR_INSTEAD_OF_DIVIDE": dividend + divisor,
                "REVERSE_DIVISION_ORDER": divisor / dividend,
            },
        )

    if selected == "RECIPE_BATCHES":
        per_batch = _proper(rng) + Fraction(rng.choice((0, 1)))
        batches = Fraction(rng.randint(2, 7))
        available = per_batch * batches
        return _variant(
            seed=seed,
            mode=mode,
            family=selected,
            prompt=(
                f"One batch uses {_text(per_batch)} cup of oats. With {_text(available)} cups, "
                "how many batches can be made? State which quantity is per batch and check the total oats."
            ),
            dividend=available,
            divisor=per_batch,
            quotient_unit="batches",
            representation_prompt="Build a double number line pairing batches with cups; leave the final batch count unknown.",
            explanation_code="UNIT_RATE_DIRECTION_AVAILABLE_DIVIDED_BY_PER_BATCH",
            misconceptions={
                "REVERSE_RATE_DIRECTION": per_batch / available,
                "MULTIPLY_AVAILABLE_BY_RATE": available * per_batch,
            },
        )

    if selected == "RECIPROCAL_ERROR_ANALYSIS":
        divisor = _proper(rng)
        dividend = _proper(rng) + rng.randint(1, 3)
        quotient = dividend / divisor
        wrong = Fraction(dividend.denominator, dividend.numerator) * divisor
        if wrong == quotient:
            dividend += Fraction(1, dividend.denominator)
            quotient = dividend / divisor
            wrong = Fraction(dividend.denominator, dividend.numerator) * divisor
        return _variant(
            seed=seed,
            mode=mode,
            family=selected,
            prompt=(
                f"A learner solves {_text(dividend)} ÷ {_text(divisor)} by reciprocating the dividend "
                f"and multiplying, obtaining {_text(wrong)}. Identify the first invalid step, correct it, "
                "and verify the corrected quotient."
            ),
            dividend=dividend,
            divisor=divisor,
            quotient_unit="quotient",
            representation_prompt="Show the original division and the related missing-factor equation side by side.",
            explanation_code="RECIPROCAL_APPLIES_TO_DIVISOR_ONLY",
            misconceptions={
                "RECIPROCATE_DIVIDEND": wrong,
                "MULTIPLY_WITHOUT_RECIPROCAL": dividend * divisor,
            },
        )

    if selected == "DIMENSIONAL_TRANSFER":
        strip_width = _proper(rng)
        panel_area = strip_width * Fraction(rng.randint(2, 8), rng.choice((1, 2)))
        length = panel_area / strip_width
        return _variant(
            seed=seed,
            mode=mode,
            family=selected,
            prompt=(
                f"A rectangular display panel has area {_text(panel_area)} m² and width "
                f"{_text(strip_width)} m. Find its length. Explain why square metres divided by metres "
                "produces metres, then reconstruct the area."
            ),
            dividend=panel_area,
            divisor=strip_width,
            quotient_unit="metres",
            representation_prompt="Use an area rectangle with known total area and width; leave the length edge unlabeled.",
            explanation_code="AREA_DIVIDED_BY_WIDTH_GIVES_LENGTH",
            misconceptions={
                "MULTIPLY_AREA_BY_WIDTH": panel_area * strip_width,
                "KEEP_SQUARE_UNIT_AFTER_DIVISION": length + 1,
            },
        )

    raise AssertionError("unreachable family")


def fresh_transfer(
    seed: int, from_mode: str = "guided", to_mode: str = "independent"
) -> FractionDivisionVariant:
    """Return a same-seed transfer in a different family and mode."""

    _validate(seed, from_mode, None)
    _validate(seed, to_mode, None)
    if from_mode == to_mode:
        raise ValueError("transfer mode must differ from source mode")
    source = generate(seed, from_mode)
    transfer = generate(seed, to_mode)
    if source.family == transfer.family or source.prompt == transfer.prompt:
        raise AssertionError("transfer must change mathematical structure")
    return transfer
