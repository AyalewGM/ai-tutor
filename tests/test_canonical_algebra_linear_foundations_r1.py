"""Focused author tests for the runtime-disabled Algebra I depth package."""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from fractions import Fraction
from itertools import pairwise
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "docs/curriculum/drafts/canonical-algebra-linear-foundations-r1"
MANIFEST = json.loads((PACKAGE_DIR / "package.json").read_text(encoding="utf-8"))
SPEC = importlib.util.spec_from_file_location("canonical_algebra_linear_r1", PACKAGE_DIR / "generator.py")
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def test_package_is_shared_draft_only_and_mapping_fails_closed() -> None:
    assert MANIFEST["status"] == "DRAFT_UNVERIFIED"
    assert MANIFEST["runtime_activation"] is False
    assert MANIFEST["mastery_writes"] is False
    assert MANIFEST["canonical_contract"]["mapping_approval"] == "UNKNOWN"
    assert MANIFEST["canonical_contract"]["jurisdiction_mapping"] == "PROVISIONAL_NOT_ACTIVATED"
    assert not any(token in code for code in MANIFEST["canonical_contract"]["families"]
                   for token in ("ONTARIO", "MARYLAND", "DC", "VIRGINIA", "MTH1W"))
    assert MANIFEST["learning_sequence"] == [
        "OBSERVE", "PREDICT", "MANIPULATE", "EXPLAIN",
        "PRACTICE", "DIAGNOSE", "TRANSFER", "VERIFY",
    ]
    assert all(value is False for value in MANIFEST["data_safety"].values())


def test_generator_is_pure_and_cannot_touch_history_or_runtime() -> None:
    source = (PACKAGE_DIR / "generator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not imports & {"sqlalchemy", "app.models", "app.core.database"}
    for forbidden in ("SessionLocal", "Attempt(", "DiagnosticAttempt(", "MasteryEvent(", "db.add"):
        assert forbidden not in source


@pytest.mark.parametrize("family", sorted(GEN.BUILDERS))
@pytest.mark.parametrize("mode", GEN.MODES)
def test_deterministic_variety_and_learner_safe_payload(family: str, mode: str) -> None:
    items = [GEN.generate(family, seed, mode) for seed in range(24)]
    assert items == [GEN.generate(family, seed, mode) for seed in range(24)]
    assert len({item.variant_id for item in items}) == 24
    assert len({item.prompt for item in items}) >= 6
    for item in items:
        public = item.public_payload()
        assert public["mastery_credit"] is False
        assert not {"oracle", "canonical_answer", "misconception_answers", "socratic_prompts", "seed"} & public.keys()
        assert item.guided_support() == (() if mode == "independent" else item.socratic_prompts)
        assert len(item.socratic_prompts) == 3
        assert item.misconception_answers


def test_expression_oracles_are_exact_and_distribution_path_is_specific() -> None:
    for seed in range(80):
        item = GEN.generate("MATH.ALG.EXPR.EVALUATE", seed, "guided")
        o = item.oracle
        x = Fraction(o["x"])
        expected = o["a"] * (x + o["b"]) - o["c"] * (x - o["d"])
        assert Fraction(item.canonical_answer) == expected == Fraction(o["value"])

        error = GEN.generate("MATH.ALG.EXPR.ERROR.DISTRIBUTE", seed, "guided")
        assert error.canonical_answer.startswith("SIGN_NOT_DISTRIBUTED_TO_CONSTANT|")
        for code, wrong in error.misconception_answers.items():
            assert error.diagnose(wrong) == code
            assert wrong != error.canonical_answer


@pytest.mark.parametrize("family", ["MATH.EQ.ONE.ADD_DIRECT", "MATH.ALG.EQ.ONE.MULT"])
def test_equation_oracles_show_both_sides_and_exact_substitution(family: str) -> None:
    for mode in GEN.MODES:
        for seed in range(120):
            item = GEN.generate(family, seed, mode)
            o = item.oracle
            solution = Fraction(o["solution"])
            assert Fraction(o["left_after_inverse"]) == solution
            assert Fraction(o["right_after_inverse"]) == solution
            if family == "MATH.EQ.ONE.ADD_DIRECT":
                assert Fraction(o["substitution_total"]) == solution + Fraction(
                    item.prompt.split("x + (")[1].split(")")[0]
                )
            else:
                assert Fraction(o["substitution_total"]) == Fraction(o["coefficient"]) * solution
            assert item.canonical_answer == f"x={o['solution']}"
            assert all(item.diagnose(answer) == code for code, answer in item.misconception_answers.items())


def test_slope_and_model_oracles_use_exact_coordinate_changes() -> None:
    for seed in range(120):
        table = GEN.generate("MATH.FUNC.LINEAR.SLOPE.TABLE", seed, "independent")
        o = table.oracle
        assert Fraction(o["slope"]) == Fraction(o["delta_y"]) / Fraction(o["delta_x"])
        points = [(Fraction(x), Fraction(y)) for x, y in o["points"]]
        assert all((y2 - y1) / (x2 - x1) == Fraction(o["slope"])
                   for (x1, y1), (x2, y2) in pairwise(points))

        model = GEN.generate("MATH.FUNC.LINEAR.MODEL", seed, "independent")
        m = Fraction(model.oracle["slope"])
        b = Fraction(model.oracle["intercept"])
        for (x, y), total in zip(model.oracle["points"], model.oracle["substitution_totals"], strict=True):
            assert m * Fraction(x) + b == Fraction(y) == Fraction(total)


def test_transfer_is_deterministic_unseen_and_changes_mathematical_structure() -> None:
    for family in GEN.BUILDERS:
        for seed in range(40):
            taught = GEN.generate(family, seed, "guided")
            one = GEN.fresh_transfer(taught, seed)
            two = GEN.fresh_transfer(taught, seed)
            assert one == two
            assert one.mode == "independent"
            assert one.canonical_skill_code == taught.canonical_skill_code
            assert one.family_code != taught.family_code
            assert one.structure_code != taught.structure_code
            assert one.variant_id != taught.variant_id
            assert one.guided_support() == ()


def test_two_pass_synthetic_materialization_is_byte_stable_and_duplicate_free() -> None:
    first = GEN.materialize_manifest(range(12))
    second = GEN.materialize_manifest(range(12))
    assert first == second
    rows = json.loads(first)
    assert len(rows) == len(GEN.BUILDERS) * len(GEN.MODES) * 12
    assert len({row["variant_id"] for row in rows}) == len(rows)
    assert len({(row["family_code"], row["mode"], row["prompt"], row["canonical_answer"]) for row in rows}) == len(rows)


def test_guided_and_independent_namespaces_never_collide() -> None:
    for family in GEN.BUILDERS:
        for seed in range(100):
            guided = GEN.generate(family, seed, "guided")
            independent = GEN.generate(family, seed, "independent")
            assert guided.variant_id != independent.variant_id


def test_misconception_answers_never_collide_with_exact_oracle() -> None:
    def normalize(value: str) -> str:
        return "".join(value.lower().split()).replace("−", "-")

    for family in GEN.BUILDERS:
        for mode in GEN.MODES:
            for seed in range(500):
                item = GEN.generate(family, seed, mode)
                assert all(
                    normalize(answer) != normalize(item.canonical_answer)
                    for answer in item.misconception_answers.values()
                )


def test_unknown_family_and_mode_fail_closed() -> None:
    with pytest.raises(ValueError):
        GEN.generate("MATH.UNKNOWN", 0, "guided")
    with pytest.raises(ValueError):
        GEN.generate("MATH.ALG.EXPR.EVALUATE", 0, "mastery")
