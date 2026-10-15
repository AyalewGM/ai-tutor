"""Seed extension (challenge-tier) problems for VA/DC grades 6-7 and the
Algebra I / MTH1W curricula.

Same contract as seed_extension_middle_grades: opt-in stretch items authored
above each skill's normal band, tagged extension_eligible so attempts stay
out of mastery evidence. Idempotent — keyed on (skill, prompt).
"""

try:
    from scripts.seed_extension_middle_grades import _extension_problem
except ModuleNotFoundError:  # standalone: python scripts/seed_extension_algebra.py
    from seed_extension_middle_grades import _extension_problem

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Curriculum, Skill

# (skill_code, prompt, answer, difficulty, problem_type, answer_kind, objective)
EXTENSIONS: dict[str, dict[str, list[tuple[str, str, str, int, str, str, str]]]] = {
    "VA_MATH_6": {
        "VA6.PFA.RATIO": [
            (("A trail mix has raisins to peanuts in the ratio 2:5. If there are "
             "35 peanuts, how many raisins are there?"), "14", 6, "WORD_PROBLEM",
             "INTEGER", "Stretch: scale one part of a ratio to find the other."),
            ((("The ratio of fiction to nonfiction books on a shelf is 7:3. After "
              "6 more fiction books are added, the ratio becomes 3:1. How many "
              "nonfiction books are there?")), "9", 8, "WORD_PROBLEM", "INTEGER",
             "Stretch: solve a ratio under an additive change."),
        ],
        "VA6.NS.RATIONAL": [
            ("Which is greater, 0.75 or 7/9? Answer with the greater value.",
             "7/9", 6, "INTEGER_OPERATIONS", "FREE_TEXT",
             "Stretch: compare a decimal to a non-terminating fraction."),
            (("Of -3/4, -0.8, and -7/10, which is least? Answer with the value."),
             "-0.8", 7, "INTEGER_OPERATIONS", "FREE_TEXT",
             "Stretch: order negative rationals in mixed forms."),
        ],
        "VA6.CE.FRACTION": [
            ("Compute: 3/4 / (5/6). Write as a fraction.", "9/10", 6,
             "INTEGER_OPERATIONS", "FRACTION",
             "Stretch: divide fractions with unlike denominators."),
            ((("A recipe needs 2 2/3 cups of flour and you only have a 1/3-cup "
              "scoop. How many scoops do you need?")), "8", 7, "WORD_PROBLEM",
             "INTEGER", "Stretch: measurement division of a mixed number."),
        ],
        "VA6.PFA.EXPR": [
            ("Evaluate 5a - 2b when a = 3 and b = 7.", "1", 6,
             "SIMPLIFY_EXPRESSION", "INTEGER",
             "Stretch: substitute two variables with a subtraction."),
            ((("Write '4 more than twice n' as an expression, then evaluate it "
              "at n = 9. Give the value.")), "22", 7, "SIMPLIFY_EXPRESSION",
             "INTEGER", "Stretch: translate words to an expression, then evaluate."),
        ],
        "VA6.PFA.EQUATION": [
            ("Solve for x: x/6 = 5.", "30", 6, "SOLVE_EQUATION", "INTEGER",
             "Stretch: undo a quotient in one step."),
            ("Solve for x: 2.5x = 20.", "8", 7, "SOLVE_EQUATION", "INTEGER",
             "Stretch: divide by a decimal coefficient."),
        ],
    },
    "VA_MATH_7": {
        "VA7.CE.RATIONAL": [
            ("Compute: (-3/4) x (-8/9). Write as a fraction.", "2/3", 7,
             "SIGNED_NUMBERS", "FRACTION",
             "Stretch: multiply signed fractions with reduction."),
            ("Evaluate: -5 - (-12) + (-3)^2.", "16", 7, "SIGNED_NUMBERS",
             "INTEGER", "Stretch: mixed signed operations with an exponent."),
        ],
        "VA7.PFA.PROPORTIONAL": [
            ((("A proportional relationship y = kx passes through (4, 26). "
              "What is y when x = 10?")), "65", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: recover k, then evaluate."),
            ((("If 5 notebooks cost $8.75, how much do 12 notebooks cost in "
              "dollars?")), "21", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: unit rate then scale up."),
        ],
        "VA7.PFA.EQUATION": [
            ("Solve for x: (x - 3)/5 = 4.", "23", 7, "SOLVE_EQUATION", "INTEGER",
             "Stretch: undo a quotient around a subtraction."),
            ("Solve for x: -4(x + 2) = 28.", "-9", 8, "SOLVE_EQUATION",
             "INTEGER", "Stretch: negative distribution before isolating."),
        ],
        "VA7.MG.GEOMETRY": [
            ((("A circle has circumference 14pi units. What is its area? Write "
              "your answer like 49pi.")), "49pi", 7, "WORD_PROBLEM", "FREE_TEXT",
             "Stretch: circumference to radius to area."),
            ((("The angles of a triangle are x, 2x, and 3x degrees. How many "
              "degrees is the largest angle?")), "90", 6, "WORD_PROBLEM",
             "INTEGER", "Stretch: partition 180 degrees by a ratio."),
        ],
        "VA7.PS.PROBABILITY": [
            ((("Two fair dice are rolled. What is the probability the sum is 5? "
              "Write as a fraction.")), "1/9", 6, "PROBABILITY", "FRACTION",
             "Stretch: enumerate outcomes in a 36-cell sample space."),
            ((("A bag has 3 red and 2 blue marbles. Two are drawn without "
              "replacement. What is the probability both are red? Write as a "
              "fraction.")), "3/10", 8, "PROBABILITY", "FRACTION",
             "Stretch: compound probability without replacement."),
        ],
    },
    "DC_MATH_6": {
        "DC6.RP.RATIO": [
            ((("The ratio of boys to girls in a club is 4:7. There are 28 boys. "
              "How many girls are there?")), "49", 6, "WORD_PROBLEM", "INTEGER",
             "Stretch: scale a ratio from one known part."),
            ((("Forty-five points are split between two players in the ratio "
              "2:3. How many points does the player with the larger share "
              "have?")), "27", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: split a total by a ratio."),
        ],
        "DC6.RP.UNIT_RATE": [
            ((("A 5-pound bag of rice costs $12.50 and an 8-pound bag costs "
              "$19.20. How many cents cheaper per pound is the larger bag?")),
             "10", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: compare two unit rates in cents."),
            ((("A train travels 150 miles in 2.5 hours at a constant speed. What "
              "is its speed in miles per hour?")), "60", 6, "WORD_PROBLEM",
             "INTEGER", "Stretch: divide by a decimal elapsed time."),
        ],
        "DC6.NS.FRACTION": [
            ("How many 2/5-meter pieces of ribbon can be cut from 6 meters?",
             "15", 6, "WORD_PROBLEM", "INTEGER",
             "Stretch: measurement division by a fraction."),
            ("Compute: 1 1/2 / (3/8).", "4", 7, "INTEGER_OPERATIONS", "INTEGER",
             "Stretch: divide a mixed number by a fraction."),
        ],
        "DC6.EE.EXPR": [
            ("Evaluate 3n^2 - 2n when n = 4.", "40", 7, "SIMPLIFY_EXPRESSION",
             "INTEGER", "Stretch: substitute into a squared term."),
            ((("The expression 5(x + 2) - 3x simplifies to ax + b. What is "
              "a + b?")), "12", 8, "SIMPLIFY_EXPRESSION", "INTEGER",
             "Stretch: simplify, then combine the resulting coefficients."),
        ],
        "DC6.EE.EQUATION": [
            ("Solve for x: 4x - 9 = 27.", "9", 6, "SOLVE_EQUATION", "INTEGER",
             "Stretch: two-step with a subtraction."),
            ("Solve for x: x + 15 = 2x - 8.", "23", 8, "SOLVE_EQUATION",
             "INTEGER", "Stretch: variable on both sides."),
        ],
    },
    "DC_MATH_7": {
        "DC7.RP.PROPORTIONAL": [
            ((("A proportional line passes through (0, 0) and (3, 21). In the "
              "equation y = kx, what is k?")), "7", 6, "PROPORTIONAL_GRAPH",
             "INTEGER", "Stretch: extract the constant of proportionality."),
            (("The point (2, 9) lies on y = kx. What is y when x = 6?"),
             "27", 8, "PROPORTIONAL_GRAPH", "INTEGER",
             "Stretch: recover a fractional k, then evaluate."),
        ],
        "DC7.RP.PERCENT": [
            ((("A $150 item is marked up 20%, then discounted 20%. What is the "
              "final price in dollars?")), "144", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: successive percent changes multiply, not cancel."),
            ((("A store raises a $40 price by 25%, then lowers the new price by "
              "25%. What is the final price in dollars?")), "37.50", 8,
             "WORD_PROBLEM", "DECIMAL",
             "Stretch: symmetric percent changes on a different base."),
        ],
        "DC7.NS.RATIONAL": [
            ("Compute: (-2/3) / (4/9). Write as a fraction.", "-3/2", 7,
             "SIGNED_NUMBERS", "FRACTION",
             "Stretch: signed fraction division with reduction."),
            ("Evaluate: (-4)^2 - 3(-5).", "31", 7, "SIGNED_NUMBERS", "INTEGER",
             "Stretch: exponent and signed product together."),
        ],
        "DC7.EE.EQUATION": [
            ("Solve for x: 5x + 3 = 2x - 12.", "-5", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: collect variable terms to a negative answer."),
            ("Solve for x: 3(x - 4) = 2(x + 1).", "14", 8, "SOLVE_EQUATION",
             "INTEGER", "Stretch: distribute on both sides, then collect."),
        ],
        "DC7.SP.PROBABILITY": [
            ((("Two fair coins are flipped. What is the probability both land "
              "heads? Write as a fraction.")), "1/4", 6, "PROBABILITY",
             "FRACTION", "Stretch: independent compound probability."),
            ((("A spinner numbered 1 to 4 is spun twice. What is the probability "
              "the two spins sum to 5? Write as a fraction.")), "1/4", 7,
             "PROBABILITY", "FRACTION",
             "Stretch: count favorable pairs in a 16-outcome space."),
        ],
    },
    "MD_ALGEBRA_1_2026_27": {
        "A1.EXPR": [
            ("Simplify: (3x^2 - 2x + 5) - (x^2 + 4x - 3).", "2x^2 - 6x + 8", 6,
             "POLYNOMIAL_ADD_SUBTRACT", "FREE_TEXT",
             "Stretch: subtract a whole trinomial."),
            ("Evaluate |2x - 7| + x when x = -3.", "10", 7,
             "SIMPLIFY_EXPRESSION", "INTEGER",
             "Stretch: absolute value inside an expression."),
        ],
        "A1.EXPR.COMBINE": [
            ("Simplify: 7x - 3(2x - 5) + x.", "2x + 15", 6,
             "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: combine like terms through a negative factor."),
            ("Simplify: (4a + 3b) - 2(a - 5b).", "2a + 13b", 7,
             "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: two variables with a distributed negative."),
        ],
        "A1.EXPR.DIST": [
            ("Expand and simplify: -3(2x - 5) + 4(x + 1).", "-2x + 19", 7,
             "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: negative distribution plus a second product."),
            ("Expand and simplify: 2x(3x - 4) - 5(x^2 - 2).", "x^2 - 8x + 10",
             8, "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: monomial products create x^2 terms to combine."),
        ],
        "A1.LINEAR.EQ.ONE": [
            ("Solve for x: (2x + 5)/3 = 7.", "8", 6, "SOLVE_EQUATION",
             "INTEGER", "Stretch: undo a quotient around a sum."),
            ("Solve for x: -3x/4 = 15.", "-20", 7, "SOLVE_EQUATION", "INTEGER",
             "Stretch: multiply both sides by a negative reciprocal."),
        ],
        "A1.LINEAR.EQ.TWO": [
            ("Solve for x: 7x - 4 = 3x + 20.", "6", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: variable terms on both sides."),
            ("Solve for x: 5(2x - 1) = 4x + 13.", "3", 8, "SOLVE_EQUATION",
             "INTEGER", "Stretch: distribute before collecting terms."),
        ],
        "A1.LINEAR.EQ": [
            ("Solve for x: 2(x - 3) + 4x = 3(x + 7).", "9", 8,
             "SOLVE_EQUATION", "INTEGER",
             "Stretch: distribute twice, then collect across the equals sign."),
            ("Solve d = rt for t.", "d/r", 6, "SOLVE_EQUATION", "FREE_TEXT",
             "Stretch: isolate a variable in a literal equation."),
        ],
        "A1.LINEAR.FN.SLOPE": [
            ("What is the slope of the line through (-2, 5) and (4, -1)?",
             "-1", 7, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: slope with a negative rise."),
            ((("A line is parallel to y = 3x - 1 and passes through (0, 4). "
              "What is its slope?")), "3", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: parallel lines share a slope."),
        ],
        "A1.LINEAR.FN.EVAL": [
            ("If f(x) = -2x + 7, what is f(5)?", "-3", 6, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: evaluate with a negative coefficient."),
            ("If f(x) = x^2 - 3x, what is f(-2)?", "10", 7, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: evaluate a quadratic rule at a negative input."),
        ],
        "A1.LINEAR.FN": [
            ((("A line with slope -2 passes through (3, 1). What is its "
              "y-intercept?")), "7", 7, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: recover the intercept from slope and a point."),
            ("If f(x) = 4x - 1, what value of x makes f(x) = 19?", "5", 7,
             "LINEAR_FUNCTION", "INTEGER",
             "Stretch: invert a function rule to find the input."),
        ],
        "A1.LINEAR.INEQ": [
            ("Solve: 2x - 5 <= 9. Write like x <= 7.", "x <= 7", 6,
             "LINEAR_FUNCTION", "FREE_TEXT",
             "Stretch: two-step inequality."),
            (("Solve: -3x + 2 > 14. Write like x < 4."), "x < -4", 8,
             "LINEAR_FUNCTION", "FREE_TEXT",
             "Stretch: dividing by a negative flips the inequality."),
        ],
        "A1.POLY.FN": [
            ("Multiply: (x + 5)(x - 3).", "x^2 + 2x - 15", 6,
             "POLYNOMIAL_ADD_SUBTRACT", "FREE_TEXT",
             "Stretch: binomial product with a negative constant."),
            ("Multiply: (2x - 1)(x + 4).", "2x^2 + 7x - 4", 7,
             "POLYNOMIAL_ADD_SUBTRACT", "FREE_TEXT",
             "Stretch: binomial product with a leading coefficient."),
        ],
        "A1.QUAD.FN": [
            ("If f(x) = x^2 - 4x + 3, what is f(5)?", "8", 6,
             "LINEAR_FUNCTION", "INTEGER",
             "Stretch: evaluate a quadratic away from the vertex."),
            ((("What is the x-coordinate of the vertex of "
              "y = x^2 - 6x + 11?")), "3", 7, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: vertex x = -b/2a."),
        ],
        "A1.SEQ": [
            (("An arithmetic sequence starts 5, 9, 13, ... What is the 12th "
             "term?"), "49", 7, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: apply a_n = a_1 + (n-1)d."),
            ("A geometric sequence starts 3, 6, 12, ... What is the 8th term?",
             "384", 7, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: repeated doubling from a small seed."),
        ],
        "A1.SYS.EQ": [
            (("If x + y = 10 and x - y = 4, what is x?"), "7", 6,
             "SOLVE_EQUATION", "INTEGER",
             "Stretch: add the equations to eliminate y."),
            ((("The lines y = 2x + 1 and y = x + 5 intersect. What is the "
              "x-coordinate of the intersection?")), "4", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: set two rules equal and solve."),
        ],
        "A1.EXP.FN": [
            ("If f(x) = 3 * 2^x, what is f(4)?", "48", 6, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: evaluate an exponential rule."),
            ((("A colony of 50 bacteria doubles every hour. How many bacteria "
              "are there after 6 hours?")), "3200", 7, "WORD_PROBLEM",
             "INTEGER", "Stretch: compounding growth over several steps."),
        ],
    },
    "VA_ALGEBRA_1_SOL_2023": {
        "VAA1.EXPR": [
            ("Simplify: 2(3x - 1) - (x - 8).", "5x + 6", 6,
             "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: distribute, then subtract a group."),
            ("Combine: (5x^2 + 2x) + (x^2 - 7x).", "6x^2 - 5x", 6,
             "POLYNOMIAL_ADD_SUBTRACT", "FREE_TEXT",
             "Stretch: add polynomials with mixed-sign like terms."),
        ],
        "VAA1.LINEAR.EQ": [
            ("Solve for x: 4(x + 2) - 3x = 17.", "9", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: distribute and combine before isolating."),
            ("Solve for x: x/2 + 5 = 2x - 1.", "4", 8, "SOLVE_EQUATION",
             "INTEGER", "Stretch: fraction coefficient with variables both sides."),
        ],
        "VAA1.LINEAR.FN": [
            ((("A line has slope 3 and passes through (0, 2). If f is this "
              "line's rule, what is f(4)?")), "14", 6, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: build the rule, then evaluate."),
            ((("For what x do the rules 5x - 2 and 3x + 10 give the same "
              "output?")), "6", 7, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: set two expressions equal."),
        ],
        "VAA1.LINEAR.FN.SLOPE": [
            ("What is the slope of the line through (1, 7) and (3, 15)?", "4",
             6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: slope from two points."),
            ((("What is the slope of the line 2x + 5y = 10? Write as a "
              "fraction.")), "-2/5", 8, "LINEAR_FUNCTION", "FRACTION",
             "Stretch: rearrange to slope-intercept first."),
        ],
        "VAA1.LINEAR.FN.EVAL": [
            ("If g(t) = 60 - 4t, what is g(9)?", "24", 6, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: evaluate a decreasing linear rule."),
            ("If h(x) = x^2 + 1, what is h(-4)?", "17", 6, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: square a negative input."),
        ],
    },
    "DC_ALGEBRA_1_CCSS_M": {
        "DCA1.EXPR": [
            ("Simplify: 6a - 2(a + 4) + b.", "4a + b - 8", 7,
             "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: distribute a negative, two variables remain."),
            ("Expand and simplify: x(x - 3) + 2(x - 3).", "x^2 - x - 6", 7,
             "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: shared binomial factor hidden in two products."),
        ],
        "DCA1.LINEAR.EQ": [
            ("Solve for x: 3x - 7 = 2(x + 5).", "17", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: distribute on one side, then collect."),
            ("Solve for x: (2x - 4)/6 = 3.", "11", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: undo a quotient around a subtraction."),
        ],
        "DCA1.LINEAR.FN": [
            ("The line y = -x + 9 passes through (k, 2). What is k?", "7", 7,
             "LINEAR_FUNCTION", "INTEGER",
             "Stretch: solve for the input from a given output."),
            ((("A linear rule grows by 5 each step with f(0) = 3. What is "
              "f(6)?")), "33", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: apply a constant rate from a starting value."),
        ],
        "DCA1.LINEAR.FN.SLOPE": [
            ("What is the slope of the line through (-1, -2) and (5, 4)?",
             "1", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: slope from two negative-coordinate points."),
            ((("What is the slope of a line perpendicular to "
              "y = (1/3)x + 2?")), "-3", 8, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: perpendicular slope is the negative reciprocal."),
        ],
        "DCA1.LINEAR.FN.EVAL": [
            ("If p(n) = 8 + 3n, what is p(11)?", "41", 6, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: evaluate at a two-digit input."),
            ("If q(x) = 2x^2 - x, what is q(3)?", "15", 7, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: quadratic rule evaluation."),
        ],
    },
    "MD_INTEGRATED_ALGEBRA_1_2027_28": {
        # Skills are atomic decompositions — matched to their names, one each.
        "IA1.AT.A.1": [  # Equivalent Linear and Exponential Expressions
            ((("Evaluate the expressions 2(3)^x and 6(3)^(x-1) at x = 2. Are "
              "they equal? Answer yes or no.")), "yes", 7, "SIMPLIFY_EXPRESSION",
             "FREE_TEXT",
             "Stretch: equivalent exponential forms give equal values."),
        ],
        "IA1.AT.B.8": [  # Linear-Inequality Optimization
            ((("A student has at most $20 to spend on $2 notebooks and $1 pens. "
              "She buys 4 pens. What is the greatest number of notebooks she "
              "can buy?")), "8", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: maximize a variable under a budget constraint."),
        ],
        "IA1.AT.C.10": [  # Functions, Domain, and Range
            ((("For f(x) = 2x + 1 with domain {0, 1, 2, 3}, what is the largest "
              "value in the range?")), "7", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: map the domain through the rule."),
            ((("Which value is not in the range of f(x) = x^2: -1, 0, 4, or 9? "
              "Answer with the value.")), "-1", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: reason about which outputs a squaring rule can produce."),
        ],
        "IA1.AT.C.11": [  # Average Rate of Change
            ((("If f(2) = 10 and f(6) = 26, what is the average rate of change "
              "of f from x = 2 to x = 6?")), "4", 6, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: slope between two output points."),
            ((("For f(x) = x^2, what is the average rate of change from x = 1 "
              "to x = 4?")), "5", 7, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: nonlinear functions still have an average rate."),
        ],
        "IA1.AT.C.12": [  # Compare Linear and Exponential Functions
            ((("f(x) = 2x + 5 is linear and g(x) = 2^x is exponential. Which is "
              "larger at x = 5? Answer f or g.")), "g", 7, "LINEAR_FUNCTION",
             "FREE_TEXT",
             "Stretch: exponential growth overtakes linear growth."),
        ],
        "IA1.AT.D.13": [  # Arithmetic and Geometric Sequences
            ("A sequence starts 2, 6, 18, ... What is the next term?", "54", 6,
             "LINEAR_FUNCTION", "INTEGER",
             "Stretch: recognize a geometric ratio."),
            ((("An arithmetic sequence has 3rd term 11 and 5th term 19. What is "
              "the 1st term?")), "3", 8, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: recover the common difference from spaced terms."),
        ],
        "IA1.AT.D.14": [  # Function Representations and Features
            ((("A table shows f(0) = 4, f(1) = 7, f(2) = 10, f(3) = 13. What "
              "is f(5)?")), "19", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: extend a linear table pattern."),
            (("For y = (x - 3)^2, at what value of x does the vertex occur?"),
             "3", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: read the horizontal shift as the vertex location."),
        ],
        "IA1.AT.D.15": [  # Linear and Exponential Models
            ((("A $200 phone loses 20% of its value each year. What is it worth "
              "in dollars after 2 years?")), "128", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: repeated percent decay compounds."),
            ((("You save $15 per week starting with $40. What is your total in "
              "dollars after 10 weeks?")), "190", 6, "WORD_PROBLEM", "INTEGER",
             "Stretch: linear accumulation model."),
        ],
        "IA1.AT.D.16": [  # Function Transformations
            ((("The graph of f(x) = x^2 is shifted up 5 units. What is the new "
              "value of f(0)?")), "5", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: vertical shift adds to every output."),
            ((("If g(x) = f(x - 3) and f(4) = 10, what value of x makes "
              "g(x) = 10?")), "7", 7, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: horizontal shift delays the input."),
        ],
        "IA1.AT.D.17": [  # Inverse Linear Functions
            ("If f(x) = 3x - 6, what is the inverse of f evaluated at 9?",
             "5", 7, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: undo the rule to find the input."),
            ((("The inverse of f(x) = x + 7 is applied to 12. What is the "
              "result?")), "5", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: inverse undoes the added constant."),
        ],
        "IA1.DS.A.1": [  # Correlation and Causation
            ((("Ice cream sales and drowning incidents both rise in July. "
              "Does buying ice cream cause drowning? Answer correlation or "
              "causation for what the data shows.")), "correlation", 6,
             "WORD_PROBLEM", "FREE_TEXT",
             "Stretch: a shared lurking variable is not causation."),
        ],
        "IA1.DS.B.6": [  # Two-Way Data and Association
            ((("Of 80 students, 45 take art and 30 take both art and music. "
              "How many take art but not music?")), "15", 7, "WORD_PROBLEM",
             "INTEGER", "Stretch: subtract the overlap cell from the row total."),
        ],
        "IA1.GR.A.1": [  # Rigid Transformations and Congruence
            ((("A triangle is translated 4 units right and 2 units up. Does its "
              "area change? Answer yes or no.")), "no", 5, "WORD_PROBLEM",
             "FREE_TEXT",
             "Stretch: rigid motions preserve area."),
        ],
    },
    "MTH1W": {
        "MTH1W.B.NUM.INT": [
            ("Evaluate: (-6)(-4) + (-3)^2 - 5.", "28", 6, "SIGNED_NUMBERS",
             "INTEGER", "Stretch: mixed integer operations with a power."),
            ((("Of (-12)/(-3), -(-5), and (-2)^3, which is least? Answer with "
              "the value.")), "-8", 7, "SIGNED_NUMBERS", "INTEGER",
             "Stretch: evaluate three signed expressions, then compare."),
        ],
        "MTH1W.B.NUM.FRAC": [
            ("Compute: 5/6 - (-3/4). Write as a fraction.", "19/12", 7,
             "SIGNED_NUMBERS", "FRACTION",
             "Stretch: subtract a negative fraction."),
            ("Evaluate: (2/3)^2 x (9/2).", "2", 7, "INTEGER_OPERATIONS",
             "INTEGER", "Stretch: square a fraction, then multiply."),
        ],
        "MTH1W.C.ALG.EXPR": [
            ("Simplify: 5m - 2(3m - 4).", "-m + 8", 6, "SIMPLIFY_EXPRESSION",
             "FREE_TEXT", "Stretch: distribute a negative across two terms."),
            ((("For 4x^3 - 2x + 1, add the degree and the leading coefficient. "
              "What is the result?")), "7", 7, "SIMPLIFY_EXPRESSION", "INTEGER",
             "Stretch: read degree and coefficient, then combine."),
        ],
        "MTH1W.C.ALG.LIKE": [
            ("Simplify: 3x - (x - 2y) + 5y.", "2x + 7y", 6,
             "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: subtract a whole bracket with two variables."),
            ((("A triangle's sides are x, 2x + 3, and x - 1 units. What is its "
              "perimeter?")), "4x + 2", 7, "SIMPLIFY_EXPRESSION", "FREE_TEXT",
             "Stretch: model perimeter by collecting like terms."),
        ],
        "MTH1W.C.ALG.POLY": [
            ("Multiply: (x + 4)(x - 6).", "x^2 - 2x - 24", 6,
             "POLYNOMIAL_ADD_SUBTRACT", "FREE_TEXT",
             "Stretch: binomial product with a negative constant."),
            ("Multiply: (3x - 2)(x + 5).", "3x^2 + 13x - 10", 7,
             "POLYNOMIAL_ADD_SUBTRACT", "FREE_TEXT",
             "Stretch: binomial product with a leading coefficient."),
        ],
        "MTH1W.C.ALG.EQ1": [
            ("Solve for x: x/5 - 3 = 2.", "25", 6, "SOLVE_EQUATION", "INTEGER",
             "Stretch: undo a quotient and a subtraction."),
            ("Solve for x: 0.4x + 1.2 = 4.", "7", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: decimal coefficients in two steps."),
        ],
        "MTH1W.C.ALG.EQ2": [
            ("Solve for x: 6x - 5 = 2x + 19.", "6", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: variable terms on both sides."),
            ("Solve for x: 4x + 9 = x - 6.", "-5", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: collect to a negative solution."),
        ],
        "MTH1W.C.ALG.EQ3": [
            ("Solve for x: 2(3x - 1) = 4(x + 3).", "7", 7, "SOLVE_EQUATION",
             "INTEGER", "Stretch: distribute on both sides."),
            ("Solve for x: 5(x - 2) - 2(x + 1) = 3.", "5", 8,
             "SOLVE_EQUATION", "INTEGER",
             "Stretch: two distributions, then isolate."),
        ],
        "MTH1W.C.REL.SLOPE": [
            ("What is the slope of the line through (-3, 2) and (1, 10)?",
             "2", 6, "LINEAR_FUNCTION", "INTEGER",
             "Stretch: slope from two points."),
            ((("A taxi charges a flat $4 plus $2 per km. What is the rate of "
              "change in dollars per km?")), "2", 6, "LINEAR_FUNCTION",
             "INTEGER", "Stretch: read the rate out of a cost model."),
        ],
        "MTH1W.C.REL.EVAL": [
            ((("A car rental costs C = 25 + 0.15k dollars for k kilometres. "
              "What is the cost in dollars for 40 km?")), "31", 6,
             "LINEAR_FUNCTION", "INTEGER",
             "Stretch: evaluate a two-parameter linear model."),
            ("If h(t) = -5t^2 + 20t, what is h(2)?", "20", 7,
             "LINEAR_FUNCTION", "INTEGER",
             "Stretch: evaluate a projectile-style quadratic."),
        ],
        "MTH1W.C.QUAD": [
            ("For y = x^2 - 4x, what is y when x = 5?", "5", 6,
             "LINEAR_FUNCTION", "INTEGER",
             "Stretch: evaluate a quadratic at an integer."),
            ((("The equation x^2 - 9 = 0 has two solutions. What is the larger "
              "one?")), "3", 7, "SOLVE_EQUATION", "INTEGER",
             "Stretch: solve a difference of squares."),
        ],
        "MTH1W.F.FIN.PCT": [
            ((("You invest $500 at 4% simple interest per year. How much "
              "interest in dollars do you earn in 3 years?")), "60", 6,
             "WORD_PROBLEM", "INTEGER",
             "Stretch: simple interest multiplies principal, rate, time."),
            ((("A $2,000 investment grows 5% per year. What is it worth in "
              "dollars after 2 years?")), "2205", 7, "WORD_PROBLEM", "INTEGER",
             "Stretch: compound growth squares the factor."),
        ],
        "MTH1W.F.FIN.APP": [
            (("A bike costs $1,200. What is a 15% down payment in dollars?"),
             "180", 6, "WORD_PROBLEM", "INTEGER",
             "Stretch: percent of a price."),
            ((("A $60 item is on sale for 25% off, then 13% tax is added to the "
              "sale price. What is the total in dollars?")), "50.85", 8,
             "WORD_PROBLEM", "DECIMAL",
             "Stretch: discount, then tax on the reduced base."),
        ],
    },
}


def seed() -> None:
    written = 0
    with SessionLocal() as db:
        for curriculum_code, by_skill in EXTENSIONS.items():
            curriculum = db.scalar(
                select(Curriculum).where(Curriculum.code == curriculum_code)
            )
            if curriculum is None:
                raise ValueError(f"Curriculum {curriculum_code} not seeded")
            for skill_code, problems in by_skill.items():
                skill = db.scalar(
                    select(Skill).where(
                        Skill.curriculum_id == curriculum.id,
                        Skill.code == skill_code,
                    )
                )
                if skill is None:
                    raise ValueError(
                        f"Skill {skill_code} missing in {curriculum_code}"
                    )
                for prompt, answer, difficulty, ptype, akind, objective in problems:
                    _extension_problem(
                        db, curriculum, skill, prompt, answer, difficulty,
                        ptype, akind, objective,
                    )
                    written += 1
        db.commit()
    print(f"Seeded {written} extension problems across {len(EXTENSIONS)} curricula")


if __name__ == "__main__":
    seed()
