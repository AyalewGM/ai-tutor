"""Focused tests for the two teacher-evidence depth gaps from Issue #337."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP_PATH = ROOT / "docs/curriculum/drafts/exponent-power-geometry-learning-package-r1/learning_flow.py"
ALG_PATH = ROOT / "docs/curriculum/drafts/ontario-algebra-family-generators-r1/seeded_family_extensions.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EXP = _load("ontario_teacher_exp_depth", EXP_PATH)
ALG = _load("ontario_teacher_measurement_depth", ALG_PATH)


def test_existing_reviewed_seed_namespaces_are_not_broadened() -> None:
    assert EXP.KINDS == (
        "POWER_OF_PRODUCT",
        "POWER_OF_QUOTIENT",
        "REWRITE_TO_REQUESTED_BASE",
        "COMPARE_EQUIVALENT_POWERS",
        "CUBE_SURFACE_AREA_AND_VOLUME",
        "PYTHAGOREAN_SQUARE_AREAS",
        "SIMPLIFY_THEN_SUBSTITUTE",
    )
    assert ALG.STRUCTURES == (
        "MONOMIAL_QUOTIENT",
        "POLYNOMIAL_BY_MONOMIAL",
        "COMBINED_EXPONENT_LAWS",
        "ROOT_EQUATION",
        "SCIENTIFIC_NOTATION",
    )


@pytest.mark.parametrize("mode", ["guided", "independent"])
def test_first_error_localization_is_deterministic_exact_and_answer_hidden(mode: str) -> None:
    positions = set()
    laws = set()
    for index in range(60):
        item = EXP.generate_first_error_localization(index, mode)
        replay = EXP.generate_first_error_localization(index, mode)
        assert item == replay
        assert item.kind == "FIRST_ERROR_LOCALIZATION"
        assert EXP.verify_first_error_localization(item)
        positions.add(item.teacher_oracle["first_error_step"])
        laws.add(item.teacher_oracle["violated_law"])

        payload = item.public_payload()
        assert payload["mastery_credit"] is False
        assert "teacher_oracle" not in payload
        assert "parameters" not in payload
        assert set(item.response_fields) == {
            "first_error_step",
            "violated_law",
            "corrected_step_exponent",
            "explanation",
        }

        p = item.parameters
        shown_1, shown_2, shown_3 = p["shown_exponents"]
        assert (
            f"Step 1: (({p['base']}^{p['inner']})^{p['outer']} x "
            f"{p['base']}^{p['product_exponent']}) / {p['base']}^{p['divisor_exponent']} = "
            f"({p['base']}^{shown_1} x {p['base']}^{p['product_exponent']}) / "
            f"{p['base']}^{p['divisor_exponent']}."
        ) in item.prompt
        assert (
            f"Step 2: ({p['base']}^{shown_1} x {p['base']}^{p['product_exponent']}) / "
            f"{p['base']}^{p['divisor_exponent']} = {p['base']}^{shown_2} / "
            f"{p['base']}^{p['divisor_exponent']}."
        ) in item.prompt
        assert (
            f"Step 3: {p['base']}^{shown_2} / {p['base']}^{p['divisor_exponent']} = "
            f"{p['base']}^{shown_3}."
        ) in item.prompt

    assert positions == {1, 2, 3}
    assert laws == {
        "POWER_OF_POWER_MULTIPLIES_EXPONENTS",
        "PRODUCT_OF_POWERS_ADDS_EXPONENTS",
        "QUOTIENT_OF_POWERS_SUBTRACTS_EXPONENTS",
    }


def test_first_error_oracle_recomputes_from_original_not_from_corrupted_work() -> None:
    for index in range(30):
        item = EXP.generate_first_error_localization(index, "independent")
        p = item.parameters
        correct = (
            p["inner"] * p["outer"],
            p["inner"] * p["outer"] + p["product_exponent"],
            p["inner"] * p["outer"] + p["product_exponent"] - p["divisor_exponent"],
        )
        shown = p["shown_exponents"]
        first = next(i + 1 for i, pair in enumerate(zip(shown, correct, strict=True)) if pair[0] != pair[1])
        assert item.teacher_oracle["first_error_step"] == first
        assert item.teacher_oracle["corrected_step_exponent"] == correct[first - 1]
        assert item.teacher_oracle["correct_final_exponent"] == correct[2]


@pytest.mark.parametrize("mode", ["guided", "independent"])
def test_measurement_inversion_reuses_exact_monomial_division_and_reconstructs(mode: str) -> None:
    shapes = set()
    for seed in range(80):
        item = ALG.generate_measurement_inversion(seed, mode)
        replay = ALG.generate_measurement_inversion(seed, mode)
        assert item == replay
        assert item.structure == "ALGEBRAIC_MEASUREMENT_INVERSION"
        assert item.canonical_family == "MATH.EE.POLYNOMIAL_OPERATIONS"
        assert ALG.verify_measurement_inversion(item)

        shapes.add(item.parameters["shape"])
        measure = item.parameters["measure"]
        known = item.parameters["known_factor"]
        recovered, restrictions = ALG.divide_monomials(measure, known)
        assert recovered == item.teacher_oracle["unknown_dimension"]
        assert recovered.multiply(known) == measure
        assert restrictions == item.teacher_oracle["domain_restrictions"]
        assert restrictions
        assert item.teacher_oracle["unknown_units"] == "linear units"

        payload = item.public_payload()
        assert "teacher_oracle" not in payload
        assert "parameters" not in payload
        assert payload["response_schema"] == [
            "unknown_dimension",
            "domain_restrictions",
            "reconstruction",
            "units_explanation",
        ]

    assert shapes == {"RECTANGLE", "RECTANGULAR_PRISM"}


def test_measurement_inversion_preserves_dimensional_units() -> None:
    rectangle = ALG.generate_measurement_inversion(2, "independent")
    prism = ALG.generate_measurement_inversion(3, "independent")

    assert rectangle.parameters["shape"] == "RECTANGLE"
    assert rectangle.teacher_oracle["known_units"] == "linear units"
    assert rectangle.teacher_oracle["measure_units"] == "square units"

    assert prism.parameters["shape"] == "RECTANGULAR_PRISM"
    assert prism.teacher_oracle["known_units"] == "square units"
    assert prism.teacher_oracle["measure_units"] == "cubic units"


@pytest.mark.parametrize("bad", [-1, True, False, 1.5, "3", None])
def test_depth_extension_invalid_seeds_fail_closed(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        EXP.generate_first_error_localization(bad, "guided")
    with pytest.raises((TypeError, ValueError)):
        ALG.generate_measurement_inversion(bad, "guided")


@pytest.mark.parametrize("bad_mode", ["", "assessment", "GUIDED", None, []])
def test_depth_extension_invalid_modes_fail_closed(bad_mode: object) -> None:
    with pytest.raises(ValueError):
        EXP.generate_first_error_localization(1, bad_mode)
    with pytest.raises(ValueError):
        ALG.generate_measurement_inversion(1, bad_mode)
