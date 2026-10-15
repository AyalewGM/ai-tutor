"""Generate extension (challenge-tier) problems for the DMV elementary packs.

The three jurisdictions (DC, MD, VA) share identical skill skeletons per
grade, so this generator authors each stretch problem once as a parametric
template and instantiates it with different numbers per pack — deterministic
via a fixed seed per pack, so rerunning produces identical output and the
packs stay idempotent.

Extension problems are opt-in: modes ["extension"] only, authored above each
skill's normal band, never evidence. md-grade3 already has a hand-authored
extension pool and is skipped.
"""

import json
import random
from fractions import Fraction
from pathlib import Path

PACK_DIR = Path(__file__).parents[1] / "docs/curriculum/packs"


def _t(prompt: str, answer, difficulty: int, objective: str) -> dict:
    return {
        "prompt": prompt,
        "canonical_answer": str(answer),
        "difficulty": difficulty,
        "objective": objective,
    }


# ---------------------------------------------------------------------------
# Grade-band templates. Each value is a list of callables taking a seeded RNG
# and returning a problem dict. Two per skill, difficulty above the pack band.
# ---------------------------------------------------------------------------

GRADE1 = {
    "NS.COUNT_COMPARE": [
        lambda r: _t(
            f"Start at {(s := r.randrange(20, 90))}. Count forward {(k := r.randrange(15, 35))}. What number do you reach?",
            s + k, 4, "Stretch: count forward across a decade."),
        lambda r: _t(
            f"Which number is bigger, {(a := r.randrange(61, 99))} or "
            f"{(b := a + r.randrange(1, 9))}? Answer with the number.",
            b, 4, "Stretch: compare two two-digit numbers."),
    ],
    "NBT.PLACE_VALUE": [
        lambda r: _t(
            f"A number has {(t := r.randrange(3, 8))} tens and {(o := r.randrange(10, 19))} ones. What is the number?",
            t * 10 + o, 5, "Stretch: regroup more than ten ones."),
        lambda r: _t(
            f"What is 10 more than the number made of {(t := r.randrange(2, 8))} tens and "
            f"{(o := r.randrange(1, 9))} ones?",
            t * 10 + o + 10, 5, "Stretch: compose, then add a ten."),
    ],
    "OA.ADDITION_20": [
        lambda r: _t(
            f"{(a := r.randrange(6, 10))} + {(b := r.randrange(5, 9))} + {(c := r.randrange(3, 6))} = ?",
            a + b + c, 5, "Stretch: three addends with regrouping."),
        lambda r: _t(
            f"? + {(b := r.randrange(4, 8))} = {(t := r.randrange(13, 18))}. Add "
            f"{(c := r.randrange(2, 5))} more to the missing number. What do you get?",
            t - b + c, 5, "Stretch: find a missing addend, then keep going."),
    ],
    "OA.SUBTRACTION_20": [
        lambda r: _t(
            f"{(a := r.randrange(15, 20))} - {(b := r.randrange(4, 9))} - {(c := r.randrange(2, 6))} = ?",
            a - b - c, 5, "Stretch: two subtractions in a row."),
        lambda r: _t(
            f"Start at {(a := r.randrange(13, 18))}, subtract a number, and land on "
            f"{(b := r.randrange(4, 8))}. What number was subtracted?",
            a - b, 5, "Stretch: unknown subtrahend."),
    ],
    "OA.WORD_PROBLEM_20": [
        lambda r: _t(
            f"Mia had {(a := r.randrange(12, 19))} stickers. She gave some away and has "
            f"{(b := r.randrange(4, 8))} left. How many stickers did she give away?",
            a - b, 5, "Stretch: missing-part word problem."),
        lambda r: _t(
            f"There are {(a := r.randrange(6, 10))} red and {(b := r.randrange(5, 9))} blue marbles in a jar. "
            f"After losing {(c := r.randrange(4, 7))} marbles, how many remain?",
            a + b - c, 5, "Stretch: combine, then take away."),
    ],
    "OA.EQUATION_BALANCE": [
        lambda r: _t(
            f"Fill in the missing number: {(a := r.randrange(6, 10))} + ? = "
            f"{(b := r.randrange(4, 8))} + {(c := r.randrange(4, 8))}.",
            b + c - a, 5, "Stretch: balance both sides of the equal sign."),
        lambda r: _t(
            f"Fill in the missing number: {(a := r.randrange(11, 16))} - ? = "
            f"{(b := r.randrange(3, 6))} + {(c := r.randrange(2, 5))}.",
            a - b - c, 5, "Stretch: missing subtrahend on a balance."),
    ],
    "MD.TELL_TIME": [
        lambda r: _t(
            f"Recess starts at {(h := r.randrange(1, 5))}:30 and ends at {h + 1}:00. "
            "How many minutes is recess?",
            30, 4, "Stretch: elapsed time across the hour."),
        lambda r: _t(
            f"The clock shows half past {(h := r.randrange(3, 9))}. What time is it 30 minutes later? "
            "Write like 8:00.",
            f"{h + 1}:00", 5, "Stretch: half past plus a half hour."),
    ],
    "G.SHAPES": [
        lambda r: _t(
            "A shape has 3 straight sides and 3 corners. What shape is it?",
            "triangle", 4, "Stretch: name a shape from its attributes."),
        lambda r: _t(
            "How many sides do two separate triangles have altogether?",
            6, 4, "Stretch: count attributes across two figures."),
    ],
}

