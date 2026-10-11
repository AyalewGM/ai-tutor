from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "ontario-algebra-family-generators-r1"


def _load_json(name: str) -> dict:
    return json.loads((DRAFT / name).read_text(encoding="utf-8"))


def _generators():
    path = DRAFT / "seeded_family_extensions.py"
    spec = importlib.util.spec_from_file_location("ontario_algebra_family_generators", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_provenance_and_traceability_fail_closed() -> None:
    provenance = _load_json("provenance.json")
    traceability = _load_json("traceability.json")

    assert provenance["status"] == "DRAFT_UNVERIFIED"
    assert provenance["runtime_activation"] is False
    assert provenance["learner_data_writes"] is False
    assert provenance["mastery_writes"] is False
    assert provenance["standards"]["exact_expectation_ids"] == []
    assert provenance["standards"]["mapping_approval"] == "NONE"
    assert provenance["delivery_status"]["wired"] is False
    assert provenance["delivery_status"]["independently_accepted"] is False
    assert provenance["delivery_status"]["deployed"] is False
    assert traceability["runtime_activation"] is False
    assert len(traceability["rows"]) == 5
    assert all(row["existing_work"] for row in traceability["rows"])
    assert all(row["actual_gap"] for row in traceability["rows"])
    assert all(row["planned_improvement"] for row in traceability["rows"])
    assert all(row["verification"] for row in traceability["rows"])


def test_no_new_canonical_identity_and_expected_reuse_only() -> None:
    provenance = _load_json("provenance.json")
    records = provenance["canonical_reuse"]

    assert all(record["new_canonical_identity"] is False for record in records)
    assert {record["canonical_family"] for record in records} == {
        "MATH.EE.POLYNOMIAL_OPERATIONS",
        "MATH.NS.EXPONENTS",
        "MATH.NS.ROOTS",
        "MATH.NS.SCIENTIFIC_NOTATION",
    }
    assert {
        record["status"] for record in records
    } == {"HISTORICAL_IMPLEMENTATION_REUSE_ONLY_NO_NEW_MASTERY"}
    boundary = provenance["architecture_boundary"]
    assert boundary["status"] == "SETTLED_BOUNDARIES_DRAFT_IDENTITIES_NOT_AUTHORITY"
    assert boundary["scope_card_owner"] == "CANONICAL_CURRICULUM_CONTENT"
    assert boundary["generator_binding"].startswith("UNBOUND_PENDING_")
    assert boundary["no_duplicate_credit"] is True
    assert boundary["historical_mastery_reinterpretation"] is False


def test_seeded_replay_mode_separation_diversity_and_oracle_non_disclosure() -> None:
    generators = _generators()
    seen: dict[str, set[str]] = {structure: set() for structure in generators.STRUCTURES}

    for seed in range(250):
        guided = generators.generate(seed, "guided")
        independent = generators.generate(seed, "independent")
        assert guided == generators.generate(seed, "guided")
        assert independent == generators.generate(seed, "independent")
        assert guided.variant_id != independent.variant_id
        assert guided.prompt != independent.prompt
        payload = independent.public_payload()
        assert "teacher_oracle" not in payload
        assert "parameters" not in payload
        assert "hint" not in " ".join(payload).lower()
        seen[independent.structure].add(independent.prompt)

    assert all(len(prompts) >= 20 for prompts in seen.values())


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "4", None])
def test_invalid_seeds_fail_closed(seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _generators().generate(seed, "independent")


@pytest.mark.parametrize("mode", ["", "assessment", "INDEPENDENT", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        _generators().generate(3, mode)


def test_monomial_quotient_matches_independent_division_and_round_trip() -> None:
    generators = _generators()

    for seed in range(0, 500, 5):
        item = generators.generate(seed, "independent")
        dividend = item.parameters["dividend"]
        divisor = item.parameters["divisor"]
        quotient, restrictions = generators.divide_monomials(dividend, divisor)
        assert quotient == item.teacher_oracle["quotient"]
        assert quotient.multiply(divisor) == dividend
        assert restrictions == item.teacher_oracle["domain_restrictions"]
        assert restrictions
        values = {name: Fraction(index + 2) for index, name in enumerate({*dividend.power_map(), *divisor.power_map()})}
        assert quotient.evaluate(values) == dividend.evaluate(values) / divisor.evaluate(values)


def test_zero_divisor_is_rejected() -> None:
    generators = _generators()
    dividend = generators.Monomial.make(6, {"x": 2})
    zero = generators.Monomial.make(0, {"x": 1})

    with pytest.raises(ZeroDivisionError, match="cannot be zero"):
        generators.divide_monomials(dividend, zero)


def test_polynomial_quotient_divides_every_term_and_reconstructs() -> None:
    generators = _generators()

    for seed in range(1, 500, 5):
        item = generators.generate(seed, "independent")
        divisor = item.parameters["divisor"]
        dividend_terms = item.parameters["dividend_terms"]
        quotient_terms = item.teacher_oracle["quotient_terms"]
        assert len(dividend_terms) == len(quotient_terms) == 2
        for dividend, expected in zip(dividend_terms, quotient_terms, strict=True):
            actual, restrictions = generators.divide_monomials(dividend, divisor)
            assert actual == expected
            assert actual.multiply(divisor) == dividend
            assert restrictions == item.teacher_oracle["domain_restrictions"]


def test_combined_exponent_oracle_is_exact_including_negative_results() -> None:
    generators = _generators()
    negative_results = 0
    zero_results = 0
    positive_results = 0

    for seed in range(2, 1000, 5):
        item = generators.generate(seed, "independent")
        p = item.parameters
        expected_exponent = p["m"] + p["n"] - p["p"] * p["q"]
        assert item.teacher_oracle["result_exponent"] == expected_exponent
        expected_value = Fraction(p["base"] ** expected_exponent) if expected_exponent >= 0 else Fraction(1, p["base"] ** (-expected_exponent))
        assert item.teacher_oracle["exact_value"] == expected_value
        assert p["base_nonzero"] is True
        assert item.teacher_oracle["base_nonzero_required"] is True
        assert p["law_case"] == ("ZERO_EXPONENT" if expected_exponent == 0 else "NONZERO_EXPONENT")
        assert f"base {p['base']} is nonzero" in item.prompt
        negative_results += expected_exponent < 0
        zero_results += expected_exponent == 0
        positive_results += expected_exponent > 0

    assert negative_results >= 25
    assert zero_results >= 25
    assert positive_results >= 25


def test_zero_exponent_variants_independently_establish_nonzero_base_and_value_one() -> None:
    generators = _generators()

    zero_variants = [
        generators.generate(seed, "independent")
        for seed in range(2, 1000, 5)
        if generators.generate(seed, "independent").teacher_oracle["result_exponent"] == 0
    ]

    assert len(zero_variants) >= 25
    for item in zero_variants:
        parameters = item.parameters
        assert parameters["base"] != 0
        assert parameters["m"] + parameters["n"] == parameters["p"] * parameters["q"]
        assert item.teacher_oracle["exact_value"] == Fraction(1)
        assert item.public_payload()["prompt"].endswith(f"The base {parameters['base']} is nonzero.")


def test_exponent_geometry_transfer_is_deterministic_exact_and_dimensionally_labeled() -> None:
    generators = _generators()
    observed = set()

    for seed in range(200):
        item = generators.generate_geometry_transfer(seed, "independent")
        assert item == generators.generate_geometry_transfer(seed, "independent")
        assert item.prompt != generators.generate_geometry_transfer(seed, "guided").prompt
        assert "teacher_oracle" not in item.public_payload()
        parameters = item.parameters
        oracle = item.teacher_oracle
        observed.add(parameters["shape"])
        assert oracle["result_coefficient"] == (
            parameters["dimension_coefficient"] ** parameters["dimensional_power"]
        )
        assert oracle["result_exponent"] == (
            parameters["dimension_exponent"] * parameters["dimensional_power"]
        )
        assert oracle["exact_value"] == (
            oracle["result_coefficient"] * parameters["base"] ** oracle["result_exponent"]
        )
        expected_units = "square units" if parameters["shape"] == "SQUARE" else "cubic units"
        assert oracle["units"] == expected_units

    assert observed == {"SQUARE", "CUBE"}


def test_root_equation_has_complete_exact_solution_set_or_no_real_branch() -> None:
    generators = _generators()
    observed = set()

    for seed in range(3, 1000, 5):
        item = generators.generate(seed, "independent")
        coefficient = item.parameters["coefficient"]
        shift = item.parameters["shift"]
        radicand = item.parameters["radicand"]
        classification = item.teacher_oracle["classification"]
        observed.add(classification)
        solutions = item.teacher_oracle["solutions"]
        if radicand < 0:
            assert classification == "NO_REAL_SOLUTIONS"
            assert solutions == ()
        else:
            assert classification == "TWO_REAL_SOLUTIONS"
            assert len(solutions) == 2
            assert all((coefficient * solution + shift) ** 2 == radicand for solution in solutions)

    assert observed == {"NO_REAL_SOLUTIONS", "TWO_REAL_SOLUTIONS"}


def test_scientific_notation_operations_are_normalized_and_value_preserving() -> None:
    generators = _generators()
    operations = set()

    for seed in range(4, 1004, 5):
        item = generators.generate(seed, "independent")
        coefficient = item.teacher_oracle["coefficient"]
        exponent = item.teacher_oracle["exponent"]
        ordinary = item.teacher_oracle["ordinary_value"]
        operations.add(item.parameters["operation"])
        assert Fraction(1) <= abs(coefficient) < 10
        factor = Fraction(10**exponent) if exponent >= 0 else Fraction(1, 10 ** (-exponent))
        assert coefficient * factor == ordinary
        renormalized = generators.normalize_scientific(coefficient, exponent)
        assert renormalized == (coefficient, exponent)

    assert operations == {"TO_SCIENTIFIC", "TO_ORDINARY", "MULTIPLY", "DIVIDE"}


def test_diagnostics_are_evidence_specific_and_correct_work_never_routes() -> None:
    generators = _generators()
    cases = [
        ({"coefficient_division_reversed": True}, "POLY.DIV.COEFFICIENT_RECIPROCAL"),
        ({"quotient_exponents_added": True}, "POLY.DIV.ADD_EXPONENTS"),
        ({"all_polynomial_terms_divided": False}, "POLY.DIV.ONE_TERM_ONLY"),
        ({"zero_exponent_written_as_zero": True}, "EXP.ZERO_WRITTEN_AS_ZERO"),
        ({"negative_exponent_written_as_negative_value": True}, "EXP.NEGATIVE_IS_NEGATIVE_VALUE"),
        (
            {
                "geometry_power_applied_to_coefficient": True,
                "geometry_power_applied_to_exponent": False,
            },
            "EXP.GEOMETRY.POWER_NOT_DISTRIBUTED",
        ),
        ({"equation_requires_solution_set": True, "only_principal_root_given": True}, "ROOT.PRINCIPAL_ONLY"),
        ({"decimal_shift_matches_exponent": False}, "SCI.EXPONENT.DIRECTION"),
        ({"coefficient_normalized": False}, "SCI.NOT_NORMALIZED"),
    ]

    assert generators.diagnose_response({"response_correct": True}) is None
    for evidence, expected in cases:
        assert generators.diagnose_response(evidence) == expected
    with pytest.raises(ValueError, match="Unsupported evidence"):
        generators.diagnose_response({"generic_wrong": True})
    with pytest.raises(TypeError, match="booleans"):
        generators.diagnose_response({"coefficient_normalized": 0})


def test_every_diagnostic_has_unique_socratic_path_and_fresh_exit() -> None:
    generators = _generators()
    paths = _load_json("misconception_paths.json")["paths"]

    assert {path["misconception_id"] for path in paths} == generators.MISCONCEPTIONS
    assert len({tuple(path["socratic_questions"]) for path in paths}) == len(paths)
    assert all(len(path["socratic_questions"]) == 3 for path in paths)
    assert all(path["observed_evidence"] for path in paths)
    assert all(path["fresh_exit"] for path in paths)


def test_draft_module_is_not_registered_for_runtime_generation() -> None:
    from app.canonical_problem_families import FAMILIES

    assert not any(code.startswith("ONT-ALG-FAMILY-GENERATORS") for code in FAMILIES)
    assert "ontario-algebra-family-generators-r1" not in str(FAMILIES)
