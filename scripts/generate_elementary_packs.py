"""Generate declarative curriculum packs for DMV elementary grades 1-5.

This is a content-authoring helper, not runtime code. It produces the JSON
packs committed under docs/curriculum/packs/. All problem prompts are
original and jurisdiction-appropriate; they are deterministic inputs to the
application-owned generators and visual renderers.
"""

import json
from dataclasses import dataclass
from pathlib import Path

_PACK_DIR = Path(__file__).parents[1] / "docs/curriculum/packs"


@dataclass(frozen=True)
class Jurisdiction:
    code: str
    name: str
    source_uri: str


@dataclass(frozen=True)
class Authority:
    code: str
    name: str
    source_uri: str


@dataclass(frozen=True)
class StandardDef:
    code: str
    title: str
    strand: str
    description: str


@dataclass(frozen=True)
class SkillDef:
    code: str
    name: str
    description: str
    canonical_code: str
    canonical_name: str
    canonical_description: str
    families: tuple[str, ...]
    prerequisite_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProblemDef:
    key: str
    family: str
    prompt: str
    answer: str
    difficulty: int
    objective: str
    mode: str
    parameters: dict


JURISDICTIONS = {
    "MD": Jurisdiction(
        code="MD",
        name="Maryland",
        source_uri="https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx",
    ),
    "DC": Jurisdiction(
        code="DC",
        name="District of Columbia",
        source_uri="https://osse-migrate.dc.gov/service/district-columbia-standards-learning-0",
    ),
    "VA": Jurisdiction(
        code="VA",
        name="Virginia",
        source_uri="https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics",
    ),
}

AUTHORITIES = {
    "MD": Authority(
        code="MSDE",
        name="Maryland State Department of Education",
        source_uri="https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx",
    ),
    "DC": Authority(
        code="OSSE",
        name="Office of the State Superintendent of Education",
        source_uri="https://osse-migrate.dc.gov/service/district-columbia-standards-learning-0",
    ),
    "VA": Authority(
        code="VDOE",
        name="Virginia Department of Education",
        source_uri="https://www.doe.virginia.gov/teaching-learning-assessment/instruction/mathematics/standards-of-learning-for-mathematics",
    ),
}


def _curriculum_source(jurisdiction: str, grade: int) -> str:
    if jurisdiction == "MD":
        return "https://marylandpublicschools.org/about/pages/dcaa/math/revised-standards.aspx"
    if jurisdiction == "DC":
        return "https://osse-migrate.dc.gov/sites/default/files/dc/sites/osse/page_content/attachments/mathematics-adjusted-blueprintGrades3_0.pdf"
    return "https://www.doe.virginia.gov/teaching-learning-assessment/k-12-standards-instruction/mathematics/2023-sol-instructional-resources"


def _curriculum_name(jurisdiction: str, grade: int) -> str:
    if jurisdiction == "MD":
        return f"Maryland Grade {grade} Mathematics — revised MCCRS"
    if jurisdiction == "DC":
        return f"District of Columbia Grade {grade} Mathematics — Common Core State Standards"
    return f"Virginia Grade {grade} Mathematics — 2023 Standards of Learning"


def _version(jurisdiction: str, grade: int) -> str:
    if jurisdiction == "MD":
        return "MCCRS-revised-SY2026-27"
    if jurisdiction == "DC":
        return "CCSS-OSSE-2024-25"
    return "VDOE-2023-SY2024-25"


def _version_tag(jurisdiction: str, grade: int) -> str:
    if jurisdiction == "MD":
        return "2026_27"
    return "2024_25"


_SKIP = {
    ("MD", 3),
    ("DC", 3),
}


