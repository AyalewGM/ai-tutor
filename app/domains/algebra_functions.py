"""Canonical expressions, equations, and linear-function problem families."""

from __future__ import annotations

import random

from app.canonical_problem_families import ALL_MODES, ProblemFamilySpec

FAMILIES: dict[str, ProblemFamilySpec] = {
    "MATH.ALG.EXPR.EVALUATE": ProblemFamilySpec("MATH.ALG.EXPR.EVALUATE","Evaluate an algebraic expression","MATH.EE.EXPR","EVALUATE_EXPRESSION",1,4,ALL_MODES,frozenset({"procedural_fluency","representation"})),
    "MATH.ALG.EXPR.TRANSLATE": ProblemFamilySpec("MATH.ALG.EXPR.TRANSLATE","Translate words to an expression","MATH.EE.EXPR","MODEL_EXPRESSION",1,4,ALL_MODES,frozenset({"representation","modeling"})),
    "MATH.ALG.EXPR.ERROR.DISTRIBUTE": ProblemFamilySpec("MATH.ALG.EXPR.ERROR.DISTRIBUTE","Diagnose a distributive-property error","MATH.EE.EXPR","ERROR_ANALYSIS",2,4,ALL_MODES,frozenset({"conceptual_understanding","error_analysis","misconception_probe"})),
    "MATH.ALG.LIKE.COMBINE": ProblemFamilySpec("MATH.ALG.LIKE.COMBINE","Combine like terms","MATH.EE.LIKE_TERMS","SIMPLIFY_EXPRESSION",1,4,ALL_MODES,frozenset({"procedural_fluency","structure_identification"})),
    "MATH.ALG.LIKE.CLASSIFY": ProblemFamilySpec("MATH.ALG.LIKE.CLASSIFY","Identify like terms","MATH.EE.LIKE_TERMS","CLASSIFICATION",1,3,ALL_MODES,frozenset({"conceptual_understanding","representation"})),
    "MATH.ALG.EQ.ONE.MULT": ProblemFamilySpec("MATH.ALG.EQ.ONE.MULT","One-step multiplicative equations","MATH.EE.EQUATION.ONE","SOLVE_EQUATION",1,3,ALL_MODES,frozenset({"procedural_fluency","inverse_operations"})),
    "MATH.ALG.EQ.MULTISTEP.DISTRIBUTE": ProblemFamilySpec("MATH.ALG.EQ.MULTISTEP.DISTRIBUTE","Multi-step equations with distribution","MATH.EE.EQUATION.MULTISTEP","SOLVE_EQUATION",2,4,ALL_MODES,frozenset({"procedural_fluency","reasoning","operation_sequence"})),
    "MATH.ALG.EQ.MULTISTEP.BOTH_SIDES": ProblemFamilySpec("MATH.ALG.EQ.MULTISTEP.BOTH_SIDES","Variables on both sides","MATH.EE.EQUATION.MULTISTEP","SOLVE_EQUATION",2,4,ALL_MODES,frozenset({"procedural_fluency","reasoning"})),
    "MATH.ALG.EQ.WORD.TARGET": ProblemFamilySpec("MATH.ALG.EQ.WORD.TARGET","Target-total multi-step modeling","MATH.EE.EQUATION.MULTISTEP","WORD_PROBLEM",2,4,ALL_MODES,frozenset({"modeling","transfer","reasoning"})),
    "MATH.FUNC.LINEAR.EVALUATE": ProblemFamilySpec("MATH.FUNC.LINEAR.EVALUATE","Evaluate a linear function","MATH.F.LINEAR.EVALUATE","FUNCTION_EVALUATION",1,4,ALL_MODES,frozenset({"procedural_fluency","representation"})),
    "MATH.FUNC.LINEAR.SLOPE.TABLE": ProblemFamilySpec("MATH.FUNC.LINEAR.SLOPE.TABLE","Determine slope from a table","MATH.F.LINEAR.SLOPE_INTERCEPT","TABLE_REASONING",2,4,ALL_MODES,frozenset({"representation","reasoning","conceptual_understanding"})),
    "MATH.FUNC.LINEAR.MODEL": ProblemFamilySpec("MATH.FUNC.LINEAR.MODEL","Build a linear model from context","MATH.F.LINEAR.SLOPE_INTERCEPT","MODEL_EQUATION",2,4,ALL_MODES,frozenset({"modeling","transfer","representation"})),
    "MATH.FUNC.LINEAR.ERROR.INTERCEPT": ProblemFamilySpec("MATH.FUNC.LINEAR.ERROR.INTERCEPT","Diagnose slope/intercept confusion","MATH.F.LINEAR.SLOPE_INTERCEPT","ERROR_ANALYSIS",2,4,ALL_MODES,frozenset({"error_analysis","misconception_probe","conceptual_understanding"})),
}


