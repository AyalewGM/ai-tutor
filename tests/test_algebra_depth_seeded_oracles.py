import importlib.util
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "algebra_depth_provenance_20261010"


def load_oracles_module():
    path = DRAFT / "seeded_oracles.py"
    spec = importlib.util.spec_from_file_location("g9_algebra_seeded_oracles", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("seed", range(100))
def test_linear_plan_variants_have_exact_unique_crossover(seed: int) -> None:
    oracles = load_oracles_module()
    first = oracles.generate_linear_plan(seed, "independent")
    second = oracles.generate_linear_plan(seed, "independent")
    parameters = first["parameters"]
    rate_difference = parameters["rate_b"] - parameters["rate_a"]
    fee_difference = parameters["fee_a"] - parameters["fee_b"]
    crossover, remainder = divmod(fee_difference, rate_difference)

    assert first == second
    assert remainder == 0
    assert parameters["fee_a"] + parameters["rate_a"] * crossover == (
        parameters["fee_b"] + parameters["rate_b"] * crossover
    )
    assert parameters["rate_a"] != parameters["rate_b"]
    assert "crossover" not in parameters


@pytest.mark.parametrize("seed", range(100))
def test_quadratic_area_variants_match_factored_and_expanded_oracles(seed: int) -> None:
    oracles = load_oracles_module()
    record = oracles.generate_quadratic_area(seed, "independent")
    parameters = record["parameters"]
    n, a, b = parameters["n"], parameters["a"], parameters["b"]
    factored = (n + a) * (n + b)
    expanded = n**2 + (a + b) * n + a * b

    assert factored == expanded == int(record["answer_teacher_only"])


@pytest.mark.parametrize("seed", range(100))
def test_exponential_variants_match_repeated_fraction_oracle(seed: int) -> None:
    oracles = load_oracles_module()
    record = oracles.generate_exponential_change(seed, "independent")
    parameters = record["parameters"]
    multiplier = Fraction(
        parameters["multiplier_numerator"], parameters["multiplier_denominator"]
    )
    repeated = Fraction(parameters["initial"])
    for _ in range(parameters["periods"]):
        repeated *= multiplier

    assert repeated == Fraction(record["answer_teacher_only"])


@pytest.mark.parametrize(
    "generator_name",
    ["generate_linear_plan", "generate_quadratic_area", "generate_exponential_change"],
)
def test_independent_namespace_is_distinct_and_public_payload_hides_answer(
    generator_name: str,
) -> None:
    oracles = load_oracles_module()
    generator = getattr(oracles, generator_name)
    guided = generator(701, "guided")
    independent = generator(701, "independent")

    assert guided["variant_id"] != independent["variant_id"]
    assert guided["parameters"] != independent["parameters"]
    public = oracles.public_payload(independent)
    assert "answer_teacher_only" not in public
    assert "hints" not in public
    assert "worked_steps" not in public
    assert public["mode"] == "independent"
    if generator_name == "generate_linear_plan":
        assert "crossover" not in public["parameters"]


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "7", None])
def test_generators_reject_invalid_seed_values(seed: object) -> None:
    oracles = load_oracles_module()

    with pytest.raises((TypeError, ValueError)):
        oracles.generate_linear_plan(seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_generators_reject_invalid_modes(mode: object) -> None:
    oracles = load_oracles_module()

    with pytest.raises(ValueError, match="unsupported mode"):
        oracles.generate_linear_plan(7, mode)
