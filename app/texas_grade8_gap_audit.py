"""Texas Grade 8 content-expectation gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

TX_GRADE8_STANDARD_CODES = (
    "8.2A", "8.2B", "8.2C", "8.2D",
    "8.3A", "8.3B", "8.3C",
    "8.4A", "8.4B", "8.4C",
    "8.5A", "8.5B", "8.5C", "8.5D", "8.5E", "8.5F", "8.5G", "8.5H", "8.5I",
    "8.6A", "8.6B", "8.6C",
    "8.7A", "8.7B", "8.7C", "8.7D",
    "8.8A", "8.8B", "8.8C", "8.8D",
    "8.9A",
    "8.10A", "8.10B", "8.10C", "8.10D",
    "8.11A", "8.11B", "8.11C",
    "8.12A", "8.12B", "8.12C", "8.12D", "8.12E", "8.12F", "8.12G",
)


def _c(code: str, skill: str) -> StandardGap:
    return StandardGap("TX", 8, code, GapStatus.COVERED, skill)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("TX", 8, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("TX", 8, code, GapStatus.GAP, rationale=f"gap:{key}")


TX_GRADE8_GAPS = (
    _g("8.2A", "irrational-number-concept"),
    _g("8.2B", "irrational-approximation"),
    _c("8.2C", "MATH.NS.SCIENTIFIC_NOTATION"),
    _g("8.2D", "irrational-number-concept"),
    _c("8.3A", "MATH.GEO.SIMILARITY"),
    _p("8.3B", "MATH.GEO.TRANSFORMATIONS", "Dilations exist; coordinate-plane attribute comparison needs depth."),
    _c("8.3C", "MATH.GEO.TRANSFORMATIONS"),
    _p("8.4A", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Slope exists; similar-triangle invariance derivation needs depth."),
    _c("8.4B", "MATH.F.LINEAR.SLOPE_INTERCEPT"),
    _c("8.4C", "MATH.F.LINEAR.SLOPE_INTERCEPT"),
    _c("8.5A", "MATH.F.LINEAR.SLOPE_INTERCEPT"),
    _c("8.5B", "MATH.F.LINEAR.SLOPE_INTERCEPT"),
    _c("8.5C", "MATH.DATA.BIVARIATE"),
    _c("8.5D", "MATH.DATA.LINEAR_MODEL"),
    _c("8.5E", "MATH.RP.PROPORTIONAL.REPRESENT"),
    _c("8.5F", "MATH.F.LINEAR.COMPARE"),
    _p("8.5G", "MATH.F.FUNCTIONS", "Function identification exists; mapping-diagram representation needs depth."),
    _c("8.5H", "MATH.F.LINEAR.COMPARE"),
    _c("8.5I", "MATH.F.LINEAR.SLOPE_INTERCEPT"),
    _c("8.6A", "MATH.GEO.MEASURE.VOLUME"),
    _c("8.6B", "MATH.GEO.MEASURE.VOLUME"),
    _p("8.6C", "MATH.GEO.PYTHAGOREAN", "Pythagorean theorem exists; model/diagram explanation needs depth."),
    _c("8.7A", "MATH.GEO.MEASURE.VOLUME"),
    _c("8.7B", "MATH.GEO.SURFACE_AREA"),
    _c("8.7C", "MATH.GEO.PYTHAGOREAN"),
    _c("8.7D", "MATH.GEO.PYTHAGOREAN"),
    _c("8.8A", "MATH.EE.EQUATION.MULTISTEP"),
    _p("8.8B", "MATH.EE.EQUATION.MULTISTEP", "Equation solving exists; learner-generated real-world problems need depth."),
    _c("8.8C", "MATH.EE.EQUATION.MULTISTEP"),
    _c("8.8D", "MATH.GEO.ANGLES"),
    _c("8.9A", "MATH.EE.SYSTEMS"),
    _c("8.10A", "MATH.GEO.TRANSFORMATIONS"),
    _c("8.10B", "MATH.GEO.CONGRUENCE"),
    _c("8.10C", "MATH.GEO.TRANSFORMATIONS"),
    _p("8.10D", "MATH.GEO.SIMILARITY", "Dilation scale effects exist; integrated linear/area measurement modeling needs depth."),
    _c("8.11A", "MATH.DATA.BIVARIATE"),
    _g("8.11B", "mean-absolute-deviation"),
    _c("8.11C", "MATH.DATA.SAMPLING"),
    _g("8.12A", "personal-financial-literacy-foundations"),
    _g("8.12B", "personal-financial-literacy-foundations"),
    _g("8.12C", "personal-financial-literacy-foundations"),
    _g("8.12D", "personal-financial-literacy-foundations"),
    _g("8.12E", "personal-financial-literacy-foundations"),
    _g("8.12F", "personal-financial-literacy-foundations"),
    _g("8.12G", "personal-financial-literacy-foundations"),
)

validate_inventory(TX_GRADE8_STANDARD_CODES, TX_GRADE8_GAPS)
