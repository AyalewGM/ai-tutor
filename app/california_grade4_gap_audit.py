"""California Grade 4 authoritative gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

CA_GRADE4_STANDARD_CODES = (
    "4.OA.1", "4.OA.2", "4.OA.3", "4.OA.4", "4.OA.5",
    "4.NBT.1", "4.NBT.2", "4.NBT.3", "4.NBT.4", "4.NBT.5", "4.NBT.6",
    "4.NF.1", "4.NF.2", "4.NF.3", "4.NF.4", "4.NF.5", "4.NF.6", "4.NF.7",
    "4.MD.1", "4.MD.2", "4.MD.3", "4.MD.4", "4.MD.5", "4.MD.6", "4.MD.7",
    "4.G.1", "4.G.2", "4.G.3",
)


def _item(
    code: str,
    status: GapStatus,
    skill: str | None = None,
    rationale: str | None = None,
) -> StandardGap:
    return StandardGap("CA", 4, code, status, skill, rationale)


CA_GRADE4_GAPS = (
    _item("4.OA.1", GapStatus.COVERED, "MATH.NS.MULTIPLICATION"),
    _item("4.OA.2", GapStatus.COVERED, "MATH.NS.MULTIPLICATION"),
    _item(
        "4.OA.3",
        GapStatus.PARTIAL,
        "MATH.NS.MULTIPLICATION",
        "Multistep word families exist; integrate all four operations, estimation, and remainder interpretation.",
    ),
    _item("4.OA.4", GapStatus.COVERED, "MATH.NS.FACTORS_MULTIPLES"),
    _item("4.OA.5", GapStatus.COVERED, "MATH.PATTERN.NUMERIC"),
    _item("4.NBT.1", GapStatus.COVERED, "MATH.NS.PLACE_VALUE"),
    _item("4.NBT.2", GapStatus.COVERED, "MATH.NS.PLACE_VALUE"),
    _item("4.NBT.3", GapStatus.COVERED, "MATH.NS.ROUNDING"),
    _item("4.NBT.4", GapStatus.COVERED, "MATH.NS.ADDITION"),
    _item("4.NBT.5", GapStatus.COVERED, "MATH.NS.MULTIPLICATION"),
    _item("4.NBT.6", GapStatus.COVERED, "MATH.NS.DIVISION"),
    _item("4.NF.1", GapStatus.COVERED, "MATH.NF.EQUIVALENT_FRACTIONS"),
    _item("4.NF.2", GapStatus.COVERED, "MATH.NF.COMPARE"),
    _item(
        "4.NF.3",
        GapStatus.PARTIAL,
        "MATH.NF.ADD_SUBTRACT",
        "Fraction addition/subtraction and mixed numbers exist; decomposition and same-whole reasoning need depth.",
    ),
    _item(
        "4.NF.4",
        GapStatus.PARTIAL,
        "MATH.NF.MULTIPLY",
        "Fraction multiplication exists; unit-fraction multiples and visual word modeling need depth.",
    ),
    _item("4.NF.5", GapStatus.COVERED, "MATH.NS.DECIMAL.CONVERT"),
    _item("4.NF.6", GapStatus.COVERED, "MATH.NS.DECIMAL.CONVERT"),
    _item("4.NF.7", GapStatus.COVERED, "MATH.NS.DECIMAL.COMPARE"),
    _item("4.MD.1", GapStatus.COVERED, "MATH.MEAS.UNIT_CONVERSION"),
    _item(
        "4.MD.2",
        GapStatus.PARTIAL,
        "MATH.MEAS.UNIT_CONVERSION",
        "Conversions and time exist; integrate distance/volume/mass/money fraction-decimal word problems.",
    ),
    _item("4.MD.3", GapStatus.COVERED, "MATH.GEO.MEASURE.AREA"),
    _item(
        "4.MD.4",
        GapStatus.PARTIAL,
        "MATH.DATA.ELEMENTARY.REPRESENT",
        "Line plots exist; fractional measurement data and difference questions need depth.",
    ),
    _item(
        "4.MD.5",
        GapStatus.PARTIAL,
        "MATH.GEO.ANGLES",
        "Angle families exist; turn-based angle-measure concepts need explicit depth.",
    ),
    _item("4.MD.6", GapStatus.GAP, rationale="gap:angle-measure-draw-protractor"),
    _item(
        "4.MD.7",
        GapStatus.PARTIAL,
        "MATH.GEO.ANGLES",
        "Missing-angle relationships exist; additive angle decomposition needs broader depth.",
    ),
    _item(
        "4.G.1",
        GapStatus.PARTIAL,
        "MATH.GEO.SHAPES",
        "Shape/angle families exist; explicit points-lines-rays and parallel/perpendicular drawing need depth.",
    ),
    _item(
        "4.G.2",
        GapStatus.PARTIAL,
        "MATH.GEO.SHAPES",
        "Shape classification exists; classification by line and angle attributes needs depth.",
    ),
    _item(
        "4.G.3",
        GapStatus.PARTIAL,
        "MATH.GEO.SYMMETRY.REFLECTION",
        "Reflection/symmetry exists; line-symmetry identification and drawing need elementary depth.",
    ),
)

validate_inventory(CA_GRADE4_STANDARD_CODES, CA_GRADE4_GAPS)
