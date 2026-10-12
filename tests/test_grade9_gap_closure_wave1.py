"""Fail-closed checks for the Grade 9 gap-closure content wave."""

from __future__ import annotations

import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs/curriculum/drafts/grade9-gap-closure-wave1"
PACKAGE = json.loads((DIR / "package.json").read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("grade9_gap_variants", DIR / "variants.py")
assert spec is not None and spec.loader is not None
MODULE = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = MODULE
spec.loader.exec_module(MODULE)


def test_manifest_contains_all_twenty_packages_and_hard_gates() -> None:
    ids = [row["id"] for row in PACKAGE["packages"]]
    assert len(ids) == 20
    assert len(set(ids)) == 20
    assert set(ids) == set(MODULE.CONCEPTS)
    assert PACKAGE["status"] == "DRAFT_UNVERIFIED"
    assert PACKAGE["runtime_activation"] is False
    assert PACKAGE["mastery_writes"] is False
    assert PACKAGE["gates"]["production_wired"] is False
    assert PACKAGE["gates"]["standards_accepted"] is False
    assert PACKAGE["gates"]["math_accepted"] is False
    assert PACKAGE["gates"]["pedagogy_accepted"] is False
    assert PACKAGE["gates"]["architecture_accepted"] is False
    assert PACKAGE["gates"]["assessment_backend_wired"] is False
    assert PACKAGE["gates"]["muse_qa"] is False
    assert PACKAGE["gates"]["deployed"] is False

    required_phases = [
        "OBSERVE", "PREDICT", "MANIPULATE", "EXPLAIN",
        "PRACTICE", "DIAGNOSE", "TRANSFER", "VERIFY",
    ]
    for package in PACKAGE["packages"]:
        assert [row["phase"] for row in package["teaching_flow"]] == required_phases
        assert len(package["core_reasoning"]) >= 3
        assert len(package["misconception_routes"]) >= 3
        assert package["independent_transfer"]["unseen_namespace"] is True
        assert package["independent_transfer"]["no_hints"] is True


@pytest.mark.parametrize("mode", ["guided", "independent"])
def test_every_concept_has_deterministic_seeded_variants(mode: str) -> None:
    for concept in MODULE.CONCEPTS:
        prompts = set()
        for seed in range(12):
            one = MODULE.generate(concept, seed, mode)
            two = MODULE.generate(concept, seed, mode)
            assert one == two
            assert one.mode == mode
            assert one.concept_id == concept
            assert one.teacher_oracle()
            assert one.public_fields
            payload = one.public_payload()
            assert payload["item_id"] == one.item_id
            assert "oracle" not in payload
            assert "teacher_oracle" not in payload
            assert "answer" not in payload
            prompts.add(one.prompt)
        assert len(prompts) >= 2


def test_guided_and_independent_namespaces_do_not_reuse_items() -> None:
    for concept in MODULE.CONCEPTS:
        for seed in range(40):
            guided = MODULE.generate(concept, seed, "guided")
            independent = MODULE.generate(concept, seed, "independent")
            assert guided.item_id != independent.item_id
            # Guided and independent items live in disjoint namespaces. Mathematical
            # prompts may occasionally coincide by chance, so text inequality is not
            # required for every same-seed pair.


def test_absolute_value_has_complete_two_branch_solution_sets() -> None:
    for mode in MODULE.MODES:
        for seed in range(30):
            variant = MODULE.generate("G9-ABS-EQUATIONS", seed, mode)
            solutions = [Fraction(x) for x in variant.teacher_oracle()["solutions"]]
            assert len(solutions) == 2
            assert solutions[0] < solutions[1]
            assert variant.teacher_oracle()["complete_set"] is True


def test_2d_inequality_boundary_semantics_cover_all_styles_and_regions() -> None:
    seen_styles = set()
    seen_regions = set()
    for seed in range(80):
        oracle = MODULE.generate(
            "G9-TWO-VAR-INEQUALITIES", seed, "guided"
        ).teacher_oracle()
        seen_styles.add(oracle["boundary_style"])
        seen_regions.add(oracle["half_plane"])
        assert oracle["test_point_satisfies"] is True
    assert seen_styles == {"SOLID", "DASHED"}
    assert seen_regions == {"ABOVE", "BELOW"}


def test_system_inequality_samples_distinguish_feasible_from_infeasible() -> None:
    for seed in range(30):
        oracle = MODULE.generate(
            "G9-SYSTEMS-INEQUALITIES", seed, "independent"
        ).teacher_oracle()
        fx, fy = oracle["sample_feasible"]
        ix, iy = oracle["sample_infeasible"]
        # Prompt construction guarantees x>=a, y>=0, x+y<=c for feasible,
        # and the infeasible example violates x>=a by exactly one.
        assert fy == 0 and iy == 0
        assert fx > ix
        assert oracle["intersection_semantics"] == "ALL_CONSTRAINTS"


def test_optimization_oracle_is_maximum_over_declared_vertices() -> None:
    for seed in range(40):
        oracle = MODULE.generate(
            "G9-LINEAR-OPTIMIZATION", seed, "guided"
        ).teacher_oracle()
        assert oracle["optimal_point"] in oracle["vertices"]
        assert isinstance(oracle["optimal_value"], int)


def test_linear_exponential_intersection_is_integer_and_verified() -> None:
    for seed in range(40):
        oracle = MODULE.generate(
            "G9-LINEAR-EXP-INTERSECTION", seed, "independent"
        ).teacher_oracle()
        x, y = oracle["intersection"]
        assert y == 2**x
        assert oracle["verified"] is True


def test_domain_range_function_has_one_output_per_domain_input() -> None:
    for seed in range(30):
        oracle = MODULE.generate(
            "G9-DOMAIN-RANGE-NOTATION", seed, "guided"
        ).teacher_oracle()
        assert len(oracle["domain"]) == len(oracle["range"])
        assert len(set(oracle["domain"])) == len(oracle["domain"])
        assert oracle["value"] == oracle["range"][-1]


def test_inverse_linear_requires_composition_and_input_output_swap() -> None:
    for seed in range(20):
        oracle = MODULE.generate(
            "G9-INVERSE-LINEAR", seed, "independent"
        ).teacher_oracle()
        assert oracle["composition_identity"] is True
        assert oracle["input_output_swap"] is True
        assert "x" in oracle["inverse"]


def test_piecewise_absolute_value_vertex_and_shape() -> None:
    for seed in range(30):
        oracle = MODULE.generate(
            "G9-PIECEWISE-ABS-FUNCTIONS", seed, "guided"
        ).teacher_oracle()
        assert len(oracle["vertex"]) == 2
        assert oracle["shape"] == "V"
        assert oracle["distance_meaning"] is True


def test_average_rate_change_is_delta_y_over_delta_x() -> None:
    for seed in range(40):
        oracle = MODULE.generate(
            "G9-AVERAGE-RATE-CHANGE", seed, "independent"
        ).teacher_oracle()
        assert Fraction(oracle["average_rate"]) == Fraction(
            oracle["delta_y"], oracle["delta_x"]
        )
        assert oracle["delta_x"] > 0


def test_sequences_cover_arithmetic_and_geometric_explicit_recursive_forms() -> None:
    kinds = set()
    for seed in range(40):
        oracle = MODULE.generate("G9-SEQUENCES", seed, "guided").teacher_oracle()
        kinds.add(oracle["type"])
        assert "n" in oracle["explicit"]
        assert "a_n" in oracle["recursive"]
        assert isinstance(oracle["term"], int)
    assert kinds == {"ARITHMETIC", "GEOMETRIC"}


def test_transformations_record_vertex_from_horizontal_and_vertical_shifts() -> None:
    for seed in range(30):
        oracle = MODULE.generate(
            "G9-FUNCTION-TRANSFORMATIONS", seed, "guided"
        ).teacher_oracle()
        assert oracle["vertex"] == [
            oracle["horizontal_shift"],
            oracle["vertical_shift"],
        ]


def test_parallel_and_perpendicular_slopes_are_exact_negative_reciprocals() -> None:
    for seed in range(30):
        oracle = MODULE.generate(
            "G9-SLOPE-GEOMETRY", seed, "independent"
        ).teacher_oracle()
        parallel = Fraction(oracle["parallel_slope"])
        perpendicular = Fraction(oracle["perpendicular_slope"])
        assert parallel * perpendicular == -1


def test_triangle_congruence_rejects_aaa_and_generic_ssa() -> None:
    observed = {}
    for seed in range(120):
        oracle = MODULE.generate(
            "G9-TRIANGLE-CONGRUENCE", seed, "guided"
        ).teacher_oracle()
        observed[oracle["criterion"]] = oracle["sufficient"]
    assert observed["AAA"] is False
    assert observed["SSA"] is False
    for method in ("SSS", "SAS", "ASA", "AAS", "HL"):
        assert observed[method] is True


def test_sampling_and_statistical_investigation_do_not_infer_causation() -> None:
    for seed in range(40):
        sampling = MODULE.generate(
            "G9-RANDOM-SAMPLING", seed, "guided"
        ).teacher_oracle()
        assert sampling["population_parameter_not_sample_statistic"] is True
        investigation = MODULE.generate(
            "G9-STAT-INVESTIGATION", seed, "independent"
        ).teacher_oracle()
        assert investigation["causal_claim_allowed_from_observational"] is False
        assert investigation["requires_sampling_plan"] is True


def test_bivariate_prediction_and_correlation_contracts() -> None:
    for seed in range(40):
        model = MODULE.generate(
            "G9-BIVARIATE-MODELING", seed, "guided"
        ).teacher_oracle()
        assert isinstance(model["prediction"], int)
        assert model["extrapolation_caution"] is True

        corr = MODULE.generate(
            "G9-CORRELATION-CAUSATION", seed, "independent"
        ).teacher_oracle()
        assert corr["direction"] in {"POSITIVE", "NEGATIVE"}
        assert corr["strength"] in {"WEAK", "STRONG"}
        assert corr["causation_established"] is False
        assert corr["r_is_not_slope"] is True


def test_precision_formula_and_two_variable_solution_set_contracts() -> None:
    for seed in range(30):
        precision = MODULE.generate(
            "G9-QUANTITY-PRECISION", seed, "guided"
        ).teacher_oracle()
        assert precision["unit"] == "cm"
        assert precision["false_precision_warning"] is True

        formula = MODULE.generate(
            "G9-FORMULA-REARRANGE", seed, "independent"
        ).teacher_oracle()
        assert formula["isolated_formula"] == "h=2A/b"
        assert formula["restriction"] == "b!=0"

        twovar = MODULE.generate(
            "G9-TWO-VAR-EQUATIONS", seed, "guided"
        ).teacher_oracle()
        assert twovar["satisfies"] is True
        assert twovar["graph_is_solution_set"] is True


@pytest.mark.parametrize(
    ("concept", "seed", "mode", "error"),
    [
        ("NO_SUCH_CONCEPT", 1, "guided", ValueError),
        ("G9-SEQUENCES", -1, "guided", ValueError),
        ("G9-SEQUENCES", True, "guided", TypeError),
        ("G9-SEQUENCES", 1, "assessment", ValueError),
    ],
)
def test_invalid_generation_fails_closed(concept, seed, mode, error) -> None:
    with pytest.raises(error):
        MODULE.generate(concept, seed, mode)
