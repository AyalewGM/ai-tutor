"""Draft-only exponent, power and geometry learning package for Issue #337.

This content module is not a runtime family, route or scorer.  It supplements
the accepted exponent generator with original package-level transfer variants
and never writes learner, attempt, diagnostic or mastery evidence.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

PACKAGE_ID = "EXPONENT-POWER-GEOMETRY-LEARNING-PACKAGE-R1"
NAMESPACE = "exponent-power-geometry-learning-package-r1"
STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
CANONICAL_FAMILY = "MATH.NS.EXPONENTS"
MODES = frozenset({"guided", "independent"})
PHASES = (
    "OBSERVE",
    "PREDICT",
    "MANIPULATE",
    "EXPLAIN",
    "PRACTICE",
    "DIAGNOSE",
    "TRANSFER",
    "VERIFY",
)
KINDS = (
    "POWER_OF_PRODUCT",
    "POWER_OF_QUOTIENT",
    "REWRITE_TO_REQUESTED_BASE",
    "COMPARE_EQUIVALENT_POWERS",
    "CUBE_SURFACE_AREA_AND_VOLUME",
    "PYTHAGOREAN_SQUARE_AREAS",
    "SIMPLIFY_THEN_SUBSTITUTE",
)

SOCRATIC_PATHS = {
    "EXP.POWER_OF_POWER_ADDS": (
        "How many copies of the inner power does the outer exponent create?",
        "How many base factors are in each copy?",
        "Which operation combines equal groups of repeated factors?",
    ),
    "EXP.POWER_OF_PRODUCT_BASE_ONLY": (
        "Which factors are inside the parentheses?",
        "How many times is the entire product repeated?",
        "What exponent must each factor receive when the repetitions are regrouped?",
    ),
    "EXP.POWER_OF_QUOTIENT_DENOMINATOR_UNPOWERED": (
        "Which numerator and denominator factors belong to the quotient?",
        "How many copies of the whole quotient are multiplied?",
        "Why must the outer power apply to both parts?",
    ),
    "EXP.REWRITE_BASE_EXPONENT_UNCHANGED": (
        "How many requested-base factors make one copy of the displayed base?",
        "How many copies of the displayed base does its exponent request?",
        "What product counts all requested-base factors without evaluating them?",
    ),
    "EXP.EQUIVALENCE_BY_VALUE_ONLY": (
        "What single exponent represents each expression?",
        "Can the exponent structures be compared before calculating a large value?",
        "Which equality or inequality between exponents decides the comparison?",
    ),
    "EXP.ZERO_WRITTEN_AS_ZERO": (
        "What quotient is formed by equal nonzero powers?",
        "What exponent remains after equal exponents are subtracted?",
        "Which multiplicative identity must that quotient equal?",
    ),
    "EXP.NEGATIVE_IS_NEGATIVE_VALUE": (
        "What factor would make this power product equal the zero-exponent identity?",
        "Where must the positive power move to become a reciprocal?",
        "Does your exact substituted value have the expected sign and magnitude?",
    ),
    "EXP.GEOMETRY.POWER_NOT_DISTRIBUTED": (
        "How many equal side-length factors define this measure?",
        "Which coefficient and base-power factors repeat each time?",
        "What exponent counts every repeated base factor?",
    ),
    "EXP.GEOMETRY.SURFACE_VOLUME_CONFUSED": (
        "Does surface area use square faces or three-dimensional filling?",
        "How many square faces does a cube have?",
        "Which dimensional power and unit belong to surface area and which to volume?",
    ),
    "EXP.PYTHAGOREAN.AREAS_NOT_ADDED": (
        "Which square is built on each side of the right triangle?",
        "What are the two leg-square areas in the same symbolic form?",
        "Does their sum reconstruct the square on the hypotenuse?",
    ),
    "EXP.SUBSTITUTION_BEFORE_SIMPLIFY": (
        "Which exponent laws can reduce the expression before any number is substituted?",
        "What single exponent remains after multiplication and division?",
        "How does the simplified exact value verify against the original expression?",
    ),
}

EVIDENCE_TO_MISCONCEPTION = {
    "power_of_power_exponents_added": "EXP.POWER_OF_POWER_ADDS",
    "power_applied_to_only_one_product_factor": "EXP.POWER_OF_PRODUCT_BASE_ONLY",
    "denominator_left_unpowered": "EXP.POWER_OF_QUOTIENT_DENOMINATOR_UNPOWERED",
    "rewritten_base_exponent_unchanged": "EXP.REWRITE_BASE_EXPONENT_UNCHANGED",
    "large_values_computed_without_structural_comparison": "EXP.EQUIVALENCE_BY_VALUE_ONLY",
    "zero_exponent_written_as_zero": "EXP.ZERO_WRITTEN_AS_ZERO",
    "negative_exponent_written_as_negative_value": "EXP.NEGATIVE_IS_NEGATIVE_VALUE",
    "geometry_power_not_applied_to_every_factor": "EXP.GEOMETRY.POWER_NOT_DISTRIBUTED",
    "surface_area_and_volume_interchanged": "EXP.GEOMETRY.SURFACE_VOLUME_CONFUSED",
    "leg_square_areas_not_added": "EXP.PYTHAGOREAN.AREAS_NOT_ADDED",
    "substituted_before_symbolic_simplification": "EXP.SUBSTITUTION_BEFORE_SIMPLIFY",
}


def _validate(index: int, mode: str) -> None:
    if isinstance(index, bool) or not isinstance(index, int):
        raise TypeError("index must be a non-boolean integer")
    if index < 0:
        raise ValueError("index must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")


def _pow_fraction(base: int, exponent: int) -> Fraction:
    if exponent >= 0:
        return Fraction(base**exponent)
    return Fraction(1, base ** (-exponent))


@dataclass(frozen=True)
class PackageVariant:
    variant_id: str
    mode: str
    kind: str
    prompt: str
    response_fields: tuple[str, ...]
    parameters: dict[str, Any]
    teacher_oracle: dict[str, Any]

    def public_payload(self) -> dict[str, Any]:
        """Return a no-answer learner payload."""

        return {
            "task_id": hashlib.sha256(self.variant_id.encode()).hexdigest()[:24],
            "mode": self.mode,
            "kind": self.kind,
            "canonical_family": CANONICAL_FAMILY,
            "prompt": self.prompt,
            "response_fields": list(self.response_fields),
            "hints": [],
            "worked_steps": [],
            "guided_feedback_available": self.mode == "guided",
            "mastery_credit": False,
        }


def generate_package_variant(index: int, mode: str) -> PackageVariant:
    """Generate one original, deterministic package-level practice or transfer item."""

    _validate(index, mode)
    rng = random.Random(f"{NAMESPACE}:{mode}:{index}")
    kind = KINDS[index % len(KINDS)]
    variant_id = f"{NAMESPACE}:{mode}:{index}"
    prefix = "Guided practice" if mode == "guided" else "Independent transfer"

    if kind == "POWER_OF_PRODUCT":
        coefficient = rng.randint(2, 5)
        base_exponent = rng.randint(1, 5)
        outer_power = rng.randint(2, 4)
        parameters = {
            "coefficient": coefficient,
            "base_exponent": base_exponent,
            "outer_power": outer_power,
        }
        oracle = {
            "coefficient": coefficient**outer_power,
            "x_exponent": base_exponent * outer_power,
            "law_code": "POWER_DISTRIBUTES_OVER_EVERY_PRODUCT_FACTOR",
        }
        prompt = (
            f"{prefix}: Rewrite ({coefficient}x^{base_exponent})^{outer_power} "
            "as one coefficient times one power of x. Explain using repeated factors."
        )
    elif kind == "POWER_OF_QUOTIENT":
        numerator = rng.randint(2, 5)
        denominator = rng.randint(2, 6)
        x_exponent = rng.randint(1, 4)
        y_exponent = rng.randint(1, 4)
        outer_power = rng.randint(2, 3)
        parameters = {
            "numerator": numerator,
            "denominator": denominator,
            "x_exponent": x_exponent,
            "y_exponent": y_exponent,
            "outer_power": outer_power,
        }
        oracle = {
            "coefficient": Fraction(numerator**outer_power, denominator**outer_power),
            "x_exponent": x_exponent * outer_power,
            "y_exponent": -(y_exponent * outer_power),
            "domain_restrictions": ("y != 0",),
            "law_code": "POWER_DISTRIBUTES_TO_NUMERATOR_AND_DENOMINATOR",
        }
        prompt = (
            f"{prefix}: Simplify (({numerator}x^{x_exponent})/"
            f"({denominator}y^{y_exponent}))^{outer_power} exactly and preserve "
            "the original denominator restriction."
        )
    elif kind == "REWRITE_TO_REQUESTED_BASE":
        requested_base = rng.randint(2, 5)
        base_power = rng.randint(2, 4)
        displayed_exponent = rng.randint(2, 6)
        displayed_base = requested_base**base_power
        parameters = {
            "requested_base": requested_base,
            "base_power": base_power,
            "displayed_base": displayed_base,
            "displayed_exponent": displayed_exponent,
        }
        oracle = {
            "requested_base": requested_base,
            "result_exponent": base_power * displayed_exponent,
            "law_code": "REWRITE_BASE_THEN_MULTIPLY_EXPONENTS",
        }
        prompt = (
            f"{prefix}: Rewrite {displayed_base}^{displayed_exponent} as one power "
            f"of {requested_base} without evaluating the large value."
        )
    elif kind == "COMPARE_EQUIVALENT_POWERS":
        base = rng.randint(2, 7)
        inner = rng.randint(2, 5)
        outer = rng.randint(2, 4)
        left_exponent = inner * outer
        delta = (-1, 0, 1)[(index // len(KINDS)) % 3]
        first = rng.randint(1, max(1, left_exponent - 1))
        second = left_exponent - first + delta
        right_exponent = first + second
        relation = "EQUAL" if delta == 0 else ("LEFT_GREATER" if delta < 0 else "RIGHT_GREATER")
        parameters = {
            "base": base,
            "inner": inner,
            "outer": outer,
            "first": first,
            "second": second,
        }
        oracle = {
            "left_exponent": left_exponent,
            "right_exponent": right_exponent,
            "relation": relation,
            "law_code": "COMPARE_COMMON_BASE_EXPONENTS",
        }
        prompt = (
            f"{prefix}: Compare ({base}^{inner})^{outer} and "
            f"{base}^{first} x {base}^{second} without evaluating either large value."
        )
    elif kind == "CUBE_SURFACE_AREA_AND_VOLUME":
        coefficient = rng.randint(2, 5)
        base = rng.randint(2, 5)
        exponent = rng.randint(1, 4)
        parameters = {"coefficient": coefficient, "base": base, "exponent": exponent}
        oracle = {
            "surface_coefficient": 6 * coefficient**2,
            "surface_exponent": 2 * exponent,
            "surface_units": "square units",
            "volume_coefficient": coefficient**3,
            "volume_exponent": 3 * exponent,
            "volume_units": "cubic units",
            "law_code": "DIMENSIONAL_POWER_APPLIES_TO_EVERY_SIDE_FACTOR",
        }
        prompt = (
            f"{prefix}: A cube has side length {coefficient}({base}^{exponent}) units. "
            "Express both total surface area and volume as a coefficient times one power "
            "of the same base, with correct dimensional units."
        )
    elif kind == "PYTHAGOREAN_SQUARE_AREAS":
        scale = rng.randint(1, 4)
        base = rng.randint(2, 5)
        exponent = rng.randint(1, 3)
        a, b, c = 3 * scale, 4 * scale, 5 * scale
        parameters = {"a": a, "b": b, "c": c, "base": base, "exponent": exponent}
        oracle = {
            "leg_a_area_coefficient": a**2,
            "leg_b_area_coefficient": b**2,
            "hypotenuse_area_coefficient": c**2,
            "area_exponent": 2 * exponent,
            "area_identity_verified": a**2 + b**2 == c**2,
            "units": "square units",
            "law_code": "LEG_SQUARE_AREAS_SUM_TO_HYPOTENUSE_SQUARE_AREA",
        }
        prompt = (
            f"{prefix}: A right triangle has side lengths {a}({base}^{exponent}), "
            f"{b}({base}^{exponent}) and {c}({base}^{exponent}) units. Express the "
            "area of the square on each side symbolically and verify the area relation."
        )
    else:
        base = rng.randint(2, 6)
        inner = rng.randint(2, 5)
        outer = rng.randint(2, 4)
        product_exponent = rng.randint(1, 5)
        target_exponent = (-2, 0, 3)[(index // len(KINDS)) % 3]
        divisor_exponent = inner * outer + product_exponent - target_exponent
        parameters = {
            "base": base,
            "inner": inner,
            "outer": outer,
            "product_exponent": product_exponent,
            "divisor_exponent": divisor_exponent,
            "substitution": base,
        }
        oracle = {
            "result_exponent": target_exponent,
            "exact_value": _pow_fraction(base, target_exponent),
            "base_nonzero_required": True,
            "law_code": "SIMPLIFY_SYMBOLICALLY_THEN_SUBSTITUTE",
        }
        prompt = (
            f"{prefix}: Simplify ((x^{inner})^{outer} x x^{product_exponent}) / "
            f"x^{divisor_exponent} as one power, then evaluate exactly at x={base}. "
            "State the original nonzero restriction."
        )

    return PackageVariant(
        variant_id=variant_id,
        mode=mode,
        kind=kind,
        prompt=prompt,
        response_fields=("canonical_result", "exact_value", "domain_and_units", "law_explanation"),
        parameters=parameters,
        teacher_oracle=oracle,
    )


def verify_oracle(item: PackageVariant) -> bool:
    """Independently recompute every package-level oracle from typed parameters."""

    p = item.parameters
    o = item.teacher_oracle
    if item.kind == "POWER_OF_PRODUCT":
        return o["coefficient"] == p["coefficient"] ** p["outer_power"] and o[
            "x_exponent"
        ] == p["base_exponent"] * p["outer_power"]
    if item.kind == "POWER_OF_QUOTIENT":
        return (
            o["coefficient"]
            == Fraction(p["numerator"] ** p["outer_power"], p["denominator"] ** p["outer_power"])
            and o["x_exponent"] == p["x_exponent"] * p["outer_power"]
            and o["y_exponent"] == -(p["y_exponent"] * p["outer_power"])
            and o["domain_restrictions"] == ("y != 0",)
        )
    if item.kind == "REWRITE_TO_REQUESTED_BASE":
        return (
            p["displayed_base"] == p["requested_base"] ** p["base_power"]
            and o["result_exponent"] == p["base_power"] * p["displayed_exponent"]
        )
    if item.kind == "COMPARE_EQUIVALENT_POWERS":
        left = p["inner"] * p["outer"]
        right = p["first"] + p["second"]
        relation = "EQUAL" if left == right else ("LEFT_GREATER" if left > right else "RIGHT_GREATER")
        return o["left_exponent"] == left and o["right_exponent"] == right and o["relation"] == relation
    if item.kind == "CUBE_SURFACE_AREA_AND_VOLUME":
        return (
            o["surface_coefficient"] == 6 * p["coefficient"] ** 2
            and o["surface_exponent"] == 2 * p["exponent"]
            and o["volume_coefficient"] == p["coefficient"] ** 3
            and o["volume_exponent"] == 3 * p["exponent"]
            and o["surface_units"] == "square units"
            and o["volume_units"] == "cubic units"
        )
    if item.kind == "PYTHAGOREAN_SQUARE_AREAS":
        return (
            o["leg_a_area_coefficient"] == p["a"] ** 2
            and o["leg_b_area_coefficient"] == p["b"] ** 2
            and o["hypotenuse_area_coefficient"] == p["c"] ** 2
            and o["leg_a_area_coefficient"] + o["leg_b_area_coefficient"]
            == o["hypotenuse_area_coefficient"]
            and o["area_exponent"] == 2 * p["exponent"]
        )
    exponent = p["inner"] * p["outer"] + p["product_exponent"] - p["divisor_exponent"]
    return (
        o["result_exponent"] == exponent
        and o["exact_value"] == _pow_fraction(p["substitution"], exponent)
        and o["base_nonzero_required"] is True
    )


def guided_lesson(item: PackageVariant) -> dict[str, Any]:
    """Return the complete guided phase contract without its answer oracle."""

    if item.mode != "guided":
        raise ValueError("guided lesson requires a guided variant")
    return {
        "variant_id": item.variant_id,
        "kind": item.kind,
        "prompt": item.prompt,
        "phases": list(PHASES),
        "representations": ["CONCRETE_FACTOR_CARDS", "VISUAL_FACTOR_GROUPS", "SYMBOLIC"],
        "prediction_prompt": "Predict which factors repeat and whether the resulting exponent is positive, zero or negative before simplifying.",
        "manipulation_prompt": "Expand one bounded factor group, regroup equal bases, and keep domain restrictions and dimensional units visible.",
        "explanation_requirement": "Name each exponent law and connect it to the repeated-factor or geometric model.",
        "mastery_credit": False,
    }


def evaluate_guided_evidence(item: PackageVariant, evidence: Mapping[str, object]) -> dict[str, Any]:
    """Route only concrete guided evidence; independent variants fail closed."""

    if item.mode != "guided":
        raise PermissionError("guided feedback is unavailable in independent assessment")
    if not isinstance(evidence, Mapping):
        raise TypeError("evidence must be a mapping")
    allowed = {"response_correct", *EVIDENCE_TO_MISCONCEPTION}
    unknown = set(evidence) - allowed
    if unknown:
        raise ValueError(f"Unsupported evidence fields: {sorted(unknown)!r}")
    if any(type(value) is not bool for value in evidence.values()):
        raise TypeError("all evidence values must be booleans")
    if evidence.get("response_correct") is True:
        return {"correct": True, "misconception_id": None, "socratic_questions": []}
    selected = [
        misconception
        for field, misconception in EVIDENCE_TO_MISCONCEPTION.items()
        if evidence.get(field) is True
    ]
    if len(selected) != 1:
        raise ValueError("exactly one misconception-specific evidence field is required")
    misconception = selected[0]
    return {
        "correct": False,
        "misconception_id": misconception,
        "socratic_questions": list(SOCRATIC_PATHS[misconception]),
        "fresh_exit": fresh_exit(misconception, int(item.variant_id.rsplit(":", 1)[1])),
        "mastery_credit": False,
    }


_REPAIR_KINDS = {
    "EXP.POWER_OF_POWER_ADDS": "POWER_OF_PRODUCT",
    "EXP.POWER_OF_PRODUCT_BASE_ONLY": "POWER_OF_PRODUCT",
    "EXP.POWER_OF_QUOTIENT_DENOMINATOR_UNPOWERED": "POWER_OF_QUOTIENT",
    "EXP.REWRITE_BASE_EXPONENT_UNCHANGED": "REWRITE_TO_REQUESTED_BASE",
    "EXP.EQUIVALENCE_BY_VALUE_ONLY": "COMPARE_EQUIVALENT_POWERS",
    "EXP.ZERO_WRITTEN_AS_ZERO": "SIMPLIFY_THEN_SUBSTITUTE",
    "EXP.NEGATIVE_IS_NEGATIVE_VALUE": "SIMPLIFY_THEN_SUBSTITUTE",
    "EXP.GEOMETRY.POWER_NOT_DISTRIBUTED": "CUBE_SURFACE_AREA_AND_VOLUME",
    "EXP.GEOMETRY.SURFACE_VOLUME_CONFUSED": "CUBE_SURFACE_AREA_AND_VOLUME",
    "EXP.PYTHAGOREAN.AREAS_NOT_ADDED": "PYTHAGOREAN_SQUARE_AREAS",
    "EXP.SUBSTITUTION_BEFORE_SIMPLIFY": "SIMPLIFY_THEN_SUBSTITUTE",
}


def fresh_exit(misconception: str, index: int) -> dict[str, Any]:
    """Return a deterministic, structurally targeted, answer-hidden repair exit."""

    _validate(index, "guided")
    if misconception not in SOCRATIC_PATHS:
        raise ValueError(f"Unsupported misconception: {misconception!r}")
    original = generate_package_variant(index, "guided")
    target_kind = _REPAIR_KINDS[misconception]
    offset = sum(ord(character) for character in misconception) % 211 + 1
    for attempt in range(4096):
        candidate = generate_package_variant(index + offset + attempt, "guided")
        if candidate.kind != target_kind or candidate.prompt == original.prompt:
            continue
        if misconception == "EXP.ZERO_WRITTEN_AS_ZERO" and candidate.teacher_oracle.get(
            "result_exponent"
        ) != 0:
            continue
        if misconception == "EXP.NEGATIVE_IS_NEGATIVE_VALUE" and candidate.teacher_oracle.get(
            "result_exponent", 0
        ) >= 0:
            continue
        public = candidate.public_payload()
        public["guided_feedback_available"] = True
        return public
    raise RuntimeError("deterministic repair search exhausted")


def adapt_accepted_combined(item: Any) -> dict[str, Any]:
    """Adapt an accepted combined-law generator item without changing its math."""

    if getattr(item, "structure", None) != "COMBINED_EXPONENT_LAWS":
        raise ValueError("expected COMBINED_EXPONENT_LAWS")
    if getattr(item, "canonical_family", None) != CANONICAL_FAMILY:
        raise ValueError("unexpected canonical family")
    return {
        "variant_id": item.variant_id,
        "mode": item.mode,
        "prompt": item.prompt,
        "phases": list(PHASES),
        "response_fields": list(item.response_schema),
        "teacher_oracle_hidden": True,
        "mastery_credit": False,
    }


def adapt_accepted_geometry(item: Any) -> dict[str, Any]:
    """Adapt an accepted square/cube transfer without changing its math."""

    if getattr(item, "structure", None) != "EXPONENT_GEOMETRY_TRANSFER":
        raise ValueError("expected EXPONENT_GEOMETRY_TRANSFER")
    if getattr(item, "canonical_family", None) != CANONICAL_FAMILY:
        raise ValueError("unexpected canonical family")
    return {
        "variant_id": item.variant_id,
        "mode": item.mode,
        "prompt": item.prompt,
        "phases": list(PHASES),
        "response_fields": list(item.response_schema),
        "teacher_oracle_hidden": True,
        "mastery_credit": False,
    }


def generate_first_error_localization(index: int, mode: str) -> PackageVariant:
    """Generate a fresh exponent derivation with one earliest incorrect law application.

    This additive teacher-depth extension deliberately does not enter KINDS so
    previously reviewed package-seed behavior remains stable.
    """

    _validate(index, mode)
    rng = random.Random(f"{NAMESPACE}:first-error:{mode}:{index}")
    base = rng.randint(2, 7)
    inner = rng.randint(2, 5)
    outer = rng.randint(3, 5)
    product_exponent = rng.randint(2, 6)
    divisor_exponent = rng.randint(1, 5)

    correct_step_1 = inner * outer
    correct_step_2 = correct_step_1 + product_exponent
    correct_step_3 = correct_step_2 - divisor_exponent
    case = index % 3

    if case == 0:
        shown_step_1 = inner + outer
        shown_step_2 = shown_step_1 + product_exponent
        shown_step_3 = shown_step_2 - divisor_exponent
        first_error_step = 1
        violated_law = "POWER_OF_POWER_MULTIPLIES_EXPONENTS"
        corrected_step_exponent = correct_step_1
    elif case == 1:
        shown_step_1 = correct_step_1
        shown_step_2 = shown_step_1 * product_exponent
        shown_step_3 = shown_step_2 - divisor_exponent
        first_error_step = 2
        violated_law = "PRODUCT_OF_POWERS_ADDS_EXPONENTS"
        corrected_step_exponent = correct_step_2
    else:
        shown_step_1 = correct_step_1
        shown_step_2 = correct_step_2
        shown_step_3 = shown_step_2 + divisor_exponent
        first_error_step = 3
        violated_law = "QUOTIENT_OF_POWERS_SUBTRACTS_EXPONENTS"
        corrected_step_exponent = correct_step_3

    prefix = "Guided error analysis" if mode == "guided" else "Independent error analysis"
    prompt = (
        f"{prefix}: A derivation starts with (({base}^{inner})^{outer} x "
        f"{base}^{product_exponent}) / {base}^{divisor_exponent}. "
        f"Step 1: (({base}^{inner})^{outer} x {base}^{product_exponent}) / "
        f"{base}^{divisor_exponent} = ({base}^{shown_step_1} x "
        f"{base}^{product_exponent}) / {base}^{divisor_exponent}. "
        f"Step 2: ({base}^{shown_step_1} x {base}^{product_exponent}) / "
        f"{base}^{divisor_exponent} = {base}^{shown_step_2} / "
        f"{base}^{divisor_exponent}. "
        f"Step 3: {base}^{shown_step_2} / {base}^{divisor_exponent} = "
        f"{base}^{shown_step_3}. "
        "Identify the first incorrect step, name the exponent law that was violated, "
        "and give the corrected exponent for that step."
    )
    return PackageVariant(
        variant_id=f"{NAMESPACE}:first-error:{mode}:{index}",
        mode=mode,
        kind="FIRST_ERROR_LOCALIZATION",
        prompt=prompt,
        response_fields=(
            "first_error_step",
            "violated_law",
            "corrected_step_exponent",
            "explanation",
        ),
        parameters={
            "base": base,
            "inner": inner,
            "outer": outer,
            "product_exponent": product_exponent,
            "divisor_exponent": divisor_exponent,
            "shown_exponents": (shown_step_1, shown_step_2, shown_step_3),
        },
        teacher_oracle={
            "first_error_step": first_error_step,
            "violated_law": violated_law,
            "corrected_step_exponent": corrected_step_exponent,
            "correct_final_exponent": correct_step_3,
        },
    )


def verify_first_error_localization(item: PackageVariant) -> bool:
    """Recompute the first invalid step independently from the original expression."""

    if item.kind != "FIRST_ERROR_LOCALIZATION":
        raise ValueError("expected FIRST_ERROR_LOCALIZATION")
    p = item.parameters
    shown = tuple(p["shown_exponents"])
    expected = (
        p["inner"] * p["outer"],
        p["inner"] * p["outer"] + p["product_exponent"],
        p["inner"] * p["outer"] + p["product_exponent"] - p["divisor_exponent"],
    )
    first = next(
        (
            i + 1
            for i, (actual, correct) in enumerate(zip(shown, expected, strict=True))
            if actual != correct
        ),
        None,
    )
    if first is None:
        return False
    law_by_step = {
        1: "POWER_OF_POWER_MULTIPLIES_EXPONENTS",
        2: "PRODUCT_OF_POWERS_ADDS_EXPONENTS",
        3: "QUOTIENT_OF_POWERS_SUBTRACTS_EXPONENTS",
    }
    oracle = item.teacher_oracle
    return (
        oracle["first_error_step"] == first
        and oracle["violated_law"] == law_by_step[first]
        and oracle["corrected_step_exponent"] == expected[first - 1]
        and oracle["correct_final_exponent"] == expected[2]
    )
