from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping, EducationAuthority
from app.models import Curriculum, Misconception, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "MCPS_MATH_7"


def _skill(
    db,
    curriculum: Curriculum,
    code: str,
    name: str,
    description: str,
    level: int,
) -> Skill:
    skill = db.scalar(
        select(Skill).where(Skill.curriculum_id == curriculum.id, Skill.code == code)
    )
    if skill is None:
        skill = Skill(
            curriculum_id=curriculum.id,
            code=code,
            name=name,
            description=description,
            difficulty_level=level,
            mastery_threshold=Decimal("0.850"),
        )
        db.add(skill)
        db.flush()
    canonical_code = "MATH." + code.split(".", 1)[1]
    canonical = db.scalar(select(CanonicalSkill).where(CanonicalSkill.code == canonical_code))
    if canonical is None:
        canonical = CanonicalSkill(
            code=canonical_code,
            name=name,
            description=description,
            subject="MATHEMATICS",
        )
        db.add(canonical)
        db.flush()
    mapping = db.scalar(
        select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id == skill.id)
    )
    if mapping is None:
        db.add(
            CurriculumSkillMapping(
                canonical_skill_id=canonical.id,
                skill_id=skill.id,
                mapping_type="EQUIVALENT",
                provenance_json={
                    "basis": "AI Tutor authored curriculum mapping",
                    "curriculum_code": curriculum.code,
                    "curriculum_version": curriculum.version,
                },
            )
        )
    return skill


def _prerequisite(db, skill: Skill, prerequisite: Skill) -> None:
    if skill.curriculum_id != prerequisite.curriculum_id:
        raise ValueError("Prerequisite edges cannot cross curriculum boundaries")
    key = {"skill_id": skill.id, "prerequisite_skill_id": prerequisite.id}
    if db.get(SkillPrerequisite, key) is None:
        db.add(SkillPrerequisite(**key, importance_weight=Decimal("1.000")))


def _problem(
    db,
    skill: Skill,
    difficulty: int,
    prompt: str,
    answer: str,
    problem_type: str,
    *,
    answer_kind: str = "FREE_TEXT",
    parameters: dict | None = None,
    choices: list | None = None,
) -> None:
    provenance = {
        "origin": "AUTHORED",
        "author": "AI Tutor curriculum team",
        "license": "proprietary",
        "source_uri": "https://www.montgomeryschoolsmd.org/curriculum/math/ms/",
    }
    existing = db.scalar(
        select(Problem).where(
            Problem.primary_skill_id == skill.id,
            Problem.prompt == prompt,
        )
    )
    solution = {"answer": answer, "provenance": provenance}
    if parameters is not None:
        solution["problem_family"] = problem_type
        solution["parameters"] = parameters
    if existing is None:
        db.add(
            Problem(
                primary_skill_id=skill.id,
                problem_type=problem_type,
                difficulty=difficulty,
                prompt=prompt,
                canonical_answer=answer,
                answer_kind=answer_kind,
                choices=choices,
                solution=solution,
                source_type="CURATED",
            )
        )
    elif parameters is not None and "parameters" not in (existing.solution or {}):
        existing.solution = {
            **(existing.solution or {}),
            "problem_family": problem_type,
            "parameters": parameters,
        }
    elif "provenance" not in (existing.solution or {}):
        existing.solution = {**(existing.solution or {}), "provenance": provenance}


