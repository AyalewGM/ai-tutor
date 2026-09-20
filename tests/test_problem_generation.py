import random
import re
import uuid
from fractions import Fraction

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import (
    Attempt,
    Curriculum,
    Problem,
    Skill,
    Student,
    TutorSession,
    TutorState,
)
from app.services.evaluation import evaluate_problem
from app.services.problem_generation import GENERATORS
from app.services.problem_selection import select_next_problem


def test_all_generators_produce_evaluable_answers() -> None:
    rng = random.Random(7)
    for problem_type, generate in GENERATORS.items():
        for difficulty in (1, 3, 5):
            generated = generate(rng, difficulty)
            assert generated.problem_type == problem_type
            result = evaluate_problem(
                generated.prompt, generated.canonical_answer, generated.canonical_answer
            )
            assert result.correct


def test_solve_equation_answers_satisfy_the_equation() -> None:
    rng = random.Random(11)
    for difficulty in (1, 2, 3, 4, 5, 8):
        generated = GENERATORS["SOLVE_EQUATION"](rng, difficulty)
        x = int(generated.canonical_answer.split("=")[1])
        lhs, rhs = generated.prompt.split(" = ")
        lhs = lhs.replace(" ", "")
        # LHS is one of: "x+b", "ax", "ax+b", "a(x+b)" / "a(x-b)"
        match = re.fullmatch(r"(\d*)(\(?x\)?)([+-]\d+)?\)?", lhs)
        assert match is not None, lhs
        a = int(match.group(1) or 1)
        b = int(match.group(3) or 0)
        value = a * (x + b) if "(" in lhs else a * x + b
        assert value == int(rhs)


def test_fraction_addition_answers_are_reduced() -> None:
    rng = random.Random(3)
    for _ in range(20):
        generated = GENERATORS["FRACTION_OPERATIONS"](rng, 2)
        n1, d1, n2, d2 = map(int, re.findall(r"\d+", generated.prompt))
        expected = Fraction(n1, d1) + Fraction(n2, d2)
        if expected.denominator == 1:
            assert generated.canonical_answer == str(expected.numerator)
        else:
            assert generated.canonical_answer == f"{expected.numerator}/{expected.denominator}"


def test_generated_problems_do_not_repeat_within_session() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id, Skill.code == "M8.ALG.INVERSE"
            )
        )
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Generation QA",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        session = TutorSession(student_id=student.id, primary_skill_id=skill.id)
        db.add(session)
        db.flush()

        seen_ids = set()
        for _ in range(4):
            problem = select_next_problem(
                db,
                skill_id=skill.id,
                current_problem_id=None,
                current_difficulty=2,
                state=TutorState.INDEPENDENT_PRACTICE,
                session_id=session.id,
            )
            assert problem is not None
            assert problem.id not in seen_ids
            seen_ids.add(problem.id)
            db.add(
                Attempt(
                    session_id=session.id,
                    student_id=student.id,
                    problem_id=problem.id,
                    student_answer="x=1",
                    is_correct=False,
                )
            )
            db.flush()

        generated = db.scalars(
            select(Problem).where(
                Problem.id.in_(seen_ids), Problem.source_type == "GENERATED"
            )
        ).all()
        assert len(generated) >= 1  # pool (2 curated) exhausted → generation kicked in
        db.rollback()


def test_skill_without_generator_falls_back_to_repeats() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = Skill(
            curriculum_id=curriculum.id,
            code=f"GEN.UNSUPPORTED.{uuid.uuid4().hex[:8]}",
            name="Unsupported type",
            description="problem_type with no generator",
            difficulty_level=1,
        )
        db.add(skill)
        db.flush()
        problem = Problem(
            primary_skill_id=skill.id,
            problem_type="UNSUPPORTED_TYPE",
            difficulty=1,
            prompt="What is 1 + 1?",
            canonical_answer="2",
        )
        db.add(problem)
        db.flush()
        student = Student(
            curriculum_id=curriculum.id,
            first_name="Fallback QA",
            grade_level="8",
            school_system="MCPS",
        )
        db.add(student)
        db.flush()
        session = TutorSession(student_id=student.id, primary_skill_id=skill.id)
        db.add(session)
        db.flush()
        db.add(
            Attempt(
                session_id=session.id,
                student_id=student.id,
                problem_id=problem.id,
                student_answer="2",
                is_correct=True,
            )
        )
        db.flush()

        selected = select_next_problem(
            db,
            skill_id=skill.id,
            current_problem_id=None,
            current_difficulty=1,
            state=TutorState.INDEPENDENT_PRACTICE,
            session_id=session.id,
        )
        assert selected is not None and selected.id == problem.id
        db.rollback()
