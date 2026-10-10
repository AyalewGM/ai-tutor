"""DRAFT only: seeded Wave 2 problem contracts. Never import into runtime.

Keep private answer keys server-side. No network, DB, or mastery writes.
"""
from __future__ import annotations

from collections import deque
from fractions import Fraction
from random import Random

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
PACKAGE_IDS = (
    "W2-G1-ADDITION-UNKNOWN",
    "W2-G5-DECIMAL-PLACE-VALUE",
    "W2-G6-RATIO-DOUBLE-LINE",
    "W2-G7-DISTRIBUTIONS-IQR",
    "W2-G8-CUBE-NETS",
    "W2-G9-QUADRATIC-PATTERNS",
)


def _neg(v):
    return tuple(-x for x in v)


def is_cube_net(cells: tuple[tuple[int, int], ...]) -> bool:
    """BFS fold six connected grid squares through right-angle hinges.

    A valid cube net reaches all six distinct outward face normals without
    an inconsistent orientation; repeated normals represent face collisions.
    """
    squares = set(cells)
    if len(squares) != 6:
        return False
    first = min(squares)
    frame = {first: ((0, 0, 1), (1, 0, 0), (0, 1, 0))}
    queue = deque([first])
    while queue:
        x, y = queue.popleft()
        normal, right, up = frame[(x, y)]
        neighbors = {
            (x + 1, y): (right, _neg(normal), up),
            (x - 1, y): (_neg(right), normal, up),
            (x, y + 1): (up, right, _neg(normal)),
            (x, y - 1): (_neg(up), right, normal),
        }
        for cell, next_frame in neighbors.items():
            if cell not in squares:
                continue
            if cell in frame:
                if frame[cell] != next_frame:
                    return False
            else:
                frame[cell] = next_frame
                queue.append(cell)
    return len(frame) == 6 and len({basis[0] for basis in frame.values()}) == 6


