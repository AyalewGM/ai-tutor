"""Generate comprehensive declarative curriculum packs for DMV Grades 1-2.

This content-authoring helper produces expanded JSON packs for Maryland,
District of Columbia, and Virginia Grade 1 and Grade 2 mathematics. It is
not runtime code; the committed JSON packs are the source of truth for the
loader.
"""

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

GRADE1_SKILLS = [
    SkillTemplate(
        local_code="{jurisdiction}1.NS.COUNT_COMPARE",
        name="Count and Compare Numbers to 120",
        description="Count forward, read and write numerals, and compare quantities up to 120.",
        canonical_code="MATH.ELEMENTARY.NUMBER_SENSE.COUNT_COMPARE_TO_120",
        canonical_name="Count and Compare Numbers to 120",
        canonical_description="Count, represent, compare, and order whole numbers up to 120.",
        families=("NUMBER_SEQUENCE", "COMPARE_NUMBERS"),
        prerequisite_codes=(),
        standards_md_dc=("1.NBT",),
        standards_va=("1.NS",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}1.NBT.PLACE_VALUE",
        name="Place Value: Tens and Ones",
        description="Understand that two-digit numbers represent tens and ones, including special cases for teen numbers and multiples of ten.",
        canonical_code="MATH.ELEMENTARY.PLACE_VALUE.TENS_ONES",
        canonical_name="Place Value: Tens and Ones",
        canonical_description="Decompose two-digit numbers into tens and ones.",
        families=("PLACE_VALUE_BASE_TEN",),
        prerequisite_codes=("{jurisdiction}1.NS.COUNT_COMPARE",),
        standards_md_dc=("1.NBT",),
        standards_va=("1.NS",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}1.OA.ADDITION_20",
        name="Addition within 20",
        description="Add within 20 using counting on, making ten, and other strategies; demonstrate fluency within 10.",
        canonical_code="MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_20",
        canonical_name="Addition and Subtraction within 20",
        canonical_description="Add and subtract whole numbers within 20 with objects, drawings, and equations.",
        families=("ADDITION_WITHIN_20",),
        prerequisite_codes=("{jurisdiction}1.NBT.PLACE_VALUE",),
        standards_md_dc=("1.OA",),
        standards_va=("1.CE",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}1.OA.SUBTRACTION_20",
        name="Subtraction within 20",
        description="Subtract within 20 using counting back, decomposing to a ten, and the relationship between addition and subtraction.",
        canonical_code="MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_20",
        canonical_name="Addition and Subtraction within 20",
        canonical_description="Add and subtract whole numbers within 20 with objects, drawings, and equations.",
        families=("SUBTRACTION_WITHIN_20",),
        prerequisite_codes=("{jurisdiction}1.OA.ADDITION_20",),
        standards_md_dc=("1.OA",),
        standards_va=("1.CE",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}1.OA.WORD_PROBLEM_20",
        name="Word Problems within 20",
        description="Solve single-step word problems involving adding to, taking from, putting together, taking apart, and comparing within 20.",
        canonical_code="MATH.ELEMENTARY.ARITHMETIC.WORD_PROBLEM_WITHIN_20",
        canonical_name="Word Problems within 20",
        canonical_description="Solve contextual addition and subtraction word problems within 20 with unknowns in various positions.",
        families=("WORD_PROBLEM_ADD_SUB_20",),
        prerequisite_codes=("{jurisdiction}1.OA.ADDITION_20", "{jurisdiction}1.OA.SUBTRACTION_20"),
        standards_md_dc=("1.OA",),
        standards_va=("1.CE",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}1.OA.EQUATION_BALANCE",
        name="Equal Sign and Unknowns",
        description="Understand the meaning of the equal sign and determine the unknown whole number in addition or subtraction equations.",
        canonical_code="MATH.ELEMENTARY.ARITHMETIC.EQUATION_BALANCE",
        canonical_name="Equal Sign and Unknowns",
        canonical_description="Understand equality and find unknowns in addition and subtraction equations.",
        families=("EQUATION_BALANCE",),
        prerequisite_codes=("{jurisdiction}1.OA.ADDITION_20",),
        standards_md_dc=("1.OA",),
        standards_va=("1.CE",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}1.MD.TELL_TIME",
        name="Tell Time to Hour and Half-Hour",
        description="Tell and write time in hours and half-hours using analog and digital clocks.",
        canonical_code="MATH.ELEMENTARY.MEASUREMENT.TELL_TIME_HOUR_HALF_HOUR",
        canonical_name="Tell Time to Hour and Half-Hour",
        canonical_description="Tell and write time in hours and half-hours using analog and digital clocks.",
        families=("TIME_TO_HOUR_HALF_HOUR",),
        prerequisite_codes=("{jurisdiction}1.NS.COUNT_COMPARE",),
        standards_md_dc=("1.MD",),
        standards_va=("1.MG",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}1.G.SHAPES",
        name="Identify and Compose Shapes",
        description="Distinguish between defining and non-defining attributes; build and draw shapes; compose two-dimensional shapes to form larger shapes.",
        canonical_code="MATH.ELEMENTARY.GEOMETRY.IDENTIFY_COMPOSE_SHAPES",
        canonical_name="Identify and Compose Shapes",
        canonical_description="Recognize, describe, and compose two-dimensional and three-dimensional shapes.",
        families=("GEOMETRY_SHAPES",),
        prerequisite_codes=(),
        standards_md_dc=("1.G",),
        standards_va=("1.MG",),
    ),
]

