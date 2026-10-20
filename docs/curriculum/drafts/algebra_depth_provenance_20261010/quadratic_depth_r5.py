"""Draft-only deterministic quadratic reasoning depth for the existing W2 package.

This module is deliberately outside ``app``.  It is content evidence only: it does
not register a taxonomy identity, seed a database, select learner problems, score
responses, or write attempts/mastery.  Exact rational values are serialized as
``numerator/denominator`` strings so a separate reviewer can reconstruct them.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Callable
from fractions import Fraction

PACKAGE_ID = "W2-G9-QUADRATIC-PATTERNS"
REVISION = "G9_DEPTH_R5_2026-10-18"
CANONICAL_CANDIDATE = "MATH.F.QUADRATIC.INTERPRET"
CANONICAL_APPROVAL = "UNKNOWN_NOT_AUTHORITATIVE"
MODES = frozenset({"diagnostic", "guided", "independent", "mastery"})

STANDARD_SUBSTITUTION = "QUAD.STANDARD.EXACT_SUBSTITUTION"
FACTORED_ROOTS = "QUAD.FACTORED.ROOTS_VERIFY"
VERTEX_SYMMETRY = "QUAD.VERTEX.SYMMETRY"
SQUARE_ROOT_BRANCHES = "QUAD.SQUARE_ROOT.PLUS_MINUS"
NO_REAL_VERTEX = "QUAD.VERTEX.NO_REAL"
TABLE_TO_RULE = "QUAD.TABLE.SECOND_DIFFERENCE_RULE"
FORM_RECONCILIATION = "QUAD.FORMS.RECONCILE_FEATURES"

FAMILY_ORDER = (
    STANDARD_SUBSTITUTION,
    FACTORED_ROOTS,
    VERTEX_SYMMETRY,
    SQUARE_ROOT_BRANCHES,
    NO_REAL_VERTEX,
    TABLE_TO_RULE,
    FORM_RECONCILIATION,
)


def _validate(seed: int, mode: str) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if mode not in MODES:
        raise ValueError(f"unsupported mode: {mode}")


def _rng(seed: int, mode: str, family: str) -> random.Random:
    _validate(seed, mode)
    digest = hashlib.sha256(
        f"{PACKAGE_ID}|{REVISION}|{mode}|{family}|{seed}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _q(value: Fraction | int) -> str:
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _record(
    *,
    seed: int,
    mode: str,
    family: str,
    structure: str,
    prompt: str,
    public_data: dict,
    response_schema: tuple[str, ...],
    oracle: dict,
    misconceptions: dict[str, dict],
) -> dict:
    return {
        "package_id": PACKAGE_ID,
        "revision": REVISION,
        "variant_id": f"{PACKAGE_ID}:{REVISION}:{mode}:{family}:{seed}",
        "mode": mode,
        "family": family,
        "structure": structure,
        "canonical_candidate": CANONICAL_CANDIDATE,
        "canonical_approval": CANONICAL_APPROVAL,
        "prompt": prompt,
        "public_data": public_data,
        "response_schema": list(response_schema),
        "oracle_teacher_only": oracle,
        "misconceptions_teacher_only": misconceptions,
    }


def public_payload(record: dict) -> dict:
    """Return only fields allowed before an independent response is submitted."""

    return {
        key: value
        for key, value in record.items()
        if key not in {"oracle_teacher_only", "misconceptions_teacher_only"}
    }


def guided_misconception_question(record: dict, misconception_code: str) -> dict:
    """Return one Socratic follow-up after a trusted guided-mode classification.

    This content helper deliberately does not classify a learner response.  A
    future trusted scorer may select a misconception code and request the
    matching question, but only for a record generated in ``guided`` mode.
    Submitted misconception exemplars and exact oracles stay teacher-only.
    """

    if not isinstance(record, dict):
        raise TypeError("record must be a dictionary")
    if record.get("mode") != "guided":
        raise ValueError("guided misconception questions require guided mode")
    if not isinstance(misconception_code, str) or not misconception_code:
        raise TypeError("misconception_code must be a nonempty string")

    misconceptions = record.get("misconceptions_teacher_only")
    if not isinstance(misconceptions, dict):
        raise TypeError("record is missing misconception evidence")
    try:
        misconception = misconceptions[misconception_code]
    except KeyError as exc:
        raise ValueError(f"unsupported misconception code: {misconception_code}") from exc
    if not isinstance(misconception, dict):
        raise TypeError("misconception evidence must be a dictionary")
    question = misconception.get("socratic_probe")
    if not isinstance(question, str) or not question.endswith("?"):
        raise ValueError("misconception evidence is missing a Socratic question")

    return {
        "variant_id": record["variant_id"],
        "mode": "guided",
        "family": record["family"],
        "misconception_code": misconception_code,
        "socratic_question": question,
        "return_to_response_schema": list(record["response_schema"]),
        "next_action": "REVISE_AND_RESUBMIT_WITHOUT_ORACLE_DISCLOSURE",
    }


def _standard_substitution(seed: int, mode: str) -> dict:
    rng = _rng(seed, mode, STANDARD_SUBSTITUTION)
    while True:
        a = rng.choice((-3, -2, -1, 1, 2, 3))
        b = rng.randint(-7, 7)
        c = rng.randint(-9, 9)
        x = Fraction(rng.randint(-9, 9), rng.choice((1, 2, 3, 4)))
        exact = a * x * x + b * x + c
        forgot_square = a * x + b * x + c
        if x not in (0, 1) and forgot_square != exact:
            break
    return _record(
        seed=seed,
        mode=mode,
        family=STANDARD_SUBSTITUTION,
        structure="standard-form exact rational evaluation",
        prompt=(
            f"For f(x)={a}x^2+({b})x+({c}), evaluate f({_q(x)}). "
            "Show the squared input and the final exact value."
        ),
        public_data={"a": a, "b": b, "c": c, "x": _q(x)},
        response_schema=("squared_input", "exact_value", "substitution_check"),
        oracle={
            "squared_input": _q(x * x),
            "exact_value": _q(exact),
            "substitution_check": _q(a * x * x + b * x + c),
        },
        misconceptions={
            "QUAD.EVAL.FORGET_SQUARE": {
                "submitted": {
                    "squared_input": _q(x),
                    "exact_value": _q(forgot_square),
                    "substitution_check": _q(forgot_square),
                },
                "socratic_probe": "What is the value of the entire parenthesized input squared before multiplying by a?",
            }
        },
    )


def _factored_roots(seed: int, mode: str) -> dict:
    rng = _rng(seed, mode, FACTORED_ROOTS)
    while True:
        r1, r2 = sorted(rng.sample(range(-8, 9), 2))
        if r1 and r2 and sorted((-r1, -r2)) != [r1, r2]:
            break
    a = rng.choice((-3, -2, -1, 1, 2, 3))
    wrong = sorted((-r1, -r2))

    def value_at(x: int) -> int:
        return a * (x - r1) * (x - r2)

    return _record(
        seed=seed,
        mode=mode,
        family=FACTORED_ROOTS,
        structure="factored-form roots plus independent substitution totals",
        prompt=(
            f"Solve {a}(x-({r1}))(x-({r2}))=0. Give the ordered real roots "
            "and verify each by substituting it into the complete left side."
        ),
        public_data={"a": a, "r1_factor_parameter": r1, "r2_factor_parameter": r2},
        response_schema=("ordered_roots", "left_total_at_first", "left_total_at_second"),
        oracle={
            "ordered_roots": [r1, r2],
            "left_total_at_first": value_at(r1),
            "left_total_at_second": value_at(r2),
        },
        misconceptions={
            "QUAD.ROOT_SIGN": {
                "submitted": {
                    "ordered_roots": wrong,
                    "left_total_at_first": value_at(wrong[0]),
                    "left_total_at_second": value_at(wrong[1]),
                },
                "socratic_probe": "If x-r=0, which operation isolates x, and does the proposed value make that factor zero?",
            }
        },
    )


def _vertex_symmetry(seed: int, mode: str) -> dict:
    rng = _rng(seed, mode, VERTEX_SYMMETRY)
    a = rng.choice((-4, -3, -2, -1, 1, 2, 3, 4))
    h = rng.choice(tuple(x for x in range(-7, 8) if x))
    # Keep the vertical shift's sign opposite the leading coefficient so the
    # common "k controls opening" response is always observably distinct.
    k = rng.randint(-9, -1) if a > 0 else rng.randint(1, 9)
    distance = rng.randint(1, 5)
    symmetric_value = a * distance**2 + k
    return _record(
        seed=seed,
        mode=mode,
        family=VERTEX_SYMMETRY,
        structure="vertex-form feature and symmetry reconciliation",
        prompt=(
            f"For y={a}(x-({h}))^2+({k}), identify the vertex and axis, state "
            f"the opening direction, then compare the outputs at x={h-distance} and x={h+distance}."
        ),
        public_data={"a": a, "h": h, "k": k, "distance": distance},
        response_schema=("vertex", "axis", "opening", "left_value", "right_value"),
        oracle={
            "vertex": [h, k],
            "axis": f"x={h}",
            "opening": "up" if a > 0 else "down",
            "left_value": symmetric_value,
            "right_value": symmetric_value,
        },
        misconceptions={
            "QUAD.VERTEX.SIGN": {
                "submitted": {
                    "vertex": [-h, k],
                    "axis": f"x={-h}",
                    "opening": "up" if a > 0 else "down",
                    "left_value": symmetric_value,
                    "right_value": symmetric_value,
                },
                "socratic_probe": "Which x makes the squared factor x-h equal zero?",
            },
            "QUAD.OPENING.USES_K": {
                "submitted": {
                    "vertex": [h, k],
                    "axis": f"x={h}",
                    "opening": "up" if k > 0 else "down",
                    "left_value": symmetric_value,
                    "right_value": symmetric_value,
                },
                "socratic_probe": "Which coefficient multiplies the squared distance and therefore controls whether values rise or fall from the vertex?",
            },
        },
    )


def _square_root_branches(seed: int, mode: str) -> dict:
    rng = _rng(seed, mode, SQUARE_ROOT_BRANCHES)
    a = rng.randint(1, 5)
    h = rng.randint(-8, 8)
    step = rng.randint(2, 8)
    total = a * step**2
    roots = sorted((h - step, h + step))
    return _record(
        seed=seed,
        mode=mode,
        family=SQUARE_ROOT_BRANCHES,
        structure="square-root equation with two real branches",
        prompt=(
            f"Solve {a}(x-({h}))^2={total}. Give every real solution and "
            "verify both in the original equation."
        ),
        public_data={"a": a, "h": h, "right_total": total},
        response_schema=("ordered_real_solutions", "left_totals"),
        oracle={"ordered_real_solutions": roots, "left_totals": [total, total]},
        misconceptions={
            "QUAD.LOST_PLUS_MINUS": {
                "submitted": {
                    "ordered_real_solutions": [roots[1]],
                    "left_totals": [total],
                },
                "socratic_probe": "Which two numbers have the same positive square, and how do both shift from the axis x=h?",
            }
        },
    )


def _no_real_vertex(seed: int, mode: str) -> dict:
    rng = _rng(seed, mode, NO_REAL_VERTEX)
    a = rng.randint(1, 5)
    h = rng.randint(-8, 8)
    k = rng.randint(1, 12)
    return _record(
        seed=seed,
        mode=mode,
        family=NO_REAL_VERTEX,
        structure="vertex-form real-solution classification",
        prompt=(
            f"Classify the real solutions of {a}(x-({h}))^2+{k}=0. "
            "Justify the classification using the minimum possible left-side value."
        ),
        public_data={"a": a, "h": h, "k": k},
        response_schema=("classification", "minimum_left_value", "reason"),
        oracle={
            "classification": "no real solutions",
            "minimum_left_value": k,
            "reason": f"a square is nonnegative, so the left side is at least {k}",
        },
        misconceptions={
            "QUAD.NEGATIVE_RADICAND.ABS_VALUE": {
                "submitted": {
                    "classification": "two real solutions",
                    "minimum_left_value": -k,
                    "reason": "replace the negative radicand with its absolute value",
                },
                "socratic_probe": "Can a real square be negative, and what is the smallest value the full left side can reach?",
            }
        },
    )


def _table_to_rule(seed: int, mode: str) -> dict:
    rng = _rng(seed, mode, TABLE_TO_RULE)
    a = rng.choice((-3, -2, -1, 1, 2, 3))
    b = rng.randint(-6, 6)
    c = rng.randint(-8, 8)
    xs = [-1, 0, 1, 2]
    ys = [a * x**2 + b * x + c for x in xs]
    first = [ys[i + 1] - ys[i] for i in range(3)]
    second = [first[i + 1] - first[i] for i in range(2)]
    next_value = a * 3**2 + b * 3 + c
    return _record(
        seed=seed,
        mode=mode,
        family=TABLE_TO_RULE,
        structure="equal-step table to second differences and symbolic rule",
        prompt=(
            f"For the equal-step table {list(zip(xs, ys))}, show both difference rows, "
            "determine ax^2+bx+c, and predict the value at x=3."
        ),
        public_data={"x_values": xs, "y_values": ys, "x_step": 1},
        response_schema=("first_differences", "second_differences", "coefficients", "value_at_3"),
        oracle={
            "first_differences": first,
            "second_differences": second,
            "coefficients": [a, b, c],
            "value_at_3": next_value,
        },
        misconceptions={
            "QUAD.FIRST_DIFFERENCE_AS_COEFFICIENT": {
                "submitted": {
                    "first_differences": first,
                    "second_differences": second,
                    "coefficients": [second[0], first[0], ys[1]],
                    "value_at_3": ys[-1] + first[-1],
                },
                "socratic_probe": "For unit-spaced x-values, what is the relationship between the constant second difference and 2a?",
            }
        },
    )


def _form_reconciliation(seed: int, mode: str) -> dict:
    rng = _rng(seed, mode, FORM_RECONCILIATION)
    parity = rng.choice((0, 1))
    candidates = [x for x in range(-8, 9) if x % 2 == parity]
    while True:
        r1, r2 = sorted(rng.sample(candidates, 2))
        if r1 and r2 and sorted((-r1, -r2)) != [r1, r2]:
            break
    a = rng.choice((-3, -2, -1, 1, 2, 3))
    b = -a * (r1 + r2)
    c = a * r1 * r2
    h = (r1 + r2) // 2
    k = a * (h - r1) * (h - r2)
    wrong_roots = sorted((-r1, -r2))
    return _record(
        seed=seed,
        mode=mode,
        family=FORM_RECONCILIATION,
        structure="factored-standard-vertex form equivalence and feature evidence",
        prompt=(
            f"A quadratic is written as {a}(x-({r1}))(x-({r2})). "
            "Give its standard and vertex forms, roots, vertex, and independently "
            "verify that all three forms have the same value at x=0."
        ),
        public_data={"a": a, "r1": r1, "r2": r2, "verification_input": 0},
        response_schema=("standard_coefficients", "vertex_form", "roots", "vertex", "three_totals_at_zero"),
        oracle={
            "standard_coefficients": [a, b, c],
            "vertex_form": {"a": a, "h": h, "k": k},
            "roots": [r1, r2],
            "vertex": [h, k],
            "three_totals_at_zero": [c, c, c],
        },
        misconceptions={
            "QUAD.FACTOR_SIGN_AND_MIDDLE_TERM": {
                "submitted": {
                    "standard_coefficients": [a, a * (r1 + r2), c],
                    "vertex_form": {"a": a, "h": -h, "k": k},
                    "roots": wrong_roots,
                    "vertex": [-h, k],
                    "three_totals_at_zero": [c, c, c],
                },
                "socratic_probe": "Expand only the two x-terms first: what sign does their sum have, and which x makes each original factor zero?",
            }
        },
    )


BUILDERS: dict[str, Callable[[int, str], dict]] = {
    STANDARD_SUBSTITUTION: _standard_substitution,
    FACTORED_ROOTS: _factored_roots,
    VERTEX_SYMMETRY: _vertex_symmetry,
    SQUARE_ROOT_BRANCHES: _square_root_branches,
    NO_REAL_VERTEX: _no_real_vertex,
    TABLE_TO_RULE: _table_to_rule,
    FORM_RECONCILIATION: _form_reconciliation,
}


def generate(family: str, seed: int, mode: str) -> dict:
    """Generate one exact draft content record from a named family."""

    try:
        builder = BUILDERS[family]
    except KeyError as exc:
        raise ValueError(f"unsupported family: {family}") from exc
    return builder(seed, mode)


def generate_fresh_transfer(
    source_family: str,
    seed: int,
    source_mode: str,
    target_mode: str,
) -> dict:
    """Choose a different family and require an independent verification exit."""

    _validate(seed, source_mode)
    _validate(seed, target_mode)
    if target_mode != "independent":
        raise ValueError("fresh transfer verification must use independent mode")
    if source_family not in BUILDERS:
        raise ValueError(f"unsupported source family: {source_family}")
    source_index = FAMILY_ORDER.index(source_family)
    offset = 1 + (
        _rng(seed, source_mode, "TRANSFER_SELECTOR").randrange(len(FAMILY_ORDER) - 1)
    )
    target_family = FAMILY_ORDER[(source_index + offset) % len(FAMILY_ORDER)]
    record = generate(target_family, seed + 1_000_003, target_mode)
    record["transfer_from_family"] = source_family
    record["transfer_source_mode"] = source_mode
    record["transfer_target_mode"] = target_mode
    record["transfer_contract"] = "DIFFERENT_MATHEMATICAL_STRUCTURE_SAME_CANDIDATE_SKILL"
    record["verification_contract"] = "INDEPENDENT_HINT_FREE_EXIT"
    return record
