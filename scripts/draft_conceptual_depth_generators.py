"""Draft-only concept-first generators: fractions, integers, proportionality, algebra.

These are NOT runtime or canonical registry entries. Every generated item has
an exact arithmetic oracle, a visual representation, a misconception-specific
diagnostic, a non-answer-revealing hint ladder, and a distinct mastery transfer.
"""
from __future__ import annotations

import argparse
import json
import random
from fractions import Fraction

STRUCTURES = (
    "fraction-equivalence", "fraction-compare", "fraction-unlike-add",
    "integer-temperature-change", "integer-subtract-negative", "integer-distance",
    "ratio-recipe-scale", "ratio-partition", "percent-original-price",
    "algebra-two-sided", "algebra-slope", "algebra-linear-evaluation",
)

TEACHING = {
    "fraction-equivalence": {
        "invariant": "Scaling numerator and denominator by the same nonzero factor preserves the fraction.",
        "visual": "Show identical shaded lengths with two different equal partitions.",
        "socratic": ["What portion of the whole is shaded?", "How do partitions change while the shaded amount stays fixed?", "Which multiplication preserves the fraction?"],
        "misconception": "multiply-numerator-only",
        "feedback": "Multiplying only the numerator changes the shaded portion; scale both terms.",
        "alternative": "Use a fraction strip or divide both terms by their common factor.",
    },
    "fraction-compare": {
        "invariant": "Fractions must refer to the same whole before comparing their sizes.",
        "visual": "Overlay two same-length fraction bars with different partitions.",
        "socratic": ["Do the bars represent the same whole?", "Could equivalent fractions use a shared denominator?", "Which shaded length is greater?"],
        "misconception": "larger-denominator-means-larger-fraction",
        "feedback": "More equal parts make each individual part smaller; compare values, not denominator digits.",
        "alternative": "Cross-multiply positive denominators or benchmark against one half.",
    },
    "fraction-unlike-add": {
        "invariant": "Only equal-sized fractional units can be added directly.",
        "visual": "Partition both bars into the least common multiple of the denominators.",
        "socratic": ["Are the original pieces the same size?", "What common-sized piece represents both?", "How many pieces of that size are there in total?"],
        "misconception": "add-denominators",
        "feedback": "Adding denominators changes the unit size instead of combining the parts.",
        "alternative": "Use equivalent fractions with a common multiple of the denominators.",
    },
    "integer-temperature-change": {
        "invariant": "Adding a signed change moves right or left on a number line.",
        "visual": "Draw a number line crossing zero with a directional arrow.",
        "socratic": ["Where does the starting temperature lie?", "Does the change point toward warmer or colder values?", "Where does the arrow end?"],
        "misconception": "ignore-negative-sign",
        "feedback": "A negative change means moving left, even if the start is already below zero.",
        "alternative": "Model negative and positive counters, cancelling zero pairs.",
    },
    "integer-subtract-negative": {
        "invariant": "Subtracting a negative quantity is equivalent to adding its opposite.",
        "visual": "Use a signed number line and reverse the direction of the removed negative change.",
        "socratic": ["What quantity is being subtracted?", "What is the opposite of that signed quantity?", "Where does the equivalent addition land?"],
        "misconception": "treat-subtract-negative-as-subtract-positive",
        "feedback": "Subtracting a negative is not the same as subtracting its positive magnitude.",
        "alternative": "Rewrite a - (-b) as a + b, then verify by adding the removed number.",
    },
    "integer-distance": {
        "invariant": "Distance between signed positions is nonnegative and independent of direction.",
        "visual": "Mark both positions on a number line and count unit intervals between them.",
        "socratic": ["Where are the two positions?", "How many unit intervals separate them?", "Would reversing the endpoints change the distance?"],
        "misconception": "signed-difference-as-distance",
        "feedback": "Distance is a magnitude; use the absolute value of the difference.",
        "alternative": "Count from the lower endpoint to zero and then to the higher endpoint.",
    },
    "ratio-recipe-scale": {
        "invariant": "A proportional recipe scales all ingredient quantities by the same factor.",
        "visual": "Double number line linking batches and ingredient amounts.",
        "socratic": ["How many batches does the original recipe make?", "What scale factor reaches the target batch count?", "Does every ingredient scale by the same factor?"],
        "misconception": "add-scale-factor",
        "feedback": "Scaling is multiplicative; adding the batch difference to the ingredient amount changes the ratio.",
        "alternative": "Find ingredient per batch and multiply by target batches.",
    },
    "ratio-partition": {
        "invariant": "Ratio parts are equal-sized units whose counts sum to the whole.",
        "visual": "Tape diagram with two groups of equal-sized boxes.",
        "socratic": ["How many total ratio parts are there?", "How much does one part represent?", "How many parts belong to the requested group?"],
        "misconception": "divide-by-only-one-ratio-part",
        "feedback": "The total is shared across the sum of the ratio parts, not just one group.",
        "alternative": "Set x:y = a:b and x+y = total, then solve for the requested share.",
    },
    "percent-original-price": {
        "invariant": "A discounted price represents the remaining percentage of the original whole.",
        "visual": "Percent bar with a shaded remaining fraction and an unknown full bar.",
        "socratic": ["What percentage of the original price remains?", "Is the sale price the whole or a part?", "What division recovers 100%?"],
        "misconception": "discount-the-sale-price-again",
        "feedback": "The sale price is already discounted; recover the original using the remaining fraction.",
        "alternative": "Find one percent of the original from the sale price, then scale to 100%.",
    },
    "algebra-two-sided": {
        "invariant": "Equivalent operations on both sides preserve equation solutions.",
        "visual": "Balance scale with equal variable blocks and constant blocks on each side.",
        "socratic": ["How can the variable terms be collected on one side?", "Which constants must be moved next?", "Does substitution satisfy both sides?"],
        "misconception": "move-term-without-changing-sign",
        "feedback": "Maintain equality by applying the same inverse operation to both sides.",
        "alternative": "Subtract the smaller variable term first, then isolate the unknown.",
    },
    "algebra-slope": {
        "invariant": "Slope is change in vertical quantity divided by change in horizontal quantity.",
        "visual": "Coordinate grid with a right triangle marking rise and run.",
        "socratic": ["What is the change in y?", "What is the change in x?", "What is the signed ratio of rise to run?"],
        "misconception": "invert-rise-and-run",
        "feedback": "Slope is vertical change divided by horizontal change, not its reciprocal.",
        "alternative": "Use a table of coordinates and compare equal x-steps.",
    },
    "algebra-linear-evaluation": {
        "invariant": "An input-output rule applies the variable multiplier before adding the constant.",
        "visual": "Function machine: multiply the input, then add the fixed term.",
        "socratic": ["Which operation acts on the input?", "Which term is fixed?", "What happens if you reverse the two operations?"],
        "misconception": "multiply-constant-as-well",
        "feedback": "Only the variable term is multiplied by the input; the intercept is added once.",
        "alternative": "Make a table for neighboring input values and compare differences.",
    },
}