GRADE2_SKILLS = [
    SkillTemplate(
        local_code="{jurisdiction}2.NBT.PLACE_VALUE",
        name="Place Value: Hundreds, Tens, Ones",
        description="Understand that three-digit numbers represent hundreds, tens, and ones; count within 1000; read and write numbers to 1000.",
        canonical_code="MATH.ELEMENTARY.PLACE_VALUE.HUNDREDS_TENS_ONES",
        canonical_name="Place Value: Hundreds, Tens, Ones",
        canonical_description="Decompose three-digit numbers into hundreds, tens, and ones.",
        families=("PLACE_VALUE_BASE_TEN", "NUMBER_SEQUENCE"),
        prerequisite_codes=(),
        standards_md_dc=("2.NBT",),
        standards_va=("2.NS",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}2.NBT.PATTERNS",
        name="Skip Counting and Number Patterns",
        description="Skip-count by 5s, 10s, and 100s; identify and extend number patterns within 1000.",
        canonical_code="MATH.ELEMENTARY.NUMBER_SENSE.SKIP_COUNTING_PATTERNS",
        canonical_name="Skip Counting and Number Patterns",
        canonical_description="Skip-count and identify patterns in number sequences.",
        families=("NUMBER_PATTERN", "NUMBER_SEQUENCE"),
        prerequisite_codes=("{jurisdiction}2.NBT.PLACE_VALUE",),
        standards_md_dc=("2.NBT",),
        standards_va=("2.NS",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}2.NBT.ADDITION_100",
        name="Addition within 100",
        description="Fluently add within 100 using place-value strategies, properties of operations, and the relationship between addition and subtraction.",
        canonical_code="MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_100",
        canonical_name="Addition and Subtraction within 100",
        canonical_description="Add and subtract whole numbers within 100 using place-value strategies.",
        families=("ADDITION_WITHIN_100",),
        prerequisite_codes=("{jurisdiction}2.NBT.PLACE_VALUE",),
        standards_md_dc=("2.NBT",),
        standards_va=("2.CE",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}2.NBT.SUBTRACTION_100",
        name="Subtraction within 100",
        description="Fluently subtract within 100 using place-value strategies, decomposing tens, and the relationship between addition and subtraction.",
        canonical_code="MATH.ELEMENTARY.ARITHMETIC.ADD_SUB_WITHIN_100",
        canonical_name="Addition and Subtraction within 100",
        canonical_description="Add and subtract whole numbers within 100 using place-value strategies.",
        families=("SUBTRACTION_WITHIN_100",),
        prerequisite_codes=("{jurisdiction}2.NBT.ADDITION_100",),
        standards_md_dc=("2.NBT",),
        standards_va=("2.CE",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}2.OA.WORD_PROBLEM_100",
        name="Word Problems within 100",
        description="Solve one- and two-step word problems involving addition and subtraction within 100 with unknowns in all positions.",
        canonical_code="MATH.ELEMENTARY.ARITHMETIC.WORD_PROBLEM_WITHIN_100",
        canonical_name="Word Problems within 100",
        canonical_description="Solve contextual addition and subtraction word problems within 100.",
        families=("WORD_PROBLEM_ADD_SUB_100",),
        prerequisite_codes=("{jurisdiction}2.NBT.ADDITION_100", "{jurisdiction}2.NBT.SUBTRACTION_100"),
        standards_md_dc=("2.OA",),
        standards_va=("2.CE",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}2.MD.MONEY",
        name="Count Money",
        description="Determine the value of a collection of coins and bills; solve word problems involving money using dollar and cent symbols.",
        canonical_code="MATH.ELEMENTARY.MEASUREMENT.MONEY_COUNT",
        canonical_name="Count Money",
        canonical_description="Determine the value of a collection of coins and bills and solve money word problems.",
        families=("MONEY_COUNT",),
        prerequisite_codes=("{jurisdiction}2.NBT.ADDITION_100",),
        standards_md_dc=("2.MD",),
        standards_va=("2.MG",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}2.MD.LENGTH",
        name="Measure and Compare Length",
        description="Measure lengths using appropriate tools; estimate lengths in inches, feet, centimeters, and meters; compare lengths within 100.",
        canonical_code="MATH.ELEMENTARY.MEASUREMENT.LENGTH_COMPARE",
        canonical_name="Measure and Compare Length",
        canonical_description="Measure, estimate, and compare lengths using standard and nonstandard units.",
        families=("COMPARE_LENGTH",),
        prerequisite_codes=("{jurisdiction}2.NBT.SUBTRACTION_100",),
        standards_md_dc=("2.MD",),
        standards_va=("2.MG",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}2.MD.TIME",
        name="Tell Time to Five Minutes",
        description="Tell and write time from analog and digital clocks to the nearest five minutes.",
        canonical_code="MATH.ELEMENTARY.MEASUREMENT.TELL_TIME_FIVE_MINUTES",
        canonical_name="Tell Time to Five Minutes",
        canonical_description="Tell and write time to the nearest five minutes using analog and digital clocks.",
        families=("TIME_TO_5_MINUTES",),
        prerequisite_codes=("{jurisdiction}2.NBT.PATTERNS",),
        standards_md_dc=("2.MD",),
        standards_va=("2.MG",),
    ),
    SkillTemplate(
        local_code="{jurisdiction}2.G.SHAPES_FRACTIONS",
        name="Shapes and Equal Shares",
        description="Identify and draw shapes with specified attributes; partition circles and rectangles into halves, thirds, and fourths.",
        canonical_code="MATH.ELEMENTARY.GEOMETRY.SHAPES_EQUAL_SHARES",
        canonical_name="Shapes and Equal Shares",
        canonical_description="Identify shapes by attributes and partition shapes into equal shares.",
        families=("GEOMETRY_SHAPES", "FRACTION_HALVES_THIRDS_FOURTHS"),
        prerequisite_codes=("{jurisdiction}2.NBT.PLACE_VALUE",),
        standards_md_dc=("2.G",),
        standards_va=("2.MG",),
    ),
]

