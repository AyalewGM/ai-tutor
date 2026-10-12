"""Independent draft-only oracle, deterministic replay and assessment isolation."""
from __future__ import annotations

import importlib.util
import json
from fractions import Fraction
from math import isqrt
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs/curriculum/drafts/learning-packages-wave2/seeded_variants.py"
SPEC = importlib.util.spec_from_file_location("wave2_draft_variants", PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def oracle(kind: str, p: dict) -> str:
    """Recompute each answer independently from its parameter contract."""
    if kind in {"unknown_addend", "unknown_subtrahend"}:
        return str(p["b"])
    if kind == "unknown_start_transfer":
        return str(p["a"] + p["b"])
    if kind == "decimal_compare":
        return money(max(p["a_cents"], p["b_cents"]))
    if kind == "fraction_to_decimal":
        value = Fraction(p["numerator"], p["denominator"]) * 100
        assert value.denominator == 1
        return money(int(value))
    if kind == "decimal_measure_transfer":
        return money(p["initial_cents"] - p["cut_cents"])
    if kind == "unit_rate":
        return str(p["wanted"] * Fraction(p["n"] * p["unit"], p["n"]))
    if kind == "equivalent_ratio":
        return str(Fraction(p["b"], p["a"]) * p["a"] * p["scale"])
    if kind == "rate_comparison_transfer":
        a = Fraction(p["distance_a"], p["time_a"])
        b = Fraction(p["distance_b"], p["time_b"])
        assert a != b
        return "A" if a > b else "B"
    if kind == "raw_data_iqr":
        v = sorted(p["values"])
        assert len(v) == 8
        iqr = Fraction(v[5] + v[6] - v[1] - v[2], 2)
        return str(iqr.numerator) if iqr.denominator == 1 else f"{iqr.numerator // 2}.5"
    if kind == "summary_iqr":
        assert p["q1"] <= p["median"] <= p["q3"]
        return str(p["q3"] - p["q1"])
    if kind == "compare_distributions_transfer":
        assert p["iqr_a"] != p["iqr_b"]
        return "A" if p["iqr_a"] > p["iqr_b"] else "B"
    if kind == "cube_surface_area":
        return str(6 * p["edge"] ** 2)
    if kind == "inverse_surface_area":
        r = isqrt(p["surface_area"] // 6)
        assert 6 * r * r == p["surface_area"]
        return str(r)
    if kind == "cube_net_transfer":
        cells = {tuple(v) for v in p["cells"]}
        if cells == {(x, 0) for x in range(6)}:
            return "no"
        assert cells == {(0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (1, -1)}
        return "yes"
    if kind == "factor_monic":
        a, b = sorted((p["a"], p["b"]))
        return f"(x+{a})(x+{b})"
    if kind == "two_roots":
        r = isqrt(p["square"])
        assert r > 0 and r * r == p["square"]
        return f"-{r}, {r}"
    if kind == "area_model_transfer":
        return f"x²+{p['a'] + p['b']}x+{p['a'] * p['b']}"
    raise AssertionError(f"unknown oracle {kind}")


def test_draft_manifest_gate():
    path = ROOT / "docs/curriculum/drafts/learning-packages-wave2/content.draft.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "DRAFT_UNVERIFIED"
    assert data["runtime_activation"] is False
    assert data["mastery_writes"] is False
    assert {p["id"] for p in data["packages"]} == set(mod.PACKAGE_IDS)


@pytest.mark.parametrize("package_id", mod.PACKAGE_IDS)
@pytest.mark.parametrize("variant", [0, 1, 2])
def test_seeded_oracles_and_assessment_isolation(package_id, variant):
    prompts = set()
    for seed in (0, 1, 2, 17, 42, 123, 999, 2026):
        for mode in ("guided", "independent"):
            item = mod.generate_item(package_id, seed, variant, mode)
            assert item == mod.generate_item(package_id, seed, variant, mode)
            assert item["status"] == "DRAFT_UNVERIFIED"
            assert item["runtime_activation"] is False
            assert item["mastery_writes"] is False
            public, private = item["student"], item["private"]
            assert private["answer"] == oracle(private["oracle_kind"], private["parameters"])
            assert not ({"answer", "parameters", "oracle_kind"} & set(public))
            assert "parameters" not in json.dumps(public)
            if mode == "guided":
                assert len(public["socratic_hints"]) == 3
                assert public["visual_instruction"]
            else:
                assert "socratic_hints" not in public
                assert "visual_instruction" not in public
            prompts.add(public["prompt"])
    assert len(prompts) >= 2


def test_cube_net_geometric_invariants():
    valid = ((0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (1, -1))
    invalid = tuple((x, 0) for x in range(6))
    assert mod.is_cube_net(valid)
    assert not mod.is_cube_net(invalid)
    assert not mod.is_cube_net(((0, 0),) * 6)
    assert not mod.is_cube_net(((0, 0), (1, 0), (2, 0), (3, 0), (9, 0), (9, 1)))
    assert not mod.is_cube_net(((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)))
    for transform in (
        lambda x, y: (x + 7, y - 9),
        lambda x, y: (-y, x),
        lambda x, y: (-x, y),
        lambda x, y: (y, x),
    ):
        assert mod.is_cube_net(tuple(transform(*p) for p in valid))
        assert not mod.is_cube_net(tuple(transform(*p) for p in invalid))


@pytest.mark.parametrize("kwargs", [
    {"package_id": "bad", "seed": 0, "variant": 0, "mode": "guided"},
    {"package_id": mod.PACKAGE_IDS[0], "seed": -1, "variant": 0, "mode": "guided"},
    {"package_id": mod.PACKAGE_IDS[0], "seed": True, "variant": 0, "mode": "guided"},
    {"package_id": mod.PACKAGE_IDS[0], "seed": 0, "variant": 3, "mode": "guided"},
    {"package_id": mod.PACKAGE_IDS[0], "seed": 0, "variant": 0, "mode": "bad"},
])
def test_invalid_input_rejected(kwargs):
    with pytest.raises(ValueError):
        mod.generate_item(**kwargs)
