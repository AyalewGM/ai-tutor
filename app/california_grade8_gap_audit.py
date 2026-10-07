"""California Grade 8 authoritative gap audit.

Identifiers are from the California Common Core State Standards for Mathematics
(2013 electronic edition). This is a proposed mapping audit, not publication or
a state-grade completion claim.
"""

from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

CA_GRADE8_STANDARD_CODES = (
    "8.NS.1", "8.NS.2",
    "8.EE.1", "8.EE.2", "8.EE.3", "8.EE.4", "8.EE.5", "8.EE.6", "8.EE.7", "8.EE.8",
    "8.F.1", "8.F.2", "8.F.3", "8.F.4", "8.F.5",
    "8.G.1", "8.G.2", "8.G.3", "8.G.4", "8.G.5", "8.G.6", "8.G.7", "8.G.8", "8.G.9",
    "8.SP.1", "8.SP.2", "8.SP.3", "8.SP.4",
)


def _item(
    code: str,
    status: GapStatus,
    skill: str | None = None,
    rationale: str | None = None,
) -> StandardGap:
    return StandardGap("CA", 8, code, status, skill, rationale)


CA_GRADE8_GAPS = (
    _item("8.NS.1", GapStatus.GAP, rationale="gap:irrational-number-concept"),
    _item("8.NS.2", GapStatus.GAP, rationale="gap:irrational-approximation"),
    _item(
        "8.EE.1",
        GapStatus.PARTIAL,
        "MATH.NS.EXPONENTS",
        "Existing exponent families need full integer-exponent law depth.",
    ),
    _item(
        "8.EE.2",
        GapStatus.PARTIAL,
        "MATH.NS.ROOTS",
        "Perfect roots exist; equation-solution and irrational-root depth remains.",
    ),
    _item(
        "8.EE.3",
        GapStatus.PARTIAL,
        "MATH.NS.SCIENTIFIC_NOTATION",
        "Large-number conversion exists; very-small quantities and magnitude comparison need depth.",
    ),
    _item(
        "8.EE.4",
        GapStatus.PARTIAL,
        "MATH.NS.SCIENTIFIC_NOTATION",
        "Multiplication exists; complete operations and unit-selection depth remains.",
    ),
    _item("8.EE.5", GapStatus.COVERED, "MATH.RP.PROPORTIONAL.REPRESENT"),
    _item(
        "8.EE.6",
        GapStatus.PARTIAL,
        "MATH.F.LINEAR.SLOPE_INTERCEPT",
        "Slope and line equations exist; similar-triangle justification needs explicit depth.",
    ),
    _item("8.EE.7", GapStatus.COVERED, "MATH.EE.EQUATION.MULTISTEP"),
    _item("8.EE.8", GapStatus.COVERED, "MATH.EE.SYSTEMS"),
    _item("8.F.1", GapStatus.COVERED, "MATH.F.FUNCTIONS"),
    _item("8.F.2", GapStatus.COVERED, "MATH.F.LINEAR.COMPARE"),
    _item("8.F.3", GapStatus.COVERED, "MATH.F.FUNCTIONS"),
    _item("8.F.4", GapStatus.COVERED, "MATH.F.LINEAR.SLOPE_INTERCEPT"),
    _item(
        "8.F.5",
        GapStatus.PARTIAL,
        "MATH.F.FUNCTIONS",
        "Function classification exists; qualitative graph-interval behavior needs depth.",
    ),
    _item(
        "8.G.1",
        GapStatus.PARTIAL,
        "MATH.GEO.TRANSFORMATIONS",
        "Rigid transformations exist; explicit preservation-property reasoning needs depth.",
    ),
    _item("8.G.2", GapStatus.COVERED, "MATH.GEO.CONGRUENCE"),
    _item(
        "8.G.3",
        GapStatus.PARTIAL,
        "MATH.GEO.TRANSFORMATIONS",
        "Coordinate transformations exist; full figure-coordinate effects need depth.",
    ),
    _item("8.G.4", GapStatus.COVERED, "MATH.GEO.SIMILARITY"),
    _item(
        "8.G.5",
        GapStatus.PARTIAL,
        "MATH.GEO.ANGLES",
        "Angle relationships exist; informal argument and AA reasoning need integrated depth.",
    ),
    _item(
        "8.G.6",
        GapStatus.PARTIAL,
        "MATH.GEO.PYTHAGOREAN",
        "The theorem and converse exist; explicit proof/explanation evidence needs depth.",
    ),
    _item(
        "8.G.7",
        GapStatus.PARTIAL,
        "MATH.GEO.PYTHAGOREAN",
        "Side solving exists; broaden real-world two- and three-dimensional applications.",
    ),
    _item("8.G.8", GapStatus.COVERED, "MATH.GEO.COORDINATE"),
    _item("8.G.9", GapStatus.COVERED, "MATH.GEO.SOLID_VOLUME"),
    _item("8.SP.1", GapStatus.COVERED, "MATH.DATA.BIVARIATE"),
    _item("8.SP.2", GapStatus.COVERED, "MATH.DATA.LINEAR_MODEL"),
    _item("8.SP.3", GapStatus.COVERED, "MATH.DATA.LINEAR_MODEL"),
    _item("8.SP.4", GapStatus.COVERED, "MATH.DATA.FREQUENCY"),
)

validate_inventory(CA_GRADE8_STANDARD_CODES, CA_GRADE8_GAPS)