GRADE1_EXPECTATIONS = [
    {
        "source_identifier": "1.OA",
        "title": "Represent and solve problems involving addition and subtraction",
        "strand": "Operations and Algebraic Thinking",
        "description": "Use addition and subtraction within 20 to solve word problems and work with equations.",
    },
    {
        "source_identifier": "1.NBT",
        "title": "Extend the counting sequence and understand place value",
        "strand": "Number and Operations in Base Ten",
        "description": "Count to 120, read and write numerals, and understand two-digit place value.",
    },
    {
        "source_identifier": "1.MD",
        "title": "Measure lengths and tell time",
        "strand": "Measurement and Data",
        "description": "Tell and write time in hours and half-hours; compare and measure lengths indirectly.",
    },
    {
        "source_identifier": "1.G",
        "title": "Reason with shapes and their attributes",
        "strand": "Geometry",
        "description": "Distinguish defining attributes, build and draw shapes, and compose larger shapes.",
    },
]

GRADE2_EXPECTATIONS = [
    {
        "source_identifier": "2.OA",
        "title": "Represent and solve problems involving addition and subtraction",
        "strand": "Operations and Algebraic Thinking",
        "description": "Solve one- and two-step word problems within 100 and build fluency within 20.",
    },
    {
        "source_identifier": "2.NBT",
        "title": "Understand place value and use it to add and subtract",
        "strand": "Number and Operations in Base Ten",
        "description": "Understand three-digit place value, count within 1000, and fluently add and subtract within 100.",
    },
    {
        "source_identifier": "2.MD",
        "title": "Measure and estimate lengths, work with time and money",
        "strand": "Measurement and Data",
        "description": "Measure lengths, tell time to five minutes, and solve money word problems.",
    },
    {
        "source_identifier": "2.G",
        "title": "Reason with shapes and their attributes",
        "strand": "Geometry",
        "description": "Identify shapes by attributes and partition shapes into equal shares.",
    },
]


