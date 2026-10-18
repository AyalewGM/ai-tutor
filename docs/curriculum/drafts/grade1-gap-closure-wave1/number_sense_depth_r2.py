"""Draft-only Grade 1 number-sense and place-value depth families.

This module is deliberately outside ``app``.  It deepens two existing package
concepts without registering content, changing mappings, or writing evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
REVISION = "g1-number-place-depth-r2"

COUNT_CONCEPT = "G1-COUNT-REPRESENT"
PLACE_CONCEPT = "G1-PLACE-VALUE"
CONCEPTS = (COUNT_CONCEPT, PLACE_CONCEPT)
MODES = ("diagnostic", "guided", "independent", "mastery")

COUNT_FAMILIES = (
    "QUANTITY_TO_NUMERAL",
    "COUNT_ON_CROSS_DECADE",
    "COMPARE_BY_PLACE",
    "ORDER_RETAIN_DUPLICATES",
    "ONE_MORE_ONE_LESS_BOUNDARY",
)
PLACE_FAMILIES = (
    "COMPOSE_BASE_TEN",
    "DECOMPOSE_BASE_TEN",
    "DIGIT_VALUE",
    "EXCHANGE_INVARIANCE",
    "TEEN_VS_MULTIPLE_TEN",
    "ZERO_ONES_PLACEHOLDER",
)

_MODE_OFFSET = {"diagnostic": 0, "guided": 1, "independent": 2, "mastery": 3}


@dataclass(frozen=True)
class Variant:
    concept_id: str
    family_code: str
    mode: str
    seed: int
    item_id: str
    prompt: str
    response_fields: tuple[str, ...]
    visual_model: dict[str, object]
    interaction: dict[str, object]
    oracle: dict[str, object]
    misconception_responses: dict[str, object]
    socratic_repairs: dict[str, str]

    def public_payload(self) -> dict[str, object]:
        return {
            "concept_id": self.concept_id,
            "family_code": self.family_code,
            "mode": self.mode,
            "item_id": self.item_id,
            "prompt": self.prompt,
            "response_fields": list(self.response_fields),
            "visual_model": dict(self.visual_model),
            "interaction": dict(self.interaction),
        }

    def teacher_oracle(self) -> dict[str, object]:
        return dict(self.oracle)


def _validate(concept_id: str, seed: int, mode: str) -> None:
    if concept_id not in CONCEPTS:
        raise ValueError("unknown Grade 1 depth concept")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if mode not in MODES:
        raise ValueError("unsupported learning mode")


def _family(concept_id: str, seed: int, mode: str) -> str:
    families = COUNT_FAMILIES if concept_id == COUNT_CONCEPT else PLACE_FAMILIES
    return families[(seed + _MODE_OFFSET[mode]) % len(families)]


def _interaction(kind: str, state_template: str) -> dict[str, object]:
    return {
        "kind": kind,
        "keyboard": "Tab to the model; use arrow keys to move; Space toggles or places; Enter submits.",
        "screen_reader_state_template": state_template,
        "focus_after_feedback": "Return focus to the first changed mathematical object.",
        "reduced_motion": True,
        "color_only_meaning": False,
    }


def _count_variant(family: str, rng: Random) -> tuple:
    if family == "QUANTITY_TO_NUMERAL":
        tens = rng.randint(1, 11)
        ones = rng.randint(0, 9)
        value = 10 * tens + ones
        prompt = (
            f"A collection is bundled as {tens} tens and {ones} single counters. "
            "Write the numeral and explain how the bundles prove it."
        )
        oracle = {
            "numeral": value,
            "reconstruction": {"tens_value": 10 * tens, "ones_value": ones},
            "equation": f"{10 * tens}+{ones}={value}",
        }
        misconceptions = {"COUNT_AS_OBJECTS_ONLY": tens + ones}
        repairs = {
            "COUNT_AS_OBJECTS_ONLY": (
                "Does one tens bundle represent one object or ten objects? What value do all the bundles have?"
            )
        }
        return (
            prompt,
            ("numeral", "bundle_explanation"),
            {"kind": "bundled_counters", "tens_bundles": tens, "single_counters": ones},
            _interaction(
                "counter_bundles",
                "{tens_bundles} bundles of ten and {single_counters} single counters",
            ),
            oracle,
            misconceptions,
            repairs,
        )

    if family == "COUNT_ON_CROSS_DECADE":
        start = rng.randint(87, 107)
        sequence = tuple(start + i for i in range(6))
        missing_index = rng.choice((1, 2, 3, 4))
        shown = tuple("blank" if i == missing_index else value for i, value in enumerate(sequence))
        prompt = (
            f"Count on by ones from {start}. Fill the blank in {shown} and explain what changes when "
            "the count crosses a new ten."
        )
        oracle = {
            "missing_number": sequence[missing_index],
            "sequence": sequence,
            "step_checks": tuple(sequence[i + 1] - sequence[i] for i in range(5)),
        }
        misconceptions = {"COUNT_SKIPS": sequence[missing_index] + 1}
        repairs = {
            "COUNT_SKIPS": (
                "What number is exactly one more than the number before the blank? Check it on the number line."
            )
        }
        return (
            prompt,
            ("missing_number", "crossing_explanation"),
            {"kind": "number_line", "minimum": start, "maximum": start + 5, "shown": shown},
            _interaction("number_line", "Number line from {minimum} through {maximum}; {shown}"),
            oracle,
            misconceptions,
            repairs,
        )

    if family == "COMPARE_BY_PLACE":
        tens = rng.randint(1, 8)
        left = 10 * tens + rng.randint(6, 9)
        right = 10 * (tens + 1) + rng.randint(0, 3)
        if rng.choice((True, False)):
            left, right = right, left
        relation = ">" if left > right else "<"
        prompt = (
            f"Compare {left} and {right}. Choose <, =, or >, then justify the choice by comparing tens "
            "before ones."
        )
        oracle = {
            "relation": relation,
            "left_tens": left // 10,
            "left_ones": left % 10,
            "right_tens": right // 10,
            "right_ones": right % 10,
        }
        misconceptions = {"COMPARE_DIGITS_ONLY": ">" if left % 10 > right % 10 else "<"}
        repairs = {
            "COMPARE_DIGITS_ONLY": (
                "Which place has the greatest value? If the tens are equal, which ones amount is larger?"
            )
        }
        return (
            prompt,
            ("relation", "place_value_justification"),
            {
                "kind": "paired_base_ten",
                "left": {"tens": left // 10, "ones": left % 10},
                "right": {"tens": right // 10, "ones": right % 10},
            },
            _interaction(
                "paired_base_ten",
                "Left has {left.tens} tens and {left.ones} ones; right has {right.tens} tens and {right.ones} ones",
            ),
            oracle,
            misconceptions,
            repairs,
        )

    if family == "ORDER_RETAIN_DUPLICATES":
        values = [rng.randint(12, 118) for _ in range(3)]
        values.append(values[rng.randrange(3)])
        rng.shuffle(values)
        ordered = tuple(sorted(values))
        prompt = (
            f"Order {tuple(values)} from least to greatest. Keep every entry, including repeated values, "
            "and explain one neighboring comparison."
        )
        oracle = {"ordered": ordered, "input_count": 4, "output_count": len(ordered)}
        misconceptions = {"ORDER_DROPS_DUPLICATE": tuple(sorted(set(values)))}
        repairs = {
            "ORDER_DROPS_DUPLICATE": (
                "How many entries were given? How many must remain after ordering, even when two are equal?"
            )
        }
        return (
            prompt,
            ("ordered_list", "neighbor_comparison"),
            {"kind": "order_cards", "cards": tuple(values), "retain_duplicates": True},
            _interaction("order_cards", "Four number cards: {cards}; repeated cards must remain"),
            oracle,
            misconceptions,
            repairs,
        )

    value = rng.choice((9, 10, 19, 20, 29, 30, 98, 99, 100, 109, 110, 119))
    prompt = (
        f"Name the number one less than {value} and the number one more than {value}. "
        "Use the number line to verify both neighbors."
    )
    oracle = {"one_less": value - 1, "one_more": value + 1, "center": value}
    misconceptions = {"BOUNDARY_DIGIT_RESET": {"one_less": value - 1, "one_more": value + 10}}
    repairs = {
        "BOUNDARY_DIGIT_RESET": (
            "Move exactly one step from the center. Which numeral is on that adjacent tick?"
        )
    }
    return (
        prompt,
        ("one_less", "one_more"),
        {"kind": "number_line", "minimum": value - 2, "maximum": value + 2, "center": value},
        _interaction("number_line", "Five consecutive numbers centered on {center}"),
        oracle,
        misconceptions,
        repairs,
    )


def _place_variant(family: str, rng: Random) -> tuple:
    if family == "COMPOSE_BASE_TEN":
        tens, ones = rng.randint(1, 9), rng.randint(0, 9)
        value = 10 * tens + ones
        prompt = (
            f"Compose a number from {tens} tens and {ones} ones. Write the numeral and equation."
        )
        oracle = {"numeral": value, "equation": f"{10 * tens}+{ones}={value}"}
        misconceptions = {"FACE_VALUE_ONLY": tens + ones}
    elif family == "DECOMPOSE_BASE_TEN":
        tens, ones = rng.randint(1, 9), rng.randint(0, 9)
        if tens == ones:
            ones = (ones + 1) % 10
        value = 10 * tens + ones
        prompt = f"Decompose {value} into tens and ones, then verify by rebuilding the total."
        oracle = {"tens": tens, "ones": ones, "reconstruction": 10 * tens + ones}
        misconceptions = {"TEEN_TEN": {"tens": ones, "ones": tens}}
    elif family == "DIGIT_VALUE":
        value = rng.randint(10, 99)
        place = rng.choice(("tens", "ones"))
        digit = value // 10 if place == "tens" else value % 10
        place_value = digit * 10 if place == "tens" else digit
        prompt = f"In {value}, what is the value of the digit in the {place} place? Explain digit versus value."
        oracle = {"digit": digit, "place": place, "digit_value": place_value}
        misconceptions = {"FACE_VALUE_ONLY": digit if place == "tens" else digit * 10 + 1}
        tens, ones = divmod(value, 10)
    elif family == "EXCHANGE_INVARIANCE":
        tens, ones = rng.randint(2, 9), rng.randint(0, 9)
        value = 10 * tens + ones
        prompt = (
            f"Start with {tens} tens and {ones} ones. Exchange one ten for ten ones. "
            "Record the new counts and prove the value did not change."
        )
        oracle = {
            "before": {"tens": tens, "ones": ones, "total": value},
            "after": {"tens": tens - 1, "ones": ones + 10, "total": value},
            "difference": 0,
        }
        misconceptions = {"EXCHANGE_CHANGES_VALUE": value + 10}
    elif family == "TEEN_VS_MULTIPLE_TEN":
        digit = rng.randint(2, 9)
        teen = 10 + digit
        multiple = 10 * digit
        prompt = (
            f"Contrast {teen} and {multiple}. Build both numbers and explain why the same digit {digit} "
            "has a different value in each numeral."
        )
        oracle = {
            "teen": {"tens": 1, "ones": digit, "value": teen},
            "multiple_ten": {"tens": digit, "ones": 0, "value": multiple},
            "difference": abs(multiple - teen),
        }
        misconceptions = {"TEEN_TEN": {"teen": multiple, "multiple_ten": teen}}
        tens, ones = 1, digit
    else:
        tens = rng.randint(1, 9)
        ones = 0
        value = 10 * tens
        prompt = (
            f"Build {value}. Explain why the zero in the ones place is necessary and why "
            f"{tens} is worth {value}, not {tens}."
        )
        oracle = {"tens": tens, "ones": 0, "value": value, "zero_placeholder": True}
        misconceptions = {"ZERO_PLACE_IGNORED": tens}

    repairs = {
        "FACE_VALUE_ONLY": (
            "What is one counter in the tens column worth? Replace each ten with ten ones and recount."
        ),
        "TEEN_TEN": (
            "Which digit is in the tens place and which is in the ones place? Build each place separately."
        ),
        "EXCHANGE_CHANGES_VALUE": (
            "After trading, how many ones replace the removed ten? Compare both totals before deciding."
        ),
        "ZERO_PLACE_IGNORED": (
            "What would the numeral mean without the zero? Which place needs a placeholder?"
        ),
    }
    return (
        prompt,
        ("model", "symbolic_answer", "verification"),
        {"kind": "place_value_mat", "tens": tens, "ones": ones},
        _interaction("place_value_mat", "Tens column has {tens}; ones column has {ones}"),
        oracle,
        misconceptions,
        {code: repairs[code] for code in misconceptions},
    )


def generate(concept_id: str, seed: int, mode: str) -> Variant:
    _validate(concept_id, seed, mode)
    family = _family(concept_id, seed, mode)
    rng = Random(f"{REVISION}:{concept_id}:{family}:{mode}:{seed}")
    parts = (
        _count_variant(family, rng) if concept_id == COUNT_CONCEPT else _place_variant(family, rng)
    )
    prompt, fields, visual, interaction, oracle, misconceptions, repairs = parts
    return Variant(
        concept_id=concept_id,
        family_code=family,
        mode=mode,
        seed=seed,
        item_id=f"{REVISION}:{concept_id}:{family}:{mode}:{seed}",
        prompt=prompt,
        response_fields=fields,
        visual_model=visual,
        interaction=interaction,
        oracle=oracle,
        misconception_responses=misconceptions,
        socratic_repairs=repairs,
    )
