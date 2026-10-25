"""Draft-only Grade 8 multistep linear-equation question families.

This module is authoring evidence.  It is deliberately outside ``app`` and is
not registered, seeded, scored, mapped, or exposed to learners at runtime.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any

MODES = ("diagnostic", "guided", "independent", "mastery")
LEARNING_STAGES = (
    "OBSERVE",
    "PREDICT",
    "MANIPULATE",
    "EXPLAIN",
    "PRACTICE",
    "DIAGNOSE",
    "TRANSFER",
    "VERIFY",
)
COMPLETE_STAGE = "COMPLETE"
PRIMARY_SEEDS = range(16)
TRANSFER_SEEDS = range(1_000_003, 1_000_019)
CANONICAL_SKILL = "MATH.EE.EQUATION.MULTISTEP"

FAMILIES = (
    "DISTRIBUTE_POSITIVE_ONE_SIDE",
    "DISTRIBUTE_NEGATIVE_ONE_SIDE",
    "COMBINE_LIKE_TERMS",
    "VARIABLES_BOTH_SIDES",
    "FRACTIONAL_COEFFICIENTS",
    "NESTED_GROUPS",
    "IDENTITY_ALL_REAL",
    "CONTRADICTION_NO_SOLUTION",
    "PERIMETER_MODEL",
    "COMPETING_PLANS_MODEL",
    "ERROR_ANALYSIS_FIRST_INVALID_STEP",
    "SOLUTION_CLASS_COMPARE",
)

FAMILY_METADATA: dict[str, dict[str, Any]] = {
    "DISTRIBUTE_POSITIVE_ONE_SIDE": {
        "prerequisites": ["integer arithmetic", "distributive property", "one-step inverse operations"],
        "difficulty_rationale": "Requires distributing before isolating a rational solution.",
        "representation": ["equal-group balance", "area/partial-product diagram", "symbolic equation"],
        "structure": "positive distribution on one side",
    },
    "DISTRIBUTE_NEGATIVE_ONE_SIDE": {
        "prerequisites": ["signed multiplication", "distributive property", "equality preservation"],
        "difficulty_rationale": "The outside negative must affect both terms before inverse operations.",
        "representation": ["signed chips", "two-arrow distribution diagram", "symbolic equation"],
        "structure": "negative distribution on one side",
    },
    "COMBINE_LIKE_TERMS": {
        "prerequisites": ["like terms", "integer arithmetic", "inverse operations"],
        "difficulty_rationale": "Combining two variable terms is necessary before solving.",
        "representation": ["algebra tiles", "coefficient table", "symbolic equation"],
        "structure": "combine like terms before solving",
    },
    "VARIABLES_BOTH_SIDES": {
        "prerequisites": ["signed rational arithmetic", "equality preservation"],
        "difficulty_rationale": "A variable term must be removed from one complete side.",
        "representation": ["balance model", "side-by-side coefficient table", "symbolic equation"],
        "structure": "variables on both sides",
    },
    "FRACTIONAL_COEFFICIENTS": {
        "prerequisites": ["fraction multiplication", "common denominators", "inverse operations"],
        "difficulty_rationale": "Exact fractional coefficients require reciprocal reasoning without decimal approximation.",
        "representation": ["fraction bars", "scaled balance", "symbolic equation"],
        "structure": "exact fractional coefficients",
    },
    "NESTED_GROUPS": {
        "prerequisites": ["distribution", "like terms", "signed arithmetic"],
        "difficulty_rationale": "Two grouped expressions must be expanded and combined.",
        "representation": ["paired area models", "term ledger", "symbolic equation"],
        "structure": "two grouped expressions",
    },
    "IDENTITY_ALL_REAL": {
        "prerequisites": ["equivalent expressions", "solution sets"],
        "difficulty_rationale": "Students must recognize an identity rather than force a single solution.",
        "representation": ["matching balance states", "coefficient comparison", "symbolic identity"],
        "structure": "infinitely many solutions",
    },
    "CONTRADICTION_NO_SOLUTION": {
        "prerequisites": ["equivalent expressions", "solution sets"],
        "difficulty_rationale": "Equal variable coefficients reduce to a false constant statement.",
        "representation": ["unbalanced equal-variable model", "coefficient comparison", "symbolic contradiction"],
        "structure": "no solution contradiction",
    },
    "PERIMETER_MODEL": {
        "prerequisites": ["rectangle perimeter", "distribution", "equation solving"],
        "difficulty_rationale": "A geometric context must be modeled before the equation is solved and checked.",
        "representation": ["labelled rectangle", "perimeter decomposition", "symbolic equation"],
        "structure": "context-to-equation perimeter model",
    },
    "COMPETING_PLANS_MODEL": {
        "prerequisites": ["fixed-plus-rate expressions", "variables on both sides"],
        "difficulty_rationale": "Two contextual linear expressions must be equated and interpreted.",
        "representation": ["cost table", "two line descriptions", "symbolic equality"],
        "structure": "equal-value competing plans",
    },
    "ERROR_ANALYSIS_FIRST_INVALID_STEP": {
        "prerequisites": ["distribution", "equivalent transformations", "substitution"],
        "difficulty_rationale": "Students locate the first invalid transformation, repair it, and still solve exactly.",
        "representation": ["step cards", "balance annotations", "corrected symbolic path"],
        "structure": "first-error critique and repair",
    },
    "SOLUTION_CLASS_COMPARE": {
        "prerequisites": ["one/no/all-real solution classes", "distribution", "like terms"],
        "difficulty_rationale": "Three superficially similar equations must be classified by structure, not appearance.",
        "representation": ["three balance snapshots", "coefficient-invariant table", "symbolic classifications"],
        "structure": "compare all three solution classes",
    },
}

ACCESSIBILITY = {
    "keyboard": "All response choices and exact-value fields are reachable in prompt order without drag gestures.",
    "screen_reader": "Read each complete left side, then 'equals', then each complete right side; announce parentheses and fraction bars.",
    "focus": "After checking, focus moves to the first invalid field or the stage summary without erasing prior work.",
    "non_color": "Every sign, side, group, and step uses a text label and shape/border cue in addition to colour.",
    "reduced_motion": "Any balance or tile animation has a simultaneous labelled before/after alternative.",
    "exact_input": "Accept signed integers, a/b fractions, and equivalent reduced or unreduced fractions; never require a Unicode minus.",
}


def _fmt(value: Fraction | int) -> str:
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _term(coefficient: Fraction, variable: str = "x") -> str:
    coefficient = Fraction(coefficient)
    if coefficient == 0:
        return "0"
    if coefficient == 1:
        return variable
    if coefficient == -1:
        return f"-{variable}"
    return f"{_fmt(coefficient)}{variable}"


def _affine(a: Fraction, b: Fraction) -> str:
    if a == 0:
        return _fmt(b)
    if b == 0:
        return _term(a)
    sign = "+" if b > 0 else "-"
    return f"{_term(a)} {sign} {_fmt(abs(b))}"


def _equation(coefficients: tuple[Fraction, Fraction, Fraction, Fraction]) -> str:
    a, b, c, d = coefficients
    return f"{_affine(a, b)} = {_affine(c, d)}"


def _parse_exact(response: str | None) -> Fraction | None:
    if not isinstance(response, str):
        return None
    value = response.strip().replace(" ", "").replace("−", "-")
    if value.lower().startswith("x="):
        value = value[2:]
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        return None


def _parse_error_code_and_rational(response: str | None) -> tuple[str, Fraction] | None:
    """Validate the step identifier separately from the exact rational x-value."""
    if not isinstance(response, str):
        return None
    parts = response.strip().split("|")
    if len(parts) != 2:
        return None
    step_code, solution_text = parts
    step_code = step_code.strip().upper()
    solution_text = solution_text.strip()
    solution_parts = solution_text.split("=")
    if (
        not step_code
        or len(solution_parts) != 2
        or solution_parts[0].strip().lower() != "x"
    ):
        return None
    rational = _parse_exact(solution_parts[1])
    if rational is None:
        return None
    return step_code, rational


def _normalize_coefficients(values: tuple[Fraction, ...]) -> tuple[int, ...]:
    denominators = [v.denominator for v in values]
    scale = math.lcm(*denominators)
    integers = [int(v * scale) for v in values]
    common = 0
    for value in integers:
        common = math.gcd(common, abs(value))
    if common:
        integers = [value // common for value in integers]
    first = next((value for value in integers if value), 1)
    if first < 0:
        integers = [-value for value in integers]
    return tuple(integers)


def _affine_fingerprint(
    coefficients: tuple[Fraction, Fraction, Fraction, Fraction],
) -> str:
    direct = _normalize_coefficients(coefficients)
    a, b, c, d = coefficients
    reversed_sides = _normalize_coefficients((c, d, a, b))
    canonical = min(direct, reversed_sides)
    return ":".join(str(value) for value in canonical)


def _mode_index(mode: str) -> int:
    if mode not in MODES:
        raise ValueError(f"unsupported draft mode: {mode}")
    return MODES.index(mode)


def _seed_index(seed: int, mode: str) -> int:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if seed in PRIMARY_SEEDS:
        local = seed
    elif seed in TRANSFER_SEEDS:
        local = seed - TRANSFER_SEEDS.start
    else:
        raise ValueError("seed is outside the reviewed primary/transfer bands")
    return local + 16 * _mode_index(mode)


def _unique_target(index: int) -> Fraction:
    numerator = (index * 17) % 37 - 18
    if numerator == 0:
        numerator = 19
    denominator = (2, 3, 4, 5)[index % 4]
    value = Fraction(numerator, denominator)
    if value in (1, -1):
        value += Fraction(1, denominator)
    return value


def _classify(coefficients: tuple[Fraction, Fraction, Fraction, Fraction]) -> tuple[str, str]:
    a, b, c, d = coefficients
    if a == c:
        return ("ALL_REAL", "ALL_REAL") if b == d else ("NO_SOLUTION", "NO_SOLUTION")
    answer = (d - b) / (a - c)
    return "UNIQUE", f"x={_fmt(answer)}"


def _unique_signals(answer: Fraction) -> tuple[dict[str, Any], ...]:
    candidates = [
        ("SIGN_REVERSAL", -answer, "I moved a term across the equals sign and changed its sign."),
        ("INVERSE_OPERATION", answer + 1, "I used the same operation instead of its inverse."),
        ("RECIPROCAL_CONFUSION", Fraction(1, 1) / answer, "I inverted the final value instead of undoing the coefficient."),
    ]
    seen = {answer}
    result = []
    for code, value, reasoning in candidates:
        if value in seen:
            continue
        seen.add(value)
        result.append({
            "code": code,
            "candidate_response": f"x={_fmt(value)}",
            "reasoning_choice": code,
            "reasoning_label": reasoning,
        })
    return tuple(result)


def _class_signals(solution_class: str) -> tuple[dict[str, Any], ...]:
    if solution_class == "ALL_REAL":
        return (
            {"code": "FORCED_SINGLE_SOLUTION", "candidate_response": "x=0", "reasoning_choice": "DIVIDED_ZERO_COEFFICIENT", "reasoning_label": "I divided by the remaining x coefficient even though it was zero."},
            {"code": "IDENTITY_CALLED_CONTRADICTION", "candidate_response": "NO_SOLUTION", "reasoning_choice": "EQUAL_CONSTANTS_IGNORED", "reasoning_label": "I treated the equal constants as a contradiction."},
        )
    return (
        {"code": "FORCED_SINGLE_SOLUTION", "candidate_response": "x=0", "reasoning_choice": "DIVIDED_ZERO_COEFFICIENT", "reasoning_label": "I divided by the remaining x coefficient even though it was zero."},
        {"code": "CONTRADICTION_CALLED_IDENTITY", "candidate_response": "ALL_REAL", "reasoning_choice": "UNEQUAL_CONSTANTS_IGNORED", "reasoning_label": "I treated unequal constants as if they matched."},
    )


@dataclass(frozen=True)
class Variant:
    family_code: str
    canonical_skill_code: str
    mode: str
    seed: int
    variant_id: str
    structure_code: str
    prompt: str
    answer_kind: str
    canonical_answer: str
    oracle: dict[str, Any]
    task_fingerprint: str
    first_step_choices: tuple[dict[str, Any], ...]
    misconception_signals: tuple[dict[str, Any], ...]
    socratic_questions: tuple[str, ...]
    guided_explanation: str

    def public_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "variant_id": self.variant_id,
            "family_code": self.family_code,
            "canonical_skill_code": self.canonical_skill_code,
            "mode": self.mode,
            "structure_code": self.structure_code,
            "answer_kind": self.answer_kind,
            "interaction_requirements": dict(ACCESSIBILITY),
            "mastery_credit": False,
            "runtime_activation": False,
        }
        if self.mode == "guided":
            payload.update(
                {
                    "stage": LEARNING_STAGES[0],
                    "guided_session_required": True,
                    "observation": {
                        "representation": FAMILY_METADATA[self.family_code]["representation"][0],
                        "prompt": "Notice the quantities, groups, and two complete sides before choosing an operation.",
                    },
                }
            )
        else:
            payload.update(
                {
                    "stage": "DIAGNOSE" if self.mode == "diagnostic" else "PRACTICE",
                    "prompt": self.prompt,
                    "response_fields": ["answer"],
                    "guided_support_available": False,
                }
            )
        return payload

    def response_is_correct(self, response: str) -> bool:
        if self.answer_kind == "EXACT_RATIONAL":
            return _parse_exact(response) == _parse_exact(self.canonical_answer)
        if self.answer_kind == "ERROR_CODE_AND_EXACT_RATIONAL":
            parsed = _parse_error_code_and_rational(response)
            return (
                parsed is not None
                and parsed == _parse_error_code_and_rational(self.canonical_answer)
            )
        return response.strip().upper() == self.canonical_answer.upper()

    def guided_repair(self, response: str, reasoning_choice: str | None) -> dict[str, Any]:
        if self.mode != "guided":
            return {"status": "SUPPORT_NOT_AVAILABLE"}
        matching = [
            signal
            for signal in self.misconception_signals
            if _responses_equal(signal["candidate_response"], response, self.answer_kind)
        ]
        if len(matching) != 1:
            return {"status": "NEUTRAL_RETRY", "reason": "UNMATCHED_OR_AMBIGUOUS"}
        signal = matching[0]
        if reasoning_choice != signal["reasoning_choice"]:
            return {"status": "NEUTRAL_RETRY", "reason": "EVIDENCE_NOT_CORROBORATED"}
        return {
            "status": "TARGETED_REPAIR",
            "misconception_code": signal["code"],
            "questions": list(self.socratic_questions),
            "explanation": self.guided_explanation,
            "worked_answer_revealed": False,
            "mastery_credit": False,
        }


def _responses_equal(left: str, right: str, answer_kind: str) -> bool:
    if answer_kind == "EXACT_RATIONAL":
        parsed_left, parsed_right = _parse_exact(left), _parse_exact(right)
        return parsed_left is not None and parsed_left == parsed_right
    if answer_kind == "ERROR_CODE_AND_EXACT_RATIONAL":
        parsed_left = _parse_error_code_and_rational(left)
        return parsed_left is not None and parsed_left == _parse_error_code_and_rational(right)
    return left.strip().upper() == right.strip().upper()


def _base_parameters(index: int) -> tuple[Fraction, int, int, int]:
    target = _unique_target(index)
    k = 2 + index % 5
    p = 1 + (index * 3) % 9
    q = (index * 7) % 17 - 8
    return target, k, p, q


def _build_equation_family(family: str, index: int) -> tuple[Any, ...]:
    x, k, p, q = _base_parameters(index)
    tag = index + 3
    context_domain: dict[str, Any] | None = None
    if family == "DISTRIBUTE_POSITIVE_ONE_SIDE":
        shift = q + tag
        coefficients = (Fraction(k), Fraction(k * p + shift), Fraction(0), Fraction(k) * x + k * p + shift)
        prompt = f"Solve exactly: {k}(x + {p}) {('+' if shift >= 0 else '-')} {abs(shift)} = {_fmt(coefficients[3])}."
        first = "Distribute to both terms inside the parentheses."
    elif family == "DISTRIBUTE_NEGATIVE_ONE_SIDE":
        shift = q + tag
        coefficients = (Fraction(-k), Fraction(k * p + shift), Fraction(0), Fraction(-k) * x + k * p + shift)
        prompt = f"Solve exactly: -{k}(x - {p}) {('+' if shift >= 0 else '-')} {abs(shift)} = {_fmt(coefficients[3])}."
        first = "Multiply both x and the constant by the outside negative factor."
    elif family == "COMBINE_LIKE_TERMS":
        m = 1 + index % 4
        coefficients = (Fraction(k + m), Fraction(q), Fraction(0), Fraction(k + m) * x + q)
        prompt = f"Solve exactly: {k}x + {m}x {('+' if q >= 0 else '-')} {abs(q)} = {_fmt(coefficients[3])}."
        first = "Combine the two like variable terms before isolating x."
    elif family == "VARIABLES_BOTH_SIDES":
        c = Fraction(1 + index % 3)
        a = c + k
        b = Fraction(q + tag)
        d = b + (a - c) * x
        coefficients = (a, b, c, d)
        prompt = f"Solve exactly: {_equation(coefficients)}."
        first = "Subtract the smaller variable term from both complete sides."
    elif family == "FRACTIONAL_COEFFICIENTS":
        denominator = (2, 3, 4, 5)[index % 4]
        a = Fraction(k, denominator)
        b = Fraction(q + tag, denominator)
        coefficients = (a, b, Fraction(0), a * x + b)
        prompt = f"Solve exactly without decimal approximation: {_equation(coefficients)}."
        first = "Clear or preserve the exact fraction by applying an equivalent operation to both sides."
    elif family == "NESTED_GROUPS":
        h = 1 + index % 3
        if h == k:
            h = h % 3 + 1
        a = Fraction(k - h)
        shift = q + tag
        b = Fraction(k * p + h * (p + 1) + shift)
        coefficients = (a, b, Fraction(0), a * x + b)
        prompt = f"Solve exactly: {k}(x + {p}) - {h}(x - {p + 1}) {('+' if shift >= 0 else '-')} {abs(shift)} = {_fmt(coefficients[3])}."
        first = "Distribute into both groups, then combine like terms."
    elif family == "IDENTITY_ALL_REAL":
        a = Fraction(1)
        b = Fraction(tag)
        coefficients = (a, b, a, b)
        prompt = f"Classify the solution set and justify it: {_equation(coefficients)}."
        first = "Compare the simplified variable coefficient and constant on both sides."
    elif family == "CONTRADICTION_NO_SOLUTION":
        a = Fraction(1)
        b = Fraction(tag)
        d = b + 1 + index % 4
        coefficients = (a, b, a, d)
        prompt = f"Classify the solution set and justify it: {_equation(coefficients)}."
        first = "Compare the simplified variable coefficient and constant on both sides."
    elif family == "PERIMETER_MODEL":
        # Geometry contexts cannot reuse the unrestricted rational target.
        x = Fraction(index + 6)
        offset = tag + 2
        width_offset = 1 + (index * 2) % 5
        length = x + offset
        width = x - width_offset
        perimeter = 2 * length + 2 * width
        assert length > 0 and width > 0 and perimeter > 0
        coefficients = (Fraction(4), Fraction(2 * offset - 2 * width_offset), Fraction(0), perimeter)
        prompt = f"A rectangle has length x + {offset} cm and width x - {width_offset} cm. Its perimeter is {_fmt(perimeter)} cm. Write the perimeter equation, solve for x, and verify both dimensions are positive."
        context_domain = {
            "kind": "RECTANGLE_DIMENSIONS",
            "length": _fmt(length),
            "width": _fmt(width),
            "perimeter": _fmt(perimeter),
            "strictly_positive": True,
        }
        first = "Represent the perimeter as two lengths plus two widths before simplifying."
    elif family == "COMPETING_PLANS_MODEL":
        # A number of uses is a nonnegative integer, not an unrestricted rational.
        x = Fraction(index + 1)
        r1 = 2 + index % 4
        r2 = r1 + k
        f2 = Fraction(tag + 30)
        f1 = f2 + (r2 - r1) * x
        assert x.denominator == 1 and x >= 0 and f1 >= 0 and f2 >= 0
        coefficients = (Fraction(r1), Fraction(f1), Fraction(r2), Fraction(f2))
        prompt = f"Plan A costs ${f1} plus ${r1} per use. Plan B costs ${_fmt(f2)} plus ${r2} per use. After how many uses do the totals match?"
        context_domain = {
            "kind": "DISCRETE_USE_COUNT",
            "use_count": _fmt(x),
            "plan_a_fixed": _fmt(f1),
            "plan_b_fixed": _fmt(f2),
            "nonnegative_integers": True,
        }
        first = "Set the two complete fixed-plus-rate expressions equal."
    else:
        raise KeyError(family)
    solution_class, answer = _classify(coefficients)
    oracle = {
        "coefficients": [_fmt(v) for v in coefficients],
        "solution_class": solution_class,
        "canonical_answer": answer,
        "substitution_left": None,
        "substitution_right": None,
    }
    if context_domain is not None:
        oracle["context_domain"] = context_domain
    if solution_class == "UNIQUE":
        value = _parse_exact(answer)
        assert value is not None
        a, b, c, d = coefficients
        oracle["substitution_left"] = _fmt(a * value + b)
        oracle["substitution_right"] = _fmt(c * value + d)
        signals = _unique_signals(value)
        answer_kind = "EXACT_RATIONAL"
    else:
        signals = _class_signals(solution_class)
        answer_kind = "SOLUTION_CLASS"
    return prompt, coefficients, answer_kind, answer, oracle, signals, first


def _build_error_analysis(index: int) -> tuple[Any, ...]:
    x, k, p, q = _base_parameters(index)
    shift = q + index + 3
    b = Fraction(k * p + shift)
    rhs = Fraction(k) * x + b
    coefficients = (Fraction(k), b, Fraction(0), rhs)
    correct_answer = f"STEP_1|x={_fmt(x)}"
    prompt = (
        f"A student solves {k}(x + {p}) {('+' if shift >= 0 else '-')} {abs(shift)} = {_fmt(rhs)}. "
        f"Step 1: {k}x + {p} {('+' if shift >= 0 else '-')} {abs(shift)} = {_fmt(rhs)}. "
        "Identify the first invalid step, then give the exact solution as STEP_1|x=value."
    )
    oracle = {"coefficients": [_fmt(v) for v in coefficients], "solution_class": "UNIQUE", "canonical_answer": correct_answer, "first_invalid_step": "STEP_1"}
    signals = (
        {"code": "DISTRIBUTED_TO_ONE_TERM", "candidate_response": f"NO_ERROR|x={_fmt(x)}", "reasoning_choice": "CONSTANT_NOT_MULTIPLIED", "reasoning_label": "I accepted the step without multiplying the constant by the outside factor."},
        {"code": "ERROR_STEP_MISLOCATED", "candidate_response": f"STEP_2|x={_fmt(x)}", "reasoning_choice": "CHECK_FIRST_CHANGED_LINE", "reasoning_label": "I inspected a later step before checking the first changed line."},
    )
    return prompt, coefficients, "ERROR_CODE_AND_EXACT_RATIONAL", correct_answer, oracle, signals, "Compare Step 1 term-by-term with a complete distribution."


def _build_class_compare(index: int) -> tuple[Any, ...]:
    _, k, p, q = _base_parameters(index)
    tag = index + 5
    unique_x = _unique_target(index)
    one = (Fraction(k + 1), Fraction(tag), Fraction(1), Fraction(tag) + k * unique_x)
    all_real = (Fraction(k), Fraction(k * p + q), Fraction(k), Fraction(k * p + q))
    none = (Fraction(k + 2), Fraction(tag + q), Fraction(k + 2), Fraction(tag + q + 1))
    equations = (one, all_real, none)
    prompt = "Classify A, B, and C as ONE, ALL_REAL, or NO_SOLUTION: " + "; ".join(
        f"{label}: {_equation(eq)}" for label, eq in zip("ABC", equations)
    )
    answer = "A=ONE|B=ALL_REAL|C=NO_SOLUTION"
    oracle = {"equations": [[_fmt(v) for v in eq] for eq in equations], "canonical_answer": answer, "solution_classes": ["ONE", "ALL_REAL", "NO_SOLUTION"]}
    signals = (
        {"code": "IDENTITY_CONTRADICTION_SWAPPED", "candidate_response": "A=ONE|B=NO_SOLUTION|C=ALL_REAL", "reasoning_choice": "CONSTANT_COMPARISON", "reasoning_label": "I did not compare the constants after variable terms canceled."},
        {"code": "FORCED_THREE_SINGLE_SOLUTIONS", "candidate_response": "A=ONE|B=ONE|C=ONE", "reasoning_choice": "ZERO_COEFFICIENT_DIVISION", "reasoning_label": "I forced a single answer after the variable coefficient became zero."},
    )
    fingerprint = "|".join(_affine_fingerprint(eq) for eq in equations)
    return prompt, equations[0], "CLASSIFICATION_TRIPLE", answer, oracle, signals, "Simplify each equation only until you can compare its remaining coefficient and constant invariants.", fingerprint


def create_variant(family_code: str, *, seed: int, mode: str) -> Variant:
    if family_code not in FAMILIES:
        raise ValueError(f"unknown family: {family_code}")
    index = _seed_index(seed, mode)
    if family_code == "ERROR_ANALYSIS_FIRST_INVALID_STEP":
        prompt, coefficients, answer_kind, answer, oracle, signals, first = _build_error_analysis(index)
        fingerprint = _affine_fingerprint(coefficients)
    elif family_code == "SOLUTION_CLASS_COMPARE":
        prompt, coefficients, answer_kind, answer, oracle, signals, first, fingerprint = _build_class_compare(index)
    else:
        prompt, coefficients, answer_kind, answer, oracle, signals, first = _build_equation_family(family_code, index)
        fingerprint = _affine_fingerprint(coefficients)
    digest = hashlib.sha256(f"grade8-multistep-r1|{family_code}|{mode}|{seed}".encode()).hexdigest()
    correct_step = {"id": "PRESERVE_EQUALITY", "label": first, "correct": True}
    distractor = {"id": "CHANGE_ONE_SIDE", "label": "Apply the operation to only the side containing x.", "correct": False}
    meta = FAMILY_METADATA[family_code]
    return Variant(
        family_code=family_code,
        canonical_skill_code=CANONICAL_SKILL,
        mode=mode,
        seed=seed,
        variant_id=digest[:24],
        structure_code=meta["structure"],
        prompt=prompt,
        answer_kind=answer_kind,
        canonical_answer=answer,
        oracle=oracle,
        task_fingerprint=f"{family_code}|{fingerprint}",
        first_step_choices=(correct_step, distractor),
        misconception_signals=signals,
        socratic_questions=(
            "What changed on the left side, and what same change preserves equality on the complete right side?",
            "After simplifying, what do the variable coefficient and constant tell you about the solution class?",
        ),
        guided_explanation=(
            "An equation stays equivalent only when each operation applies to both complete sides. "
            "Distribute to every term, combine like terms, and interpret a zero remaining x coefficient "
            "by comparing the constants instead of forcing division by zero."
        ),
    )


def create_unhinted_transfer(source: Variant) -> Variant:
    target_index = (FAMILIES.index(source.family_code) + 1) % len(FAMILIES)
    target_family = FAMILIES[target_index]
    local = source.seed if source.seed in PRIMARY_SEEDS else source.seed - TRANSFER_SEEDS.start
    for offset in range(64):
        seed = TRANSFER_SEEDS.start + ((local + offset) % 16)
        target = create_variant(target_family, seed=seed, mode="independent")
        if target.task_fingerprint != source.task_fingerprint and target.canonical_answer != source.canonical_answer:
            return target
    raise ArithmeticError("reviewed transfer seed band exhausted")



@dataclass(frozen=True)
class LearningState:
    source: Variant
    stage: str
    practice_response: str | None = None
    transfer_variant: Variant | None = None
    diagnosis_route: str | None = None
    feedback_code: str | None = None
    complete: bool = False


def start_guided_learning(variant: Variant) -> LearningState:
    if variant.mode != "guided":
        raise ValueError("the eight-stage teaching flow is available only in guided mode")
    return LearningState(source=variant, stage=LEARNING_STAGES[0])


def _correct_first_step_id(variant: Variant) -> str:
    matches = [item["id"] for item in variant.first_step_choices if item.get("correct") is True]
    if len(matches) != 1:
        raise ValueError("variant must have exactly one reviewed first-step choice")
    return matches[0]


def _retry(state: LearningState, feedback_code: str, *, diagnosis_route: str | None = None) -> LearningState:
    return replace(
        state,
        feedback_code=feedback_code,
        diagnosis_route=state.diagnosis_route if diagnosis_route is None else diagnosis_route,
    )


def _advance(state: LearningState, stage: str, **changes: Any) -> LearningState:
    return replace(state, stage=stage, feedback_code=None, **changes)


def learning_stage_payload(state: LearningState) -> dict[str, Any]:
    if state.complete:
        return {
            "stage": COMPLETE_STAGE,
            "complete": True,
            "mastery_credit": False,
            "feedback_code": state.feedback_code,
        }
    variant = state.source
    payload: dict[str, Any] = {
        "variant_id": variant.variant_id,
        "family_code": variant.family_code,
        "stage": state.stage,
        "complete": False,
        "mastery_credit": False,
        "feedback_code": state.feedback_code,
        "interaction_requirements": dict(ACCESSIBILITY),
    }
    if state.stage == "OBSERVE":
        payload["observation"] = {
            "representation": FAMILY_METADATA[variant.family_code]["representation"][0],
            "prompt": "Notice the quantities, groups, and two complete sides.",
            "response_choices": [
                {
                    "id": "STRUCTURE_NOTICED",
                    "label": "I can identify the groups and both complete sides without solving yet.",
                }
            ],
        }
    elif state.stage == "PREDICT":
        payload["prompt"] = variant.prompt
        payload["first_step_choices"] = [
            {"id": item["id"], "label": item["label"]} for item in variant.first_step_choices
        ]
    elif state.stage == "MANIPULATE":
        payload["prompt"] = variant.prompt
        payload["operation_choices"] = [
            {"id": item["id"], "label": item["label"]} for item in variant.first_step_choices
        ]
        payload["required_side_labels"] = ["LEFT_COMPLETE_SIDE", "RIGHT_COMPLETE_SIDE"]
    elif state.stage == "EXPLAIN":
        payload["claim_choices"] = [
            {
                "id": "SAME_OPERATION_BOTH_COMPLETE_SIDES",
                "label": "The same operation applies to both complete sides, so equality is preserved.",
            },
            {
                "id": "MOVE_AND_CHANGE_SIGN",
                "label": "A term can move across the equals sign and change sign by itself.",
            },
            {
                "id": "CHANGE_ONLY_X_SIDE",
                "label": "Only the side containing x needs to change.",
            },
        ]
    elif state.stage == "PRACTICE":
        payload.update({"prompt": variant.prompt, "answer_kind": variant.answer_kind})
    elif state.stage == "DIAGNOSE":
        if variant.response_is_correct(state.practice_response or ""):
            payload["readiness_choices"] = [
                {
                    "id": "READY_UNHINTED",
                    "label": "I checked my answer and am ready for an unhinted different structure.",
                }
            ]
        elif state.diagnosis_route is None:
            payload["reasoning_choices"] = [
                {"id": item["reasoning_choice"], "label": item["reasoning_label"]}
                for item in variant.misconception_signals
            ]
            payload["prompt"] = "Choose the reasoning that best matches the work you actually did."
        else:
            payload["repair"] = {
                "misconception_code": state.diagnosis_route,
                "questions": list(variant.socratic_questions),
                "explanation": variant.guided_explanation,
                "worked_answer_revealed": False,
                "corrected_response_required": True,
            }
    elif state.stage == "TRANSFER":
        transfer = state.transfer_variant or create_unhinted_transfer(variant)
        payload["transfer"] = transfer.public_payload()
        payload["transfer"]["stage"] = "TRANSFER"
    elif state.stage == "VERIFY":
        payload.update(
            {
                "prompt": variant.prompt,
                "answer_kind": variant.answer_kind,
                "verification_fields": (
                    ["answer", "substitution_left", "substitution_right"]
                    if variant.answer_kind == "EXACT_RATIONAL"
                    else ["answer", "verification_claim"]
                ),
            }
        )
    else:
        raise ValueError(f"unsupported learning stage: {state.stage}")
    return payload


def advance_guided_learning(state: LearningState, evidence: dict[str, Any]) -> LearningState:
    if state.complete:
        return _retry(state, "ALREADY_COMPLETE")
    if not isinstance(evidence, dict):
        return _retry(state, "MALFORMED_EVIDENCE")
    variant = state.source
    if state.stage == "OBSERVE":
        if evidence.get("observation_choice") != "STRUCTURE_NOTICED":
            return _retry(state, "OBSERVATION_REQUIRED")
        return _advance(state, "PREDICT")
    if state.stage == "PREDICT":
        if evidence.get("first_step_id") != _correct_first_step_id(variant):
            return _retry(state, "PREDICTION_NOT_EQUALITY_PRESERVING")
        return _advance(state, "MANIPULATE")
    if state.stage == "MANIPULATE":
        sides = evidence.get("applied_to")
        if (
            evidence.get("operation_choice") != _correct_first_step_id(variant)
            or not isinstance(sides, list)
            or set(sides) != {"LEFT_COMPLETE_SIDE", "RIGHT_COMPLETE_SIDE"}
            or len(sides) != 2
        ):
            return _retry(state, "BOTH_COMPLETE_SIDES_REQUIRED")
        return _advance(state, "EXPLAIN")
    if state.stage == "EXPLAIN":
        if evidence.get("claim_choice") != "SAME_OPERATION_BOTH_COMPLETE_SIDES":
            return _retry(state, "EQUALITY_EXPLANATION_REQUIRED")
        return _advance(state, "PRACTICE")
    if state.stage == "PRACTICE":
        response = evidence.get("answer")
        if not isinstance(response, str) or not response.strip():
            return _retry(state, "PRACTICE_RESPONSE_REQUIRED")
        return _advance(state, "DIAGNOSE", practice_response=response)
    if state.stage == "DIAGNOSE":
        if variant.response_is_correct(state.practice_response or ""):
            if evidence.get("readiness_choice") != "READY_UNHINTED":
                return _retry(state, "READINESS_CONFIRMATION_REQUIRED")
            transfer = create_unhinted_transfer(variant)
            return _advance(state, "TRANSFER", transfer_variant=transfer)
        if state.diagnosis_route is not None:
            corrected = evidence.get("corrected_response")
            if not isinstance(corrected, str) or not variant.response_is_correct(corrected):
                return _retry(state, "TARGETED_REPAIR_STILL_REQUIRED")
            transfer = create_unhinted_transfer(variant)
            return _advance(state, "TRANSFER", transfer_variant=transfer)
        reasoning = evidence.get("reasoning_choice")
        repair = variant.guided_repair(state.practice_response or "", reasoning)
        if repair["status"] != "TARGETED_REPAIR":
            return _retry(state, "DIAGNOSIS_NOT_CORROBORATED")
        corrected = evidence.get("corrected_response")
        if isinstance(corrected, str) and variant.response_is_correct(corrected):
            transfer = create_unhinted_transfer(variant)
            return _advance(
                state,
                "TRANSFER",
                transfer_variant=transfer,
                diagnosis_route=repair["misconception_code"],
            )
        return _retry(
            state,
            "TARGETED_REPAIR_REQUIRED",
            diagnosis_route=repair["misconception_code"],
        )
    if state.stage == "TRANSFER":
        transfer = state.transfer_variant
        if transfer is None:
            return _retry(state, "TRANSFER_NOT_BOUND")
        if evidence.get("variant_id") != transfer.variant_id:
            return _retry(state, "TRANSFER_ID_MISMATCH")
        response = evidence.get("answer")
        if not isinstance(response, str) or not transfer.response_is_correct(response):
            return _retry(state, "TRANSFER_RESPONSE_INCORRECT")
        return _advance(state, "VERIFY")
    if state.stage == "VERIFY":
        response = evidence.get("answer")
        if not isinstance(response, str) or not variant.response_is_correct(response):
            return _retry(state, "ORIGINAL_RESPONSE_INCORRECT")
        if variant.answer_kind == "EXACT_RATIONAL":
            submitted_left = _parse_exact(evidence.get("substitution_left"))
            submitted_right = _parse_exact(evidence.get("substitution_right"))
            expected_left = _parse_exact(variant.oracle.get("substitution_left"))
            expected_right = _parse_exact(variant.oracle.get("substitution_right"))
            if (
                submitted_left is None
                or submitted_right is None
                or expected_left is None
                or expected_right is None
                or submitted_left != expected_left
                or submitted_right != expected_right
                or submitted_left != submitted_right
            ):
                return _retry(state, "SUBSTITUTION_DOES_NOT_VERIFY_ORIGINAL")
        elif evidence.get("verification_claim") != "CHECKED_ORIGINAL_STRUCTURE":
            return _retry(state, "STRUCTURE_VERIFICATION_REQUIRED")
        return replace(
            state,
            stage=COMPLETE_STAGE,
            complete=True,
            feedback_code=None,
        )
    raise ValueError(f"unsupported learning stage: {state.stage}")


def create_pack(*, seeds_per_family_mode: int = 16) -> dict[str, Any]:
    if type(seeds_per_family_mode) is not int or not 1 <= seeds_per_family_mode <= 16:
        raise ValueError("seeds_per_family_mode must be an integer in 1..16")
    variants = [
        create_variant(family, seed=seed, mode=mode)
        for family in FAMILIES
        for mode in MODES
        for seed in range(seeds_per_family_mode)
    ]
    return {
        "schema": "MIHUR_DRAFT_GRADE8_MULTISTEP_EQUATIONS_R1",
        "status": "DRAFT_UNVERIFIED",
        "runtime_activation": False,
        "canonical_skill_code": CANONICAL_SKILL,
        "mapping_status": "PROVISIONAL_NOT_ACCEPTED",
        "family_count": len(FAMILIES),
        "variants": [variant.public_payload() for variant in variants],
    }