VA_GRADE1_EXPECTATIONS = [
    {
        "source_identifier": "1.NS",
        "title": "Number and Number Sense",
        "strand": "Number and Number Sense",
        "description": "Count, represent, compare, and order quantities up to 120.",
    },
    {
        "source_identifier": "1.CE",
        "title": "Computation and Estimation",
        "strand": "Computation and Estimation",
        "description": "Recall addition and subtraction facts within 10 and solve single-step problems within 20.",
    },
    {
        "source_identifier": "1.MG",
        "title": "Measurement and Geometry",
        "strand": "Measurement and Geometry",
        "description": "Measure and compare objects; tell time to the hour and half-hour; describe and sort plane figures.",
    },
]

VA_GRADE2_EXPECTATIONS = [
    {
        "source_identifier": "2.NS",
        "title": "Number and Number Sense",
        "strand": "Number and Number Sense",
        "description": "Read, write, and identify numbers to 999; compare and order whole numbers.",
    },
    {
        "source_identifier": "2.CE",
        "title": "Computation and Estimation",
        "strand": "Computation and Estimation",
        "description": "Solve single-step practical problems using addition and subtraction within 1000.",
    },
    {
        "source_identifier": "2.MG",
        "title": "Measurement and Geometry",
        "strand": "Measurement and Geometry",
        "description": "Tell time to the nearest five minutes; measure length; identify and partition shapes.",
    },
]


