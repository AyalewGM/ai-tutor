from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping, EducationAuthority
from app.models import Curriculum, Misconception, Problem, Skill, SkillPrerequisite

CURRICULUM_CODE = "MCPS_MATH_6"
MSDE_SOURCE = "https://marylandpublicschools.org/about/Pages/DCAA/Math/revised-standards.aspx"
MCPS_OVERLAY = "https://www.montgomeryschoolsmd.org/curriculum/math/ms/"


def _skill(db, curriculum, code, name, description, level, canonical_code):
    skill = db.scalar(select(Skill).where(Skill.curriculum_id == curriculum.id, Skill.code == code))
    if skill is None:
        skill = Skill(curriculum_id=curriculum.id, code=code, name=name, description=description,
                      difficulty_level=level, mastery_threshold=Decimal("0.850"))
        db.add(skill)
        db.flush()
    canonical = db.scalar(select(CanonicalSkill).where(CanonicalSkill.code == canonical_code))
    if canonical is None:
        canonical = CanonicalSkill(code=canonical_code, name=name, description=description, subject="MATHEMATICS")
        db.add(canonical)
        db.flush()
    mapping = db.scalar(select(CurriculumSkillMapping).where(CurriculumSkillMapping.skill_id == skill.id))
    if mapping is None:
        db.add(CurriculumSkillMapping(canonical_skill_id=canonical.id, skill_id=skill.id,
            mapping_type="EQUIVALENT", provenance_json={"basis": "AI Tutor reviewed standards mapping",
            "standards_authority": "Maryland State Department of Education", "standards_source": MSDE_SOURCE,
            "local_overlay": MCPS_OVERLAY, "curriculum_code": curriculum.code, "curriculum_version": curriculum.version}))
        db.flush()
    return skill


def _edge(db, skill, prerequisite):
    if skill.curriculum_id != prerequisite.curriculum_id:
        raise ValueError("Prerequisite edges cannot cross curriculum boundaries")
    key = {"skill_id": skill.id, "prerequisite_skill_id": prerequisite.id}
    if db.get(SkillPrerequisite, key) is None:
        db.add(SkillPrerequisite(**key, importance_weight=Decimal("1.000")))


def _problem(db, skill, prompt, answer, difficulty=1, problem_type="WORD_PROBLEM",
             answer_kind="FREE_TEXT", parameters=None, choices=None):
    if db.scalar(select(Problem).where(Problem.primary_skill_id == skill.id, Problem.prompt == prompt)) is None:
        solution = {"answer": answer, "provenance": {"origin": "AUTHORED", "author": "AI Tutor curriculum team",
            "license": "proprietary", "standards_authority": "Maryland State Department of Education",
            "standards_source": MSDE_SOURCE, "local_overlay": MCPS_OVERLAY}}
        if parameters is not None:
            solution["problem_family"] = problem_type
            solution["parameters"] = parameters
        db.add(Problem(primary_skill_id=skill.id, problem_type=problem_type, difficulty=difficulty,
            prompt=prompt, canonical_answer=answer, answer_kind=answer_kind, choices=choices,
            source_type="CURATED", solution=solution))


def _misconception(db, skill, code, name, description, strategy):
    if db.scalar(select(Misconception).where(
            Misconception.skill_id == skill.id, Misconception.code == code)) is None:
        db.add(Misconception(skill_id=skill.id, code=code, name=name,
            description=description, remediation_strategy=strategy))


