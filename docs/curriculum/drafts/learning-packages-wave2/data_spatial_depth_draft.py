"""DRAFT-only, reproducible histogram and cube-net reasoning; never runtime-import."""
from __future__ import annotations

from collections import deque
from fractions import Fraction
from random import Random

STATUS = "DRAFT_UNVERIFIED"
FAMILIES = ("histogram", "cube_nets")
BINS = ((0, 5), (5, 10), (10, 15), (15, 20), (20, 25))
PROFILES = ((2, 3, 9, 4, 2), (8, 5, 4, 2, 1), (1, 2, 4, 5, 8), (2, 6, 7, 3, 2), (4, 2, 9, 3, 2))


def canonical(cells: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    """Normalize translation, quarter-turns and reflections of a grid shape."""
    if len(cells) != len(set(cells)) or not cells:
        raise ValueError("cells must be distinct and nonempty")
    candidates = []
    for reflect in (1, -1):
        for turn in range(4):
            transformed = []
            for x, y in cells:
                x *= reflect
                for _ in range(turn):
                    x, y = -y, x
                transformed.append((x, y))
            min_x = min(x for x, _ in transformed)
            min_y = min(y for _, y in transformed)
            candidates.append(tuple(sorted((x - min_x, y - min_y) for x, y in transformed)))
    return min(candidates)


def free_hexominoes() -> tuple[tuple[tuple[int, int], ...], ...]:
    """Exhaustively enumerate connected free six-cell polyominoes (35 shapes)."""
    shapes = {((0, 0),)}
    for _ in range(5):
        next_shapes = set()
        for shape in shapes:
            occupied = set(shape)
            for x, y in shape:
                for candidate in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if candidate not in occupied:
                        next_shapes.add(canonical((*shape, candidate)))
        shapes = next_shapes
    return tuple(sorted(shapes))


def foldable(cells: tuple[tuple[int, int], ...]) -> bool:
    """Propagate 3D face frames across hinges; require six unique cube normals."""
    squares = set(cells)
    if len(squares) != 6:
        return False
    start = min(squares)
    frames = {start: ((0, 0, 1), (1, 0, 0), (0, 1, 0))}
    pending = deque([start])

    def neg(v: tuple[int, int, int]) -> tuple[int, int, int]:
        return tuple(-a for a in v)

    while pending:
        x, y = pending.popleft()
        normal, right, up = frames[(x, y)]
        neighbors = (
            ((x + 1, y), (right, neg(normal), up)),
            ((x - 1, y), (neg(right), normal, up)),
            ((x, y + 1), (up, right, neg(normal))),
            ((x, y - 1), (neg(up), right, normal)),
        )
        for cell, frame in neighbors:
            if cell not in squares:
                continue
            if cell in frames and frames[cell] != frame:
                return False
            if cell not in frames:
                frames[cell] = frame
                pending.append(cell)
    return len(frames) == 6 and len({frame[0] for frame in frames.values()}) == 6


SHAPES = free_hexominoes()
VALID = tuple(shape for shape in SHAPES if foldable(shape))
INVALID = tuple(shape for shape in SHAPES if not foldable(shape))


def observations(rng: Random) -> list[int]:
    """Generate a complete 20-observation distribution with a unique modal bin."""
    profile = rng.choice(PROFILES)
    values = [5 * index + rng.randrange(5) for index, count in enumerate(profile) for _ in range(count)]
    rng.shuffle(values)
    return values


def _counts(values: list[int]) -> tuple[int, ...]:
    return tuple(sum(lo <= value < hi for value in values) for lo, hi in BINS)


def _histogram(rng: Random, variant: int):
    data = observations(rng)
    intervals = "0–4, 5–9, 10–14, 15–19, 20–24"
    if variant == 0:
        return (f"Data: {data}. Count observations in each interval ({intervals}) in order.",
                ", ".join(map(str, _counts(data))), {"data": data}, "bin_counts",
                "Place each observation in exactly one left-closed, right-open bin.")
    if variant == 1:
        peak = _counts(data).index(max(_counts(data)))
        return (f"Data: {data}. Which interval has the greatest frequency ({intervals})?",
                intervals.split(", ")[peak], {"data": data}, "modal_interval",
                "Count each interval, then identify the unique tallest bar.")
    other = observations(rng)
    while sum(x >= 15 for x in data) == sum(x >= 15 for x in other):
        other = observations(rng)
    a = sum(x >= 15 for x in data)
    b = sum(x >= 15 for x in other)
    return (f"Class A data: {data}. Class B data: {other}. Which class has more scores "
            "from 15 through 24 inclusive (A or B)?", "A" if a > b else "B",
            {"data_a": data, "data_b": other}, "compare_upper_bins",
            "Combine frequencies of the last two bins for each class.")


def _spatial(rng: Random, variant: int):
    if variant == 2:
        numerator, denominator = rng.randint(1, 9), rng.randint(2, 6)
        edge = Fraction(numerator, denominator)
        return (f"A foldable six-square cube net has edge {edge} cm. "
                "Find total surface area in cm² (exact fraction or integer).",
                str(6 * edge * edge), {"numerator": numerator, "denominator": denominator},
                "net_surface_area", "Count six square faces and square the edge length.")
    valid = rng.choice(VALID)
    invalid = rng.choice(INVALID)
    if variant == 1:
        if rng.choice((True, False)):
            first, second, answer = valid, invalid, "A"
        else:
            first, second, answer = invalid, valid, "B"
        return (f"Net A: {list(first)}. Net B: {list(second)}. "
                "Which six-square shape folds into a cube without face overlap (A or B)?",
                answer, {"a": first, "b": second}, "net_pair",
                "Track six distinct outward face directions as hinges fold.")
    chosen = valid if rng.choice((True, False)) else invalid
    return (f"Can the six squares at {list(chosen)} fold into a cube without overlap (yes or no)?",
            "yes" if foldable(chosen) else "no", {"cells": chosen}, "net_single",
            "Fold one hinge at a time; repeated face directions indicate collision.")


def generate_item(family: str, seed: int, variant: int, mode: str) -> dict:
    """Draft content only. Guided and independent modes have separate seed domains."""
    if family not in FAMILIES:
        raise ValueError("unknown draft family")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(variant) is not int or variant not in (0, 1, 2):
        raise ValueError("variant must be 0, 1 or 2")
    if mode not in ("guided", "independent"):
        raise ValueError("mode must be guided or independent")
    rng = Random(f"mihur-w2-data-spatial-v1:{family}:{mode}:{variant}:{seed}")
    prompt, answer, params, kind, visual = (
        _histogram(rng, variant) if family == "histogram" else _spatial(rng, variant)
    )
    student = {"prompt": prompt, "mode": mode, "response_format": "short_exact"}
    if mode == "guided":
        student["socratic_hints"] = [
            "What is being counted or compared?",
            "Which representation preserves the data, geometry and units?",
            visual,
        ]
        student["visual_instruction"] = visual
    return {
        "status": STATUS,
        "runtime_activation": False,
        "mastery_writes": False,
        "standards_mapping": "PROVISIONAL_NOT_ACCEPTED",
        "item_id": f"w2-depth:{family}:{mode}:{variant}:{seed}",
        "student": student,
        "private": {"answer": answer, "parameters": params, "oracle_kind": kind},
    }
