"""DRAFT-only, reproducible histogram and cube-net reasoning; never runtime-import."""
from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from fractions import Fraction
from random import Random
from typing import Final, NamedTuple

STATUS = "DRAFT_UNVERIFIED"
FAMILIES = ("histogram", "cube_nets")
BINS = ((0, 5), (5, 10), (10, 15), (15, 20), (20, 25))
PROFILES = ((2, 3, 9, 4, 2), (8, 5, 4, 2, 1), (1, 2, 4, 5, 8), (2, 6, 7, 3, 2), (4, 2, 9, 3, 2))
CUBE_NET_EVIDENCE_NAMESPACE: Final = "mihur-w2-cube-net-evidence-r1"
CUBE_NET_STRUCTURES: Final = (
    "CLASSIFY_SINGLE",
    "CONTRAST_PAIR",
    "INVARIANCE_TRANSFER",
    "SURFACE_AREA",
    "PACKAGING_TRANSFER",
)
CUBE_NET_PRIMARY_ROLES: Final = {
    "CLASSIFY_SINGLE": "CUBE_NET_FOLDABILITY",
    "CONTRAST_PAIR": "CUBE_NET_FOLDABILITY",
    "INVARIANCE_TRANSFER": "CUBE_NET_FOLDABILITY",
    "SURFACE_AREA": "CUBE_SURFACE_AREA",
    "PACKAGING_TRANSFER": "CUBE_NET_FOLDABILITY_TRANSFER",
}
CUBE_NET_DIAGNOSIS_CODES: Final = frozenset(
    {
        "SIX_SQUARE_FACE_COUNT_MISSING",
        "ANY_SIX_CONNECTED_IS_NET",
        "VALID_NET_REJECTED",
        "FACE_DIRECTION_EVIDENCE_INCORRECT",
        "FOLDING_JUSTIFICATION_MISSING",
        "PAIR_CLASSIFICATION_REVERSED",
        "PAPER_ORIENTATION_CHANGES_FOLDABILITY",
        "INVARIANCE_JUSTIFICATION_MISSING",
        "FACE_COUNT_NOT_APPLIED",
        "EDGE_NOT_SQUARED",
        "FACE_AREA_INCORRECT",
        "ONE_FACE_ONLY",
        "TOTAL_SURFACE_AREA_INCORRECT",
        "SQUARE_UNIT_MISSING",
        "SURFACE_AREA_JUSTIFICATION_MISSING",
        "PACKAGING_TEMPLATE_SELECTION_ERROR",
        "PACKAGING_FOLDING_EVIDENCE_MISSING",
    }
)


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


def fold_trace(cells: tuple[tuple[int, int], ...]) -> dict[str, object]:
    """Return teacher-only hinge evidence without changing the established oracle."""

    squares = set(cells)
    if len(squares) != 6:
        return {
            "foldable": False,
            "assigned_faces": len(squares),
            "distinct_face_directions": 0,
            "reason_code": "FACE_COUNT_NOT_SIX",
        }
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
                return {
                    "foldable": False,
                    "assigned_faces": len(frames),
                    "distinct_face_directions": len({value[0] for value in frames.values()}),
                    "reason_code": "INCONSISTENT_HINGE_CYCLE",
                }
            if cell not in frames:
                frames[cell] = frame
                pending.append(cell)
    directions = len({frame[0] for frame in frames.values()})
    if len(frames) != 6:
        reason = "DISCONNECTED_SQUARES"
    elif directions != 6:
        reason = "REPEATED_FACE_DIRECTION"
    else:
        reason = "SIX_DISTINCT_FACE_DIRECTIONS"
    result = len(frames) == 6 and directions == 6
    assert result is foldable(cells)
    return {
        "foldable": result,
        "assigned_faces": len(frames),
        "distinct_face_directions": directions,
        "reason_code": reason,
    }


SHAPES = free_hexominoes()
VALID = tuple(shape for shape in SHAPES if foldable(shape))
INVALID = tuple(shape for shape in SHAPES if not foldable(shape))


class CubeNetEvidenceVariant(NamedTuple):
    seed: int
    variant_id: str
    mode: str
    structure: str
    primary_scope_role: str
    prompt: str
    response_fields: tuple[str, ...]
    expected_evidence: Mapping[str, object]
    teacher_parameters: Mapping[str, object]

    def public_payload(self) -> dict[str, object]:
        """Expose one task and its response schema, never its oracle or seed."""

        return {
            "variant_id": self.variant_id,
            "mode": self.mode,
            "structure": self.structure,
            "primary_scope_role": self.primary_scope_role,
            "prompt": self.prompt,
            "response_fields": list(self.response_fields),
        }


def _transform_shape(
    shape: tuple[tuple[int, int], ...], operation: str
) -> tuple[tuple[int, int], ...]:
    transformed = []
    for x, y in shape:
        if operation == "ROTATE_90":
            x, y = -y, x
        elif operation == "REFLECT_VERTICAL":
            x = -x
        elif operation != "TRANSLATE":
            raise ValueError("unsupported paper transformation")
        transformed.append((x + 4, y - 3))
    return tuple(sorted(transformed))


