"""Texas Grade 6 content-expectation gap audit."""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

TX_GRADE6_STANDARD_CODES = (
    "6.2A", "6.2B", "6.2C", "6.2D", "6.2E",
    "6.3A", "6.3B", "6.3C", "6.3D", "6.3E",
    "6.4A", "6.4B", "6.4C", "6.4D", "6.4E", "6.4F", "6.4G", "6.4H",
    "6.5A", "6.5B", "6.5C",
    "6.6A", "6.6B", "6.6C",
    "6.7A", "6.7B", "6.7C", "6.7D",
    "6.8A", "6.8B", "6.8C", "6.8D",
    "6.9A", "6.9B", "6.9C",
    "6.10A", "6.10B",
    "6.11A",
    "6.12A", "6.12B", "6.12C", "6.12D",
    "6.13A", "6.13B",
    "6.14A", "6.14B", "6.14C", "6.14D", "6.14E", "6.14F", "6.14G", "6.14H",
)


def _c(code: str, skill: str) -> StandardGap:
    return StandardGap("TX", 6, code, GapStatus.COVERED, skill)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("TX", 6, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("TX", 6, code, GapStatus.GAP, rationale=f"gap:{key}")


TX_GRADE6_GAPS = (
    _p("6.2A", "MATH.NS.INTEGERS", "Integer/rational skills exist; explicit nested number-set classification needs depth."),
    _c("6.2B", "MATH.NS.INTEGERS"),
    _c("6.2C", "MATH.NS.RATIONAL.COMPARE"),
    _c("6.2D", "MATH.NS.RATIONAL.COMPARE"),
    _p("6.2E", "MATH.NF.DIVIDE", "Fraction division exists; explicit fraction-notation-as-division equivalence needs depth."),
    _c("6.3A", "MATH.NF.DIVIDE"),
    _p("6.3B", "MATH.NF.MULTIPLY", "Fraction multiplication exists; product-size increase/decrease reasoning needs depth."),
    _p("6.3C", "MATH.NS.INTEGERS", "Integer operations exist; concrete-model-to-algorithm bridge needs depth."),
    _c("6.3D", "MATH.NS.INTEGERS"),
    _p("6.3E", "MATH.NS.DECIMAL.MULTIPLY", "Positive rational operations exist across fraction/decimal skills; integrated fluency needs depth."),
    _c("6.4A", "MATH.PATTERN.NUMERIC"),
    _p("6.4B", "MATH.RP.RATIO.EQUIVALENT", "Ratio/rate skills exist; qualitative prediction/comparison contexts need depth."),
    _c("6.4C", "MATH.RP.RATIO.INTERPRET"),
    _c("6.4D", "MATH.RP.RATE.UNIT"),
    _p("6.4E", "MATH.RP.PERCENT.APPLICATIONS", "Percent/fraction/decimal conversion exists; concrete representation breadth needs depth."),
    _p("6.4F", "MATH.RP.PERCENT.APPLICATIONS", "Benchmark percents exist conceptually; grid/strip/number-line representations need depth."),
    _c("6.4G", "MATH.NS.DECIMAL.CONVERT"),
    _c("6.4H", "MATH.MEAS.UNIT_CONVERSION"),
    _c("6.5A", "MATH.RP.RATIO.EQUIVALENT"),
    _c("6.5B", "MATH.RP.PERCENT.APPLICATIONS"),
    _c("6.5C", "MATH.NS.DECIMAL.CONVERT"),
    _p("6.6A", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Variable relationships exist; independent/dependent identification from tables/graphs needs depth."),
    _p("6.6B", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Linear equations exist; equation-from-table dependency needs depth."),
    _p("6.6C", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Linear representations exist; y=kx versus y=x+b multi-representation depth remains."),
    _c("6.7A", "MATH.NS.ORDER_OF_OPERATIONS"),
    _p("6.7B", "MATH.EE.EXPR", "Expressions exist; expression-versus-equation classification needs depth."),
    _p("6.7C", "MATH.EE.EXPR", "Equivalent expressions exist; concrete/pictorial equivalence evidence needs depth."),
    _c("6.7D", "MATH.NS.PROPERTIES"),
    _c("6.8A", "MATH.GEO.TRIANGLES"),
    _p("6.8B", "MATH.GEO.MEASURE.AREA", "Area formulas exist; decomposition-based derivation needs depth."),
    _p("6.8C", "MATH.GEO.MEASURE.AREA", "Area/volume exist; equation-writing from geometry contexts needs depth."),
    _c("6.8D", "MATH.GEO.MEASURE.AREA"),
    _c("6.9A", "MATH.EE.EQUATION.ONE"),
    _c("6.9B", "MATH.EE.INEQUALITY.ONE"),
    _p("6.9C", "MATH.EE.EQUATION.ONE", "One-step equations exist; learner-generated real-world problems need depth."),
    _c("6.10A", "MATH.EE.EQUATION.ONE"),
    _p("6.10B", "MATH.EE.EQUATION.ONE", "Solving exists; truth-testing specified candidate values needs depth."),
    _c("6.11A", "MATH.GEO.COORDINATE"),
    _p("6.12A", "MATH.DATA.REPRESENTATIONS", "Data representations exist; explicit box-plot and stem-and-leaf breadth needs depth."),
    _p("6.12B", "MATH.DATA.SPREAD", "Center/spread exists; distribution-shape interpretation needs depth."),
    _c("6.12C", "MATH.DATA.CENTER"),
    _p("6.12D", "MATH.DATA.FREQUENCY", "Relative frequency exists; categorical percent-bar summaries need depth."),
    _p("6.13A", "MATH.DATA.REPRESENTATIONS", "Numeric-data interpretation exists; broaden across all required plots."),
    _g("6.13B", "statistical-question-variability"),
    _g("6.14A", "personal-financial-literacy-foundations"),
    _g("6.14B", "personal-financial-literacy-foundations"),
    _g("6.14C", "personal-financial-literacy-foundations"),
    _g("6.14D", "personal-financial-literacy-foundations"),
    _g("6.14E", "personal-financial-literacy-foundations"),
    _g("6.14F", "personal-financial-literacy-foundations"),
    _g("6.14G", "personal-financial-literacy-foundations"),
    _g("6.14H", "personal-financial-literacy-foundations"),
)

validate_inventory(TX_GRADE6_STANDARD_CODES, TX_GRADE6_GAPS)