def build(family_code: str, rng: random.Random, difficulty: int):
    if family_code == "MATH.ALG.EXPR.EVALUATE":
        x=rng.randint(-4 if difficulty>=3 else 1,8+difficulty); a=rng.randint(2,5+difficulty); b=rng.randint(1,7)
        return f"Evaluate {a}x + {b} when x = {x}.",str(a*x+b),(f"Substitute {x} for x.",f"Compute {a}({x}) before adding {b}."),{"ALG.EXPR.IGNORE_COEFFICIENT":str(x+b)}
    if family_code == "MATH.ALG.EXPR.TRANSLATE":
        a=rng.randint(2,7); b=rng.randint(1,9)
        return f"Which expression represents {b} more than {a} times a number n?",f"{a}n+{b}",("Translate 'times a number' first.","Then add the amount described by 'more than'."),{"ALG.TRANSLATE.REVERSE":f"{b}n+{a}","ALG.TRANSLATE.ADD_ONLY":f"{a}+n+{b}"}
    if family_code == "MATH.ALG.EXPR.ERROR.DISTRIBUTE":
        a=rng.randint(2,6); b=rng.randint(2,8)
        prompt=f"A student rewrites {a}(x + {b}) as {a}x + {b}. Which statement identifies the error? (A) The multiplier must apply to both terms. (B) The terms should be subtracted. (C) x should be squared. (D) There is no error."
        return prompt,"A",("Compare the original expression with the distributive property.","The outside factor multiplies every term inside the parentheses."),{"ALG.DISTRIBUTE.MISSED_CONSTANT":"D"}
    if family_code == "MATH.ALG.LIKE.COMBINE":
        a=rng.randint(2,7); b=rng.randint(2,7); c=rng.randint(1,9)
        return f"Simplify {a}x + {b}x + {c}.",f"{a+b}x+{c}",("Identify terms with the same variable part.",f"Add the coefficients {a} and {b}; keep the constant separate."),{"ALG.LIKE.COMBINE_CONSTANT":f"{a+b+c}x"}
    if family_code == "MATH.ALG.LIKE.CLASSIFY":
        a=rng.randint(2,8); b=rng.randint(2,8)
        return f"Which pair contains like terms? (A) {a}x and {b}x (B) {a}x and {b}y (C) {a} and {b}x (D) x and x²","A",("Like terms have identical variable parts.","Coefficients may differ; variables and exponents must match."),{"ALG.LIKE.VARIABLE_CONFUSION":"B"}
    if family_code == "MATH.ALG.EQ.ONE.MULT":
        x=rng.randint(2,12+difficulty*2); a=rng.randint(2,7); total=a*x
        return f"Solve {a}x = {total}.",f"x={x}",(f"Undo multiplication by {a}.",f"Divide both sides by {a}."),{"ALG.EQ.MULTIPLY_AGAIN":f"x={total*a}"}
    if family_code == "MATH.ALG.EQ.MULTISTEP.DISTRIBUTE":
        x=rng.randint(2,8+difficulty); a=rng.randint(2,5); b=rng.randint(1,6); c=rng.randint(1,8); total=a*(x+b)+c
        return f"Solve {a}(x + {b}) + {c} = {total}.",f"x={x}",("Undo the outside addition or distribute consistently.","After isolating the parenthesized term, divide by its coefficient and finish isolating x."),{"ALG.EQ.SKIP_DISTRIBUTION":f"x={total-a*b-c}"}
    if family_code == "MATH.ALG.EQ.MULTISTEP.BOTH_SIDES":
        x=rng.randint(2,10+difficulty); right_a=rng.randint(1,3); left_a=right_a+rng.randint(1,4); b=rng.randint(1,8); d=(left_a-right_a)*x+b
        return f"Solve {left_a}x + {b} = {right_a}x + {d}.",f"x={x}",("Move variable terms to one side using the same operation on both sides.",f"Subtract {right_a}x from both sides, then isolate x."),{"ALG.EQ.DROP_RIGHT_VARIABLE":f"x={(d-b)//left_a}"}
    if family_code == "MATH.ALG.EQ.WORD.TARGET":
        weeks=rng.randint(3,7); per=rng.randint(4,12); start=rng.randint(5,20); target=start+weeks*per
        return f"Sam already has {start} points and earns {per} points each week. How many weeks are needed to reach exactly {target} points?",str(weeks),(f"Model the total as {start} + {per}w = {target}.","Remove the starting points before dividing by the weekly rate."),{"ALG.WORD.IGNORE_START":str(target//per)}
    if family_code == "MATH.FUNC.LINEAR.EVALUATE":
        x=rng.randint(-4 if difficulty>=3 else 1,8); m=rng.randint(2,6); b=rng.randint(-5 if difficulty>=3 else 1,7)
        return f"If f(x) = {m}x + {b}, find f({x}).",str(m*x+b),(f"Substitute {x} everywhere x appears.","Multiply before adding the intercept."),{"FUNC.EVAL.RETURN_X":str(x)}
    if family_code == "MATH.FUNC.LINEAR.SLOPE.TABLE":
        m=rng.choice([-3,-2,2,3,4] if difficulty>=3 else [2,3,4]); b=rng.randint(-4,6); x0=rng.randint(-2,2); x1=x0+rng.randint(1,3); y0=m*x0+b; y1=m*x1+b
        return f"A linear function contains the points ({x0}, {y0}) and ({x1}, {y1}). What is its slope?",str(m),("Slope measures change in y per unit change in x.",f"Compute ({y1} - {y0}) / ({x1} - {x0})."),{"FUNC.SLOPE.RECIPROCAL":str((x1-x0)/(y1-y0))}
    if family_code == "MATH.FUNC.LINEAR.MODEL":
        m=rng.randint(2,8); b=rng.randint(3,15)
        return f"A service charges a fixed fee of ${b} plus ${m} per hour. Which equation gives total cost C after h hours?",f"C={m}h+{b}",("The fixed fee is the value when h = 0.","The hourly charge is the rate multiplying h."),{"FUNC.MODEL.SWAP":f"C={b}h+{m}"}
    if family_code == "MATH.FUNC.LINEAR.ERROR.INTERCEPT":
        m=rng.randint(2,7); b=rng.randint(1,9)
        return f"For y = {m}x + {b}, a student says the slope is {b} and the y-intercept is {m}. Which response is correct? (A) The student swapped slope and intercept. (B) The student is correct. (C) Both values should be negative. (D) The equation is not linear.","A",("Compare the equation with y = mx + b.","m is slope; b is the y-intercept."),{"FUNC.SLOPE_INTERCEPT.SWAPPED":"B"}
    raise ValueError(f"No algebra/function builder for family: {family_code}")
