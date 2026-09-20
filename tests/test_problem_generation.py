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
from app.services.problem_generation import (
    GENERATORS,
    content_readiness,
    generate_problem,
    regenerate_variant,
)
from app.services.problem_selection import select_next_problem
from tests.fixtures import TEST_PROVENANCE


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


def test_fraction_answers_are_reduced() -> None:
    rng = random.Random(3)
    for _ in range(20):
        generated = GENERATORS["FRACTION_OPERATIONS"](rng, 2)
        n1, d1, n2, d2 = map(int, re.findall(r"\d+", generated.prompt))
        if " - " in generated.prompt:
            expected = Fraction(n1, d1) - Fraction(n2, d2)
            assert generated.family == "fraction/subtract"
        else:
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


def test_regenerate_variant_produces_fresh_same_template_problem() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id, Skill.code == "M8.ALG.INVERSE"
            )
        )
        source = Problem(
            primary_skill_id=skill.id,
            problem_type="SOLVE_EQUATION",
            difficulty=2,
            prompt="Solve 4x = 20.",
            canonical_answer="x=5",
            solution={"generated": True, "generator": "SOLVE_EQUATION", "difficulty": 2},
            source_type="GENERATED",
        )
        db.add(source)
        db.flush()

        variant = regenerate_variant(db, source_problem=source, rng=random.Random(5))
        assert variant is not None
        assert variant.id != source.id
        assert variant.source_type == "GENERATED"
        assert variant.difficulty == 2
        assert variant.problem_type == "SOLVE_EQUATION"
        assert variant.canonical_answer is not None
        db.rollback()


def test_regenerate_variant_rejects_curated_problem() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MCPS_MATH_8"))
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id, Skill.code == "M8.ALG.INVERSE"
            )
        )
        curated = Problem(
            primary_skill_id=skill.id,
            problem_type="SOLVE_EQUATION",
            difficulty=1,
            prompt="Solve 5x = 30.",
            canonical_answer="x=6",
            solution={"answer": "x=6", "provenance": TEST_PROVENANCE},
            source_type="CURATED",
        )
        db.add(curated)
        db.flush()
        assert regenerate_variant(db, source_problem=curated) is None
        db.rollback()


class _StubContextualizer:
    def __init__(self, narrative):
        self.narrative = narrative

    def contextualize(self, *, template, parameters, canonical_answer):
        return self.narrative


def test_word_problem_uses_contextualizer_narrative(monkeypatch) -> None:
    from app.services import problem_contextualizer

    monkeypatch.setattr(
        problem_contextualizer,
        "contextualizer",
        _StubContextualizer("A jacket costs $80. What is 20% of 80?"),
    )
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MTH1W.F.FIN.PCT",
            )
        )
        problem = generate_problem(
            db, skill_id=skill.id, difficulty=1, problem_type="WORD_PROBLEM",
            rng=random.Random(2),
        )
        assert problem is not None
        assert problem.prompt == "A jacket costs $80. What is 20% of 80?"
        assert problem.canonical_answer  # still code-computed, not model output
        db.rollback()
    monkeypatch.setattr(problem_contextualizer, "contextualizer", None)