def seed():
    db = SessionLocal()
    try:
        authority = db.scalar(select(EducationAuthority).where(EducationAuthority.code == "MCPS"))
        if authority is None:
            raise RuntimeError("MCPS education authority must be seeded before Grade 6 content")
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == CURRICULUM_CODE))
        if curriculum is None:
            curriculum = Curriculum(code=CURRICULUM_CODE, name="MCPS Grade 6 Mathematics",
                jurisdiction="Montgomery County, Maryland", grade_level="6", authority_id=authority.id,
                version="MSDE-2026-27-v1", source_uri=MSDE_SOURCE)
            db.add(curriculum)
            db.flush()

        ratio = _skill(db, curriculum, "M6.RP.RATIO", "Ratio Reasoning", "Reason about ratios and equivalent ratios.", 1, "MATH.RP.RATIO")
        unit_rate = _skill(db, curriculum, "M6.RP.UNIT_RATE", "Unit Rates", "Find and interpret unit rates.", 2, "MATH.RP.UNIT_RATE")
        fraction = _skill(db, curriculum, "M6.NS.FRACTION", "Fraction Division", "Divide fractions in mathematical and contextual problems.", 2, "MATH.NS.FRACTION_DIVISION")
        expression = _skill(db, curriculum, "M6.EE.EXPR", "Expressions", "Write and evaluate numerical and algebraic expressions.", 2, "MATH.EE.EXPRESSIONS")
        equation = _skill(db, curriculum, "M6.EE.EQUATION", "One-variable Equations", "Represent and solve one-variable equations.", 3, "MATH.EE.ONE_VARIABLE_EQUATIONS")
        statistics = _skill(db, curriculum, "M6.SP.STAT", "Center and Spread", "Find the mean, median, mode and range of a data set, read dot plots, and choose the best measure of center when data contain an outlier.", 2, "MATH.SP.CENTER_SPREAD")
        _edge(db, unit_rate, ratio)
        _edge(db, equation, expression)
        _edge(db, statistics, fraction)

        for args in [
            (statistics, "STAT6_001", "Mean confused with median or total", "The learner reports the middle value, the sum of the data, or the spread instead of dividing the total by the count.", "The mean is the fair-share total: add every value, then divide by how many values there are."),
            (statistics, "STAT6_002", "Median read without ordering", "The learner picks the middle value of the list as printed, or misses that an even-sized set needs the mean of the two middle values.", "Order the data first, then find the middle; for an even count, average the two middle values."),
            (statistics, "STAT6_003", "Range or mode confused with center", "The learner reports the largest value or the most frequent value where the spread was asked, or treats range as the maximum.", "The range is max minus min; the mode is the most frequent value — neither describes the centre on its own."),
            (statistics, "STAT6_004", "Center measure chosen without regard to shape", "The learner chooses the mean for a data set with an outlier, or counts the wrong column on a dot plot.", "An outlier pulls the mean toward it but not the median; check a value in the middle of the data to see which measure fits."),
        ]:
            _misconception(db, *args)

        for args in [
            (ratio, "A class has 12 red markers and 8 blue markers. What is the ratio of red to blue in simplest form?", "3:2", 1),
            (ratio, "A drink uses 2 cups of juice for every 3 cups of water. How many cups of juice are needed with 9 cups of water?", "6", 2),
            (unit_rate, "A cyclist travels 36 miles in 3 hours. What is the unit rate in miles per hour?", "12", 1),
            (unit_rate, "Five notebooks cost $15. What is the cost per notebook?", "3", 2),
            (fraction, "Three-fourths of a gallon is shared equally among 3 containers. How many gallons go in each container?", "1/4", 1),
            (fraction, "How many one-half-cup servings are in 3 cups?", "6", 2),
            (expression, "Evaluate 4x + 3 when x = 5.", "23", 1),
            (expression, "Write the value of 2(6 + 4).", "20", 1),
            (equation, "A number plus 7 equals 19. What is the number?", "12", 1),
            (equation, "Four times a number is 28. What is the number?", "7", 2),
        ]:
            _problem(db, *args)

        # Statistics items — center, spread and dot-plot reading (6.SP).
        for args in [
            (statistics, "Find the mean of the data set: 4, 6, 8, 10.", "c", 1, "CENTER_SPREAD", "MULTIPLE_CHOICE",
             {"tier": "mean", "data": [4, 6, 8, 10]},
             [{"id": "a", "text": "6", "misconception_code": "STAT6_001"},
              {"id": "b", "text": "28", "misconception_code": "STAT6_001"},
              {"id": "c", "text": "7"},
              {"id": "d", "text": "6.5"}]),
            (statistics, "Find the median of the data set: 8, 3, 5.", "a", 2, "CENTER_SPREAD", "MULTIPLE_CHOICE",
             {"tier": "median", "data": [3, 5, 8], "display": [8, 3, 5]},
             [{"id": "a", "text": "5"},
              {"id": "b", "text": "3", "misconception_code": "STAT6_002"},
              {"id": "c", "text": "16/3", "misconception_code": "STAT6_001"},
              {"id": "d", "text": "8", "misconception_code": "STAT6_003"}]),
            (statistics, "The dot plot shows the number of books each student read. How many students read 4 books?",
             "b", 2, "CENTER_SPREAD", "MULTIPLE_CHOICE",
             {"tier": "dot_count", "data": [2, 3, 3, 4, 4, 4, 5, 6], "value": 4, "min": 2, "max": 6},
             [{"id": "a", "text": "4", "misconception_code": "STAT6_004"},
              {"id": "b", "text": "3"},
              {"id": "c", "text": "8"},
              {"id": "d", "text": "2"}]),
            (statistics, "The mean of 4 test scores is 10. 3 of the scores are 8, 12, 9. What is the missing score?",
             "11", 3, "CENTER_SPREAD", "INTEGER",
             {"tier": "mean_reverse", "n": 4, "mean": 10, "known": [8, 12, 9]}, None),
            (statistics, "The data set 3, 4, 5, 6, 32 contains the outlier 32. Which measure best describes the centre of the data?",
             "c", 3, "CENTER_SPREAD", "MULTIPLE_CHOICE",
             {"tier": "best_measure", "data": [3, 4, 5, 6, 32], "outlier": 32},
             [{"id": "a", "text": "The mean — it uses every value", "misconception_code": "STAT6_004"},
              {"id": "b", "text": "The range — it shows the spread", "misconception_code": "STAT6_003"},
              {"id": "c", "text": "The median — it is not pulled toward the outlier"},
              {"id": "d", "text": "The mode — it is the most frequent value", "misconception_code": "STAT6_004"}]),
        ]:
            _problem(db, args[0], args[1], args[2], difficulty=args[3],
                     problem_type=args[4], answer_kind=args[5], parameters=args[6], choices=args[7])
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
