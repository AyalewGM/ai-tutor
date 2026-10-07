"""California Algebra I proposed canonical gap audit."""

from app.california_grade9_inventory import CA_ALGEBRA_I_STANDARD_CODES
from app.curriculum_gap_analysis import GapStatus, StandardGap, validate_inventory


def _c(code: str, skill: str, note: str | None = None) -> StandardGap:
    return StandardGap("CA", 9, code, GapStatus.COVERED, skill, note)


def _p(code: str, skill: str, note: str) -> StandardGap:
    return StandardGap("CA", 9, code, GapStatus.PARTIAL, skill, note)


def _g(code: str, key: str) -> StandardGap:
    return StandardGap("CA", 9, code, GapStatus.GAP, rationale=f"gap:{key}")


CA_ALGEBRA_I_GAPS = (
    _g("N-RN.1", "rational-exponents-radicals"),
    _g("N-RN.2", "radical-rational-exponent-rewrite"),
    _g("N-RN.3", "rational-irrational-closure"),
    _p("N-Q.1", "MATH.MEAS.DIMENSIONAL_ANALYSIS", "Units exist; integrate scale/origin and formula-unit reasoning."),
    _p("N-Q.2", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Modeling exists; explicit quantity-definition decisions need depth."),
    _p("N-Q.3", "MATH.NS.ROUNDING", "Rounding exists; measurement-limitation accuracy decisions need depth."),
    _c("A-SSE.1.a", "MATH.EE.EXPR"),
    _p("A-SSE.1.b", "MATH.EE.EXPR", "Expression structure exists; nested-entity interpretation needs depth."),
    _p("A-SSE.2", "MATH.EE.EXPR", "Equivalent forms exist; broader structural rewriting needs depth."),
    _p("A-SSE.3.a", "MATH.EE.POLYNOMIAL_OPERATIONS", "Factoring exists at GCF/factored-root depth; quadratic factor-form reasoning needs depth."),
    _g("A-SSE.3.b", "complete-square-expression"),
    _p("A-SSE.3.c", "MATH.F.EXPONENTIAL", "Exponential functions exist; equivalent-rate expression transformations need depth."),
    _c("A-APR.1", "MATH.EE.POLYNOMIAL_OPERATIONS"),
    _p("A-CED.1", "MATH.EE.EQUATION.MULTISTEP", "Equation/inequality solving exists; creation across linear/quadratic/exponential contexts needs depth."),
    _p("A-CED.2", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Linear modeling exists; broader two-variable equation creation and graph labeling need depth."),
    _p("A-CED.3", "MATH.EE.SYSTEMS", "Systems exist; constraint viability and inequality-system modeling need depth."),
    _p("A-CED.4", "MATH.EE.EQUATION.MULTISTEP", "Equation manipulation exists; literal-formula rearrangement needs depth."),
    _p("A-REI.1", "MATH.EE.EQUATION.MULTISTEP", "Solving exists; explicit justification of equivalence-preserving steps needs depth."),
    _c("A-REI.3", "MATH.EE.INEQUALITY.MULTISTEP"),
    _g("A-REI.3.1", "absolute-value-equations-inequalities"),
    _g("A-REI.4.a", "quadratic-completing-square-formula"),
    _p("A-REI.4.b", "MATH.F.QUADRATIC.INTERPRET", "Factored quadratic roots exist; square-root/completing-square/formula breadth needs depth."),
    _p("A-REI.5", "MATH.EE.SYSTEMS", "Elimination exists; proof of solution-preserving equation replacement needs depth."),
    _c("A-REI.6", "MATH.EE.SYSTEMS"),
    _g("A-REI.7", "linear-quadratic-systems"),
    _p("A-REI.10", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Graphs exist; equation-as-solution-set reasoning needs depth."),
    _p("A-REI.11", "MATH.F.FUNCTIONS", "Function comparison exists; graph-intersection solution reasoning across families needs depth."),
    _g("A-REI.12", "two-variable-linear-inequality-graphs"),
    _p("F-IF.1", "MATH.F.FUNCTIONS", "Function concept exists; formal set/domain definition needs depth."),
    _c("F-IF.2", "MATH.F.LINEAR.EVALUATE"),
    _p("F-IF.3", "MATH.F.LINEAR.SEQUENCE", "Linear sequences exist; recursive and broader sequence-as-function depth remains."),
    _p("F-IF.4", "MATH.F.QUADRATIC.INTERPRET", "Quadratic interpretation exists; full key-feature graph vocabulary needs depth."),
    _p("F-IF.5", "MATH.F.FUNCTIONS", "Domain/range exists; contextual domain restrictions need depth."),
    _p("F-IF.6", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Slope exists; average-rate-over-interval and graph estimation need depth."),
    _p("F-IF.7.a", "MATH.F.QUADRATIC.INTERPRET", "Quadratics exist; graphing intercept/max/min representations need depth."),
    _g("F-IF.7.b", "piecewise-absolute-root-function-graphs"),
    _p("F-IF.7.e", "MATH.F.EXPONENTIAL", "Exponential functions exist; required Algebra-I graph features need depth."),
    _p("F-IF.8.a", "MATH.F.QUADRATIC.INTERPRET", "Quadratic forms exist; completing-square interpretation is missing."),
    _c("F-IF.8.b", "MATH.F.EXPONENTIAL"),
    _p("F-IF.9", "MATH.F.LINEAR.COMPARE", "Function comparison exists; broaden across quadratic/exponential representations."),
    _p("F-BF.1.a", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Function models exist; explicit/recursive/process construction needs depth."),
    _g("F-BF.1.b", "combine-functions-arithmetic"),
    _p("F-BF.2", "MATH.F.LINEAR.SEQUENCE", "Arithmetic sequence exists; geometric sequence and two-form translation need depth."),
    _g("F-BF.3", "function-transformations"),
    _g("F-BF.4.a", "inverse-functions"),
    _p("F-LE.1.a", "MATH.F.LINEAR.COMPARE", "Linear/exponential comparison exists; proof of equal-difference/equal-factor growth needs depth."),
    _c("F-LE.1.b", "MATH.F.LINEAR.SLOPE_INTERCEPT"),
    _c("F-LE.1.c", "MATH.F.EXPONENTIAL"),
    _p("F-LE.2", "MATH.F.EXPONENTIAL", "Exponential models exist; construction from tables/pairs and geometric sequences needs depth."),
    _p("F-LE.3", "MATH.F.EXPONENTIAL", "Linear-vs-exponential comparison exists; eventual-growth graph/table reasoning needs depth."),
    _p("F-LE.5", "MATH.F.LINEAR.SLOPE_INTERCEPT", "Linear/exponential parameters exist; contextual parameter interpretation needs depth."),
    _p("F-LE.6", "MATH.F.QUADRATIC.INTERPRET", "Quadratic functions exist; physical-motion modeling needs depth."),
    _p("S-ID.1", "MATH.DATA.REPRESENTATIONS", "Dot/histogram/five-number work exists; explicit box-plot representation needs depth."),
    _p("S-ID.2", "MATH.DATA.SPREAD", "Center/spread exists; standard-deviation comparison needs depth."),
    _p("S-ID.3", "MATH.DATA.CENTER", "Outlier effects exist; comparative distribution-shape interpretation needs depth."),
    _c("S-ID.5", "MATH.DATA.FREQUENCY"),
    _p("S-ID.6.a", "MATH.DATA.LINEAR_MODEL", "Line-fit prediction exists; model selection across function families needs depth."),
    _g("S-ID.6.b", "residual-analysis"),
    _c("S-ID.6.c", "MATH.DATA.LINEAR_MODEL"),
    _c("S-ID.7", "MATH.DATA.LINEAR_MODEL"),
    _g("S-ID.8", "correlation-coefficient"),
    _g("S-ID.9", "correlation-vs-causation"),
)

validate_inventory(CA_ALGEBRA_I_STANDARD_CODES, CA_ALGEBRA_I_GAPS)
