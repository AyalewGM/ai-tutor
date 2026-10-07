"""California Grade 7 authoritative gap audit.

Identifiers are from the California Common Core State Standards for Mathematics
(2013 electronic edition). Classifications are proposed, fail-closed audit data.
"""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

CA_GRADE7_STANDARD_CODES = (
    "7.RP.1", "7.RP.2", "7.RP.3",
    "7.NS.1", "7.NS.2", "7.NS.3",
    "7.EE.1", "7.EE.2", "7.EE.3", "7.EE.4",
    "7.G.1", "7.G.2", "7.G.3", "7.G.4", "7.G.5", "7.G.6",
    "7.SP.1", "7.SP.2", "7.SP.3", "7.SP.4", "7.SP.5", "7.SP.6", "7.SP.7", "7.SP.8",
)


def _item(
    code: str,
    status: GapStatus,
    skill: str | None = None,
    rationale: str | None = None,
) -> StandardGap:
    return StandardGap("CA", 7, code, status, skill, rationale)


CA_GRADE7_GAPS = (
    _item("7.RP.1", GapStatus.COVERED, "MATH.RP.RATE.UNIT"),
    _item("7.RP.2", GapStatus.COVERED, "MATH.RP.PROPORTIONAL.REPRESENT"),
    _item("7.RP.3", GapStatus.COVERED, "MATH.RP.PERCENT.APPLICATIONS"),
    _item("7.NS.1", GapStatus.COVERED, "MATH.NS.RATIONAL.OPERATIONS"),
    _item("7.NS.2", GapStatus.COVERED, "MATH.NS.RATIONAL.OPERATIONS"),
    _item(
        "7.NS.3",
        GapStatus.PARTIAL,
        "MATH.NS.RATIONAL.OPERATIONS",
        "Four rational operations exist; broaden multistep real-world application depth.",
    ),
    _item(
        "7.EE.1",
        GapStatus.PARTIAL,
        "MATH.EE.EXPR",
        "Expression operations exist; rational-coefficient factoring/expansion needs depth.",
    ),
    _item(
        "7.EE.2",
        GapStatus.PARTIAL,
        "MATH.EE.EXPR",
        "Equivalent-form manipulation exists; contextual interpretation needs depth.",
    ),
    _item(
        "7.EE.3",
        GapStatus.PARTIAL,
        "MATH.EE.EQUATION.MULTISTEP",
        "Multistep solving exists; mixed rational-form estimation contexts need depth.",
    ),
    _item(
        "7.EE.4",
        GapStatus.PARTIAL,
        "MATH.EE.INEQUALITY.MULTISTEP",
        "Equation and inequality families exist; contextual construction needs depth.",
    ),
    _item("7.G.1", GapStatus.COVERED, "MATH.GEO.SCALE_DRAWING"),
    _item("7.G.2", GapStatus.GAP, rationale="gap:geometric-construction-conditions"),
    _item("7.G.3", GapStatus.GAP, rationale="gap:solid-cross-sections"),
    _item("7.G.4", GapStatus.COVERED, "MATH.GEO.CIRCLES"),
    _item("7.G.5", GapStatus.COVERED, "MATH.GEO.ANGLES"),
    _item("7.G.6", GapStatus.COVERED, "MATH.GEO.SURFACE_AREA"),
    _item("7.SP.1", GapStatus.COVERED, "MATH.DATA.SAMPLING"),
    _item(
        "7.SP.2",
        GapStatus.PARTIAL,
        "MATH.DATA.SAMPLING",
        "Representative sampling exists; repeated-sample population inference needs depth.",
    ),
    _item(
        "7.SP.3",
        GapStatus.PARTIAL,
        "MATH.DATA.REPRESENTATIONS",
        "Distribution representations exist; informal overlap/visual comparison needs depth.",
    ),
    _item(
        "7.SP.4",
        GapStatus.PARTIAL,
        "MATH.DATA.CENTER",
        "Center/spread exist; comparative population inference needs integrated depth.",
    ),
    _item("7.SP.5", GapStatus.COVERED, "MATH.PROB.SIMPLE"),
    _item("7.SP.6", GapStatus.COVERED, "MATH.PROB.EXPERIMENTAL"),
    _item(
        "7.SP.7",
        GapStatus.PARTIAL,
        "MATH.PROB.EXPERIMENTAL",
        "Experimental probability exists; explicit model-vs-frequency comparison needs depth.",
    ),
    _item("7.SP.8", GapStatus.COVERED, "MATH.PROB.COMPOUND"),
)

validate_inventory(CA_GRADE7_STANDARD_CODES, CA_GRADE7_GAPS)