PROBLEM_BANKS: dict[str, list[dict]] = {
    "NUMBER_SEQUENCE": [
        {"prompt": "What number comes next? {sequence}", "params": [("next", 12, 1, 13)], "answer_field": "answer"},
        {"prompt": "What number is missing? {sequence}", "params": [("missing", 25, 5, 35)], "answer_field": "answer"},
    ],
    "COMPARE_NUMBERS": [
        {"prompt": "Compare: {a} ___ {b}. Use >, <, or =.", "params": [(15, 22), (38, 38), (71, 64), (101, 110)], "answer_field": "symbol"},
    ],
    "PLACE_VALUE_BASE_TEN": [
        {"prompt": "How many tens and ones make {number}?", "params": [(45, 4, 5), (63, 6, 3), (70, 7, 0), (18, 1, 8)], "answer_field": "place_value"},
        {"prompt": "How many hundreds, tens, and ones make {number}?", "params": [(247, 2, 4, 7), (385, 3, 8, 5), (506, 5, 0, 6), (920, 9, 2, 0)], "answer_field": "place_value"},
    ],
    "ADDITION_WITHIN_20": [
        {"prompt": "What is {a} + {b}?", "params": [(5, 4), (7, 6), (8, 9), (6, 7), (9, 5), (4, 8), (7, 7), (3, 9)], "answer_field": "sum"},
    ],
    "SUBTRACTION_WITHIN_20": [
        {"prompt": "What is {a} - {b}?", "params": [(12, 5), (15, 7), (17, 9), (14, 6), (16, 8), (13, 4), (11, 3), (18, 9)], "answer_field": "diff"},
    ],
    "WORD_PROBLEM_ADD_SUB_20": [
        {"prompt": "{a} crayons are on the table. {b} more are added. How many crayons are there?", "params": [(5, 4), (7, 6), (8, 9), (6, 7)], "answer_field": "sum", "operation": "+"},
        {"prompt": "There are {a} birds on a branch. {b} fly away. How many birds are left?", "params": [(12, 5), (15, 7), (17, 9), (14, 6)], "answer_field": "diff", "operation": "-"},
    ],
    "EQUATION_BALANCE": [
        {"prompt": "Find the missing number: {a} + ___ = {c}", "params": [(5, 4, 9), (7, 6, 13), (8, 9, 17), (6, 7, 13)], "answer_field": "b"},
        {"prompt": "Find the missing number: ___ + {b} = {c}", "params": [(5, 4, 9), (7, 6, 13), (8, 9, 17), (6, 7, 13)], "answer_field": "a"},
    ],
    "TIME_TO_HOUR_HALF_HOUR": [
        {"prompt": "What time is shown when the hour hand points to {hour} and the minute hand points to 12?", "params": [(3, 0), (7, 0), (11, 0), (1, 0)], "answer_field": "time"},
        {"prompt": "What time is shown when the hour hand is between {hour} and {hour2} and the minute hand points to 6?", "params": [(3, 3), (7, 7), (11, 11), (1, 1)], "answer_field": "time_half"},
    ],
    "GEOMETRY_SHAPES": [
        {"prompt": "How many sides does a {shape} have?", "params": [("triangle", 3), ("square", 4), ("rectangle", 4), ("hexagon", 6), ("circle", 0), ("triangle", 3), ("square", 4), ("rectangle", 4)], "answer_field": "sides"},
    ],
    "NUMBER_PATTERN": [
        {"prompt": "What number completes the pattern? {sequence}", "params": [("count_by_5", 5, 25), ("count_by_10", 10, 50), ("count_by_2", 2, 12), ("count_by_100", 100, 400)], "answer_field": "next"},
    ],
    "ADDITION_WITHIN_100": [
        {"prompt": "What is {a} + {b}?", "params": [(24, 35), (47, 28), (56, 39), (63, 19), (15, 67), (34, 45), (72, 18), (55, 27)], "answer_field": "sum"},
    ],
    "SUBTRACTION_WITHIN_100": [
        {"prompt": "What is {a} - {b}?", "params": [(50, 23), (72, 38), (65, 29), (81, 47), (90, 56), (44, 18), (76, 49), (68, 35)], "answer_field": "diff"},
    ],
    "WORD_PROBLEM_ADD_SUB_100": [
        {"prompt": "A library has {a} fiction books and {b} nonfiction books. How many books are there?", "params": [(24, 35), (47, 28), (56, 39), (63, 19)], "answer_field": "sum", "operation": "+"},
        {"prompt": "There are {a} sheets of paper. {b} are used. How many are left?", "params": [(50, 23), (72, 38), (65, 29), (81, 47)], "answer_field": "diff", "operation": "-"},
    ],
    "MONEY_COUNT": [
        {"prompt": "What is the total value of {q} quarter(s), {d} dime(s), {n} nickel(s), and {p} penny(ies)?", "params": [(1, 1, 1, 1), (2, 0, 1, 3), (0, 3, 2, 4), (1, 2, 0, 0), (2, 1, 1, 2), (0, 2, 0, 5), (1, 0, 3, 4), (3, 1, 0, 0)], "answer_field": "total"},
    ],
    "COMPARE_LENGTH": [
        {"prompt": "One ribbon is {a} inches long. Another is {b} inches long. How much longer is the longer ribbon?", "params": [(10, 6), (15, 9), (20, 14), (8, 5), (12, 7), (18, 11), (9, 4), (14, 8)], "answer_field": "diff"},
    ],
    "TIME_TO_5_MINUTES": [
        {"prompt": "What time is {hour}:{minute:02d} on an analog clock when the hour hand is near {hour} and the minute hand points to {minute_div_5}?", "params": [(3, 15, 3), (7, 30, 6), (11, 45, 9), (1, 20, 4), (5, 5, 1), (9, 50, 10), (2, 25, 5), (6, 40, 8)], "answer_field": "time"},
    ],
    "FRACTION_HALVES_THIRDS_FOURTHS": [
        {"prompt": "A circle is divided into {denominator} equal parts. {numerator} part(s) are shaded. What fraction is shaded?", "params": [(1, 2), (1, 3), (2, 4), (3, 4), (1, 4), (2, 3), (1, 2), (3, 4)], "answer_field": "fraction"},
    ],
}


def _format_time(hour: int, minute: int) -> str:
    return f"{hour}:{minute:02d}"


