"""California Grade 6 authoritative gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

CA_GRADE6_STANDARD_CODES = (
    "6.RP.1", "6.RP.2", "6.RP.3",
    "6.NS.1", "6.NS.2", "6.NS.3", "6.NS.4", "6.NS.5", "6.NS.6", "6.NS.7", "6.NS.8",
    "6.EE.1", "6.EE.2", "6.EE.3", "6.EE.4", "6.EE.5", "6.EE.6", "6.EE.7", "6.EE.8", "6.EE.9",
    "6.G.1", "6.G.2", "6.G.3", "6.G.4",
    "6.SP.1", "6.SP.2", "6.SP.3", "6.SP.4", "6.SP.5",
)


def _item(
    code: str,
    status: GapStatus,
    skill: str | None = None,
    rationale: str | None = None,
) -> StandardGap:
    return StandardGap("CA", 6, code, status, skill, rationale)


CA_GRADE6_GAPS = (
    _item("6.RP.1", GapStatus.COVERED, "MATH.RP.RATIO.INTERPRET"),
    _item("6.RP.2", GapStatus.COVERED, "MATH.RP.RATE.UNIT"),
    _item(
        "6.RP.3",
        GapStatus.PARTIAL,
        "MATH.RP.RATIO.EQUIVALENT",
        "Ratio tables/rates/percents/conversions exist across shared skills; integrated breadth needs depth.",
    ),
    _item("6.NS.1", GapStatus.COVERED, "MATH.NF.DIVIDE"),
    _item("6.NS.2", GapStatus.COVERED, "MATH.NS.DIVISION"),
    _item(
        "6.NS.3",
        GapStatus.PARTIAL,
        "MATH.NS.DECIMAL.ADD_SUBTRACT",
        "All decimal operations exist across shared decimal skills; fluency integration needs depth.",
    ),
    _item("6.NS.4", GapStatus.COVERED, "MATH.NS.GCF_LCM"),
    _item("6.NS.5", GapStatus.COVERED, "MATH.NS.INTEGERS"),
    _item(
        "6.NS.6",
        GapStatus.PARTIAL,
        "MATH.NS.RATIONAL.COMPARE",
        "Rational number-line and coordinate capabilities exist; four-quadrant integration needs depth.",
    ),
    _item(
        "6.NS.7",
        GapStatus.PARTIAL,
        "MATH.NS.RATIONAL.COMPARE",
        "Rational comparison exists; absolute-value magnitude/context reasoning needs depth.",
    ),
    _item("6.NS.8", GapStatus.COVERED, "MATH.GEO.COORDINATE"),
    _item("6.EE.1", GapStatus.COVERED, "MATH.NS.EXPONENTS"),
    _item("6.EE.2", GapStatus.COVERED, "MATH.EE.EXPR"),
    _item(
        "6.EE.3",
        GapStatus.PARTIAL,
        "MATH.EE.EXPR",
        "Distributive/combining capabilities exist; full property-driven equivalence depth remains.",
    ),
    _item(
        "6.EE.4",
        GapStatus.PARTIAL,
        "MATH.EE.EXPR",
        "Expression evaluation exists; identity/equivalence reasoning needs explicit depth.",
    ),
    _item(
        "6.EE.5",
        GapStatus.PARTIAL,
        "MATH.EE.EQUATION.ONE",
        "Solving/checking capabilities exist; specified-set truth testing needs depth.",
    ),
    _item("6.EE.6", GapStatus.COVERED, "MATH.EE.EXPR"),
    _item("6.EE.7", GapStatus.COVERED, "MATH.EE.EQUATION.ONE"),
    _item("6.EE.8", GapStatus.COVERED, "MATH.EE.INEQUALITY.ONE"),
    _item(
        "6.EE.9",
        GapStatus.PARTIAL,
        "MATH.F.LINEAR.SLOPE_INTERCEPT",
        "Linear models exist; dependent/independent variable table-graph-equation translation needs depth.",
    ),
    _item("6.G.1", GapStatus.COVERED, "MATH.GEO.MEASURE.AREA"),
    _item(
        "6.G.2",
        GapStatus.PARTIAL,
        "MATH.GEO.MEASURE.VOLUME",
        "Prism volume exists; fractional-edge packing/justification needs depth.",
    ),
    _item(
        "6.G.3",
        GapStatus.PARTIAL,
        "MATH.GEO.COORDINATE",
        "Coordinate distance exists; polygon construction and contextual side-length work needs depth.",
    ),
    _item(
        "6.G.4",
        GapStatus.PARTIAL,
        "MATH.GEO.SURFACE_AREA",
        "Surface-area and net capabilities exist; broader prism/pyramid net representation needs depth.",
    ),
    _item("6.SP.1", GapStatus.GAP, rationale="gap:statistical-question-variability"),
    _item(
        "6.SP.2",
        GapStatus.PARTIAL,
        "MATH.DATA.SPREAD",
        "Center/spread families exist; distribution-shape concept needs explicit depth.",
    ),
    _item(
        "6.SP.3",
        GapStatus.PARTIAL,
        "MATH.DATA.CENTER",
        "Center and variation measures exist; conceptual summary distinction needs depth.",
    ),
    _item(
        "6.SP.4",
        GapStatus.PARTIAL,
        "MATH.DATA.REPRESENTATIONS",
        "Dot/histogram/five-number work exists; full box-plot representation needs depth.",
    ),
    _item(
        "6.SP.5",
        GapStatus.PARTIAL,
        "MATH.DATA.SPREAD",
        "Center/spread calculations exist; contextual distribution summaries need integrated depth.",
    ),
)

validate_inventory(CA_GRADE6_STANDARD_CODES, CA_GRADE6_GAPS)
