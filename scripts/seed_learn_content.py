"""Seed ``learn_content`` (concept summary + worked examples) on skills.

Content is concept-authored once and applied to every skill code that teaches
that concept — one-step equations appear in M7, M8, A1, and MTH1W packs alike.
Steps use plain math notation; the frontend renders them through MathText.

Run inside the API container after seeding curricula:

    docker compose exec tutor-api python /app/scripts/seed_learn_content.py
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Skill


def _content(
    summary: str,
    *examples: dict,
    key_terms: list[tuple[str, str]] | None = None,
    watch_out: list[str] | None = None,
) -> dict:
    return {
        "summary": summary,
        "examples": list(examples),
        "key_terms": [
            {"term": term, "definition": definition}
            for term, definition in (key_terms or [])
        ],
        "watch_out": list(watch_out or []),
    }


def _ex(title: str, steps: list[str], answer: str | None = None) -> dict:
    return {"title": title, "steps": steps, "answer": answer}


INVERSE_OPS = _content(
    "To solve an equation, isolate the variable by undoing whatever is done to it. "
    "Addition undoes subtraction, and division undoes multiplication — always do the "
    "same thing to both sides so the equation stays balanced.",
    _ex(
        "Solve x + 5 = 12",
        [
            "The variable has +5 attached, so undo it: subtract 5 from both sides.",
            "x + 5 - 5 = 12 - 5",
            "x = 7",
        ],
        "x = 7",
    ),
    _ex(
        "Solve 4x = 20",
        [
            "The variable is multiplied by 4, so undo it: divide both sides by 4.",
            "4x ÷ 4 = 20 ÷ 4",
            "x = 5",
        ],
        "x = 5",
    ),
    key_terms=[
        ("equation", "A statement that two expressions are equal, like x + 5 = 12."),
        ("variable", "A letter that stands for an unknown number, like x."),
        ("inverse operation", "The operation that undoes another — subtraction undoes addition."),
        ("isolate", "Get the variable alone on one side of the equation."),
    ],
    watch_out=[
        "Undoing only one side: whatever you do to the left, you must do to the right.",
        "Using the same operation instead of the inverse — adding when you should subtract keeps x attached.",
        "Forgetting a sign: in x - 3 = 9, the 3 is subtracted, so you add 3 back — not subtract it again.",
    ],
)

ONE_STEP_ADD = _content(
    "In x + a = b, the variable has a constant added to it. Subtract that constant "
    "from both sides to get x by itself.",
    _ex(
        "Solve x + 7 = 15",
        [
            "Undo +7 by subtracting 7 from both sides.",
            "x + 7 - 7 = 15 - 7",
            "x = 8",
        ],
        "x = 8",
    ),
    _ex(
        "Solve x - 3 = 9",
        [
            "Undo -3 by adding 3 to both sides.",
            "x - 3 + 3 = 9 + 3",
            "x = 12",
        ],
        "x = 12",
    ),
    key_terms=[
        ("constant", "A plain number with no variable attached, like 7 in x + 7."),
        ("both sides", "The two expressions joined by the equals sign — they must stay equal."),
    ],
    watch_out=[
        "Adding when the equation needs subtracting — check which operation is attached to x.",
        "Subtracting the constant from only one side, which unbalances the equation.",
    ],
)

ONE_STEP_MULT = _content(
    "In ax = b, the variable is multiplied by a coefficient. Divide both sides by "
    "that coefficient to get x by itself.",
    _ex(
        "Solve 6x = 42",
        [
            "Undo ×6 by dividing both sides by 6.",
            "6x ÷ 6 = 42 ÷ 6",
            "x = 7",
        ],
        "x = 7",
    ),
    _ex(
        "Solve x ÷ 3 = 5",
        [
            "Undo ÷3 by multiplying both sides by 3.",
            "x ÷ 3 × 3 = 5 × 3",
            "x = 15",
        ],
        "x = 15",
    ),
    key_terms=[
        ("coefficient", "The number multiplied by the variable — the 6 in 6x."),
        ("reciprocal thinking", "Dividing by a number is the same as multiplying by its fraction."),
    ],
    watch_out=[
        "Dividing only the left side — both sides must be divided by the coefficient.",
        "Mixing up which number is the coefficient: in 6x = 42, divide by 6, not by 42.",
    ],
)

TWO_STEP = _content(
    "In ax + b = c, two things are attached to x: a multiplication and an addition. "
    "Undo them in reverse order — first subtract b, then divide by a.",
    _ex(
        "Solve 2x + 3 = 11",
        [
            "Undo +3 first: subtract 3 from both sides → 2x = 8.",
            "Then undo ×2: divide both sides by 2.",
            "x = 4",
        ],
        "x = 4",
    ),
    _ex(
        "Solve 5x - 7 = 18",
        [
            "Undo -7 first: add 7 to both sides → 5x = 25.",
            "Then undo ×5: divide both sides by 5.",
            "x = 5",
        ],
        "x = 5",
    ),
    key_terms=[
        ("two-step equation", "An equation needing two inverse operations, like 2x + 3 = 11."),
        ("reverse order", "Undo the addition/subtraction first, then the multiplication/division."),
    ],
    watch_out=[
        "Undoing in the wrong order — dividing by the coefficient first leaves the constant tangled.",
        "Only undoing one step and stopping early: 2x + 3 = 11 is not finished at 2x = 8.",
    ],
)

DISTRIBUTE = _content(
    "The distributive property says a(b + c) = ab + ac. Multiply the outside factor "
    "by every term inside the parentheses — don't stop after the first term.",
    _ex(
        "Expand 3(x + 4)",
        [
            "Multiply 3 by each term inside the parentheses.",
            "3 × x + 3 × 4",
            "3x + 12",
        ],
        "3x + 12",
    ),
    _ex(
        "Expand 5(2x - 3)",
        [
            "Multiply 5 by each term, keeping the subtraction sign.",
            "5 × 2x - 5 × 3",
            "10x - 15",
        ],
        "10x - 15",
    ),
    key_terms=[
        ("distributive property", "a(b + c) = ab + ac — the outside factor multiplies every term inside."),
        ("term", "A part of an expression separated by + or − signs."),
        ("expand", "Rewrite a product like 3(x + 4) as a sum, 3x + 12."),
    ],
    watch_out=[
        "Stopping after the first term: 3(x + 4) is 3x + 12, not 3x + 4.",
        "Adding instead of multiplying: 3(x + 4) ≠ 3 + x + 4.",
        "Losing the sign inside parentheses — (2x − 3) keeps the subtraction.",
    ],
)

DISTRIBUTE_NEG = _content(
    "Distributing a negative factor flips the sign of every term inside the "
    "parentheses: -a(b + c) = -ab - ac. Watch the signs on both terms.",
    _ex(
        "Expand -2(x + 5)",
        [
            "Multiply -2 by each term inside the parentheses.",
            "-2 × x + (-2) × 5",
            "-2x - 10",
        ],
        "-2x - 10",
    ),
    _ex(
        "Expand -(x - 7)",
        [
            "A lone minus sign means multiply by -1.",
            "-1 × x + (-1) × (-7)",
            "-x + 7",
        ],
        "-x + 7",
    ),
    key_terms=[
        ("negative factor", "A factor below zero — it flips the sign of every term it multiplies."),
        ("opposite", "The number with its sign flipped: the opposite of +7 is −7."),
    ],
    watch_out=[
        "Forgetting the second sign flip: −2(x + 5) is −2x − 10, not −2x + 10.",
        "A bare minus sign in front means −1: −(x − 7) = −x + 7.",
    ],
)

COMBINE_TERMS = _content(
    "Like terms have the same variable part — 3x and 5x are like terms, but 3x and "
    "5 are not. Combine them by adding their coefficients; keep the variable part "
    "unchanged.",
    _ex(
        "Simplify 3x + 5x - 2",
        [
            "3x and 5x are like terms: (3 + 5)x = 8x.",
            "The -2 has no variable, so it stays as is.",
        ],
        "8x - 2",
    ),
    _ex(
        "Simplify 4a + 2b - a + 6",
        [
            "Group like terms: (4a - a) + 2b + 6.",
            "4a - a = 3a; 2b and 6 can't combine with anything.",
        ],
        "3a + 2b + 6",
    ),
    key_terms=[
        ("like terms", "Terms with the same variable part — 3x and 5x are like; 3x and 5 are not."),
        ("coefficient", "The number in front of the variable — combine like terms by adding coefficients."),
        ("simplify", "Rewrite an expression in its shortest form."),
    ],
    watch_out=[
        "Combining unlike terms: 3x + 5 does not become 8x — constants and variables stay separate.",
        "Dropping the variable: 3x + 5x is 8x, not 8.",
        "Forgetting the invisible 1: a lone a means 1a, so 4a − a = 3a.",
    ],
)

COMBINE_IN_EQUATIONS = _content(
    "When an equation has several terms on one side, combine like terms on each "
    "side first. Then solve the simplified equation with inverse operations.",
    _ex(
        "Solve 3x + 2x = 20",
        [
            "Combine like terms on the left: 3x + 2x = 5x.",
            "Now solve 5x = 20: divide both sides by 5.",
            "x = 4",
        ],
        "x = 4",
    ),
    _ex(
        "Solve 4x + 2 - x = 11",
        [
            "Combine like terms: 4x - x = 3x, so 3x + 2 = 11.",
            "Subtract 2 from both sides → 3x = 9.",
            "Divide by 3 → x = 3.",
        ],
        "x = 3",
    ),
    key_terms=[
        ("combine first", "Simplify each side before moving terms across the equals sign."),
    ],
    watch_out=[
        "Jumping to inverse operations before combining — 3x + 2x = 20 has an easy 5x hiding in it.",
        "Combining terms across the equals sign — like terms must be on the same side first.",
    ],
)

MULTI_STEP = _content(
    "Multi-step equations mix distribution with inverse operations. The reliable "
    "order: distribute to clear parentheses, combine like terms, then undo the "
    "addition and multiplication last.",
    _ex(
        "Solve 2(x + 3) = 14",
        [
            "Distribute first: 2x + 6 = 14.",
            "Subtract 6 from both sides → 2x = 8.",
            "Divide by 2 → x = 4.",
        ],
        "x = 4",
    ),
    _ex(
        "Solve 3(x - 2) + 1 = 10",
        [
            "Distribute: 3x - 6 + 1 = 10.",
            "Combine constants: 3x - 5 = 10.",
            "Add 5 → 3x = 15, then divide by 3 → x = 5.",
        ],
        "x = 5",
    ),
    key_terms=[
        ("order of moves", "Distribute → combine like terms → undo operations, in that order."),
    ],
    watch_out=[
        "Solving before clearing parentheses — distribute first or the equation gets tangled.",
        "Distributing to only one term inside the parentheses.",
    ],
)

FRACTION_OPS = _content(
    "To add or subtract fractions, first rewrite them with a common denominator — "
    "a shared bottom number. Then add or subtract only the numerators and keep "
    "the denominator the same.",
    _ex(
        "Evaluate 1/3 + 2/8",
        [
            "Common denominator of 3 and 8 is 24.",
            "1/3 = 8/24 and 2/8 = 6/24.",
            "8/24 + 6/24 = 14/24, which simplifies to 7/12.",
        ],
        "7/12",
    ),
    _ex(
        "Evaluate 3/4 - 1/6",
        [
            "Common denominator of 4 and 6 is 12.",
            "3/4 = 9/12 and 1/6 = 2/12.",
            "9/12 - 2/12 = 7/12.",
        ],
        "7/12",
    ),
    key_terms=[
        ("numerator", "The top number of a fraction — how many parts you have."),
        ("denominator", "The bottom number — how many equal parts make a whole."),
        ("common denominator", "A shared bottom number so fractions can be added or subtracted."),
    ],
    watch_out=[
        "Adding denominators too: 1/2 + 1/4 ≠ 2/6. Only numerators combine.",
        "Forgetting to simplify: 14/24 should reduce to 7/12.",
    ],
)

INTEGER_OPS = _content(
    "Integers include negatives. Adding a negative is the same as subtracting; "
    "subtracting a negative is the same as adding. When multiplying or dividing, "
    "same signs give a positive result, different signs give a negative result.",
    _ex(
        "Evaluate -6 + 14",
        [
            "Start at -6 on the number line, move 14 units right.",
            "You pass 0 after 6 units and continue 8 more.",
        ],
        "8",
    ),
    _ex(
        "Evaluate (-3) × (-4)",
        [
            "Multiply the values: 3 × 4 = 12.",
            "Same signs (both negative) → positive result.",
        ],
        "12",
    ),
    key_terms=[
        ("integer", "A whole number, positive, negative, or zero: …−2, −1, 0, 1, 2…"),
        ("negative number", "A number less than zero, written with a minus sign."),
    ],
    watch_out=[
        "Sign slips on subtraction: −4 − (−9) becomes −4 + 9.",
        "Forgetting that negative × negative is positive — different signs are negative.",
    ],
)

SLOPE_INTERCEPT = _content(
    "A linear relation can be written y = mx + b, where m is the slope (how steep "
    "the line is — rise over run) and b is the y-intercept (where the line crosses "
    "the y-axis).",
    _ex(
        "Write the equation of a line with slope 2 and y-intercept -1",
        [
            "m = 2 and b = -1.",
            "Substitute into y = mx + b.",
        ],
        "y = 2x - 1",
    ),
    _ex(
        "Identify slope and intercept of y = -3x + 5",
        [
            "Compare with y = mx + b: m is the coefficient of x, b is the constant.",
            "Slope m = -3, y-intercept b = 5.",
        ],
        "slope = -3, intercept = 5",
    ),
    key_terms=[
        ("slope", "How steep the line is — rise over run, the m in y = mx + b."),
        ("y-intercept", "Where the line crosses the y-axis — the b in y = mx + b."),
        ("linear relation", "A relationship whose graph is a straight line."),
    ],
    watch_out=[
        "Swapping m and b — the slope is attached to x, the intercept stands alone.",
        "Dropping a negative sign: in y = −3x + 5 the slope is −3, not 3.",
    ],
)

EVAL_LINEAR = _content(
    "Evaluating a relation or function means substituting a given value for the "
    "variable and simplifying. Write the substitution in parentheses to keep "
    "negative signs straight.",
    _ex(
        "Evaluate y = 3x - 2 when x = 4",
        [
            "Substitute: y = 3(4) - 2.",
            "Multiply first: y = 12 - 2.",
        ],
        "y = 10",
    ),
    _ex(
        "Evaluate f(x) = -2x + 7 when x = -3",
        [
            "Substitute: f(-3) = -2(-3) + 7.",
            "-2 × -3 = 6, so f(-3) = 6 + 7.",
        ],
        "f(-3) = 13",
    ),
    key_terms=[
        ("evaluate", "Substitute a value for the variable and simplify."),
        ("substitute", "Replace a variable with a given number."),
    ],
    watch_out=[
        "Sign errors when substituting negatives — write f(−3) = −2(−3) + 7 in parentheses.",
        "Adding before multiplying: in 3x − 2, multiply 3 × x first.",
    ],
)

PERCENT = _content(
    "A percent is a rate out of 100. To find a percent of a quantity, convert the "
    "percent to a decimal (divide by 100) and multiply.",
    _ex(
        "Find 15% of 80",
        [
            "Convert: 15% = 0.15.",
            "Multiply: 0.15 × 80.",
        ],
        "12",
    ),
    _ex(
        "Find 40% of 250",
        [
            "Convert: 40% = 0.40.",
            "Multiply: 0.40 × 250.",
        ],
        "100",
    ),
    key_terms=[
        ("percent", "A rate out of 100 — 15% means 15 per 100."),
        ("decimal form", "The percent divided by 100: 15% = 0.15."),
    ],
    watch_out=[
        "Using the percent as a whole number: 15% of 80 is 0.15 × 80, not 15 × 80.",
        "Forgetting to move the decimal two places when converting.",
    ],
)

DISCOUNT_TAX = _content(
    "Discounts subtract a percent from the original price; tax adds a percent on "
    "top. Compute the percent amount first, then subtract (discount) or add (tax).",
    _ex(
        "A $60 jacket is 25% off. What is the sale price?",
        [
            "Discount amount: 25% × 60 = 0.25 × 60 = $15.",
            "Sale price: 60 - 15 = $45.",
        ],
        "$45",
    ),
    _ex(
        "A $80 game has 13% tax. What is the total cost?",
        [
            "Tax amount: 13% × 80 = 0.13 × 80 = $10.40.",
            "Total: 80 + 10.40 = $90.40.",
        ],
        "$90.40",
    ),
    key_terms=[
        ("discount", "A percent taken off the original price — subtract it."),
        ("tax", "A percent added on top of the price — add it."),
        ("sale price", "The price after the discount is subtracted."),
    ],
    watch_out=[
        "Adding a discount instead of subtracting it.",
        "Applying the percent to the new price instead of the original.",
    ],
)

UNIT_RATE = _content(
    "A unit rate tells you the amount per one unit — like cost per item or km per "
    "hour. Find it by dividing the first quantity by the second.",
    _ex(
        "8 granola bars cost $6. What is the unit price?",
        [
            "Divide total cost by number of items: 6 ÷ 8 = 0.75.",
            "Each bar costs $0.75.",
        ],
        "$0.75 per bar",
    ),
    _ex(
        "A car travels 180 km in 2 hours. What is its speed?",
        [
            "Divide distance by time: 180 ÷ 2.",
        ],
        "90 km per hour",
    ),
    key_terms=[
        ("rate", "A comparison of two quantities, like dollars per hour."),
        ("unit rate", "The amount per one unit — $5 per ticket, km per hour."),
    ],
    watch_out=[
        "Dividing the wrong way — 'per' means divide the first quantity by the second.",
        "Forgetting the units on the answer.",
    ],
)

PROPORTIONAL = _content(
    "Two quantities are proportional when their ratio stays constant — doubling "
    "one doubles the other. Check whether each pair has the same unit rate.",
    _ex(
        "Is the relationship proportional: 2 tickets cost $10, 5 tickets cost $25?",
        [
            "Unit rate: 10 ÷ 2 = $5 per ticket.",
            "Check the other pair: 25 ÷ 5 = $5 per ticket.",
            "Same unit rate → proportional.",
        ],
        "Yes, proportional",
    ),
    key_terms=[
        ("proportional", "Two quantities with a constant ratio — doubling one doubles the other."),
    ],
    watch_out=[
        "Checking only one pair — every pair must share the same unit rate.",
    ],
)

ALGEBRAIC_EXPR = _content(
    "An algebraic expression combines numbers and variables. Simplify by "
    "distributing to clear parentheses first, then combining like terms.",
    _ex(
        "Simplify 2(x + 3) + 4x",
        [
            "Distribute: 2x + 6 + 4x.",
            "Combine like terms: 2x + 4x = 6x.",
        ],
        "6x + 6",
    ),
    key_terms=[
        ("expression", "Numbers, variables, and operations — with no equals sign."),
        ("simplify", "Rewrite in shortest form: distribute, then combine like terms."),
    ],
    watch_out=[
        "Trying to 'solve' an expression — there's no equals sign, just simplify it.",
        "Combining unlike terms after distributing.",
    ],
)

EQ_AND_INEQUALITY = _content(
    "Equations (x + a = b) and inequalities (x + a < b) solve the same way — undo "
    "operations on both sides. One difference: multiplying or dividing an "
    "inequality by a negative flips the inequality sign.",
    _ex(
        "Solve 3x = 21",
        ["Divide both sides by 3."],
        "x = 7",
    ),
    _ex(
        "Solve -2x < 10",
        [
            "Divide both sides by -2.",
            "Because you divided by a negative, flip the sign.",
        ],
        "x > -5",
    ),
    key_terms=[
        ("inequality", "A comparison using <, >, ≤, or ≥ instead of equals."),
        ("flip the sign", "Multiplying or dividing an inequality by a negative reverses it."),
    ],
    watch_out=[
        "Forgetting to flip the inequality sign when dividing by a negative — −2x < 10 gives x > −5.",
    ],
)

NUMBER_SENSE = _content(
    "Number sense means working fluently with integers and fractions: sign rules "
    "for integers, and common denominators for fraction addition and subtraction.",
    _ex(
        "Evaluate -4 - (-9)",
        [
            "Subtracting a negative is adding: -4 + 9.",
            "Start at -4, move 9 units right.",
        ],
        "5",
    ),
    _ex(
        "Evaluate 1/2 + 1/4",
        [
            "Common denominator is 4: 1/2 = 2/4.",
            "2/4 + 1/4 = 3/4.",
        ],
        "3/4",
    ),
    key_terms=[
        ("integer", "A whole number, including negatives and zero."),
        ("common denominator", "A shared bottom number for adding or subtracting fractions."),
    ],
    watch_out=[
        "Treating −(−9) as subtraction — two negatives make an addition.",
        "Adding fraction denominators instead of finding a common one.",
    ],
)

ALG_OVERVIEW = _content(
    "Algebraic work means simplifying expressions and solving equations. The core "
    "moves: distribute to clear parentheses, combine like terms, then use inverse "
    "operations to isolate the variable — always doing the same thing to both sides.",
    _ex(
        "Solve 2x + 3 = 11",
        [
            "Subtract 3 from both sides → 2x = 8.",
            "Divide both sides by 2.",
        ],
        "x = 4",
    ),
    key_terms=[
        ("isolate", "Get the variable alone on one side."),
        ("inverse operation", "The operation that undoes another."),
    ],
    watch_out=[
        "Undoing only one side — both sides must get the same operation.",
    ],
)

LINEAR_REL_OVERVIEW = _content(
    "A linear relation makes a straight line when graphed. In y = mx + b form, m is "
    "the slope and b is the y-intercept. You can evaluate it by substituting a "
    "value for x.",
    _ex(
        "For y = 2x + 1, find y when x = 3",
        [
            "Substitute: y = 2(3) + 1.",
            "y = 6 + 1.",
        ],
        "y = 7",
    ),
    key_terms=[
        ("linear relation", "A relationship whose graph is a straight line."),
        ("slope", "How steep the line is — the m in y = mx + b."),
        ("y-intercept", "Where the line crosses the y-axis — the b."),
    ],
    watch_out=[
        "Mixing up which letter is slope vs. intercept in y = mx + b.",
    ],
)

FIN_LIT_OVERVIEW = _content(
    "Financial literacy problems usually involve percents: discounts reduce a "
    "price, tax increases it, and tips or interest add a percent of an amount.",
    _ex(
        "A $40 shirt is 20% off. What is the sale price?",
        [
            "Discount: 20% × 40 = $8.",
            "Sale price: 40 - 8 = $32.",
        ],
        "$32",
    ),
    key_terms=[
        ("discount", "A percent off the price — subtract it."),
        ("tax", "A percent added on — add it."),
        ("interest", "A percent earned or owed over time."),
    ],
    watch_out=[
        "Applying percents as whole numbers — convert 20% to 0.20 first.",
        "Subtracting tax instead of adding it.",
    ],
)


LEARN_CONTENT: dict[str, dict] = {
    # MCPS Algebra 1
    "A1.EXPR": ALGEBRAIC_EXPR,
    "A1.EXPR.COMBINE": COMBINE_TERMS,
    "A1.EXPR.DIST": DISTRIBUTE,
    "A1.LINEAR.EQ": ALG_OVERVIEW,
    "A1.LINEAR.EQ.ONE": INVERSE_OPS,
    "A1.LINEAR.EQ.TWO": TWO_STEP,
    "A1.LINEAR.FN": LINEAR_REL_OVERVIEW,
    "A1.LINEAR.FN.EVAL": EVAL_LINEAR,
    "A1.LINEAR.FN.SLOPE": SLOPE_INTERCEPT,
    # MCPS Math 7
    "M7.EE.EQUATION": EQ_AND_INEQUALITY,
    "M7.EE.EQUATION.ONE": INVERSE_OPS,
    "M7.EE.EQUATION.TWO": TWO_STEP,
    "M7.EE.EXPR": ALGEBRAIC_EXPR,
    "M7.EE.EXPR.COMBINE": COMBINE_TERMS,
    "M7.EE.EXPR.DIST": DISTRIBUTE,
    "M7.RP.PERCENT": PERCENT,
    "M7.RP.PERCENT.OF": PERCENT,
    "M7.RP.PROP": PROPORTIONAL,
    "M7.RP.PROP.RATE": UNIT_RATE,
    "M7.NS.RAT": INTEGER_OPS,
    # MCPS Math 8
    "M8.ALG.DIST": DISTRIBUTE,
    "M8.ALG.DIST.NEG": DISTRIBUTE_NEG,
    "M8.ALG.DIST.POS": DISTRIBUTE,
    "M8.ALG.INVERSE": INVERSE_OPS,
    "M8.ALG.INVERSE.ADD": ONE_STEP_ADD,
    "M8.ALG.INVERSE.MULT": ONE_STEP_MULT,
    "M8.ALG.MULTI_STEP": MULTI_STEP,
    "M8.ALG.MULTI_STEP.COMBINE": COMBINE_IN_EQUATIONS,
    "M8.ALG.TWO_STEP": TWO_STEP,
    # Ontario MTH1W (both pack versions share skill codes)
    "MTH1W.B.NUM": NUMBER_SENSE,
    "MTH1W.B.NUM.FRAC": FRACTION_OPS,
    "MTH1W.B.NUM.INT": INTEGER_OPS,
    "MTH1W.C.ALG": ALG_OVERVIEW,
    "MTH1W.C.ALG.EQ1": INVERSE_OPS,
    "MTH1W.C.ALG.EQ2": TWO_STEP,
    "MTH1W.C.ALG.EXPR": ALGEBRAIC_EXPR,
    "MTH1W.C.REL": LINEAR_REL_OVERVIEW,
    "MTH1W.C.REL.EVAL": EVAL_LINEAR,
    "MTH1W.C.REL.SLOPE": SLOPE_INTERCEPT,
    "MTH1W.F.FIN": FIN_LIT_OVERVIEW,
    "MTH1W.F.FIN.APP": DISCOUNT_TAX,
    "MTH1W.F.FIN.PCT": PERCENT,
}


def seed() -> None:
    with SessionLocal() as db:
        skills = db.scalars(
            select(Skill).where(Skill.code.in_(LEARN_CONTENT.keys()))
        ).all()
        updated = 0
        for skill in skills:
            if skill.learn_content != LEARN_CONTENT[skill.code]:
                skill.learn_content = LEARN_CONTENT[skill.code]
                updated += 1
        db.commit()
        missing = set(LEARN_CONTENT) - {s.code for s in skills}
        print(f"learn_content written to {updated} skills ({len(skills)} matched)")
        if missing:
            print(f"no matching skills for codes: {sorted(missing)}")


if __name__ == "__main__":
    seed()