GRADE_CONFIG = {
    1: {
        "md_dc_standards": {
            "1.OA.C": StandardDef(
                "1.OA.C",
                "Add and subtract within 20",
                "Operations and Algebraic Thinking",
                "Demonstrate fluency for addition and subtraction within 10 and apply strategies within 20.",
            ),
            "1.NBT.B": StandardDef(
                "1.NBT.B",
                "Understand place value",
                "Number and Operations in Base Ten",
                "Understand that the two digits of a two-digit number represent amounts of tens and ones.",
            ),
            "1.MD.B": StandardDef(
                "1.MD.B",
                "Tell and write time",
                "Measurement and Data",
                "Tell and write time in hours and half-hours using analog and digital clocks.",
            ),
        },
        "va_standards": {
            "1.NS.1": StandardDef(
                "1.NS.1",
                "Count and represent quantities",
                "Number and Number Sense",
                "Count forward orally by ones to 110, starting at any number.",
            ),
            "1.NS.2": StandardDef(
                "1.NS.2",
                "Represent, compare, and order quantities",
                "Number and Number Sense",
                "Represent, compare, and order quantities up to 120.",
            ),
            "1.MG.1": StandardDef(
                "1.MG.1",
                "Tell time and read a calendar",
                "Measurement and Geometry",
                "Tell time to the hour and half-hour using analog and digital clocks.",
            ),
        },
        "skills": [
            SkillDef(
                "{jurisdiction}{grade}.OA.ADD_SUB_20",
                "Addition and Subtraction within 20",
                "Add and subtract within 20 using objects, drawings, and equations.",
                "MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_20",
                "Addition and Subtraction within 20",
                "Add and subtract whole numbers within 20 with objects, drawings, and equations.",
                ("ADDITION_WITHIN_20", "SUBTRACTION_WITHIN_20"),
            ),
            SkillDef(
                "{jurisdiction}{grade}.NBT.PLACE_VALUE",
                "Place Value: Tens and Ones",
                "Understand two-digit numbers as tens and ones.",
                "MATH.ELEMENTARY.PLACE_VALUE.TENS_ONES",
                "Place Value: Tens and Ones",
                "Understand that the digits of a two-digit number represent tens and ones.",
                ("PLACE_VALUE_BASE_TEN",),
            ),
            SkillDef(
                "{jurisdiction}{grade}.MD.TELL_TIME",
                "Tell Time to Hour and Half-Hour",
                "Read analog and digital clocks to the nearest hour and half-hour.",
                "MATH.ELEMENTARY.MEASUREMENT.TELL_TIME_HOUR_HALF_HOUR",
                "Tell Time to Hour and Half-Hour",
                "Tell and write time in hours and half-hours using analog and digital clocks.",
                ("TIME_TO_HOUR_HALF_HOUR",),
                ("{jurisdiction}{grade}.OA.ADD_SUB_20",),
            ),
        ],
    },
    2: {
        "md_dc_standards": {
            "2.OA.A": StandardDef(
                "2.OA.A",
                "Represent and solve problems involving addition and subtraction",
                "Operations and Algebraic Thinking",
                "Use addition and subtraction within 100 to solve one- and two-step word problems.",
            ),
            "2.NBT.B": StandardDef(
                "2.NBT.B",
                "Use place value understanding and properties of operations to add and subtract",
                "Number and Operations in Base Ten",
                "Fluently add and subtract within 1000 using strategies based on place value.",
            ),
            "2.MD.C": StandardDef(
                "2.MD.C",
                "Work with time and money",
                "Measurement and Data",
                "Tell and write time from analog and digital clocks to the nearest five minutes and work with money.",
            ),
        },
        "va_standards": {
            "2.NS.1": StandardDef(
                "2.NS.1",
                "Read, write, and identify numbers",
                "Number and Number Sense",
                "Read, write, and identify numbers to 999.",
            ),
            "2.CE.1": StandardDef(
                "2.CE.1",
                "Solve problems using addition and subtraction",
                "Computation and Estimation",
                "Solve single-step practical problems involving addition and subtraction within 1000.",
            ),
            "2.MG.1": StandardDef(
                "2.MG.1",
                "Tell time and read a calendar",
                "Measurement and Geometry",
                "Tell time to the nearest five minutes using analog and digital clocks.",
            ),
        },
        "skills": [
            SkillDef(
                "{jurisdiction}{grade}.OA.ADD_SUB_100",
                "Addition and Subtraction within 100",
                "Add and subtract within 100 using strategies based on place value.",
                "MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_100",
                "Addition and Subtraction within 100",
                "Add and subtract whole numbers within 100 using place-value strategies.",
                ("ADDITION_WITHIN_100", "SUBTRACTION_WITHIN_100"),
            ),
            SkillDef(
                "{jurisdiction}{grade}.NBT.PLACE_VALUE_3DIGIT",
                "Place Value: Hundreds, Tens, Ones",
                "Understand three-digit numbers as hundreds, tens, and ones.",
                "MATH.ELEMENTARY.PLACE_VALUE.HUNDREDS_TENS_ONES",
                "Place Value: Hundreds, Tens, Ones",
                "Understand that the digits of a three-digit number represent hundreds, tens, and ones.",
                ("PLACE_VALUE_BASE_TEN",),
                ("{jurisdiction}{grade}.OA.ADD_SUB_100",),
            ),
            SkillDef(
                "{jurisdiction}{grade}.MD.MONEY",
                "Count Money",
                "Count collections of coins and bills and solve money word problems.",
                "MATH.ELEMENTARY.MEASUREMENT.MONEY_COUNT",
                "Count Money",
                "Determine the value of a collection of coins and bills and solve money word problems.",
                ("MONEY_COUNT",),
                ("{jurisdiction}{grade}.OA.ADD_SUB_100",),
            ),
        ],
    },
    3: {
        "md_dc_standards": {
            "3.OA.A": StandardDef(
                "3.OA.A",
                "Represent and solve problems involving multiplication and division",
                "Operations and Algebraic Thinking",
                "Interpret products and quotients of whole numbers and solve word problems.",
            ),
            "3.NF.A": StandardDef(
                "3.NF.A",
                "Develop understanding of fractions as numbers",
                "Number and Operations—Fractions",
                "Understand fractions 1/b and a/b and represent them on a number line.",
            ),
            "3.MD.C": StandardDef(
                "3.MD.C",
                "Geometric measurement: understand concepts of area",
                "Measurement and Data",
                "Recognize area as an attribute of plane figures and relate area to multiplication.",
            ),
        },
        "va_standards": {
            "3.NS.3": StandardDef(
                "3.NS.3",
                "Represent and compare fractions",
                "Number and Number Sense",
                "Represent and compare fractions with denominators of 2, 3, 4, 5, 6, 8, and 10.",
            ),
            "3.CE.2": StandardDef(
                "3.CE.2",
                "Solve problems involving multiplication and division",
                "Computation and Estimation",
                "Solve practical problems involving multiplication and division with whole numbers.",
            ),
            "3.MG.2": StandardDef(
                "3.MG.2",
                "Understand area and perimeter",
                "Measurement and Geometry",
                "Determine the area and perimeter of rectangles and squares.",
            ),
        },
        "skills": [
            SkillDef(
                "{jurisdiction}{grade}.OA.EQUAL_GROUPS",
                "Multiplication as Equal Groups",
                "Interpret products as equal groups and arrays.",
                "MATH.ELEMENTARY.MULTIPLICATION.EQUAL_GROUPS",
                "Multiplication as Equal Groups",
                "Understand multiplication as equal groups, arrays, and repeated addition.",
                ("EQUAL_GROUPS",),
            ),
            SkillDef(
                "{jurisdiction}{grade}.OA.EQUAL_SHARING",
                "Division as Equal Sharing",
                "Interpret quotients through fair sharing and groups of a known size.",
                "MATH.ELEMENTARY.DIVISION.EQUAL_SHARING",
                "Division as Equal Sharing",
                "Understand division as fair sharing and as finding an unknown group size or number of groups.",
                ("EQUAL_SHARING",),
                ("{jurisdiction}{grade}.OA.EQUAL_GROUPS",),
            ),
            SkillDef(
                "{jurisdiction}{grade}.NF.UNIT_FRACTION",
                "Unit Fractions as Numbers",
                "Understand 1/b as one equal part of a whole and build fractions from it.",
                "MATH.ELEMENTARY.FRACTION.UNIT",
                "Unit Fractions as Numbers",
                "Understand unit fractions 1/b and build non-unit fractions a/b from unit fractions.",
                ("UNIT_FRACTION",),
                ("{jurisdiction}{grade}.OA.EQUAL_SHARING",),
            ),
            SkillDef(
                "{jurisdiction}{grade}.MD.RECTANGLE_AREA",
                "Rectangle Area with Unit Squares",
                "Relate rectangular arrays, unit squares, and multiplication to area.",
                "MATH.ELEMENTARY.MEASUREMENT.RECTANGLE_AREA",
                "Rectangle Area with Unit Squares",
                "Understand area as covering with unit squares and relate it to multiplication.",
                ("RECTANGLE_AREA",),
                ("{jurisdiction}{grade}.OA.EQUAL_GROUPS",),
            ),
        ],
    },
    4: {
        "md_dc_standards": {
            "4.NBT.B": StandardDef(
                "4.NBT.B",
                "Use place value understanding and properties of operations to perform multi-digit arithmetic",
                "Number and Operations in Base Ten",
                "Multiply whole numbers and find whole-number quotients and remainders.",
            ),
            "4.NF.A": StandardDef(
                "4.NF.A",
                "Extend understanding of fraction equivalence and ordering",
                "Number and Operations—Fractions",
                "Explain why fractions are equivalent using visual models and generate equivalent fractions.",
            ),
            "4.MD.C": StandardDef(
                "4.MD.C",
                "Geometric measurement: understand concepts of angle",
                "Measurement and Data",
                "Recognize angles as geometric shapes and understand concepts of angle measurement.",
            ),
        },
        "va_standards": {
            "4.NS.4": StandardDef(
                "4.NS.4",
                "Compare and order decimals and fractions",
                "Number and Number Sense",
                "Compare and order fractions and mixed numbers having denominators of 2, 3, 4, 5, 6, 8, 10, and 12.",
            ),
            "4.CE.2": StandardDef(
                "4.CE.2",
                "Solve practical problems involving multiplication and division",
                "Computation and Estimation",
                "Solve practical problems involving multiplication and division of whole numbers.",
            ),
            "4.MG.3": StandardDef(
                "4.MG.3",
                "Identify and describe geometric figures",
                "Measurement and Geometry",
                "Identify and describe points, lines, line segments, rays, angles, and triangles.",
            ),
        },
        "skills": [
            SkillDef(
                "{jurisdiction}{grade}.NBT.MULTIPLY_DIVIDE",
                "Multi-Digit Multiplication and Division",
                "Multiply multi-digit whole numbers and find quotients with remainders.",
                "MATH.ELEMENTARY.ARITHMETIC.MULTI_DIGIT_MULTIPLY_DIVIDE",
                "Multi-Digit Multiplication and Division",
                "Multiply multi-digit whole numbers and divide to find quotients and remainders.",
                ("MULTI_DIGIT_MULTIPLICATION", "LONG_DIVISION"),
            ),
            SkillDef(
                "{jurisdiction}{grade}.NF.FRACTION_EQUIVALENCE",
                "Fraction Equivalence and Ordering",
                "Explain and generate equivalent fractions and compare fractions.",
                "MATH.ELEMENTARY.FRACTION.EQUIVALENCE_ORDERING",
                "Fraction Equivalence and Ordering",
                "Explain why fractions are equivalent and generate equivalent fractions using visual models.",
                ("FRACTION_EQUIVALENCE", "FRACTION_ADD_SUBTRACT_LIKE"),
            ),
            SkillDef(
                "{jurisdiction}{grade}.MD.ANGLE",
                "Angle Measurement",
                "Measure angles in whole-number degrees using a protractor and sketch angles.",
                "MATH.ELEMENTARY.MEASUREMENT.ANGLE_DEGREES",
                "Angle Measurement",
                "Understand angle measurement and measure angles in whole-number degrees.",
                ("ANGLE_MEASUREMENT",),
                ("{jurisdiction}{grade}.NBT.MULTIPLY_DIVIDE",),
            ),
        ],
    },
    5: {
        "md_dc_standards": {
            "5.NBT.B": StandardDef(
                "5.NBT.B",
                "Perform operations with multi-digit whole numbers and decimals",
                "Number and Operations in Base Ten",
                "Add, subtract, multiply, and divide decimals to hundredths.",
            ),
            "5.NF.B": StandardDef(
                "5.NF.B",
                "Apply and extend previous understandings of multiplication and division to multiply and divide fractions",
                "Number and Operations—Fractions",
                "Interpret multiplication as scaling and solve real-world problems involving fraction operations.",
            ),
            "5.G.A": StandardDef(
                "5.G.A",
                "Graph points on the coordinate plane",
                "Geometry",
                "Use a pair of perpendicular number lines to define a coordinate system and graph points.",
            ),
        },
        "va_standards": {
            "5.NS.3": StandardDef(
                "5.NS.3",
                "Represent and compare decimals",
                "Number and Number Sense",
                "Represent and identify equivalencies among fractions and decimals and compare fractions and decimals.",
            ),
            "5.CE.3": StandardDef(
                "5.CE.3",
                "Solve single-step and multistep practical problems involving fractions and decimals",
                "Computation and Estimation",
                "Solve single-step and multistep practical problems involving addition, subtraction, multiplication, and division of fractions and decimals.",
            ),
            "5.MG.4": StandardDef(
                "5.MG.4",
                "Understand and apply concepts of perimeter, area, and volume",
                "Measurement and Geometry",
                "Solve practical problems involving perimeter, area, and volume.",
            ),
        },
        "skills": [
            SkillDef(
                "{jurisdiction}{grade}.NBT.DECIMAL_OPERATIONS",
                "Decimal Place Value and Operations",
                "Understand decimal place value and perform operations with decimals to hundredths.",
                "MATH.ELEMENTARY.DECIMAL.PLACE_VALUE_OPERATIONS",
                "Decimal Place Value and Operations",
                "Understand decimal place value through thousandths and perform decimal operations.",
                ("DECIMAL_PLACE_VALUE",),
            ),
            SkillDef(
                "{jurisdiction}{grade}.NF.FRACTION_OPERATIONS",
                "Fraction Multiplication and Division",
                "Multiply and divide fractions in real-world contexts.",
                "MATH.ELEMENTARY.FRACTION.MULTIPLY_DIVIDE",
                "Fraction Multiplication and Division",
                "Apply previous understandings of multiplication and division to fractions.",
                ("FRACTION_MULTIPLY", "FRACTION_ADD_SUBTRACT_LIKE"),
                ("{jurisdiction}{grade}.NBT.DECIMAL_OPERATIONS",),
            ),
            SkillDef(
                "{jurisdiction}{grade}.G.COORDINATE_PLANE",
                "Coordinate Plane",
                "Graph ordered pairs on a coordinate plane and interpret coordinate values.",
                "MATH.ELEMENTARY.GEOMETRY.COORDINATE_PLANE",
                "Coordinate Plane",
                "Use a pair of perpendicular number lines to define a coordinate system and graph points.",
                ("COORDINATE_PLANE",),
                ("{jurisdiction}{grade}.NF.FRACTION_OPERATIONS",),
            ),
        ],
    },
}


