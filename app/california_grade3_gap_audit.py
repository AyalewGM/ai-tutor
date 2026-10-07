"""California Grade 3 authoritative gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

CA_GRADE3_STANDARD_CODES = (
    "3.OA.1", "3.OA.2", "3.OA.3", "3.OA.4", "3.OA.5", "3.OA.6", "3.OA.7", "3.OA.8", "3.OA.9",
    "3.NBT.1", "3.NBT.2", "3.NBT.3",
    "3.NF.1", "3.NF.2", "3.NF.3",
    "3.MD.1", "3.MD.2", "3.MD.3", "3.MD.4", "3.MD.5", "3.MD.6", "3.MD.7", "3.MD.8",
    "3.G.1", "3.G.2",
)


def _item(
    code: str,
    status: GapStatus,
    skill: str | None = None,
    rationale: str | None = None,
) -> StandardGap:
    return StandardGap("CA", 3, code, status, skill, rationale)


CA_GRADE3_GAPS = (
    _item("3.OA.1", GapStatus.COVERED, "MATH.NS.MULTIPLICATION"),
    _item("3.OA.2", GapStatus.COVERED, "MATH.NS.DIVISION"),
    _item("3.OA.3", GapStatus.COVERED, "MATH.NS.MULTIPLICATION"),
    _item("3.OA.4", GapStatus.COVERED, "MATH.NS.DIVISION"),
    _item("3.OA.5", GapStatus.COVERED, "MATH.NS.PROPERTIES"),
    _item("3.OA.6", GapStatus.COVERED, "MATH.NS.DIVISION"),
    _item("3.OA.7", GapStatus.COVERED, "MATH.NS.MULTIPLICATION"),
    _item(
        "3.OA.8",
        GapStatus.PARTIAL,
        "MATH.NS.MULTIPLICATION",
        "Multistep word families exist; integrate all four operations and reasonableness checks.",
    ),
    _item("3.OA.9", GapStatus.COVERED, "MATH.PATTERN.NUMERIC"),
    _item("3.NBT.1", GapStatus.COVERED, "MATH.NS.ROUNDING"),
    _item("3.NBT.2", GapStatus.COVERED, "MATH.NS.ADDITION"),
    _item("3.NBT.3", GapStatus.COVERED, "MATH.NS.MULTIPLICATION"),
    _item("3.NF.1", GapStatus.COVERED, "MATH.NF.FRACTION_MEANING"),
    _item("3.NF.2", GapStatus.COVERED, "MATH.NF.FRACTION_MEANING"),
    _item(
        "3.NF.3",
        GapStatus.PARTIAL,
        "MATH.NF.EQUIVALENT_FRACTIONS",
        "Equivalence and comparison exist; visual whole-number equivalence and justification need depth.",
    ),
    _item("3.MD.1", GapStatus.COVERED, "MATH.MEAS.TIME"),
    _item(
        "3.MD.2",
        GapStatus.PARTIAL,
        "MATH.MEAS.UNIT_CONVERSION",
        "Mass/capacity skills exist; one-step measurement word-problem modeling needs elementary depth.",
    ),
    _item("3.MD.3", GapStatus.COVERED, "MATH.DATA.ELEMENTARY.REPRESENT"),
    _item(
        "3.MD.4",
        GapStatus.PARTIAL,
        "MATH.DATA.ELEMENTARY.REPRESENT",
        "Line plots exist; half- and quarter-unit measurement scales need depth.",
    ),
    _item(
        "3.MD.5",
        GapStatus.PARTIAL,
        "MATH.GEO.MEASURE.AREA",
        "Area computation exists; unit-square covering concept needs explicit depth.",
    ),
    _item(
        "3.MD.6",
        GapStatus.PARTIAL,
        "MATH.GEO.MEASURE.AREA",
        "Area computation exists; direct unit-square counting representations need depth.",
    ),
    _item(
        "3.MD.7",
        GapStatus.PARTIAL,
        "MATH.GEO.MEASURE.AREA",
        "Rectangle area and distributive models exist; formal multiplication/additivity connections need depth.",
    ),
    _item(
        "3.MD.8",
        GapStatus.PARTIAL,
        "MATH.GEO.MEASURE.PERIMETER",
        "Perimeter exists; same-area/different-perimeter and inverse comparison investigations need depth.",
    ),
    _item(
        "3.G.1",
        GapStatus.PARTIAL,
        "MATH.GEO.SHAPES",
        "Shape classification exists; shared-attribute quadrilateral category reasoning needs depth.",
    ),
    _item(
        "3.G.2",
        GapStatus.PARTIAL,
        "MATH.NF.FRACTION_MEANING",
        "Fraction meaning exists; partitioned-shape area representation needs depth.",
    ),
)

validate_inventory(CA_GRADE3_STANDARD_CODES, CA_GRADE3_GAPS)
