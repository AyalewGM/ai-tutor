"""Draft-only shared Grade 8 inverse-operation question depth.

The package reuses the existing ``M8.ALG.INVERSE.ADD`` and
``M8.ALG.INVERSE.MULT`` skill identities.  It is deliberately outside the
application import graph: there is no persistence, selector, scorer, routing,
curriculum-mapping, or mastery authority here.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Final

STATUS: Final = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION: Final = False
NAMESPACE: Final = "canonical-grade8:inverse-operations-depth-r1"
MODES: Final = frozenset({"diagnostic", "guided", "independent", "mastery"})

ADD_SKILL: Final = "M8.ALG.INVERSE.ADD"
MULT_SKILL: Final = "M8.ALG.INVERSE.MULT"

FAMILIES: Final = (
    "MATH.EQ.INVERSE.ADD.BALANCE",
    "MATH.EQ.INVERSE.SUB.MISSING_ADDEND",
    "MATH.EQ.INVERSE.ADD.VARIABLE_RIGHT",
    "MATH.EQ.INVERSE.ADD.RATIONAL",
    "MATH.EQ.INVERSE.ADD.CHANGE_CONTEXT",
    "MATH.EQ.INVERSE.ADD.ERROR_ANALYSIS",
    "MATH.EQ.INVERSE.MULT.BALANCE",
    "MATH.EQ.INVERSE.DIV.QUOTIENT",
    "MATH.EQ.INVERSE.MULT.NEGATIVE",
    "MATH.EQ.INVERSE.MULT.RATIONAL",
    "MATH.EQ.INVERSE.MULT.SCALE_CONTEXT",
    "MATH.EQ.INVERSE.MULT.ERROR_ANALYSIS",
)

CANONICAL_SKILL: Final = MappingProxyType(
    {family: ADD_SKILL for family in FAMILIES[:6]}
    | {family: MULT_SKILL for family in FAMILIES[6:]}
)

TRANSFER_PARTNER: Final = MappingProxyType(
    {
        FAMILIES[0]: FAMILIES[4],
        FAMILIES[1]: FAMILIES[3],
        FAMILIES[2]: FAMILIES[5],
        FAMILIES[3]: FAMILIES[1],
        FAMILIES[4]: FAMILIES[0],
        FAMILIES[5]: FAMILIES[2],
        FAMILIES[6]: FAMILIES[10],
        FAMILIES[7]: FAMILIES[9],
        FAMILIES[8]: FAMILIES[11],
        FAMILIES[9]: FAMILIES[7],
        FAMILIES[10]: FAMILIES[6],
        FAMILIES[11]: FAMILIES[8],
    }
)

ACCESSIBILITY_CONTRACT: Final = MappingProxyType(
    {
        "keyboard": "Every balance control, number-line step, and response field is reachable and operable without dragging.",
        "screen_reader": "Announce the left expression, equality relation, right expression, operation applied to both sides, and resulting equation in order.",
        "visual": "Use labels, shapes, and text in addition to colour; preserve the equals sign as the visual balance anchor.",
        "motion": "A reduced-motion state presents before/after equations simultaneously instead of animating balance pieces.",
        "input": "Accept integers and any equivalent exact fraction; do not require pointer drawing or decimal approximation.",
        "focus": "After a transformation, focus moves to the resulting equation and its concise live-region summary.",
    }
)

FAMILY_CONTRACT: Final = MappingProxyType(
    {
        FAMILIES[0]: ("signed-number addition", "one inverse step with equality preservation", "signed integer"),
        FAMILIES[1]: ("subtraction and missing-addend meaning", "reconcile subtraction with addition", "signed integer"),
        FAMILIES[2]: ("symmetry of equality", "variable expression appears on the right", "signed integer"),
        FAMILIES[3]: ("exact fraction addition", "inverse addition with rational values", "exact rational"),
        FAMILIES[4]: ("signed change in context", "model an unknown start value", "context-valid exact rational"),
        FAMILIES[5]: ("equality-preserving addition", "analyze, refute, and correct a sign error", "signed integer"),
        FAMILIES[6]: ("multiplication facts and equality", "one inverse division step", "signed integer"),
        FAMILIES[7]: ("division as an equation", "undo a quotient with multiplication", "signed integer"),
        FAMILIES[8]: ("signed multiplication", "isolate from a negative coefficient", "signed integer"),
        FAMILIES[9]: ("fraction multiplication", "undo a rational coefficient with its reciprocal", "exact rational"),
        FAMILIES[10]: ("constant scale in context", "model an unknown per-group quantity", "context-valid exact rational"),
        FAMILIES[11]: ("coefficient meaning", "analyze, refute, and correct coefficient-as-addend reasoning", "signed integer"),
    }
)

_REPAIR: Final = MappingProxyType(
    {
        "EQ_001": (
            "What operation is attached to x in the original equation?",
            "Which opposite operation must be applied to both sides to keep equality?",
            "Show the same signed counter change on both balance pans.",
        ),
        "EQ_005": (
            "Which side contains x, and does that change what equality means?",
            "Can you swap the complete left and right expressions before isolating x?",
            "Rotate the whole balance; do not move a term across the equals sign.",
        ),
        "EQ_006": (
            "What is the sign of the offset, including its numerator?",
            "What exact opposite fraction added to both sides makes that offset zero?",
            "Partition both sides into the same denominator before cancelling opposites.",
        ),
        "EQ_007": (
            "Does the stated change describe the start, the change, or the final value?",
            "What equation reconstructs final = start + change?",
            "Place start, signed change, and final on a labelled number line.",
        ),
        "EQ_003": (
            "Is the coefficient multiplying x or being added to x?",
            "Which division applied to both sides makes the coefficient equal to 1?",
            "Partition both balance pans into the same number of equal groups.",
        ),
        "EQ_008": (
            "What operation does the fraction bar apply to x?",
            "What multiplication on both sides undoes division by the divisor?",
            "Regroup each side into equal sets of the divisor before recombining.",
        ),
        "EQ_009": (
            "What is the sign of the coefficient multiplying x?",
            "After division, what sign results from the quotient of the two signed values?",
            "Label the signed coefficient before partitioning both sides equally.",
        ),
        "EQ_010": (
            "Which exact number multiplies x?",
            "What reciprocal makes that coefficient equal to 1, and what must happen on the other side?",
            "Use equal fraction strips to show reciprocal multiplication on both sides.",
        ),
        "EQ_011": (
            "Does the total name one group or all equal groups?",
            "Which quotient recovers the amount in one group?",
            "Partition the total into the stated number of equal, labelled groups.",
        ),
        "EQ_004": (
            "In the term ax, what operation connects a and x?",
            "Would subtracting a undo multiplication by a? Test by substitution.",
            "Replace repeated x-groups with equal boxes before choosing the inverse.",
        ),
    }
)

_PROBE_TOKEN: Final = MappingProxyType(
    {
        "EQ_001": "REPEATED_THE_OFFSET_OPERATION",
        "EQ_005": "MOVED_A_TERM_ACROSS_EQUALS",
        "EQ_006": "IGNORED_FRACTION_SIGN_OR_DENOMINATOR",
        "EQ_007": "CONFUSED_START_CHANGE_FINAL",
        "EQ_003": "MULTIPLIED_BY_COEFFICIENT_AGAIN",
        "EQ_008": "DIVIDED_BY_DIVISOR_AGAIN",
        "EQ_009": "DROPPED_NEGATIVE_COEFFICIENT",
        "EQ_010": "USED_COEFFICIENT_NOT_RECIPROCAL",
        "EQ_011": "USED_TOTAL_AS_ONE_GROUP",
        "EQ_004": "TREATED_COEFFICIENT_AS_ADDEND",
    }
)


def _fmt(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _signed(value: Fraction) -> str:
    return f"+ {_fmt(value)}" if value >= 0 else f"- {_fmt(-value)}"


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
    parameters: tuple[tuple[str, str], ...]
    answer: str
    prerequisite: str
    difficulty_rationale: str
    equivalence_boundary: str
    representation: tuple[str, str, str]
    misconception_answers: tuple[tuple[str, str], ...]

    def public_payload(self) -> dict[str, object]:
        """Return an answer-free learner contract."""

        payload: dict[str, object] = {
            "variant_id": self.variant_id,
            "family": self.family,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
            "response_fields": ["exact_answer", "equality_justification"],
            "representation": list(self.representation),
            "accessibility": dict(ACCESSIBILITY_CONTRACT),
        }
        if self.mode in {"independent", "mastery"}:
            payload["support"] = "NONE_UNHINTED"
        return payload

    def teacher_oracle(self) -> dict[str, object]:
        """Return exact review evidence; this is never learner payload."""

        return {
            "answer": self.answer,
            "parameters": dict(self.parameters),
            "verification": verification_equation(self),
            "answer_equivalence": "Any exact integer or fraction equal to the oracle is valid.",
            "domain_boundary": self.equivalence_boundary,
        }


def _variant(
    *,
    family: str,
    seed: int,
    mode: str,
    structure: str,
    prompt: str,
    coefficient: Fraction,
    offset: Fraction,
    rhs: Fraction,
    solution: Fraction,
    wrong: dict[str, Fraction],
    representation: tuple[str, str, str],
) -> Variant:
    if coefficient == 0:
        raise AssertionError("A one-variable inverse-operation item needs a nonzero coefficient")
    if coefficient * solution + offset != rhs:
        raise AssertionError("Oracle does not satisfy its authored equation")
    answer = _fmt(solution)
    misconceptions = {
        code: _fmt(value) for code, value in wrong.items() if value != solution
    }
    if not misconceptions:
        raise AssertionError("Every variant needs a non-colliding misconception signature")
    prerequisite, rationale, boundary = FAMILY_CONTRACT[family]
    return Variant(
        variant_id=f"{NAMESPACE}:{mode}:{family}:{seed}",
        family=family,
        canonical_skill=CANONICAL_SKILL[family],
        mode=mode,
        structure=structure,
        prompt=prompt,
        parameters=tuple(
            sorted(
                {
                    "coefficient": _fmt(coefficient),
                    "offset": _fmt(offset),
                    "rhs": _fmt(rhs),
                }.items()
            )
        ),
        answer=answer,
        prerequisite=prerequisite,
        difficulty_rationale=rationale,
        equivalence_boundary=boundary,
        representation=representation,
        misconception_answers=tuple(sorted(misconceptions.items())),
    )


def generate(family: str, seed: int, mode: str) -> Variant:
    """Generate one deterministic original task for a declared structure."""

    _validate(family, seed, mode)
    rng = random.Random(f"{NAMESPACE}:{family}:{mode}:{seed}")
    x = Fraction(rng.choice([n for n in range(-12, 13) if n not in (0,)]))

    if family == FAMILIES[0]:
        offset = Fraction(rng.choice([n for n in range(-11, 12) if n not in (0,)]))
        rhs = x + offset
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="SIGNED_ADDITIVE_BALANCE",
            prompt=f"Solve x {_signed(offset)} = {_fmt(rhs)}. Show the same inverse operation on both sides and verify by substitution.",
            coefficient=Fraction(1), offset=offset, rhs=rhs, solution=x,
            wrong={"EQ_001": rhs + offset},
            representation=(
                "Concrete: place x and signed counters on one balance pan and the total on the other.",
                "Visual: cross out opposite counter pairs after changing both pans equally.",
                f"Symbolic: add {_fmt(-offset)} to both sides, then substitute the result.",
            ),
        )

    if family == FAMILIES[1]:
        amount = Fraction(rng.randint(2, 12))
        rhs = x - amount
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="SUBTRACTION_AS_MISSING_ADDEND",
            prompt=f"A number minus {_fmt(amount)} equals {_fmt(rhs)}. Find the number, rewrite the statement as a missing-addend equation, and verify it.",
            coefficient=Fraction(1), offset=-amount, rhs=rhs, solution=x,
            wrong={"EQ_001": rhs - amount},
            representation=(
                "Concrete: remove the stated number of signed counters from an unknown collection.",
                "Visual: reverse the leftward number-line displacement to recover the start.",
                f"Symbolic: x - {_fmt(amount)} = {_fmt(rhs)} is equivalent to {_fmt(rhs)} + {_fmt(amount)} = x.",
            ),
        )

    if family == FAMILIES[2]:
        offset = Fraction(rng.choice([n for n in range(-10, 11) if n not in (0,)]))
        rhs = x + offset
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="VARIABLE_EXPRESSION_ON_RIGHT_OF_EQUALITY",
            prompt=f"Solve {_fmt(rhs)} = x {_signed(offset)}. Explain why swapping the two complete sides preserves equality before isolating x.",
            coefficient=Fraction(1), offset=offset, rhs=rhs, solution=x,
            wrong={"EQ_005": rhs + offset, "EQ_001": -rhs - offset},
            representation=(
                "Concrete: rotate a balanced scale so the unknown pan appears first.",
                "Visual: bracket each complete side before exchanging their positions.",
                f"Symbolic: use equality symmetry, then add {_fmt(-offset)} to both sides.",
            ),
        )

    if family == FAMILIES[3]:
        denominator = rng.choice((2, 3, 4, 5, 6))
        offset = Fraction(rng.choice([n for n in range(-9, 10) if n]), denominator)
        solution = Fraction(rng.choice([n for n in range(-15, 16) if n]), rng.choice((2, 3, 4)))
        rhs = solution + offset
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="RATIONAL_OFFSET_EXACT_BALANCE",
            prompt=f"Solve x {_signed(offset)} = {_fmt(rhs)} exactly. Use fraction strips or a common denominator, and verify without a decimal approximation.",
            coefficient=Fraction(1), offset=offset, rhs=rhs, solution=solution,
            wrong={"EQ_006": rhs + offset, "EQ_001": rhs - abs(offset)},
            representation=(
                "Concrete: model both rational values with same-denominator fraction strips.",
                "Visual: remove or add the same signed fraction strip on both balance pans.",
                f"Symbolic: x = {_fmt(rhs)} - ({_fmt(offset)}), kept as an exact fraction.",
            ),
        )

    if family == FAMILIES[4]:
        change = Fraction(rng.choice([n for n in range(-9, 10) if n]))
        final = x + change
        direction = "rose" if change > 0 else "fell"
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="UNKNOWN_START_SIGNED_CHANGE_CONTEXT",
            prompt=f"A sensor reading {direction} by {_fmt(abs(change))} units and ended at {_fmt(final)}. Find the starting reading, write final = start + signed change, and check the context.",
            coefficient=Fraction(1), offset=change, rhs=final, solution=x,
            wrong={"EQ_007": final + change, "EQ_001": final - abs(change)},
            representation=(
                "Concrete: label cards for start, signed change, and final instead of relying on keywords.",
                "Visual: draw the signed displacement from the unknown start to the known final.",
                f"Symbolic: start {_signed(change)} = {_fmt(final)}.",
            ),
        )

    if family == FAMILIES[5]:
        offset = Fraction(rng.randint(2, 11))
        rhs = x + offset
        claimed = rhs + offset
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="ADDITIVE_INVERSE_ERROR_ANALYSIS_AND_COUNTEREXAMPLE",
            prompt=f"A learner says x + {_fmt(offset)} = {_fmt(rhs)} gives x = {_fmt(claimed)} because the {_fmt(offset)} 'moves across' and stays positive. Test the claim by substitution, identify the equality error, and solve correctly.",
            coefficient=Fraction(1), offset=offset, rhs=rhs, solution=x,
            wrong={"EQ_001": claimed},
            representation=(
                "Concrete: compare changing one balance pan with changing both pans equally.",
                "Visual: mark the claimed value on a number line and test whether the forward change reaches the target.",
                f"Symbolic: substitute {_fmt(claimed)} for a counterexample, then subtract {_fmt(offset)} from both sides.",
            ),
        )

    if family == FAMILIES[6]:
        coefficient = Fraction(rng.randint(2, 12))
        rhs = coefficient * x
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="INTEGER_COEFFICIENT_EQUAL_GROUP_BALANCE",
            prompt=f"Solve {_fmt(coefficient)}x = {_fmt(rhs)}. Partition both sides into the same number of equal groups and verify by multiplication.",
            coefficient=coefficient, offset=Fraction(0), rhs=rhs, solution=x,
            wrong={"EQ_003": rhs * coefficient, "EQ_004": rhs - coefficient},
            representation=(
                f"Concrete: arrange each balance pan into {_fmt(coefficient)} equal groups.",
                "Visual: pair each x-box with one equal share of the total.",
                f"Symbolic: divide both sides by {_fmt(coefficient)}.",
            ),
        )

    if family == FAMILIES[7]:
        divisor = Fraction(rng.randint(2, 10))
        rhs = x / divisor
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="QUOTIENT_EQUATION_RECOMPOSITION",
            prompt=f"Solve x/{_fmt(divisor)} = {_fmt(rhs)}. Recompose the whole from equal shares, then verify the quotient.",
            coefficient=Fraction(1, divisor), offset=Fraction(0), rhs=rhs, solution=x,
            wrong={"EQ_008": rhs / divisor, "EQ_004": rhs + divisor},
            representation=(
                f"Concrete: combine {_fmt(divisor)} equal groups, each worth {_fmt(rhs)}.",
                "Visual: join equal tape-diagram sections to reconstruct the whole.",
                f"Symbolic: multiply both sides by {_fmt(divisor)}.",
            ),
        )

    if family == FAMILIES[8]:
        coefficient = Fraction(-rng.randint(2, 10))
        rhs = coefficient * x
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="NEGATIVE_COEFFICIENT_SIGNED_QUOTIENT",
            prompt=f"Solve {_fmt(coefficient)}x = {_fmt(rhs)}. Track the coefficient's sign, divide both sides, and verify the signed product.",
            coefficient=coefficient, offset=Fraction(0), rhs=rhs, solution=x,
            wrong={"EQ_009": -x, "EQ_003": rhs * coefficient},
            representation=(
                "Concrete: use signed equal groups, with each group representing the same unknown.",
                "Visual: label both magnitude and sign before making equal partitions.",
                f"Symbolic: x = {_fmt(rhs)} / ({_fmt(coefficient)}).",
            ),
        )

    if family == FAMILIES[9]:
        numerator = rng.randint(2, 8)
        denominator = rng.randint(2, 9)
        while numerator == denominator:
            denominator = rng.randint(2, 9)
        coefficient = Fraction(numerator, denominator)
        solution = Fraction(rng.choice([n for n in range(-12, 13) if n]))
        rhs = coefficient * solution
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="RATIONAL_COEFFICIENT_RECIPROCAL",
            prompt=f"Solve ({_fmt(coefficient)})x = {_fmt(rhs)} exactly. Explain why multiplying both sides by {_fmt(1 / coefficient)} isolates x, then verify.",
            coefficient=coefficient, offset=Fraction(0), rhs=rhs, solution=solution,
            wrong={"EQ_010": rhs * coefficient, "EQ_003": rhs / (1 / coefficient)},
            representation=(
                "Concrete: use fraction strips to show the coefficient as part of one x-strip.",
                "Visual: scale both balance pans by the reciprocal with matched arrows.",
                f"Symbolic: ({_fmt(1 / coefficient)})({_fmt(coefficient)})x = ({_fmt(1 / coefficient)})({_fmt(rhs)}).",
            ),
        )

    if family == FAMILIES[10]:
        groups = Fraction(rng.randint(2, 12))
        per_group = Fraction(rng.choice([n for n in range(1, 13)]), rng.choice((1, 1, 2, 4)))
        total = groups * per_group
        return _variant(
            family=family, seed=seed, mode=mode,
            structure="UNKNOWN_PER_GROUP_SCALE_CONTEXT",
            prompt=f"{_fmt(groups)} identical kits use {_fmt(total)} metres of cord altogether. How many metres are in each kit? Model {_fmt(groups)}x = {_fmt(total)} and check that equal groups reconstruct the total.",
            coefficient=groups, offset=Fraction(0), rhs=total, solution=per_group,
            wrong={"EQ_011": total, "EQ_004": total - groups},
            representation=(
                f"Concrete: share {_fmt(total)} metres equally among {_fmt(groups)} labelled kits.",
                "Visual: partition one total-length tape into equal kit sections.",
                f"Symbolic: x = {_fmt(total)} / {_fmt(groups)}.",
            ),
        )

    coefficient = Fraction(rng.randint(2, 11))
    rhs = coefficient * x
    claimed = rhs - coefficient
    return _variant(
        family=family, seed=seed, mode=mode,
        structure="COEFFICIENT_AS_ADDEND_ERROR_ANALYSIS",
        prompt=f"A learner solves {_fmt(coefficient)}x = {_fmt(rhs)} by subtracting {_fmt(coefficient)} and claims x = {_fmt(claimed)}. Explain what {_fmt(coefficient)}x means, test the claim, and solve with an equality-preserving inverse.",
        coefficient=coefficient, offset=Fraction(0), rhs=rhs, solution=x,
        wrong={"EQ_004": claimed, "EQ_003": rhs * coefficient},
        representation=(
            f"Concrete: build {_fmt(coefficient)} equal x-groups, not x plus {_fmt(coefficient)} counters.",
            "Visual: contrast repeated equal boxes with an additive counter strip.",
            f"Symbolic: divide both sides by {_fmt(coefficient)} and substitute to refute the claim.",
        ),
    )


def verification_equation(variant: Variant) -> str:
    p = dict(variant.parameters)
    return f"({_fmt(Fraction(p['coefficient']) * Fraction(variant.answer) + Fraction(p['offset']))}) = {p['rhs']}"


def guided_probe(variant: Variant, observed_answer: str) -> dict[str, object] | None:
    """Ask a neutral second probe; do not infer a misconception from one answer."""

    if variant.mode != "guided":
        return None
    try:
        observed = _fmt(Fraction(observed_answer))
    except (ValueError, ZeroDivisionError):
        return {
            "classification": "UNPARSEABLE_NEEDS_CLARIFICATION",
            "questions": (
                "What exact integer or fraction does your response represent?",
                "Which operation did you apply to both sides?",
            ),
        }
    if observed == variant.answer:
        return {"classification": "CORRECT_NO_REMEDIATION", "questions": ()}
    candidates = tuple(
        code for code, answer in variant.misconception_answers if answer == observed
    )
    return {
        "classification": "EVIDENCE_INCOMPLETE_NEEDS_STRATEGY_PROBE",
        "questions": (
            "Which operation did you apply to the complete left side and the complete right side?",
            "Substitute your result: what value does each side become?",
        ),
        "candidate_count": len(candidates),
    }


def guided_repair(
    variant: Variant, observed_answer: str, strategy_probe: str
) -> dict[str, object] | None:
    """Return targeted repair only after answer and strategy probes agree."""

    if variant.mode != "guided":
        return None
    try:
        observed = _fmt(Fraction(observed_answer))
    except (ValueError, ZeroDivisionError):
        return {
            "classification": "UNCLASSIFIED_NO_ANSWER_REVEAL",
            "questions": ("Restate your exact value and the operation used on both sides.",),
        }
    if observed == variant.answer:
        return {"classification": "CORRECT_NO_REMEDIATION", "questions": ()}
    candidates = tuple(
        code for code, answer in variant.misconception_answers
        if answer == observed and _PROBE_TOKEN[code] == strategy_probe
    )
    if len(candidates) != 1:
        return {
            "classification": "UNCLASSIFIED_NO_ANSWER_REVEAL",
            "questions": (
                "Show the same operation on both complete sides.",
                "Then substitute your value before deciding what to revise.",
            ),
        }
    code = candidates[0]
    q1, q2, move = _REPAIR[code]
    return {
        "classification": code,
        "questions": (q1, q2),
        "representation_move": move,
        "fresh_exit_family": TRANSFER_PARTNER[variant.family],
    }


def strategy_probe_token(misconception_code: str) -> str:
    """Testing/reviewer hook for the second-probe contract, not learner copy."""

    return _PROBE_TOKEN[misconception_code]


def source_seed(variant: Variant) -> int:
    return int(variant.variant_id.rsplit(":", 1)[-1])


def generate_transfer(source: Variant, *, seed_offset: int = 1_000_003) -> Variant:
    """Generate a different-structure, unhinted independent transfer item."""

    if source.mode not in {"diagnostic", "guided"}:
        raise ValueError("transfer source must be diagnostic or guided")
    return generate(
        TRANSFER_PARTNER[source.family], source_seed(source) + seed_offset, "independent"
    )
