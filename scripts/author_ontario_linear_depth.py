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


def _case(family: str, rng: random.Random) -> tuple[str, tuple[Fraction, Fraction, Fraction, Fraction], str, str, tuple[str, str], Fraction]:
    """Return prompt, expanded (Lx,L0,Rx,R0), code, rationale, hints, distractor."""
    if family == "TWO_STEP_SIGNED_RATIONAL":
        x = _noninteger(rng)
        a = x.denominator * rng.choice((-1, 1)) * rng.randint(1, 4)
        b = _nonzero(rng, -15, 15)
        c = a * x + b
        return (
            f"Solve {a}x {b:+d} = {c}.",
            (Fraction(a), Fraction(b), Fraction(0), Fraction(c)),
            "EQ.OMIT_CONSTANT",
            "Subtract the constant on BOTH sides before dividing by the signed coefficient.",
            ("What operation preserves equality while removing the constant?",
             "Divide both sides by the coefficient, including its sign."),
            Fraction(c, a),
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
        c = b + change
        return (
            f"Solve ({a}/{denominator})x {b:+d} = {c}.",
            (Fraction(a, denominator), Fraction(b), Fraction(0), Fraction(c)),
            "EQ.MULTIPLY_INSTEAD_OF_DIVIDE_FRACTION",
            "First isolate the product, then multiply both sides by the coefficient's reciprocal.",
            ("Remove the additive term from both sides first.",
             "Undo multiplication by a fraction with its reciprocal."),
            Fraction(a * change, denominator),
        )
    if family == "MULTISTEP_NEGATIVE_DISTRIBUTION":
        x = _noninteger(rng)
        k = x.denominator * rng.randint(1, 4)
        b = _nonzero(rng, -9, 9)
        c = rng.randint(-12, 12)
        target = -k * (x - b) + c
        return (
            f"Solve -{k}(x - ({b})) + ({c}) = {target}.",
            (Fraction(-k), Fraction(k * b + c), Fraction(0), Fraction(target)),
            "EQ.DROPPED_BRACKET_CONSTANT",
            "Distribute the negative factor to BOTH terms, simplify, and preserve equality.",
            ("A negative multiplier changes each term inside the parentheses.",
             "After distribution, collect constants and isolate x."),
            Fraction(c - target, k),
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
        return (
            f"Solve {a}x {b:+d} = {c}x {int(d):+d}.",
            (Fraction(a), Fraction(b), Fraction(c), Fraction(d)),
            "EQ.IGNORED_RIGHT_VARIABLE",
            "Apply the same subtraction to both sides to collect variable terms before dividing.",
            ("Subtract one variable term from BOTH sides.",
             "Simplify the variable coefficient, then isolate x."),
            Fraction(d - b, a),
        )
    raise ValueError(f"Unknown draft family: {family}")


def create_candidate(family: str, *, seed: str | int, mode: str) -> dict:
    if family not in FAMILIES or mode not in MODES:
        raise ValueError("Unknown family or mode")
    prompt, (a, b, c, d), misconception, rationale, hints, wrong = _case(
        family, _rng(family, seed, mode)
    )
    if a == c:
        raise ArithmeticError("Nonunique or nonexistent equation solution")
    answer = (d - b) / (a - c)
    if answer.denominator == 1:
        raise ArithmeticError("Draft family must provide a noninteger rational answer")
    if wrong == answer:
        raise ArithmeticError("Misconception collides with the correct answer")
    coefficients = {"lhs_x": _fmt(a), "lhs_constant": _fmt(b),
                    "rhs_x": _fmt(c), "rhs_constant": _fmt(d)}
    fingerprint = hashlib.sha256(json.dumps({"family": family, "coefficients": coefficients},
                                                sort_keys=True).encode()).hexdigest()
    # No untrusted generated text is evaluated, compiled, or executed.
    return {
        "candidate_family": family,
        "canonical_skill_hint": SKILLS[family],
        "mode": mode,
        "variant_id": hashlib.sha256(f"{family}|{mode}|{seed}".encode()).hexdigest()[:24],
        "task_fingerprint": fingerprint,
        "prompt": prompt,
        "equation_coefficients": coefficients,
        "canonical_answer": f"x={_fmt(answer)}",
        "explanation_for_author_review": rationale,
        "guided_hints_for_author_review": list(hints),
        "misconception_code": misconception,
        "misconception_answer": f"x={_fmt(wrong)}",
    }


def learner_projection(candidate: dict) -> dict:
    """Minimal view, including no answers/hints/misconception values in any mode."""
    return {k: candidate[k] for k in ("variant_id", "mode", "prompt")}


def create_pack(*, count_per_family_mode: int = 25) -> dict:
    if not 1 <= count_per_family_mode <= 100:
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
        "schema": "MIHUR_DRAFT_RATIONAL_EQUATION_CANDIDATES_V1",
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
