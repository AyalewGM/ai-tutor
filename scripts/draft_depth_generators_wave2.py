"""Second-wave, draft-only deterministic mathematics practice generators.

No curriculum approval, canonical identity, student runtime import, or mastery
writes. Exact arithmetic uses fractions; visuals are reviewable specifications.
"""
from __future__ import annotations

import argparse
import json
import random
from fractions import Fraction

STATUS = "DRAFT_UNVERIFIED"

STRUCTURES = (
    "place-value-compose", "place-value-digit-value",
    "addition-missing-addend", "subtraction-regroup",
    "fraction-equivalent", "fraction-compare",
    "fraction-unlike-add", "fraction-of-remaining",
    "ratio-equivalent", "ratio-proportional-table",
    "ratio-percent-change", "ratio-scale-drawing",
    "algebra-distributive", "algebra-two-step",
    "algebra-inequality", "algebra-slope",
)

def _make(
    structure: str, variant: int, question: str, operands: dict[str, int],
    answer: Fraction | int, hints: tuple[str, str, str],
    steps: tuple[str, str, str], misconception: str, wrong: Fraction | int,
    feedback: str, visual: str, check: str,
) -> dict:
    return {
        "item_id": f"draft-depth-{structure}-{variant:03d}",
        "provisional_skill": (\n            "FOUNDATIONAL"\n            if structure.startswith(("place-", "addition-", "subtraction-"))\n            else structure.split("-")[0].upper()\n        ),
        "structure": structure,
        "status": STATUS,
        "review_status": "PENDING",
        "runtime_activation": False,
        "question": question,
        "operands": operands,
        "expected": str(Fraction(answer)),
        "answer_contract": "exact_rational_or_integer",
        "hints": list(hints),
        "teaching_sequence": [
            {"phase": "concrete", "instruction": steps[0]},
            {"phase": "visual", "instruction": steps[1], "visual_model": visual},
            {"phase": "symbolic", "instruction": steps[2]},
        ],
        "misconception": {
            "tag": misconception,
            "plausible_wrong_answer": str(Fraction(wrong)),
            "feedback": feedback,
        },
        "transfer_check": check,
    }

