"""Texas Grade 1 content-expectation gap audit.

The seven §111.3(b)(1) mathematical process expectations are cross-cutting
practice requirements, not content skills, and are tracked outside this
content-to-canonical inventory. Sections (2)-(9) are included, including
Texas personal financial literacy expectations.
"""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

TX_GRADE1_STANDARD_CODES = (
    "1.2A", "1.2B", "1.2C", "1.2D", "1.2E", "1.2F", "1.2G",
    "1.3A", "1.3B", "1.3C", "1.3D", "1.3E", "1.3F",
    "1.4A", "1.4B", "1.4C",
    "1.5A", "1.5B", "1.5C", "1.5D", "1.5E", "1.5F", "1.5G",
    "1.6A", "1.6B", "1.6C", "1.6D", "1.6E", "1.6F", "1.6G", "1.6H",
    "1.7A", "1.7B", "1.7C", "1.7D", "1.7E",
    "1.8A", "1.8B", "1.8C",
    "1.9A", "1.9B", "1.9C", "1.9D",
)


def _c(code: str, skill: str) -> StandardGap:
    return StandardGap("TX", 1, code, GapStatus.COVERED, skill)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("TX", 1, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("TX", 1, code, GapStatus.GAP, rationale=f"gap:{key}")


TX_GRADE1_GAPS = (
    _p("1.2A", "MATH.NS.COUNTING", "Counting exists; structured-arrangement subitizing needs depth."),
    _c("1.2B", "MATH.NS.COMPOSE_DECOMPOSE"),
    _c("1.2C", "MATH.NS.EXPANDED_FORM"),
    _c("1.2D", "MATH.NS.COMPARE_ORDER"),
    _c("1.2E", "MATH.NS.COMPARE_ORDER"),
    _c("1.2F", "MATH.NS.COMPARE_ORDER"),
    _c("1.2G", "MATH.NS.COMPARE_ORDER"),
    _p("1.3A", "MATH.NS.ADDITION", "Addition exists; concrete/pictorial tens-plus-ones models need Grade-1 depth."),
    _c("1.3B", "MATH.NS.ADDITION"),
    _p("1.3C", "MATH.NS.ADDITION", "Addition exists; composing ten from multiple addends needs explicit depth."),
    _p("1.3D", "MATH.NS.ADDITION", "Facts exist; make-ten/decomposition strategy evidence needs depth."),
    _p("1.3E", "MATH.NS.ADDITION", "Deterministic solutions exist; spoken/pictorial strategy explanation needs depth."),
    _p("1.3F", "MATH.NS.ADDITION", "Word families exist; learner-generated situations from equations need depth."),
    _p("1.4A", "MATH.DEC.MONEY.TOTAL", "Money arithmetic exists; elementary U.S.-coin identity/value relationships need depth."),
    _p("1.4B", "MATH.DEC.MONEY.TOTAL", "Money arithmetic exists; cent-symbol representation needs elementary depth."),
    _p("1.4C", "MATH.DEC.MONEY.TOTAL", "Money arithmetic exists; coin-collection skip-count representations need depth."),
    _c("1.5A", "MATH.NS.COUNTING"),
    _c("1.5B", "MATH.NS.COUNTING"),
    _c("1.5C", "MATH.NS.PLACE_VALUE"),
    _c("1.5D", "MATH.NS.ADDITION"),
    _p("1.5E", "MATH.EE.EQUATION.ONE", "Equation truth exists; elementary equal-sign relational meaning needs depth."),
    _c("1.5F", "MATH.NS.ADDITION"),
    _c("1.5G", "MATH.NS.PROPERTIES"),
    _c("1.6A", "MATH.GEO.SHAPES"),
    _p("1.6B", "MATH.GEO.SHAPES", "Shape classification exists; defining versus nondefining attributes need depth."),
    _p("1.6C", "MATH.GEO.SHAPES", "Shape families exist; learner construction of specified shapes needs depth."),
    _p("1.6D", "MATH.GEO.SHAPES", "Shape recognition exists; formal attribute language needs elementary depth."),
    _p("1.6E", "MATH.GEO.SHAPES", "Shape families exist; three-dimensional solid attributes need depth."),
    _p("1.6F", "MATH.GEO.SHAPES", "Shape families exist; composing target shapes in multiple ways needs depth."),
    _p("1.6G", "MATH.NF.FRACTION_MEANING", "Fraction meaning exists; fair-share halves/fourths shape partitioning needs depth."),
    _p("1.6H", "MATH.NF.FRACTION_MEANING", "Fraction meaning exists; examples/non-examples of halves and fourths need depth."),
    _p("1.7A", "MATH.MEAS.LENGTH.METRIC", "Length exists; direct measuring-tool use needs elementary depth."),
    _p("1.7B", "MATH.MEAS.LENGTH.METRIC", "Length exists; unit iteration with no gaps/overlaps needs depth."),
    _p("1.7C", "MATH.MEAS.UNIT_CONVERSION", "Measurement exists; same-object different-unit reasoning needs depth."),
    _p("1.7D", "MATH.MEAS.LENGTH.METRIC", "Length exists; nearest-whole-unit reporting needs elementary depth."),
    _c("1.7E", "MATH.MEAS.TIME"),
    _p("1.8A", "MATH.DATA.ELEMENTARY.REPRESENT", "Data representations exist; learner collection/sorting into categories needs depth."),
    _c("1.8B", "MATH.DATA.ELEMENTARY.REPRESENT"),
    _c("1.8C", "MATH.DATA.ELEMENTARY.COMPARE"),
    _g("1.9A", "personal-financial-literacy-foundations"),
    _g("1.9B", "personal-financial-literacy-foundations"),
    _g("1.9C", "personal-financial-literacy-foundations"),
    _g("1.9D", "personal-financial-literacy-foundations"),
)

validate_inventory(TX_GRADE1_STANDARD_CODES, TX_GRADE1_GAPS)
