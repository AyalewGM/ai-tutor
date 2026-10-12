"""Draft polynomial-division package layer for owner-approved Issue #337.

This module is deliberately outside runtime code. It reuses PR #344's exact
generator, adds package sequencing and diagnostic behavior, and never writes
learner or mastery data.
"""

from __future__ import annotations

import importlib.util
import random
import re
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

PACKAGE_ID = "ONT-ALG-POLY-DIVISION-R1"
REVISION = "issue-337-polynomial-division-package-r2"
STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
RESPONSE_CONTRACT_REVISION = "poly-division-evidence-v1"
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
SCAFFOLD_STATES = ("MODELED", "COACHED", "INDEPENDENT_READINESS")
MISCONCEPTIONS = frozenset(
    {
        "POLY.DIV.COEFFICIENT_RECIPROCAL",
        "POLY.DIV.ADD_EXPONENTS",
        "POLY.DIV.ONE_TERM_ONLY",
        "POLY.DIV.DOMAIN_OMITTED",
    }
)
COEFFICIENT_REASONS = frozenset(
    {
        "DIVIDEND_COEFFICIENT_DIVIDED_BY_DIVISOR_COEFFICIENT",
        "DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT",
    }
)
EXPONENT_REASONS = frozenset(
    {
        "DIVIDEND_EXPONENT_MINUS_DIVISOR_EXPONENT",
        "DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT",
    }
)
CORRECT_COEFFICIENT_REASON = "DIVIDEND_COEFFICIENT_DIVIDED_BY_DIVISOR_COEFFICIENT"
CORRECT_EXPONENT_REASON = "DIVIDEND_EXPONENT_MINUS_DIVISOR_EXPONENT"
_FRACTION_WIRE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z")


