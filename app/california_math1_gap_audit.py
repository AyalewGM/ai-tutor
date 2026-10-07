"""California Mathematics I proposed canonical gap audit.

Shared standards reuse the Algebra I classification so the same mathematics is
not classified twice differently. Mathematics-I-only geometry is classified here.
"""

from app.california_algebra1_gap_audit import CA_ALGEBRA_I_GAPS
from app.california_grade9_inventory import CA_MATHEMATICS_I_STANDARD_CODES
from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory

_SHARED = {item.standard_code: item for item in CA_ALGEBRA_I_GAPS}


def _c(code: str, skill: str, note: str | None = None) -> StandardGap:
    return StandardGap("CA", 9, code, GapStatus.COVERED, skill, note)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("CA", 9, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("CA", 9, code, GapStatus.GAP, rationale=f"gap:{key}")


_GEOMETRY = {
    "G-CO.1": _p("G-CO.1", "MATH.GEO.SHAPES", "Core shapes/angles exist; formal primitive-based definitions need depth."),
    "G-CO.2": _p("G-CO.2", "MATH.GEO.TRANSFORMATIONS", "Coordinate transformations exist; transformation-as-function representation needs depth."),
    "G-CO.3": _p("G-CO.3", "MATH.GEO.SYMMETRY.REFLECTION", "Symmetry exists; rotational/reflection symmetry of polygons needs depth."),
    "G-CO.4": _p("G-CO.4", "MATH.GEO.TRANSFORMATIONS", "Rigid transformations exist; formal geometric definitions need depth."),
    "G-CO.5": _p("G-CO.5", "MATH.GEO.TRANSFORMATIONS", "Point/coordinate transformations exist; full-figure construction and sequences need depth."),
    "G-CO.6": _c("G-CO.6", "MATH.GEO.CONGRUENCE"),
    "G-CO.7": _p("G-CO.7", "MATH.GEO.CONGRUENCE", "Rigid congruence exists; explicit corresponding-side/angle iff reasoning needs depth."),
    "G-CO.8": _g("G-CO.8", "triangle-congruence-criteria"),
    "G-CO.12": _g("G-CO.12", "formal-geometric-constructions"),
    "G-CO.13": _g("G-CO.13", "regular-polygon-circle-constructions"),
    "G-GPE.4": _p("G-GPE.4", "MATH.GEO.COORDINATE", "Coordinate tools exist; algebraic proof of geometric theorems needs depth."),
    "G-GPE.5": _p("G-GPE.5", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Slope exists; proof/use of parallel and perpendicular slope criteria needs depth."),
    "G-GPE.7": _p("G-GPE.7", "MATH.GEO.COORDINATE", "Distance/area skills exist; polygon perimeter/area coordinate integration needs depth."),
}


def _classification(code: str) -> StandardGap:
    if code in _SHARED:
        return _SHARED[code]
    if code in _GEOMETRY:
        return _GEOMETRY[code]
    raise ValueError(f"Unclassified California Mathematics I standard: {code}")


CA_MATHEMATICS_I_GAPS = tuple(_classification(code) for code in CA_MATHEMATICS_I_STANDARD_CODES)

validate_inventory(CA_MATHEMATICS_I_STANDARD_CODES, CA_MATHEMATICS_I_GAPS)
