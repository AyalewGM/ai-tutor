"""Generate comprehensive declarative curriculum packs for DMV Grades 3-5."""

import json
from dataclasses import dataclass
from pathlib import Path

_PACK_DIR = Path(__file__).parents[1] / "docs/curriculum/packs"


@dataclass(frozen=True)
class JurisdictionDef:
    code: str
    name: str
    authority_code: str
    authority_name: str
    standards_source_uri: str
    authority_uri: str
    version: str


@dataclass(frozen=True)
class SkillTemplate:
    local_code: str
    name: str
    description: str
    canonical_code: str
    canonical_name: str
    canonical_description: str
    families: tuple[str, ...]
    prerequisite_codes: tuple[str, ...]
    standards_md_dc: tuple[str, ...]
    standards_va: tuple[str, ...]


JURISDICTIONS = {
    "MD": JurisdictionDef(
        code="MD",
        name="Maryland",
        authority_code="MSDE",
        authority_name="Maryland State Department of Education",
        standards_source_uri="https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx",
        authority_uri="https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx",
        version="MCCRS-revised-SY2026-27",
    ),
    "DC": JurisdictionDef(
        code="DC",
        name="District of Columbia",
        authority_code="OSSE",
        authority_name="Office of the State Superintendent of Education",
        standards_source_uri="https://osse-migrate.dc.gov/sites/default/files/dc/sites/osse/page_content/attachments/mathematics-adjusted-blueprintGrades3_0.pdf",
        authority_uri="https://osse-migrate.dc.gov/service/district-columbia-standards-learning-0",
        version="CCSS-OSSE-2024-25",
    ),
    "VA": JurisdictionDef(
        code="VA",
        name="Virginia",
        authority_code="VDOE",
        authority_name="Virginia Department of Education",
        standards_source_uri="https://www.doe.virginia.gov/teaching-learning-assessment/k-12-standards-instruction/mathematics/2023-sol-instructional-resources",
        authority_uri="https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics",
        version="VDOE-2023-SY2024-25",
    ),
}

