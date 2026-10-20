import importlib.util
import json
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
DRAFT = ROOT / "docs" / "curriculum" / "drafts" / "algebra_depth_provenance_20261010"


def load_module():
    path = DRAFT / "quadratic_depth_r5.py"
    spec = importlib.util.spec_from_file_location("quadratic_depth_r5", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def as_fraction(value: str | int) -> Fraction:
    return Fraction(str(value))


@pytest.mark.parametrize("family_index", range(7))
@pytest.mark.parametrize("mode", ["diagnostic", "guided", "independent", "mastery"])
@pytest.mark.parametrize("seed", range(40))
def test_every_family_replays_idempotently_without_oracle_leakage(
    family_index: int, mode: str, seed: int
) -> None:
    depth = load_module()
    family = depth.FAMILY_ORDER[family_index]
    first = depth.generate(family, seed, mode)
    second = depth.generate(family, seed, mode)

    assert first == second
    assert first["canonical_approval"] == "UNKNOWN_NOT_AUTHORITATIVE"
    assert first["mode"] == mode
    assert first["oracle_teacher_only"]
    assert first["misconceptions_teacher_only"]
    public = depth.public_payload(first)
    assert "oracle_teacher_only" not in public
    assert "misconceptions_teacher_only" not in public
    assert "guided_support" not in public
    assert "answer" not in json.dumps(public).lower()


@pytest.mark.parametrize("family_index", range(7))
@pytest.mark.parametrize("seed", range(80))
def test_guided_question_selects_one_misconception_without_answer_leakage(
    family_index: int, seed: int
) -> None:
    depth = load_module()
    record = depth.generate(depth.FAMILY_ORDER[family_index], seed, "guided")

    for code, evidence in record["misconceptions_teacher_only"].items():
        support = depth.guided_misconception_question(record, code)
        encoded = json.dumps(support, sort_keys=True).lower()

        assert support["mode"] == "guided"
        assert support["family"] == record["family"]
        assert support["misconception_code"] == code
        assert support["socratic_question"] == evidence["socratic_probe"]
        assert support["return_to_response_schema"] == record["response_schema"]
        assert support["next_action"] == "REVISE_AND_RESUBMIT_WITHOUT_ORACLE_DISCLOSURE"
        assert "submitted" not in encoded
        assert "oracle_teacher_only" not in encoded


@pytest.mark.parametrize("mode", ["diagnostic", "independent", "mastery"])
def test_guided_question_fails_closed_outside_guided_mode(mode: str) -> None:
    depth = load_module()
    record = depth.generate(depth.FACTORED_ROOTS, 17, mode)

    with pytest.raises(ValueError, match="require guided mode"):
        depth.guided_misconception_question(record, "QUAD.ROOT_SIGN")


def test_guided_question_rejects_unknown_or_malformed_classification() -> None:
    depth = load_module()
    record = depth.generate(depth.FACTORED_ROOTS, 17, "guided")

    with pytest.raises(ValueError, match="unsupported misconception code"):
        depth.guided_misconception_question(record, "QUAD.UNKNOWN")
    with pytest.raises(TypeError, match="nonempty string"):
        depth.guided_misconception_question(record, "")
    with pytest.raises(TypeError, match="record must be a dictionary"):
        depth.guided_misconception_question(None, "QUAD.ROOT_SIGN")
    malformed = dict(record)
    malformed.pop("misconceptions_teacher_only")
    with pytest.raises(TypeError, match="missing misconception evidence"):
        depth.guided_misconception_question(malformed, "QUAD.ROOT_SIGN")


@pytest.mark.parametrize("seed", range(120))
def test_standard_substitution_oracle_is_independently_reconstructed(seed: int) -> None:
    depth = load_module()
    record = depth.generate(depth.STANDARD_SUBSTITUTION, seed, "independent")
    p = record["public_data"]
    x = as_fraction(p["x"])
    expected = p["a"] * x * x + p["b"] * x + p["c"]
    oracle = record["oracle_teacher_only"]

    assert as_fraction(oracle["squared_input"]) == x * x
    assert as_fraction(oracle["exact_value"]) == expected
    assert as_fraction(oracle["substitution_check"]) == expected


@pytest.mark.parametrize("seed", range(120))
def test_factored_roots_have_two_zero_substitution_totals(seed: int) -> None:
    depth = load_module()
    record = depth.generate(depth.FACTORED_ROOTS, seed, "independent")
    p = record["public_data"]
    oracle = record["oracle_teacher_only"]
    roots = oracle["ordered_roots"]

    assert roots == sorted([p["r1_factor_parameter"], p["r2_factor_parameter"]])
    assert roots[0] != roots[1]
    assert [p["a"] * (x - roots[0]) * (x - roots[1]) for x in roots] == [0, 0]
    assert oracle["left_total_at_first"] == oracle["left_total_at_second"] == 0


@pytest.mark.parametrize("seed", range(120))
def test_vertex_symmetry_and_opening_are_exact(seed: int) -> None:
    depth = load_module()
    record = depth.generate(depth.VERTEX_SYMMETRY, seed, "independent")
    p = record["public_data"]
    oracle = record["oracle_teacher_only"]
    left_x, right_x = p["h"] - p["distance"], p["h"] + p["distance"]
    left = p["a"] * (left_x - p["h"]) ** 2 + p["k"]
    right = p["a"] * (right_x - p["h"]) ** 2 + p["k"]

    assert oracle["vertex"] == [p["h"], p["k"]]
    assert oracle["axis"] == f"x={p['h']}"
    assert oracle["opening"] == ("up" if p["a"] > 0 else "down")
    assert left == oracle["left_value"] == oracle["right_value"] == right


@pytest.mark.parametrize("seed", range(120))
def test_square_root_branch_oracle_keeps_both_solutions(seed: int) -> None:
    depth = load_module()
    record = depth.generate(depth.SQUARE_ROOT_BRANCHES, seed, "independent")
    p = record["public_data"]
    oracle = record["oracle_teacher_only"]
    roots = oracle["ordered_real_solutions"]

    assert len(roots) == 2 and roots[0] != roots[1]
    assert [p["a"] * (x - p["h"]) ** 2 for x in roots] == [
        p["right_total"],
        p["right_total"],
    ]
    lost = record["misconceptions_teacher_only"]["QUAD.LOST_PLUS_MINUS"]["submitted"]
    assert len(lost["ordered_real_solutions"]) == 1


@pytest.mark.parametrize("seed", range(120))
def test_no_real_classification_uses_true_vertex_minimum(seed: int) -> None:
    depth = load_module()
    record = depth.generate(depth.NO_REAL_VERTEX, seed, "independent")
    p = record["public_data"]
    oracle = record["oracle_teacher_only"]

    assert p["a"] > 0 and p["k"] > 0
    assert oracle["classification"] == "no real solutions"
    assert oracle["minimum_left_value"] == p["k"]
    for offset in range(-20, 21):
        assert p["a"] * offset**2 + p["k"] >= p["k"] > 0


@pytest.mark.parametrize("seed", range(120))
def test_table_rule_reconstruction_uses_second_difference_equal_two_a(seed: int) -> None:
    depth = load_module()
    record = depth.generate(depth.TABLE_TO_RULE, seed, "independent")
    p = record["public_data"]
    oracle = record["oracle_teacher_only"]
    a, b, c = oracle["coefficients"]
    ys = [a * x**2 + b * x + c for x in p["x_values"]]
    first = [ys[i + 1] - ys[i] for i in range(3)]
    second = [first[i + 1] - first[i] for i in range(2)]

    assert ys == p["y_values"]
    assert first == oracle["first_differences"]
    assert second == oracle["second_differences"] == [2 * a, 2 * a]
    assert oracle["value_at_3"] == a * 9 + b * 3 + c


@pytest.mark.parametrize("seed", range(120))
def test_three_forms_reconcile_features_and_zero_input_total(seed: int) -> None:
    depth = load_module()
    record = depth.generate(depth.FORM_RECONCILIATION, seed, "independent")
    p = record["public_data"]
    oracle = record["oracle_teacher_only"]
    a, b, c = oracle["standard_coefficients"]
    h, k = oracle["vertex"]

    assert [a, b, c] == [p["a"], -p["a"] * (p["r1"] + p["r2"]), p["a"] * p["r1"] * p["r2"]]
    assert oracle["roots"] == sorted([p["r1"], p["r2"]])
    assert a * h**2 + b * h + c == k
    assert [c, p["a"] * (0 - p["r1"]) * (0 - p["r2"]), p["a"] * (0 - h) ** 2 + k] == oracle["three_totals_at_zero"]


@pytest.mark.parametrize("family_index", range(7))
@pytest.mark.parametrize("mode", ["diagnostic", "guided", "independent", "mastery"])
@pytest.mark.parametrize("seed", range(160))
def test_misconception_submissions_never_equal_exact_oracle(
    family_index: int, mode: str, seed: int
) -> None:
    depth = load_module()
    record = depth.generate(depth.FAMILY_ORDER[family_index], seed, mode)
    oracle = record["oracle_teacher_only"]

    for misconception in record["misconceptions_teacher_only"].values():
        assert misconception["submitted"] != oracle
        assert misconception["socratic_probe"].endswith("?")


@pytest.mark.parametrize("family_index", range(7))
@pytest.mark.parametrize("source_mode", ["diagnostic", "guided", "independent", "mastery"])
@pytest.mark.parametrize("seed", range(80))
def test_transfer_is_deterministic_changes_structure_and_exits_independent(
    family_index: int, source_mode: str, seed: int
) -> None:
    depth = load_module()
    source = depth.FAMILY_ORDER[family_index]
    first = depth.generate_fresh_transfer(source, seed, source_mode, "independent")
    second = depth.generate_fresh_transfer(source, seed, source_mode, "independent")

    assert first == second
    assert first["family"] != source
    assert first["mode"] == "independent"
    assert first["transfer_from_family"] == source
    assert first["transfer_source_mode"] == source_mode
    assert first["transfer_target_mode"] == "independent"
    assert first["transfer_contract"] == "DIFFERENT_MATHEMATICAL_STRUCTURE_SAME_CANDIDATE_SKILL"
    assert first["verification_contract"] == "INDEPENDENT_HINT_FREE_EXIT"
    public = depth.public_payload(first)
    assert "oracle_teacher_only" not in public
    assert "misconceptions_teacher_only" not in public


@pytest.mark.parametrize("target_mode", ["diagnostic", "guided", "mastery"])
def test_transfer_rejects_non_independent_verification_exit(target_mode: str) -> None:
    depth = load_module()

    with pytest.raises(ValueError, match="must use independent mode"):
        depth.generate_fresh_transfer(
            depth.VERTEX_SYMMETRY,
            31,
            "guided",
            target_mode,
        )


def test_modes_use_distinct_variant_namespaces_and_parameters() -> None:
    depth = load_module()
    for family in depth.FAMILY_ORDER:
        records = [depth.generate(family, 91, mode) for mode in sorted(depth.MODES)]
        assert len({record["variant_id"] for record in records}) == len(depth.MODES)
        assert len({json.dumps(record["public_data"], sort_keys=True) for record in records}) > 1


@pytest.mark.parametrize("seed", [-1, True, False, 1.5, "7", None])
def test_invalid_seed_values_fail_closed(seed: object) -> None:
    depth = load_module()
    with pytest.raises((TypeError, ValueError)):
        depth.generate(depth.FACTORED_ROOTS, seed, "guided")


@pytest.mark.parametrize("mode", ["", "assessment", "GUIDED", None, []])
def test_invalid_modes_fail_closed(mode: object) -> None:
    depth = load_module()
    with pytest.raises((TypeError, ValueError)):
        depth.generate(depth.FACTORED_ROOTS, 7, mode)


def test_manifest_and_module_remain_runtime_disabled_and_persistence_free() -> None:
    manifest = json.loads((DRAFT / "quadratic_depth_r5.package.json").read_text())
    source = (DRAFT / "quadratic_depth_r5.py").read_text()

    assert manifest["status"] == "DRAFT_UNVERIFIED"
    assert manifest["runtime_activation"] is False
    assert manifest["mastery_writes"] is False
    assert manifest["learner_data_writes"] is False
    assert manifest["canonical"]["approval"] == "UNKNOWN_NOT_AUTHORITATIVE"
    assert manifest["independent_evidence"]["math_review"] == "PENDING"
    assert manifest["independent_evidence"]["pedagogical_review"] == "PENDING"
    assert "from app" not in source
    assert "import app" not in source
    assert "Session" not in source
    assert "Attempt" not in source
    assert "MasteryEvent" not in source
