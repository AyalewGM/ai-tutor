"""Authoritative California standards-to-canonical mapping proposals.

This is a reviewed implementation slice, not a California-complete claim.
Official identifiers are preserved from the California Common Core State
Standards for Mathematics. Proposed mappings still require the existing human
review/publication gate before they can count toward national completion.
"""

from __future__ import annotations

from app.california_curriculum import CA_CURRICULUM_VERSION, CA_SOURCE_URI
from app.curriculum_ingestion_schema import (
    SCHEMA_VERSION,
    CurriculumIngestionPack,
    ProposedSkillMapping,
    StandardDraft,
)

# (official identifier, short Mihur title, domain/strand, canonical skill, mapping type)
# Titles summarize the mathematical target; the official CDE source remains authoritative.
_GRADE_1_8: dict[int, tuple[tuple[str, str, str, str, str], ...]] = {
    1: (
        ("1.OA.1", "Addition and subtraction situations", "Operations and Algebraic Thinking", "MATH.NS.ADDITION", "PARTIAL"),
        ("1.OA.6", "Add and subtract within 20", "Operations and Algebraic Thinking", "MATH.NS.ADDITION", "PARTIAL"),
        ("1.NBT.2", "Understand two-digit place value", "Number and Operations in Base Ten", "MATH.NS.PLACE_VALUE", "EQUIVALENT"),
        ("1.NBT.3", "Compare two-digit numbers", "Number and Operations in Base Ten", "MATH.NS.COMPARE_ORDER", "EQUIVALENT"),
        ("1.NBT.4", "Add within 100", "Number and Operations in Base Ten", "MATH.NS.ADDITION", "PARTIAL"),
    ),
    2: (
        ("2.OA.1", "One- and two-step addition/subtraction problems", "Operations and Algebraic Thinking", "MATH.NS.ADDITION", "PARTIAL"),
        ("2.NBT.1", "Understand three-digit place value", "Number and Operations in Base Ten", "MATH.NS.PLACE_VALUE", "EQUIVALENT"),
        ("2.NBT.4", "Compare three-digit numbers", "Number and Operations in Base Ten", "MATH.NS.COMPARE_ORDER", "EQUIVALENT"),
        ("2.NBT.5", "Add and subtract within 100", "Number and Operations in Base Ten", "MATH.NS.ADDITION", "PARTIAL"),
        ("2.NBT.7", "Add and subtract within 1000", "Number and Operations in Base Ten", "MATH.NS.ADDITION", "PARTIAL"),
    ),
    3: (
        ("3.OA.1", "Interpret products", "Operations and Algebraic Thinking", "MATH.NS.MULTIPLICATION", "EQUIVALENT"),
        ("3.OA.2", "Interpret whole-number quotients", "Operations and Algebraic Thinking", "MATH.NS.DIVISION", "EQUIVALENT"),
        ("3.OA.3", "Multiplication and division word problems", "Operations and Algebraic Thinking", "MATH.NS.MULTIPLICATION", "PARTIAL"),
        ("3.OA.7", "Multiply and divide within 100", "Operations and Algebraic Thinking", "MATH.NS.MULTIPLICATION", "PARTIAL"),
        ("3.NBT.1", "Round whole numbers", "Number and Operations in Base Ten", "MATH.NS.ROUNDING", "EQUIVALENT"),
        ("3.MD.8", "Perimeter of polygons", "Measurement and Data", "MATH.GEO.MEASURE.PERIMETER", "EQUIVALENT"),
    ),
    4: (
        ("4.OA.2", "Multiplicative comparison", "Operations and Algebraic Thinking", "MATH.NS.MULTIPLICATION", "EQUIVALENT"),
        ("4.OA.3", "Multistep whole-number problems", "Operations and Algebraic Thinking", "MATH.NS.MULTIPLICATION", "PARTIAL"),
        ("4.NBT.2", "Compare multi-digit whole numbers", "Number and Operations in Base Ten", "MATH.NS.COMPARE_ORDER", "EQUIVALENT"),
        ("4.NBT.3", "Round multi-digit whole numbers", "Number and Operations in Base Ten", "MATH.NS.ROUNDING", "EQUIVALENT"),
        ("4.NBT.4", "Multi-digit addition and subtraction", "Number and Operations in Base Ten", "MATH.NS.ADDITION", "PARTIAL"),
        ("4.NBT.5", "Multiply whole numbers", "Number and Operations in Base Ten", "MATH.NS.MULTIPLICATION", "PARTIAL"),
        ("4.NBT.6", "Whole-number quotients and remainders", "Number and Operations in Base Ten", "MATH.NS.DIVISION", "PARTIAL"),
        ("4.NF.1", "Equivalent fractions", "Number and Operations—Fractions", "MATH.NF.EQUIVALENT_FRACTIONS", "EQUIVALENT"),
        ("4.NF.2", "Compare fractions", "Number and Operations—Fractions", "MATH.NF.COMPARE", "EQUIVALENT"),
        ("4.MD.3", "Area and perimeter formulas", "Measurement and Data", "MATH.GEO.MEASURE.AREA", "PARTIAL"),
    ),
    5: (
        ("5.NBT.1", "Place-value patterns by powers of ten", "Number and Operations in Base Ten", "MATH.NS.PLACE_VALUE", "EQUIVALENT"),
        ("5.NBT.3", "Read, write, and compare decimals", "Number and Operations in Base Ten", "MATH.NS.DECIMAL.COMPARE", "PARTIAL"),
        ("5.NBT.5", "Multi-digit multiplication", "Number and Operations in Base Ten", "MATH.NS.MULTIPLICATION", "EQUIVALENT"),
        ("5.NBT.6", "Multi-digit division", "Number and Operations in Base Ten", "MATH.NS.DIVISION", "EQUIVALENT"),
        ("5.NBT.7", "Decimal operations", "Number and Operations in Base Ten", "MATH.NS.DECIMAL.ADD_SUBTRACT", "PARTIAL"),
        ("5.NF.1", "Add and subtract fractions", "Number and Operations—Fractions", "MATH.NF.ADD_SUBTRACT", "EQUIVALENT"),
        ("5.NF.4", "Multiply fractions", "Number and Operations—Fractions", "MATH.NF.MULTIPLY", "EQUIVALENT"),
        ("5.NF.7", "Divide unit fractions and whole numbers", "Number and Operations—Fractions", "MATH.NF.DIVIDE", "PARTIAL"),
        ("5.MD.5", "Volume as multiplication", "Measurement and Data", "MATH.GEO.MEASURE.VOLUME", "EQUIVALENT"),
    ),
    6: (
        ("6.RP.1", "Understand ratios", "Ratios and Proportional Relationships", "MATH.RP.RATIO.INTERPRET", "EQUIVALENT"),
        ("6.RP.2", "Understand unit rates", "Ratios and Proportional Relationships", "MATH.RP.RATE.UNIT", "EQUIVALENT"),
        ("6.RP.3", "Use ratio and rate reasoning", "Ratios and Proportional Relationships", "MATH.RP.RATIO.EQUIVALENT", "PARTIAL"),
        ("6.NS.1", "Divide fractions", "The Number System", "MATH.NF.DIVIDE", "EQUIVALENT"),
        ("6.NS.6", "Rational numbers on number lines and coordinate planes", "The Number System", "MATH.NS.INTEGERS", "PARTIAL"),
        ("6.NS.7", "Order and absolute value of rational numbers", "The Number System", "MATH.NS.INTEGERS", "PARTIAL"),
        ("6.EE.2", "Write, read, and evaluate expressions", "Expressions and Equations", "MATH.EE.EXPR", "PARTIAL"),
        ("6.EE.7", "Solve one-variable equations", "Expressions and Equations", "MATH.EE.EQUATION.ONE", "EQUIVALENT"),
        ("6.G.1", "Area of triangles and quadrilaterals", "Geometry", "MATH.GEO.MEASURE.AREA", "PARTIAL"),
        ("6.SP.3", "Measures of center and variation", "Statistics and Probability", "MATH.DATA.CENTER", "PARTIAL"),
    ),
    7: (
        ("7.RP.1", "Unit rates with fractions", "Ratios and Proportional Relationships", "MATH.RP.RATE.UNIT", "PARTIAL"),
        ("7.RP.2", "Recognize and represent proportional relationships", "Ratios and Proportional Relationships", "MATH.RP.PROPORTION.IDENTIFY", "PARTIAL"),
        ("7.RP.3", "Multistep percent problems", "Ratios and Proportional Relationships", "MATH.RP.PERCENT.APPLICATIONS", "EQUIVALENT"),
        ("7.EE.1", "Use properties to transform expressions", "Expressions and Equations", "MATH.EE.EXPR", "PARTIAL"),
        ("7.EE.4", "Solve equations from real-life problems", "Expressions and Equations", "MATH.EE.EQUATION.MULTISTEP", "PARTIAL"),
        ("7.G.5", "Angle relationships", "Geometry", "MATH.GEO.ANGLES", "EQUIVALENT"),
        ("7.SP.5", "Probability as a number from 0 to 1", "Statistics and Probability", "MATH.PROB.SIMPLE", "PARTIAL"),
        ("7.SP.8", "Compound probability", "Statistics and Probability", "MATH.PROB.COMPOUND", "EQUIVALENT"),
    ),
    8: (
        ("8.EE.7", "Solve linear equations in one variable", "Expressions and Equations", "MATH.EE.EQUATION.MULTISTEP", "EQUIVALENT"),
        ("8.F.1", "Understand functions", "Functions", "MATH.F.LINEAR.EVALUATE", "PARTIAL"),
        ("8.F.4", "Model linear relationships", "Functions", "MATH.F.LINEAR.SLOPE_INTERCEPT", "PARTIAL"),
        ("8.G.2", "Transformations and congruence", "Geometry", "MATH.GEO.TRANSFORMATIONS", "PARTIAL"),
        ("8.G.7", "Apply the Pythagorean theorem", "Geometry", "MATH.GEO.PYTHAGOREAN", "EQUIVALENT"),
        ("8.SP.4", "Two-way tables and relative frequencies", "Statistics and Probability", "MATH.DATA.FREQUENCY", "EQUIVALENT"),
    ),
}

