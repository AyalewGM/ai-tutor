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
STRUCTURES = {
    family: ("VARIABLE_TERM_FIRST", "CONSTANT_TERM_FIRST", "SIDES_REVERSED")
    for family in FAMILIES
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
    """Return prompt, displayed/base coefficients, repair metadata and structure."""
    if family == "TWO_STEP_SIGNED_RATIONAL":
        x = _noninteger(rng)
        a = x.denominator * rng.choice((-1, 1)) * rng.randint(1, 4)
        b = _nonzero(rng, -15, 15)
        d = a * x + b
        structure = rng.choice(STRUCTURES[family])
        if structure == "VARIABLE_TERM_FIRST":
            prompt = f"Solve {a}x {b:+d} = {d}."
            displayed = (Fraction(a), Fraction(b), Fraction(0), Fraction(d))
        elif structure == "CONSTANT_TERM_FIRST":
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
            structure,
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
        structure = rng.choice(STRUCTURES[family])
        coefficient = Fraction(a, denominator)
        if structure == "VARIABLE_TERM_FIRST":
            prompt = f"Solve ({a}/{denominator})x {b:+d} = {d}."
            displayed = (coefficient, Fraction(b), Fraction(0), Fraction(d))
        elif structure == "CONSTANT_TERM_FIRST":
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
            structure,
        )
    if family == "MULTISTEP_NEGATIVE_DISTRIBUTION":
        x = _noninteger(rng)
        k = x.denominator * rng.randint(1, 4)
        b = _nonzero(rng, -9, 9)
        c = rng.randint(-12, 12)
        target = -k * (x - b) + c
        structure = rng.choice(STRUCTURES[family])
        if structure == "VARIABLE_TERM_FIRST":
            prompt = f"Solve -{k}(x - ({b})) + ({c}) = {target}."
            displayed = (Fraction(-k), Fraction(k * b + c), Fraction(0), Fraction(target))
        elif structure == "CONSTANT_TERM_FIRST":
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
            structure,
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
        structure = rng.choice(STRUCTURES[family])
        if structure == "VARIABLE_TERM_FIRST":
            prompt = f"Solve {a}x {b:+d} = {c}x {int(d):+d}."
            displayed = (Fraction(a), Fraction(b), Fraction(c), Fraction(d))
        elif structure == "CONSTANT_TERM_FIRST":
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
            structure,
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
        signals.append(
            {
                "misconception_code": code,
                "candidate_response": f"x={_fmt(wrong)}",
                "confirmation_probe_for_author_review": repair["confirmation"],
                "confirmation_oracle_for_author_review": repair["oracle"],
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
        structure,
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
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "family": family,
                "structure_id": structure,
                "coefficients": coefficients,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return {
        "candidate_family": family,
        "canonical_skill_hint": SKILLS[family],
        "mode": mode,
        "variant_id": hashlib.sha256(f"{family}|{mode}|{seed}".encode()).hexdigest()[:24],
        "task_fingerprint": fingerprint,
        "structure_id": structure,
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
            "requires_changed_structure_id": True,
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
    """Select a same-target, structurally changed task; never award runtime credit."""
    if target_mode not in ("INDEPENDENT", "MASTERY"):
        raise ValueError("Transfer must be independent or mastery mode")
    family = source["candidate_family"]
    for attempt in range(2048):
        seed = f"transfer|{source['variant_id']}|{attempt}"
        target = create_candidate(family, seed=seed, mode=target_mode)
        if target["structure_id"] == source["structure_id"]:
            continue
        if target["task_fingerprint"] == source["task_fingerprint"]:
            continue
        if target["canonical_answer"] == source["canonical_answer"]:
            continue
        return {
            "source_variant_id": source["variant_id"],
            "target_family": family,
            "target_mode": target_mode,
            "source_structure_id": source["structure_id"],
            "target_structure_id": target["structure_id"],
            "structure_changed": True,
            "task_fingerprint_changed": True,
            "answer_changed": True,
            "hints_allowed": False,
            "hinted_success_counts_as_independent": False,
            "runtime_credit_authorized": False,
            "learner_task": learner_projection(target),
            "private_exact_oracle_for_review": target["canonical_answer"],
            "private_target_fingerprint_for_review": target["task_fingerprint"],
        }
    raise ArithmeticError("Structurally distinct transfer budget exhausted")


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
        "schema": "MIHUR_DRAFT_RATIONAL_EQUATION_CANDIDATES_V2",
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
        "hinted_success_counts_as_independent": False,
        "transfer_requires_changed_structure": True,
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