PROBLEM_TEMPLATES: dict[str, list[dict]] = {
    "ADDITION_WITHIN_20": [
        {"prompt": "{a} apples and {b} apples are on the table. How many apples are there?", "answer": "{total}", "objective": "Add within 20 using a ten-frame model.", "params": [(5, 4), (7, 6), (8, 9), (6, 7)]},
    ],
    "SUBTRACTION_WITHIN_20": [
        {"prompt": "There are {a} birds on a branch. {b} fly away. How many birds are left?", "answer": "{total}", "objective": "Subtract within 20 using a ten-frame model.", "params": [(12, 5), (15, 7), (17, 9), (14, 6)]},
    ],
    "ADDITION_WITHIN_100": [
        {"prompt": "A school has {a} fiction books and {b} nonfiction books. How many books are there?", "answer": "{total}", "objective": "Add two-digit numbers within 100 using place-value strategies.", "params": [(24, 35), (47, 28), (56, 39), (63, 19)]},
    ],
    "SUBTRACTION_WITHIN_100": [
        {"prompt": "There are {a} crayons in a box. {b} are used. How many crayons are left?", "answer": "{total}", "objective": "Subtract two-digit numbers within 100 using place-value strategies.", "params": [(50, 23), (72, 38), (65, 29), (81, 47)]},
    ],
    "PLACE_VALUE_BASE_TEN": [
        {"prompt": "How many tens and ones make {number}?", "answer": "{tens} tens and {ones} ones", "objective": "Decompose two-digit numbers into tens and ones.", "params": [("tens_and_ones", 45, 4, 5, 0), ("tens_and_ones", 63, 6, 3, 0), ("hundreds_tens_ones", 247, 2, 4, 7), ("hundreds_tens_ones", 385, 3, 8, 5)]},
    ],
    "MONEY_COUNT": [
        {"prompt": "What is the total value of {q} quarter(s), {d} dime(s), {n} nickel(s), and {p} penny(ies)?", "answer": "{answer}", "objective": "Count mixed coin collections.", "params": [(1, 1, 1, 1), (2, 0, 1, 3), (0, 3, 2, 4), (1, 2, 0, 0)]},
    ],
    "TIME_TO_HOUR_HALF_HOUR": [
        {"prompt": "What time is shown when the hour hand points to {hour} and the minute hand points to 12?", "answer": "{hour}:00", "objective": "Read time to the nearest hour.", "params": [("hour", 3, 0), ("hour", 7, 0), ("half", 4, 30), ("half", 9, 30)]},
    ],
    "EQUAL_GROUPS": [
        {"prompt": "There are {rows} rows with {columns} objects in each row. How many objects are there?", "answer": "{total}", "objective": "Interpret products as equal groups or arrays.", "params": [(3, 4, 12), (5, 2, 10), (6, 7, 42), (8, 4, 32)]},
    ],
    "EQUAL_SHARING": [
        {"prompt": "{total} objects are shared equally among {groups} groups. How many objects are in each group?", "answer": "{group_size}", "objective": "Interpret quotients as equal sharing.", "params": [(12, 3, 4), (20, 4, 5), (28, 7, 4), (36, 6, 6)]},
    ],
    "UNIT_FRACTION": [
        {"prompt": "A whole is divided into {denominator} equal parts. What fraction is {numerator} of those parts?", "answer": "{numerator}/{denominator}", "objective": "Understand unit and non-unit fractions.", "params": [(1, 4), (1, 6), (3, 5), (2, 8)]},
    ],
    "RECTANGLE_AREA": [
        {"prompt": "A rectangle has {rows} rows of {columns} unit squares. What is its area in square units?", "answer": "{total}", "objective": "Relate rectangular arrays to area.", "params": [(3, 5, 15), (4, 6, 24), (5, 7, 35), (6, 8, 48)]},
    ],
    "MULTI_DIGIT_MULTIPLICATION": [
        {"prompt": "What is {a} × {b}?", "answer": "{total}", "objective": "Multiply multi-digit whole numbers.", "params": [(23, 4, 92), (15, 6, 90), (34, 7, 238), (125, 3, 375)]},
    ],
    "LONG_DIVISION": [
        {"prompt": "What is {dividend} ÷ {divisor}?", "answer": "{quotient}", "objective": "Divide to find whole-number quotients.", "params": [(48, 4, 12), (72, 6, 12), (96, 8, 12), (105, 5, 21)]},
    ],
    "FRACTION_EQUIVALENCE": [
        {"prompt": "What fraction with denominator {target_denominator} is equivalent to {original_numerator}/{original_denominator}?", "answer": "{target_numerator}/{target_denominator}", "objective": "Generate equivalent fractions.", "params": [(1, 2, 2, 4), (2, 3, 4, 6), (1, 4, 3, 12), (3, 4, 6, 8)]},
    ],
    "FRACTION_ADD_SUBTRACT_LIKE": [
        {"prompt": "What is {n1}/{denominator} {op} {n2}/{denominator}?", "answer": "{answer}", "objective": "Add and subtract fractions with like denominators.", "params": [(1, 2, 3, 1, "+", "2/3"), (3, 4, 1, 4, "-", "2/4"), (2, 5, 1, 5, "+", "3/5"), (5, 6, 2, 6, "-", "3/6")]},
    ],
    "FRACTION_MULTIPLY": [
        {"prompt": "What is {n1}/{d1} × {n2}/{d2}?", "answer": "{answer}", "objective": "Multiply fractions in context.", "params": [(1, 2, 1, 3, "1/6"), (2, 3, 3, 4, "6/12"), (1, 5, 2, 3, "2/15"), (3, 4, 2, 5, "6/20")]},
    ],
    "DECIMAL_PLACE_VALUE": [
        {"prompt": "What is the value of the {place} digit in {number}?", "answer": "{digit}", "objective": "Understand decimal place value.", "params": [("tenths", 0.4, 4), ("tenths", 0.7, 7), ("hundredths", 0.25, 5), ("hundredths", 0.63, 3)]},
    ],
    "ANGLE_MEASUREMENT": [
        {"prompt": "What is the measure of an angle that is {angle} degrees?", "answer": "{angle}", "objective": "Measure angles in whole-number degrees.", "params": [(45,), (60,), (90,), (120,)]},
    ],
    "COORDINATE_PLANE": [
        {"prompt": "What ordered pair is located at ({x}, {y}) on a coordinate grid?", "answer": "({x}, {y})", "objective": "Identify and write ordered pairs.", "params": [(2, 3), (5, 1), (0, 4), (7, 6)]},
    ],
}


