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

        db.commit()
        print(f"Grade 8 seed complete. Curriculum={curriculum.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