GRADE2 = {
    "NBT.PLACE_VALUE": [
        lambda r: _t(
            f"A number has {(h := r.randrange(2, 6))} hundreds, {(t := r.randrange(10, 15))} tens, and "
            f"{(o := r.randrange(1, 9))} ones. What is the number?",
            h * 100 + t * 10 + o, 6, "Stretch: regroup more than ten tens."),
        lambda r: _t(
            f"Start with {(a := r.randrange(340, 480))}. Add {(b := r.randrange(11, 25))}, then subtract 100. "
            "What number do you get?",
            a + b - 100, 5, "Stretch: two-step across a hundred."),
    ],
    "NBT.PATTERNS": [
        lambda r: _t(
            f"Count by 25s starting at {(s := r.randrange(2, 8) * 100 + r.randrange(0, 4) * 25)}: "
            "what is the 4th number you say?",
            s + 75, 5, "Stretch: skip-count by 25s."),
        lambda r: _t(
            f"Pattern: {(a := r.randrange(8, 20))}, {a + (d := r.randrange(4, 9))}, "
            f"{a + 2 * d}, ... What comes next?",
            a + 3 * d, 5, "Stretch: extend an add-d pattern."),
    ],
    "NBT.ADDITION_100": [
        lambda r: _t(
            f"{(a := r.randrange(30, 55))} + {(b := r.randrange(15, 100 - a - 10))} + ? = 100. "
            "What is the missing number?",
            100 - a - b, 6, "Stretch: three addends to a round hundred."),
        lambda r: _t(
            f"Two numbers add to 100. One of them is {(a := r.randrange(23, 79))}. What is the other?",
            100 - a, 5, "Stretch: unknown part of 100."),
    ],
    "NBT.SUBTRACTION_100": [
        lambda r: _t(
            f"100 - {(a := r.randrange(30, 50))} - {(b := r.randrange(15, 30))} = ?",
            100 - a - b, 5, "Stretch: subtract twice from 100."),
        lambda r: _t(
            f"{(a := r.randrange(70, 99))} - ? = {(b := r.randrange(40, 60))}. What is the missing number?",
            a - b, 5, "Stretch: unknown subtrahend within 100."),
    ],
    "OA.WORD_PROBLEM_100": [
        lambda r: _t(
            f"A baker made {(a := r.randrange(55, 80))} rolls, sold {(b := r.randrange(20, 35))} in the "
            f"morning and {(c := r.randrange(12, 22))} after lunch. How many rolls are left?",
            a - b - c, 6, "Stretch: two take-aways in one story."),
        lambda r: _t(
            f"The library had {(a := r.randrange(35, 60))} books on the shelf. {(b := r.randrange(12, 20))} "
            f"were borrowed and {(c := r.randrange(5, 12))} were returned. How many are on the shelf now?",
            a - b + c, 6, "Stretch: subtract then add in context."),
    ],
    "MD.MONEY": [
        lambda r: _t(
            f"You have {(q := r.randrange(2, 4))} quarters, {(d := r.randrange(1, 4))} dimes, and "
            f"{(p := r.randrange(2, 7))} pennies. How many cents is that?",
            q * 25 + d * 10 + p, 6, "Stretch: mixed coins to cents."),
        lambda r: _t(
            f"A snack costs {(c := r.randrange(55, 85))} cents. You pay with a dollar bill. "
            "How many cents change do you get?",
            100 - c, 5, "Stretch: change from a dollar."),
    ],
    "MD.LENGTH": [
        lambda r: _t(
            f"A pencil is {(a := r.randrange(14, 22))} cm long and a crayon is "
            f"{(b := r.randrange(7, 12))} cm long. How many cm longer is the pencil?",
            a - b, 5, "Stretch: compare lengths by subtracting."),
        lambda r: _t(
            f"A ribbon is {(t := r.randrange(50, 80))} cm long. You cut off two pieces of "
            f"{(c := r.randrange(10, 20))} cm each. How much ribbon is left?",
            t - 2 * c, 6, "Stretch: repeated measurement removal."),
    ],
    "MD.TIME": [
        lambda r: _t(
            f"A cartoon starts at {(h := r.randrange(3, 7))}:45 and lasts 30 minutes. "
            "What time does it end? Write like 5:15.",
            f"{h + 1}:15", 5, "Stretch: duration across the hour."),
        lambda r: _t(
            f"The clock shows {(m := r.randrange(5, 15))} minutes before {(h := r.randrange(4, 11))} o'clock. "
            "What time is it? Write like 7:50.",
            f"{h - 1}:{60 - m}", 6, "Stretch: minutes before the hour."),
    ],
    "G.SHAPES_FRACTIONS": [
        lambda r: _t(
            f"A pizza is cut into {(n := r.choice([6, 8]))} equal slices. You eat "
            f"{(e := r.randrange(2, n - 3))} slices. What fraction of the pizza is left?",
            f"{n - e}/{n}", 5, "Stretch: fraction remaining after eating some."),
        lambda r: _t(
            f"A rectangle is split into {(n := r.choice([4, 6]))} equal parts and "
            f"{(s := r.randrange(2, n))} are shaded. What fraction is shaded?",
            f"{s}/{n}", 4, "Stretch: part-whole fraction of a figure."),
    ],
}