MODE_ORDER = ("diagnostic", "guided", "independent", "mastery")


def _format_answer(template: str, mapping: dict) -> str:
    return template.format(**mapping)


def _make_problem(family: str, index: int, jurisdiction: str, grade: int, skill_code: str) -> dict:
    templates = PROBLEM_TEMPLATES[family]
    template = templates[index % len(templates)]
    params_raw = template["params"][index % len(template["params"])]

    params: dict
    answer_mapping: dict
    if family == "PLACE_VALUE_BASE_TEN":
        _, number, tens, ones, hundreds = params_raw
        params = {"number": number, "tens": tens, "ones": ones, "hundreds": hundreds, "place": params_raw[0]}
        if hundreds:
            answer_mapping = {"number": number, "tens": tens, "ones": ones, "hundreds": hundreds}
        else:
            answer_mapping = {"number": number, "tens": tens, "ones": ones, "hundreds": 0}
    elif family == "MONEY_COUNT":
        q, d, n, p = params_raw
        total = q * 25 + d * 10 + n * 5 + p
        dollars = total // 100
        cents = total % 100
        answer = f"${dollars}.{cents:02d}" if dollars else f"${cents / 100:.2f}"
        params = {"quarters": q, "dimes": d, "nickels": n, "pennies": p, "total_cents": total}
        answer_mapping = {"q": q, "d": d, "n": n, "p": p, "answer": answer}
    elif family == "TIME_TO_HOUR_HALF_HOUR":
        _, hour, minute = params_raw
        params = {"hour": hour, "minute": minute}
        answer_mapping = {"hour": hour, "minute": minute}
    elif family in {"EQUAL_GROUPS", "RECTANGLE_AREA"}:
        rows, columns, total = params_raw
        params = {"rows": rows, "columns": columns, "unit": "square units" if family == "RECTANGLE_AREA" else "objects"}
        answer_mapping = {"rows": rows, "columns": columns, "total": total}
    elif family == "EQUAL_SHARING":
        total, groups, group_size = params_raw
        params = {"total": total, "groups": groups, "group_size": group_size}
        answer_mapping = {"total": total, "groups": groups, "group_size": group_size}
    elif family == "UNIT_FRACTION":
        numerator, denominator = params_raw
        params = {"numerator": numerator, "denominator": denominator}
        answer_mapping = {"numerator": numerator, "denominator": denominator}
    elif family in {"ADDITION_WITHIN_20", "ADDITION_WITHIN_100"}:
        a, b = params_raw
        params = {"a": a, "b": b, "operation": "+"}
        answer_mapping = {"a": a, "b": b, "total": a + b}
    elif family in {"SUBTRACTION_WITHIN_20", "SUBTRACTION_WITHIN_100"}:
        a, b = params_raw
        params = {"a": a, "b": b, "operation": "-"}
        answer_mapping = {"a": a, "b": b, "total": a - b}
    elif family == "MULTI_DIGIT_MULTIPLICATION":
        a, b, total = params_raw
        params = {"a": a, "b": b, "operation": "×"}
        answer_mapping = {"a": a, "b": b, "total": total}
    elif family == "LONG_DIVISION":
        dividend, divisor, quotient = params_raw
        params = {"dividend": dividend, "divisor": divisor, "quotient": quotient, "operation": "÷"}
        answer_mapping = {"dividend": dividend, "divisor": divisor, "quotient": quotient}
    elif family == "FRACTION_EQUIVALENCE":
        original_numerator, original_denominator, multiplier, target_denominator = params_raw
        target_numerator = original_numerator * multiplier
        params = {
            "original_numerator": original_numerator,
            "original_denominator": original_denominator,
            "multiplier": multiplier,
            "target_numerator": target_numerator,
            "target_denominator": target_denominator,
        }
        answer_mapping = {
            "original_numerator": original_numerator,
            "original_denominator": original_denominator,
            "target_numerator": target_numerator,
            "target_denominator": target_denominator,
        }
    elif family == "FRACTION_ADD_SUBTRACT_LIKE":
        n1, denominator, n2, _, op, answer = params_raw
        params = {"n1": n1, "n2": n2, "denominator": denominator, "operation": op}
        answer_mapping = {"n1": n1, "n2": n2, "denominator": denominator, "op": op, "answer": answer}
    elif family == "FRACTION_MULTIPLY":
        n1, d1, n2, d2, answer = params_raw
        params = {"n1": n1, "d1": d1, "n2": n2, "d2": d2}
        answer_mapping = {"n1": n1, "d1": d1, "n2": n2, "d2": d2, "answer": answer}
    elif family == "DECIMAL_PLACE_VALUE":
        place, number, digit = params_raw
        params = {"number": number, "place": place, "digit": digit}
        answer_mapping = {"number": number, "place": place, "digit": digit}
    elif family == "ANGLE_MEASUREMENT":
        angle = params_raw[0]
        params = {"angle": angle}
        answer_mapping = {"angle": angle}
    elif family == "COORDINATE_PLANE":
        x, y = params_raw
        params = {"x": x, "y": y}
        answer_mapping = {"x": x, "y": y}
    else:
        raise ValueError(f"Unknown problem family: {family}")

    prompt = _format_answer(template["prompt"], answer_mapping)
    canonical_answer = _format_answer(template["answer"], answer_mapping)

    return {
        "key": f"{jurisdiction.lower()}{grade}-{skill_code.split('.')[-1].lower()}-{family.lower()}-{index + 1:02d}",
        "family": family,
        "prompt": prompt,
        "canonical_answer": canonical_answer,
        "difficulty": 1 if index < 2 else 2,
        "objective": template["objective"],
        "modes": [MODE_ORDER[index]],
        "parameters": params,
    }


