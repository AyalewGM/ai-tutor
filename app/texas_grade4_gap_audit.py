"""Texas Grade 4 content-expectation gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

TX_GRADE4_STANDARD_CODES = (
    "4.2A", "4.2B", "4.2C", "4.2D", "4.2E", "4.2F", "4.2G", "4.2H",
    "4.3A", "4.3B", "4.3C", "4.3D", "4.3E", "4.3F", "4.3G",
    "4.4A", "4.4B", "4.4C", "4.4D", "4.4E", "4.4F", "4.4G", "4.4H",
    "4.5A", "4.5B", "4.5C", "4.5D",
    "4.6A", "4.6B", "4.6C", "4.6D",
    "4.7A", "4.7B", "4.7C", "4.7D", "4.7E",
    "4.8A", "4.8B", "4.8C",
    "4.9A", "4.9B",
    "4.10A", "4.10B", "4.10C", "4.10D", "4.10E",
)


def _c(code: str, skill: str) -> StandardGap:
    return StandardGap("TX", 4, code, GapStatus.COVERED, skill)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("TX", 4, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("TX", 4, code, GapStatus.GAP, rationale=f"gap:{key}")


TX_GRADE4_GAPS = (
    _c("4.2A", "MATH.NS.PLACE_VALUE"),
    _c("4.2B", "MATH.NS.EXPANDED_FORM"),
    _c("4.2C", "MATH.NS.COMPARE_ORDER"),
    _c("4.2D", "MATH.NS.ROUNDING"),
    _p("4.2E", "MATH.NS.DECIMAL.PLACE_VALUE", "Decimal place value exists; concrete/visual/money models need depth."),
    _c("4.2F", "MATH.NS.DECIMAL.COMPARE"),
    _c("4.2G", "MATH.NS.DECIMAL.CONVERT"),
    _p("4.2H", "MATH.NS.DECIMAL.PLACE_VALUE", "Decimal place value exists; number-line point identification needs depth."),
    _p("4.3A", "MATH.NF.FRACTION_MEANING", "Fraction meaning exists; improper unit-fraction sums need depth."),
    _p("4.3B", "MATH.NF.ADD_SUBTRACT", "Fraction decomposition exists implicitly; multiple same-denominator decompositions need depth."),
    _c("4.3C", "MATH.NF.EQUIVALENT_FRACTIONS"),
    _c("4.3D", "MATH.NF.COMPARE"),
    _c("4.3E", "MATH.NF.ADD_SUBTRACT"),
    _c("4.3F", "MATH.FRAC.ESTIMATE.BENCHMARK"),
    _p("4.3G", "MATH.NS.DECIMAL.CONVERT", "Fraction-decimal conversion exists; shared number-line distance representation needs depth."),
    _c("4.4A", "MATH.NS.DECIMAL.ADD_SUBTRACT"),
    _c("4.4B", "MATH.NS.MULTIPLICATION"),
    _c("4.4C", "MATH.NS.MULTIPLICATION"),
    _c("4.4D", "MATH.NS.MULTIPLICATION"),
    _c("4.4E", "MATH.NS.DIVISION"),
    _c("4.4F", "MATH.NS.DIVISION"),
    _c("4.4G", "MATH.NS.ROUNDING"),
    _c("4.4H", "MATH.NS.DIVISION"),
    _p("4.5A", "MATH.NS.ORDER_OF_OPERATIONS", "Multistep operations exist; strip-diagram/letter-equation representation needs depth."),
    _c("4.5B", "MATH.PATTERN.FUNCTION_RULE"),
    _c("4.5C", "MATH.GEO.MEASURE.PERIMETER"),
    _c("4.5D", "MATH.GEO.MEASURE.AREA"),
    _p("4.6A", "MATH.GEO.SHAPES", "Geometry primitives exist; explicit points/lines/rays/parallel/perpendicular identification needs depth."),
    _p("4.6B", "MATH.GEO.SYMMETRY.REFLECTION", "Reflection/symmetry exists; elementary line-symmetry drawing needs depth."),
    _c("4.6C", "MATH.GEO.TRIANGLES"),
    _p("4.6D", "MATH.GEO.SHAPES", "Shape classification exists; combined line/angle-attribute classification needs depth."),
    _p("4.7A", "MATH.GEO.ANGLES", "Angle families exist; turn/circle-part interpretation needs depth."),
    _p("4.7B", "MATH.GEO.ANGLES", "Angle families exist; degree-as-1/360 conceptual model needs depth."),
    _g("4.7C", "angle-measure-draw-protractor"),
    _g("4.7D", "angle-measure-draw-protractor"),
    _p("4.7E", "MATH.GEO.ANGLES", "Missing-angle reasoning exists; adjacent-angle additive decomposition needs depth."),
    _c("4.8A", "MATH.MEAS.UNIT_CONVERSION"),
    _c("4.8B", "MATH.MEAS.UNIT_CONVERSION"),
    _p("4.8C", "MATH.MEAS.UNIT_CONVERSION", "Measurement operations exist; integrated length/time/volume/mass/money contexts need depth."),
    _p("4.9A", "MATH.DATA.REPRESENTATIONS", "Data representations exist; stem-and-leaf plus fractional marks need depth."),
    _p("4.9B", "MATH.DATA.ELEMENTARY.COMPARE", "Data problems exist; multi-step decimal/fraction data problems need depth."),
    _g("4.10A", "personal-financial-literacy-foundations"),
    _g("4.10B", "personal-financial-literacy-foundations"),
    _g("4.10C", "personal-financial-literacy-foundations"),
    _g("4.10D", "personal-financial-literacy-foundations"),
    _g("4.10E", "personal-financial-literacy-foundations"),
)

validate_inventory(TX_GRADE4_STANDARD_CODES, TX_GRADE4_GAPS)
