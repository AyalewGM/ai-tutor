"""Draft-only deterministic word-problem variants for independent review.

This module is NOT imported by the student runtime. Its provisional families and
variants confer no canonical identity, curriculum mapping, or mastery evidence.
"""
from __future__ import annotations

import argparse
import json
import random
from fractions import Fraction

STATUS = "DRAFT_UNVERIFIED"
REVIEW_STATUS = "PENDING"


def _item(
    family: str,
    structure: str,
    variant: int,
    question: str,
    operation: str,
    operands: dict[str, int],
    answer: int | Fraction,
    hints: list[str],
    worked: str,
    misconception: str,
    wrong_answer: str,
    feedback: str,
    model: str,
    check: str,
) -> dict:
    if isinstance(answer, Fraction):
        expected = str(answer)
    else:
        expected = str(answer)
    return {
        "item_id": f"draft-generated-{structure}-{variant:03d}",
        "provisional_skill": family,
        "problem_structure": structure,
        "variant_index": variant,
        "status": STATUS,
        "review_status": REVIEW_STATUS,
        "runtime_activation": False,
        "question": question,
        "operation": operation,
        "operands": operands,
        "expected": expected,
        "answer_contract": "exact_rational_or_integer",
        "hints": hints,
        "worked_solution": worked,
        "misconception": {
            "tag": misconception,
            "plausible_wrong_answer": wrong_answer,
            "feedback": feedback,
        },
        "visual_model_prompt": model,
        "independent_check": check,
    }


