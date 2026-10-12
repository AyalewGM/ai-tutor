"""Original Grade 7 inequality lesson variants; REVIEW-ONLY, never runtime scoring.

Generated teacher oracles are deliberately separate from learner projections.
No database, router, canonical registration or mastery-event integration.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from random import Random

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
NAMESPACE = "grade7-inequality-reasoning-v1"
MODES = frozenset({"guided", "independent"})
RELATIONS = ("<", "<=", ">", ">=")
RESPONSE_FIELDS = (
    "boundary",
    "solution_relation",
    "endpoint",
    "graph_direction",
    "satisfying_test",
    "rejected_test",
    "context_domain",
    "equality_preservation",
    "written_justification",
)


def _flip(relation: str) -> str:
    return {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[relation]


def _holds(left: int, relation: str, right: int) -> bool:
    return {
        "<": left < right,
        "<=": left <= right,
        ">": left > right,
        ">=": left >= right,
    }[relation]


@dataclass(frozen=True)
class Variant:
    item_id: str
    mode: str
    structure: str
    prompt: str
    a: int
    b: int
    c: int
    d: int
    relation: str
    boundary: int

    @property
    def solution_relation(self) -> str:
        return self.relation if self.a > self.c else _flip(self.relation)

    def satisfies(self, x: int) -> bool:
        """Independently evaluate the original two-sided inequality."""
        return _holds(self.a * x + self.b, self.relation, self.c * x + self.d)

    def public_payload(self) -> dict[str, object]:
        """Projection only; never includes the teacher's answer or scaffolds."""
        return {
            "item_id": self.item_id,
            "mode": self.mode,
            "prompt": self.prompt,
            "response_fields": list(RESPONSE_FIELDS),
        }

    def teacher_oracle(self) -> dict[str, object]:
        """Private draft verification contract, NOT a student API or mastery scorer."""
        direction = "RIGHT" if self.solution_relation in (">", ">=") else "LEFT"
        satisfying = self.boundary + (1 if direction == "RIGHT" else -1)
        rejected = self.boundary - (1 if direction == "RIGHT" else -1)
        assert satisfying >= 0 and rejected >= 0
        assert self.satisfies(satisfying) and not self.satisfies(rejected)
        assert self.a * self.boundary + self.b == self.c * self.boundary + self.d
        return {
            "boundary": self.boundary,
            "solution_relation": self.solution_relation,
            "endpoint": ("CLOSED" if "=" in self.relation else "OPEN"),
            "graph_direction": direction,
            "satisfying_test": satisfying,
            "rejected_test": rejected,
            "context_domain": "NONNEGATIVE_WHOLE_NUMBERS",
            "equality_preservation": "SAME_CHANGE_BOTH_SIDES",
            "difference_coefficient": self.a - self.c,
            "difference_constant": self.d - self.b,
            "proof_left_at_witness": self.a * satisfying + self.b,
            "proof_right_at_witness": self.c * satisfying + self.d,
        }


def generate(seed: int, mode: str) -> Variant:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer, not bool")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if mode not in MODES:
        raise ValueError("mode must be guided or independent")

    rng = Random(f"{NAMESPACE}:{mode}:{seed}")
    # Four distinct structures: positive/negative coefficient difference,
    # symbolic/context translation. Independent thresholds cannot repeat guided.
    structure_number = seed % 4
    boundary = rng.randint(4, 12) if mode == "guided" else rng.randint(16, 26)
    delta = rng.randint(1, 4)
    if structure_number in (0, 2):
        c = rng.randint(1, 4)
        a = c + delta
        b = rng.randint(2, 12)
        d = b + delta * boundary
    else:
        a = rng.randint(1, 4)
        c = a + delta
        d = rng.randint(2, 12)
        b = d + delta * boundary
    relation = RELATIONS[rng.randrange(len(RELATIONS))]
    expression = f"{a}x + {b} {relation} {c}x + {d}"
    if structure_number in (2, 3):
        words = {
            "<": "costs less than",
            "<=": "costs no more than",
            ">": "costs more than",
            ">=": "costs at least as much as",
        }[relation]
        prompt = (
            f"Two activity-pass plans charge in dollars: Plan A costs {b} plus "
            f"{a} per visit; Plan B costs {d} plus {c} per visit. "
            f"For which nonnegative whole-number visit counts x does A {words} B? "
            "Write the inequality yourself, solve using justified changes to both "
            "sides, graph the solution set, and test one count in and one count out."
        )
    else:
        prompt = (
            f"For nonnegative whole numbers x, solve {expression}. "
            "Show an operation applied equally to both sides, describe the "
            "number-line endpoint and direction, and verify one satisfying "
            "and one non-satisfying value by substitution into the original."
        )
    return Variant(
        item_id=f"{NAMESPACE}:{mode}:{seed}:s{structure_number}",
        mode=mode,
        structure=("symbolic" if structure_number < 2 else "context"),
        prompt=prompt,
        a=a,
        b=b,
        c=c,
        d=d,
        relation=relation,
        boundary=boundary,
    )


def diagnose_guided(variant: Variant, response: Mapping[str, object]) -> str:
    """Evidence-specific *guided* prompts only; never a mastery decision."""
    if variant.mode != "guided":
        raise ValueError("No learner diagnosis on independent variants")
    if not all(key in response for key in RESPONSE_FIELDS):
        return "INCOMPLETE_GUIDED_EVIDENCE"
    oracle = variant.teacher_oracle()
    boundary = response["boundary"]
    if type(boundary) is not int or boundary != oracle["boundary"]:
        if type(boundary) is int and variant.a != 0:
            # Distinct signature: omitted the x term on the right, then
            # divided the constant difference by the left coefficient.
            wrong_numerator = variant.d - variant.b
            if wrong_numerator % variant.a == 0 and boundary == wrong_numerator // variant.a:
                return "G7.VARIABLE_ON_RIGHT_IGNORED"
        return "G7.BOUNDARY_ARITHMETIC_RECHECK"
    if response["equality_preservation"] != oracle["equality_preservation"]:
        return "G7.UNEQUAL_SIDE_CHANGE"
    if response["solution_relation"] != oracle["solution_relation"]:
        return (
            "G7.NEGATIVE_DIVISION_NO_REVERSAL"
            if variant.a < variant.c
            else "G7.GRAPH_DIRECTION_CONFUSION"
        )
    if response["endpoint"] != oracle["endpoint"]:
        return "G7.STRICTNESS_ENDPOINT_CONFUSION"
    if response["graph_direction"] != oracle["graph_direction"]:
        return "G7.GRAPH_DIRECTION_CONFUSION"
    if response["context_domain"] != oracle["context_domain"]:
        return "G7.COUNT_DOMAIN_CONFUSION"
    yes = response["satisfying_test"]
    no = response["rejected_test"]
    if (
        type(yes) is not int
        or type(no) is not int
        or yes < 0
        or no < 0
        or not variant.satisfies(yes)
        or variant.satisfies(no)
    ):
        return "G7.SUBSTITUTION_NOT_A_PROOF"
    if not isinstance(response["written_justification"], str) or not response[
        "written_justification"
    ].strip():
        return "G7.EXPLANATION_REQUIRES_EVIDENCE"
    # Text is NOT machine-graded here; written reasoning still needs review.
    return "GUIDED_STRUCTURED_FIELDS_MATCH_REASONING_UNREVIEWED"
