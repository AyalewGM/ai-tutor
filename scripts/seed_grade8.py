"""Seed the MCPS Grade 8 transformations skill onto the existing
MCPS_MATH_8 curriculum (created by seed_sprint1)."""

from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping, EducationAuthority
from app.models import Curriculum, Misconception, Problem, Skill

CURRICULUM_CODE = "MCPS_MATH_8"


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
        curriculum = db.scalar(
            select(Curriculum).where(Curriculum.code == CURRICULUM_CODE)
        )
        if curriculum is None:
            authority = db.scalar(
                select(EducationAuthority).where(EducationAuthority.code == "MCPS")
            )
            if authority is None:
                raise RuntimeError(
                    "MCPS education authority must be seeded before Grade 8 content"
                )
            curriculum = Curriculum(
                code=CURRICULUM_CODE,
                name="MCPS Grade 8 Mathematics",
                jurisdiction="Montgomery County, Maryland",
                grade_level="8",
                authority_id=authority.id,
                version="1",
                source_uri="https://www.montgomeryschoolsmd.org/curriculum/math/ms/",
            )
            db.add(curriculum)
            db.flush()

        transforms = _skill(
            db, curriculum, "M8.G.TRANS",
            "Transformations on the Coordinate Plane",
            "Translate, reflect, rotate, and dilate points and figures on "
            "the coordinate plane, and identify the transformation that "
            "maps a figure onto its image.",
            3,
        )
        similarity = _skill(
            db, curriculum, "M8.G.SIM",
            "Similarity and Congruence",
            "Use scale factors and proportional sides on similar figures, "
            "reason about how scaling affects perimeter and area, and "
            "classify pairs of figures as congruent, similar, or neither.",
            3,
        )
        statistics = _skill(
            db, curriculum, "M8.SP.STAT",
            "Scatterplots and Bivariate Data",
            "Read associations on scatterplots, identify outliers, use a "
            "line of best fit to make predictions, choose the equation "
            "that best fits a data set, and distinguish association from "
            "causation.",
            3,
        )
        pythagorean = _skill(
            db, curriculum, "M8.G.PYTH",
            "The Pythagorean Theorem",
            "Find missing side lengths of right triangles, apply the "
            "converse to test for right triangles, and use the theorem to "
            "find distances between points on the coordinate plane.",
            3,
        )

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
            transforms,
            "TR_001",
            "Rotation applied with wrong direction or coordinate order",
            "The learner turns the point the wrong way, swaps the "
            "coordinates without adjusting signs, or rotates 90° when the "
            "prompt asks for 180°.",
            "Track one coordinate at a time: 90° clockwise sends (x, y) "
            "to (y, −x). Mark the starting quadrant and check which "
            "quadrant the image should land in.",
        )
        _misconception(
            transforms,
            "TR_002",
            "Reflection negates the wrong coordinate",
            "The learner negates the coordinate the axis keeps — for "
            "example answering (2, 3) when reflecting (−2, 3) over the "
            "x-axis.",
            "A reflection keeps the coordinate that matches the axis: "
            "over the x-axis, x stays and y flips; over the y-axis, y "
            "stays and x flips.",
        )
        _misconception(
            transforms,
            "TR_003",
            "Translation applied with the wrong direction",
            "The learner moves left instead of right or down instead of "
            "up on one or both axes.",
            "Read the units in order: 'right' adds to x, 'left' subtracts, "
            "'up' adds to y, 'down' subtracts. Move the point on the grid "
            "one unit at a time.",
        )
        _misconception(
            transforms,
            "TR_004",
            "Transformation misidentified",
            "The learner names the wrong motion — calling a reflection a "
            "rotation, or missing the direction of a translation.",
            "Check whether the figure flipped (reflection), turned "
            "(rotation), or slid (translation). Then match the axis, "
            "angle, or vector.",
        )
        _misconception(
            transforms,
            "TR_005",
            "Dilation applied partially",
            "The learner scales only one coordinate, or adds the scale "
            "factor instead of multiplying both coordinates by it.",
            "A dilation centred at the origin multiplies every coordinate "
            "by the scale factor: (x, y) → (kx, ky). Check that both "
            "coordinates changed by the factor.",
        )
        _misconception(
            similarity,
            "SIM_001",
            "Missing side found by adding instead of scaling",
            "The learner adds the difference between a pair of "
            "corresponding sides instead of multiplying every side by the "
            "scale factor.",
            "Similar figures keep ratios, not differences: find the scale "
            "factor from a known pair, then multiply the unknown side by "
            "the same factor.",
        )
        _misconception(
            similarity,
            "SIM_002",
            "Scale factor used where k² is needed, or vice versa",
            "The learner reports the area ratio as k instead of k², or "
            "the perimeter ratio as k² instead of k.",
            "Lengths scale by k, perimeters by k, and areas by k²: each "
            "dimension in the measure adds one power of the scale factor.",
        )
        _misconception(
            similarity,
            "SIM_003",
            "Scale factor inverted",
            "The learner divides larger by smaller in the wrong direction, "
            "reporting the reciprocal of the intended scale factor.",
            "Check the direction the question asks: 'smaller to larger' "
            "means image ÷ preimage. A scale factor above 1 grows the "
            "figure; below 1 shrinks it.",
        )
        _misconception(
            similarity,
            "SIM_004",
            "Congruent, similar, and unrelated figures confused",
            "The learner calls same-shape-different-size figures "
            "congruent, or treats unequal figures as similar.",
            "Congruent means same shape and same size; similar means same "
            "shape at any size. Check the angle measures and whether all "
            "sides scale by one factor.",
        )
        _misconception(
            statistics,
            "STAT_001",
            "Association direction or strength misread",
            "The learner calls a positive association negative, reads a "
            "scattered cloud as a trend, or reports no relationship where "
            "one is visible.",
            "Trace the cloud left to right: rising points mean a positive "
            "association, falling points negative, and a shapeless spread "
            "means no association.",
        )
        _misconception(
            statistics,
            "STAT_002",
            "Association treated as causation",
            "The learner concludes that one variable causes the other "
            "just because the scatterplot shows a strong association.",
            "Association means the variables move together — a hidden "
            "third factor may drive both. Ice cream sales and swimming "
            "are both driven by hot weather.",
        )
        _misconception(
            statistics,
            "STAT_003",
            "Outlier confused with the largest value",
            "The learner picks the point with the biggest coordinates "
            "instead of the point that breaks the pattern the other "
            "points follow.",
            "An outlier is a point that does not fit the trend — not the "
            "largest point. Sketch the pattern first, then look for the "
            "point that falls away from it.",
        )
        _misconception(
            statistics,
            "STAT_004",
            "Intercept dropped when using the line of best fit",
            "The learner computes slope times x and forgets to add the "
            "intercept, or subtracts it instead of adding.",
            "A prediction uses the whole equation: multiply x by the "
            "slope, then add the y-intercept before answering.",
        )
        _misconception(
            statistics,
            "STAT_005",
            "Slope and intercept of the best-fit line swapped",
            "The learner chooses an equation with the slope and "
            "y-intercept exchanged, or one whose intercept does not match "
            "where the trend crosses the y-axis.",
            "The intercept is where the trend line would hit the y-axis; "
            "the slope is how fast the cloud rises. Check each candidate "
            "against both.",
        )
        _misconception(
            statistics,
            "STAT_006",
            "Joint, marginal, and conditional frequencies confused",
            "The learner divides by the grand total when a group total "
            "is needed, or reports a joint cell where a conditional "
            "fraction was asked.",
            "Find the group named after 'of the' or 'who' — that group "
            "is the denominator. The joint cell in the matching row and "
            "column is the numerator.",
        )
        _misconception(
            statistics,
            "STAT_007",
            "Cell or total misread in a two-way table",
            "The learner reports a different cell or a marginal total "
            "instead of the value asked, or sums only part of the table "
            "for a total.",
            "Trace the row label and column label to the cell they "
            "cross. A total adds every cell in its row, column, or the "
            "whole table.",
        )
        _misconception(
            statistics,
            "STAT_008",
            "Association in a two-way table misjudged",
            "The learner claims there is no association when the "
            "conditional rates clearly differ, or claims one when the "
            "rates are the same.",
            "Compare the fraction of 'yes' outcomes in each row: a big "
            "gap between the rows signals an association; matching "
            "fractions signal none.",
        )
        _misconception(
            pythagorean,
            "PYTH_001",
            "Sum of squares never square-rooted",
            "The learner computes a² + b² (or c² − a²) and reports it as "
            "the side length, forgetting to take the square root.",
            "The theorem gives the square of the side, not the side: "
            "after squaring and adding, take the square root to finish.",
        )
        _misconception(
            pythagorean,
            "PYTH_002",
            "Sides added or squares miscombined",
            "The learner adds the legs directly for a hypotenuse, adds "
            "the hypotenuse and leg for a missing leg, or adds |dx| + "
            "|dy| for a distance.",
            "Square first, then add or subtract, then root: c = √(a² + "
            "b²) and a leg is √(c² − a²).",
        )
        _misconception(
            pythagorean,
            "PYTH_003",
            "Converse misapplied when testing for a right triangle",
            "The learner checks the wrong condition — comparing a + b "
            "to c or the triangle inequality instead of a² + b² = c².",
            "A triangle is right exactly when the two shorter sides "
            "squared add to the longest side squared.",
        )

        problems = [
            (
                transforms, 1,
                "Point P is shown on the grid. Translate it 3 units right and 2 units up. What are the coordinates of P'?",
                "(5, 5)", "TRANSFORMATION", "FREE_TEXT",
                {"tier": "translate", "x": 2, "y": 3, "dx": 3, "dy": 2,
                 "preimage": [[2, 3]], "labels": ["P"]},
                None,
            ),
            (
                transforms, 2,
                "Point P is shown on the grid. Reflect it over the x-axis. What are the coordinates of P'?",
                "(3, -4)", "TRANSFORMATION", "FREE_TEXT",
                {"tier": "reflect", "x": 3, "y": 4, "axis": "x-axis",
                 "preimage": [[3, 4]], "labels": ["P"]},
                None,
            ),
            (
                transforms, 3,
                "Point P is shown on the grid. Rotate it 90° clockwise about the origin. What are the coordinates of P'?",
                "(4, 2)", "TRANSFORMATION", "FREE_TEXT",
                {"tier": "rotate", "x": -2, "y": 4, "direction": "90° clockwise",
                 "preimage": [[-2, 4]], "labels": ["P"]},
                None,
            ),
            (
                transforms, 4,
                "Triangle ABC is mapped onto triangle A'B'C' as shown. Which transformation maps the preimage onto the image?",
                "b", "TRANSFORMATION", "MULTIPLE_CHOICE",
                {"tier": "identify", "motion": "reflect_x",
                 "preimage": [[1, 2], [4, 2], [2, 5]],
                 "image": [[1, -2], [4, -2], [2, -5]],
                 "labels": ["A", "B", "C"],
                 "image_labels": ["A'", "B'", "C'"]},
                [
                    {"id": "a", "text": "a translation 4 units down", "misconception_code": "TR_004"},
                    {"id": "b", "text": "a reflection over the x-axis"},
                    {"id": "c", "text": "a rotation of 180° about the origin", "misconception_code": "TR_004"},
                    {"id": "d", "text": "a reflection over the y-axis", "misconception_code": "TR_004"},
                ],
            ),
        ]
        for skill, difficulty, prompt, answer, ptype, answer_kind, parameters, choices in problems:
            _problem(
                db, skill, difficulty, prompt, answer, ptype,
                answer_kind=answer_kind, parameters=parameters, choices=choices,
            )

        # Similarity items — proportional figure pairs with edge labels.
        sim_problems = [
            (
                similarity, 1,
                "The two triangles shown are similar. What is the scale factor from the smaller triangle to the larger one?",
                "a", "SIMILARITY", "MULTIPLE_CHOICE",
                {"tier": "scale_factor", "preimage": [[0, 0], [4, 0], [1.33, 3.33]],
                 "image": [[0, 0], [8, 0], [2.67, 6.67]],
                 "pre_edge_labels": ["4", None, None],
                 "image_edge_labels": ["8", None, None],
                 "k_num": 2, "k_den": 1},
                [
                    {"id": "a", "text": "2"},
                    {"id": "b", "text": "1/2", "misconception_code": "SIM_003"},
                    {"id": "c", "text": "4"},
                    {"id": "d", "text": "3"},
                ],
            ),
            (
                similarity, 2,
                "The two triangles shown are similar. What is the length of the side labeled ?",
                "c", "SIMILARITY", "MULTIPLE_CHOICE",
                {"tier": "missing_side", "preimage": [[0, 0], [4, 0], [1.33, 3.33]],
                 "image": [[0, 0], [8, 0], [2.67, 6.67]],
                 "pre_edge_labels": ["4", "5", None],
                 "image_edge_labels": ["8", "?", None]},
                [
                    {"id": "a", "text": "9", "misconception_code": "SIM_001"},
                    {"id": "b", "text": "8"},
                    {"id": "c", "text": "10"},
                    {"id": "d", "text": "12"},
                ],
            ),
            (
                similarity, 3,
                "The smaller triangle is scaled by a factor of 3 to produce the larger one shown. By what factor does its area change?",
                "b", "SIMILARITY", "MULTIPLE_CHOICE",
                {"tier": "perimeter_area_effect", "measure": "area", "k": 3,
                 "preimage": [[0, 0], [3, 0], [1, 2.5]],
                 "image": [[0, 0], [9, 0], [3, 7.5]]},
                [
                    {"id": "a", "text": "multiplied by 3", "misconception_code": "SIM_002"},
                    {"id": "b", "text": "multiplied by 9"},
                    {"id": "c", "text": "multiplied by 6"},
                    {"id": "d", "text": "stays the same"},
                ],
            ),
            (
                similarity, 4,
                "How are the two triangles shown related?",
                "a", "SIMILARITY", "MULTIPLE_CHOICE",
                {"tier": "classify",
                 "preimage": [[0, 0], [3, 0], [1, 2.5]],
                 "image": [[0, 0], [6, 0], [2, 5]]},
                [
                    {"id": "a", "text": "similar but not congruent"},
                    {"id": "b", "text": "congruent", "misconception_code": "SIM_004"},
                    {"id": "c", "text": "neither congruent nor similar", "misconception_code": "SIM_004"},
                    {"id": "d", "text": "similar only when rotated", "misconception_code": "SIM_004"},
                ],
            ),
        ]
        for skill, difficulty, prompt, answer, ptype, answer_kind, parameters, choices in sim_problems:
            _problem(
                db, skill, difficulty, prompt, answer, ptype,
                answer_kind=answer_kind, parameters=parameters, choices=choices,
            )

        # Statistics items — scatterplots on a shared 0..10 grid.
        stat_problems = [
            (
                statistics, 1,
                "What type of association does the scatterplot show between the two variables?",
                "a", "STATISTICS", "MULTIPLE_CHOICE",
                {"tier": "association", "points": [[1, 3], [2, 3], [3, 5], [4, 6], [5, 6], [6, 7], [7, 8], [8, 9]]},
                [
                    {"id": "a", "text": "a positive association"},
                    {"id": "b", "text": "a negative association", "misconception_code": "STAT_001"},
                    {"id": "c", "text": "no association", "misconception_code": "STAT_001"},
                    {"id": "d", "text": "a curved (nonlinear) association", "misconception_code": "STAT_001"},
                ],
            ),
            (
                statistics, 2,
                "Which point is the outlier in the scatterplot?",
                "d", "STATISTICS", "MULTIPLE_CHOICE",
                {"tier": "outlier", "points": [[1, 2], [2, 4], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [5, 1]]},
                [
                    {"id": "a", "text": "(7, 8)", "misconception_code": "STAT_003"},
                    {"id": "b", "text": "(4, 5)"},
                    {"id": "c", "text": "(6, 7)"},
                    {"id": "d", "text": "(5, 1)"},
                ],
            ),
            (
                statistics, 3,
                "The scatterplot shows data with the line of best fit y = 2x + 1. Use it to predict y when x = 3.",
                "7", "STATISTICS", "INTEGER",
                {"tier": "predict",
                 "points": [[1, 3], [2, 5], [3, 6], [4, 9], [5, 10]],
                 "fit": {"m_num": 2, "m_den": 1, "i_num": 1, "i_den": 1}},
                None,
            ),
            (
                statistics, 4,
                "A scatterplot shows a strong positive association between ice cream sales and the number of swimmers at local pools. Which conclusion is most reasonable?",
                "b", "STATISTICS", "MULTIPLE_CHOICE",
                {"tier": "correlation_causation",
                 "x_var": "ice cream sales",
                 "y_var": "the number of swimmers at local pools",
                 "direction": "positive"},
                [
                    {"id": "a", "text": "Changes in ice cream sales directly cause changes in the number of swimmers", "misconception_code": "STAT_002"},
                    {"id": "b", "text": "The variables are associated, but one does not necessarily cause the other"},
                    {"id": "c", "text": "Changes in the number of swimmers directly cause changes in ice cream sales", "misconception_code": "STAT_002"},
                    {"id": "d", "text": "There is no relationship between the two variables", "misconception_code": "STAT_001"},
                ],
            ),
        ]
        for skill, difficulty, prompt, answer, ptype, answer_kind, parameters, choices in stat_problems:
            _problem(
                db, skill, difficulty, prompt, answer, ptype,
                answer_kind=answer_kind, parameters=parameters, choices=choices,
            )

        # Two-way frequency table items — complete the 8.SP strand.
        freq_problems = [
            (
                statistics, 2,
                "The table shows the results of a survey of students. What fraction of the students surveyed play a sport and take an art class?",
                "b", "FREQUENCY_TABLE", "MULTIPLE_CHOICE",
                {"tier": "joint_frequency",
                 "rows": ["Plays a sport", "Does not play a sport"],
                 "cols": ["Takes an art class", "Does not take an art class"],
                 "cells": [[12, 8], [6, 14]],
                 "show_totals": True, "ri": 0, "ci": 0},
                [
                    {"id": "a", "text": "3/5", "misconception_code": "STAT_006"},
                    {"id": "b", "text": "3/10"},
                    {"id": "c", "text": "2/3", "misconception_code": "STAT_006"},
                    {"id": "d", "text": "3/20", "misconception_code": "STAT_007"},
                ],
            ),
            (
                statistics, 3,
                "The table shows the results of a survey of students. Of the students who play a sport, what fraction also take an art class?",
                "c", "FREQUENCY_TABLE", "MULTIPLE_CHOICE",
                {"tier": "conditional_frequency",
                 "rows": ["Plays a sport", "Does not play a sport"],
                 "cols": ["Takes an art class", "Does not take an art class"],
                 "cells": [[12, 8], [9, 11]],
                 "show_totals": True, "axis": "row", "index": 0, "target": 0},
                [
                    {"id": "a", "text": "3/10", "misconception_code": "STAT_006"},
                    {"id": "b", "text": "9/20", "misconception_code": "STAT_006"},
                    {"id": "c", "text": "3/5"},
                    {"id": "d", "text": "2/5", "misconception_code": "STAT_006"},
                ],
            ),
            (
                statistics, 4,
                "The table shows the results of a survey of students. Is there evidence of an association between riding the bus and eating school lunch?",
                "a", "FREQUENCY_TABLE", "MULTIPLE_CHOICE",
                {"tier": "association",
                 "rows": ["Rides the bus", "Does not ride the bus"],
                 "cols": ["Eats school lunch", "Brings lunch from home"],
                 "cells": [[18, 6], [8, 20]],
                 "show_totals": True, "associated": True},
                [
                    {"id": "a", "text": "Yes — students who ride the bus are more likely to eat school lunch"},
                    {"id": "b", "text": "Yes — students who ride the bus are less likely to eat school lunch", "misconception_code": "STAT_008"},
                    {"id": "c", "text": "No — the proportions are about the same for both groups", "misconception_code": "STAT_008"},
                    {"id": "d", "text": "The table does not give enough information to decide"},
                ],
            ),
        ]
        for skill, difficulty, prompt, answer, ptype, answer_kind, parameters, choices in freq_problems:
            _problem(
                db, skill, difficulty, prompt, answer, ptype,
                answer_kind=answer_kind, parameters=parameters, choices=choices,
            )

        # Pythagorean items — rendered right triangles and grid segments.
        pyth_problems = [
            (
                pythagorean, 1,
                "The right triangle has legs of length 3 and 4. What is the length of the hypotenuse?",
                "5", "PYTHAGOREAN", "INTEGER",
                {"tier": "hypotenuse", "a": 3, "b": 4, "c": 5},
                None,
            ),
            (
                pythagorean, 2,
                "The right triangle has a hypotenuse of length 13 and one leg of length 5. What is the length of the other leg?",
                "12", "PYTHAGOREAN", "INTEGER",
                {"tier": "leg", "a": 5, "b": 12, "c": 13},
                None,
            ),
            (
                pythagorean, 3,
                "A triangle has sides of length 4, 5, and 6. Could it be a right triangle?",
                "b", "PYTHAGOREAN", "MULTIPLE_CHOICE",
                {"tier": "converse", "sides": [4, 5, 6]},
                [
                    {"id": "a", "text": "Yes, because 4² + 5² = 6²", "misconception_code": "PYTH_003"},
                    {"id": "b", "text": "No, because 4² + 5² ≠ 6²"},
                    {"id": "c", "text": "Yes, because 4 + 5 > 6", "misconception_code": "PYTH_003"},
                    {"id": "d", "text": "There is not enough information to decide"},
                ],
            ),
            (
                pythagorean, 4,
                "What is the distance between point A(1, 1) and point B(5, 4)?",
                "5", "PYTHAGOREAN", "INTEGER",
                {"tier": "distance", "points": [[1, 1], [5, 4]]},
                None,
            ),
        ]
        for skill, difficulty, prompt, answer, ptype, answer_kind, parameters, choices in pyth_problems:
            _problem(
                db, skill, difficulty, prompt, answer, ptype,
                answer_kind=answer_kind, parameters=parameters, choices=choices,
            )

        db.commit()
        print(f"Grade 8 seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