def generate_cube_net_evidence(seed: int, mode: str) -> CubeNetEvidenceVariant:
    """Generate draft evidence-rich cube-net tasks from the existing oracle."""

    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if mode not in ("guided", "independent"):
        raise ValueError("mode must be guided or independent")
    rng = Random(f"{CUBE_NET_EVIDENCE_NAMESPACE}:{mode}:{seed}")
    offset = 2 if mode == "independent" else 0
    structure = CUBE_NET_STRUCTURES[(seed + offset) % len(CUBE_NET_STRUCTURES)]
    variant_id = f"{CUBE_NET_EVIDENCE_NAMESPACE}:{mode}:{seed}"

    if structure == "CLASSIFY_SINGLE":
        shape = rng.choice(VALID if rng.choice((True, False)) else INVALID)
        trace = fold_trace(shape)
        evidence = {
            "decision": "foldable" if trace["foldable"] else "not_foldable",
            "connected_square_count": 6,
            "distinct_face_directions": trace["distinct_face_directions"],
            "reason_code": trace["reason_code"],
        }
        prompt = (
            f"A six-square cut pattern uses grid cells {list(shape)}. Decide whether it "
            "folds into a cube without overlap, then justify the face-direction evidence."
        )
        parameters = {"cells": shape, "trace": trace}
    elif structure == "CONTRAST_PAIR":
        valid, invalid = rng.choice(VALID), rng.choice(INVALID)
        if rng.choice((True, False)):
            first, second, foldable_label = valid, invalid, "A"
        else:
            first, second, foldable_label = invalid, valid, "B"
        rejected = second if foldable_label == "A" else first
        rejected_trace = fold_trace(rejected)
        evidence = {
            "foldable_label": foldable_label,
            "rejected_label": "B" if foldable_label == "A" else "A",
            "foldable_distinct_face_directions": 6,
            "rejected_reason_code": rejected_trace["reason_code"],
        }
        prompt = (
            f"Pattern A uses {list(first)}; pattern B uses {list(second)}. Choose the one "
            "that folds into a cube and identify why the other fails."
        )
        parameters = {"a": first, "b": second}
    elif structure == "INVARIANCE_TRANSFER":
        original = rng.choice(VALID)
        operation = rng.choice(("ROTATE_90", "REFLECT_VERTICAL", "TRANSLATE"))
        transformed = _transform_shape(original, operation)
        evidence = {
            "original_decision": "foldable",
            "transformed_decision": "foldable",
            "invariant_reason": "RIGID_GRID_TRANSFORM_PRESERVES_ADJACENCY",
        }
        prompt = (
            f"A foldable package pattern {list(original)} is changed by {operation.lower()} "
            f"to {list(transformed)}. Decide the foldability of both and name the invariant."
        )
        parameters = {"original": original, "transformed": transformed, "operation": operation}
    elif structure == "SURFACE_AREA":
        edge = Fraction(rng.randint(1, 9), rng.randint(2, 7))
        face_area = edge * edge
        total_area = 6 * face_area
        evidence = {
            "face_count": 6,
            "face_area": str(face_area),
            "total_surface_area": str(total_area),
            "unit": "cm²",
            "reason_code": "SIX_CONGRUENT_SQUARE_FACES",
        }
        prompt = (
            f"A confirmed foldable cube net has edge {edge} cm. Record the area of one "
            "face and the exact total surface area, including units and rule."
        )
        parameters = {"edge": edge, "face_area": face_area, "total_area": total_area}
    else:
        valid = rng.choice(VALID)
        cyclic = tuple(
            shape
            for shape in INVALID
            if any(
                {(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)} <= set(shape)
                for x, y in shape
            )
        )
        invalid = rng.choice(cyclic)
        if rng.choice((True, False)):
            first, second, choice = valid, invalid, "A"
        else:
            first, second, choice = invalid, valid, "B"
        evidence = {
            "usable_template": choice,
            "rejected_template": "B" if choice == "A" else "A",
            "foldable_face_directions": 6,
            "rejection_reason": "INCONSISTENT_HINGE_CYCLE",
        }
        prompt = (
            "A box maker must choose a cut pattern that closes without overlap. "
            f"Template A uses {list(first)}; template B uses {list(second)}. Choose and "
            "justify the usable template from hinge and face-direction evidence."
        )
        parameters = {"a": first, "b": second}

    return CubeNetEvidenceVariant(
        seed=seed,
        variant_id=variant_id,
        mode=mode,
        structure=structure,
        primary_scope_role=CUBE_NET_PRIMARY_ROLES[structure],
        prompt=prompt,
        response_fields=tuple(evidence),
        expected_evidence=evidence,
        teacher_parameters=parameters,
    )


