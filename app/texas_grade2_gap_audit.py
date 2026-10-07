"""Texas Grade 2 content-expectation gap audit.

§111.4(b)(1) process expectations are tracked as cross-cutting practices rather
than forced into one canonical skill. Sections (2)-(11) are the content inventory.
"""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

TX_GRADE2_STANDARD_CODES = (
    "2.2A", "2.2B", "2.2C", "2.2D", "2.2E", "2.2F",
    "2.3A", "2.3B", "2.3C", "2.3D",
    "2.4A", "2.4B", "2.4C", "2.4D",
    "2.5A", "2.5B",
    "2.6A", "2.6B",
    "2.7A", "2.7B", "2.7C",
    "2.8A", "2.8B", "2.8C", "2.8D", "2.8E",
    "2.9A", "2.9B", "2.9C", "2.9D", "2.9E", "2.9F", "2.9G",
    "2.10A", "2.10B", "2.10C", "2.10D",
    "2.11A", "2.11B", "2.11C", "2.11D", "2.11E", "2.11F",
)


def _c(code: str, skill: str) -> StandardGap:
    return StandardGap("TX", 2, code, GapStatus.COVERED, skill)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("TX", 2, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("TX", 2, code, GapStatus.GAP, rationale=f"gap:{key}")


TX_GRADE2_GAPS = (
    _c("2.2A", "MATH.NS.COMPOSE_DECOMPOSE"),
    _c("2.2B", "MATH.NS.EXPANDED_FORM"),
    _c("2.2C", "MATH.NS.COMPARE_ORDER"),
    _c("2.2D", "MATH.NS.COMPARE_ORDER"),
    _c("2.2E", "MATH.NS.NUMBER_LINE"),
    _c("2.2F", "MATH.NS.NUMBER_LINE"),
    _p("2.3A", "MATH.NF.FRACTION_MEANING", "Fraction meaning exists; halves/fourths/eighths partitioning needs depth."),
    _p("2.3B", "MATH.NF.COMPARE", "Fraction comparison exists; inverse part-size reasoning needs elementary depth."),
    _p("2.3C", "MATH.NF.FRACTION_MEANING", "Fraction meaning exists; counting parts beyond one whole with models needs depth."),
    _p("2.3D", "MATH.NF.FRACTION_MEANING", "Fraction meaning exists; examples/non-examples of halves/fourths/eighths need depth."),
    _c("2.4A", "MATH.NS.ADDITION"),
    _p("2.4B", "MATH.NS.ADDITION", "Operations exist; four-addend mental/place-value strategy evidence needs depth."),
    _c("2.4C", "MATH.NS.ADDITION"),
    _p("2.4D", "MATH.NS.ADDITION", "Word families exist; learner-generated situations from number sentences need depth."),
    _c("2.5A", "MATH.DEC.MONEY.TOTAL"),
    _p("2.5B", "MATH.DEC.MONEY.TOTAL", "Money arithmetic exists; cent/dollar/decimal notation for coin collections needs depth."),
    _p("2.6A", "MATH.NS.MULTIPLICATION", "Equal-group multiplication exists; concrete contextual modeling needs Grade-2 depth."),
    _p("2.6B", "MATH.NS.DIVISION", "Partitive division exists; concrete equal-set modeling needs Grade-2 depth."),
    _p("2.7A", "MATH.NS.FACTORS_MULTIPLES", "Parity-related number structure exists; object-pairing odd/even models need depth."),
    _c("2.7B", "MATH.NS.PLACE_VALUE"),
    _c("2.7C", "MATH.NS.ADDITION"),
    _p("2.8A", "MATH.GEO.SHAPES", "Shape families exist; learner construction from specified attributes needs depth."),
    _p("2.8B", "MATH.GEO.SHAPES", "Solid classification exists; formal three-dimensional attribute language needs depth."),
    _p("2.8C", "MATH.GEO.SHAPES", "Polygon classification exists; elementary side/vertex sorting through 12 sides needs depth."),
    _p("2.8D", "MATH.GEO.SHAPES", "Shape families exist; composing 2D/3D targets from properties needs depth."),
    _p("2.8E", "MATH.GEO.SHAPES", "Shape families exist; decomposition and resulting-part identification needs depth."),
    _p("2.9A", "MATH.MEAS.LENGTH.CUSTOMARY", "Length exists; concrete standard-unit measurement needs elementary depth."),
    _p("2.9B", "MATH.MEAS.UNIT_CONVERSION", "Measurement exists; inverse unit-size/count relationship needs depth."),
    _c("2.9C", "MATH.NS.NUMBER_LINE"),
    _p("2.9D", "MATH.MEAS.LENGTH.CUSTOMARY", "Length exists; physical ruler/yardstick/meter-stick reading needs depth."),
    _p("2.9E", "MATH.MEAS.LENGTH.CUSTOMARY", "Length and estimation exist; integrated length problem solving needs depth."),
    _p("2.9F", "MATH.GEO.MEASURE.AREA", "Area exists; square-unit covering with no gaps/overlaps needs elementary depth."),
    _p("2.9G", "MATH.MEAS.TIME", "Time exists; one-minute analog/digital reading plus a.m./p.m. needs depth."),
    _p("2.10A", "MATH.DATA.ELEMENTARY.REPRESENT", "Bar/picture graphs exist; explicit visual-unit meaning needs depth."),
    _c("2.10B", "MATH.DATA.ELEMENTARY.REPRESENT"),
    _p("2.10C", "MATH.DATA.ELEMENTARY.COMPARE", "Graph comparison exists; embedded one-step operation problems need depth."),
    _p("2.10D", "MATH.DATA.ELEMENTARY.COMPARE", "Graph interpretation exists; prediction from graph data needs depth."),
    _g("2.11A", "personal-financial-literacy-foundations"),
    _g("2.11B", "personal-financial-literacy-foundations"),
    _g("2.11C", "personal-financial-literacy-foundations"),
    _g("2.11D", "personal-financial-literacy-foundations"),
    _g("2.11E", "personal-financial-literacy-foundations"),
    _g("2.11F", "personal-financial-literacy-foundations"),
)

validate_inventory(TX_GRADE2_STANDARD_CODES, TX_GRADE2_GAPS)
