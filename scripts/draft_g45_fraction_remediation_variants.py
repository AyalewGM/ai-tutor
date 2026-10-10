"""Seeded, draft-only fraction misconception practice variant generator.

Pure content tooling: no runtime imports, student records, mastery writes, or
curriculum approval. Exact rational answers are represented as reduced strings.
"""
from __future__ import annotations

import argparse
import json
import random
from fractions import Fraction
from pathlib import Path

PHASES = ("concrete", "guided", "independent", "transfer")
FAMILIES = (
    "reference-whole",
    "number-line-intervals",
    "equivalence",
    "fraction-addition",
    "compare-size",
    "remaining-whole",
)


def _fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _make(family: str, phase: str, rng: random.Random) -> dict[str, str]:
    if family == "reference-whole":
        total = rng.choice((6, 8, 10, 12, 15, 18, 20, 24))
        selected = rng.randint(1, total - 1)
        answer = Fraction(selected, total)
        wrong = Fraction(total, selected)
        question = f"A whole has {total} equal parts, of which {selected} are shaded. What fraction is shaded, in simplest form?"
        reason = "The denominator counts equal parts of the same whole; the numerator counts shaded parts."
    elif family == "number-line-intervals":
        intervals = rng.choice((4, 5, 6, 8, 10, 12))
        jump = rng.randint(1, intervals - 1)
        end = 2 if phase == "transfer" else 1
        answer = Fraction(end * jump, intervals)
        wrong = Fraction(end * jump, intervals + 1)
        question = f"A number line from 0 to {end} is divided into {intervals} equal intervals. What number is at jump {jump} after zero?"
        reason = "Count equal intervals, not endpoint marks; each jump is total length divided by intervals."
    elif family == "equivalence":
        den = rng.choice((3, 4, 5, 6, 7, 8))
        num = rng.randint(1, den - 1)
        scale = rng.randint(2, 5)
        answer = Fraction(num * scale)
        wrong = Fraction(num + (scale - 1) * den)
        question = f"Complete {num}/{den} = ?/{den * scale}. Give the missing numerator."
        reason = "Multiply numerator and denominator by the same factor."
    elif family == "fraction-addition":
        den = rng.choice((5, 6, 7, 8, 9, 10, 12))
        first = rng.randint(1, den - 1)
        second = rng.randint(1, den - 1)
        answer = Fraction(first + second, den)
        wrong = Fraction(first + second, 2 * den)
        question = f"Compute {first}/{den} + {second}/{den} as a fraction in simplest form."
        reason = "Add the counts of equal-sized units; the denominator stays the same before simplifying."
    elif family == "compare-size":
        den1, den2 = rng.sample((3, 4, 5, 6, 7, 8, 9, 10), 2)
        num = rng.randint(1, min(den1, den2) - 1)
        left, right = Fraction(num, den1), Fraction(num, den2)
        answer = max(left, right)
        wrong = min(left, right)
        question = f"Which fraction is greater: {num}/{den1} or {num}/{den2}? Give the greater fraction."
        reason = "For the same whole and numerator, fewer equal partitions make each part larger."
    elif family == "remaining-whole":
        first_den = rng.choice((2, 3, 4, 5))
        second_den = rng.choice((2, 3, 4, 5))
        total = first_den * second_den * rng.randint(2, 6)
        after_first = total - total // first_den
        answer = Fraction(after_first - after_first // second_den)
        wrong = Fraction(total - total // first_den - total // second_den)
        question = f"Start with {total} counters. Remove 1/{first_den} of the original, then 1/{second_den} of the remainder. How many remain?"
        reason = "The second fraction applies to the new remaining whole, not the original count."
    else:
        raise ValueError(f"Unknown family: {family}")
    if answer == wrong:
        raise AssertionError(f"Misconception answer equals correct answer for {family}")
    return {
        "question": question,
        "expected": _fraction(answer),
        "misconception_answer": _fraction(wrong),
        "mathematical_reasoning": reason,
    }


def generate(seed: int = 20261009, variants_per_phase: int = 4) -> dict[str, object]:
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    if not isinstance(variants_per_phase, int) or isinstance(variants_per_phase, bool) or not 1 <= variants_per_phase <= 30:
        raise ValueError("variants_per_phase must be an integer from 1 to 30")
    rng = random.Random(seed)
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for family in FAMILIES:
        for phase in PHASES:
            for index in range(variants_per_phase):
                for _ in range(300):
                    item = _make(family, phase, rng)
                    if item["question"] not in seen:
                        break
                else:
                    raise ValueError(f"Cannot generate {variants_per_phase} unique variants for {family}/{phase}")
                seen.add(item["question"])
                items.append({
                    "variant_id": f"{family}-{phase}-{index + 1:02d}",
                    "family": family,
                    "phase": phase,
                    "review_status": "PENDING",
                    **item,
                })
    return {
        "package_id": "draft-g45-fractions-seeded-remediation-v1",
        "status": "DRAFT_UNVERIFIED",
        "review_status": "PENDING",
        "runtime_activation": False,
        "mastery_updater": False,
        "canonical_skill_ids": [],
        "curriculum_mappings": [],
        "seed": seed,
        "variants_per_phase": variants_per_phase,
        "variants": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--variants-per-phase", type=int, default=4)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = json.dumps(generate(args.seed, args.variants_per_phase), indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