def fresh_cube_net_exit(item: CubeNetEvidenceVariant) -> CubeNetEvidenceVariant:
    """Return a deterministic same-structure new task after a guided repair."""

    for increment in range(5, 55, 5):
        candidate = generate_cube_net_evidence(item.seed + increment, item.mode)
        if candidate.structure == item.structure and candidate.prompt != item.prompt:
            return candidate
    raise RuntimeError("could not construct a fresh cube-net exit")


def diagnose_cube_net_guided(
    item: CubeNetEvidenceVariant, response: Mapping[str, object]
) -> str:
    """Classify guided evidence only; independent assessment is never scored here."""

    if item.mode != "guided":
        return "INDEPENDENT_ASSESSMENT_NOT_SCORED_HERE"
    if not isinstance(response, Mapping) or set(response) != set(item.response_fields):
        return "INCOMPLETE_EVIDENCE"
    expected = item.expected_evidence
    if item.structure == "CLASSIFY_SINGLE":
        if response["connected_square_count"] != 6:
            return "SIX_SQUARE_FACE_COUNT_MISSING"
        if response["decision"] != expected["decision"]:
            return (
                "ANY_SIX_CONNECTED_IS_NET"
                if expected["decision"] == "not_foldable"
                else "VALID_NET_REJECTED"
            )
        if response["distinct_face_directions"] != expected["distinct_face_directions"]:
            return "FACE_DIRECTION_EVIDENCE_INCORRECT"
        if response["reason_code"] != expected["reason_code"]:
            return "FOLDING_JUSTIFICATION_MISSING"
    elif item.structure == "CONTRAST_PAIR":
        if (
            response["foldable_label"] != expected["foldable_label"]
            or response["rejected_label"] != expected["rejected_label"]
        ):
            return "PAIR_CLASSIFICATION_REVERSED"
        if response["foldable_distinct_face_directions"] != 6:
            return "FACE_DIRECTION_EVIDENCE_INCORRECT"
        if response["rejected_reason_code"] != expected["rejected_reason_code"]:
            return "FOLDING_JUSTIFICATION_MISSING"
    elif item.structure == "INVARIANCE_TRANSFER":
        if (
            response["original_decision"] != "foldable"
            or response["transformed_decision"] != "foldable"
        ):
            return "PAPER_ORIENTATION_CHANGES_FOLDABILITY"
        if response["invariant_reason"] != expected["invariant_reason"]:
            return "INVARIANCE_JUSTIFICATION_MISSING"
    elif item.structure == "SURFACE_AREA":
        edge = item.teacher_parameters["edge"]
        if response["face_count"] != 6:
            return "FACE_COUNT_NOT_APPLIED"
        if response["unit"] != "cm²":
            return "SQUARE_UNIT_MISSING"
        if response["face_area"] != expected["face_area"]:
            return "EDGE_NOT_SQUARED" if response["face_area"] == str(edge) else "FACE_AREA_INCORRECT"
        if response["total_surface_area"] != expected["total_surface_area"]:
            return (
                "ONE_FACE_ONLY"
                if response["total_surface_area"] == expected["face_area"]
                else "TOTAL_SURFACE_AREA_INCORRECT"
            )
        if response["reason_code"] != expected["reason_code"]:
            return "SURFACE_AREA_JUSTIFICATION_MISSING"
    else:
        if (
            response["usable_template"] != expected["usable_template"]
            or response["rejected_template"] != expected["rejected_template"]
        ):
            return "PACKAGING_TEMPLATE_SELECTION_ERROR"
        if response["foldable_face_directions"] != 6:
            return "FACE_DIRECTION_EVIDENCE_INCORRECT"
        if response["rejection_reason"] != expected["rejection_reason"]:
            return "PACKAGING_FOLDING_EVIDENCE_MISSING"
    return "CORRECT_STRUCTURED_PRACTICE_ONLY"


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
    return ((f"Class A data: {data}. Class B data: {other}. Which class has more scores "
             "from 15 through 24 inclusive (A or B)?"), "A" if a > b else "B",
            {"data_a": data, "data_b": other}, "compare_upper_bins",
            "Combine frequencies of the last two bins for each class.")


def _spatial(rng: Random, variant: int):
    if variant == 2:
        numerator, denominator = rng.randint(1, 9), rng.randint(2, 6)
        edge = Fraction(numerator, denominator)
        return ((f"A foldable six-square cube net has edge {edge} cm. "
                 "Find total surface area in cm² (exact fraction or integer)."),
                str(6 * edge * edge), {"numerator": numerator, "denominator": denominator},
                "net_surface_area", "Count six square faces and square the edge length.")
    valid = rng.choice(VALID)
    invalid = rng.choice(INVALID)
    if variant == 1:
        if rng.choice((True, False)):
            first, second, answer = valid, invalid, "A"
        else:
            first, second, answer = invalid, valid, "B"
        return ((f"Net A: {list(first)}. Net B: {list(second)}. "
                 "Which six-square shape folds into a cube without face overlap (A or B)?"),
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
