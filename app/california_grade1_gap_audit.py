"""California Grade 1 authoritative gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

CA_GRADE1_STANDARD_CODES = (
    "1.OA.1", "1.OA.2", "1.OA.3", "1.OA.4", "1.OA.5", "1.OA.6", "1.OA.7", "1.OA.8",
    "1.NBT.1", "1.NBT.2", "1.NBT.3", "1.NBT.4", "1.NBT.5", "1.NBT.6",
    "1.MD.1", "1.MD.2", "1.MD.3", "1.MD.4",
    "1.G.1", "1.G.2", "1.G.3",
)


def _item(
    code: str,
    status: GapStatus,
    skill: str | None = None,
    rationale: str | None = None,
) -> StandardGap:
    return StandardGap("CA", 1, code, status, skill, rationale)


CA_GRADE1_GAPS = (
    _item("1.OA.1", GapStatus.COVERED, "MATH.NS.ADDITION"),
    _item(
        "1.OA.2",
        GapStatus.PARTIAL,
        "MATH.NS.ADDITION",
        "Addition word families exist; explicit three-addend story problems need depth.",
    ),
    _item("1.OA.3", GapStatus.COVERED, "MATH.NS.PROPERTIES"),
    _item("1.OA.4", GapStatus.COVERED, "MATH.NS.SUBTRACTION"),
    _item(
        "1.OA.5",
        GapStatus.PARTIAL,
        "MATH.NS.COUNTING",
        "Counting and operations exist; counting-on/back as operation strategies needs depth.",
    ),
    _item(
        "1.OA.6",
        GapStatus.PARTIAL,
        "MATH.NS.ADDITION",
        "Facts exist; make-ten/decompose/related-sum strategy evidence needs elementary depth.",
    ),
    _item(
        "1.OA.7",
        GapStatus.PARTIAL,
        "MATH.EE.EQUATION.ONE",
        "Equation truth exists at higher depth; elementary equal-sign meaning and true/false forms need depth.",
    ),
    _item("1.OA.8", GapStatus.COVERED, "MATH.NS.ADDITION"),
    _item("1.NBT.1", GapStatus.COVERED, "MATH.NS.COUNTING"),
    _item("1.NBT.2", GapStatus.COVERED, "MATH.NS.PLACE_VALUE"),
    _item("1.NBT.3", GapStatus.COVERED, "MATH.NS.COMPARE_ORDER"),
    _item(
        "1.NBT.4",
        GapStatus.PARTIAL,
        "MATH.NS.ADDITION",
        "Addition exists; concrete tens/ones strategies within 100 need elementary depth.",
    ),
    _item(
        "1.NBT.5",
        GapStatus.PARTIAL,
        "MATH.NS.PLACE_VALUE",
        "Place value exists; mental ten-more/ten-less reasoning needs explicit depth.",
    ),
    _item(
        "1.NBT.6",
        GapStatus.PARTIAL,
        "MATH.NS.SUBTRACTION",
        "Subtraction exists; multiples-of-ten concrete/place-value models need depth.",
    ),
    _item(
        "1.MD.1",
        GapStatus.PARTIAL,
        "MATH.NS.COMPARE_ORDER",
        "Comparison/order exists; direct length comparison and transitivity context need depth.",
    ),
    _item(
        "1.MD.2",
        GapStatus.PARTIAL,
        "MATH.MEAS.UNIT_CONVERSION",
        "Length units exist; iterating equal-size units with no gaps/overlaps needs elementary depth.",
    ),
    _item("1.MD.3", GapStatus.COVERED, "MATH.MEAS.TIME"),
    _item("1.MD.4", GapStatus.COVERED, "MATH.DATA.ELEMENTARY.REPRESENT"),
    _item(
        "1.G.1",
        GapStatus.PARTIAL,
        "MATH.GEO.SHAPES",
        "Shape classification exists; defining-vs-nondefining attribute construction needs depth.",
    ),
    _item(
        "1.G.2",
        GapStatus.PARTIAL,
        "MATH.GEO.SHAPES",
        "Shape families exist; composing two- and three-dimensional shapes needs explicit depth.",
    ),
    _item(
        "1.G.3",
        GapStatus.PARTIAL,
        "MATH.NF.FRACTION_MEANING",
        "Fraction meaning exists; halves/fourths partitioning and equal-share language need depth.",
    ),
)

validate_inventory(CA_GRADE1_STANDARD_CODES, CA_GRADE1_GAPS)