_GRADE_9_COMMON = (
    ("A-SSE.1.a", "Interpret parts of expressions", "Seeing Structure in Expressions", "MATH.EE.EXPR", "EQUIVALENT"),
    ("A-SSE.1.b", "Interpret complicated expressions", "Seeing Structure in Expressions", "MATH.EE.EXPR", "PARTIAL"),
    ("A-CED.1", "Create equations and inequalities", "Creating Equations", "MATH.EE.EQUATION.MULTISTEP", "PARTIAL"),
    ("A-REI.3", "Solve linear equations and inequalities", "Reasoning with Equations and Inequalities", "MATH.EE.EQUATION.MULTISTEP", "PARTIAL"),
    ("F-IF.2", "Evaluate functions", "Interpreting Functions", "MATH.F.LINEAR.EVALUATE", "PARTIAL"),
    ("F-LE.1", "Distinguish and construct linear/exponential models", "Linear, Quadratic, and Exponential Models", "MATH.F.LINEAR.SLOPE_INTERCEPT", "PARTIAL"),
    ("S-ID.1", "Represent data with real-number plots", "Interpreting Categorical and Quantitative Data", "MATH.DATA.SPREAD", "PARTIAL"),
)


def _standard(row: tuple[str, str, str, str, str], *, grade_label: str) -> StandardDraft:
    code, title, strand, _, _ = row
    return StandardDraft(
        code=code,
        title=f"{grade_label}: {title}",
        source_uri=CA_SOURCE_URI,
        strand=strand,
    )