GRADE3_SKILLS = [
    SkillTemplate(
        "{jurisdiction}3.OA.MULTIPLICATION",
        "Multiplication as Equal Groups",
        "Interpret products of whole numbers and solve multiplication word problems within 100 using equal groups and arrays.",
        "MATH.ELEMENTARY.MULTIPLICATION.EQUAL_GROUPS",
        "Multiplication as Equal Groups",
        "Interpret products and solve word problems involving equal groups and arrays.",
        ("EQUAL_GROUPS", "MULTIPLICATION_WITHIN_100", "WORD_PROBLEM_MULTIPLY_DIVIDE_100"),
        (),
        ("3.OA",),
        ("3.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}3.OA.DIVISION",
        "Division as Equal Sharing",
        "Interpret quotients and solve division word problems within 100 using equal sharing and arrays.",
        "MATH.ELEMENTARY.DIVISION.EQUAL_SHARING",
        "Division as Equal Sharing",
        "Interpret quotients and solve word problems involving equal sharing and arrays.",
        ("EQUAL_SHARING", "DIVISION_WITHIN_100", "WORD_PROBLEM_MULTIPLY_DIVIDE_100"),
        ("{jurisdiction}3.OA.MULTIPLICATION",),
        ("3.OA",),
        ("3.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}3.OA.FACT_FAMILIES",
        "Properties of Multiplication and Division",
        "Apply commutative, associative, and distributive properties and use multiplication/division fact families.",
        "MATH.ELEMENTARY.MULTIPLICATION.PROPERTIES_FACT_FAMILIES",
        "Properties of Multiplication and Division",
        "Apply properties of operations and use fact families to solve problems.",
        ("MULTIPLICATION_WITHIN_100", "DIVISION_WITHIN_100"),
        ("{jurisdiction}3.OA.DIVISION",),
        ("3.OA",),
        ("3.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}3.NBT.PLACE_VALUE",
        "Place Value and Rounding",
        "Round whole numbers to the nearest 10 or 100 and use place value to add and subtract within 1000.",
        "MATH.ELEMENTARY.PLACE_VALUE.ROUNDING_THREE_DIGIT",
        "Place Value and Rounding",
        "Round whole numbers to nearest 10 or 100 and use place-value strategies for addition/subtraction.",
        ("PLACE_VALUE_BASE_TEN", "ROUNDING"),
        (),
        ("3.NBT",),
        ("3.NS",),
    ),
    SkillTemplate(
        "{jurisdiction}3.NF.FRACTIONS",
        "Fractions as Numbers",
        "Understand fractions as parts of a whole, represent fractions on a number line, and identify equivalent fractions.",
        "MATH.ELEMENTARY.FRACTIONS.FRACTIONS_AS_NUMBERS",
        "Fractions as Numbers",
        "Represent fractions as numbers on a number line and identify equivalent fractions.",
        ("UNIT_FRACTION", "FRACTION_NUMBER_LINE", "FRACTION_EQUIVALENCE", "FRACTION_COMPARE"),
        (),
        ("3.NF",),
        ("3.NS",),
    ),
    SkillTemplate(
        "{jurisdiction}3.MD.TIME",
        "Time and Elapsed Time",
        "Tell and write time to the nearest minute and measure intervals of time.",
        "MATH.ELEMENTARY.MEASUREMENT.TELL_TIME_MINUTE_ELAPSED",
        "Time and Elapsed Time",
        "Tell time to the nearest minute and solve elapsed-time problems.",
        ("TIME_TO_5_MINUTES", "ELAPSED_TIME"),
        (),
        ("3.MD",),
        ("3.MG",),
    ),
    SkillTemplate(
        "{jurisdiction}3.MD.DATA",
        "Data: Picture and Bar Graphs",
        "Draw and interpret scaled picture graphs and bar graphs to solve problems.",
        "MATH.ELEMENTARY.DATA.PICTURE_BAR_GRAPHS",
        "Picture and Bar Graphs",
        "Draw and interpret scaled picture graphs and bar graphs.",
        ("BAR_GRAPH_READ", "PICTURE_GRAPH_READ"),
        (),
        ("3.MD",),
        ("3.PS",),
    ),
    SkillTemplate(
        "{jurisdiction}3.MD.AREA_PERIMETER",
        "Area and Perimeter",
        "Understand area as counting unit squares; relate area to multiplication; and solve perimeter problems.",
        "MATH.ELEMENTARY.MEASUREMENT.AREA_PERIMETER",
        "Area and Perimeter",
        "Measure area by counting unit squares and solve area/perimeter problems for rectangles.",
        ("RECTANGLE_AREA", "AREA_PERIMETER_RECTANGLE"),
        ("{jurisdiction}3.OA.MULTIPLICATION",),
        ("3.MD",),
        ("3.MG",),
    ),
    SkillTemplate(
        "{jurisdiction}3.G.SHAPES",
        "Shapes and Their Attributes",
        "Understand that shapes in different categories share attributes and identify quadrilaterals.",
        "MATH.ELEMENTARY.GEOMETRY.QUADRILATERAL_ATTRIBUTES",
        "Shapes and Their Attributes",
        "Recognize shared attributes of shapes and classify quadrilaterals.",
        ("CLASSIFY_SHAPE",),
        (),
        ("3.G",),
        ("3.MG",),
    ),
]

GRADE4_SKILLS = [
    SkillTemplate(
        "{jurisdiction}4.OA.COMPARISON",
        "Multiplicative Comparison",
        "Interpret a multiplication equation as a comparison and solve multiplicative comparison word problems.",
        "MATH.ELEMENTARY.MULTIPLICATION.MULTIPLICATIVE_COMPARISON",
        "Multiplicative Comparison",
        "Interpret multiplication as a comparison and solve comparison word problems.",
        ("WORD_PROBLEM_MULTIPLY_DIVIDE_100", "MULTIPLICATION_WITHIN_100"),
        (),
        ("4.OA",),
        ("4.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}4.OA.MULTI_STEP",
        "Multi-Step Word Problems",
        "Solve multi-step word problems using the four operations and interpret remainders.",
        "MATH.ELEMENTARY.ARITHMETIC.MULTI_STEP_WORD_PROBLEMS",
        "Multi-Step Word Problems",
        "Solve multi-step word problems using addition, subtraction, multiplication, and division.",
        ("WORD_PROBLEM_ADD_SUB_100", "WORD_PROBLEM_MULTIPLY_DIVIDE_100"),
        ("{jurisdiction}4.OA.COMPARISON",),
        ("4.OA",),
        ("4.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}4.OA.FACTORS_PATTERNS",
        "Factors, Multiples, and Patterns",
        "Find factor pairs, recognize multiples, and generate number or shape patterns.",
        "MATH.ELEMENTARY.NUMBER_SENSE.FACTORS_MULTIPLES_PATTERNS",
        "Factors, Multiples, and Patterns",
        "Find factors and multiples and generate and analyze patterns.",
        ("NUMBER_PATTERN", "MULTIPLICATION_WITHIN_100", "DIVISION_WITHIN_100"),
        (),
        ("4.OA",),
        ("4.NS",),
    ),
    SkillTemplate(
        "{jurisdiction}4.NBT.PLACE_VALUE",
        "Multi-Digit Place Value",
        "Read, write, and compare multi-digit whole numbers using place value understanding.",
        "MATH.ELEMENTARY.PLACE_VALUE.MULTI_DIGIT",
        "Multi-Digit Place Value",
        "Read, write, compare, and round multi-digit whole numbers.",
        ("PLACE_VALUE_BASE_TEN", "COMPARE_NUMBERS", "ROUNDING"),
        (),
        ("4.NBT",),
        ("4.NS",),
    ),
    SkillTemplate(
        "{jurisdiction}4.NBT.MULTIPLY",
        "Multi-Digit Multiplication",
        "Multiply a whole number of up to four digits by a one-digit whole number and multiply two two-digit numbers.",
        "MATH.ELEMENTARY.ARITHMETIC.MULTI_DIGIT_MULTIPLICATION",
        "Multi-Digit Multiplication",
        "Multiply multi-digit whole numbers using place-value strategies.",
        ("MULTI_DIGIT_MULTIPLICATION",),
        ("{jurisdiction}4.NBT.PLACE_VALUE",),
        ("4.NBT",),
        ("4.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}4.NBT.DIVIDE",
        "Long Division",
        "Find whole-number quotients and remainders with up to four-digit dividends and one-digit divisors.",
        "MATH.ELEMENTARY.ARITHMETIC.LONG_DIVISION",
        "Long Division",
        "Divide multi-digit whole numbers using place-value strategies.",
        ("LONG_DIVISION",),
        ("{jurisdiction}4.NBT.MULTIPLY",),
        ("4.NBT",),
        ("4.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}4.NF.FRACTIONS",
        "Fraction Equivalence and Operations",
        "Explain fraction equivalence, compare fractions, add and subtract like-denominator fractions, and multiply fractions by whole numbers.",
        "MATH.ELEMENTARY.FRACTIONS.EQUIVALENCE_OPERATIONS",
        "Fraction Equivalence and Operations",
        "Understand fraction equivalence, compare fractions, and perform basic fraction operations.",
        ("FRACTION_EQUIVALENCE", "FRACTION_COMPARE", "FRACTION_ADD_SUBTRACT_LIKE", "MULTIPLY_FRACTION_BY_WHOLE"),
        (),
        ("4.NF",),
        ("4.NS", "4.CE"),
    ),
    SkillTemplate(
        "{jurisdiction}4.NF.DECIMALS",
        "Decimal Notation and Comparison",
        "Understand decimal notation for fractions and compare decimal fractions.",
        "MATH.ELEMENTARY.FRACTIONS.DECIMAL_NOTATION",
        "Decimal Notation and Comparison",
        "Express fractions with denominators 10 and 100 as decimals and compare decimal numbers.",
        ("DECIMAL_PLACE_VALUE",),
        (),
        ("4.NF",),
        ("4.NS",),
    ),
    SkillTemplate(
        "{jurisdiction}4.MD.MEASUREMENT",
        "Measurement and Conversion",
        "Know relative sizes of measurement units within one system and solve measurement conversion problems.",
        "MATH.ELEMENTARY.MEASUREMENT.CONVERSION",
        "Measurement and Conversion",
        "Convert between measurement units within the same system and solve word problems.",
        ("MEASUREMENT_CONVERSION",),
        (),
        ("4.MD",),
        ("4.MG",),
    ),
    SkillTemplate(
        "{jurisdiction}4.MD.ANGLE_LINES",
        "Angles, Lines, and Shapes",
        "Measure and sketch angles, identify parallel and perpendicular lines, and classify two-dimensional figures.",
        "MATH.ELEMENTARY.GEOMETRY.ANGLES_LINES_SHAPES",
        "Angles, Lines, and Shapes",
        "Measure angles, identify line relationships, and classify two-dimensional shapes.",
        ("ANGLE_MEASUREMENT", "LINES_PARALLEL_PERPENDICULAR", "CLASSIFY_SHAPE"),
        (),
        ("4.MD", "4.G"),
        ("4.MG",),
    ),
]

GRADE5_SKILLS = [
    SkillTemplate(
        "{jurisdiction}5.OA.EXPRESSIONS",
        "Expressions and Order of Operations",
        "Use parentheses, brackets, or braces in numerical expressions and write simple expressions.",
        "MATH.ELEMENTARY.ARITHMETIC.ORDER_OF_OPERATIONS",
        "Expressions and Order of Operations",
        "Evaluate numerical expressions with grouping symbols and write expressions from verbal descriptions.",
        ("DECIMAL_OPERATIONS", "POWERS_OF_TEN"),
        (),
        ("5.OA",),
        ("5.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}5.OA.PATTERNS",
        "Numerical Patterns",
        "Generate two numerical patterns using given rules and identify relationships between corresponding terms.",
        "MATH.ELEMENTARY.NUMBER_SENSE.PATTERNS_TWO_RULES",
        "Numerical Patterns",
        "Generate and analyze numerical patterns from two rules.",
        ("NUMBER_PATTERN",),
        ("{jurisdiction}5.OA.EXPRESSIONS",),
        ("5.OA",),
        ("5.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}5.NBT.DECIMALS",
        "Decimal Place Value and Operations",
        "Understand place value in decimals, perform operations with decimals, and use powers of 10.",
        "MATH.ELEMENTARY.DECIMALS.PLACE_VALUE_OPERATIONS",
        "Decimal Place Value and Operations",
        "Understand decimal place value and fluently add, subtract, multiply, and divide decimals.",
        ("DECIMAL_PLACE_VALUE", "DECIMAL_OPERATIONS", "POWERS_OF_TEN"),
        (),
        ("5.NBT",),
        ("5.NS", "5.CE"),
    ),
    SkillTemplate(
        "{jurisdiction}5.NF.ADD_SUBTRACT",
        "Add and Subtract Fractions with Unlike Denominators",
        "Add and subtract fractions with unlike denominators by replacing with equivalent fractions.",
        "MATH.ELEMENTARY.FRACTIONS.ADD_SUBTRACT_UNLIKE",
        "Add and Subtract Fractions with Unlike Denominators",
        "Add and subtract fractions with unlike denominators using equivalent fractions.",
        ("ADD_SUBTRACT_UNLIKE_FRACTIONS", "FRACTION_EQUIVALENCE"),
        (),
        ("5.NF",),
        ("5.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}5.NF.MULTIPLY_DIVIDE",
        "Multiply and Divide Fractions",
        "Interpret multiplication as scaling, multiply fractions and mixed numbers, and divide fractions by whole numbers and unit fractions.",
        "MATH.ELEMENTARY.FRACTIONS.MULTIPLY_DIVIDE",
        "Multiply and Divide Fractions",
        "Multiply and divide fractions in contextual and symbolic problems.",
        ("FRACTION_MULTIPLY", "MULTIPLY_FRACTIONS", "DIVIDE_FRACTIONS"),
        ("{jurisdiction}5.NF.ADD_SUBTRACT",),
        ("5.NF",),
        ("5.CE",),
    ),
    SkillTemplate(
        "{jurisdiction}5.MD.CONVERSION",
        "Convert Measurement Units",
        "Convert among different-sized standard measurement units within a given measurement system.",
        "MATH.ELEMENTARY.MEASUREMENT.CONVERSION",
        "Convert Measurement Units",
        "Convert between standard measurement units and solve word problems involving conversions.",
        ("MEASUREMENT_CONVERSION",),
        (),
        ("5.MD",),
        ("5.MG",),
    ),
    SkillTemplate(
        "{jurisdiction}5.MD.VOLUME",
        "Volume",
        "Recognize volume as an attribute of solid figures and measure volumes by counting unit cubes.",
        "MATH.ELEMENTARY.MEASUREMENT.VOLUME",
        "Volume",
        "Measure volume by counting unit cubes and apply volume formulas for rectangular prisms.",
        ("VOLUME",),
        ("{jurisdiction}5.MD.CONVERSION",),
        ("5.MD",),
        ("5.MG",),
    ),
    SkillTemplate(
        "{jurisdiction}5.G.COORDINATES",
        "Coordinate Plane",
        "Use a pair of perpendicular number lines to define a coordinate system and graph points.",
        "MATH.ELEMENTARY.GEOMETRY.COORDINATE_PLANE",
        "Coordinate Plane",
        "Graph points in the first quadrant of the coordinate plane.",
        ("COORDINATE_PLANE",),
        (),
        ("5.G",),
        ("5.MG",),
    ),
    SkillTemplate(
        "{jurisdiction}5.G.SHAPES",
        "Classify Two-Dimensional Figures",
        "Understand attributes of two-dimensional figures and classify them in a hierarchy.",
        "MATH.ELEMENTARY.GEOMETRY.CLASSIFY_2D_FIGURES",
        "Classify Two-Dimensional Figures",
        "Classify two-dimensional figures in a hierarchy based on properties.",
        ("CLASSIFY_SHAPE",),
        (),
        ("5.G",),
        ("5.MG",),
    ),
]

GRADE3_EXPECTATIONS = [
    {"source_identifier": "3.OA", "title": "Represent and solve problems involving multiplication and division", "strand": "Operations and Algebraic Thinking", "description": "Understand products and quotients, solve word problems, and apply properties of multiplication and division."},
    {"source_identifier": "3.NBT", "title": "Use place value understanding and properties of operations to perform multi-digit arithmetic", "strand": "Number and Operations in Base Ten", "description": "Round whole numbers and fluently add and subtract within 1000."},
    {"source_identifier": "3.NF", "title": "Develop understanding of fractions as numbers", "strand": "Number and Operations—Fractions", "description": "Understand fractions as numbers, represent them on a number line, and identify equivalent fractions."},
    {"source_identifier": "3.MD", "title": "Solve problems involving measurement and estimation of intervals of time, liquid volumes, and masses of objects", "strand": "Measurement and Data", "description": "Tell time, measure mass and volume, represent and interpret data, and understand area and perimeter."},
    {"source_identifier": "3.G", "title": "Reason with shapes and their attributes", "strand": "Geometry", "description": "Understand that shapes in different categories share attributes."},
]

GRADE4_EXPECTATIONS = [
    {"source_identifier": "4.OA", "title": "Use the four operations with whole numbers to solve problems", "strand": "Operations and Algebraic Thinking", "description": "Solve multi-step word problems, gain familiarity with factors and multiples, and generate patterns."},
    {"source_identifier": "4.NBT", "title": "Generalize place value understanding for multi-digit whole numbers", "strand": "Number and Operations in Base Ten", "description": "Use place value to perform multi-digit arithmetic."},
    {"source_identifier": "4.NF", "title": "Extend understanding of fraction equivalence and ordering", "strand": "Number and Operations—Fractions", "description": "Understand fraction equivalence, ordering, and decimal notation."},
    {"source_identifier": "4.MD", "title": "Solve problems involving measurement and conversion", "strand": "Measurement and Data", "description": "Solve measurement conversion problems, understand angle measurement, and represent data."},
    {"source_identifier": "4.G", "title": "Draw and identify lines and angles, and classify shapes", "strand": "Geometry", "description": "Draw and identify lines and angles and classify shapes by properties."},
]

GRADE5_EXPECTATIONS = [
    {"source_identifier": "5.OA", "title": "Write and interpret numerical expressions", "strand": "Operations and Algebraic Thinking", "description": "Use parentheses in expressions, write expressions, and analyze patterns."},
    {"source_identifier": "5.NBT", "title": "Understand the place value system and perform operations with multi-digit whole numbers and decimals", "strand": "Number and Operations in Base Ten", "description": "Understand decimal place value and fluently perform operations with decimals."},
    {"source_identifier": "5.NF", "title": "Use equivalent fractions as a strategy to add and subtract fractions", "strand": "Number and Operations—Fractions", "description": "Add and subtract fractions with unlike denominators; multiply and divide fractions."},
    {"source_identifier": "5.MD", "title": "Convert like measurement units within a given measurement system and understand volume", "strand": "Measurement and Data", "description": "Convert measurement units and understand concepts of volume."},
    {"source_identifier": "5.G", "title": "Graph points on the coordinate plane and classify two-dimensional figures", "strand": "Geometry", "description": "Graph points in the first quadrant and classify two-dimensional figures."},
]

VA_GRADE3_EXPECTATIONS = [
    {"source_identifier": "3.CE", "title": "Computation and Estimation", "strand": "Computation and Estimation", "description": "Solve practical problems using multiplication and division within 100 and represent fractions."},
    {"source_identifier": "3.NS", "title": "Number and Number Sense", "strand": "Number and Number Sense", "description": "Represent and compare whole numbers and fractions."},
    {"source_identifier": "3.MG", "title": "Measurement and Geometry", "strand": "Measurement and Geometry", "description": "Tell time, measure, and solve problems involving area, perimeter, and shape attributes."},
    {"source_identifier": "3.PS", "title": "Probability and Statistics", "strand": "Probability and Statistics", "description": "Collect, organize, and interpret data."},
]

VA_GRADE4_EXPECTATIONS = [
    {"source_identifier": "4.CE", "title": "Computation and Estimation", "strand": "Computation and Estimation", "description": "Solve multi-step and multiplicative comparison problems."},
    {"source_identifier": "4.NS", "title": "Number and Number Sense", "strand": "Number and Number Sense", "description": "Understand place value, fractions, and decimals."},
    {"source_identifier": "4.MG", "title": "Measurement and Geometry", "strand": "Measurement and Geometry", "description": "Measure, convert, and classify geometric figures."},
]

VA_GRADE5_EXPECTATIONS = [
    {"source_identifier": "5.CE", "title": "Computation and Estimation", "strand": "Computation and Estimation", "description": "Evaluate expressions and solve problems involving fractions and decimals."},
    {"source_identifier": "5.NS", "title": "Number and Number Sense", "strand": "Number and Number Sense", "description": "Understand place value and number relationships with decimals and fractions."},
    {"source_identifier": "5.MG", "title": "Measurement and Geometry", "strand": "Measurement and Geometry", "description": "Convert units, measure volume, and graph points in the coordinate plane."},
]


PROBLEM_BANKS: dict[str, list[dict]] = {
    "EQUAL_GROUPS": [
        {"prompt": "There are {a} groups of {b} counters. How many counters are there in all?", "params": [(3, 4), (5, 6), (4, 7), (6, 8)], "answer_field": "product"},
    ],
    "EQUAL_SHARING": [
        {"prompt": "{a} counters are shared equally among {b} groups. How many counters are in each group?", "params": [(12, 3), (24, 4), (36, 6), (45, 5)], "answer_field": "quotient"},
    ],
    "MULTIPLICATION_WITHIN_100": [
        {"prompt": "What is {a} × {b}?", "params": [(3, 4), (5, 6), (7, 8), (9, 9), (6, 7), (4, 9), (8, 7), (5, 8)], "answer_field": "product"},
    ],
    "DIVISION_WITHIN_100": [
        {"prompt": "What is {a} ÷ {b}?", "params": [(24, 3), (42, 6), (54, 9), (48, 8), (35, 5), (72, 8), (27, 3), (56, 7)], "answer_field": "quotient"},
    ],
    "WORD_PROBLEM_MULTIPLY_DIVIDE_100": [
        {"prompt": "There are {a} boxes with {b} pencils in each box. How many pencils are there in all?", "params": [(3, 4), (5, 6), (7, 8), (6, 7)], "answer_field": "product", "operation": "×"},
        {"prompt": "{a} stickers are shared equally among {b} students. How many stickers does each student get?", "params": [(24, 4), (36, 6), (48, 8), (54, 9)], "answer_field": "quotient", "operation": "÷"},
    ],
    "WORD_PROBLEM_ADD_SUB_100": [
        {"prompt": "A library has {a} fiction books and {b} nonfiction books. How many books are there?", "params": [(24, 35), (47, 28), (56, 39), (63, 19)], "answer_field": "sum", "operation": "+"},
        {"prompt": "There are {a} sheets of paper. {b} are used. How many are left?", "params": [(50, 23), (72, 38), (65, 29), (81, 47)], "answer_field": "diff", "operation": "-"},
    ],
    "COMPARE_NUMBERS": [
        {"prompt": "Compare: {a} ___ {b}. Use >, <, or =.", "params": [(245, 254), (1002, 998), (3456, 3456), (7890, 7809), (1234, 1243), (5678, 5687), (999, 1000), (3200, 320)], "answer_field": "symbol"},
    ],
    "PLACE_VALUE_BASE_TEN": [
        {"prompt": "How many hundreds, tens, and ones make {number}?", "params": [(247, 2, 4, 7), (385, 3, 8, 5), (506, 5, 0, 6), (920, 9, 2, 0)], "answer_field": "place_value"},
        {"prompt": "How many thousands, hundreds, tens, and ones make {number}?", "params": [(1247, 1, 2, 4, 7), (5385, 5, 3, 8, 5), (7006, 7, 0, 0, 6), (3920, 3, 9, 2, 0)], "answer_field": "place_value"},
    ],
    "ROUNDING": [
        {"prompt": "Round {number} to the nearest {place}.", "params": [(47, 10, 50), (123, 100, 100), (256, 10, 260), (349, 100, 300), (1523, 100, 1500), (2891, 1000, 3000), (445, 10, 450), (738, 100, 700)], "answer_field": "rounded"},
    ],
    "UNIT_FRACTION": [
        {"prompt": "A whole is divided into {denominator} equal parts. What fraction is 1 of those parts?", "params": [(3,), (4,), (6,), (8,)], "answer_field": "unit_fraction"},
    ],
    "FRACTION_NUMBER_LINE": [
        {"prompt": "Where is the fraction {numerator}/{denominator} located on a number line from 0 to 1?", "params": [(1, 3), (2, 4), (3, 8), (5, 6)], "answer_field": "fraction"},
    ],
    "FRACTION_EQUIVALENCE": [
        {"prompt": "Find a fraction equivalent to {numerator}/{denominator}.", "params": [(1, 2), (2, 3), (3, 4), (2, 5)], "answer_field": "equivalent_fraction"},
    ],
    "FRACTION_COMPARE": [
        {"prompt": "Compare: {n1}/{d1} ___ {n2}/{d2}. Use >, <, or =.", "params": [(1, 2, 1, 3), (2, 3, 3, 4), (3, 8, 2, 8), (4, 6, 2, 3)], "answer_field": "symbol"},
    ],
    "TIME_TO_5_MINUTES": [
        {"prompt": "What time is {hour}:{minute:02d} on an analog clock?", "params": [(3, 15), (7, 30), (11, 45), (1, 20), (5, 5), (9, 50), (2, 25), (6, 40)], "answer_field": "time"},
    ],
    "ELAPSED_TIME": [
        {"prompt": "A movie starts at {start} and ends at {end}. How many minutes long is the movie?", "params": [("3:15", "3:45", 30), ("7:20", "8:05", 45), ("1:10", "2:00", 50), ("5:30", "6:15", 45)], "answer_field": "elapsed"},
    ],
    "BAR_GRAPH_READ": [
        {"prompt": "A bar graph shows votes for favorite colors: red=4, blue=7, green=3, yellow=6. How many votes did blue receive?", "params": [("blue", 7)], "answer_field": "count"},
        {"prompt": "A bar graph shows votes for favorite colors: red=8, blue=5, green=6, yellow=2. How many votes did red receive?", "params": [("red", 8)], "answer_field": "count"},
    ],
    "PICTURE_GRAPH_READ": [
        {"prompt": "A picture graph shows pets: dog=5, cat=3, bird=4, fish=2. How many dogs are there?", "params": [("dog", 5)], "answer_field": "count"},
        {"prompt": "A picture graph shows pets: dog=2, cat=6, bird=3, fish=5. How many cats are there?", "params": [("cat", 6)], "answer_field": "count"},
    ],
    "RECTANGLE_AREA": [
        {"prompt": "A rectangle has {rows} rows of {columns} unit squares. What is its area?", "params": [(3, 4, 12), (5, 6, 30), (7, 4, 28), (6, 6, 36)], "answer_field": "area"},
    ],
    "AREA_PERIMETER_RECTANGLE": [
        {"prompt": "A rectangle has length {length} units and width {width} units. What is its {measure}?", "params": [(4, 5, "perimeter", 18), (6, 3, "area", 18), (7, 2, "perimeter", 18), (5, 5, "area", 25)], "answer_field": "measure"},
    ],
    "CLASSIFY_SHAPE": [
        {"prompt": "How many sides does a {shape} have?", "params": [("triangle", 3), ("quadrilateral", 4), ("pentagon", 5), ("hexagon", 6), ("octagon", 8)], "answer_field": "sides"},
    ],
    "NUMBER_PATTERN": [
        {"prompt": "What number completes the pattern? {sequence}", "params": [("count_by_5", 5, 25), ("count_by_10", 10, 50), ("count_by_2", 2, 12), ("count_by_100", 100, 400)], "answer_field": "next"},
    ],
    "MULTI_DIGIT_MULTIPLICATION": [
        {"prompt": "What is {a} × {b}?", "params": [(23, 4, 92), (156, 3, 468), (45, 67, 3015), (29, 38, 1102), (123, 5, 615), (34, 26, 884), (209, 7, 1463), (58, 49, 2842)], "answer_field": "product"},
    ],
    "LONG_DIVISION": [
        {"prompt": "What is {a} ÷ {b}?", "params": [(84, 4, 21), (735, 5, 147), (128, 8, 16), (912, 6, 152), (408, 3, 136), (675, 9, 75), (525, 7, 75), (884, 4, 221)], "answer_field": "quotient"},
    ],
    "FRACTION_ADD_SUBTRACT_LIKE": [
        {"prompt": "What is {n1}/{d} {op} {n2}/{d}?", "params": [(1, 4, 2, 4, "+", 3), (5, 6, 2, 6, "-", 3), (3, 8, 2, 8, "+", 5), (7, 10, 4, 10, "-", 3)], "answer_field": "result"},
    ],
    "MULTIPLY_FRACTION_BY_WHOLE": [
        {"prompt": "What is {whole} × {numerator}/{denominator}?", "params": [(3, 2, 3, 2), (4, 1, 5, 4), (5, 3, 4, 15), (2, 2, 7, 4)], "answer_field": "product"},
    ],
    "DECIMAL_PLACE_VALUE": [
        {"prompt": "What is the value of the digit {digit} in the number {number}?", "params": [(3, 3.45, "tenths"), (5, 2.05, "hundredths"), (7, 7.89, "ones"), (6, 0.67, "tenths")], "answer_field": "value"},
    ],
    "MEASUREMENT_CONVERSION": [
        {"prompt": "Convert {value} {from_unit} to {to_unit}.", "params": [(3, "m", "cm", 300), (5, "km", "m", 5000), (2, "kg", "g", 2000), (4, "L", "mL", 4000), (7, "ft", "in", 84), (6, "ft", "yd", 2), (9, "cm", "mm", 90), (1.5, "m", "cm", 150)], "answer_field": "converted"},
    ],
    "ANGLE_MEASUREMENT": [
        {"prompt": "What is the measure of an angle that is {relation} a right angle?", "params": [("acute", 45), ("obtuse", 120), ("one half of a", 45), ("one-third of a straight", 60)], "answer_field": "degrees"},
    ],
    "LINES_PARALLEL_PERPENDICULAR": [
        {"prompt": "{description}", "params": [("Two lines in the same plane never meet. Are they parallel or perpendicular?", "parallel"), ("Two lines meet at a right angle. Are they parallel or perpendicular?", "perpendicular")], "answer_field": "relation"},
    ],
    "ADD_SUBTRACT_UNLIKE_FRACTIONS": [
        {"prompt": "What is {n1}/{d1} {op} {n2}/{d2}?", "params": [(1, 2, 1, 4, "+", "3/4"), (3, 4, 1, 6, "-", "7/12"), (2, 3, 1, 5, "+", "13/15"), (5, 6, 1, 2, "-", "1/3")], "answer_field": "result"},
    ],
    "FRACTION_MULTIPLY": [
        {"prompt": "What is {n1}/{d1} of {n2}/{d2}?", "params": [(1, 2, 3, 4, "3/8"), (2, 3, 3, 5, "2/5"), (3, 4, 2, 3, "1/2"), (1, 3, 6, 7, "2/7")], "answer_field": "result"},
    ],
    "MULTIPLY_FRACTIONS": [
        {"prompt": "What is {n1}/{d1} × {n2}/{d2}?", "params": [(1, 2, 3, 4, "3/8"), (2, 3, 3, 5, "2/5"), (3, 4, 2, 3, "1/2"), (1, 3, 6, 7, "2/7")], "answer_field": "result"},
    ],
    "DIVIDE_FRACTIONS": [
        {"prompt": "How many servings of {n}/{d} are in {whole}?", "params": [(1, 2, 3, 6), (1, 4, 2, 8), (2, 3, 4, 6), (1, 3, 5, 15)], "answer_field": "servings"},
    ],
    "POWERS_OF_TEN": [
        {"prompt": "What is 10^{exponent}?", "params": [(2, 100), (3, 1000), (4, 10000), (5, 100000), (1, 10), (3, 1000), (4, 10000), (2, 100)], "answer_field": "power"},
    ],
    "DECIMAL_OPERATIONS": [
        {"prompt": "What is {a} {op} {b}?", "params": [(2.5, "+", 1.4, 3.9), (5.6, "-", 2.3, 3.3), (0.7, "+", 0.25, 0.95), (4.8, "-", 1.9, 2.9), (1.2, "+", 3.45, 4.65), (6.7, "-", 4.08, 2.62), (0.55, "+", 0.45, 1.0), (3.14, "-", 2.0, 1.14)], "answer_field": "result"},
    ],
    "VOLUME": [
        {"prompt": "A rectangular prism has length {l}, width {w}, and height {h}. What is its volume?", "params": [(2, 3, 4, 24), (5, 2, 3, 30), (4, 4, 2, 32), (6, 3, 2, 36), (3, 3, 3, 27), (5, 4, 2, 40), (2, 5, 6, 60), (7, 2, 2, 28)], "answer_field": "volume"},
    ],
    "COORDINATE_PLANE": [
        {"prompt": "What is the ordered pair for the point located {x} units right and {y} units up from the origin?", "params": [(2, 3, "(2, 3)"), (4, 1, "(4, 1)"), (0, 5, "(0, 5)"), (3, 3, "(3, 3)"), (5, 0, "(5, 0)"), (1, 4, "(1, 4)"), (6, 2, "(6, 2)"), (2, 5, "(2, 5)")], "answer_field": "pair"},
    ],
}


def _make_answer(family: str, params: tuple, answer_field: str) -> str:
    if family == "EQUAL_GROUPS":
        a, b = params
        return str(a * b)
    if family == "EQUAL_SHARING":
        a, b = params
        return str(a // b)
    if family == "COMPARE_NUMBERS":
        from fractions import Fraction
        a, b = params
        if a > b:
            return ">"
        if a < b:
            return "<"
        return "="
    if family in {"MULTIPLICATION_WITHIN_100", "WORD_PROBLEM_MULTIPLY_DIVIDE_100"}:
        a, b = params[:2]
        op = params[2] if len(params) > 2 and params[2] == "÷" else "×"
        if op == "÷":
            return str(a // b)
        return str(a * b)
    if family == "WORD_PROBLEM_ADD_SUB_100":
        a, b = params[:2]
        op = params[2] if len(params) > 2 and params[2] == "-" else "+"
        if op == "-":
            return str(a - b)
        return str(a + b)
    if family == "DIVISION_WITHIN_100":
        a, b = params
        return str(a // b)
    if family == "PLACE_VALUE_BASE_TEN":
        if len(params) == 4:
            _number, hundreds, tens, ones = params
            if hundreds == 0:
                return f"{tens} tens and {ones} ones"
            return f"{hundreds} hundreds, {tens} tens, and {ones} ones"
        _number, thousands, hundreds, tens, ones = params
        return f"{thousands} thousands, {hundreds} hundreds, {tens} tens, and {ones} ones"
    if family == "ROUNDING":
        _number, _place, rounded = params
        return str(rounded)
    if family == "UNIT_FRACTION":
        denominator = params[0]
        return f"1/{denominator}"
    if family in {"FRACTION_NUMBER_LINE", "FRACTION_EQUIVALENCE"}:
        numerator, denominator = params[:2]
        if answer_field == "equivalent_fraction":
            return f"{numerator * 2}/{denominator * 2}"
        return f"{numerator}/{denominator}"
    if family == "FRACTION_COMPARE":
        from fractions import Fraction
        n1, d1, n2, d2 = params
        f1 = Fraction(n1, d1)
        f2 = Fraction(n2, d2)
        if f1 > f2:
            return ">"
        if f1 < f2:
            return "<"
        return "="
    if family == "TIME_TO_5_MINUTES":
        hour, minute = params
        return f"{hour}:{minute:02d}"
    if family == "ELAPSED_TIME":
        _start, _end, elapsed = params
        return str(elapsed)
    if family in {"BAR_GRAPH_READ", "PICTURE_GRAPH_READ"}:
        _category, value = params
        return str(value)
    if family == "RECTANGLE_AREA":
        rows, columns, _area = params
        return str(rows * columns)
    if family == "AREA_PERIMETER_RECTANGLE":
        length, width, measure, _ = params
        if measure == "area":
            return str(length * width)
        return str(2 * (length + width))
    if family == "CLASSIFY_SHAPE":
        _shape, sides = params
        return str(sides)
    if family == "NUMBER_PATTERN":
        _kind, step, start = params
        return str(start + step)
    if family == "MULTI_DIGIT_MULTIPLICATION":
        a, b, _product = params
        return str(a * b)
    if family == "LONG_DIVISION":
        a, b, _quotient = params
        return str(a // b)
    if family == "FRACTION_ADD_SUBTRACT_LIKE":
        n1, _d, n2, _d2, _op, result = params
        return f"{result}/{_d}"
    if family == "MULTIPLY_FRACTION_BY_WHOLE":
        whole, n, d, _product = params
        from fractions import Fraction
        result = Fraction(whole * n, d)
        return f"{result.numerator}/{result.denominator}"
    if family in {"MULTIPLY_FRACTIONS", "FRACTION_MULTIPLY"}:
        n1, d1, n2, d2, _result = params
        from fractions import Fraction
        result = Fraction(n1 * n2, d1 * d2)
        return f"{result.numerator}/{result.denominator}"
    if family == "DECIMAL_PLACE_VALUE":
        _digit, _number, place = params
        return place
    if family == "MEASUREMENT_CONVERSION":
        _value, _from_unit, _to_unit, converted = params
        return str(converted)
    if family == "ANGLE_MEASUREMENT":
        _relation, degrees = params
        return str(degrees)
    if family == "LINES_PARALLEL_PERPENDICULAR":
        _description, relation = params
        return relation
    if family == "ADD_SUBTRACT_UNLIKE_FRACTIONS":
        _n1, _d1, _n2, _d2, _op, result = params
        return result
    if family == "DIVIDE_FRACTIONS":
        n, d, whole, _servings = params
        return str(whole * d // n)
    if family == "POWERS_OF_TEN":
        _exponent, power = params
        return str(power)
    if family == "DECIMAL_OPERATIONS":
        _a, _op, _b, result = params
        return str(result)
    if family == "VOLUME":
        l, w, h, _volume = params
        return str(l * w * h)
    if family == "COORDINATE_PLANE":
        _x, _y, pair = params
        return pair
    raise ValueError(f"Unknown family: {family}")


def _format_prompt(family: str, template: str, params: tuple, answer_field: str) -> str:
    if family == "COMPARE_NUMBERS":
        return template.format(a=params[0], b=params[1])
    if family in {"EQUAL_GROUPS", "WORD_PROBLEM_MULTIPLY_DIVIDE_100", "WORD_PROBLEM_ADD_SUB_100"}:
        return template.format(a=params[0], b=params[1])
    if family == "EQUAL_SHARING":
        return template.format(a=params[0], b=params[1])
    if family in {"MULTIPLICATION_WITHIN_100", "DIVISION_WITHIN_100"}:
        return template.format(a=params[0], b=params[1])
    if family == "PLACE_VALUE_BASE_TEN":
        return template.format(number=params[0])
    if family == "ROUNDING":
        number, place, _rounded = params
        place_name = "ten" if place == 10 else "hundred" if place == 100 else "thousand"
        return template.format(number=number, place=place_name)
    if family == "UNIT_FRACTION":
        return template.format(denominator=params[0])
    if family in {"FRACTION_NUMBER_LINE", "FRACTION_EQUIVALENCE"}:
        return template.format(numerator=params[0], denominator=params[1])
    if family == "FRACTION_COMPARE":
        return template.format(n1=params[0], d1=params[1], n2=params[2], d2=params[3])
    if family == "TIME_TO_5_MINUTES":
        return template.format(hour=params[0], minute=params[1])
    if family == "ELAPSED_TIME":
        return template.format(start=params[0], end=params[1])
    if family in {"BAR_GRAPH_READ", "PICTURE_GRAPH_READ"}:
        return template
    if family == "RECTANGLE_AREA":
        return template.format(rows=params[0], columns=params[1])
    if family == "AREA_PERIMETER_RECTANGLE":
        return template.format(length=params[0], width=params[1], measure=params[2])
    if family == "CLASSIFY_SHAPE":
        return template.format(shape=params[0])
    if family == "NUMBER_PATTERN":
        _kind, step, start = params
        sequence = [start + step * i for i in range(5)] + ["?"]
        return template.format(sequence=", ".join(str(x) for x in sequence))
    if family == "MULTI_DIGIT_MULTIPLICATION":
        return template.format(a=params[0], b=params[1])
    if family == "LONG_DIVISION":
        return template.format(a=params[0], b=params[1])
    if family == "FRACTION_ADD_SUBTRACT_LIKE":
        return template.format(n1=params[0], d=params[1], op=params[4], n2=params[2])
    if family == "MULTIPLY_FRACTION_BY_WHOLE":
        return template.format(whole=params[0], numerator=params[1], denominator=params[2])
    if family in {"MULTIPLY_FRACTIONS", "FRACTION_MULTIPLY"}:
        return template.format(n1=params[0], d1=params[1], n2=params[2], d2=params[3])
    if family == "DECIMAL_PLACE_VALUE":
        return template.format(digit=params[0], number=params[1])
    if family == "MEASUREMENT_CONVERSION":
        return template.format(value=params[0], from_unit=params[1], to_unit=params[2])
    if family == "ANGLE_MEASUREMENT":
        return template.format(relation=params[0])
    if family == "LINES_PARALLEL_PERPENDICULAR":
        return template.format(description=params[0])
    if family == "ADD_SUBTRACT_UNLIKE_FRACTIONS":
        return template.format(n1=params[0], d1=params[1], op=params[4], n2=params[2], d2=params[3])
    if family == "DIVIDE_FRACTIONS":
        return template.format(n=params[0], d=params[1], whole=params[2])
    if family == "POWERS_OF_TEN":
        return template.format(exponent=params[0])
    if family == "DECIMAL_OPERATIONS":
        return template.format(a=params[0], op=params[1], b=params[2])
    if family == "VOLUME":
        return template.format(l=params[0], w=params[1], h=params[2])
    if family == "COORDINATE_PLANE":
        return template.format(x=params[0], y=params[1])
    raise ValueError(f"Unknown family: {family}")


def _make_parameters(family: str, params: tuple) -> dict:
    if family == "EQUAL_GROUPS":
        return {"a": params[0], "b": params[1], "operation": "×"}
    if family == "COMPARE_NUMBERS":
        return {"a": params[0], "b": params[1]}
    if family == "EQUAL_SHARING":
        return {"a": params[0], "b": params[1], "operation": "÷"}
    if family in {"MULTIPLICATION_WITHIN_100", "WORD_PROBLEM_MULTIPLY_DIVIDE_100"}:
        return {"a": params[0], "b": params[1], "operation": "×", "answer": params[0] * params[1]}
    if family == "WORD_PROBLEM_ADD_SUB_100":
        op = params[2] if len(params) > 2 else "+"
        answer = params[0] + params[1] if op == "+" else params[0] - params[1]
        return {"a": params[0], "b": params[1], "operation": op, "answer": answer}
    if family == "DIVISION_WITHIN_100":
        return {"a": params[0], "b": params[1], "operation": "÷"}
    if family == "PLACE_VALUE_BASE_TEN":
        if len(params) == 4:
            return {"number": params[0], "hundreds": params[1], "tens": params[2], "ones": params[3]}
        return {"number": params[0], "thousands": params[1], "hundreds": params[2], "tens": params[3], "ones": params[4]}
    if family == "ROUNDING":
        return {"number": params[0], "place": params[1]}
    if family == "UNIT_FRACTION":
        return {"denominator": params[0]}
    if family == "FRACTION_NUMBER_LINE":
        return {"numerator": params[0], "denominator": params[1]}
    if family == "FRACTION_EQUIVALENCE":
        return {"numerator": params[0], "denominator": params[1]}
    if family == "FRACTION_COMPARE":
        return {"numerator1": params[0], "denominator1": params[1], "numerator2": params[2], "denominator2": params[3]}
    if family == "TIME_TO_5_MINUTES":
        return {"hour": params[0], "minute": params[1]}
    if family == "ELAPSED_TIME":
        return {"start": params[0], "end": params[1], "elapsed_minutes": params[2]}
    if family in {"BAR_GRAPH_READ", "PICTURE_GRAPH_READ"}:
        return {"category": params[0], "value": params[1]}
    if family == "RECTANGLE_AREA":
        return {"rows": params[0], "columns": params[1]}
    if family == "AREA_PERIMETER_RECTANGLE":
        return {"length": params[0], "width": params[1], "measure": params[2]}
    if family == "CLASSIFY_SHAPE":
        return {"shape": params[0], "sides": params[1]}
    if family == "NUMBER_PATTERN":
        return {"start": params[2], "step": params[1]}
    if family == "MULTI_DIGIT_MULTIPLICATION":
        return {"a": params[0], "b": params[1]}
    if family == "LONG_DIVISION":
        return {"a": params[0], "b": params[1]}
    if family == "FRACTION_ADD_SUBTRACT_LIKE":
        return {"numerator1": params[0], "denominator": params[1], "numerator2": params[2], "operation": params[4]}
    if family == "MULTIPLY_FRACTION_BY_WHOLE":
        return {"whole": params[0], "numerator": params[1], "denominator": params[2]}
    if family in {"MULTIPLY_FRACTIONS", "FRACTION_MULTIPLY"}:
        return {"numerator1": params[0], "denominator1": params[1], "numerator2": params[2], "denominator2": params[3]}
    if family == "DECIMAL_PLACE_VALUE":
        return {"digit": params[0], "number": params[1]}
    if family == "MEASUREMENT_CONVERSION":
        return {"value": params[0], "from": params[1], "to": params[2]}
    if family == "ANGLE_MEASUREMENT":
        return {"relation": params[0], "degrees": params[1]}
    if family == "LINES_PARALLEL_PERPENDICULAR":
        return {"relation": params[1]}
    if family == "ADD_SUBTRACT_UNLIKE_FRACTIONS":
        return {"numerator1": params[0], "denominator1": params[1], "numerator2": params[2], "denominator2": params[3], "operation": params[4]}
    if family == "DIVIDE_FRACTIONS":
        return {"numerator": params[0], "denominator": params[1], "whole": params[2]}
    if family == "POWERS_OF_TEN":
        return {"exponent": params[0]}
    if family == "DECIMAL_OPERATIONS":
        return {"a": params[0], "b": params[2], "operation": params[1]}
    if family == "VOLUME":
        return {"length": params[0], "width": params[1], "height": params[2]}
    if family == "COORDINATE_PLANE":
        return {"x": params[0], "y": params[1]}
    raise ValueError(f"Unknown family: {family}")


def _make_problem(skill_index: int, problem_index: int, skill_code: str, family: str, jurisdiction: str, grade: int) -> dict:
    bank = PROBLEM_BANKS[family]
    template_entry = bank[problem_index % len(bank)]
    params = template_entry["params"][problem_index % len(template_entry["params"])]
    prompt = _format_prompt(family, template_entry["prompt"], params, template_entry["answer_field"])
    answer = _make_answer(family, params, template_entry["answer_field"])
    modes = ["diagnostic", "guided", "independent", "mastery"]
    mode = modes[problem_index % 4]
    difficulty = 1 if problem_index < 4 else 2
    key = f"{jurisdiction.lower()}{grade}-{skill_code.split('.')[-1].lower()}-{family.lower()}-{problem_index + 1:02d}"
    return {
        "key": key,
        "family": family,
        "prompt": prompt,
        "canonical_answer": answer,
        "difficulty": difficulty,
        "objective": f"Practice {family.replace('_', ' ').lower()} in {mode} mode.",
        "modes": [mode],
        "parameters": _make_parameters(family, params),
    }


def _build_pack(jurisdiction: str, grade: int) -> dict:
    jdef = JURISDICTIONS[jurisdiction]
    skills = {3: GRADE3_SKILLS, 4: GRADE4_SKILLS, 5: GRADE5_SKILLS}[grade]
    expectations = {3: GRADE3_EXPECTATIONS, 4: GRADE4_EXPECTATIONS, 5: GRADE5_EXPECTATIONS}[grade]
    if jurisdiction == "VA":
        expectations = {
            3: VA_GRADE3_EXPECTATIONS,
            4: VA_GRADE4_EXPECTATIONS,
            5: VA_GRADE5_EXPECTATIONS,
        }[grade]

    version_tag = "2026_27" if jurisdiction == "MD" else "2024_25"
    curriculum_code = f"{jurisdiction}_MATH_{grade}_{version_tag}"
    filename_tag = "mccrs" if jurisdiction == "MD" else "ccss" if jurisdiction == "DC" else "sol"
    filename = f"{jurisdiction.lower()}-grade{grade}-{filename_tag}-{version_tag}.json"

    skill_specs = []
    for idx, skill in enumerate(skills):
        skill_code = skill.local_code.format(jurisdiction=jurisdiction)
        problems = []
        for i in range(8):
            family = skill.families[i % len(skill.families)]
            problems.append(_make_problem(idx, i, skill_code, family, jurisdiction, grade))
        skill_specs.append({
            "code": skill_code,
            "name": skill.name,
            "description": skill.description,
            "difficulty_level": grade,
            "canonical": {
                "code": skill.canonical_code,
                "name": skill.canonical_name,
                "description": skill.canonical_description,
            },
            "standard_refs": list(skill.standards_md_dc if jurisdiction in ("MD", "DC") else skill.standards_va),
            "prerequisite_codes": [prereq.format(jurisdiction=jurisdiction) for prereq in skill.prerequisite_codes],
            "problem_families": list(skill.families),
            "problems": problems,
        })

    pack = {
        "schema_version": 1,
        "jurisdiction": {
            "country_code": "US",
            "code": jdef.code,
            "name": jdef.name,
            "jurisdiction_type": "STATE_PROVINCE_TERRITORY",
            "source_uri": jdef.standards_source_uri,
        },
        "authority": {
            "code": jdef.authority_code,
            "name": jdef.authority_name,
            "authority_type": "STATE_AGENCY",
            "source_uri": jdef.authority_uri,
        },
        "curriculum": {
            "code": curriculum_code,
            "name": f"{jdef.name} Grade {grade} Mathematics — {jdef.version}",
            "version": jdef.version,
            "grade_level": str(grade),
            "source_uri": jdef.standards_source_uri,
        },
        "expectations": [
            {
                "source_identifier": exp["source_identifier"],
                "title": exp["title"],
                "source_uri": jdef.standards_source_uri,
                "strand": exp["strand"],
                "description": exp["description"],
            }
            for exp in expectations
        ],
        "skills": skill_specs,
        "readiness": {
            "minimum_curated_per_skill": 4,
            "required_modes": ["diagnostic", "guided", "independent", "mastery"],
        },
    }

    path = _PACK_DIR / filename
    path.write_text(json.dumps(pack, indent=2))
    print(f"Wrote {path}")
    return pack


def generate() -> None:
    _PACK_DIR.mkdir(parents=True, exist_ok=True)
    for jurisdiction in ("MD", "DC", "VA"):
        for grade in (3, 4, 5):
            _build_pack(jurisdiction, grade)


if __name__ == "__main__":
    generate()
