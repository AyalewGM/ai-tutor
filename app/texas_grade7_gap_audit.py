"""Texas Grade 7 content-expectation gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

TX_GRADE7_STANDARD_CODES = (
    "7.2A",
    "7.3A", "7.3B",
    "7.4A", "7.4B", "7.4C", "7.4D", "7.4E",
    "7.5A", "7.5B", "7.5C",
    "7.6A", "7.6B", "7.6C", "7.6D", "7.6E", "7.6F", "7.6G", "7.6H", "7.6I",
    "7.7A",
    "7.8A", "7.8B", "7.8C",
    "7.9A", "7.9B", "7.9C", "7.9D",
    "7.10A", "7.10B", "7.10C",
    "7.11A", "7.11B", "7.11C",
    "7.12A", "7.12B", "7.12C",
    "7.13A", "7.13B", "7.13C", "7.13D", "7.13E", "7.13F",
)


def _c(code: str, skill: str) -> StandardGap:
    return StandardGap("TX", 7, code, GapStatus.COVERED, skill)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("TX", 7, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("TX", 7, code, GapStatus.GAP, rationale=f"gap:{key}")


TX_GRADE7_GAPS = (
    _p("7.2A", "MATH.NS.RATIONAL.OPERATIONS", "Rational numbers exist; nested set/subset visualization needs depth."),
    _c("7.3A", "MATH.NS.RATIONAL.OPERATIONS"),
    _p("7.3B", "MATH.NS.RATIONAL.OPERATIONS", "Rational operations exist; broaden contextual multistep applications."),
    _p("7.4A", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Rate/slope exists; constant-rate multi-representation breadth needs depth."),
    _c("7.4B", "MATH.RP.RATE.UNIT"),
    _c("7.4C", "MATH.RP.PROPORTIONAL.REPRESENT"),
    _c("7.4D", "MATH.RP.PERCENT.APPLICATIONS"),
    _c("7.4E", "MATH.MEAS.UNIT_CONVERSION"),
    _c("7.5A", "MATH.GEO.SIMILARITY"),
    _p("7.5B", "MATH.GEO.CIRCLES", "Circle relationships exist; explicit derivation of pi as circumference/diameter needs depth."),
    _c("7.5C", "MATH.GEO.SCALE_DRAWING"),
    _p("7.6A", "MATH.PROB.COMPOUND", "Compound probability exists; explicit list/tree sample-space representation needs depth."),
    _p("7.6B", "MATH.PROB.COMPOUND", "Probability exists; simulation selection with/without technology needs depth."),
    _c("7.6C", "MATH.PROB.EXPERIMENTAL"),
    _c("7.6D", "MATH.PROB.COMPOUND"),
    _p("7.6E", "MATH.PROB.SIMPLE", "Simple probability exists; complement relationship needs explicit depth."),
    _c("7.6F", "MATH.DATA.SAMPLING"),
    _p("7.6G", "MATH.DATA.REPRESENTATIONS", "Data representations exist; circle-graph part-to-whole/part-to-part problem depth remains."),
    _c("7.6H", "MATH.PROB.EXPERIMENTAL"),
    _c("7.6I", "MATH.PROB.THEORY.VS_EXPERIMENT"),
    _c("7.7A", "MATH.F.LINEAR.SLOPE_INTERCEPT"),
    _p("7.8A", "MATH.GEO.MEASURE.VOLUME", "Prism/pyramid volume exists; one-third formula relationship modeling needs depth."),
    _p("7.8B", "MATH.GEO.MEASURE.VOLUME", "Volume exists; triangular-prism/pyramid symbolic relationship needs depth."),
    _p("7.8C", "MATH.GEO.CIRCLES", "Circle formulas exist; model-based derivation of circumference/area needs depth."),
    _p("7.9A", "MATH.GEO.MEASURE.VOLUME", "Volume exists; broaden rectangular/triangular pyramid applications."),
    _c("7.9B", "MATH.GEO.CIRCLES"),
    _p("7.9C", "MATH.GEO.MEASURE.AREA", "Composite area exists; semicircle/quarter-circle combinations need depth."),
    _p("7.9D", "MATH.GEO.SURFACE_AREA", "Surface area exists; prism/pyramid net breadth needs depth."),
    _c("7.10A", "MATH.EE.INEQUALITY.MULTISTEP"),
    _c("7.10B", "MATH.EE.INEQUALITY.MULTISTEP"),
    _p("7.10C", "MATH.EE.EQUATION.MULTISTEP", "Two-step equations exist; learner-generated real-world problems need depth."),
    _c("7.11A", "MATH.EE.EQUATION.MULTISTEP"),
    _p("7.11B", "MATH.EE.EQUATION.MULTISTEP", "Solving exists; candidate-value truth testing needs depth."),
    _c("7.11C", "MATH.GEO.ANGLES"),
    _p("7.12A", "MATH.DATA.REPRESENTATIONS", "Dot/box plots exist; explicit two-group shape/center/spread comparison needs depth."),
    _c("7.12B", "MATH.DATA.SAMPLING"),
    _p("7.12C", "MATH.DATA.SAMPLING", "Sampling exists; comparative inference between two populations needs depth."),
    _g("7.13A", "personal-financial-literacy-foundations"),
    _g("7.13B", "personal-financial-literacy-foundations"),
    _g("7.13C", "personal-financial-literacy-foundations"),
    _g("7.13D", "personal-financial-literacy-foundations"),
    _g("7.13E", "personal-financial-literacy-foundations"),
    _g("7.13F", "personal-financial-literacy-foundations"),
)

validate_inventory(TX_GRADE7_STANDARD_CODES, TX_GRADE7_GAPS)
