"""Original draft depth layer for teacher-evidenced center/data reasoning (#424).

Uses existing canonical center/rate concepts without declaring new taxonomy or
Ontario expectation authority. No worksheet wording or figures are reproduced.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
STRUCTURES = (
    "FAIR_RATE_COMPARISON",
    "DISTINCT_FIVE_VALUE_MAXIMUM",
    "MISSING_EXTREME_FROM_MEAN_MEDIAN",
)
PHASES = (
    "OBSERVE", "PREDICT", "MANIPULATE", "EXPLAIN",
    "PRACTICE", "DIAGNOSE", "TRANSFER", "VERIFY",
)
REUSABLE_FAMILIES = (
    "MATH.DATA.MEAN",
    "MATH.DATA.MEDIAN",
    "MATH.DATA.MISSING_MEAN",
)
REASONS = {
    "FAIR_RATE_COMPARISON": "DIVIDE_TOTAL_BY_PARTICIPANTS",
    "DISTINCT_FIVE_VALUE_MAXIMUM": "MINIMIZE_OTHER_DISTINCT_VALUES",
    "MISSING_EXTREME_FROM_MEAN_MEDIAN": "RECOVER_TOTAL_THEN_SUBTRACT_KNOWN",
}
SOCRATIC = {
    "STAT.CENTER.RAW_TOTAL_BIAS": (
        "Do the groups have the same number of participants?",
        "What is the contribution per person in each group?",
        "Does the raw-total leader still lead after a fair comparison?",
    ),
    "STAT.CENTER.FORGOT_DENOMINATOR": (
        "How many people share that group's total?",
        "Which operation gives an amount per person?",
        "What unit should the resulting quotient have?",
    ),
    "STAT.CENTER.QUOTIENT_ERROR": (
        "Can you multiply each proposed per-person value by its group size?",
        "Does that reconstruct the group's original total?",
        "Which quotient needs revision?",
    ),
    "STAT.CENTER.DUPLICATED_DISTINCT_VALUE": (
        "Can any two values be the same if the problem says distinct?",
        "Which smaller positive integers can be chosen without duplicates?",
        "Does the corrected collection still have the required median and mean?",
    ),
    "STAT.CENTER.MEAN_AS_SUM": (
        "How many entries are in the data set?",
        "What total is required by the stated mean?",
        "Does your collection have that sum?",
    ),
    "STAT.CENTER.NOT_MAXIMAL": (
        "How small can the first two positive distinct entries be?",
        "What is the smallest fourth entry above the median?",
        "How does reserving the least total for those entries maximize the last?",
    ),
    "STAT.CENTER.MEAN_AS_TOTAL": (
        "Is the mean the sum or the sum divided by the number of entries?",
        "How do you reconstruct the total from a mean and a count?",
        "What remains when the known values are subtracted?",
    ),
    "STAT.CENTER.ORDER_CONSTRAINT": (
        "Which value must be the middle of three ordered numbers?",
        "Can the proposed maximum be smaller than the median?",
        "Does the sorted list satisfy all the stated conditions?",
    ),
    "STAT.CENTER.JUSTIFICATION_MISSING": (
        "What equality or rate justifies your choice?",
        "Can the relevant calculation be reconstructed independently?",
        "Which constraint would be violated by the competing answer?",
    ),
    "STAT.CENTER.UNCLASSIFIED": (
        "Which total or ordered list are you using?",
        "What does each number represent?",
        "Can you verify every condition independently?",
    ),
}
_FRACTION = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z")


def _valid(index: int, mode: str) -> None:
    if type(index) is not int or index < 0:
        raise ValueError("index must be a non-negative integer")
    if mode not in {"guided", "independent"}:
        raise ValueError("mode must be guided or independent")


def _wire(value: Fraction | int) -> str:
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _parse(value: object) -> Fraction:
    if not isinstance(value, str) or not _FRACTION.fullmatch(value):
        raise ValueError("value must be an exact rational string")
    exact = Fraction(value)
    if _wire(exact) != value:
        raise ValueError("rational must be reduced and canonically signed")
    return exact


@dataclass(frozen=True)
class DraftVariant:
    index: int
    mode: str
    structure: str
    variant_id: str
    prompt: str
    values: dict[str, Any]
    teacher_oracle: dict[str, Any]

    def public_payload(self) -> dict[str, Any]:
        result = {
            "status": STATUS,
            "runtime_activation": RUNTIME_ACTIVATION,
            "variant_id": self.variant_id if self.mode == "guided" else None,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
            "response_fields": list(self.teacher_oracle["response_fields"]),
            "mastery_credit": False,
        }
        if self.mode == "guided":
            result.update(
                phases=list(PHASES),
                representations=["CONCRETE_COUNTERS", "VISUAL_ORDERED_DOT_PLOT", "SYMBOLIC_TABLE"],
                prediction_required_before_manipulation=True,
                scaffold_fading_requires_repair_and_fresh_exit=True,
                accessible_mve_status="NOT_WIRED",
            )
        else:
            result.update(
                hints=[],
                worked_steps=[],
                guided_feedback_available=False,
                backend_trusted_scoring="REQUIRED_NOT_WIRED",
            )
            del result["variant_id"]
        return result


def generate(index: int, mode: str) -> DraftVariant:
    """Mode-separated, deterministic synthetic variants of existing math."""

    _valid(index, mode)
    rng = random.Random(f"mihur:ontario-center-depth:{index}:{mode}")
    structure = STRUCTURES[index % len(STRUCTURES)]
    variant_id = f"ontario-center-depth:{mode}:{index}"

    if structure == "FAIR_RATE_COMPARISON":
        small = rng.randint(10, 12) if mode == "guided" else rng.randint(7, 9)
        large = rng.randint(40, 43) if mode == "guided" else rng.randint(47, 51)
        middle = rng.randint(18, 21)
        counts = (small, large, middle)
        rates = (rng.randint(10, 12), 4, 6)
        totals = tuple(n * rate for n, rate in zip(counts, rates, strict=True))
        assert totals[1] > max(totals[0], totals[2])
        prompt = (
            f"Three original community teams have (participants, total items): "
            f"A=({counts[0]}, {totals[0]}), B=({counts[1]}, {totals[1]}), "
            f"C=({counts[2]}, {totals[2]}). Name the highest per-person team, "
            "show all exact per-person rates, and justify why the comparison is fair."
        )
        oracle = {
            "response_fields": ("rates", "winner", "reason"),
            "rates": tuple(Fraction(x) for x in rates),
            "winner": "A",
            "raw_total_winner": "B",
            "reason": REASONS[structure],
        }
        values = {"participants": counts, "totals": totals}
    elif structure == "DISTINCT_FIVE_VALUE_MAXIMUM":
        median = rng.randint(6, 14) if mode == "guided" else rng.randint(17, 25)
        total = 5 * median
        optimal = (1, 2, median, median + 1, 3 * median - 4)
        assert len(set(optimal)) == 5 and sum(optimal) == total
        prompt = (
            "Construct five distinct positive integers with "
            f"mean {median} and median {median}. "
            "Make the largest number as large as mathematically possible. "
            "Provide the full set and justify why no larger maximum is possible."
        )
        oracle = {
            "response_fields": ("values", "largest", "reason"),
            "values": optimal,
            "largest": optimal[-1],
            "sum": total,
            "reason": REASONS[structure],
        }
        values = {"mean": median, "median": median, "count": 5}
    else:
        minimum = rng.randint(1, 6) if mode == "guided" else rng.randint(8, 13)
        median = minimum + rng.randint(3, 6)
        maximum = median + rng.randint(3, 9)
        mean = Fraction(minimum + median + maximum, 3)
        prompt = (
            "Three ordered nonnegative integer measurements have "
            f"smallest value {minimum}, median {median}, and mean {_wire(mean)}. "
            "Determine the largest value, reconstruct the total, "
            "and verify the ordering."
        )
        oracle = {
            "response_fields": ("largest", "total", "reason"),
            "largest": maximum,
            "total": Fraction(minimum + median + maximum),
            "reason": REASONS[structure],
        }
        values = {"minimum": minimum, "median": median, "mean": mean}
    return DraftVariant(index, mode, structure, variant_id, prompt, values, oracle)


def diagnose_guided(item: DraftVariant, response: object) -> dict[str, Any]:
    """Return response-derived Socratic diagnosis, never mastery evidence."""

    if not isinstance(item, DraftVariant):
        raise TypeError("item must be a draft variant")
    if item.mode != "guided":
        raise PermissionError("no guided feedback in independent assessment")
    if not isinstance(response, dict):
        raise TypeError("response must be a dictionary")
    required = set(item.teacher_oracle["response_fields"])
    if set(response) != required:
        raise ValueError("response must have exactly the expected evidence fields")
    expected = item.teacher_oracle
    structure = item.structure
    reason = response.get("reason")
    if not isinstance(reason, str):
        raise TypeError("reason must be a justification code")

    if structure == "FAIR_RATE_COMPARISON":
        rates = response["rates"]
        if not isinstance(rates, list) or len(rates) != 3:
            raise ValueError("rates must be three exact rational strings")
        parsed = tuple(_parse(rate) for rate in rates)
        winner = response["winner"]
        if not isinstance(winner, str) or winner not in {"A", "B", "C"}:
            raise ValueError("winner must be A, B or C")
        correct = (
            parsed == expected["rates"]
            and winner == expected["winner"]
            and reason == expected["reason"]
        )
        if winner == expected["raw_total_winner"] and winner != expected["winner"]:
            misconception = "STAT.CENTER.RAW_TOTAL_BIAS"
        elif parsed == tuple(Fraction(x) for x in item.values["totals"]):
            misconception = "STAT.CENTER.FORGOT_DENOMINATOR"
        elif parsed != expected["rates"]:
            misconception = "STAT.CENTER.QUOTIENT_ERROR"
        else:
            misconception = "STAT.CENTER.JUSTIFICATION_MISSING"
    elif structure == "DISTINCT_FIVE_VALUE_MAXIMUM":
        values = response["values"]
        largest = response["largest"]
        if not isinstance(values, list) or len(values) != 5 or any(type(x) is not int for x in values):
            raise ValueError("values must contain five integer entries")
        if type(largest) is not int:
            raise ValueError("largest must be an integer")
        ordered = tuple(sorted(values))
        correct = ordered == expected["values"] and largest == expected["largest"] and reason == expected["reason"]
        if len(set(values)) != 5:
            misconception = "STAT.CENTER.DUPLICATED_DISTINCT_VALUE"
        elif sum(values) != expected["sum"]:
            misconception = "STAT.CENTER.MEAN_AS_SUM"
        elif largest != expected["largest"] or ordered != expected["values"]:
            misconception = "STAT.CENTER.NOT_MAXIMAL"
        else:
            misconception = "STAT.CENTER.JUSTIFICATION_MISSING"
    else:
        largest = response["largest"]
        if type(largest) is not int:
            raise ValueError("largest must be an integer")
        total = _parse(response["total"])
        correct = (
            largest == expected["largest"]
            and total == expected["total"]
            and reason == expected["reason"]
        )
        if total == item.values["mean"]:
            misconception = "STAT.CENTER.MEAN_AS_TOTAL"
        elif largest < item.values["median"]:
            misconception = "STAT.CENTER.ORDER_CONSTRAINT"
        else:
            misconception = "STAT.CENTER.JUSTIFICATION_MISSING"

    if correct:
        return {"correct": True, "misconception_id": None, "socratic_questions": [],
                "mastery_credit": False}
    return {"correct": False, "misconception_id": misconception,
            "socratic_questions": list(SOCRATIC[misconception]), "mastery_credit": False}


def fresh_repair_exit(item: DraftVariant) -> DraftVariant:
    """A new *different* structure before guided supports may fade."""

    if not isinstance(item, DraftVariant) or item.mode != "guided":
        raise PermissionError("fresh repair exits are guided only")
    next_structure = (item.index + 1) % len(STRUCTURES)
    index = 30_000 + item.index * len(STRUCTURES) + next_structure
    candidate = generate(index, "guided")
    assert candidate.structure != item.structure
    return candidate