def _generate_one(structure: str, variant: int, seed: int) -> dict:
    rng = random.Random(f"mihur-draft-v1:{seed}:{structure}:{variant}")
    n = rng.randint
    if structure == "add-start-unknown":
        start, change = n(35, 450), n(20, 175)
        end = start + change
        return _item("ADDITIVE_WORD_PROBLEMS", structure, variant,
            f"A library received {change} books and now has {end}. How many books were there before the delivery?",
            "subtract", {"end": end, "change": change}, start,
            ["Identify the starting amount as the unknown.", "Draw a bar for the final amount and its added part.", "Undo the increase by subtracting the delivery."],
            f"Start + {change} = {end}; start = {end} - {change} = {start}.",
            "adding-both-givens", str(end + change),
            "The final amount already includes the new books; do not add them again.",
            "Part-whole tape diagram with final total and the known added segment.",
            f"{start} + {change} = {end}.")
    if structure == "add-comparison":
        smaller, difference = n(45, 280), n(12, 140)
        larger = smaller + difference
        return _item("ADDITIVE_WORD_PROBLEMS", structure, variant,
            f"A community garden has {larger} seedlings. Another has {smaller}. How many more seedlings does the first have?",
            "subtract", {"larger": larger, "smaller": smaller}, difference,
            ["Identify which garden has more.", "Align two bars at their starting edge.", "Subtract the shorter length from the longer length."],
            f"Difference = {larger} - {smaller} = {difference}.",
            "sum-instead-of-difference", str(larger + smaller),
            "How many more asks for a difference, not the combined total.",
            "Two aligned comparison bars with a highlighted excess segment.",
            f"{smaller} + {difference} = {larger}.")
    if structure == "add-two-changes":
        start, added, removed = n(120, 450), n(40, 160), n(20, 95)
        end = start + added - removed
        return _item("ADDITIVE_WORD_PROBLEMS", structure, variant,
            f"A school starts with {start} notebooks, receives {added}, and gives away {removed}. How many remain?",
            "add_subtract", {"start": start, "added": added, "removed": removed}, end,
            ["Identify which change increases the total and which decreases it.", "Use a start-change-change-end diagram.", "Add the delivery, then subtract the giveaway."],
            f"{start} + {added} - {removed} = {end}.",
            "both-changes-added", str(start + added + removed),
            "Giving notebooks away reduces the count.",
            "A number line with a positive jump and then a negative jump.",
            f"{end} + {removed} - {added} = {start}.")
    if structure == "multiply-equal-groups":
        groups, each = n(4, 16), n(7, 24)
        total = groups * each
        return _item("MULTIPLICATIVE_WORD_PROBLEMS", structure, variant,
            f"An art class fills {groups} identical boxes with {each} markers in each box. How many markers are packed?",
            "multiply", {"groups": groups, "each": each}, total,
            ["Count the number of equal groups.", "Draw an array with one row per box.", "Multiply group count by markers per box."],
            f"{groups} groups of {each} = {groups} x {each} = {total}.",
            "adding-factors", str(groups + each),
            "Adding the two factors does not count every marker in every box.",
            "Equal-group circles and an array with labeled rows.",
            f"{total} / {groups} = {each}.")
    if structure == "multiply-remainder-capacity":
        capacity, full, leftover = n(5, 16), n(4, 14), n(1, 4)
        leftover = min(leftover, capacity - 1)
        people = capacity * full + leftover
        return _item("MULTIPLICATIVE_WORD_PROBLEMS", structure, variant,
            f"{people} students need vans with at most {capacity} seats each. What is the minimum number of vans?",
            "ceil_divide", {"people": people, "capacity": capacity}, full + 1,
            ["Divide students into full vans.", "Represent the remaining students separately.", "A partially filled van still counts as a van."],
            f"{people} = {full} x {capacity} + {leftover}; use {full} full vans and 1 more, so {full + 1}.",
            "truncate-quotient", str(full),
            "The remaining students still need seats, so round up.",
            "Full van boxes plus one box for the remainder.",
            f"{full} vans seat only {full * capacity}; {full + 1} vans have enough seats.")
    if structure == "multiply-two-stage":
        shelves, boxes, each = n(3, 8), n(3, 9), n(4, 15)
        total = shelves * boxes * each
        return _item("MULTIPLICATIVE_WORD_PROBLEMS", structure, variant,
            f"A store has {shelves} shelves, each with {boxes} boxes. Each box contains {each} pencils. How many pencils are there?",
            "multiply_three", {"shelves": shelves, "boxes": boxes, "each": each}, total,
            ["Identify all three levels: shelves, boxes, pencils.", "Find the number of boxes first.", "Multiply boxes by pencils per box."],
            f"{shelves} x {boxes} = {shelves * boxes} boxes; times {each} = {total} pencils.",
            "omit-a-level", str(shelves * boxes),
            "The number of boxes is not the number of pencils.",
            "Nested shelves-to-boxes-to-pencils diagram.",
            f"{total} / {each} / {boxes} = {shelves}.")
    if structure == "fraction-of-set":
        den = rng.choice([3, 4, 5, 6, 8, 10])
        num = n(1, den - 1)
        unit = n(3, 15)
        whole = den * unit
        part = num * unit
        return _item("FRACTION_WORD_PROBLEMS", structure, variant,
            f"A club has {whole} members. {num}/{den} joined the robotics group. How many members joined?",
            "fraction_of_set", {"numerator": num, "denominator": den, "whole": whole}, part,
            ["Identify the whole collection.", "Divide the whole into equal denominator-sized groups.", "Take the numerator number of groups."],
            f"{whole} / {den} = {unit} per part; {num} x {unit} = {part}.",
            "use-denominator-as-multiplier", str(whole * den),
            "The denominator tells how many equal parts the whole has.",
            "A bar split into equal groups with numerator groups shaded.",
            f"{part} / {whole} = {Fraction(num, den)}.")
    if structure == "fraction-unknown-whole":
        den = rng.choice([3, 4, 5, 6, 8])
        num = n(1, den - 1)
        unit = n(4, 17)
        part, whole = num * unit, den * unit
        return _item("FRACTION_WORD_PROBLEMS", structure, variant,
            f"{part} beads represent {num}/{den} of a collection. How many beads are in the full collection?",
            "fraction_unknown_whole", {"part": part, "numerator": num, "denominator": den}, whole,
            ["The given beads are a part, not the whole.", "Split the known part into numerator equal groups.", "Extend the groups to the full denominator."],
            f"One part = {part}/{num} = {unit}; whole = {den} x {unit} = {whole}.",
            "multiply-part-by-fraction", str(Fraction(part * num, den)),
            "Multiplying the known part by a proper fraction makes it smaller, not the full whole.",
            "Denominator-section bar with the known numerator sections shaded.",
            f"{Fraction(num, den)} x {whole} = {part}.")
    if structure == "fraction-like-addition":
        den = rng.choice([5, 6, 8, 10, 12])
        a, b = n(1, den - 2), n(1, den - 2)
        expected = Fraction(a + b, den)
        wrong = Fraction(a + b, den * 2)
        return _item("FRACTION_WORD_PROBLEMS", structure, variant,
            f"A baker uses {a}/{den} of a bag of flour and then {b}/{den} of a bag. How many bags of flour were used in total? Give an exact fraction.",
            "fraction_like_add", {"a": a, "b": b, "denominator": den}, expected,
            ["Both amounts use the same-sized fractional parts.", "Combine the number of parts, keeping their size unchanged.", "Simplify the resulting fraction."],
            f"{a}/{den} + {b}/{den} = {a+b}/{den} = {expected}.",
            "add-denominators", str(wrong),
            "The size of each part does not change when like fractions are added.",
            "Two fraction bars with the same denominator, combined end-to-end.",
            f"{expected} - {Fraction(a, den)} = {Fraction(b, den)}.")
    if structure == "ratio-unit-price":
        units, unit_price = n(3, 12), n(2, 19)
        total = units * unit_price
        return _item("RATIO_RATE_WORD_PROBLEMS", structure, variant,
            f"{units} identical notebooks cost ${total} altogether. What is the price of one notebook in dollars?",
            "unit_price", {"units": units, "total_dollars": total}, unit_price,
            ["Identify the total cost and the number of identical items.", "Use a ratio table with 1 item as the target.", "Divide total cost by the number of items."],
            f"${total} / {units} = ${unit_price} per notebook.",
            "multiply-instead-of-divide", str(total * units),
            "Unit price is total cost divided across the items.",
            "Double number line connecting item count to total dollars.",
            f"{units} x ${unit_price} = ${total}.")
    if structure == "ratio-percent-discount":
        percent = rng.choice([10, 20, 25])
        price = 20 * n(3, 25)
        discount = price * percent // 100
        final = price - discount
        return _item("RATIO_RATE_WORD_PROBLEMS", structure, variant,
            f"A jacket costs ${price} and is discounted by {percent}%. What is the final price in dollars?",
            "percent_discount", {"price": price, "percent": percent}, final,
            ["Find the discount as a part of the original price.", "Subtract the discount rather than adding it.", "Check that the final price is below the original price."],
            f"Discount = {percent}% of ${price} = ${discount}; final = ${price} - ${discount} = ${final}.",
            "discount-instead-of-final", str(discount),
            "The question asks for the price after the discount, not the discount amount.",
            "100-part percent bar with the discount segment removed.",
            f"{final} + {discount} = {price}.")
    if structure == "ratio-fixed-fee":
        fee, hourly, hours = n(4, 30), n(3, 18), n(2, 12)
        cost = fee + hourly * hours
        return _item("RATIO_RATE_WORD_PROBLEMS", structure, variant,
            f"A tool rental charges a fixed ${fee} fee plus ${hourly} per hour. What is the cost for {hours} hours?",
            "fixed_fee", {"fee": fee, "hourly": hourly, "hours": hours}, cost,
            ["Separate the fixed charge from the hourly charge.", "Draw one fixed block plus equal hourly blocks.", "Multiply hourly rate by hours, then add the fixed fee once."],
            f"${fee} + {hours} x ${hourly} = ${cost}.",
            "multiply-fixed-fee", str(fee * hours + hourly),
            "The fixed fee is charged only once, regardless of hours.",
            "One fixed-cost bar plus a repeated-hourly-cost array.",
            f"{cost} - {fee} = {hours * hourly} = {hours} x {hourly}.")
    if structure == "geometry-perimeter":
        length, width = n(9, 35), n(3, 8)
        perimeter = 2 * (length + width)
        return _item("GEOMETRY_MEASUREMENT_WORD_PROBLEMS", structure, variant,
            f"A rectangular garden is {length} metres long and {width} metres wide. How many metres of fencing go around it?",
            "perimeter", {"length": length, "width": width}, perimeter,
            ["Fencing follows the boundary, not the interior.", "Label all four sides of the rectangle.", "Add both lengths and both widths."],
            f"2 x ({length} + {width}) = {perimeter} metres.",
            "area-instead-of-perimeter", str(length * width),
            "Multiplying length by width gives area in square metres, not fence length.",
            "Outlined rectangle with four labeled sides.",
            f"{length} + {width} + {length} + {width} = {perimeter}.")
    if structure == "geometry-area":
        length, width = n(8, 25), n(3, 16)
        area = length * width
        return _item("GEOMETRY_MEASUREMENT_WORD_PROBLEMS", structure, variant,
            f"A rectangular poster is {length} cm long and {width} cm wide. What is its area in square centimetres?",
            "area", {"length": length, "width": width}, area,
            ["Area measures the interior, not the boundary.", "Draw rows and columns of unit squares.", "Multiply the number of rows by the number of squares per row."],
            f"{length} x {width} = {area} square centimetres.",
            "perimeter-instead-of-area", str(2 * (length + width)),
            "Perimeter counts boundary length; area counts unit squares inside.",
            "A rectangular unit-square grid with labeled dimensions.",
            f"{area} / {length} = {width}.")
    if structure == "geometry-volume":
        length, width, height = n(4, 14), n(3, 9), n(2, 7)
        volume = length * width * height
        return _item("GEOMETRY_MEASUREMENT_WORD_PROBLEMS", structure, variant,
            f"A rectangular storage box measures {length} cm by {width} cm by {height} cm. What is its volume in cubic centimetres?",
            "volume", {"length": length, "width": width, "height": height}, volume,
            ["Volume measures space inside a three-dimensional object.", "Find unit cubes in one layer.", "Multiply cubes per layer by the number of layers."],
            f"{length} x {width} x {height} = {volume} cubic centimetres.",
            "base-area-only", str(length * width),
            "Base area counts one layer; volume requires all layers.",
            "Layered unit-cube prism showing length, width, and height.",
            f"{volume} / {height} = {length * width} square centimetres per layer.")
    if structure == "algebra-unknown-start":
        multiplier, start, fee = n(2, 8), n(4, 22), n(3, 30)
        total = multiplier * start + fee
        return _item("ALGEBRA_REASONING_WORD_PROBLEMS", structure, variant,
            f"A group pays ${fee} for supplies plus ${multiplier} for each ticket, spending ${total} altogether. How many tickets were purchased?",
            "linear_one", {"multiplier": multiplier, "fee": fee, "total": total}, start,
            ["Let x represent the ticket count.", "Subtract the one-time supply cost.", "Divide the remaining cost by the price per ticket."],
            f"{multiplier}x + {fee} = {total}; x = ({total} - {fee}) / {multiplier} = {start}.",
            "forget-fixed-fee", str(Fraction(total, multiplier)),
            "Remove the fixed charge before dividing by the ticket price.",
            "Balance diagram with one fee block and repeated ticket blocks.",
            f"{multiplier} x {start} + {fee} = {total}.")
    if structure == "algebra-linear-pattern":
        first, step, position = n(3, 30), n(2, 11), n(5, 19)
        term = first + (position - 1) * step
        return _item("ALGEBRA_REASONING_WORD_PROBLEMS", structure, variant,
            f"A pattern begins at {first} and increases by {step} each term. What is term number {position}?",
            "linear_pattern", {"first": first, "step": step, "position": position}, term,
            ["Term one is already given.", "Count how many jumps from term one to the requested position.", "Multiply the number of jumps by the step and add the first term."],
            f"{first} + ({position} - 1) x {step} = {term}.",
            "off-by-one", str(first + position * step),
            "From term 1 to term n there are n-1 increases.",
            "Number line showing the first term and equally sized jumps.",
            f"Term {position - 1} is {term - step}; add {step} to obtain {term}.")
    if structure == "algebra-two-ticket-types":
        adult_price, child_price = n(13, 24), n(4, 10)
        adults, children = n(5, 18), n(4, 15)
        count = adults + children
        revenue = adult_price * adults + child_price * children
        return _item("ALGEBRA_REASONING_WORD_PROBLEMS", structure, variant,
            f"A show sells {count} tickets. Adult tickets cost ${adult_price} and child tickets cost ${child_price}. Total sales are ${revenue}. How many adult tickets were sold?",
            "ticket_system", {"count": count, "adult_price": adult_price, "child_price": child_price, "revenue": revenue}, adults,
            ["Let a be adult tickets and count-a be child tickets.", "Write total revenue using both prices.", "Solve the equation and check both ticket count and revenue."],
            f"{adult_price}a + {child_price}({count}-a) = {revenue}; a = {adults}.",
            "assume-all-adults", str(count),
            "Both adult and child tickets contribute to the revenue.",
            "Two-color ticket cards with total count and total price constraints.",
            f"{adults} x {adult_price} + {children} x {child_price} = {revenue}.")
    raise ValueError(f"Unknown provisional structure: {structure}")