def _one(structure: str, variant: int, seed: int) -> dict:
    r = random.Random(f"mihur-depth-wave2:{seed}:{structure}:{variant}")
    n = r.randint
    if structure == "place-value-compose":
        hundreds, tens, ones = n(2, 8), n(2, 8), n(1, 9)
        value = 100 * hundreds + 10 * tens + ones
        return _make(structure, variant,
            f"Build a number with {hundreds} hundreds, {tens} tens and {ones} ones. What number is it?",
            {"hundreds": hundreds, "tens": tens, "ones": ones}, value,
            ("Identify each place-value unit.", "Represent hundreds, tens and ones in separate columns.", "Add the three place values."),
            ("Group base-ten blocks into hundreds, tens and ones.", "Place each group in a labeled place-value chart.", f"{hundreds}×100 + {tens}×10 + {ones} = {value}."),
            "digits-added", hundreds + tens + ones,
            "Digits name different units; add their place values, not the digits.",
            "Base-ten blocks and a hundreds/tens/ones chart.",
            f"Decompose {value} into hundreds, tens and ones.")
    if structure == "place-value-digit-value":
        thousands, hundreds, tens, ones = n(2, 8), n(1, 9), n(1, 9), n(1, 9)
        value = 1000 * thousands + 100 * hundreds + 10 * tens + ones
        return _make(structure, variant,
            f"In the number {value}, what is the value of the digit in the hundreds place?",
            {"thousands": thousands, "hundreds": hundreds, "tens": tens, "ones": ones},
            hundreds * 100,
            ("Locate the hundreds column.", "Count how many hundreds the digit represents.", "Convert hundreds to a whole-number value."),
            ("Bundle hundreds into groups of 100.", "Highlight the hundreds column of the place-value chart.", f"{hundreds} hundreds = {hundreds * 100}."),
            "digit-versus-value", hundreds,
            "A digit in the hundreds place represents hundreds, not ones.",
            "Highlight the hundreds column and its base-ten flats.",
            f"{value} - {hundreds * 100} removes the hundreds-place contribution.")
    if structure == "addition-missing-addend":
        first, missing = n(38, 275), n(17, 189)
        total = first + missing
        return _make(structure, variant,
            f"A class collected {first} cans on Monday and had {total} cans by Tuesday. How many cans were collected on Tuesday?",
            {"first": first, "total": total}, missing,
            ("Identify the known part and total.", "Draw a part-part-whole bar.", "Subtract the known part from the total."),
            ("Build two piles whose combined size is the total.", "Cover the unknown section of a tape diagram.", f"{total} − {first} = {missing}."),
            "add-instead-of-subtract", total + first,
            "The total already includes Monday's cans; find the missing part.",
            "Part-part-whole tape diagram with one hidden segment.",
            f"{first} + {missing} = {total}.")
    if structure == "subtraction-regroup":
        hundreds, tens, ones = n(2, 8), n(2, 8), n(1, 5)
        sub_tens, sub_ones = n(1, tens), n(ones + 1, 9)
        top = 100 * hundreds + 10 * tens + ones
        bottom = 10 * sub_tens + sub_ones
        result = top - bottom
        return _make(structure, variant,
            f"A school has {top} pencils and distributes {bottom}. How many pencils remain?",
            {"top": top, "bottom": bottom}, result,
            ("Identify the starting quantity and the amount removed.", "Regroup one ten into ten ones.", "Subtract by place value and verify."),
            ("Trade one ten-rod for ten unit cubes.", "Show regrouping in a place-value chart.", f"{top} − {bottom} = {result}."),
            "subtract-small-from-large-digit", 100 * hundreds + 10 * (tens - sub_tens) + (sub_ones - ones),
            "Regroup before subtracting ones; digit order matters.",
            "Base-ten blocks showing a traded ten.",
            f"{result} + {bottom} = {top}.")
    if structure == "fraction-equivalent":
        denominator, numerator, factor = n(3, 11), n(1, 2), n(3, 7)
        denominator = max(denominator, numerator + 1)
        return _make(structure, variant,
            f"Complete the equivalent fraction: {numerator}/{denominator} = ?/{denominator * factor}. What numerator is missing?",
            {"numerator": numerator, "denominator": denominator, "factor": factor},
            numerator * factor,
            ("Find how the denominator changed.", "Split each original fraction part into equal smaller pieces.", "Apply the same multiplier to the numerator."),
            ("Fold a fraction strip into equal parts.", "Refine each part into smaller equal segments.", f"{numerator}×{factor} = {numerator * factor}."),
            "add-factor-instead-of-multiply", numerator + factor,
            "Equivalent fractions scale both numerator and denominator by the same factor.",
            "Aligned fraction strips with original and refined partitions.",
            f"{numerator * factor}/{denominator * factor} simplifies to {numerator}/{denominator}.")
    if structure == "fraction-compare":
        denominator = r.choice([4, 5, 6, 8, 10, 12])
        a, b = sorted(r.sample(range(1, denominator), 2))
        return _make(structure, variant,
            f"Two ribbons measure {a}/{denominator} m and {b}/{denominator} m. How much longer is the second ribbon? Give an exact fraction of a metre.",
            {"denominator": denominator, "a": a, "b": b}, Fraction(b - a, denominator),
            ("The ribbons use equal-sized fractional units.", "Compare the shaded lengths on matching bars.", "Subtract numerators, keeping the denominator."),
            ("Line up fraction strips of the same whole.", "Shade both lengths and mark the excess.", f"{b}/{denominator} − {a}/{denominator} = {Fraction(b-a, denominator)}."),
            "add-denominators", Fraction(b - a, 2 * denominator),
            "Equal-sized fractional pieces keep the same denominator.",
            "Aligned fraction bars with excess segment highlighted.",
            f"{Fraction(b-a, denominator)} + {Fraction(a, denominator)} = {Fraction(b, denominator)}.")
    if structure == "fraction-unlike-add":
        d1, d2 = r.choice([(2, 3), (3, 4), (4, 5), (3, 8), (5, 6)])
        a, b = n(1, d1 - 1), n(1, d2 - 1)
        ans = Fraction(a, d1) + Fraction(b, d2)
        return _make(structure, variant,
            f"A recipe uses {a}/{d1} cup of oats and {b}/{d2} cup of seeds. How many cups in total? Give an exact fraction.",
            {"a": a, "d1": d1, "b": b, "d2": d2}, ans,
            ("The denominators describe different-sized pieces.", "Partition both bars into a common unit size.", "Convert and add the numerators."),
            ("Use fraction strips with different partitions.", "Overlay strips on a common partition grid.", f"{a}/{d1} + {b}/{d2} = {ans}."),
            "add-numerators-and-denominators", Fraction(a + b, d1 + d2),
            "You must use a common denominator before combining fractional pieces.",
            "Fraction bars converted to a common denominator.",
            f"{ans} − {Fraction(a,d1)} = {Fraction(b,d2)}.")
    if structure == "fraction-of-remaining":
        denominator, numerator = r.choice([(3, 1), (4, 1), (5, 2), (6, 1)])
        whole_unit = n(4, 18)
        whole = denominator * whole_unit
        used = numerator * whole_unit
        remain = whole - used
        return _make(structure, variant,
            f"A craft group has {whole} beads and uses {numerator}/{denominator} of them. How many beads remain?",
            {"whole": whole, "numerator": numerator, "denominator": denominator}, remain,
            ("Find the number used, not the remainder.", "Shade the used portion of the whole collection.", "Subtract the used portion from the whole."),
            ("Divide beads into equal groups.", "Shade the used groups and count unshaded groups.", f"{whole} − ({numerator}/{denominator} × {whole}) = {remain}."),
            "used-instead-of-remaining", used,
            "The question asks what remains after using the fractional part.",
            "Equal groups with used beads shaded and remaining beads unshaded.",
            f"{remain} + {used} = {whole}.")
    if structure == "ratio-equivalent":
        left, right, factor = n(2, 8), n(3, 11), n(2, 9)
        return _make(structure, variant,
            f"A paint mix uses {left} cups blue for every {right} cups white. If blue increases to {left * factor} cups at the same ratio, how many cups of white are needed?",
            {"left": left, "right": right, "factor": factor}, right * factor,
            ("Compare the new blue amount with the original.", "Use a ratio table with equal scaling.", "Multiply the white amount by the same factor."),
            ("Build identical batches of colored tiles.", "Extend both columns of a ratio table.", f"{right} × {factor} = {right * factor} cups white."),
            "add-instead-of-scale", right + factor,
            "An equivalent ratio multiplies both quantities by the same factor.",
            "Paired double number lines and colored batch tiles.",
            f"{left * factor}:{right * factor} simplifies to {left}:{right}.")
    if structure == "ratio-proportional-table":
        unit, quantity = n(3, 17), n(4, 13)
        total = unit * quantity
        return _make(structure, variant,
            f"Every pack holds {unit} batteries. Complete the proportional table: 1 pack → {unit} batteries; {quantity} packs → how many batteries?",
            {"unit": unit, "quantity": quantity}, total,
            ("Identify the constant rate.", "Extend a table by repeated equal groups.", "Multiply the number of packs by the unit rate."),
            ("Group batteries into equal packs.", "Plot proportional pairs on a table and origin-based graph.", f"{quantity} × {unit} = {total}."),
            "add-quantities", unit + quantity,
            "A proportional relationship uses multiplication by a constant rate.",
            "Ratio table and a line through the origin.",
            f"{total} / {quantity} = {unit} batteries per pack.")
    if structure == "ratio-percent-change":
        percent = r.choice([10, 20, 25, 30, 40])
        original = 20 * n(3, 24)
        increase = original * percent // 100
        final = original + increase
        return _make(structure, variant,
            f"A club had {original} members. Membership increased by {percent}%. How many members are there now?",
            {"original": original, "percent": percent}, final,
            ("Calculate the increase using the original as the base.", "Add the increase to the original amount.", "Check that the final number is larger."),
            ("Represent the original membership with counters.", "Extend a 100% bar by the increase portion.", f"{original} + {percent}% × {original} = {final}."),
            "increase-instead-of-final", increase,
            "The percent increase is only the additional members, not the new total.",
            "Percent bar with the increase appended to the original whole.",
            f"{final} − {original} = {increase}.")
    if structure == "ratio-scale-drawing":
        scale, drawing = n(3, 15), n(2, 17)
        actual = scale * drawing
        return _make(structure, variant,
            f"A drawing uses a scale of 1 cm to {scale} m. A path measures {drawing} cm on the drawing. How long is the real path in metres?",
            {"scale": scale, "drawing": drawing}, actual,
            ("Identify what one centimetre represents.", "Match drawing lengths to real lengths on a double number line.", "Multiply by the scale factor."),
            ("Lay down repeated 1-cm paper strips.", "Extend the paired scale line to the drawing length.", f"{drawing} × {scale} = {actual} m."),
            "divide-by-scale", Fraction(drawing, scale),
            "The real distance is larger than the drawing measurement at this scale.",
            "Double number line labeled drawing cm and real m.",
            f"{actual} / {scale} = {drawing} cm on the drawing.")
    if structure == "algebra-distributive":
        factor, x, offset = n(2, 9), n(3, 18), n(2, 13)
        value = factor * (x + offset)
        return _make(structure, variant,
            f"An arrangement has {factor} equal rows. Each row contains {x} red and {offset} blue tiles. How many tiles altogether?",
            {"factor": factor, "x": x, "offset": offset}, value,
            ("Find the number of tiles in one row.", "Represent equal rows as a split array.", "Distribute multiplication over the two tile types."),
            ("Build equal rows of red and blue tiles.", "Split the array into two rectangles.", f"{factor}({x}+{offset}) = {factor*x}+{factor*offset} = {value}."),
            "multiply-only-first-term", factor * x + offset,
            "Each row has both red and blue tiles; multiply both terms.",
            "Split rectangular array with colored columns.",
            f"{value} / {factor} = {x + offset} tiles per row.")
    if structure == "algebra-two-step":
        coefficient, x, offset = n(2, 9), n(4, 25), n(5, 29)
        total = coefficient * x + offset
        return _make(structure, variant,
            f"A museum charges a fixed ${offset} booking fee plus ${coefficient} per visitor. A group pays ${total}. How many visitors came?",
            {"coefficient": coefficient, "offset": offset, "total": total}, x,
            ("Let v represent the visitor count.", "Remove the fixed fee from the total.", "Divide the remaining charge by the per-visitor rate."),
            ("Build one fixed-cost block and repeated visitor blocks.", "Balance the cost equation with an inverse-operations diagram.", f"{coefficient}v + {offset} = {total}; v = {x}."),
            "divide-without-removing-fee", Fraction(total, coefficient),
            "The booking fee must be removed before dividing by the visitor rate.",
            "Balance-scale diagram with fixed block and repeated equal blocks.",
            f"{coefficient} × {x} + {offset} = {total}.")
    if structure == "algebra-inequality":
        price, budget = n(3, 16), n(30, 150)
        fee = n(4, 15)
        maximum = (budget - fee) // price
        return _make(structure, variant,
            f"A club has at most ${budget} to spend. A trip costs ${fee} to book plus ${price} per participant. What is the greatest whole number of participants it can afford?",
            {"price": price, "budget": budget, "fee": fee}, maximum,
            ("Write an at-most inequality, not an equation of exact spending.", "Subtract the booking fee from the budget.", "Divide by the participant cost and round down."),
            ("Allocate the fixed booking cost first.", "Show the remaining budget on a number line with equal price jumps.", f"{fee} + {price}n ≤ {budget}; maximum n = {maximum}."),
            "round-up-over-budget", maximum + 1,
            "A participant beyond the maximum would exceed the budget.",
            "Budget bar with fixed fee and whole participant-cost segments.",
            f"{fee}+{price}×{maximum} ≤ {budget} but {fee}+{price}×({maximum}+1) > {budget}.")
    if structure == "algebra-slope":
        slope, x1, y1, dx = n(2, 9), n(1, 8), n(3, 21), n(2, 9)
        x2 = x1 + dx
        y2 = y1 + slope * dx
        return _make(structure, variant,
            f"A straight line passes through ({x1}, {y1}) and ({x2}, {y2}). What is its slope?",
            {"x1": x1, "y1": y1, "x2": x2, "y2": y2}, slope,
            ("Identify the vertical change between the points.", "Identify the horizontal change in the same direction.", "Divide rise by run."),
            ("Walk right and up along a coordinate grid.", "Draw the slope triangle between the two points.", f"({y2}−{y1})/({x2}−{x1}) = {slope}."),
            "rise-not-divided-by-run", y2 - y1,
            "Slope is change in y per one unit of change in x.",
            "Coordinate grid with a right-triangle rise/run overlay.",
            f"{y1} + {slope}×({x2}−{x1}) = {y2}.")
    raise ValueError(f"Unknown structure: {structure}")


def generate(seed: int = 20261009, variants_per_structure: int = 8) -> dict:
    """Return reviewable variants without touching runtime state."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if isinstance(variants_per_structure, bool) or not isinstance(variants_per_structure, int):
        raise TypeError("variants_per_structure must be an integer")
    if not 1 <= variants_per_structure <= 50:
        raise ValueError("variants_per_structure must be between 1 and 50")
    return {
        "package_id": "draft-depth-generators-wave2-v0",
        "status": STATUS,
        "review_status": "PENDING",
        "runtime_activation": False,
        "canonical_skill_ids": [],
        "curriculum_mappings": [],
        "structure_count": len(STRUCTURES),
        "seed": seed,
        "variants_per_structure": variants_per_structure,
        "items": [
            _one(structure, i, seed)
            for structure in STRUCTURES
            for i in range(variants_per_structure)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--variants", type=int, default=8)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, args.variants), indent=2))


if __name__ == "__main__":
    main()