def _build_pack(jurisdiction: str, grade: int) -> dict:
    config = GRADE_CONFIG[grade]
    standards = config["md_dc_standards"] if jurisdiction in ("MD", "DC") else config["va_standards"]
    skills_config = config["skills"]

    jurisdiction_obj = JURISDICTIONS[jurisdiction]
    authority = AUTHORITIES[jurisdiction]
    curriculum_code = f"{jurisdiction}_MATH_{grade}_{_version_tag(jurisdiction, grade)}"

    expectations = []
    for code, std in standards.items():
        expectations.append({
            "source_identifier": code,
            "title": std.title,
            "source_uri": _curriculum_source(jurisdiction, grade),
            "strand": std.strand,
            "description": std.description,
        })

    skill_specs = []
    for skill in skills_config:
        skill_code = skill.code.format(jurisdiction=jurisdiction, grade=grade)
        standard_refs = list(standards.keys())[:1]
        if len(standards) >= 2:
            standard_refs = list(standards.keys())[:2]

        problem_families = tuple(skill.families)
        problems = []
        for i in range(4):
            family = problem_families[i % len(problem_families)]
            problems.append(_make_problem(family, i, jurisdiction, grade, skill_code))

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
            "standard_refs": standard_refs,
            "prerequisite_codes": [
                prereq.format(jurisdiction=jurisdiction, grade=grade)
                for prereq in skill.prerequisite_codes
            ],
            "problem_families": problem_families,
            "problems": problems,
        })

    return {
        "schema_version": 1,
        "jurisdiction": {
            "country_code": "US",
            "code": jurisdiction_obj.code,
            "name": jurisdiction_obj.name,
            "jurisdiction_type": "STATE_PROVINCE_TERRITORY",
            "source_uri": jurisdiction_obj.source_uri,
        },
        "authority": {
            "code": authority.code,
            "name": authority.name,
            "authority_type": "STATE_AGENCY",
            "source_uri": authority.source_uri,
        },
        "curriculum": {
            "code": curriculum_code,
            "name": _curriculum_name(jurisdiction, grade),
            "version": _version(jurisdiction, grade),
            "grade_level": str(grade),
            "source_uri": _curriculum_source(jurisdiction, grade),
        },
        "expectations": expectations,
        "skills": skill_specs,
        "readiness": {
            "minimum_curated_per_skill": 4,
            "required_modes": ["diagnostic", "guided", "independent", "mastery"],
        },
    }


def generate() -> None:
    _PACK_DIR.mkdir(parents=True, exist_ok=True)
    for jurisdiction in ("MD", "DC", "VA"):
        for grade in (1, 2, 3, 4, 5):
            if (jurisdiction, grade) in _SKIP:
                continue
            pack = _build_pack(jurisdiction, grade)
            version_tag = "2026_27" if jurisdiction == "MD" else "2024_25"
            filename = f"{jurisdiction.lower()}-grade{grade}-{'mccrs' if jurisdiction == 'MD' else 'ccss' if jurisdiction == 'DC' else 'sol'}-{version_tag}.json"
            path = _PACK_DIR / filename
            path.write_text(json.dumps(pack, indent=2))
            print(f"Wrote {path}")


if __name__ == "__main__":
    generate()
