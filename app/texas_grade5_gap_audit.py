"""Texas Grade 5 content-expectation gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

TX_GRADE5_STANDARD_CODES = (
    "5.2A", "5.2B", "5.2C",
    "5.3A", "5.3B", "5.3C", "5.3D", "5.3E", "5.3F", "5.3G", "5.3H", "5.3I", "5.3J", "5.3K", "5.3L",
    "5.4A", "5.4B", "5.4C", "5.4D", "5.4E", "5.4F", "5.4G", "5.4H",
    "5.5A",
    "5.6A", "5.6B",
    "5.7A",
    "5.8A", "5.8B", "5.8C",
    "5.9A", "5.9B", "5.9C",
    "5.10A", "5.10B", "5.10C", "5.10D", "5.10E", "5.10F",
)


def _c(code: str, skill: str) -> StandardGap:
    return StandardGap("TX", 5, code, GapStatus.COVERED, skill)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("TX", 5, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("TX", 5, code, GapStatus.GAP, rationale=f"gap:{key}")


TX_GRADE5_GAPS = (
    _c("5.2A", "MATH.NS.DECIMAL.PLACE_VALUE"),
    _c("5.2B", "MATH.NS.DECIMAL.COMPARE"),
    _c("5.2C", "MATH.NS.ROUNDING"),
    _c("5.3A", "MATH.DEC.ESTIMATE"),
    _c("5.3B", "MATH.NS.MULTIPLICATION"),
    _c("5.3C", "MATH.NS.DIVISION"),
    _p("5.3D", "MATH.NS.DECIMAL.MULTIPLY", "Decimal multiplication exists; object/area-model representation needs depth."),
    _c("5.3E", "MATH.NS.DECIMAL.MULTIPLY"),
    _p("5.3F", "MATH.NS.DECIMAL.DIVIDE", "Decimal division exists; object/area-model quotient representation needs depth."),
    _c("5.3G", "MATH.NS.DECIMAL.DIVIDE"),
    _p("5.3H", "MATH.NF.ADD_SUBTRACT", "Unlike-denominator operations exist; object/pictorial model breadth needs depth."),
    _p("5.3I", "MATH.NF.MULTIPLY", "Fraction multiplication exists; whole-number-by-fraction visual models need depth."),
    _p("5.3J", "MATH.NF.DIVIDE", "Unit-fraction division exists; object/area-model representation needs depth."),
    _c("5.3K", "MATH.NF.ADD_SUBTRACT"),
    _c("5.3L", "MATH.NF.DIVIDE"),
    _c("5.4A", "MATH.NS.FACTORS_MULTIPLES"),
    _c("5.4B", "MATH.NS.ORDER_OF_OPERATIONS"),
    _p("5.4C", "MATH.PATTERN.FUNCTION_RULE", "Function rules exist; graphing y=ax and y=x+a numerical patterns needs depth."),
    _c("5.4D", "MATH.PATTERN.NUMERIC"),
    _c("5.4E", "MATH.NS.ORDER_OF_OPERATIONS"),
    _c("5.4F", "MATH.NS.ORDER_OF_OPERATIONS"),
    _p("5.4G", "MATH.GEO.MEASURE.VOLUME", "Prism volume exists; formula development from concrete/pictorial models needs depth."),
    _p("5.4H", "MATH.GEO.MEASURE.VOLUME", "Area/perimeter/volume exist; integrated mixed-measurement problems need depth."),
    _p("5.5A", "MATH.GEO.SHAPES", "Shape classification exists; explicit hierarchy graphic organizers need depth."),
    _p("5.6A", "MATH.GEO.MEASURE.VOLUME", "Volume exists; unit-cube packing meaning needs explicit depth."),
    _p("5.6B", "MATH.GEO.MEASURE.VOLUME", "Prism volume exists; layers-times-base-unit-cubes reasoning needs depth."),
    _c("5.7A", "MATH.MEAS.UNIT_CONVERSION"),
    _p("5.8A", "MATH.GEO.COORDINATE", "Coordinate skills exist; formal first-quadrant axis/origin attribute language needs depth."),
    _p("5.8B", "MATH.GEO.COORDINATE", "Coordinate plotting exists; procedural first-quadrant explanation needs depth."),
    _p("5.8C", "MATH.GEO.COORDINATE", "Coordinate work exists; contextual points from patterns/tables need depth."),
    _p("5.9A", "MATH.DATA.REPRESENTATIONS", "Representations exist; combined categorical/numerical stem-and-leaf breadth needs depth."),
    _c("5.9B", "MATH.DATA.BIVARIATE"),
    _p("5.9C", "MATH.DATA.ELEMENTARY.COMPARE", "Data problems exist; multi-representation one/two-step breadth needs depth."),
    _g("5.10A", "personal-financial-literacy-foundations"),
    _g("5.10B", "personal-financial-literacy-foundations"),
    _g("5.10C", "personal-financial-literacy-foundations"),
    _g("5.10D", "personal-financial-literacy-foundations"),
    _g("5.10E", "personal-financial-literacy-foundations"),
    _g("5.10F", "personal-financial-literacy-foundations"),
)

validate_inventory(TX_GRADE5_STANDARD_CODES, TX_GRADE5_GAPS)
