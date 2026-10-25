"""Author-side *draft* exact-rational equation candidates for MTH1W review.

No imports into Mihur runtime, canonical registration, seeding, grading endpoints,
or curriculum mappings. This is a mathematical-content candidate tool, not a
release authorization or a learner assessment service.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from fractions import Fraction
from pathlib import Path

FAMILIES = (
    "TWO_STEP_SIGNED_RATIONAL",
    "TWO_STEP_FRACTIONAL_COEFFICIENT",
    "MULTISTEP_NEGATIVE_DISTRIBUTION",
    "MULTISTEP_VARIABLES_BOTH_SIDES",
)
MODES = ("DIAGNOSTIC", "GUIDED", "INDEPENDENT", "MASTERY")
SKILLS = {
    "TWO_STEP_SIGNED_RATIONAL": "MATH.EE.EQUATION.TWO",
    "TWO_STEP_FRACTIONAL_COEFFICIENT": "MATH.EE.EQUATION.TWO",
    "MULTISTEP_NEGATIVE_DISTRIBUTION": "MATH.EE.EQUATION.MULTISTEP",
    "MULTISTEP_VARIABLES_BOTH_SIDES": "MATH.EE.EQUATION.MULTISTEP",
}
PRESENTATIONS = {
    family: ("VARIABLE_TERM_FIRST", "CONSTANT_TERM_FIRST", "SIDES_REVERSED")
    for family in FAMILIES
}
TRANSFER_FAMILY = {
    "TWO_STEP_SIGNED_RATIONAL": "TWO_STEP_FRACTIONAL_COEFFICIENT",
    "TWO_STEP_FRACTIONAL_COEFFICIENT": "TWO_STEP_SIGNED_RATIONAL",
    "MULTISTEP_NEGATIVE_DISTRIBUTION": "MULTISTEP_VARIABLES_BOTH_SIDES",
    "MULTISTEP_VARIABLES_BOTH_SIDES": "MULTISTEP_NEGATIVE_DISTRIBUTION",
}

_REPAIR_LIBRARY = {
    "EQ.OMIT_CONSTANT": {
        "confirmation": "Before dividing, which term must be removed with the same operation on both sides?",
        "oracle": "REMOVE_CONSTANT_FROM_BOTH_SIDES",
        "questions": (
            "Which constant is attached to the variable term?",
            "What inverse operation removes it while preserving equality?",
        ),
    },
    "EQ.MULTIPLY_INSTEAD_OF_DIVIDE_FRACTION": {
        "confirmation": "After isolating the product, what undoes multiplication by the fractional coefficient?",
        "oracle": "MULTIPLY_BY_RECIPROCAL_ON_BOTH_SIDES",
        "questions": (
            "What number multiplied by the coefficient equals one?",
            "How must that reciprocal be applied to both sides?",
        ),
    },
    "EQ.DROPPED_BRACKET_CONSTANT": {
        "confirmation": "Which terms inside the parentheses receive the negative factor?",
        "oracle": "DISTRIBUTE_TO_EVERY_TERM",
        "questions": (
            "What is the product of the negative factor and x?",
            "What is its product with the second term in the parentheses?",
        ),
    },
    "EQ.IGNORED_RIGHT_VARIABLE": {
        "confirmation": "What must happen to the variable term on the right before division?",
        "oracle": "COLLECT_VARIABLE_TERMS_WITH_EQUAL_OPERATIONS",
        "questions": (
            "Which variable term can be subtracted from both sides?",
            "What coefficient remains after the variable terms are combined?",
        ),
    },
    "EQ.MOVED_LEFT_CONSTANT_WRONG_SIGN": {
        "confirmation": "Which inverse operation removes the left constant without changing the solution set?",
        "oracle": "APPLY_INVERSE_TO_BOTH_SIDES",
        "questions": (
            "What operation is currently applied to the variable term?",
            "What is its inverse, and where must it be applied?",
        ),
    },
    "EQ.OMITTED_LEFT_CONSTANT": {
        "confirmation": "Can the equation be divided by the variable coefficient before the additive term is removed?",
        "oracle": "ISOLATE_VARIABLE_TERM_FIRST",
        "questions": (
            "Which additive term prevents the variable term from being isolated?",
            "How can it be removed from both sides?",
        ),
    },
    "EQ.ADDED_VARIABLE_COEFFICIENTS": {
        "confirmation": "When variable terms are on opposite sides, should their coefficients be added or subtracted?",
        "oracle": "SUBTRACT_ONE_VARIABLE_TERM_FROM_BOTH_SIDES",
        "questions": (
            "Choose one variable term to remove from both sides.",
            "What signed coefficient remains after that subtraction?",
        ),
    },
    "EQ.USED_RECIPROCAL_WRONG_DIRECTION": {
        "confirmation": "After the variable term is isolated, should its coefficient be multiplied again or undone?",
        "oracle": "DIVIDE_BY_COEFFICIENT_OR_MULTIPLY_BY_ITS_RECIPROCAL",
        "questions": (
            "What operation currently connects the coefficient and the variable?",
            "Which inverse operation leaves a coefficient of one?",
        ),
    },
}

_CONFIRMATION_CHOICES = {
    "EQ.OMIT_CONSTANT": {
        "evidence_choice": "DIVIDE_BEFORE_REMOVING_CONSTANT",
        "choices": (
            (
                "DIVIDE_BEFORE_REMOVING_CONSTANT",
                "Divide by the variable coefficient before removing the additive constant.",
            ),
            (
                "REMOVE_CONSTANT_BOTH_SIDES",
                "Remove the additive constant with the same inverse operation on both sides.",
            ),
            (
                "CHANGE_ONLY_ONE_SIDE",
                "Change the side containing the variable without changing the other side.",
            ),
        ),
    },
    "EQ.MULTIPLY_INSTEAD_OF_DIVIDE_FRACTION": {
        "evidence_choice": "MULTIPLY_BY_COEFFICIENT_AGAIN",
        "choices": (
            (
                "MULTIPLY_BY_COEFFICIENT_AGAIN",
                "Multiply by the fractional coefficient again after isolating its product.",
            ),
            (
                "MULTIPLY_BY_RECIPROCAL_BOTH_SIDES",
                "Multiply both sides by the coefficient's reciprocal.",
            ),
            (
                "REMOVE_DENOMINATOR_ONE_SIDE",
                "Remove the denominator only from the side containing the variable.",
            ),
        ),
    },
    "EQ.DROPPED_BRACKET_CONSTANT": {
        "evidence_choice": "DISTRIBUTE_TO_X_ONLY",
        "choices": (
            (
                "DISTRIBUTE_TO_X_ONLY",
                "Multiply the factor by x but leave the other term in the parentheses unchanged.",
            ),
            (
                "DISTRIBUTE_TO_EVERY_TERM",
                "Multiply every term in the parentheses by the outside factor.",
            ),
            (
                "CHANGE_CONSTANT_WITHOUT_MULTIPLYING",
                "Change the sign of the constant without multiplying it by the outside factor.",
            ),
        ),
    },
    "EQ.IGNORED_RIGHT_VARIABLE": {
        "evidence_choice": "LEAVE_RIGHT_VARIABLE_UNCHANGED",
        "choices": (
            (
                "LEAVE_RIGHT_VARIABLE_UNCHANGED",
                "Solve using only the variable term on the left side.",
            ),
            (
                "SUBTRACT_VARIABLE_TERM_BOTH_SIDES",
                "Subtract one variable term from both complete sides before dividing.",
            ),
            (
                "ADD_COEFFICIENTS_ACROSS_SIDES",
                "Add the two variable coefficients because they appear on opposite sides.",
            ),
        ),
    },
    "EQ.MOVED_LEFT_CONSTANT_WRONG_SIGN": {
        "evidence_choice": "CHANGE_SIGN_WITHOUT_BALANCING",
        "choices": (
            (
                "CHANGE_SIGN_WITHOUT_BALANCING",
                "Move the constant and change its sign without applying an "
                "operation to both sides.",
            ),
            (
                "APPLY_INVERSE_BOTH_SIDES",
                "Apply the inverse operation to both complete sides.",
            ),
            (
                "KEEP_SIGN_AND_MOVE",
                "Move the constant to the other side without changing anything else.",
            ),
        ),
    },
    "EQ.OMITTED_LEFT_CONSTANT": {
        "evidence_choice": "DIVIDE_WHILE_CONSTANT_REMAINS",
        "choices": (
            (
                "DIVIDE_WHILE_CONSTANT_REMAINS",
                "Divide by the variable coefficient while the additive constant remains.",
            ),
            (
                "REMOVE_ADDITIVE_TERM_FIRST",
                "Remove the additive term from both sides before dividing.",
            ),
            (
                "DROP_CONSTANT",
                "Drop the additive constant because it has no variable.",
            ),
        ),
    },
    "EQ.ADDED_VARIABLE_COEFFICIENTS": {
        "evidence_choice": "ADD_OPPOSITE_SIDE_COEFFICIENTS",
        "choices": (
            (
                "ADD_OPPOSITE_SIDE_COEFFICIENTS",
                "Add the coefficients because the variable terms are on opposite sides.",
            ),
            (
                "SUBTRACT_ONE_VARIABLE_TERM_BOTH_SIDES",
                "Subtract one complete variable term from both sides.",
            ),
            (
                "CANCEL_VARIABLES_WITHOUT_OPERATION",
                "Cancel both variable terms without applying the same operation to each side.",
            ),
        ),
    },
    "EQ.USED_RECIPROCAL_WRONG_DIRECTION": {
        "evidence_choice": "MULTIPLY_BY_COEFFICIENT_AGAIN",
        "choices": (
            (
                "MULTIPLY_BY_COEFFICIENT_AGAIN",
                "Multiply by the variable coefficient again.",
            ),
            (
                "DIVIDE_OR_RECIPROCAL",
                "Divide by the coefficient or multiply by its reciprocal on both sides.",
            ),
            (
                "FLIP_VARIABLE",
                "Replace the variable with its reciprocal.",
            ),
        ),
    },
}


def _rng(family: str, seed: str | int, mode: str) -> random.Random:
    key = f"mihur-mth1w-linear-draft-v1|{family}|{mode}|{seed}"
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def _noninteger(rng: random.Random) -> Fraction:
    while True:
        denominator = rng.randint(2, 7)
        numerator = rng.randint(-20, 20)
        if numerator != 0 and math.gcd(abs(numerator), denominator) == 1:
            return Fraction(numerator, denominator)


def _nonzero(rng: random.Random, lowest: int, highest: int) -> int:
    while True:
        n = rng.randint(lowest, highest)
        if n:
            return n


def _fmt(f: Fraction) -> str:
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def _task_fingerprint(
    family: str,
    displayed: tuple[Fraction, Fraction, Fraction, Fraction],
) -> str:
    """One identity for a displayed affine equation, even if sides are swapped.

    The family remains part of the identity because a bracket/distribution
    task and a flat equation exercise different mathematical operations.
    Within a family, reordering terms or reversing sides must not masquerade
    as a novel task in another assessment mode. Equal roots alone do *not*
    imply duplicate instructional tasks.
    """
    a, b, c, d = displayed
    sides = sorted(((_fmt(a), _fmt(b)), (_fmt(c), _fmt(d))))
    payload = {
        "version": "AFFINE_SIDE_SYMMETRY_V1",
        "family": family,
        "sides": sides,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()


def _case(
    family: str,
    rng: random.Random,
) -> tuple[
    str,
    tuple[Fraction, Fraction, Fraction, Fraction],
    tuple[Fraction, Fraction, Fraction, Fraction],
    str,
    str,
    tuple[str, str],
    Fraction,
    str,
]:
    """Return prompt, coefficients, repair metadata and presentation layout."""
    if family == "TWO_STEP_SIGNED_RATIONAL":
        x = _noninteger(rng)
        a = x.denominator * rng.choice((-1, 1)) * rng.randint(1, 4)
        b = _nonzero(rng, -15, 15)
        d = a * x + b
        presentation = rng.choice(PRESENTATIONS[family])
        if presentation == "VARIABLE_TERM_FIRST":
            prompt = f"Solve {a}x {b:+d} = {d}."
            displayed = (Fraction(a), Fraction(b), Fraction(0), Fraction(d))
        elif presentation == "CONSTANT_TERM_FIRST":
            prompt = f"Solve {b} {a:+d}x = {d}."
            displayed = (Fraction(a), Fraction(b), Fraction(0), Fraction(d))
        else:
            prompt = f"Solve {d} = {a}x {b:+d}."
            displayed = (Fraction(0), Fraction(d), Fraction(a), Fraction(b))
        return (
            prompt,
            displayed,
            (Fraction(a), Fraction(b), Fraction(0), Fraction(d)),
            "EQ.OMIT_CONSTANT",
            "Subtract the constant on BOTH sides before dividing by the signed coefficient.",
            (
                "What operation preserves equality while removing the constant?",
                "Divide both sides by the coefficient, including its sign.",
            ),
            Fraction(d, a),
            presentation,
        )
    if family == "TWO_STEP_FRACTIONAL_COEFFICIENT":
        while True:
            denominator = rng.randint(2, 8)
            a = _nonzero(rng, -9, 9)
            if math.gcd(abs(a), denominator) != 1:
                continue
            change = _nonzero(rng, -12, 12)
            x = Fraction(denominator * change, a)
            if x.denominator > 1:
                break
        b = _nonzero(rng, -12, 12)
        d = b + change
        presentation = rng.choice(PRESENTATIONS[family])
        coefficient = Fraction(a, denominator)
        if presentation == "VARIABLE_TERM_FIRST":
            prompt = f"Solve ({a}/{denominator})x {b:+d} = {d}."
            displayed = (coefficient, Fraction(b), Fraction(0), Fraction(d))
        elif presentation == "CONSTANT_TERM_FIRST":
            sign = "+" if a > 0 else "-"
            prompt = f"Solve {b} {sign} ({abs(a)}/{denominator})x = {d}."
            displayed = (coefficient, Fraction(b), Fraction(0), Fraction(d))
        else:
            prompt = f"Solve {d} = ({a}/{denominator})x {b:+d}."
            displayed = (Fraction(0), Fraction(d), coefficient, Fraction(b))
        return (
            prompt,
            displayed,
            (coefficient, Fraction(b), Fraction(0), Fraction(d)),
            "EQ.MULTIPLY_INSTEAD_OF_DIVIDE_FRACTION",
            "First isolate the product, then multiply both sides by the coefficient's reciprocal.",
            (
                "Remove the additive term from both sides first.",
                "Undo multiplication by a fraction with its reciprocal.",
            ),
            Fraction(a * change, denominator),
            presentation,
        )
    if family == "MULTISTEP_NEGATIVE_DISTRIBUTION":
        x = _noninteger(rng)
        k = x.denominator * rng.randint(1, 4)
        b = _nonzero(rng, -9, 9)
        c = rng.randint(-12, 12)
        target = -k * (x - b) + c
        presentation = rng.choice(PRESENTATIONS[family])
        if presentation == "VARIABLE_TERM_FIRST":
            prompt = f"Solve -{k}(x - ({b})) + ({c}) = {target}."
            displayed = (Fraction(-k), Fraction(k * b + c), Fraction(0), Fraction(target))
        elif presentation == "CONSTANT_TERM_FIRST":
            prompt = f"Solve ({c}) - {k}(x - ({b})) = {target}."
            displayed = (Fraction(-k), Fraction(k * b + c), Fraction(0), Fraction(target))
        else:
            prompt = f"Solve {target} = -{k}(x - ({b})) + ({c})."
            displayed = (Fraction(0), Fraction(target), Fraction(-k), Fraction(k * b + c))
        return (
            prompt,
            displayed,
            (Fraction(-k), Fraction(k * b + c), Fraction(0), Fraction(target)),
            "EQ.DROPPED_BRACKET_CONSTANT",
            "Distribute the negative factor to BOTH terms, simplify, and preserve equality.",
            (
                "A negative multiplier changes each term inside the parentheses.",
                "After distribution, collect constants and isolate x.",
            ),
            Fraction(c - target, k),
            presentation,
        )
    if family == "MULTISTEP_VARIABLES_BOTH_SIDES":
        x = _noninteger(rng)
        while True:
            c = _nonzero(rng, -8, 8)
            difference = x.denominator * rng.choice((-1, 1)) * rng.randint(1, 3)
            a = c + difference
            if a != 0:
                break
        b = _nonzero(rng, -12, 12)
        d = difference * x + b
        presentation = rng.choice(PRESENTATIONS[family])
        if presentation == "VARIABLE_TERM_FIRST":
            prompt = f"Solve {a}x {b:+d} = {c}x {int(d):+d}."
            displayed = (Fraction(a), Fraction(b), Fraction(c), Fraction(d))
        elif presentation == "CONSTANT_TERM_FIRST":
            prompt = f"Solve {b} {a:+d}x = {int(d)} {c:+d}x."
            displayed = (Fraction(a), Fraction(b), Fraction(c), Fraction(d))
        else:
            prompt = f"Solve {c}x {int(d):+d} = {a}x {b:+d}."
            displayed = (Fraction(c), Fraction(d), Fraction(a), Fraction(b))
        return (
            prompt,
            displayed,
            (Fraction(a), Fraction(b), Fraction(c), Fraction(d)),
            "EQ.IGNORED_RIGHT_VARIABLE",
            "Apply the same subtraction to both sides to collect variable terms before dividing.",
            (
                "Subtract one variable term from BOTH sides.",
                "Simplify the variable coefficient, then isolate x.",
            ),
            Fraction(d - b, a),
            presentation,
        )
    raise ValueError(f"Unknown draft family: {family}")


def _diagnostic_contract(
    *,
    answer: Fraction,
    primary_code: str,
    primary_wrong: Fraction,
    normalized: tuple[Fraction, Fraction, Fraction, Fraction],
) -> dict:
    a, b, c, d = normalized
    candidates: list[tuple[str, Fraction]] = [(primary_code, primary_wrong)]
    candidates.extend(
        [
            ("EQ.MOVED_LEFT_CONSTANT_WRONG_SIGN", (d + b) / (a - c)),
            ("EQ.OMITTED_LEFT_CONSTANT", d / (a - c)),
            ("EQ.USED_RECIPROCAL_WRONG_DIRECTION", (d - b) * (a - c)),
        ]
    )
    if a:
        candidates.append(("EQ.IGNORED_RIGHT_VARIABLE", (d - b) / a))
    if a + c:
        candidates.append(("EQ.ADDED_VARIABLE_COEFFICIENTS", (d - b) / (a + c)))

    signals: list[dict] = []
    seen = {answer}
    for code, wrong in candidates:
        if wrong in seen:
            continue
        seen.add(wrong)
        repair = _REPAIR_LIBRARY[code]
        confirmation = _CONFIRMATION_CHOICES[code]
        signals.append(
            {
                "misconception_code": code,
                "candidate_response": f"x={_fmt(wrong)}",
                "confirmation_probe_for_author_review": repair["confirmation"],
                "confirmation_oracle_for_author_review": repair["oracle"],
                "confirmation_choices_for_learner": [
                    {"id": choice_id, "text": text}
                    for choice_id, text in confirmation["choices"]
                ],
                "confirmation_evidence_choice_for_author_review": confirmation[
                    "evidence_choice"
                ],
                "socratic_repair_for_author_review": list(repair["questions"]),
            }
        )
    if len(signals) < 2:
        raise ArithmeticError("At least two distinct diagnostic signals are required")
    return {
        "classification_policy": "DO_NOT_CLASSIFY_FROM_ONE_RESPONSE",
        "minimum_corroborating_signals": 2,
        "ambiguous_response_policy": "ASK_NEUTRAL_CONFIRMATION_AND_WITHHOLD_LABEL",
        "signals": signals,
    }


def create_candidate(family: str, *, seed: str | int, mode: str) -> dict:
    if (
        family not in FAMILIES
        or mode not in MODES
        or type(seed) not in (str, int)
        or isinstance(seed, str)
        and not seed
    ):
        raise ValueError("Unknown family, mode or invalid seed")
    (
        prompt,
        (a, b, c, d),
        normalized,
        misconception,
        rationale,
        hints,
        wrong,
        presentation,
    ) = _case(family, _rng(family, seed, mode))
    if a == c:
        raise ArithmeticError("Nonunique or nonexistent equation solution")
    answer = (d - b) / (a - c)
    if answer.denominator == 1:
        raise ArithmeticError("Draft family must provide a noninteger rational answer")
    if wrong == answer:
        raise ArithmeticError("Misconception collides with the correct answer")
    coefficients = {
        "lhs_x": _fmt(a),
        "lhs_constant": _fmt(b),
        "rhs_x": _fmt(c),
        "rhs_constant": _fmt(d),
    }
    normalized_coefficients = dict(
        zip(
            ("lhs_x", "lhs_constant", "rhs_x", "rhs_constant"),
            (_fmt(value) for value in normalized),
        )
    )
    fingerprint = _task_fingerprint(family, (a, b, c, d))
    return {
        "candidate_family": family,
        "canonical_skill_hint": SKILLS[family],
        "mode": mode,
        "variant_id": hashlib.sha256(f"{family}|{mode}|{seed}".encode()).hexdigest()[:24],
        "task_fingerprint": fingerprint,
        "task_fingerprint_version": "AFFINE_SIDE_SYMMETRY_V1",
        "presentation_id": presentation,
        "reasoning_structure_id": family,
        "prompt": prompt,
        "equation_coefficients": coefficients,
        "normalized_equation_coefficients": normalized_coefficients,
        "canonical_answer": f"x={_fmt(answer)}",
        "explanation_for_author_review": rationale,
        "guided_hints_for_author_review": list(hints),
        "misconception_code": misconception,
        "misconception_answer": f"x={_fmt(wrong)}",
        "diagnostic_contract_for_author_review": _diagnostic_contract(
            answer=answer,
            primary_code=misconception,
            primary_wrong=wrong,
            normalized=normalized,
        ),
        "guided_repair_contract_for_author_review": {
            "allowed_mode": "GUIDED",
            "requires_confirmed_misconception": True,
            "target_family": family,
            "worked_answer_reveal": False,
            "independent_recheck_required": True,
        },
        "assessment_evidence_definition": {
            "hinted_success_counts_as_independent": False,
            "independent_modes": ["INDEPENDENT", "MASTERY"],
            "requires_unhinted_transfer": True,
            "requires_new_task_fingerprint": True,
            "requires_changed_reasoning_structure_id": True,
            "runtime_credit_authorized": False,
        },
    }


def learner_projection(candidate: dict) -> dict:
    """Minimal view, including no answers/hints/misconception values in any mode."""
    return {k: candidate[k] for k in ("variant_id", "mode", "prompt")}


def create_unhinted_transfer(
    source: dict,
    *,
    target_mode: str = "INDEPENDENT",
) -> dict:
    """Select a same-skill, different-reasoning-family task without runtime credit."""
    if target_mode not in ("INDEPENDENT", "MASTERY"):
        raise ValueError("Transfer must be independent or mastery mode")
    source_family = source["candidate_family"]
    target_family = TRANSFER_FAMILY[source_family]
    if SKILLS[target_family] != source["canonical_skill_hint"]:
        raise ArithmeticError("Transfer family must preserve the canonical skill")
    for attempt in range(2048):
        seed = f"transfer|{source['variant_id']}|{attempt}"
        target = create_candidate(target_family, seed=seed, mode=target_mode)
        if target["task_fingerprint"] == source["task_fingerprint"]:
            continue
        if target["canonical_answer"] == source["canonical_answer"]:
            continue
        return {
            "source_variant_id": source["variant_id"],
            "source_family": source_family,
            "target_family": target_family,
            "target_mode": target_mode,
            "source_reasoning_structure_id": source["reasoning_structure_id"],
            "target_reasoning_structure_id": target["reasoning_structure_id"],
            "reasoning_structure_changed": True,
            "source_presentation_id": source["presentation_id"],
            "target_presentation_id": target["presentation_id"],
            "presentation_changed": (
                source["presentation_id"] != target["presentation_id"]
            ),
            "task_fingerprint_changed": True,
            "answer_changed": True,
            "hints_allowed": False,
            "hinted_success_counts_as_independent": False,
            "runtime_credit_authorized": False,
            "learner_task": learner_projection(target),
            "private_exact_oracle_for_review": target["canonical_answer"],
            "private_target_fingerprint_for_review": target["task_fingerprint"],
        }
    raise ArithmeticError("Different-reasoning-family transfer budget exhausted")


def _parse_exact_response(response: str | None) -> Fraction | None:
    """Parse a bounded exact response for the author-side journey simulator."""
    if not isinstance(response, str):
        return None
    value = response.strip().replace(" ", "")
    if value.casefold().startswith("x="):
        value = value[2:]
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None


def _signal_for_response(candidate: dict, response: str) -> dict | None:
    parsed = _parse_exact_response(response)
    if parsed is None:
        return None
    for signal in candidate["diagnostic_contract_for_author_review"]["signals"]:
        if _parse_exact_response(signal["candidate_response"]) == parsed:
            return signal
    return None


def _create_target_preserving_guided_retest(
    source: dict,
    misconception_code: str,
) -> tuple[dict, dict]:
    """Find a fresh same-family task that can probe the confirmed reasoning error."""
    for attempt in range(2048):
        target = create_candidate(
            source["candidate_family"],
            seed=(
                f"guided-retest|{source['variant_id']}|"
                f"{misconception_code}|{attempt}"
            ),
            mode="GUIDED",
        )
        if target["task_fingerprint"] == source["task_fingerprint"]:
            continue
        if target["canonical_answer"] == source["canonical_answer"]:
            continue
        for signal in target["diagnostic_contract_for_author_review"]["signals"]:
            if signal["misconception_code"] == misconception_code:
                return target, signal
    raise ArithmeticError("Target-preserving guided retest budget exhausted")


def authored_journey_learner_projection(journey: dict) -> dict:
    """Expose only the learner-operable part of an author-review journey."""
    stage = journey["stage"]
    result = {
        "stage": stage,
        "guided_success_counts_as_independent": False,
        "runtime_credit_authorized": False,
    }
    if stage == "PRACTICE_RETRY":
        result["neutral_prompt"] = journey["neutral_prompt"]
    elif stage == "CONFIRM_REASONING":
        result["confirmation_prompt"] = journey["confirmation_prompt"]
        result["confirmation_choices"] = journey["confirmation_choices"]
    elif stage in ("GUIDED_RETEST", "GUIDED_RETEST_RETRY"):
        result["socratic_repair_questions"] = journey[
            "socratic_repair_questions"
        ]
        result["guided_retest_task"] = journey["guided_retest_task"]
        if stage == "GUIDED_RETEST_RETRY":
            result["neutral_prompt"] = journey["neutral_prompt"]
    elif stage == "READY_FOR_TRANSFER_CONFIRMATION":
        result["readiness_prompt"] = (
            "Are you ready to solve a fresh problem without hints?"
        )
    elif stage in ("INDEPENDENT_EXIT", "INDEPENDENT_RETRY"):
        result["independent_task"] = journey["independent_task"]
        result["hints_allowed"] = False
    elif stage == "COMPLETE":
        result["independent_success"] = True
    return result


def simulate_authored_learning_journey(
    source: dict,
    *,
    practice_response: str,
    follow_up_reasoning_response: str | None = None,
    guided_retest_response: str | None = None,
    readiness_confirmed: bool = False,
    independent_response: str | None = None,
) -> dict:
    """Execute a draft response→probe→repair→transfer authoring scenario.

    This is review evidence, not a runtime route or trusted scorer. The follow-up
    response is a learner-selected structured choice from the neutral choices
    emitted at ``CONFIRM_REASONING``. Only corroborated reasoning selects a
    misconception route. Guided success never counts as independent mastery.
    """
    if source.get("mode") != "GUIDED":
        raise ValueError("Authored teaching journey requires a GUIDED source")

    transcript: list[dict] = [
        {"stage": "PRACTICE", "learner_response": practice_response}
    ]

    def finish(journey: dict) -> dict:
        journey["journey_transcript_for_author_review"] = list(transcript)
        return journey

    practice_value = _parse_exact_response(practice_response)
    correct_value = _parse_exact_response(source["canonical_answer"])
    if practice_value is None:
        transcript.append({"stage": "PRACTICE_RETRY", "reason": "UNPARSEABLE"})
        return finish({
            "stage": "PRACTICE_RETRY",
            "neutral_prompt": "Enter one exact value for x before explaining your strategy.",
            "confirmed_misconception_for_author_review": None,
        })

    transfer_source = source
    if practice_value == correct_value:
        transcript.append({"stage": "READY_FOR_TRANSFER_CONFIRMATION"})
        journey = {
            "stage": "READY_FOR_TRANSFER_CONFIRMATION",
            "practice_was_correct": True,
            "confirmed_misconception_for_author_review": None,
        }
    else:
        signal = _signal_for_response(source, practice_response)
        if signal is None:
            transcript.append({"stage": "PRACTICE_RETRY", "reason": "NO_MATCH"})
            return finish({
                "stage": "PRACTICE_RETRY",
                "neutral_prompt": (
                    "Show the first equality-preserving operation you would apply "
                    "to both complete sides."
                ),
                "confirmed_misconception_for_author_review": None,
            })
        if follow_up_reasoning_response is None:
            transcript.append({"stage": "CONFIRM_REASONING"})
            return finish({
                "stage": "CONFIRM_REASONING",
                "confirmation_prompt": signal[
                    "confirmation_probe_for_author_review"
                ],
                "confirmation_choices": signal[
                    "confirmation_choices_for_learner"
                ],
                "pending_misconception_for_author_review": signal[
                    "misconception_code"
                ],
                "confirmed_misconception_for_author_review": None,
            })
        transcript.append(
            {
                "stage": "CONFIRM_REASONING",
                "learner_response": follow_up_reasoning_response,
            }
        )
        if (
            follow_up_reasoning_response
            != signal["confirmation_evidence_choice_for_author_review"]
        ):
            transcript.append(
                {"stage": "PRACTICE_RETRY", "reason": "AMBIGUOUS_EVIDENCE"}
            )
            return finish({
                "stage": "PRACTICE_RETRY",
                "neutral_prompt": (
                    "Your answer and strategy evidence do not yet support one "
                    "diagnosis. Try the equation again and show the same operation "
                    "on both complete sides."
                ),
                "confirmed_misconception_for_author_review": None,
            })

        retest, retest_signal = _create_target_preserving_guided_retest(
            source,
            signal["misconception_code"],
        )
        retest_task = learner_projection(retest)
        retest_value = _parse_exact_response(guided_retest_response)
        journey = {
            "stage": "GUIDED_RETEST",
            "practice_was_correct": False,
            "confirmed_misconception_for_author_review": signal[
                "misconception_code"
            ],
            "socratic_repair_questions": retest_signal[
                "socratic_repair_for_author_review"
            ],
            "guided_retest_task": retest_task,
            "private_guided_retest_for_author_review": retest,
        }
        transcript.append(
            {
                "stage": "GUIDED_RETEST",
                "learner_response": guided_retest_response,
                "confirmed_misconception": signal["misconception_code"],
            }
        )
        if guided_retest_response is None:
            return finish(journey)
        if retest_value != _parse_exact_response(retest["canonical_answer"]):
            journey["stage"] = "GUIDED_RETEST_RETRY"
            journey["neutral_prompt"] = (
                "Recheck whether the same operation was applied to both complete sides."
            )
            transcript.append({"stage": "GUIDED_RETEST_RETRY"})
            return finish(journey)
        transcript.append({"stage": "READY_FOR_TRANSFER_CONFIRMATION"})
        journey = {
            "stage": "READY_FOR_TRANSFER_CONFIRMATION",
            "practice_was_correct": False,
            "guided_retest_succeeded": True,
            "guided_success_counts_as_independent": False,
            "confirmed_misconception_for_author_review": signal[
                "misconception_code"
            ],
        }
        transfer_source = retest

    if not readiness_confirmed:
        return finish(journey)

    transfer = create_unhinted_transfer(
        transfer_source,
        target_mode="INDEPENDENT",
    )
    journey = {
        "stage": "INDEPENDENT_EXIT",
        "independent_task": transfer["learner_task"],
        "hints_allowed": False,
        "guided_success_counts_as_independent": False,
        "runtime_credit_authorized": False,
        "private_transfer_for_author_review": transfer,
    }
    transcript.append(
        {
            "stage": "INDEPENDENT_EXIT",
            "learner_response": independent_response,
        }
    )
    if independent_response is None:
        return finish(journey)
    if (
        _parse_exact_response(independent_response)
        != _parse_exact_response(transfer["private_exact_oracle_for_review"])
    ):
        journey["stage"] = "INDEPENDENT_RETRY"
        journey["independent_success"] = False
        transcript.append({"stage": "INDEPENDENT_RETRY"})
        return finish(journey)
    transcript.append({"stage": "COMPLETE"})
    return finish({
        "stage": "COMPLETE",
        "independent_success": True,
        "guided_success_counts_as_independent": False,
        "runtime_credit_authorized": False,
    })


def create_pack(*, count_per_family_mode: int = 25) -> dict:
    if type(count_per_family_mode) is not int or not 1 <= count_per_family_mode <= 100:
        raise ValueError("count must be in 1..100")
    produced: list[dict] = []
    for family in FAMILIES:
        seen: set[str] = set()
        for mode in MODES:
            count, attempt = 0, 0
            while count < count_per_family_mode:
                if attempt > count_per_family_mode * 100:
                    raise ArithmeticError("Unique-task budget exhausted")
                candidate = create_candidate(family, seed=attempt, mode=mode)
                attempt += 1
                if candidate["task_fingerprint"] in seen:
                    continue
                seen.add(candidate["task_fingerprint"])
                produced.append(candidate)
                count += 1
    return {
        "schema": "MIHUR_DRAFT_RATIONAL_EQUATION_CANDIDATES_V5",
        "source_issue": "AyalewGM/ai-tutor#337",
        "curriculum_hint": "Ontario Grade 9 MTH1W — proposed scope only",
        "official_standards_mapping_status": "NOT_INDEPENDENTLY_APPROVED",
        "origin": "MIHUR_AUTHORED_DRAFT",
        "math_review": "PENDING_INDEPENDENT",
        "pedagogy_review": "PENDING_INDEPENDENT",
        "security_review": "PENDING_INDEPENDENT",
        "qa_review": "PENDING_INDEPENDENT",
        "runtime_registered": False,
        "runtime_activation": False,
        "requires_server_authoritative_scoring": True,
        "diagnosis_requires_multiple_probes": True,
        "authored_learning_journey": "RESPONSE_PROBE_REPAIR_RETEST_TRANSFER_V1",
        "hinted_success_counts_as_independent": False,
        "transfer_requires_changed_reasoning_structure": True,
        "transfer_requires_changed_presentation": False,
        "task_fingerprint_version": "AFFINE_SIDE_SYMMETRY_V1",
        "candidates": produced,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count-per-family-mode", type=int, default=25)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pack = create_pack(count_per_family_mode=args.count_per_family_mode)
    args.output.write_text(json.dumps(pack, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(pack['candidates'])} DRAFT_UNVERIFIED candidates to {args.output}")


if __name__ == "__main__":
    main()
