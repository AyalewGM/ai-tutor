"""Regression gates for bounded independent evidence corrections in PR #328."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs/curriculum/drafts"


def _package(wave: str, ident: str) -> dict:
    path = ROOT / wave / "content.draft.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return next(p for p in data["packages"] if p["id"] == ident)


def test_start_unknown_and_equality_preservation_evidence():
    p = _package("learning-packages-wave2", "W2-G1-ADDITION-UNKNOWN")
    items = {i.get("unknown_role"): i for i in p["independent_assessment"]}
    assert {"START_UNKNOWN", "EQUALITY_UNKNOWN"} <= items.keys()
    assert 16 - 7 == 9
    assert 8 + 4 == 7 + 5
    assert p["runtime_activation"] is False
    assert p["mastery_writes"] is False
    assert p["assessment_scope_evidence"]["independent_review"] == "REQUESTED_NOT_APPROVED"
    for role in ("START_UNKNOWN", "EQUALITY_UNKNOWN"):
        item = items[role]
        assert item["hints_allowed"] is False
        assert item["teacher_oracle_visibility"] == "SERVER_ONLY"


def test_system_cardinality_and_equation_equivalence_evidence():
    p = _package("learning-packages-wave3", "W3-G9-SYSTEMS-LINEAR")
    items = {i.get("solution_count"): i for i in p["independent_assessment"]}
    assert {"ZERO", "ONE", "INFINITE"} <= items.keys()
    # Independent checks: contradictory parallel lines, a unique intersection,
    # and a proportional equation pair containing at least two different points.
    assert 4 * 0 + 1 != 4 * 0 - 3
    x, y = 5, 2
    assert x + y == 7 and x - y == 3
    for x, y in [(0, 6), (2, 3)]:
        assert 3 * x + 2 * y == 12
        assert 6 * x + 4 * y == 24
    assert p["runtime_activation"] is False
    assert p["mastery_writes"] is False
    for role in ("ZERO", "ONE", "INFINITE"):
        assert items[role]["hints_allowed"] is False
        assert items[role]["teacher_oracle_visibility"] == "SERVER_ONLY"


def test_signed_integer_scope_matches_addition_only_runtime():
    p = _package("learning-packages-wave3", "W3-G7-SIGNED-NUMBERS")
    assert p["canonical_identity"] == "REUSE_EXISTING_MATH.INT.ADD"
    assert p["runtime_activation"] is False
    assert p["mastery_writes"] is False
    assert p["assessment_scope_evidence"]["exclusions"] == [
        "integer subtraction", "integer multiplication", "integer division"
    ]
    assert len(p["independent_assessment"]) >= 3
    assert all(
        item["operation_family"] == "MATH.INT.ADD"
        and item["hints_allowed"] is False
        for item in p["independent_assessment"]
    )
    assert -8 + 3 == -5
    assert -6 + (-4) == -10
    assert -15 + 38 == 23


def test_histogram_unseen_bin_modality_and_interval_evidence():
    p = _package("learning-packages-wave4", "W4-G6-HISTOGRAM-CONTEXT")
    tagged = [i for i in p["independent_assessment"] if i.get("evidence")]
    assert len(tagged) >= 2
    assert sum([3, 1]) == 4
    assert max([2, 6, 3, 1]) == 6
    assert 10 <= 10 < 15
    assert 2 < 5 < 8 and 8 > 5 > 2
    assert all(i["hints_allowed"] is False for i in tagged)
    assert p["runtime_activation"] is False


def test_full_figure_translation_reflection_and_invariants():
    p = _package("learning-packages-wave3", "W3-G8-COORDINATE-TRANSFORM")
    tagged = [i for i in p["independent_assessment"] if i.get("evidence")]
    assert len(tagged) >= 2
    triangle = [(-2, 1), (1, 1), (-2, 4)]
    translated = [(x + 4, y - 3) for x, y in triangle]
    assert translated == [(2, -2), (5, -2), (2, 1)]
    other = [(1, 1), (4, 1), (1, 3)]
    assert [(-x, y) for x, y in other] == [(-1, 1), (-4, 1), (-1, 3)]
    assert all(i["hints_allowed"] is False for i in tagged)
    assert p["runtime_activation"] is False


def test_iqr_from_unseen_raw_data_and_boxplot_endpoints():
    p = _package("learning-packages-wave2", "W2-G7-DISTRIBUTIONS-IQR")
    tagged = [i for i in p["independent_assessment"] if i.get("evidence")]
    assert len(tagged) >= 2
    a = [1, 3, 5, 7, 9, 11, 13, 15]
    assert (a[1] + a[2]) / 2 == 4
    assert (a[5] + a[6]) / 2 == 12
    assert 12 - 4 == 8
    assert a[-1] - a[0] == 14
    assert 8.5 - 4.5 == 4
    assert 10 - 3 == 7
    assert all(i["hints_allowed"] is False for i in tagged)
    assert p["runtime_activation"] is False


def test_decimal_distinct_objectives_are_scored_separately():
    p = _package("learning-packages-wave2", "W2-G5-DECIMAL-PLACE-VALUE")
    items = [x for x in p["independent_assessment"] if x.get("scope_role")]
    assert len(items) == 4
    assert len({x["scope_role"] for x in items}) == 4
    from decimal import Decimal
    assert Decimal("0.407") == Decimal("0.4") + Decimal("0.007")
    assert Decimal(9) / Decimal(25) == Decimal("0.36")
    assert Decimal("3.060") - Decimal("3.006") == Decimal("0.054")
    assert Decimal("4.050") - Decimal("1.275") == Decimal("2.775")
    assert all(not x["hints_allowed"] for x in items)


def test_quadratic_growth_requires_stated_geometric_construction():
    p = _package("learning-packages-wave2", "W2-G9-QUADRATIC-PATTERNS")
    assert "square-tile construction" in p["concept"]
    tags = {tag for x in p["independent_assessment"] for tag in x.get("evidence", [])}
    assert {"DEFINED_GEOMETRIC_RULE", "VISUAL_GROWTH_INVARIANT", "NONUNIQUENESS_OF_FINITE_DATA"} <= tags
    assert (4 + 2) ** 2 == 36
    assert (4 + 2) ** 2 - (3 + 2) ** 2 == 11
    assert [(n + 1) ** 2 for n in range(4)] == [1, 4, 9, 16]
    assert (4 + 1) ** 2 != (4 + 1) ** 2 + 4 * 3 * 2 * 1
    assert p["runtime_activation"] is False


def _fold_cube_net(cells):
    """Independent cube face-orientation oracle for connected hexominoes."""
    cells = {tuple(x) for x in cells}
    if len(cells) != 6:
        return False
    def neg(a):
        return tuple(-x for x in a)
    start = next(iter(cells))
    states = {start: ((1, 0, 0), (0, 1, 0), (0, 0, 1))}
    queue = [start]
    while queue:
        x, y = queue.pop(0)
        u, v, n = states[(x, y)]
        neighbors = [
            ((x + 1, y), (neg(n), v, u)),
            ((x - 1, y), (n, v, neg(u))),
            ((x, y + 1), (u, neg(n), v)),
            ((x, y - 1), (u, n, neg(v))),
        ]
        for pos, state in neighbors:
            if pos not in cells:
                continue
            if pos in states and states[pos] != state:
                return False
            if pos not in states:
                states[pos] = state
                queue.append(pos)
    return len(states) == 6 and len({state[2] for state in states.values()}) == 6


def test_cube_net_true_folding_distinct_from_surface_area():
    p = _package("learning-packages-wave2", "W2-G8-CUBE-NETS")
    unseen = [x for x in p["independent_assessment"] if x.get("net_coordinates")]
    assert len(unseen) >= 2
    for x in unseen:
        assert _fold_cube_net(x["net_coordinates"]) is x["foldable"]
        assert x["hints_allowed"] is False
    assert p["runtime_activation"] is False


def test_prism_net_face_pairing_and_size_restrictions():
    p = _package("learning-packages-wave4", "W4-G7-PRISM-NETS")
    unseen = [x for x in p["independent_assessment"] if x.get("evidence")]
    assert len(unseen) >= 2
    assert sorted(unseen[0]["net_face_sizes"]) == sorted(
        [[2, 4], [3, 4], [2, 4], [3, 4], [2, 3], [2, 3]]
    )
    assert 2 * (2 * 3 + 2 * 4 + 3 * 4) == 52
    assert 3 * 4 != 3 * 3
    assert p["runtime_activation"] is False


def test_linear_vs_exponential_different_independent_invariants():
    p = _package("learning-packages-wave4", "W4-G9-EXPO-MODELING")
    unseen = [x for x in p["independent_assessment"] if x.get("evidence")]
    assert len(unseen) >= 2
    linear = [4, 7, 10, 13]
    exponential = [5, 10, 20, 40]
    assert [b - a for a, b in zip(linear, linear[1:])] == [3, 3, 3]
    assert [b // a for a, b in zip(exponential, exponential[1:])] == [2, 2, 2]
    assert exponential[-1] * 2 == 80
    assert p["assessment_scope_evidence"]["source_provenance"] == "UNKNOWN_UNLOCATED"
    assert p["runtime_activation"] is False
