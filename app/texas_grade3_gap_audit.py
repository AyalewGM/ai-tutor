"""Texas Grade 3 content-expectation gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

TX_GRADE3_STANDARD_CODES = (
    "3.2A", "3.2B", "3.2C", "3.2D",
    "3.3A", "3.3B", "3.3C", "3.3D", "3.3E", "3.3F", "3.3G", "3.3H",
    "3.4A", "3.4B", "3.4C", "3.4D", "3.4E", "3.4F", "3.4G", "3.4H", "3.4I", "3.4J", "3.4K",
    "3.5A", "3.5B", "3.5C", "3.5D", "3.5E",
    "3.6A", "3.6B", "3.6C", "3.6D", "3.6E",
    "3.7A", "3.7B", "3.7C", "3.7D", "3.7E",
    "3.8A", "3.8B",
    "3.9A", "3.9B", "3.9C", "3.9D", "3.9E", "3.9F",
)


def _c(code: str, skill: str) -> StandardGap:
    return StandardGap("TX", 3, code, GapStatus.COVERED, skill)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("TX", 3, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("TX", 3, code, GapStatus.GAP, rationale=f"gap:{key}")


TX_GRADE3_GAPS = (
    _c("3.2A", "MATH.NS.COMPOSE_DECOMPOSE"),
    _c("3.2B", "MATH.NS.PLACE_VALUE"),
    _c("3.2C", "MATH.NS.ROUNDING"),
    _c("3.2D", "MATH.NS.COMPARE_ORDER"),
    _p("3.3A", "MATH.NF.FRACTION_MEANING", "Fraction meaning exists; strip-diagram and number-line breadth needs depth."),
    _p("3.3B", "MATH.NF.FRACTION_MEANING", "Number-line fractions exist conceptually; specified-point identification needs depth."),
    _c("3.3C", "MATH.NF.FRACTION_MEANING"),
    _p("3.3D", "MATH.NF.FRACTION_MEANING", "Fraction meaning exists; unit-fraction decomposition needs depth."),
    _p("3.3E", "MATH.NF.FRACTION_MEANING", "Partitive contexts exist; pictorial fair-sharing fractions need depth."),
    _c("3.3F", "MATH.NF.EQUIVALENT_FRACTIONS"),
    _p("3.3G", "MATH.NF.EQUIVALENT_FRACTIONS", "Equivalence exists; number-line/area-model iff justification needs depth."),
    _c("3.3H", "MATH.NF.COMPARE"),
    _c("3.4A", "MATH.NS.ADDITION"),
    _c("3.4B", "MATH.NS.ROUNDING"),
    _c("3.4C", "MATH.DEC.MONEY.TOTAL"),
    _c("3.4D", "MATH.NS.MULTIPLICATION"),
    _p("3.4E", "MATH.NS.MULTIPLICATION", "Multiplication models exist; broaden repeated-addition/array/area/number-line representations."),
    _c("3.4F", "MATH.NS.MULTIPLICATION"),
    _c("3.4G", "MATH.NS.MULTIPLICATION"),
    _c("3.4H", "MATH.NS.DIVISION"),
    _p("3.4I", "MATH.NS.FACTORS_MULTIPLES", "Factor/multiple reasoning exists; explicit parity via divisibility rules needs depth."),
    _c("3.4J", "MATH.NS.DIVISION"),
    _c("3.4K", "MATH.NS.MULTIPLICATION"),
    _c("3.5A", "MATH.NS.ADDITION"),
    _p("3.5B", "MATH.NS.MULTIPLICATION", "Word families exist; strip-diagram/equation representation needs depth."),
    _c("3.5C", "MATH.NS.MULTIPLICATION"),
    _c("3.5D", "MATH.NS.MULTIPLICATION"),
    _p("3.5E", "MATH.PATTERN.FUNCTION_RULE", "Input-output rules exist; real-world number-pair tables need elementary depth."),
    _p("3.6A", "MATH.GEO.SHAPES", "Shape classification exists; formal 2D/3D attribute sorting needs depth."),
    _p("3.6B", "MATH.GEO.SHAPES", "Quadrilateral classification exists; hierarchy and non-example drawing need depth."),
    _c("3.6C", "MATH.GEO.MEASURE.AREA"),
    _c("3.6D", "MATH.GEO.MEASURE.AREA"),
    _p("3.6E", "MATH.NF.FRACTION_MEANING", "Fraction meaning exists; equal-area decomposition with noncongruent shapes needs depth."),
    _p("3.7A", "MATH.NF.FRACTION_MEANING", "Fraction number-line work exists; specified eighth/fourth/half distances need depth."),
    _c("3.7B", "MATH.GEO.MEASURE.PERIMETER"),
    _c("3.7C", "MATH.MEAS.TIME.ELAPSED"),
    _p("3.7D", "MATH.MEAS.UNIT_CONVERSION", "Capacity/weight units exist; tool/unit selection decisions need depth."),
    _p("3.7E", "MATH.MEAS.UNIT_CONVERSION", "Capacity/weight units exist; measurement-tool application needs depth."),
    _c("3.8A", "MATH.DATA.ELEMENTARY.REPRESENT"),
    _p("3.8B", "MATH.DATA.ELEMENTARY.COMPARE", "Categorical-data interpretation exists; one/two-step problems across representations need depth."),
    _g("3.9A", "personal-financial-literacy-foundations"),
    _g("3.9B", "personal-financial-literacy-foundations"),
    _g("3.9C", "personal-financial-literacy-foundations"),
    _g("3.9D", "personal-financial-literacy-foundations"),
    _g("3.9E", "personal-financial-literacy-foundations"),
    _g("3.9F", "personal-financial-literacy-foundations"),
)

validate_inventory(TX_GRADE3_STANDARD_CODES, TX_GRADE3_GAPS)