def _make_answer(family: str, params: tuple, answer_field: str) -> str:
    if family == "NUMBER_SEQUENCE":
        _kind, _start, _step, answer = params
        return str(answer)
    if family == "COMPARE_NUMBERS":
        a, b = params
        if a > b:
            return ">"
        if a < b:
            return "<"
        return "="
    if family == "PLACE_VALUE_BASE_TEN":
        if len(params) == 4:
            _number, hundreds, tens, ones = params
            if hundreds == 0:
                return f"{tens} tens and {ones} ones"
            return f"{hundreds} hundreds, {tens} tens, and {ones} ones"
        _number, tens, ones = params
        return f"{tens} tens and {ones} ones"
    if family in {"ADDITION_WITHIN_20", "WORD_PROBLEM_ADD_SUB_20", "ADDITION_WITHIN_100", "WORD_PROBLEM_ADD_SUB_100"}:
        a, b = params
        return str(a + b)
    if family in {"SUBTRACTION_WITHIN_20", "WORD_PROBLEM_ADD_SUB_20_SUB", "SUBTRACTION_WITHIN_100", "WORD_PROBLEM_ADD_SUB_100_SUB"}:
        a, b = params
        return str(a - b)
    if family == "EQUATION_BALANCE":
        a, b, _c = params
        return str(b if answer_field == "b" else a)
    if family == "TIME_TO_HOUR_HALF_HOUR":
        if answer_field == "time":
            hour, _ = params
            return _format_time(hour, 0)
        hour, _ = params
        return _format_time(hour, 30)
    if family == "GEOMETRY_SHAPES":
        _shape, sides = params
        return str(sides)
    if family == "NUMBER_PATTERN":
        _kind, step, start = params
        return str(start + step)
    if family == "MONEY_COUNT":
        q, d, n, p = params
        total = q * 25 + d * 10 + n * 5 + p
        dollars = total // 100
        cents = total % 100
        if dollars:
            return f"${dollars}.{cents:02d}"
        return f"${cents / 100:.2f}"
    if family == "COMPARE_LENGTH":
        a, b = params
        return str(abs(a - b))
    if family == "TIME_TO_5_MINUTES":
        hour, minute, _ = params
        return _format_time(hour, minute)
    if family == "FRACTION_HALVES_THIRDS_FOURTHS":
        numerator, denominator = params
        return f"{numerator}/{denominator}"
    raise ValueError(f"Unknown family: {family}")


def _make_parameters(family: str, params: tuple, operation: str | None = None) -> dict:
    if family == "NUMBER_SEQUENCE":
        kind, start, step, answer = params
        sequence = [start + step * i for i in range(5)]
        if kind == "next":
            sequence.append("?")
            sequence = ", ".join(str(x) for x in sequence)
        else:
            missing_index = 2
            sequence[missing_index] = "?"
            sequence = ", ".join(str(x) for x in sequence)
        return {"start": start, "step": step, "answer": answer, "sequence": sequence}
    if family == "COMPARE_NUMBERS":
        a, b = params
        return {"a": a, "b": b}
    if family == "PLACE_VALUE_BASE_TEN":
        if len(params) == 4:
            number, hundreds, tens, ones = params
            return {"number": number, "hundreds": hundreds, "tens": tens, "ones": ones, "place": "hundreds_tens_ones"}
        number, tens, ones = params
        return {"number": number, "tens": tens, "ones": ones, "place": "tens_and_ones"}
    if family in {"ADDITION_WITHIN_20", "ADDITION_WITHIN_100"}:
        a, b = params
        return {"a": a, "b": b, "operation": "+", "answer": a + b}
    if family in {"SUBTRACTION_WITHIN_20", "SUBTRACTION_WITHIN_100"}:
        a, b = params
        return {"a": a, "b": b, "operation": "-", "answer": a - b}
    if family in {"WORD_PROBLEM_ADD_SUB_20", "WORD_PROBLEM_ADD_SUB_100"}:
        a, b = params
        op = operation if operation in {"+", "-"} else "+"
        answer = a + b if op == "+" else a - b
        return {"a": a, "b": b, "operation": op, "answer": answer}
    if family == "EQUATION_BALANCE":
        a, b, c = params
        return {"a": a, "b": b, "c": c}
    if family == "TIME_TO_HOUR_HALF_HOUR":
        hour, hour2 = params
        minute = 0 if hour == hour2 else 30
        return {"hour": hour, "minute": minute}
    if family == "GEOMETRY_SHAPES":
        shape, sides = params
        return {"shape": shape, "sides": sides}
    if family == "NUMBER_PATTERN":
        kind, step, start = params
        sequence = [start + step * i for i in range(5)] + ["?"]
        return {"start": start, "step": step, "sequence": ", ".join(str(x) for x in sequence)}
    if family == "MONEY_COUNT":
        q, d, n, p = params
        total = q * 25 + d * 10 + n * 5 + p
        return {"quarters": q, "dimes": d, "nickels": n, "pennies": p, "total_cents": total}
    if family == "COMPARE_LENGTH":
        a, b = params
        return {"a": a, "b": b, "difference": abs(a - b)}
    if family == "TIME_TO_5_MINUTES":
        hour, minute, _minute_div_5 = params
        return {"hour": hour, "minute": minute}
    if family == "FRACTION_HALVES_THIRDS_FOURTHS":
        numerator, denominator = params
        return {"numerator": numerator, "denominator": denominator}
    raise ValueError(f"Unknown family: {family}")


