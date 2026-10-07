"""California Grade 2 authoritative gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

CA_GRADE2_STANDARD_CODES = (
    "2.OA.1", "2.OA.2", "2.OA.3", "2.OA.4",
    "2.NBT.1", "2.NBT.2", "2.NBT.3", "2.NBT.4", "2.NBT.5", "2.NBT.6", "2.NBT.7", "2.NBT.8", "2.NBT.9",
    "2.MD.1", "2.MD.2", "2.MD.3", "2.MD.4", "2.MD.5", "2.MD.6", "2.MD.7", "2.MD.8", "2.MD.9", "2.MD.10",
    "2.G.1", "2.G.2", "2.G.3",
)


def _item(
    code: str,
    status: GapStatus,
    skill: str | None = None,
    rationale: str | None = None,
) -> StandardGap:
    return StandardGap("CA", 2, code, status, skill, rationale)


CA_GRADE2_GAPS = (
    _item("2.OA.1", GapStatus.COVERED, "MATH.NS.ADDITION"),
    _item("2.OA.2", GapStatus.COVERED, "MATH.NS.ADDITION"),
    _item(
        "2.OA.3",
        GapStatus.PARTIAL,
        "MATH.NS.DIVISIBILITY",
        "Divisibility exists; elementary odd/even pairing and equal-addend representations need depth.",
    ),
    _item(
        "2.OA.4",
        GapStatus.PARTIAL,
        "MATH.NS.MULTIPLICATION",
        "Array multiplication exists; repeated-addition equations for small rectangular arrays need depth.",
    ),
    _item("2.NBT.1", GapStatus.COVERED, "MATH.NS.PLACE_VALUE"),
    _item("2.NBT.2", GapStatus.COVERED, "MATH.NS.COUNTING"),
    _item("2.NBT.3", GapStatus.COVERED, "MATH.NS.WORD_FORM"),
    _item("2.NBT.4", GapStatus.COVERED, "MATH.NS.COMPARE_ORDER"),
    _item("2.NBT.5", GapStatus.COVERED, "MATH.NS.ADDITION"),
    _item(
        "2.NBT.6",
        GapStatus.PARTIAL,
        "MATH.NS.ADDITION",
        "Addition exists; sums of up to four two-digit addends need explicit depth.",
    ),
    _item(
        "2.NBT.7",
        GapStatus.PARTIAL,
        "MATH.NS.ADDITION",
        "Multi-digit operations exist; elementary concrete/place-value strategy evidence needs depth.",
    ),
    _item(
        "2.NBT.8",
        GapStatus.PARTIAL,
        "MATH.NS.PLACE_VALUE",
        "Place-value and operations exist; mental ±10/±100 reasoning needs explicit depth.",
    ),
    _item(
        "2.NBT.9",
        GapStatus.PARTIAL,
        "MATH.NS.PROPERTIES",
        "Properties exist; explaining why place-value addition/subtraction strategies work needs depth.",
    ),
    _item(
        "2.MD.1",
        GapStatus.PARTIAL,
        "MATH.MEAS.UNIT_CONVERSION",
        "Length units exist; tool selection and direct object measurement need elementary depth.",
    ),
    _item(
        "2.MD.2",
        GapStatus.PARTIAL,
        "MATH.MEAS.UNIT_CONVERSION",
        "Unit conversion exists; same-object different-unit-size reasoning needs depth.",
    ),
    _item(
        "2.MD.3",
        GapStatus.PARTIAL,
        "MATH.MEAS.UNIT_CONVERSION",
        "Length units and estimation exist separately; benchmark length estimation needs depth.",
    ),
    _item(
        "2.MD.4",
        GapStatus.PARTIAL,
        "MATH.MEAS.UNIT_CONVERSION",
        "Length skills exist; direct difference comparison between measured objects needs depth.",
    ),
    _item(
        "2.MD.5",
        GapStatus.PARTIAL,
        "MATH.NS.ADDITION",
        "Addition/subtraction word families exist; explicit length-context diagrams need depth.",
    ),
    _item("2.MD.6", GapStatus.COVERED, "MATH.NS.NUMBER_LINE"),
    _item("2.MD.7", GapStatus.COVERED, "MATH.MEAS.TIME"),
    _item(
        "2.MD.8",
        GapStatus.PARTIAL,
        "MATH.NS.DECIMAL.ADD_SUBTRACT",
        "Money total/change exists; coin/bill symbol and cents-to-dollar elementary representations need depth.",
    ),
    _item("2.MD.9", GapStatus.COVERED, "MATH.DATA.ELEMENTARY.REPRESENT"),
    _item("2.MD.10", GapStatus.COVERED, "MATH.DATA.ELEMENTARY.REPRESENT"),
    _item(
        "2.G.1",
        GapStatus.PARTIAL,
        "MATH.GEO.SHAPES",
        "Shape classification exists; specified-attribute recognition/drawing needs elementary depth.",
    ),
    _item(
        "2.G.2",
        GapStatus.PARTIAL,
        "MATH.GEO.MEASURE.AREA",
        "Arrays/area exist; partitioning rectangles into equal square rows/columns needs depth.",
    ),
    _item(
        "2.G.3",
        GapStatus.PARTIAL,
        "MATH.NF.FRACTION_MEANING",
        "Fraction meaning exists; halves/thirds/fourths shape partitioning and equal-share language need depth.",
    ),
)

validate_inventory(CA_GRADE2_STANDARD_CODES, CA_GRADE2_GAPS)
