"""Draft-only Grade 2 place-value and pattern depth families.

The module extends the existing Grade 2 package once for reuse across approved
local mappings.  It is intentionally outside ``app``: nothing here is seeded,
routed, scored, or allowed to write learner evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
REVISION = "g2-place-pattern-depth-r2.1"

PLACE_CONCEPT = "G2-PLACE-VALUE"
PATTERN_CONCEPT = "G2-SKIP-PATTERNS"
CONCEPTS = (PLACE_CONCEPT, PATTERN_CONCEPT)
MODES = ("diagnostic", "guided", "independent", "mastery")

PLACE_FAMILIES = (
    "COMPOSE_NONSTANDARD_COUNTS",
    "REPRESENTATION_TRANSLATION",
    "REPEATED_DIGIT_VALUE",
    "EXCHANGE_HUNDRED_TENS",
    "COMPARE_FIRST_DIFFERENCE",
    "ORDER_RETAIN_DUPLICATES",
    "INVENTORY_TRANSFER",
)
PATTERN_FAMILIES = (
    "EXTEND_FORWARD",
    "EXTEND_BACKWARD",
    "MISSING_INTERNAL_TERM",
    "INFER_CONSTANT_STEP",
    "REPAIR_BROKEN_TERM",
    "PLACE_VALUE_CHANGE",
    "SCHEDULE_TRANSFER",
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
        """Return answer-free learner fields."""

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

    def guided_support_for_response(self, response: object) -> dict[str, str] | None:
        """Return one Socratic repair only after a guided misconception match.

        Diagnostic, independent, and mastery variants cannot expose authored
        repairs. Unknown guided responses also fail closed rather than receiving
        a generic hint that might reveal the hidden oracle.
        """

        if self.mode != "guided":
            return None
        for code, misconception_response in self.misconception_responses.items():
            if response == misconception_response:
                return {
                    "misconception_code": code,
                    "socratic_prompt": self.socratic_repairs[code],
                }
        return None


def _validate(concept_id: str, seed: int, mode: str) -> None:
    if concept_id not in CONCEPTS:
        raise ValueError("unknown Grade 2 depth concept")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if mode not in MODES:
        raise ValueError("unsupported learning mode")


def _family(concept_id: str, seed: int, mode: str) -> str:
    families = PLACE_FAMILIES if concept_id == PLACE_CONCEPT else PATTERN_FAMILIES
    return families[(seed + _MODE_OFFSET[mode]) % len(families)]


def _interaction(kind: str, state_template: str) -> dict[str, object]:
    return {
        "kind": kind,
        "keyboard": "Tab to the model; use arrow keys to move; Space selects; Enter submits.",
        "screen_reader_state_template": state_template,
        "focus_after_feedback": "Return focus to the first inconsistent mathematical object.",
        "reduced_motion": True,
        "color_only_meaning": False,
    }


def _place_variant(family: str, rng: Random) -> tuple:
    if family == "COMPOSE_NONSTANDARD_COUNTS":
        hundreds = rng.randint(1, 6)
        tens = rng.randint(10, 18)
        ones = rng.randint(0, 9)
        value = 100 * hundreds + 10 * tens + ones
        canonical = (value // 100, (value // 10) % 10, value % 10)
        prompt = (
            f"A model has {hundreds} hundreds, {tens} tens, and {ones} ones. "
            "Find its value, then rename it with fewer than ten tens."
        )
        oracle = {
            "value": value,
            "given_inventory": (hundreds, tens, ones),
            "canonical_inventory": canonical,
            "reconstruction": 100 * hundreds + 10 * tens + ones,
        }
        misconceptions = {"COUNT_AS_DIGITS": 100 * hundreds + 10 * (tens % 10) + ones}
        repairs = {
            "COUNT_AS_DIGITS": (
                "Which ten tens can be exchanged for one hundred? What quantity remains unchanged?"
            )
        }
        visual = {"kind": "base_ten_inventory", "hundreds": hundreds, "tens": tens, "ones": ones}
        fields = ("value", "canonical_inventory", "invariance_equation")

    elif family == "REPRESENTATION_TRANSLATION":
        hundreds = rng.randint(1, 9)
        if rng.choice((True, False)):
            tens, ones = 0, rng.randint(1, 9)
            omitted_placeholder = int(f"{hundreds}{ones}")
        else:
            tens, ones = rng.randint(1, 9), 0
            omitted_placeholder = 10 * hundreds + tens
        value = 100 * hundreds + 10 * tens + ones
        prompt = (
            f"Translate {value} into expanded form and a hundreds-tens-ones inventory. "
            "Explain how each zero keeps an empty place."
        )
        oracle = {
            "standard": value,
            "expanded_terms": (100 * hundreds, 10 * tens, ones),
            "inventory": (hundreds, tens, ones),
            "reconstruction": 100 * hundreds + 10 * tens + ones,
        }
        misconceptions = {"ZERO_PLACE_OMITTED": omitted_placeholder}
        repairs = {
            "ZERO_PLACE_OMITTED": (
                "Which labelled place is empty? What happens to the other digits if its zero disappears?"
            )
        }
        visual = {
            "kind": "place_value_chart",
            "number": value,
            "columns": ("hundreds", "tens", "ones"),
        }
        fields = ("expanded_form", "inventory", "zero_placeholder_explanation")

    elif family == "REPEATED_DIGIT_VALUE":
        digit = rng.randint(1, 9)
        other = rng.choice([number for number in range(10) if number != digit])
        value = 100 * digit + 10 * other + digit
        prompt = (
            f"The digit {digit} appears twice in {value}. State the value of each occurrence and "
            "compare the two values multiplicatively."
        )
        oracle = {
            "left_value": 100 * digit,
            "right_value": digit,
            "factor": 100,
            "reconstruction": 100 * digit + 10 * other + digit,
        }
        misconceptions = {"SAME_DIGIT_SAME_VALUE": (digit, digit)}
        repairs = {
            "SAME_DIGIT_SAME_VALUE": (
                "Which units does each position count? Replace the left digit with hundreds blocks."
            )
        }
        visual = {"kind": "place_value_disks", "number": value, "highlight_digit": digit}
        fields = ("left_digit_value", "right_digit_value", "multiplicative_comparison")

    elif family == "EXCHANGE_HUNDRED_TENS":
        hundreds = rng.randint(2, 8)
        tens = rng.randint(0, 9)
        ones = rng.randint(0, 9)
        value = 100 * hundreds + 10 * tens + ones
        after = (hundreds - 1, tens + 10, ones)
        prompt = (
            f"Start with {hundreds} hundreds, {tens} tens, and {ones} ones. Exchange one "
            "hundred for tens. Record both inventories and prove the total stays fixed."
        )
        oracle = {
            "before": (hundreds, tens, ones),
            "after": after,
            "before_total": value,
            "after_total": 100 * after[0] + 10 * after[1] + after[2],
        }
        misconceptions = {"EXCHANGE_ADDS_VALUE": value + 100}
        repairs = {
            "EXCHANGE_ADDS_VALUE": (
                "Were objects added, or was one hundred renamed as ten tens? Compare both weighted sums."
            )
        }
        visual = {"kind": "exchange_mat", "before": (hundreds, tens, ones), "after": after}
        fields = ("after_inventory", "total_before", "total_after", "invariance_explanation")

    elif family == "COMPARE_FIRST_DIFFERENCE":
        hundreds = rng.randint(1, 8)
        low_tens = rng.randint(0, 8)
        high_tens = rng.randint(low_tens + 1, 9)
        left = 100 * hundreds + 10 * low_tens + rng.randint(6, 9)
        right = 100 * hundreds + 10 * high_tens + rng.randint(0, 3)
        if rng.choice((True, False)):
            left, right = right, left
        relation = ">" if left > right else "<"
        prompt = f"Compare {left} and {right}. Give the relation and identify the highest place that decides it."
        oracle = {
            "left": left,
            "right": right,
            "relation": relation,
            "first_differing_place": "tens",
        }
        ones_relation = ">" if left % 10 > right % 10 else "<"
        misconceptions = {"COMPARE_ONES_FIRST": ones_relation}
        repairs = {
            "COMPARE_ONES_FIRST": (
                "Starting at hundreds, where is the first difference? Can fewer than ten ones reverse one ten?"
            )
        }
        visual = {"kind": "paired_place_value_chart", "left": left, "right": right}
        fields = ("relation", "first_differing_place", "place_value_explanation")

    elif family == "ORDER_RETAIN_DUPLICATES":
        values = [rng.randint(100, 899) for _ in range(3)]
        values.append(values[rng.randrange(3)])
        rng.shuffle(values)
        ordered = tuple(sorted(values))
        prompt = (
            f"Order {tuple(values)} from least to greatest, retaining repeated values. "
            "Justify one adjacent comparison by place value."
        )
        oracle = {"ordered": ordered, "input_count": 4, "output_count": len(ordered)}
        misconceptions = {"DROP_DUPLICATE": tuple(sorted(set(values)))}
        repairs = {
            "DROP_DUPLICATE": (
                "How many entries were given? Why does ordering change position but not quantity?"
            )
        }
        visual = {"kind": "order_cards", "cards": tuple(values), "retain_duplicates": True}
        fields = ("ordered_values", "adjacent_comparison", "retained_count")

    else:
        cartons = rng.randint(1, 5)
        packs = rng.randint(10, 19)
        loose = rng.randint(0, 9)
        total = 100 * cartons + 10 * packs + loose
        canonical = (total // 100, (total // 10) % 10, total % 10)
        prompt = (
            f"A supply shelf has {cartons} cartons of 100, {packs} packs of 10, and {loose} "
            "loose items. Find the total and a canonical inventory; prove both name the same quantity."
        )
        oracle = {
            "total": total,
            "canonical_inventory": canonical,
            "substitution_total": 100 * cartons + 10 * packs + loose,
        }
        misconceptions = {"PACKS_AS_ONES": 100 * cartons + packs + loose}
        repairs = {
            "PACKS_AS_ONES": (
                "What unit does each pack contain? Replace one pack with ten loose items before totaling."
            )
        }
        visual = {"kind": "supply_inventory", "cartons": cartons, "packs": packs, "loose": loose}
        fields = ("total", "canonical_inventory", "verification_equation")

    return (
        prompt,
        fields,
        visual,
        _interaction(visual["kind"], "Current mathematical model: {state}"),
        oracle,
        misconceptions,
        repairs,
    )


def _pattern_variant(family: str, rng: Random) -> tuple:
    step = rng.choice((5, 10, 100))

    if family == "EXTEND_FORWARD":
        start = rng.randrange(0, 601, 5)
        sequence = tuple(start + step * index for index in range(6))
        prompt = (
            f"Continue {sequence[:3]} by the same step for three more terms and explain the rule."
        )
        oracle = {"sequence": sequence, "step": step, "step_checks": tuple(step for _ in range(5))}
        misconceptions = {"ADD_ONE": tuple(start + index for index in range(6))}
        repairs = {
            "ADD_ONE": "What is the difference between each pair of shown neighboring terms?"
        }
        visual = {"kind": "forward_number_line", "start": start, "step": step, "jumps": 5}
        fields = ("completed_sequence", "constant_step", "rule_explanation")

    elif family == "EXTEND_BACKWARD":
        minimum_endpoint = 5 * step
        end = rng.randrange(minimum_endpoint, 901 if step == 100 else 501, step)
        sequence = tuple(end - step * index for index in range(6))
        prompt = (
            f"Count backward from {end} by {step}. Give the next five terms and explain "
            "how much smaller each term becomes."
        )
        oracle = {
            "sequence": sequence,
            "signed_step": -step,
            "step_checks": tuple(-step for _ in range(5)),
        }
        misconceptions = {"FORWARD_NOT_BACKWARD": tuple(end + step * index for index in range(6))}
        repairs = {
            "FORWARD_NOT_BACKWARD": "Does moving backward make each term greater or smaller? By how much?"
        }
        visual = {
            "kind": "backward_number_line",
            "start": end,
            "direction": "backward",
            "step_size": step,
            "jumps": 5,
        }
        fields = ("completed_sequence", "decrease_amount", "direction_explanation")

    elif family == "MISSING_INTERNAL_TERM":
        start = rng.randrange(0, 501, 5)
        sequence = tuple(start + step * index for index in range(6))
        missing_index = rng.choice((1, 2, 3, 4))
        shown = tuple(
            None if index == missing_index else value for index, value in enumerate(sequence)
        )
        prompt = (
            f"Find the missing internal term in {shown}. Verify it from both neighboring terms."
        )
        oracle = {
            "missing_term": sequence[missing_index],
            "left_check": sequence[missing_index - 1] + step,
            "right_check": sequence[missing_index + 1] - step,
            "step": step,
        }
        misconceptions = {"USE_POSITION_AS_VALUE": missing_index}
        repairs = {
            "USE_POSITION_AS_VALUE": "What value is one full step after the left neighbor and before the right neighbor?"
        }
        visual = {"kind": "sequence_slots", "shown": shown, "step": step}
        fields = ("missing_term", "left_check", "right_check")

    elif family == "INFER_CONSTANT_STEP":
        start = rng.randrange(0, 401, 5)
        sequence = tuple(start + step * index for index in range(5))
        prompt = (
            f"Infer the rule for {sequence}. State the constant step and predict the sixth term."
        )
        oracle = {
            "step": step,
            "differences": tuple(sequence[index + 1] - sequence[index] for index in range(4)),
            "next_term": sequence[-1] + step,
        }
        misconceptions = {"USE_LAST_TERM_AS_STEP": sequence[-1]}
        repairs = {
            "USE_LAST_TERM_AS_STEP": (
                "Subtract consecutive whole terms. Is the same difference repeated every time?"
            )
        }
        visual = {"kind": "difference_table", "terms": sequence, "difference_slots": 4}
        fields = ("constant_step", "difference_evidence", "next_term")

    elif family == "REPAIR_BROKEN_TERM":
        start = rng.randrange(0, 401, 5)
        correct = [start + step * index for index in range(6)]
        error_index = rng.choice((2, 3, 4))
        shown = correct.copy()
        shown[error_index] += rng.choice((-1, 1)) * (1 if step != 100 else 10)
        prompt = f"One term breaks the constant-step pattern {tuple(shown)}. Identify it, repair it, and verify both adjacent differences."
        oracle = {
            "error_index": error_index,
            "incorrect_term": shown[error_index],
            "corrected_term": correct[error_index],
            "left_difference": step,
            "right_difference": step,
        }
        misconceptions = {"CHANGE_THE_RULE": shown[error_index] - shown[error_index - 1]}
        repairs = {
            "CHANGE_THE_RULE": "Which single repair makes both neighboring differences equal to the established step?"
        }
        visual = {"kind": "error_analysis_strip", "terms": tuple(shown), "established_step": step}
        fields = ("error_position", "corrected_term", "two_difference_checks")

    elif family == "PLACE_VALUE_CHANGE":
        step = 100
        start = rng.randint(100, 599)
        sequence = tuple(start + 100 * index for index in range(5))
        prompt = f"The pattern is {sequence}. Explain which place changes by one unit each step and which places stay fixed."
        oracle = {
            "sequence": sequence,
            "step": 100,
            "changing_place": "hundreds",
            "fixed_tens": (start // 10) % 10,
            "fixed_ones": start % 10,
        }
        misconceptions = {"CHANGE_ONES": "ones"}
        repairs = {
            "CHANGE_ONES": "Compare the digits in aligned place-value columns. Which column increases?"
        }
        visual = {"kind": "stacked_place_value_chart", "terms": sequence}
        fields = ("changing_place", "fixed_places", "step_equation")

    else:
        step = rng.choice((5, 10))
        start = rng.randrange(0, 61, 5)
        times = tuple(start + step * index for index in range(6))
        prompt = (
            f"A shuttle arrives every {step} minutes beginning at minute {start}. List the first six arrivals, "
            "then determine the arrival immediately before the last one."
        )
        oracle = {
            "arrivals": times,
            "previous_arrival": times[-2],
            "elapsed_first_to_last": times[-1] - times[0],
            "interval_count": 5,
        }
        misconceptions = {"COUNT_TERMS_AS_INTERVALS": 6 * step}
        repairs = {
            "COUNT_TERMS_AS_INTERVALS": "How many gaps lie between six arrival points? Mark each gap once."
        }
        visual = {"kind": "schedule_timeline", "arrivals": times, "interval": step}
        fields = ("arrival_sequence", "previous_arrival", "elapsed_time", "interval_explanation")

    return (
        prompt,
        fields,
        visual,
        _interaction(visual["kind"], "Current pattern model: {state}"),
        oracle,
        misconceptions,
        repairs,
    )


def generate(concept_id: str, seed: int, mode: str) -> Variant:
    """Generate one deterministic, mode-namespaced draft variant."""

    _validate(concept_id, seed, mode)
    family = _family(concept_id, seed, mode)
    rng = Random(f"{REVISION}:{concept_id}:{family}:{mode}:{seed}")
    parts = (
        _place_variant(family, rng)
        if concept_id == PLACE_CONCEPT
        else _pattern_variant(family, rng)
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