def _load_generators():
    path = (
        Path(__file__).parents[1]
        / "ontario-algebra-family-generators-r1"
        / "seeded_family_extensions.py"
    )
    spec = importlib.util.spec_from_file_location("mihur_issue337_algebra_generators", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load generator module at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


generators = _load_generators()


def _validate(seed: int, mode: str) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-boolean integer")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError(f"Unsupported mode: {mode!r}")


def _generator_seed(seed: int, structure: str) -> int:
    offset = 0 if structure == "MONOMIAL_QUOTIENT" else 1
    return seed * 5 + offset


def _term_texts(values: tuple[Any, ...]) -> list[str]:
    return [value.text() for value in values]


def _fraction_wire(value: Fraction | int) -> str:
    exact = Fraction(value)
    if exact.denominator == 1:
        return str(exact.numerator)
    return f"{exact.numerator}/{exact.denominator}"


def _parse_fraction_wire(value: object) -> Fraction:
    if not isinstance(value, str) or not _FRACTION_WIRE.fullmatch(value):
        raise ValueError("coefficient must be a canonical exact-rational string")
    exact = Fraction(value)
    if _fraction_wire(exact) != value:
        raise ValueError("coefficient must be reduced and canonically signed")
    return exact


def _term_record(term: Any) -> dict[str, Any]:
    powers = term.power_map()
    return {
        "coefficient": _fraction_wire(term.coefficient),
        "x_exponent": powers.get("x", 0),
        "y_exponent": powers.get("y", 0),
    }


def _parse_term_record(value: object) -> tuple[Fraction, int, int]:
    required = {"coefficient", "x_exponent", "y_exponent"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("each term requires only coefficient, x_exponent and y_exponent")
    x_exponent = value["x_exponent"]
    y_exponent = value["y_exponent"]
    if type(x_exponent) is not int or type(y_exponent) is not int:
        raise ValueError("term exponents must be integers")
    coefficient = _parse_fraction_wire(value["coefficient"])
    if coefficient == 0:
        raise ValueError("zero-coefficient term records are not permitted")
    return coefficient, x_exponent, y_exponent


def _canonical_term_records(
    value: object, *, maximum: int = 4
) -> tuple[tuple[Fraction, int, int], ...]:
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise ValueError(f"terms must contain between 1 and {maximum} term records")
    parsed = tuple(_parse_term_record(term) for term in value)
    powers = [(x_exponent, y_exponent) for _, x_exponent, y_exponent in parsed]
    if len(set(powers)) != len(powers):
        raise ValueError("term records must have unique exponent pairs")
    return tuple(sorted(parsed, key=lambda term: (-term[1], -term[2], term[0])))


def _restriction_symbols(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or any(symbol not in {"x", "y"} for symbol in value):
        raise ValueError("domain_restrictions must be a list containing only x and y")
    if value != sorted(set(value)):
        raise ValueError("domain_restrictions must be sorted and unique")
    return tuple(value)


def _reconstruction_record(quotient: Any, divisor: Any, product: Any) -> dict[str, Any]:
    return {
        "quotient_term": _term_record(quotient),
        "divisor_term": _term_record(divisor),
        "product_term": _term_record(product),
    }


def _parse_reconstruction(value: object) -> tuple[tuple[Any, ...], ...]:
    if not isinstance(value, list) or not 1 <= len(value) <= 4:
        raise ValueError("reconstruction must contain between 1 and 4 records")
    required = {"quotient_term", "divisor_term", "product_term"}
    parsed: list[tuple[Any, ...]] = []
    for record in value:
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError(
                "each reconstruction record requires quotient_term, divisor_term and product_term"
            )
        quotient = _parse_term_record(record["quotient_term"])
        divisor = _parse_term_record(record["divisor_term"])
        product = _parse_term_record(record["product_term"])
        parsed.append((quotient, divisor, product))
    return tuple(sorted(parsed, key=lambda record: (-record[0][1], -record[0][2], record[0][0])))


def _structured_oracle(
    quotient_terms: tuple[Any, ...],
    dividend_terms: tuple[Any, ...],
    divisor: Any,
    restrictions: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "terms": [_term_record(term) for term in quotient_terms],
        "domain_restrictions": list(restrictions),
        "coefficient_reason": CORRECT_COEFFICIENT_REASON,
        "exponent_reason": CORRECT_EXPONENT_REASON,
        "reconstruction": [
            _reconstruction_record(quotient, divisor, dividend)
            for quotient, dividend in zip(quotient_terms, dividend_terms, strict=True)
        ],
    }


def normalize_structured_response(response: object) -> dict[str, Any]:
    """Parse the proposed wire contract without treating it as backend authority."""

    required = {
        "terms",
        "domain_restrictions",
        "coefficient_reason",
        "exponent_reason",
        "reconstruction",
    }
    if not isinstance(response, dict) or set(response) != required:
        raise ValueError("response fields do not match the versioned polynomial-division contract")
    coefficient_reason = response["coefficient_reason"]
    exponent_reason = response["exponent_reason"]
    if coefficient_reason not in COEFFICIENT_REASONS:
        raise ValueError("unsupported coefficient_reason")
    if exponent_reason not in EXPONENT_REASONS:
        raise ValueError("unsupported exponent_reason")
    return {
        "terms": _canonical_term_records(response["terms"]),
        "domain_restrictions": _restriction_symbols(response["domain_restrictions"]),
        "coefficient_reason": coefficient_reason,
        "exponent_reason": exponent_reason,
        "reconstruction": _parse_reconstruction(response["reconstruction"]),
    }


@dataclass(frozen=True)
class PackageVariant:
    variant_id: str
    mode: str
    structure: str
    prompt: str
    response_schema: tuple[str, ...]
    flow: tuple[dict[str, Any], ...]
    transfer: dict[str, Any]
    teacher_oracle: dict[str, Any]

    def public_payload(self) -> dict[str, Any]:
        payload = {
            "package_id": PACKAGE_ID,
            "revision": REVISION,
            "status": STATUS,
            "runtime_activation": RUNTIME_ACTIVATION,
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "prompt": self.prompt,
            "response_schema": list(self.response_schema),
            "response_contract_revision": RESPONSE_CONTRACT_REVISION,
        }
        if self.mode == "guided":
            payload["flow"] = [dict(step) for step in self.flow]
            payload["transfer_prompt"] = self.transfer["prompt"]
            payload["mve_requirement"] = "GROUPED_TERM_DIVISION_MVE_NOT_IMPLEMENTED"
        else:
            payload["assessment_contract"] = {
                "hints": False,
                "worked_steps": False,
                "guided_mve": False,
                "practice_credit": False,
                "backend_trusted_scoring": "REQUIRED_NOT_WIRED",
            }
        return payload


def _build_transfer(seed: int, mode: str) -> dict[str, Any]:
    rng = random.Random(f"{PACKAGE_ID}:composite-area:{mode}:{seed}")
    common_height = generators.Monomial.make(rng.choice((2, 3, 4)), {"x": rng.randint(1, 2)})
    width_1 = generators.Monomial.make(rng.choice((2, 3, 5)), {"x": rng.randint(0, 2), "y": 1})
    width_2 = generators.Monomial.make(rng.choice((3, 4, 6)), {"x": rng.randint(0, 1), "y": 2})
    area_terms = (width_1.multiply(common_height), width_2.multiply(common_height))
    prompt = (
        "A composite display is split into two algebraic rectangles with the same height "
        f"{common_height.text()} units and exact areas {area_terms[0].text()} and {area_terms[1].text()} "
        "square units. Recover both widths, write the total width, state the original nonzero "
        "restriction, and verify both areas by multiplication."
    )
    return {
        "variant_id": f"{PACKAGE_ID}:composite-area:{mode}:{seed}",
        "prompt": prompt,
        "parameters": {"common_height": common_height, "area_terms": area_terms},
        "oracle": {
            "width_terms": [_term_record(width_1), _term_record(width_2)],
            "total_width_terms": [_term_record(width_1), _term_record(width_2)],
            "domain_restrictions": [name for name, _ in common_height.powers],
            "multiplication_checks": [
                _reconstruction_record(width_1, common_height, area_terms[0]),
                _reconstruction_record(width_2, common_height, area_terms[1]),
            ],
            "units": {"width": "units", "area": "square units"},
        },
    }


def generate(seed: int, mode: str) -> PackageVariant:
    """Generate a mode-separated package variant without runtime registration."""

    _validate(seed, mode)
    structure = "MONOMIAL_QUOTIENT" if seed % 2 == 0 else "POLYNOMIAL_BY_MONOMIAL"
    source = generators.generate(_generator_seed(seed, structure), mode)
    transfer = _build_transfer(seed, mode)
    if structure == "MONOMIAL_QUOTIENT":
        quotient_terms = (source.teacher_oracle["quotient"],)
        dividend_terms = (source.parameters["dividend"],)
    else:
        quotient_terms = source.teacher_oracle["quotient_terms"]
        dividend_terms = source.parameters["dividend_terms"]

    flow = (
        {
            "phase": "OBSERVE",
            "prompt": "Inspect every grouped dividend term and the shared divisor. Name factors that appear in both.",
            "evidence": ["selected_terms", "shared_factor_observation"],
        },
        {
            "phase": "PREDICT",
            "prompt": "Predict each quotient sign, whether each exponent grows or shrinks, and which values make the original divisor zero.",
            "evidence": ["sign_predictions", "factor_count_predictions", "domain_prediction"],
        },
        {
            "phase": "MANIPULATE",
            "prompt": "Apply the same divisor to each grouped term; cancel matching factor tokens and keep the original-domain tokens visible.",
            "representation": "GROUPED_TERM_DIVISION_MVE_NOT_IMPLEMENTED",
            "keyboard_required": True,
            "screen_reader_equivalent_required": True,
            "reduced_motion_required": True,
        },
        {
            "phase": "EXPLAIN",
            "prompt": "Explain why coefficients divide, like-base exponent counts subtract, and cancellation cannot restore excluded values.",
            "evidence": ["coefficient_reason", "exponent_reason", "domain_reason"],
        },
        {
            "phase": "PRACTICE",
            "prompt": source.prompt,
            "response_schema": [
                "terms",
                "domain_restrictions",
                "coefficient_reason",
                "exponent_reason",
                "reconstruction",
            ],
            "response_contract_revision": RESPONSE_CONTRACT_REVISION,
            "scaffold_state": "COACHED",
            "mastery_credit": False,
        },
        {
            "phase": "DIAGNOSE",
            "prompt": "Reconstruct the dividend. A mismatch routes only to the evidenced coefficient, exponent, all-terms, or domain repair.",
            "evidence": [
                "coefficient_orientation",
                "exponent_operation",
                "divided_term_count",
                "domain_recorded",
            ],
        },
        {
            "phase": "TRANSFER",
            "prompt": transfer["prompt"],
            "response_schema": [
                "width_terms",
                "total_width_terms",
                "domain_restrictions",
                "multiplication_checks",
                "units",
            ],
        },
        {
            "phase": "VERIFY",
            "prompt": "Complete a fresh hidden quotient and prove it by multiplication. No guided representation or hints are available.",
            "backend_trusted_scoring": "REQUIRED_NOT_WIRED",
            "mastery_available": False,
        },
    )
    teacher_oracle = {
        "quotient_terms": quotient_terms,
        "dividend_terms": dividend_terms,
        "divisor": source.parameters["divisor"],
        "domain_restrictions": source.teacher_oracle["domain_restrictions"],
        "structured_response": _structured_oracle(
            quotient_terms,
            dividend_terms,
            source.parameters["divisor"],
            source.teacher_oracle["domain_restrictions"],
        ),
        "transfer": transfer["oracle"],
    }
    return PackageVariant(
        variant_id=f"{PACKAGE_ID}:{mode}:{seed}",
        mode=mode,
        structure=structure,
        prompt=source.prompt,
        response_schema=(
            "terms",
            "domain_restrictions",
            "coefficient_reason",
            "exponent_reason",
            "reconstruction",
        ),
        flow=flow,
        transfer=transfer,
        teacher_oracle=teacher_oracle,
    )


def evaluate_structured_response(response: object, variant: PackageVariant) -> bool:
    """Evaluate the draft evidence contract locally; this never awards mastery."""

    if not isinstance(variant, PackageVariant):
        raise TypeError("variant must be a PackageVariant")
    observed = normalize_structured_response(response)
    expected = normalize_structured_response(variant.teacher_oracle["structured_response"])
    return observed == expected


def _pattern_terms(variant: PackageVariant, pattern: str) -> tuple[tuple[Fraction, int, int], ...]:
    divisor = variant.teacher_oracle["divisor"]
    divisor_powers = divisor.power_map()
    terms = []
    for dividend, expected in zip(
        variant.teacher_oracle["dividend_terms"],
        variant.teacher_oracle["quotient_terms"],
        strict=True,
    ):
        if pattern == "COEFFICIENT_RECIPROCAL":
            term = generators.Monomial.make(
                divisor.coefficient / dividend.coefficient, expected.power_map()
            )
        elif pattern == "ADD_EXPONENTS":
            powers = dividend.power_map()
            for name, exponent in divisor_powers.items():
                powers[name] = powers.get(name, 0) + exponent
            term = generators.Monomial.make(expected.coefficient, powers)
        else:
            raise ValueError(f"Unsupported diagnostic pattern: {pattern!r}")
        terms.append(_parse_term_record(_term_record(term)))
    return tuple(sorted(terms, key=lambda term: (-term[1], -term[2], term[0])))


def diagnose_response(response: object, variant: PackageVariant) -> str:
    """Diagnose only deterministic response evidence; ambiguous work fails closed."""

    observed = normalize_structured_response(response)
    expected = normalize_structured_response(variant.teacher_oracle["structured_response"])
    if observed == expected:
        return "NO_REMEDIATION"
    if len(observed["terms"]) < len(expected["terms"]):
        return "POLY.DIV.ONE_TERM_ONLY"
    if observed[
        "coefficient_reason"
    ] == "DIVISOR_COEFFICIENT_DIVIDED_BY_DIVIDEND_COEFFICIENT" or observed[
        "terms"
    ] == _pattern_terms(variant, "COEFFICIENT_RECIPROCAL"):
        return "POLY.DIV.COEFFICIENT_RECIPROCAL"
    if observed["exponent_reason"] == "DIVIDEND_EXPONENT_PLUS_DIVISOR_EXPONENT" or observed[
        "terms"
    ] == _pattern_terms(variant, "ADD_EXPONENTS"):
        return "POLY.DIV.ADD_EXPONENTS"
    if (
        observed["terms"] == expected["terms"]
        and observed["domain_restrictions"] != expected["domain_restrictions"]
        and set(observed["domain_restrictions"]).issubset(expected["domain_restrictions"])
    ):
        return "POLY.DIV.DOMAIN_OMITTED"
    return "UNCLASSIFIED_FOR_HUMAN_REVIEW"


def fresh_exit(seed: int, mode: str, misconception_id: str) -> PackageVariant:
    _validate(seed, mode)
    if misconception_id not in MISCONCEPTIONS:
        raise ValueError(f"Unsupported misconception: {misconception_id!r}")
    order = sorted(MISCONCEPTIONS).index(misconception_id)
    fresh_seed = 100_000 + seed * 16 + order * 2
    if misconception_id == "POLY.DIV.ONE_TERM_ONLY":
        fresh_seed += 1
    if misconception_id != "POLY.DIV.ADD_EXPONENTS":
        return generate(fresh_seed, mode)
    for offset in range(2_048):
        candidate = generate(fresh_seed + offset, mode)
        if any(
            exponent < 0
            for term in candidate.teacher_oracle["quotient_terms"]
            for _, exponent in term.powers
        ):
            return candidate
    raise RuntimeError("unable to generate a bounded negative-exponent fresh exit")


def advance_scaffold(state: str, event: str) -> str:
    if state not in SCAFFOLD_STATES:
        raise ValueError(f"Unsupported scaffold state: {state!r}")
    if event not in {"EVIDENCE_CORRECT", "MISCONCEPTION_DIAGNOSED"}:
        raise ValueError(f"Unsupported scaffold event: {event!r}")
    if event == "MISCONCEPTION_DIAGNOSED":
        return "COACHED"
    return {
        "MODELED": "COACHED",
        "COACHED": "INDEPENDENT_READINESS",
        "INDEPENDENT_READINESS": "INDEPENDENT_READINESS",
    }[state]


def independent_reconstruction(variant: PackageVariant) -> tuple[bool, ...]:
    """Exact package-level oracle independent of displayed simplification text."""

    divisor = variant.teacher_oracle["divisor"]
    return tuple(
        quotient.multiply(divisor) == dividend
        for quotient, dividend in zip(
            variant.teacher_oracle["quotient_terms"],
            variant.teacher_oracle["dividend_terms"],
            strict=True,
        )
    )


def exact_value(term: Any, *, x: int, y: int) -> Fraction:
    return term.evaluate({"x": Fraction(x), "y": Fraction(y)})