def test_gateway_contextualizer_rejects_unfaithful_numbers(monkeypatch) -> None:
    import httpx

    from app.services.problem_contextualizer import GatewayContextualizer

    def fake_post(url, *, json, timeout):
        request = httpx.Request("POST", url)
        return httpx.Response(
            200, request=request,
            json={"prompt": "A taxi charges 5 dollars plus 2 per mile."},
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    adapter = GatewayContextualizer("http://gateway", 1.0)
    # Narrative drops the required 13% and $80 — must be rejected.
    assert (
        adapter.contextualize(
            template="percent_of",
            parameters={"percent": 13, "amount": 80},
            canonical_answer="10.40",
        )
        is None
    )


def test_gateway_contextualizer_accepts_faithful_narrative(monkeypatch) -> None:
    import httpx

    from app.services.problem_contextualizer import GatewayContextualizer

    def fake_post(url, *, json, timeout):
        request = httpx.Request("POST", url)
        return httpx.Response(
            200, request=request,
            json={"prompt": "A $80 purchase has 13% tax. What is the tax?"},
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    adapter = GatewayContextualizer("http://gateway", 1.0)
    assert adapter.contextualize(
        template="percent_of",
        parameters={"percent": 13, "amount": 80},
        canonical_answer="10.40",
    ) == "A $80 purchase has 13% tax. What is the tax?"


def test_gateway_contextualizer_returns_none_on_failure(monkeypatch) -> None:
    import httpx

    from app.services.problem_contextualizer import GatewayContextualizer

    def fail_post(*args, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "post", fail_post)
    adapter = GatewayContextualizer("http://gateway", 1.0)
    assert adapter.contextualize(
        template="unit_rate",
        parameters={"distance": 120, "hours": 3},
        canonical_answer="40",
    ) is None


def test_generated_problems_carry_family_and_parameter_identity() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MTH1W.B.NUM.INT",
            )
        )
        problem = generate_problem(
            db, skill_id=skill.id, difficulty=2, rng=random.Random(4)
        )
        assert problem is not None
        metadata = problem.solution
        assert metadata["generated"] is True
        assert metadata["problem_family"] in {"INTEGER_OPERATIONS", "INTEGER_COMPARE"}
        assert isinstance(metadata["parameters"], dict)
        assert metadata["parameters"]
        db.rollback()


def test_generated_fingerprints_do_not_collide() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MTH1W.B.NUM.INT",
            )
        )
        rng = random.Random(9)
        fingerprints = set()
        for _ in range(6):
            problem = generate_problem(
                db, skill_id=skill.id, difficulty=3, rng=rng
            )
            assert problem is not None
            key = (
                problem.solution["problem_family"],
                tuple(sorted(problem.solution["parameters"].items())),
            )
            assert key not in fingerprints
            fingerprints.add(key)
        db.rollback()


def test_avoid_family_rotates_to_a_different_family() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MTH1W.B.NUM.INT",
            )
        )
        problem = generate_problem(
            db,
            skill_id=skill.id,
            difficulty=2,
            problem_type="INTEGER_OPERATIONS",
            family="INTEGER_OPERATIONS",
            rng=random.Random(1),
        )
        assert problem.solution["problem_family"] == "INTEGER_OPERATIONS"
        rotated = generate_problem(
            db,
            skill_id=skill.id,
            difficulty=2,
            avoid_family="INTEGER_OPERATIONS",
            rng=random.Random(1),
        )
        assert rotated is not None
        assert rotated.solution["problem_family"] == "INTEGER_COMPARE"
        db.rollback()


def test_regenerate_variant_preserves_family() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MTH1W.B.NUM.INT",
            )
        )
        source = generate_problem(
            db,
            skill_id=skill.id,
            difficulty=2,
            problem_type="INTEGER_COMPARE",
            family="INTEGER_COMPARE",
            rng=random.Random(6),
        )
        variant = regenerate_variant(
            db, source_problem=source, rng=random.Random(6)
        )
        assert variant is not None
        assert variant.solution["problem_family"] == "INTEGER_COMPARE"
        assert variant.solution["parameters"] != source.solution["parameters"]
        db.rollback()


def test_content_readiness_reports_families_and_gate() -> None:
    with SessionLocal() as db:
        curriculum = db.scalar(select(Curriculum).where(Curriculum.code == "MTH1W"))
        int_skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MTH1W.B.NUM.INT",
            )
        )
        report = content_readiness(db, skill_id=int_skill.id)
        assert report.ready is True
        assert {"INTEGER_OPERATIONS", "INTEGER_COMPARE"} <= set(report.families)

        thin = Skill(
            curriculum_id=curriculum.id,
            code=f"GEN.THIN.{uuid.uuid4().hex[:8]}",
            name="Thin content skill",
            difficulty_level=1,
        )
        db.add(thin)
        db.flush()
        empty = content_readiness(db, skill_id=thin.id)
        assert empty.ready is False
        assert empty.problem_count == 0

        db.add(
            Problem(
                primary_skill_id=thin.id,
                problem_type="UNSUPPORTED_ONLY",
                difficulty=1,
                prompt="Only one family.",
                canonical_answer="x",
                solution={"answer": "x", "provenance": TEST_PROVENANCE},
            )
        )
        db.flush()
        single_family = content_readiness(db, skill_id=thin.id)
        assert single_family.ready is False
        assert single_family.families == ("UNSUPPORTED_ONLY",)
        db.rollback()