def _mapping(row: tuple[str, str, str, str, str]) -> ProposedSkillMapping:
    code, _, _, canonical, mapping_type = row
    return ProposedSkillMapping(
        standard_code=code,
        canonical_skill_code=canonical,
        mapping_type=mapping_type,
        rationale=(
            "Mihur curated proposal against the official CA CCSSM identifier; "
            "human review/publication remains required."
        ),
    )


def california_grade_1_8_mapping_pack() -> CurriculumIngestionPack:
    rows = tuple(row for grade in range(1, 9) for row in _GRADE_1_8[grade])
    standards = tuple(
        _standard(row, grade_label=f"Grade {grade}")
        for grade in range(1, 9)
        for row in _GRADE_1_8[grade]
    )
    return CurriculumIngestionPack(
        schema_version=SCHEMA_VERSION,
        curriculum_code="CA_CCSSM_G1_8",
        curriculum_version=CA_CURRICULUM_VERSION,
        authority_code="CDE",
        source_uri=CA_SOURCE_URI,
        lifecycle_status="IMPLEMENTED",
        standards=standards,
        proposed_mappings=tuple(_mapping(row) for row in rows),
    )


def california_grade9_pathway_pack(pathway: str) -> CurriculumIngestionPack:
    normalized = pathway.strip().upper()
    if normalized not in {"ALGEBRA_I", "MATHEMATICS_I"}:
        raise ValueError("California Grade 9 pathway must be ALGEBRA_I or MATHEMATICS_I")
    discipline = "Algebra I" if normalized == "ALGEBRA_I" else "Mathematics I"
    curriculum_code = f"CA_CCSSM_{normalized}"
    return CurriculumIngestionPack(
        schema_version=SCHEMA_VERSION,
        curriculum_code=curriculum_code,
        curriculum_version=CA_CURRICULUM_VERSION,
        authority_code="CDE",
        source_uri=CA_SOURCE_URI,
        lifecycle_status="IMPLEMENTED",
        standards=tuple(
            _standard(row, grade_label=f"Grade 9 pathway — {discipline}")
            for row in _GRADE_9_COMMON
        ),
        proposed_mappings=tuple(_mapping(row) for row in _GRADE_9_COMMON),
    )


def proposed_standard_count_by_grade() -> dict[int, int]:
    """Audit helper. Counts proposals only; these are not completion counts."""

    return {grade: len(rows) for grade, rows in _GRADE_1_8.items()} | {
        9: len(_GRADE_9_COMMON)
    }