def seed() -> None:
    db = SessionLocal()
    try:
        authority = db.scalar(
            select(EducationAuthority).where(EducationAuthority.code == "MCPS")
        )
        if authority is None:
            raise RuntimeError("MCPS education authority must be seeded before Grade 7 content")

        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        if curriculum is None:
            curriculum = Curriculum(
                code=CURRICULUM_CODE,
                name="MCPS Grade 7 Mathematics",
                jurisdiction="Montgomery County, Maryland",
                grade_level="7",
                authority_id=authority.id,
                version="1",
                source_uri="https://www.montgomeryschoolsmd.org/curriculum/math/ms/",
            )
            db.add(curriculum)
            db.flush()

        proportional = _skill(
            db,
            curriculum,
            "M7.RP.PROP",
            "Proportional Relationships",
            "Recognize and reason about proportional relationships.",
            1,
        )
        percent = _skill(
            db,
            curriculum,
            "M7.RP.PERCENT",
            "Percent Problems",
            "Use proportional reasoning to solve percent problems.",
            2,
        )
        expressions = _skill(
            db,
            curriculum,
            "M7.EE.EXPR",
            "Equivalent Expressions",
            "Use properties of operations to generate equivalent expressions.",
            2,
        )
        equations = _skill(
            db,
            curriculum,
            "M7.EE.EQUATION",
            "Equations and Inequalities",
            "Solve contextual equations and inequalities using rational numbers.",
            3,
        )

        _prerequisite(db, percent, proportional)
        _prerequisite(db, equations, expressions)

        # Fine-grained subskills gated by their strand anchors.
        prop_rate = _skill(
            db, curriculum, "M7.RP.PROP.RATE",
            "Unit Rates",
            "Compute a unit rate from a proportional relationship.",
            1,
        )
        pct_of = _skill(
            db, curriculum, "M7.RP.PERCENT.OF",
            "Percent of a Quantity",
            "Find a percent of a number using decimal conversion.",
            2,
        )
        expr_dist = _skill(
            db, curriculum, "M7.EE.EXPR.DIST",
            "Distribution in Expressions",
            "Apply the distributive property to expand expressions.",
            2,
        )
        expr_combine = _skill(
            db, curriculum, "M7.EE.EXPR.COMBINE",
            "Combining Like Terms",
            "Combine like terms to write equivalent simplified expressions.",
            2,
        )
        eq_one = _skill(
            db, curriculum, "M7.EE.EQUATION.ONE",
            "One-Step Equations",
            "Solve x + a = b and ax = b using a single inverse operation.",
            3,
        )
        eq_two = _skill(
            db, curriculum, "M7.EE.EQUATION.TWO",
            "Two-Step Equations",
            "Solve ax + b = c by undoing operations in reverse order.",
            3,
        )
        solids = _skill(
            db, curriculum, "M7.G.SOLID",
            "Volume and Surface Area of Solids",
            "Compute volumes and surface areas of prisms, pyramids, cylinders, "
            "and cones, and reason about faces, edges, and vertices.",
            3,
        )
        plane_geo = _skill(
            db, curriculum, "M7.G.GEO",
            "Angles, Triangles, and Circles",
            "Use complementary, supplementary, vertical, and linear-pair angle "
            "relationships, apply the triangle angle sum, and compute circle "
            "area and circumference.",
            3,
        )
        probability = _skill(
            db, curriculum, "M7.SP.PROB",
            "Probability of Simple and Compound Events",
            "Classify the likelihood of chance events, find probabilities of "
            "simple events and their complements, count sample-space "
            "outcomes, and combine events for two spins or 'or' outcomes.",
            3,
        )

        _prerequisite(db, prop_rate, proportional)
        _prerequisite(db, pct_of, percent)
        _prerequisite(db, expr_dist, expressions)
        _prerequisite(db, expr_combine, expr_dist)
        _prerequisite(db, eq_one, equations)
        _prerequisite(db, eq_two, eq_one)

        def _misconception(skill, code, name, description, strategy):
            if db.scalar(
                select(Misconception).where(
                    Misconception.skill_id == skill.id,
                    Misconception.code == code,
                )
            ) is None:
                db.add(
                    Misconception(
                        skill_id=skill.id,
                        code=code,
                        name=name,
                        description=description,
                        remediation_strategy=strategy,
                    )
                )

        _misconception(
            percent,
            "FIN_001",
            "Percent treated as a whole-number amount",
            "The learner uses the percent as a dollar amount or forgets to "
            "divide by 100.",
            "Convert the percent to a decimal by dividing by 100 before "
            "multiplying by the amount.",
        )
        _misconception(
            expressions,
            "DIST_001",
            "Partial distribution",
            "The learner multiplies the outside factor by only one term "
            "inside parentheses.",
            "Represent the outside factor as multiplying each term separately "
            "before simplifying.",
        )
        _misconception(
            expressions,
            "ALG_001",
            "Unlike terms combined",
            "The learner merges constants into the variable term instead of "
            "combining like terms separately.",
            "Group variable terms with variable terms and constants with "
            "constants before simplifying.",
        )
        _misconception(
            expressions,
            "ALG_002",
            "Constant sign dropped",
            "The learner combines constants but drops the sign of a negative "
            "term.",
            "Attach each constant's sign to the term and combine signed "
            "constants carefully.",
        )
        _misconception(
            equations,
            "EQ_003",
            "Multiplies instead of dividing",
            "The learner multiplies both sides by the coefficient instead of "
            "dividing to isolate the variable.",
            "Undo multiplication with division: divide both sides by the "
            "coefficient of the variable.",
        )
        _misconception(
            pct_of,
            "FIN_001",
            "Percent treated as a whole-number amount",
            "The learner uses the percent as a dollar amount or forgets to "
            "divide by 100.",
            "Convert the percent to a decimal by dividing by 100 before "
            "multiplying by the amount.",
        )
        _misconception(
            expr_dist,
            "DIST_001",
            "Partial distribution",
            "The learner multiplies the outside factor by only one term "
            "inside parentheses.",
            "Represent the outside factor as multiplying each term separately "
            "before simplifying.",
        )
        _misconception(
            expr_combine,
            "ALG_001",
            "Unlike terms combined",
            "The learner merges constants into the variable term instead of "
            "combining like terms separately.",
            "Group variable terms with variable terms and constants with "
            "constants before simplifying.",
        )
        _misconception(
            eq_one,
            "EQ_003",
            "Multiplies instead of dividing",
            "The learner multiplies both sides by the coefficient instead of "
            "dividing to isolate the variable.",
            "Undo multiplication with division: divide both sides by the "
            "coefficient of the variable.",
        )
        _misconception(
            eq_two,
            "EQ_001",
            "Inverse operation in wrong direction",
            "The learner applies the inverse operation in the wrong direction, "
            "for example adding the constant instead of subtracting it.",
            "Identify the operation applied to the variable and undo it with "
            "the opposite operation on both sides.",
        )
        _misconception(
            eq_two,
            "ARITH_001",
            "Arithmetic slip in isolation",
            "The learner applies the correct inverse operation but computes "
            "the result on the other side incorrectly.",
            "After applying an inverse operation, recompute the unaffected "
            "side carefully before moving on.",
        )
        _misconception(
            eq_one,
            "EQ_004",
            "Coefficient treated as addend",
            "The learner subtracts the coefficient from the constant as if "
            "3x meant x + 3 instead of 3 times x.",
            "Name the operation binding the variable: a coefficient multiplies "
            "the variable, so undo it with division.",
        )
        _misconception(
            expr_dist,
            "DIST_002",
            "Distribution sign error",
            "The learner distributes the factor but flips the sign of the "
            "constant term.",
            "Rewrite the product as a signed multiplication for each term, "
            "tracking the sign of both factors before simplifying.",
        )
        _misconception(
            eq_two,
            "EQ_002",
            "Skipped or missequenced inverse step",
            "The learner undoes one operation but skips or reorders the other "
            "inverse step, such as forgetting to divide by the coefficient.",
            "Undo operations in reverse order: remove the added constant first, "
            "then divide by the coefficient.",
        )
        _misconception(
            solids,
            "SOLID_001",
            "One-third factor dropped",
            "The learner computes a pyramid or cone volume as base area times "
            "height, forgetting the one-third factor for pointed solids.",
            "A pyramid or cone fills exactly one third of the prism or "
            "cylinder with the same base and height: V = (1/3)Bh.",
        )
        _misconception(
            solids,
            "SOLID_002",
            "Surface area confused with volume",
            "The learner answers a surface-area question with a volume "
            "formula, or vice versa — for example giving lwh as the surface "
            "area.",
            "Surface area is the total area of all faces in square units; "
            "volume is the space inside in cubic units. Name which one the "
            "question wants first.",
        )
        _misconception(
            solids,
            "SOLID_003",
            "Faces, edges, or vertices miscounted",
            "The learner undercounts faces or edges by missing the hidden "
            "ones, or confuses faces with vertices or edges.",
            "Count systematically: bases and lateral faces separately for "
            "faces; base edges and lateral edges separately for edges.",
        )
        _misconception(
            plane_geo,
            "GEO_001",
            "Area and circumference formulas swapped",
            "The learner answers a circle-area question with 2πr, or a "
            "circumference question with πr².",
            "Area covers the inside of the circle: πr². Circumference is the "
            "distance around: 2πr. Say 'inside or around?' first.",
        )
        _misconception(
            plane_geo,
            "GEO_002",
            "Complementary and supplementary confused",
            "The learner subtracts from 90° when the angles are "
            "supplementary, or from 180° when they are complementary.",
            "Check which pair it is: complementary angles make a right "
            "angle (sum 90°); supplementary angles make a straight line "
            "(sum 180°).",
        )
        _misconception(
            plane_geo,
            "GEO_003",
            "Triangle angle sum uses the wrong total",
            "The learner subtracts the two known angles from 360° or 90° "
            "instead of 180°.",
            "The three angles of any triangle add to 180°, not 360°. "
            "Subtract the two known angles from 180°.",
        )
        _misconception(
            plane_geo,
            "GEO_004",
            "Vertical angles and linear pairs confused",
            "The learner treats vertical angles as supplementary, or "
            "answers a linear-pair question with the equal vertical angle.",
            "Vertical angles sit opposite each other and are equal. A "
            "linear pair sits side by side on a line and sums to 180°.",
        )
        _misconception(
            plane_geo,
            "GEO_005",
            "Composite figure mishandles the cut-out",
            "The learner adds the missing notch to the area, or ignores it "
            "and answers the full bounding rectangle.",
            "The L-shape is the big rectangle with a corner removed: "
            "compute W×H, then subtract the notch a×b.",
        )
        _misconception(
            plane_geo,
            "GEO_006",
            "Radius and diameter confused",
            "The learner uses the diameter where the radius is needed "
            "(giving 4r²π for area) or halves a needed factor.",
            "Check which measurement the diagram gives: r is centre-to-edge "
            "and d is edge-to-edge, with d = 2r.",
        )
        _misconception(
            plane_geo,
            "GEO_007",
            "Angle classification read from the wrong side of 90°",
            "The learner calls an acute angle obtuse or vice versa — "
            "reading the boundary at 90° backwards.",
            "Acute angles are smaller than a right angle (under 90°); "
            "obtuse angles are bigger (between 90° and 180°). Compare the "
            "opening to a square corner first.",
        )
        _misconception(
            probability,
            "PROB_001",
            "Favourable or total outcomes miscounted",
            "The learner divides by the wrong count — favourable over "
            "unfavourable, total over favourable, or only one colour "
            "when two were asked.",
            "Probability is favourable outcomes over total outcomes: "
            "count every section or marble for the denominator, and only "
            "the ones the event names for the numerator.",
        )
        _misconception(
            probability,
            "PROB_002",
            "Compound outcomes added or multiplied incorrectly",
            "The learner adds two probabilities where they should be "
            "multiplied, multiplies where they should be added, or "
            "counts sample-space outcomes by adding the two event sizes.",
            "'And' across independent events multiplies; 'or' across "
            "mutually exclusive events adds; the sample space size is "
            "the product of the two event sizes.",
        )
        _misconception(
            probability,
            "PROB_003",
            "Complement handled incorrectly",
            "The learner answers the probability of the event itself "
            "when the question asks for 'not', or computes the "
            "complement of the wrong event.",
            "P(not A) = 1 − P(A): subtract the favourable count from "
            "the total first, then form the fraction.",
        )
        _misconception(
            probability,
            "PROB_004",
            "Likelihood of a chance event misclassified",
            "The learner calls an impossible event unlikely, a likely "
            "one unlikely, or confuses equally likely with likely.",
            "Compare the count with half the total: zero is impossible, "
            "below half is unlikely, exactly half is equally likely, "
            "above half is likely, and all is certain.",
        )

        problems = [
            (
                proportional,
                1,
                "A recipe uses 2 cups of flour for 3 batches. How many cups are needed for 6 batches?",
                "4",
                "WORD_PROBLEM",
            ),
            (
                proportional,
                2,
                "A car travels 150 miles in 3 hours at a constant rate. What is the unit rate in miles per hour?",
                "50",
                "WORD_PROBLEM",
            ),
            (percent, 1, "What is 20% of 60?", "12", "WORD_PROBLEM"),
            (
                percent,
                2,
                "A $40 item is discounted by 25%. What is the discount amount?",
                "10",
                "WORD_PROBLEM",
            ),
            (expressions, 1, "Simplify 3(x + 2).", "3x+6", "SIMPLIFY_EXPRESSION"),
            (
                expressions,
                2,
                "Simplify 2x + 5 + 3x - 1.",
                "5x+4",
                "SIMPLIFY_EXPRESSION",
            ),
            (equations, 1, "Solve 4x = 20", "x=5", "SOLVE_EQUATION"),
            (equations, 2, "x + 7 = 19", "x=12", "SOLVE_EQUATION"),
            (equations, 3, "3x - 4 = 17", "x=7", "SOLVE_EQUATION"),
            (prop_rate, 1, "A car travels 120 miles in 2 hours at a constant rate. What is the unit rate?", "60", "WORD_PROBLEM"),
            (prop_rate, 2, "A recipe uses 4 cups of flour for 2 batches. How many cups for 5 batches?", "10", "WORD_PROBLEM"),
            (pct_of, 1, "What is 15% of 80?", "12", "WORD_PROBLEM"),
            (pct_of, 2, "What is 35% of 200?", "70", "WORD_PROBLEM"),
            (expr_dist, 1, "Simplify 4(x + 5).", "4x+20", "SIMPLIFY_EXPRESSION"),
            (expr_dist, 2, "Simplify 6(x - 2).", "6x-12", "SIMPLIFY_EXPRESSION"),
            (expr_combine, 2, "Simplify 3x + 4 + 2x - 1.", "5x+3", "SIMPLIFY_EXPRESSION"),
            (expr_combine, 3, "Simplify 7x - 3 - 4x + 6.", "3x+3", "SIMPLIFY_EXPRESSION"),
            (eq_one, 1, "Solve x + 8 = 17.", "x=9", "SOLVE_EQUATION"),
            (eq_one, 1, "Solve 5x = 35.", "x=7", "SOLVE_EQUATION"),
            (eq_two, 2, "Solve 2x + 6 = 18.", "x=6", "SOLVE_EQUATION"),
            (eq_two, 3, "Solve 4x - 3 = 25.", "x=7", "SOLVE_EQUATION"),
        ]
        for skill, difficulty, prompt, answer, problem_type in problems:
            _problem(db, skill, difficulty, prompt, answer, problem_type)

        # Solid items — parameters feed the isometric solid visual.
        solid_problems = [
            (
                solids, 2,
                "The rectangular prism shown has length 4, width 3, and height 5. What is its volume in cubic units?",
                "60", "SOLID_VOLUME", "INTEGER",
                {"tier": "prism_volume", "solid": "rectangular_prism", "l": 4, "w": 3, "h": 5},
                None,
            ),
            (
                solids, 3,
                "The square pyramid shown has a base with side length 3 and height 6. What is its volume in cubic units?",
                "18", "SOLID_VOLUME", "INTEGER",
                {"tier": "pyramid_volume", "solid": "square_pyramid", "b": 3, "h": 6},
                None,
            ),
            (
                solids, 4,
                "The cone shown has radius 3 and height 6. Which expression gives its volume?", "a",
                "SOLID_VOLUME", "MULTIPLE_CHOICE",
                {"tier": "cone_volume", "solid": "cone", "r": 3, "h": 6},
                [
                    {"id": "a", "text": "18π"},
                    {"id": "b", "text": "54π", "misconception_code": "SOLID_001"},
                    {"id": "c", "text": "36π", "misconception_code": "SOLID_002"},
                    {"id": "d", "text": "20π"},
                ],
            ),
        ]
        for skill, difficulty, prompt, answer, ptype, answer_kind, parameters, choices in solid_problems:
            _problem(
                db, skill, difficulty, prompt, answer, ptype,
                answer_kind=answer_kind, parameters=parameters, choices=choices,
            )

        # Plane-geometry items — parameters feed the dedicated diagrams.
        geo_problems = [
            (
                plane_geo, 1,
                "The two angles shown are complementary. What is the measure of the missing angle?",
                "55", "GEOMETRY_2D", "INTEGER",
                {"tier": "complementary", "angle": 35},
                None,
            ),
            (
                plane_geo, 2,
                "The two angles shown are supplementary. What is the measure of the missing angle?",
                "110", "GEOMETRY_2D", "INTEGER",
                {"tier": "supplementary", "angle": 70},
                None,
            ),
            (
                plane_geo, 3,
                "What is the measure of the triangle's third angle, labeled ?",
                "75", "GEOMETRY_2D", "INTEGER",
                {"tier": "triangle_angle", "a": 45, "b": 60},
                None,
            ),
            (
                plane_geo, 4,
                "The circle shown has radius 3. Which expression gives its area?",
                "a", "GEOMETRY_2D", "MULTIPLE_CHOICE",
                {"tier": "circle_area", "r": 3},
                [
                    {"id": "a", "text": "9π"},
                    {"id": "b", "text": "6π", "misconception_code": "GEO_001"},
                    {"id": "c", "text": "36π", "misconception_code": "GEO_006"},
                    {"id": "d", "text": "18π"},
                ],
            ),
        ]
        for skill, difficulty, prompt, answer, ptype, answer_kind, parameters, choices in geo_problems:
            _problem(
                db, skill, difficulty, prompt, answer, ptype,
                answer_kind=answer_kind, parameters=parameters, choices=choices,
            )

        # Probability items — spinners and marble bags rendered for real.
        prob_problems = [
            (
                probability, 1,
                "A marble is drawn from the bag at random. How likely is it to be red?",
                "b", "PROBABILITY", "MULTIPLE_CHOICE",
                {"tier": "likelihood", "kind": "bag",
                 "marbles": ["blue", "blue", "blue", "blue", "blue", "red"],
                 "target": "red", "likelihood": "unlikely"},
                [
                    {"id": "a", "text": "impossible", "misconception_code": "PROB_004"},
                    {"id": "b", "text": "unlikely"},
                    {"id": "c", "text": "likely", "misconception_code": "PROB_004"},
                    {"id": "d", "text": "equally likely (50-50)", "misconception_code": "PROB_004"},
                ],
            ),
            (
                probability, 1,
                "The spinner shown is spun once. What is the probability that it lands on blue?",
                "a", "PROBABILITY", "MULTIPLE_CHOICE",
                {"tier": "simple", "kind": "spinner",
                 "sections": ["red", "blue", "green", "yellow"],
                 "target": "blue"},
                [
                    {"id": "a", "text": "1/4"},
                    {"id": "b", "text": "1/3", "misconception_code": "PROB_001"},
                    {"id": "c", "text": "3/4", "misconception_code": "PROB_003"},
                    {"id": "d", "text": "1/2"},
                ],
            ),
            (
                probability, 3,
                "The spinner shown is spun twice. What is the probability that it lands on green both times?",
                "b", "PROBABILITY", "MULTIPLE_CHOICE",
                {"tier": "compound_twice", "kind": "spinner",
                 "sections": ["red", "blue", "green", "yellow"],
                 "target": "green"},
                [
                    {"id": "a", "text": "1/2", "misconception_code": "PROB_002"},
                    {"id": "b", "text": "1/16"},
                    {"id": "c", "text": "1/8", "misconception_code": "PROB_002"},
                    {"id": "d", "text": "1/4"},
                ],
            ),
            (
                probability, 3,
                "A marble is drawn from the bag at random. What is the probability that it is red or blue?",
                "a", "PROBABILITY", "MULTIPLE_CHOICE",
                {"tier": "compound_or", "kind": "bag",
                 "marbles": ["red", "red", "red", "blue", "blue", "green", "green", "green"],
                 "target": "red", "target_b": "blue"},
                [
                    {"id": "a", "text": "5/8"},
                    {"id": "b", "text": "3/32", "misconception_code": "PROB_002"},
                    {"id": "c", "text": "3/8", "misconception_code": "PROB_001"},
                    {"id": "d", "text": "1/4", "misconception_code": "PROB_001"},
                ],
            ),
        ]
        for skill, difficulty, prompt, answer, ptype, answer_kind, parameters, choices in prob_problems:
            _problem(
                db, skill, difficulty, prompt, answer, ptype,
                answer_kind=answer_kind, parameters=parameters, choices=choices,
            )

        db.commit()
        print(f"Grade 7 seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