def _format_prompt(family: str, template: str, params: tuple) -> str:
    parameters = _make_parameters(family, params)
    if family == "NUMBER_SEQUENCE":
        return template.format(sequence=parameters["sequence"])
    if family == "COMPARE_NUMBERS":
        return template.format(a=parameters["a"], b=parameters["b"])
    if family == "PLACE_VALUE_BASE_TEN":
        return template.format(number=parameters["number"])
    if family in {"ADDITION_WITHIN_20", "SUBTRACTION_WITHIN_20", "ADDITION_WITHIN_100", "SUBTRACTION_WITHIN_100"}:
        return template.format(a=parameters["a"], b=parameters["b"])
    if family in {"WORD_PROBLEM_ADD_SUB_20", "WORD_PROBLEM_ADD_SUB_100"}:
        return template.format(a=parameters["a"], b=parameters["b"])
    if family == "EQUATION_BALANCE":
        return template.format(a=parameters["a"], b=parameters["b"], c=parameters["c"])
    if family == "TIME_TO_HOUR_HALF_HOUR":
        hour2 = (parameters["hour"] % 12) + 1
        return template.format(hour=parameters["hour"], hour2=hour2)
    if family == "GEOMETRY_SHAPES":
        return template.format(shape=parameters["shape"])
    if family == "NUMBER_PATTERN":
        return template.format(sequence=parameters["sequence"])
    if family == "MONEY_COUNT":
        return template.format(
            q=parameters["quarters"],
            d=parameters["dimes"],
            n=parameters["nickels"],
            p=parameters["pennies"],
        )
    if family == "COMPARE_LENGTH":
        return template.format(a=parameters["a"], b=parameters["b"])
    if family == "TIME_TO_5_MINUTES":
        return template.format(
            hour=parameters["hour"],
            minute=parameters["minute"],
            minute_div_5=parameters["minute"] // 5,
        )
    if family == "FRACTION_HALVES_THIRDS_FOURTHS":
        return template.format(
            numerator=parameters["numerator"],
            denominator=parameters["denominator"],
        )
    raise ValueError(f"Unknown family: {family}")


def _make_problem(skill_index: int, problem_index: int, skill_code: str, family: str, jurisdiction: str, grade: int) -> dict:
    bank = PROBLEM_BANKS[family]
    template_entry = bank[problem_index % len(bank)]
    params = template_entry["params"][problem_index % len(template_entry["params"])]
    prompt = _format_prompt(family, template_entry["prompt"], params)
    answer = _make_answer(family, params, template_entry["answer_field"])
    modes = ["diagnostic", "guided", "independent", "mastery"]
    mode = modes[problem_index % 4]
    difficulty = 1 if problem_index < 4 else 2
    key = f"{jurisdiction.lower()}{grade}-{skill_code.split('.')[-1].lower()}-{family.lower()}-{problem_index + 1:02d}"
    operation = template_entry.get("operation")
    return {
        "key": key,
        "family": family,
        "prompt": prompt,
        "canonical_answer": answer,
        "difficulty": difficulty,
        "objective": f"Practice {family.replace('_', ' ').lower()} in {mode} mode.",
        "modes": [mode],
        "parameters": _make_parameters(family, params, operation),
    }


def _build_pack(jurisdiction: str, grade: int) -> dict:
    jdef = JURISDICTIONS[jurisdiction]
    skills = GRADE1_SKILLS if grade == 1 else GRADE2_SKILLS
    expectations = GRADE1_EXPECTATIONS if grade == 1 else GRADE2_EXPECTATIONS
    if jurisdiction == "VA":
        expectations = VA_GRADE1_EXPECTATIONS if grade == 1 else VA_GRADE2_EXPECTATIONS

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
            "prerequisite_codes": [
                prereq.format(jurisdiction=jurisdiction) for prereq in skill.prerequisite_codes
            ],
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
        for grade in (1, 2):
            _build_pack(jurisdiction, grade)


if __name__ == "__main__":
    generate()