GRADE3 = {
    "OA.MULTIPLICATION": [
        lambda r: _t(
            f"{(a := r.randrange(6, 9))} rows of {(b := r.randrange(6, 9))} chairs are set up, and "
            f"{(c := r.randrange(5, 15))} more chairs arrive. How many chairs in all?",
            a * b + c, 5, "Stretch: multiply, then add."),
        lambda r: _t(
            f"{(a := r.randrange(5, 9))} × ? = {(k := r.randrange(5, 9))} × {a}. "
            "What is the missing factor?",
            k, 5, "Stretch: commutative property in disguise."),
    ],
    "OA.DIVISION": [
        lambda r: _t(
            f"{(d := r.randrange(6, 9)) * (q := r.randrange(6, 9))} pencils are shared "
            f"equally into {d} boxes. How many pencils are in {(t := r.randrange(2, 4))} "
            "boxes together?",
            q * t, 5, "Stretch: divide, then scale back up."),
        lambda r: _t(
            f"A number divided by {(d := r.randrange(6, 9))} gives {(q := r.randrange(6, 9))}. "
            "What is the number?",
            d * q, 5, "Stretch: undo a division."),
    ],
    "OA.FACT_FAMILIES": [
        lambda r: _t(
            f"{(a := r.randrange(5, 9)) * ((k := r.randrange(5, 9)) + 1)} = {a} × ?. "
            "What is the missing factor?",
            k + 1, 6, "Stretch: product hidden inside a bigger product."),
        lambda r: _t(
            f"To find {(a := r.randrange(6, 9))} × {(b := r.randrange(6, 9))}, you can compute "
            f"{a} × 10 and then subtract {a} × ?. What is the missing number?",
            10 - b, 7, "Stretch: use the distributive property."),
    ],
    "NBT.PLACE_VALUE": [
        lambda r: _t(
            f"Round {(n := r.randrange(3200, 4900))} to the nearest hundred, then subtract "
            f"{(s := r.randrange(2, 6) * 100)}. What is the result?",
            round(n, -2) - s, 6, "Stretch: round first, then subtract."),
        lambda r: _t(
            "A number rounds to 500 to the nearest hundred and to 480 to the nearest ten. "
            "Its ones digit is 4. What is the number?",
            484, 7, "Stretch: satisfy two rounding constraints."),
    ],
    "NF.FRACTIONS": [
        lambda r: _t(
            f"Which is larger: 3/4 of {(a := r.choice([16, 20, 24]))} or 2/3 of "
            f"{(b := r.choice([18, 24, 30]))}? Give the larger value.",
            max(Fraction(3, 4) * a, Fraction(2, 3) * b), 6,
            "Stretch: compare fractions of different wholes."),
        lambda r: _t(
            f"How many sixths are equal to {(h := r.randrange(2, 4))} halves?",
            h * 3, 6, "Stretch: convert halves into sixths."),
    ],
    "MD.TIME": [
        lambda r: _t(
            f"A film starts at {(h := r.randrange(2, 5))}:{(m := r.choice([10, 15, 20]))} PM and is "
            f"{(d := r.choice([50, 65, 80]))} minutes long. When does it end? Write like 5:05 PM.",
            f"{h + (m + d) // 60}:{(m + d) % 60:02d} PM",
            6, "Stretch: elapsed minutes across the hour."),
        lambda r: _t(
            f"School ends at 3:30 PM. It is now 2:{(n := r.randrange(35, 55))} PM. "
            "How many minutes until school ends?",
            90 - n, 6, "Stretch: minutes remaining to a clock time."),
    ],
    "MD.DATA": [
        lambda r: _t(
            f"A bar graph shows Mon: {(a := r.randrange(8, 15))}, Tue: {(b := r.randrange(15, 22))}, "
            f"Wed: {(c := r.randrange(5, 10))} books read. How many more books were read on "
            "Mon and Tue together than on Wed?",
            a + b - c, 6, "Stretch: combine two bars, then compare."),
        lambda r: _t(
            f"In a picture graph each book symbol = {(s := r.choice([2, 4]))} books. Fiction has "
            f"{(f := r.randrange(4, 7))} symbols and nonfiction has {(n := r.randrange(2, f - 1))} symbols. "
            "How many more fiction books than nonfiction?",
            (f - n) * s, 6, "Stretch: scale symbols before comparing."),
    ],
    "MD.AREA_PERIMETER": [
        lambda r: _t(
            f"A rectangle has area {(w := r.choice([4, 5, 6]) * (l := r.randrange(7, 12)))} square cm "
            f"and width {w} cm. What is its perimeter in cm?",
            2 * (l + w), 6, "Stretch: find length from area, then perimeter."),
        lambda r: _t(
            f"A square has perimeter {4 * (s := r.randrange(5, 9))} cm. What is its area in "
            "square cm?",
            s * s, 6, "Stretch: perimeter to side to area."),
    ],
    "G.SHAPES": [
        lambda r: _t(
            f"A hexagon has all sides {(s := r.randrange(2, 6))} cm long. What is its perimeter in cm?",
            s * 6, 5, "Stretch: perimeter of a regular polygon."),
        lambda r: _t(
            "Two identical squares share one whole side. How many sides does the outside "
            "of the combined figure have?",
            6, 6, "Stretch: shared edges disappear from the outside count."),
    ],
}

