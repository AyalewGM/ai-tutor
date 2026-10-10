"""Independent draft-only tests: exhaustive cube nets and exact histogram counts."""
from __future__ import annotations

import importlib.util
import json
from collections import deque
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs/curriculum/drafts/learning-packages-wave2/data_spatial_depth_draft.py"
SPEC = importlib.util.spec_from_file_location("w2_data_spatial_draft", PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def independent_oracle(kind: str, params: dict) -> str:
    """Compute answers from raw data or mathematical invariants, not answer strings."""
    if kind in {"bin_counts", "modal_interval", "compare_upper_bins"}:
        if kind == "compare_upper_bins":
            a = sum(15 <= value <= 24 for value in params["data_a"])
            b = sum(15 <= value <= 24 for value in params["data_b"])
            assert a != b
            return "A" if a > b else "B"
        values = params["data"]
        assert len(values) == 20 and all(0 <= x < 25 for x in values)
        frequencies = [sum(5 * i <= x < 5 * i + 5 for x in values) for i in range(5)]
        assert sum(frequencies) == len(values)
        if kind == "bin_counts":
            return ", ".join(map(str, frequencies))
        assert frequencies.count(max(frequencies)) == 1
        peak = frequencies.index(max(frequencies))
        return f"{5 * peak}–{5 * peak + 4}"
    if kind == "net_surface_area":
        edge = Fraction(params["numerator"], params["denominator"])
        return str(sum((edge * edge for _ in range(6)), Fraction(0)))
    if kind == "net_single":
        return "yes" if mod.foldable(tuple(map(tuple, params["cells"]))) else "no"
    if kind == "net_pair":
        a = mod.foldable(tuple(map(tuple, params["a"])))
        b = mod.foldable(tuple(map(tuple, params["b"])))
        assert a != b
        return "A" if a else "B"
    raise AssertionError(kind)


def test_exhaustive_six_square_net_classification():
    # Established combinatorial benchmarks: 35 free hexominoes, 11 cube nets.
    assert len(mod.SHAPES) == 35
    assert len(mod.VALID) == 11
    assert len(mod.INVALID) == 24
    assert len(set(mod.SHAPES)) == 35
    for shape in mod.SHAPES:
        assert len(shape) == 6
        visited = {shape[0]}
        todo = deque([shape[0]])
        while todo:
            x, y = todo.popleft()
            for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if p in shape and p not in visited:
                    visited.add(p)
                    todo.append(p)
        assert len(visited) == 6
        assert mod.canonical(shape) == shape
        for transform in (
            lambda x, y: (x + 11, y - 7),
            lambda x, y: (-y, x),
            lambda x, y: (-x, y),
            lambda x, y: (y, -x),
        ):
            moved = tuple(transform(x, y) for x, y in shape)
            assert mod.canonical(moved) == shape
            assert mod.foldable(moved) == mod.foldable(shape)


@pytest.mark.parametrize("family", mod.FAMILIES)
@pytest.mark.parametrize("variant", (0, 1, 2))
def test_seeded_draft_oracles_and_isolation(family: str, variant: int):
    for seed in range(40):
        for mode in ("guided", "independent"):
            item = mod.generate_item(family, seed, variant, mode)
            assert item == mod.generate_item(family, seed, variant, mode)
            assert item["status"] == "DRAFT_UNVERIFIED"
            assert item["runtime_activation"] is False
            assert item["mastery_writes"] is False
            assert item["standards_mapping"] == "PROVISIONAL_NOT_ACCEPTED"
            public, private = item["student"], item["private"]
            assert private["answer"] == independent_oracle(private["oracle_kind"], private["parameters"])
            assert not ({"answer", "parameters", "oracle_kind"} & set(public))
            assert "private" not in json.dumps(public)
            if mode == "guided":
                assert len(public["socratic_hints"]) == 3
                assert public["visual_instruction"]
            else:
                assert "socratic_hints" not in public
                assert "visual_instruction" not in public


@pytest.mark.parametrize("bad", [
    ("bad", 0, 0, "guided"), ("histogram", -1, 0, "guided"),
    ("histogram", True, 0, "guided"), ("cube_nets", 0, 3, "guided"),
    ("cube_nets", 0, False, "guided"), ("cube_nets", 0, 0, "other"),
])
def test_invalid_inputs_fail_closed(bad):
    with pytest.raises(ValueError):
        mod.generate_item(*bad)
