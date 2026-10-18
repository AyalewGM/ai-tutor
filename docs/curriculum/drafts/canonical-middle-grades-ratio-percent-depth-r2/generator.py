"""Draft-only shared middle-grades ratio, rate, and percent authoring.

This sidecar deepens the existing Grade 6 ratio/rate package and Grade 7
percent reasoning without cloning content for any jurisdiction. It reuses
registered mathematical family codes, is deliberately not imported by
application code, has no persistence dependency, and does not establish
curriculum mappings or assessment-mode eligibility.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final

STATUS: Final = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION: Final = False
NAMESPACE: Final = "canonical-middle-grades:ratio-percent-depth-r2"
MODES: Final = frozenset({"diagnostic", "guided", "independent", "mastery"})

FAMILIES: Final = (
    "MATH.RATIO.EQUIVALENT",
    "MATH.RATIO.PART_WHOLE",
    "MATH.RATIO.TABLE.MISSING",
    "MATH.RATIO.RECIPE",
    "MATH.RATE.UNIT",
    "MATH.RATE.COMPARE",
    "MATH.PCT.OF_QUANTITY",
    "MATH.PCT.FIND_WHOLE",
    "MATH.PCT.DISCOUNT",
    "MATH.PCT.INCREASE",
)

CANONICAL_SKILL: Final = MappingProxyType(
    {
        "MATH.RATIO.EQUIVALENT": "MATH.RP.RATIO.EQUIVALENT",
        "MATH.RATIO.PART_WHOLE": "MATH.RP.RATIO.INTERPRET",
        "MATH.RATIO.TABLE.MISSING": "MATH.RP.RATIO.EQUIVALENT",
        "MATH.RATIO.RECIPE": "MATH.RP.RATIO.EQUIVALENT",
        "MATH.RATE.UNIT": "MATH.RP.RATE.UNIT",
        "MATH.RATE.COMPARE": "MATH.RP.RATE.UNIT",
        "MATH.PCT.OF_QUANTITY": "MATH.RP.PERCENT.OF",
        "MATH.PCT.FIND_WHOLE": "MATH.RP.PERCENT.OF",
        "MATH.PCT.DISCOUNT": "MATH.RP.PERCENT.APPLICATIONS",
        "MATH.PCT.INCREASE": "MATH.RP.PERCENT.CHANGE",
    }
)

TRANSFER_PARTNER: Final = MappingProxyType(
    {
        "MATH.RATIO.EQUIVALENT": "MATH.RATIO.PART_WHOLE",
        "MATH.RATIO.PART_WHOLE": "MATH.RATIO.EQUIVALENT",
        "MATH.RATIO.TABLE.MISSING": "MATH.RATIO.RECIPE",
        "MATH.RATIO.RECIPE": "MATH.RATIO.TABLE.MISSING",
        "MATH.RATE.UNIT": "MATH.RATE.COMPARE",
        "MATH.RATE.COMPARE": "MATH.RATE.UNIT",
        "MATH.PCT.OF_QUANTITY": "MATH.PCT.FIND_WHOLE",
        "MATH.PCT.FIND_WHOLE": "MATH.PCT.OF_QUANTITY",
        "MATH.PCT.DISCOUNT": "MATH.PCT.INCREASE",
        "MATH.PCT.INCREASE": "MATH.PCT.DISCOUNT",
    }
)

ACCESSIBILITY_CONTRACT: Final = MappingProxyType(
    {
        "keyboard": "All table cells, number-line points, and response controls are reachable and operable without dragging.",
        "screen_reader": "Announce quantity name, value, unit, table row/column headers, and number-line scale in reading order.",
        "visual": "Do not use colour alone; pair every highlight with a label and pattern.",
        "motion": "Scaling animations have a reduced-motion state showing before/after values simultaneously.",
        "input": "Accept exact integers, reduced or equivalent fractions, and an explicit unit field; never require pointer drawing.",
    }
)


def _fmt(value: Fraction) -> str:
    return (
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    )


def _coprime_pair(rng: random.Random) -> tuple[int, int]:
    choices = ((2, 3), (3, 4), (3, 5), (4, 7), (5, 8), (5, 9), (7, 10))
    return rng.choice(choices)


def _validate(family: str, seed: int, mode: str) -> None:
    if family not in FAMILIES:
        raise ValueError(f"Unsupported family: {family}")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode}")


@dataclass(frozen=True)
class Variant:
    variant_id: str
    family: str
    canonical_skill: str
    mode: str
    structure: str
    prompt: str
    parameters: tuple[tuple[str, int | str], ...]
    answer: str
    answer_kind: str
    answer_unit: str
    representation: tuple[str, str, str]
    misconception_answers: tuple[tuple[str, str], ...]

    def public_payload(self) -> dict[str, object]:
        """Return the answer-free learner contract."""

        return {
            "variant_id": self.variant_id,
            "family": self.family,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
            "response_fields": ["exact_answer", "unit", "reasoning"],
            "representation": list(self.representation),
            "accessibility": dict(ACCESSIBILITY_CONTRACT),
        }

    def teacher_oracle(self) -> dict[str, object]:
        """Return an exact content oracle for independent review, not runtime scoring."""

        return {
            "answer": self.answer,
            "answer_kind": self.answer_kind,
            "unit": self.answer_unit,
            "parameters": dict(self.parameters),
            "verification": verification_equation(self),
        }


def generate(family: str, seed: int, mode: str) -> Variant:
    """Generate one deterministic authored structure for a registered family."""

    _validate(family, seed, mode)
    rng = random.Random(f"{NAMESPACE}:{family}:{mode}:{seed}")
    a, b = _coprime_pair(rng)
    scale = rng.randint(2, 7)
    params: dict[str, int | str]
    wrong: dict[str, str]

    if family == "MATH.RATIO.EQUIVALENT":
        target_a = a * scale
        answer = str(b * scale)
        params = {"a": a, "b": b, "scale": scale, "target_a": target_a}
        prompt = (
            f"A ratio table begins {a}:{b}. A later row begins {target_a}:?. "
            "Find the missing term and explain why both quantities use one multiplier."
        )
        wrong = {
            "RATIO_ONE_SIDED_SCALE": str(b),
            "RATIO_ADDITIVE_SCALE": str(b + target_a - a),
        }
        structure = "EQUIVALENT_RATIO_MULTIPLICATIVE_TABLE"
        unit = "second quantity"
        representation = (
            f"Concrete: group {a} first-items with {b} second-items in each batch.",
            f"Visual: align {a}, {target_a} above {b}, ? in a ratio table.",
            f"Symbolic: {a}/{b} = {target_a}/x with a shared scale factor.",
        )
    elif family == "MATH.RATIO.PART_WHOLE":
        total = (a + b) * scale
        answer = str(a * scale)
        params = {"first_parts": a, "second_parts": b, "total": total, "scale": scale}
        prompt = (
            f"A mixture has first-to-second ratio {a}:{b} and total volume {total} L. "
            "How many litres are the first ingredient? Explain why the whole has "
            f"{a + b} equal parts."
        )
        wrong = {
            "RATIO_PART_PART_AS_FRACTION_OF_WHOLE": str(Fraction(a, b) * total),
            "RATIO_SECOND_PART_SELECTED": str(b * scale),
        }
        structure = "PART_TO_PART_RATIO_WITH_GIVEN_WHOLE"
        unit = "litres"
        representation = (
            f"Concrete: partition {total} counters into {a + b} equal part-groups.",
            f"Visual: shade {a} of {a + b} equal tape-diagram sections.",
            f"Symbolic: first = {a}/({a}+{b}) × {total}.",
        )
    elif family == "MATH.RATIO.TABLE.MISSING":
        previous_scale = scale - 1
        answer = str(b * scale)
        params = {"a": a, "b": b, "previous_scale": previous_scale, "target_scale": scale}
        prompt = (
            f"A double number line pairs {a * previous_scale} with {b * previous_scale} "
            f"and {a * scale} with ?. Find the missing coordinate, then justify the "
            "multiplicative step from the origin."
        )
        wrong = {
            "RATIO_CONSTANT_DIFFERENCE": str(a * scale + (b - a)),
            "RATIO_REPEATS_PREVIOUS_ROW": str(b * previous_scale),
        }
        structure = "DOUBLE_NUMBER_LINE_NONUNIT_MISSING_COORDINATE"
        unit = "second-axis units"
        representation = (
            "Concrete: build equal batches before joining them.",
            "Visual: use aligned tick marks starting at 0 on both number lines.",
            f"Symbolic: every point satisfies y/x = {b}/{a}.",
        )
    elif family == "MATH.RATIO.RECIPE":
        batches = scale
        answer = str(b * batches)
        params = {"servings_per_batch": a, "cups_per_batch": b, "batches": batches}
        prompt = (
            f"One recipe batch serves {a} people and uses {b} cups. A group needs "
            f"{a * batches} servings. How many cups are needed? Verify by both a "
            "batch model and a unit-rate calculation."
        )
        wrong = {
            "RATIO_ADD_SERVING_DIFFERENCE": str(b + a * (batches - 1)),
            "RATIO_INVERTED_UNIT_RATE": _fmt(Fraction(a, b) * a * batches),
        }
        structure = "RECIPE_SCALE_BATCH_AND_UNIT_RATE"
        unit = "cups"
        representation = (
            f"Concrete: repeat a batch card ({a} servings, {b} cups) {batches} times.",
            "Visual: connect the batch cards with a double number line.",
            f"Symbolic: cups = ({b}/{a}) × servings.",
        )
    elif family == "MATH.RATE.UNIT":
        denominator = rng.choice((2, 3, 4, 5))
        numerator = rng.randint(denominator + 1, denominator * 4)
        if numerator == denominator * 2:
            numerator += 1
        quantity = denominator * rng.randint(2, 6)
        total = Fraction(numerator, denominator) * quantity
        answer = _fmt(Fraction(total, quantity))
        params = {
            "total": int(total),
            "quantity": quantity,
            "rate_numerator": numerator,
            "rate_denominator": denominator,
        }
        prompt = (
            f"A pump moves {int(total)} L in {quantity} min at a constant rate. "
            "Find the exact litres per minute, label the ordered units, and verify by recomposing the total."
        )
        wrong = {
            "RATE_INVERTED_UNITS": _fmt(Fraction(quantity, total)),
            "RATE_MULTIPLIES_TOTALS": str(int(total) * quantity),
        }
        structure = "FRACTIONAL_UNIT_RATE_WITH_DIMENSIONAL_CHECK"
        unit = "litres per minute"
        representation = (
            f"Concrete: share {int(total)} litre tokens equally across {quantity} minute boxes.",
            "Visual: mark total litres over total minutes, then scale minutes to 1.",
            f"Symbolic: {int(total)} L ÷ {quantity} min.",
        )
    elif family == "MATH.RATE.COMPARE":
        qa, qb = rng.randint(2, 6), rng.randint(2, 6)
        rate_a = Fraction(rng.randint(5, 12), 2)
        rate_b = rate_a + rng.choice((Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)))
        if rng.choice((True, False)):
            rate_a, rate_b = rate_b, rate_a
        cost_a, cost_b = rate_a * qa, rate_b * qb
        answer = "A" if rate_a < rate_b else "B"
        params = {
            "quantity_a": qa,
            "cost_a_numerator": cost_a.numerator,
            "cost_a_denominator": cost_a.denominator,
            "quantity_b": qb,
            "cost_b_numerator": cost_b.numerator,
            "cost_b_denominator": cost_b.denominator,
        }
        prompt = (
            f"Shop A charges ${_fmt(cost_a)} for {qa} items; Shop B charges "
            f"${_fmt(cost_b)} for {qb} items. Which shop, A or B, has the lower exact unit price? Show both rates."
        )
        wrong = {
            "RATE_COMPARE_TOTAL_PRICE_ONLY": "A" if cost_a < cost_b else "B",
            "RATE_COMPARE_LARGER_RATE_AS_BETTER": "A" if rate_a > rate_b else "B",
        }
        wrong = {code: value for code, value in wrong.items() if value != answer}
        structure = "COMPARE_UNEQUAL_PACKS_BY_EXACT_UNIT_RATE"
        unit = "shop choice"
        representation = (
            "Concrete: partition each package cost across its items.",
            "Visual: align both packages at one item in a rate table.",
            "Symbolic: compare cost_A/quantity_A and cost_B/quantity_B.",
        )
    elif family == "MATH.PCT.OF_QUANTITY":
        percent = rng.choice((10, 20, 25, 40, 50, 60, 75))
        whole = rng.choice((40, 60, 80, 120, 160, 200))
        answer = str(Fraction(percent, 100) * whole)
        params = {"percent": percent, "whole": whole}
        prompt = (
            f"Find {percent}% of {whole}. Show the same quantity on a 100-grid, "
            "a double number line, and an exact multiplication equation."
        )
        wrong = {
            "PERCENT_USES_PERCENT_AS_WHOLE_NUMBER": str(percent * whole),
            "PERCENT_SUBTRACTS_FROM_WHOLE": str(whole - percent),
        }
        structure = "PERCENT_OF_WITH_THREE_REPRESENTATIONS"
        unit = "quantity units"
        representation = (
            f"Concrete: shade {percent} of 100 equal cells, then scale to {whole}.",
            f"Visual: align 0%, {percent}%, 100% with 0, ?, {whole}.",
            f"Symbolic: ({percent}/100) × {whole}.",
        )
    elif family == "MATH.PCT.FIND_WHOLE":
        percent = rng.choice((20, 25, 40, 50, 60, 75))
        whole = rng.choice((40, 60, 80, 120, 160, 200))
        part = Fraction(percent, 100) * whole
        if part.denominator != 1:
            whole = 200
            part = Fraction(percent, 100) * whole
        answer = str(whole)
        params = {"percent": percent, "part": int(part), "whole": whole}
        prompt = (
            f"{int(part)} is {percent}% of an unknown whole. Find the whole and "
            "verify by substituting it into the percent equation."
        )
        wrong = {
            "PERCENT_MULTIPLIES_TO_FIND_WHOLE": str(Fraction(percent, 100) * part),
            "PERCENT_TREATS_PART_AS_WHOLE": str(int(part)),
        }
        structure = "RECOVER_WHOLE_FROM_PART_AND_PERCENT"
        unit = "whole units"
        representation = (
            f"Concrete: {int(part)} fills {percent} of 100 equal percent-cells.",
            f"Visual: align {percent}% with {int(part)} and 100% with ?.",
            f"Symbolic: {int(part)} = ({percent}/100)w.",
        )
    elif family == "MATH.PCT.DISCOUNT":
        percent = rng.choice((10, 20, 25, 40, 50))
        original = rng.choice((40, 60, 80, 120, 160, 200))
        discount = Fraction(percent, 100) * original
        answer = str(original - discount)
        params = {"percent": percent, "original": original, "discount": int(discount)}
        prompt = (
            f"An item costs ${original} before a {percent}% discount. Find the final "
            "price, separately name the discount amount, and verify that final plus discount reconstructs the original."
        )
        wrong = {
            "PERCENT_REPORTS_DISCOUNT_NOT_FINAL": str(discount),
            "PERCENT_ADDS_DISCOUNT": str(original + discount),
        }
        structure = "DISCOUNT_AMOUNT_VERSUS_FINAL_PRICE"
        unit = "dollars"
        representation = (
            f"Concrete: remove {percent} of 100 price-strip cells.",
            "Visual: label original, discount amount, and remaining price as distinct bars.",
            f"Symbolic: final = {original} - ({percent}/100)({original}).",
        )
    else:
        percent = rng.choice((10, 20, 25, 40, 50))
        original = rng.choice((40, 60, 80, 120, 160, 200))
        change = Fraction(percent, 100) * original
        answer = str(original + change)
        params = {"percent": percent, "original": original, "change": int(change)}
        prompt = (
            f"A quantity begins at {original} and increases by {percent}%. Find the "
            "new total, separately name the change, and verify which value is the percent base."
        )
        wrong = {
            "PERCENT_REPORTS_CHANGE_NOT_NEW_TOTAL": str(change),
            "PERCENT_USES_NEW_TOTAL_AS_BASE": str(
                original + Fraction(percent, 100) * (original + change)
            ),
        }
        structure = "PERCENT_INCREASE_BASE_CHANGE_AND_NEW_TOTAL"
        unit = "quantity units"
        representation = (
            f"Concrete: append {percent} percent-cells to a 100-cell original strip.",
            "Visual: distinguish original bar, change bar, and combined new-total bar.",
            f"Symbolic: new = {original} + ({percent}/100)({original}).",
        )

    # A misconception formula can occasionally coincide with the correct value
    # (for example, a 50% discount amount equals the final price). Such an
    # observation is mathematically ambiguous and must not be labelled wrong.
    wrong = {code: value for code, value in wrong.items() if value != answer}
    if not wrong:
        raise AssertionError("Every variant must retain a non-colliding diagnostic")
    return Variant(
        variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
        family=family,
        canonical_skill=CANONICAL_SKILL[family],
        mode=mode,
        structure=structure,
        prompt=prompt,
        parameters=tuple(sorted(params.items())),
        answer=answer,
        answer_kind="choice" if family == "MATH.RATE.COMPARE" else "exact_rational",
        answer_unit=unit,
        representation=representation,
        misconception_answers=tuple(sorted(wrong.items())),
    )


def verification_equation(variant: Variant) -> str:
    """Return a family-specific exact verification statement."""

    p = dict(variant.parameters)
    family = variant.family
    if family == "MATH.RATIO.EQUIVALENT":
        return f"{p['a']}*{variant.answer} = {p['b']}*{p['target_a']}"
    if family == "MATH.RATIO.PART_WHOLE":
        return f"{variant.answer}/({p['total']}-{variant.answer}) = {p['first_parts']}/{p['second_parts']}"
    if family == "MATH.RATIO.TABLE.MISSING":
        return f"{variant.answer}/{p['target_scale']} = {p['b']}"
    if family == "MATH.RATIO.RECIPE":
        return f"{variant.answer}/{p['batches']} = {p['cups_per_batch']}"
    if family == "MATH.RATE.UNIT":
        return f"({variant.answer})*{p['quantity']} = {p['total']}"
    if family == "MATH.RATE.COMPARE":
        return "compare exact cost/quantity fractions; lower unit rate wins"
    if family == "MATH.PCT.OF_QUANTITY":
        return f"{variant.answer} = {p['percent']}/100*{p['whole']}"
    if family == "MATH.PCT.FIND_WHOLE":
        return f"{p['part']} = {p['percent']}/100*{variant.answer}"
    if family == "MATH.PCT.DISCOUNT":
        return f"{variant.answer}+{p['discount']} = {p['original']}"
    return f"{variant.answer}-{p['change']} = {p['original']}"


_REPAIR: Final = MappingProxyType(
    {
        "RATIO_ONE_SIDED_SCALE": (
            "Which multiplier changed the first quantity?",
            "What must that same multiplier do to the second quantity?",
            "Pair corresponding batch cards before writing the new row.",
        ),
        "RATIO_ADDITIVE_SCALE": (
            "Does adding the same difference preserve every ratio?",
            "What common multiplier maps the first term to its target?",
            "Use two aligned ratio-table rows and mark the multiplicative arrows.",
        ),
        "RATIO_PART_PART_AS_FRACTION_OF_WHOLE": (
            "How many equal parts make the whole mixture?",
            "Is the denominator one part or all parts together?",
            "Partition a tape into first-parts plus second-parts before shading.",
        ),
        "RATIO_SECOND_PART_SELECTED": (
            "Which ingredient does the question name?",
            "How many ratio parts belong to that ingredient?",
            "Label both sections of the tape before calculating.",
        ),
        "RATIO_CONSTANT_DIFFERENCE": (
            "Must proportional points keep a difference or a quotient constant?",
            "What is y/x at the known point?",
            "Draw both number lines from zero and align equal scale factors.",
        ),
        "RATIO_REPEATS_PREVIOUS_ROW": (
            "Did the target move to a new tick?",
            "What scale factor labels that tick?",
            "Trace one vertical alignment at a time on the double number line.",
        ),
        "RATIO_ADD_SERVING_DIFFERENCE": (
            "Are extra batches made by addition or repeated equal groups?",
            "How many complete batches are needed?",
            "Lay out one batch card per equal serving group.",
        ),
        "RATIO_INVERTED_UNIT_RATE": (
            "Which rate is cups per serving?",
            "What units remain after multiplying by servings?",
            "Write units beside numerator and denominator before multiplying.",
        ),
        "RATE_INVERTED_UNITS": (
            "Does the question ask litres per minute or minutes per litre?",
            "Which quantity must become one?",
            "Label the two rows of a rate table before dividing.",
        ),
        "RATE_MULTIPLIES_TOTALS": (
            "A unit rate describes one minute; should the total be shared or enlarged?",
            "What operation makes the minute count equal one?",
            "Share litre tokens equally among minute boxes.",
        ),
        "RATE_COMPARE_TOTAL_PRICE_ONLY": (
            "Can unequal package sizes be compared by totals alone?",
            "What does each package cost for one item?",
            "Scale both packages to one item in parallel tables.",
        ),
        "RATE_COMPARE_LARGER_RATE_AS_BETTER": (
            "For cost, is a larger amount per item the better value?",
            "Which exact unit price is lower?",
            "Place both unit prices on the same labelled number line.",
        ),
        "PERCENT_USES_PERCENT_AS_WHOLE_NUMBER": (
            "What fraction does the percent symbol mean?",
            "Where should the factor 100 appear?",
            "Shade a 100-grid before writing the multiplier.",
        ),
        "PERCENT_SUBTRACTS_FROM_WHOLE": (
            "Is this asking for a percent of the whole or a decrease?",
            "What operation does 'of' represent?",
            "Align percent and quantity number lines at 0 and 100%.",
        ),
        "PERCENT_MULTIPLIES_TO_FIND_WHOLE": (
            "Is the known part smaller than the whole?",
            "Which inverse operation undoes multiplication by the percent rate?",
            "Extend the percent strip from the known percent to 100%.",
        ),
        "PERCENT_TREATS_PART_AS_WHOLE": (
            "Does the known value represent 100%?",
            "What value must align with 100%?",
            "Label the known partial bar before extending it to a whole bar.",
        ),
        "PERCENT_REPORTS_DISCOUNT_NOT_FINAL": (
            "Did you find the amount removed or the amount remaining?",
            "How are original, discount, and final price related?",
            "Use separate labelled bars for discount and remainder.",
        ),
        "PERCENT_ADDS_DISCOUNT": (
            "Does a discount increase or decrease the original?",
            "Which sign connects original and discount amount?",
            "Physically remove the shaded discount cells from the price strip.",
        ),
        "PERCENT_REPORTS_CHANGE_NOT_NEW_TOTAL": (
            "Did you find only the increase or the new total?",
            "What must be combined after the change is known?",
            "Join the original bar and change bar end to end.",
        ),
        "PERCENT_USES_NEW_TOTAL_AS_BASE": (
            "Which quantity existed before the increase?",
            "What value is the percent rate applied to?",
            "Bracket the original bar as the base before attaching the change bar.",
        ),
    }
)


def guided_repair(variant: Variant, submitted: str) -> dict[str, object] | None:
    """Return misconception-specific guided support; never operate in assessed modes."""

    if variant.mode != "guided":
        return None
    normalized = submitted.strip().upper() if variant.answer_kind == "choice" else submitted.strip()
    if normalized == variant.answer:
        return {"classification": "CORRECT_NO_REMEDIATION", "questions": ()}

    matches: list[str] = []
    for code, wrong_answer in variant.misconception_answers:
        candidate = wrong_answer.upper() if variant.answer_kind == "choice" else wrong_answer
        if normalized == candidate:
            matches.append(code)

    if len(matches) > 1:
        return {
            "classification": "AMBIGUOUS_RESPONSE_NEEDS_REASONING",
            "questions": (
                "Which quantities did you compare, and what operation or relationship did you use?",
                "What calculation or representation would distinguish the possible strategies?",
            ),
            "representation_move": (
                "Show the intermediate comparison with ordered units before choosing a correction."
            ),
            "fresh_exit_family": TRANSFER_PARTNER[variant.family],
        }

    if len(matches) == 1:
        code = matches[0]
        q1, q2, move = _REPAIR[code]
        return {
            "classification": code,
            "questions": (q1, q2),
            "representation_move": move,
            "fresh_exit_family": TRANSFER_PARTNER[variant.family],
        }

    return {
        "classification": "UNCLASSIFIED_NO_ANSWER_REVEAL",
        "questions": ("Which two quantities and ordered units are being compared?",),
        "representation_move": "Re-label the given quantities before choosing an operation.",
        "fresh_exit_family": TRANSFER_PARTNER[variant.family],
    }

def generate_transfer(source: Variant, *, seed_offset: int = 1_000_003) -> Variant:
    """Generate a structurally different unseen independent transfer item."""

    if source.mode not in {"diagnostic", "guided"}:
        raise ValueError("transfer source must be diagnostic or guided")
    return generate(
        TRANSFER_PARTNER[source.family], source_seed(source) + seed_offset, "independent"
    )


def source_seed(variant: Variant) -> int:
    return int(variant.variant_id.rsplit(":", 1)[-1])
