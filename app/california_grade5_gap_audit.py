"""California Grade 5 authoritative gap audit.

Includes California addition 5.OA.2.1 from the 2013 CA CCSSM edition.
Classifications are proposed audit data and do not publish equivalence.
"""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

CA_GRADE5_STANDARD_CODES = (
    "5.OA.1", "5.OA.2", "5.OA.2.1", "5.OA.3",
    "5.NBT.1", "5.NBT.2", "5.NBT.3", "5.NBT.4", "5.NBT.5", "5.NBT.6", "5.NBT.7",
    "5.NF.1", "5.NF.2", "5.NF.3", "5.NF.4", "5.NF.5", "5.NF.6", "5.NF.7",
    "5.MD.1", "5.MD.2", "5.MD.3", "5.MD.4", "5.MD.5",
    "5.G.1", "5.G.2", "5.G.3", "5.G.4",
)


def _item(
    code: str,
    status: GapStatus,
    skill: str | None = None,
    rationale: str | None = None,
) -> StandardGap:
    return StandardGap("CA", 5, code, status, skill, rationale)


CA_GRADE5_GAPS = (
    _item("5.OA.1", GapStatus.COVERED, "MATH.NS.ORDER_OF_OPERATIONS"),
    _item(
        "5.OA.2",
        GapStatus.PARTIAL,
        "MATH.EE.EXPR",
        "Expression translation/evaluation exists; interpretation without evaluation needs depth.",
    ),
    _item("5.OA.2.1", GapStatus.COVERED, "MATH.NS.FACTORS_MULTIPLES"),
    _item(
        "5.OA.3",
        GapStatus.PARTIAL,
        "MATH.PATTERN.FUNCTION_RULE",
        "Rule patterns exist; paired-pattern relationship and coordinate graphing need depth.",
    ),
    _item("5.NBT.1", GapStatus.COVERED, "MATH.NS.PLACE_VALUE"),
    _item(
        "5.NBT.2",
        GapStatus.PARTIAL,
        "MATH.NS.PLACE_VALUE",
        "Powers-of-ten reasoning exists; decimal-point shift and exponent integration need depth.",
    ),
    _item("5.NBT.3", GapStatus.COVERED, "MATH.NS.DECIMAL.PLACE_VALUE"),
    _item("5.NBT.4", GapStatus.COVERED, "MATH.NS.ROUNDING"),
    _item("5.NBT.5", GapStatus.COVERED, "MATH.NS.MULTIPLICATION"),
    _item("5.NBT.6", GapStatus.COVERED, "MATH.NS.DIVISION"),
    _item(
        "5.NBT.7",
        GapStatus.PARTIAL,
        "MATH.NS.DECIMAL.ADD_SUBTRACT",
        "All four decimal operations exist across shared skills; models and integrated fluency need depth.",
    ),
    _item("5.NF.1", GapStatus.COVERED, "MATH.NF.ADD_SUBTRACT"),
    _item(
        "5.NF.2",
        GapStatus.PARTIAL,
        "MATH.NF.ADD_SUBTRACT",
        "Unlike-denominator operations exist; broaden visual-model word problems and estimation.",
    ),
    _item("5.NF.3", GapStatus.COVERED, "MATH.NF.DIVIDE"),
    _item("5.NF.4", GapStatus.COVERED, "MATH.NF.MULTIPLY"),
    _item(
        "5.NF.5",
        GapStatus.PARTIAL,
        "MATH.NF.MULTIPLY",
        "Fraction multiplication/scaling exists; explicit product-size reasoning needs depth.",
    ),
    _item(
        "5.NF.6",
        GapStatus.PARTIAL,
        "MATH.NF.MULTIPLY",
        "Fraction word contexts exist; broaden mixed-number visual/equation modeling.",
    ),
    _item(
        "5.NF.7",
        GapStatus.PARTIAL,
        "MATH.NF.DIVIDE",
        "Fraction division exists; unit-fraction-by-whole and whole-by-unit-fraction models need depth.",
    ),
    _item("5.MD.1", GapStatus.COVERED, "MATH.MEAS.UNIT_CONVERSION"),
    _item(
        "5.MD.2",
        GapStatus.PARTIAL,
        "MATH.DATA.ELEMENTARY.REPRESENT",
        "Line plots exist; fractional-unit measurements plus fraction-operation questions need depth.",
    ),
    _item(
        "5.MD.3",
        GapStatus.PARTIAL,
        "MATH.GEO.MEASURE.VOLUME",
        "Prism volume exists; unit-cube volume concept and packing meaning need depth.",
    ),
    _item(
        "5.MD.4",
        GapStatus.PARTIAL,
        "MATH.GEO.MEASURE.VOLUME",
        "Volume computation exists; explicit unit-cube counting representations need depth.",
    ),
    _item(
        "5.MD.5",
        GapStatus.PARTIAL,
        "MATH.GEO.MEASURE.VOLUME",
        "Volume formulas exist; additive/composite-volume reasoning needs broader depth.",
    ),
    _item(
        "5.G.1",
        GapStatus.PARTIAL,
        "MATH.GEO.COORDINATE",
        "Coordinate skills exist; first-quadrant axis/origin coordinate-system concept needs depth.",
    ),
    _item(
        "5.G.2",
        GapStatus.PARTIAL,
        "MATH.GEO.COORDINATE",
        "Coordinate work exists; contextual first-quadrant graph interpretation needs depth.",
    ),
    _item(
        "5.G.3",
        GapStatus.PARTIAL,
        "MATH.GEO.SHAPES",
        "Shape classification exists; inheritance of category attributes needs explicit reasoning.",
    ),
    _item(
        "5.G.4",
        GapStatus.PARTIAL,
        "MATH.GEO.SHAPES",
        "Shape classification exists; hierarchical classification representation needs depth.",
    ),
)

validate_inventory(CA_GRADE5_STANDARD_CODES, CA_GRADE5_GAPS)