def _number(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    if value.denominator == 2:
        return f"{value.numerator // 2}.5"
    return f"{value.numerator}/{value.denominator}"


def _money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def _arithmetic(rng: Random, variant: int):
    a, b = rng.randint(3, 10), rng.randint(2, 9)
    if variant == 0:
        return (f"{a} + □ = {a+b}. What is □?", str(b), {"a": a, "b": b},
                "unknown_addend", "Model known and unknown counters with different textures.")
    if variant == 1:
        return (f"{a+b} − □ = {a}. What is □?", str(b), {"a": a, "b": b},
                "unknown_subtrahend", "Remove counters until the remainder matches.")
    return (f"A basket had □ apples. {b} were taken away; {a} remain. How many at first?",
            str(a+b), {"a": a, "b": b}, "unknown_start_transfer",
            "Rebuild the start from remaining and removed parts.")


def _decimals(rng: Random, variant: int):
    if variant == 0:
        a, b = rng.sample(range(11, 96), 2)
        return (f"Which is greater, {_money(a)} or {_money(b)}?", _money(max(a, b)),
                {"a_cents": a, "b_cents": b}, "decimal_compare",
                "Compare aligned hundred-grid columns.")
    if variant == 1:
        n = rng.randint(1, 19)
        return (f"Express {n}/20 as a decimal to hundredths.", _money(n * 5),
                {"numerator": n, "denominator": 20}, "fraction_to_decimal",
                "Partition each twentieth into five hundredths.")
    whole, cut = rng.randint(2, 5), rng.randint(15, 95)
    return (f"A {whole}.00 m ribbon has {_money(cut)} m cut away. What length remains (m)?",
            _money(whole * 100 - cut), {"initial_cents": whole * 100, "cut_cents": cut},
            "decimal_measure_transfer", "Align hundredths on a place-value grid.")


def _ratios(rng: Random, variant: int):
    if variant == 0:
        n, unit, wanted = rng.randint(2, 7), rng.randint(2, 9), rng.randint(3, 9)
        return (f"{n} tickets cost {n*unit} dollars. What do {wanted} tickets cost?",
                str(wanted * unit), {"n": n, "unit": unit, "wanted": wanted},
                "unit_rate", "Link ticket counts and costs on two number lines.")
    if variant == 1:
        a, b, scale = rng.randint(2, 6), rng.randint(3, 9), rng.randint(2, 5)
        return (f"A mix uses {a} cups juice per {b} cups water. "
                f"For {a*scale} cups juice, how many cups water?",
                str(b * scale), {"a": a, "b": b, "scale": scale},
                "equivalent_ratio", "Scale both aligned lines by the same factor.")
    speed_a = rng.randint(3, 9)
    speed_b = rng.choice([n for n in range(3, 11) if n != speed_a])
    return (f"Runner A covers {2*speed_a} km in 2 h; runner B covers "
            f"{3*speed_b} km in 3 h. Who is faster (A or B)?",
            "A" if speed_a > speed_b else "B",
            {"distance_a": 2*speed_a, "time_a": 2, "distance_b": 3*speed_b, "time_b": 3},
            "rate_comparison_transfer", "Compare distance per hour, not distance alone.")


def _distributions(rng: Random, variant: int):
    if variant == 0:
        values = sorted(rng.sample(range(2, 42), 8))
        q1 = Fraction(values[1] + values[2], 2)
        q3 = Fraction(values[5] + values[6], 2)
        return (f"For sorted data {', '.join(map(str, values))}, find the IQR "
                "using median-of-halves quartiles.", _number(q3 - q1),
                {"values": values}, "raw_data_iqr",
                "Mark medians of the lower and upper four observations.")
    if variant == 1:
        q1 = rng.randint(2, 10)
        q3 = q1 + rng.randint(3, 12)
        median = rng.randint(q1, q3)
        return (f"Five-number summary: 0, {q1}, {median}, {q3}, {q3+3}. Find the IQR.",
                str(q3-q1), {"q1": q1, "median": median, "q3": q3},
                "summary_iqr", "Subtract Q1 from Q3, not minimum from maximum.")
    a, b = rng.sample(range(2, 13), 2)
    return (f"Class A has IQR {a}; class B has IQR {b}. "
            "Which class has the more spread-out middle half (A or B)?",
            "A" if a > b else "B", {"iqr_a": a, "iqr_b": b},
            "compare_distributions_transfer", "Compare middle-half box widths.")


_VALID_NET = ((0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (1, -1))
_INVALID_NET = tuple((x, 0) for x in range(6))


def _cube_nets(rng: Random, variant: int):
    edge = rng.randint(2, 9)
    if variant == 0:
        return (f"A cube has edge {edge} cm. Find surface area (cm²).",
                str(6*edge*edge), {"edge": edge}, "cube_surface_area",
                "Arrange six equal square faces before multiplying.")
    if variant == 1:
        return (f"A cube has surface area {6*edge*edge} cm². Find edge length (cm).",
                str(edge), {"surface_area": 6*edge*edge}, "inverse_surface_area",
                "Divide by six to get one face, then find its side.")
    cells = _VALID_NET if rng.choice([True, False]) else _INVALID_NET
    return ("Can these six unit squares fold to a cube without overlap? "
            f"Coordinates: {list(cells)}. Answer yes or no.",
            "yes" if is_cube_net(cells) else "no",
            {"cells": [list(c) for c in cells]}, "cube_net_transfer",
            "Trace hinge folds and check each cube face is used once.")


def _quadratics(rng: Random, variant: int):
    a, b = sorted(rng.sample(range(2, 10), 2))
    if variant == 0:
        return (f"Factor x²+{a+b}x+{a*b} into two monic binomials.",
                f"(x+{a})(x+{b})", {"a": a, "b": b}, "factor_monic",
                "Find two integers with the stated sum and product.")
    if variant == 1:
        root = rng.randint(2, 12)
        return (f"Solve x²={root*root} over the reals. Give both roots.",
                f"-{root}, {root}", {"square": root*root}, "two_roots",
                "Both positive and negative numbers square to the same value.")
    return (f"A garden has sides x+{a} and x+{b}. Expand its area polynomial.",
            f"x²+{a+b}x+{a*b}", {"a": a, "b": b}, "area_model_transfer",
            "Split the rectangle into four sub-rectangles.")


_GENERATORS = dict(zip(PACKAGE_IDS, (
    _arithmetic, _decimals, _ratios, _distributions, _cube_nets, _quadratics
), strict=True))


def generate_item(package_id: str, seed: int, variant: int, mode: str) -> dict:
    """Variants 0/1 are distinct structures, 2 is contextual transfer.

    Guided and independent RNG domains are separate; neither mode is live.
    """
    if package_id not in _GENERATORS:
        raise ValueError("unknown Wave 2 package")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(variant) is not int or variant not in (0, 1, 2):
        raise ValueError("variant must be 0, 1, or 2")
    if mode not in ("guided", "independent"):
        raise ValueError("mode must be guided or independent")
    rng = Random(f"mihur-wave2-v1:{package_id}:{mode}:{variant}:{seed}")
    prompt, answer, params, kind, visual = _GENERATORS[package_id](rng, variant)
    student = {"prompt": prompt, "response_format": "short_exact", "mode": mode}
    if mode == "guided":
        student["socratic_hints"] = [
            "What is known and what is the unknown quantity?",
            "What representation preserves the quantities and units?",
            visual,
        ]
        student["visual_instruction"] = visual
    return {
        "status": STATUS,
        "runtime_activation": RUNTIME_ACTIVATION,
        "package_id": package_id,
        "item_id": f"{package_id}:{mode}:{variant}:{seed}",
        "student": student,
        "private": {"answer": answer, "parameters": params, "oracle_kind": kind},
        "mastery_writes": False,
    }