GRADE4 = {
    "OA.COMPARISON": [
        lambda r: _t(
            f"Jordan has {(m := r.randrange(4, 7))} times as many cards as Kai. Kai has "
            f"{(d := r.randrange(3, 8))} fewer cards than Leo, who has {(l := r.randrange(15, 25))}. "
            "How many cards does Jordan have?",
            m * (l - d), 6, "Stretch: chained multiplicative and additive comparison."),
        lambda r: _t(
            f"A is {(m := r.randrange(3, 6))} times B, and together A and B make "
            f"{(m + 1) * (b := r.randrange(8, 15))}. What is B?",
            b, 7, "Stretch: total split by a multiplicative ratio."),
    ],
    "OA.MULTI_STEP": [
        lambda r: _t(
            f"You buy {(p := r.randrange(3, 5))} packs of {(n := r.randrange(10, 14))} pens, give away "
            f"one whole pack, then lose {(l := r.randrange(3, 8))} pens. How many pens are left?",
            p * n - n - l, 6, "Stretch: multiply, remove a pack, remove more."),
        lambda r: _t(
            f"You earn ${(w := r.randrange(6, 10))} per day for {(d := r.randrange(4, 7))} days and "
            f"spend ${(s := r.randrange(15, 25))} twice. How many dollars do you have left?",
            w * d - 2 * s, 6, "Stretch: earnings minus repeated spending."),
    ],
    "OA.FACTORS_PATTERNS": [
        lambda r: _t(
            f"What is the smallest number greater than {(t := r.randrange(30, 60))} that is a "
            "multiple of both 6 and 8?",
            (t // 24 + 1) * 24, 7, "Stretch: common multiple above a bound."),
        lambda r: _t(
            f"How many factors does {(n := r.choice([24, 36, 48]))} have?",
            sum(1 for i in range(1, n + 1) if n % i == 0), 6,
            "Stretch: count factor pairs."),
    ],
    "NBT.PLACE_VALUE": [
        lambda r: _t(
            f"In the number {(n := r.randrange(200_000, 900_000))}, what digit is in the ten "
            "thousands place?",
            (n // 10_000) % 10, 4, "Stretch: identify a place beyond thousands."),
        lambda r: _t(
            "The 4 in 245,381 is how many times as large as the 4 in 3,420?",
            100, 7, "Stretch: same digit, different place values."),
    ],
    "NBT.MULTIPLY": [
        lambda r: _t(
            f"{(a := r.randrange(25, 60))} × {(b := r.randrange(15, 45))} = ?",
            a * b, 6, "Stretch: two-digit by two-digit multiplication."),
        lambda r: _t(
            f"What is 25 × {(b := r.choice([36, 44, 48, 64]))}? Think of 25 as a quarter of 100.",
            25 * b, 6, "Stretch: multiply by 25 via quarters."),
    ],
    "NBT.DIVIDE": [
        lambda r: _t(
            f"{(q := r.randrange(120, 320)) * (d := r.randrange(4, 8))} ÷ {d} = ?",
            q, 5, "Stretch: four-digit division by one digit."),
        lambda r: _t(
            f"A number divided by {(d := r.randrange(5, 9))} gives {(q := r.randrange(80, 160))} "
            f"with remainder {(rem := r.randrange(1, d))}. What is the number?",
            q * d + rem, 7, "Stretch: undo division with a remainder."),
    ],
    "NF.FRACTIONS": [
        lambda r: _t(
            f"{(a := r.choice([3, 5]))}/4 + {(b := r.choice([3, 5, 7]))}/8 = ? "
            "Write as a fraction.",
            str(Fraction(a, 4) + Fraction(b, 8)), 6,
            "Stretch: add fractions with unlike denominators."),
        lambda r: _t(
            "Which is greater, 7/8 or 5/6? Answer with the fraction.",
            "7/8", 6, "Stretch: compare fractions across denominators."),
    ],
    "NF.DECIMALS": [
        lambda r: _t(
            "What is 0.7 + 0.06 + 0.004?",
            "0.764", 5, "Stretch: align three different decimal places."),
        lambda r: _t(
            "Which is greater, 0.608 or 0.68? Give the value.",
            "0.68", 5, "Stretch: tenths beat hundredths."),
    ],
    "MD.MEASUREMENT": [
        lambda r: _t(
            f"A jug holds {(l := r.randrange(2, 5))} liters. How many 250-mL cups fill it?",
            l * 4, 5, "Stretch: convert, then measure out."),
        lambda r: _t(
            f"A board is {(f := r.randrange(3, 6))} feet {(i := r.randrange(4, 10))} inches long. "
            "How many inches is that?",
            f * 12 + i, 5, "Stretch: feet-and-inches to inches."),
    ],
    "MD.ANGLE_LINES": [
        lambda r: _t(
            f"Two angles form a right angle. One is {(a := r.randrange(25, 65))} degrees. "
            "How many degrees is the other?",
            90 - a, 5, "Stretch: complementary angles."),
        lambda r: _t(
            f"A straight angle is split into {(a := r.randrange(30, 60))} degrees, "
            f"{(b := r.randrange(40, 70))} degrees, and a third angle. How many degrees is "
            "the third angle?",
            180 - a - b, 6, "Stretch: partition 180 degrees."),
    ],
}

GRADE5 = {
    "OA.EXPRESSIONS": [
        lambda r: _t(
            f"Evaluate: {(a := r.choice([12, 24, 36]))} ÷ ({(b := r.randrange(2, 5))} + 1) × "
            f"{(c := r.randrange(2, 4))} + {(d := r.randrange(3, 9))}.",
            a // (b + 1) * c + d, 6, "Stretch: parentheses, then left-to-right."),
        lambda r: _t(
            f"Evaluate: ({(a := r.randrange(10, 18))} - {(b := r.randrange(2, 5))} × "
            f"{(c := r.randrange(2, 4))})^2.",
            (a - b * c) ** 2, 7, "Stretch: inner expression, then square."),
    ],
    "OA.PATTERNS": [
        lambda r: _t(
            "A pattern follows the rule 'multiply by 2, then add 3' starting at 4: "
            "4, 11, 25, ... What is the next term?",
            53, 7, "Stretch: apply a two-part recursive rule."),
        lambda r: _t(
            "Pattern A adds 4 each step from 3; pattern B doubles each step from 3. "
            "What is the 4th term of the faster-growing pattern?",
            24, 7, "Stretch: compare arithmetic and doubling growth."),
    ],
    "NBT.DECIMALS": [
        lambda r: _t(
            f"{(a := r.randrange(3, 8))}.{(d := r.choice([25, 50, 75]))} × {(m := r.randrange(4, 9))} = ?",
            round((a + d / 100) * m, 2), 6, "Stretch: decimal times a whole number."),
        lambda r: _t(
            "0.36 ÷ 0.04 = ?",
            9, 7, "Stretch: divide a decimal by a decimal."),
    ],
    "NF.ADD_SUBTRACT": [
        lambda r: _t(
            "5/6 - 1/4 = ? Write as a fraction.", "7/12", 6,
            "Stretch: subtract with unlike denominators."),
        lambda r: _t(
            "2/3 + 3/4 + 1/6 = ? Write as a fraction.", "19/12", 7,
            "Stretch: three addends, three denominators."),
    ],
    "NF.MULTIPLY_DIVIDE": [
        lambda r: _t(
            "3/4 × 8/9 = ? Write as a fraction.", "2/3", 6,
            "Stretch: cross-cancel before multiplying."),
        lambda r: _t(
            "7/8 ÷ (1/4) = ? Write as a fraction.", "7/2", 6,
            "Stretch: divide by a fraction."),
    ],
    "MD.CONVERSION": [
        lambda r: _t(
            f"{(a := r.randrange(2, 7))}.5 kg is how many grams?",
            a * 1000 + 500, 5, "Stretch: decimal kilograms to grams."),
        lambda r: _t(
            f"A trip takes {(h := r.randrange(2, 4))} hours {(m := r.choice([15, 30, 45]))} minutes. "
            "How many minutes is that?",
            h * 60 + m, 5, "Stretch: hours and minutes to minutes."),
    ],
    "MD.VOLUME": [
        lambda r: _t(
            f"A box is {(a := r.randrange(3, 6))} cm × {(b := r.randrange(2, 5))} cm × "
            f"{(c := r.randrange(4, 8))} cm. What is its volume in cubic cm?",
            a * b * c, 5, "Stretch: volume from three dimensions."),
        lambda r: _t(
            f"A cube has volume {(e := r.choice([4, 5, 6])) ** 3} cubic cm. What is its edge "
            "length in cm?",
            e, 7, "Stretch: cube root from a known cube."),
    ],
    "G.COORDINATES": [
        lambda r: _t(
            f"The point ({(x := r.randrange(2, 6))}, {(y := r.randrange(5, 9))}) moves right "
            f"{(dx := r.randrange(3, 6))} and down {(dy := r.randrange(2, 4))}. What are its new "
            "coordinates? Write like (7, 5).",
            f"({x + dx}, {y - dy})", 6, "Stretch: translate a point."),
        lambda r: _t(
            f"How far apart are the points ({(x1 := r.randrange(1, 4))}, {(y := r.randrange(3, 8))}) "
            f"and ({x1 + (dx := r.randrange(4, 9))}, {y})?",
            dx, 6, "Stretch: horizontal distance on the plane."),
    ],
    "G.SHAPES": [
        lambda r: _t(
            "A quadrilateral has both pairs of opposite sides equal but no right angles. "
            "What is it called?",
            "parallelogram", 6, "Stretch: classify by attribute combinations."),
        lambda r: _t(
            f"A square has side {(s := r.randrange(4, 8))} cm and a rectangle is {s} cm by "
            f"{s + (w := r.randrange(3, 6))} cm. How many more cm of perimeter does "
            "the rectangle have?",
            2 * w, 6, "Stretch: compare perimeters of related figures."),
    ],
}


BANDS = {
    "grade1": GRADE1,
    "grade2": GRADE2,
    "grade3": GRADE3,
    "grade4": GRADE4,
    "grade5": GRADE5,
}


def main() -> None:
    for path in sorted(PACK_DIR.glob("*.json")):
        stem = path.stem  # e.g. dc-grade1-ccss-2024_25
        jur, grade, *_ = stem.split("-")
        band = BANDS.get(grade)
        if band is None or "md-grade3" in stem:
            continue
        pack = json.loads(path.read_text())
        prefix = f"{jur}{grade[-1]}"
        rng = random.Random(stem)  # deterministic per pack
        changed = False
        for skill in pack["skills"]:
            suffix = skill["code"].split(".", 1)[1]
            templates = band.get(suffix)
            if not templates:
                raise ValueError(f"No templates for {skill['code']} in {stem}")
            have = [p for p in skill["problems"] if "extension" in p.get("modes", [])]
            if len(have) >= len(templates):
                continue
            family = skill["problem_families"][0]
            slug = suffix.lower().replace(".", "-").replace("_", "-")
            for i, make in enumerate(templates, start=1):
                prob = make(rng)
                prob["key"] = f"{prefix}-{slug}-extension-{i:02d}"
                prob["family"] = family
                prob["modes"] = ["extension"]
                skill["problems"].append(prob)
                changed = True
        if changed:
            path.write_text(json.dumps(pack, indent=2) + "\n")
            print(f"{stem}: added extension problems")
        else:
            print(f"{stem}: already covered")


if __name__ == "__main__":
    main()