def _make(structure: str, index: int, seed: int) -> dict:
    rng = random.Random(f"mihur-concept-wave-1:{seed}:{structure}:{index}")
    n = rng.randint
    if structure == "fraction-equivalence":
        a, b, k = n(1, 7), n(8, 15), n(2, 5)
        question = f"Complete the equivalent fraction: {a}/{b} = ?/{b * k}. What is the missing numerator?"
        operands = {"numerator": a, "denominator": b, "scale": k}
        answer, wrong = Fraction(a * k), Fraction(a)
        op = "fraction_equivalence"
        check = f"{Fraction(a, b)} = {Fraction(a * k, b * k)}."
    elif structure == "fraction-compare":
        a, b, c, d = n(1, 7), n(8, 13), n(1, 7), n(8, 13)
        # Strictly unequal fractions for unambiguous larger-fraction questions.
        if a * d == c * b:
            c = 8
        question = f"Which fraction is larger: {a}/{b} or {c}/{d}? Answer 1 for the first, 2 for the second."
        operands = {"a": a, "b": b, "c": c, "d": d}
        answer = Fraction(1 if a * d > c * b else 2)
        wrong = Fraction(3 - int(answer))
        op = "fraction_compare"
        check = f"Cross-products: {a} x {d} = {a * d}; {c} x {b} = {c * b}."
    elif structure == "fraction-unlike-add":
        b, d = rng.choice([(3, 4), (4, 5), (5, 6), (6, 8), (8, 12)])
        a, c = n(1, b - 1), n(1, d - 1)
        question = f"Add {a}/{b} + {c}/{d}. Give a simplified exact fraction."
        operands = {"a": a, "b": b, "c": c, "d": d}
        answer, wrong = Fraction(a, b) + Fraction(c, d), Fraction(a + c, b + d)
        op = "fraction_unlike_add"
        check = f"Subtract {Fraction(a, b)} from {answer} to recover {Fraction(c, d)}."
    elif structure == "integer-temperature-change":
        start, drop = -n(2, 16), n(3, 14)
        question = f"The temperature is {start} C and falls by {drop} C. What is the new temperature in C?"
        operands = {"start": start, "drop": drop}
        answer, wrong = Fraction(start - drop), Fraction(start + drop)
        op = "integer_temperature"
        check = f"{answer} + {drop} = {start}."
    elif structure == "integer-subtract-negative":
        start, magnitude = n(-14, 15), n(3, 16)
        question = f"Evaluate {start} - (-{magnitude})."
        operands = {"start": start, "magnitude": magnitude}
        answer, wrong = Fraction(start + magnitude), Fraction(start - magnitude)
        op = "integer_subtract_negative"
        check = f"{answer} + (-{magnitude}) = {start}."
    elif structure == "integer-distance":
        left, right = -n(3, 22), n(3, 22)
        question = f"Two points are at {left} and {right} on a number line. How many units apart are they?"
        operands = {"left": left, "right": right}
        answer, wrong = Fraction(right - left), Fraction(left - right)
        op = "integer_distance"
        check = f"Count {-left} units to zero and {right} units beyond: {answer}."
    elif structure == "ratio-recipe-scale":
        batches, target, ingredient = n(2, 5), n(7, 15), n(3, 12)
        question = f"A recipe uses {ingredient} cups for {batches} batches. How many cups for {target} batches? Give an exact fraction if needed."
        operands = {"batches": batches, "target": target, "ingredient": ingredient}
        answer, wrong = Fraction(ingredient * target, batches), Fraction(ingredient * target)
        op = "ratio_recipe"
        check = f"{answer} / {target} = {Fraction(ingredient, batches)} cups per batch."
    elif structure == "ratio-partition":
        a, b, unit = n(2, 6), n(7, 12), n(3, 18)
        total = (a + b) * unit
        question = f"A prize of ${total} is shared in ratio {a}:{b}. How many dollars does the first person receive?"
        operands = {"a": a, "b": b, "total": total}
        answer, wrong = Fraction(a * unit), Fraction(total)
        op = "ratio_partition"
        check = f"First share {answer}; second share {b * unit}; sum {total}."
    elif structure == "percent-original-price":
        discount = rng.choice([10, 20, 25, 40])
        original = 20 * n(5, 25)
        sale = original * (100 - discount) // 100
        question = f"After a {discount}% discount, a coat costs ${sale}. What was its original price in dollars?"
        operands = {"discount": discount, "sale": sale}
        answer, wrong = Fraction(original), Fraction(sale * (100 - discount), 100)
        op = "percent_original"
        check = f"{original} x (100-{discount})/100 = {sale}."
    elif structure == "algebra-two-sided":
        left, right, solution, constant = n(5, 12), n(1, 4), n(2, 14), n(3, 22)
        rhs = (left - right) * solution + constant
        question = f"Solve for x: {left}x + {constant} = {right}x + {rhs}."
        operands = {"left": left, "right": right, "constant": constant, "rhs": rhs}
        answer, wrong = Fraction(solution), Fraction(rhs + constant, left - right)
        op = "algebra_two_sided"
        check = f"Both sides equal {left * solution + constant} when x={solution}."
    elif structure == "algebra-slope":
        x1, y1, run, rise = n(-8, 4), n(-12, 12), n(2, 9), n(-9, -2)
        x2, y2 = x1 + run, y1 + rise
        question = f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2}). Give an exact fraction."
        operands = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        answer, wrong = Fraction(rise, run), Fraction(-rise, run)
        op = "algebra_slope"
        check = f"Rise {rise}, run {run}, slope {answer}."
    elif structure == "algebra-linear-evaluation":
        multiplier, constant, x = n(3, 13), n(4, 25), n(3, 17)
        question = f"A function is f(x) = {multiplier}x + {constant}. Find f({x})."
        operands = {"multiplier": multiplier, "constant": constant, "x": x}
        answer, wrong = Fraction(multiplier * x + constant), Fraction(multiplier * (x + constant))
        op = "algebra_linear_eval"
        check = f"Substitution gives {multiplier} x {x} + {constant} = {answer}."
    else:
        raise ValueError(f"Unsupported draft structure: {structure}")
    if answer == wrong:
        raise AssertionError(f"Diagnostic collision in {structure}")
    teaching = TEACHING[structure]
    return {
        "item_id": f"concept-draft-{structure}-{index:03d}",
        "provisional_structure": structure,
        "status": "DRAFT_UNVERIFIED",
        "review_status": "PENDING",
        "runtime_activation": False,
        "question": question,
        "operation": op,
        "operands": operands,
        "expected": str(answer),
        "diagnostic": {
            "misconception": teaching["misconception"],
            "plausible_wrong_answer": str(wrong),
            "feedback": teaching["feedback"],
        },
        "teaching": {
            "invariant": teaching["invariant"],
            "visual_model": teaching["visual"],
            "socratic_questions": teaching["socratic"],
            "alternative_strategy": teaching["alternative"],
            "hint_sequence": [
                "Identify the unknown and its units; estimate a reasonable range.",
                teaching["visual"],
                "Write a matching mathematical relationship and verify it independently.",
            ],
            "after_first_error": "Use a concrete model and ask the first Socratic question.",
            "after_second_error": "Use the visual model and address the misconception explicitly.",
            "after_third_error": "Demonstrate a contrasting strategy, then assign unseen transfer.",
        },
        "independent_check": check,
        "mastery_requirement": {
            "unseen_transfer_required": True,
            "explanation_required": True,
            "independent_verification_required": True,
            "mastery_not_awarded_by_generator": True,
        },
    }


def generate(seed: int = 20261009, variants_per_structure: int = 6) -> dict:
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")
    if not isinstance(variants_per_structure, int) or isinstance(variants_per_structure, bool):
        raise TypeError("variants_per_structure must be an integer")
    if not 1 <= variants_per_structure <= 50:
        raise ValueError("variants_per_structure must be between 1 and 50")
    return {
        "package_id": "draft-conceptual-depth-wave-v1",
        "status": "DRAFT_UNVERIFIED",
        "review_status": "PENDING",
        "runtime_activation": False,
        "canonical_skill_ids": [],
        "curriculum_mappings": [],
        "seed": seed,
        "structure_count": len(STRUCTURES),
        "items": [
            _make(structure, i, seed)
            for structure in STRUCTURES
            for i in range(variants_per_structure)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--variants", type=int, default=6)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, args.variants), indent=2))


if __name__ == "__main__":
    main()