STRUCTURES = (
    "add-start-unknown", "add-comparison", "add-two-changes",
    "multiply-equal-groups", "multiply-remainder-capacity", "multiply-two-stage",
    "fraction-of-set", "fraction-unknown-whole", "fraction-like-addition",
    "ratio-unit-price", "ratio-percent-discount", "ratio-fixed-fee",
    "geometry-perimeter", "geometry-area", "geometry-volume",
    "algebra-unknown-start", "algebra-linear-pattern", "algebra-two-ticket-types",
)


def generate(seed: int = 20261009, variants_per_structure: int = 6) -> dict:
    """Generate deterministic, reviewable variants; no runtime side effects."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")
    if (\n        not isinstance(variants_per_structure, int)\n        or isinstance(variants_per_structure, bool)\n        or not 1 <= variants_per_structure <= 50\n    ):
        raise ValueError("variants_per_structure must be between 1 and 50")
    items = [
        _generate_one(structure, variant, seed)
        for structure in STRUCTURES
        for variant in range(variants_per_structure)
    ]
    return {
        "package_id": "draft-seeded-word-problem-generators-v1",
        "status": STATUS,
        "review_status": REVIEW_STATUS,
        "runtime_activation": False,
        "canonical_skill_ids": [],
        "curriculum_mappings": [],
        "seed": seed,
        "variants_per_structure": variants_per_structure,
        "structure_count": len(STRUCTURES),
        "items": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--variants", type=int, default=6)
    args = parser.parse_args()
    print(json.dumps(generate(args.seed, args.variants), indent=2))


if __name__ == "__main__":
    main()
