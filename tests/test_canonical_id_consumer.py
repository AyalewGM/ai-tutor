"""Canonical-ID consumer regression tests (Issue #286, Deliverable A).

These tests verify that Devin-owned code paths read and write canonical and
problem-family identifiers correctly, and that historical learner evidence
remains keyed to curriculum-local skill IDs when canonical mappings are added
or changed.

Dependencies:
- Curriculum/Architecture Issue #282 owns the alias-to-canonical bridge.
- Devin Issue #286 owns consumer-side integration and these tests.
- Do not edit Curriculum/MVE/Muse-owned files from these tests.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.canonical_problem_adapter import materialize_problem
from app.canonical_problem_families import FAMILIES, LearningMode, generate
from app.canonical_problem_registry import register_problem_families
from app.curriculum_models import (
    CanonicalSkill,
    CurriculumSkillMapping,
    ProblemFamily,
)
from app.effectiveness_models import (
    AssessmentItem,
    AssessmentPhase,
    AssessmentStatus,
    LearningAssessment,
)
from app.models import (
    Attempt,
    Curriculum,
    MasteryEvent,
    Problem,
    Skill,
    SkillStatus,
    Student,
    StudentSkill,
    TutorSession,
)
from app.services.learning_assessment import (
    check_assessment_guard,
    record_item_response,
)
from app.services.learning_effectiveness import compute_effectiveness
from app.services.mastery import update_mastery
from app.services.parent_intelligence import (
    ParentSkillEvidence,
    classify_parent_skill_progress,
)
from app.services.problem_selection import _last_attempt_family
from scripts.map_canonical_curricula import map_existing_skills


@pytest.fixture
def db():
    """PostgreSQL session via SessionLocal; rolls back at the end.

    Uses the same local dev database as the integration tests. All test data
    is created inside a transaction and discarded after each test.
    """
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _make_curriculum_and_skill(
    db: Session,
    *,
    curriculum_code: str = "TEST-CURR",
    version: str = "1",
    skill_code: str = "TEST.SKILL.ADD",
    skill_name: str = "Test Addition",
) -> tuple[Curriculum, Skill]:
    """Create a minimal curriculum and one curriculum-local skill."""
    curriculum = Curriculum(
        id=uuid.uuid4(),
        code=curriculum_code,
        name="Test Curriculum",
        jurisdiction="TEST",
        version=version,
    )
    db.add(curriculum)
    db.flush()

    skill = Skill(
        id=uuid.uuid4(),
        curriculum_id=curriculum.id,
        code=skill_code,
        name=skill_name,
    )
    db.add(skill)
    db.flush()
    return curriculum, skill


def _make_student(
    db: Session,
    *,
    curriculum_id: uuid.UUID,
    first_name: str = "Synthetic",
) -> Student:
    student = Student(
        id=uuid.uuid4(),
        curriculum_id=curriculum_id,
        first_name=first_name,
        grade_level="3",
        school_system="TEST",
    )
    db.add(student)
    db.flush()
    return student


def _make_canonical_skill(
    db: Session,
    code: str = "MATH.NS.ADDITION",
) -> CanonicalSkill:
    canonical = CanonicalSkill(
        id=uuid.uuid4(),
        code=code,
        name=code.rsplit(".", 1)[-1].replace("_", " ").title(),
        subject="MATHEMATICS",
    )
    db.add(canonical)
    db.flush()
    return canonical


def _link_skill_to_canonical(
    db: Session,
    *,
    skill_id: uuid.UUID,
    canonical_skill_id: uuid.UUID,
) -> CurriculumSkillMapping:
    mapping = CurriculumSkillMapping(
        id=uuid.uuid4(),
        skill_id=skill_id,
        canonical_skill_id=canonical_skill_id,
        mapping_type="EQUIVALENT",
        provenance_json={"basis": "test harness"},
    )
    db.add(mapping)
    db.flush()
    return mapping


# -----------------------------------------------------------------------------
# Historical mastery preservation
# -----------------------------------------------------------------------------


class TestHistoricalMasteryPreservation:
    """Learner evidence must remain keyed to curriculum-local skill IDs."""

    def test_mastery_row_preserved_after_canonical_mapping(self, db: Session):
        """Adding a CurriculumSkillMapping must not move or alter StudentSkill."""
        curriculum, skill = _make_curriculum_and_skill(db)
        student = _make_student(db, curriculum_id=curriculum.id)
        canonical = _make_canonical_skill(db)

        # Pre-existing mastery on the curriculum-local skill
        evidence = StudentSkill(
            student_id=student.id,
            skill_id=skill.id,
            mastery_score=Decimal("0.900"),
            confidence_score=Decimal("0.900"),
            attempt_count=5,
            correct_count=5,
            independent_attempt_count=5,
            independent_correct_count=5,
            status=SkillStatus.MASTERED,
        )
        db.add(evidence)
        db.flush()

        original_key = (student.id, skill.id)
        original_score = evidence.mastery_score

        # Now the canonical mapping is introduced (simulate bridge post-hoc)
        _link_skill_to_canonical(
            db, skill_id=skill.id, canonical_skill_id=canonical.id,
        )

        # Evidence row is unchanged and still keyed to the original skill
        after = db.get(StudentSkill, original_key)
        assert after is not None
        assert after.skill_id == skill.id
        assert after.mastery_score == original_score
        assert after.attempt_count == 5

    def test_cross_curriculum_evidence_isolated_with_shared_canonical(self, db: Session):
        """Two jurisdiction-local skills sharing a canonical skill must not share evidence."""
        canonical = _make_canonical_skill(db, code="MATH.NS.ADDITION")

        curr_a, skill_a = _make_curriculum_and_skill(
            db,
            curriculum_code="JURIS-A",
            skill_code="A.ADD.1",
            skill_name="Jurisdiction A Addition",
        )
        _curr_b, skill_b = _make_curriculum_and_skill(
            db,
            curriculum_code="JURIS-B",
            skill_code="B.ADD.1",
            skill_name="Jurisdiction B Addition",
        )

        _link_skill_to_canonical(db, skill_id=skill_a.id, canonical_skill_id=canonical.id)
        _link_skill_to_canonical(db, skill_id=skill_b.id, canonical_skill_id=canonical.id)

        student_a = _make_student(db, curriculum_id=curr_a.id, first_name="Student A")

        db.add(
            StudentSkill(
                student_id=student_a.id,
                skill_id=skill_a.id,
                mastery_score=Decimal("0.900"),
                confidence_score=Decimal("0.900"),
                attempt_count=10,
                correct_count=9,
                independent_attempt_count=10,
                independent_correct_count=9,
                status=SkillStatus.MASTERED,
            )
        )
        db.flush()

        # No evidence should exist for the equivalent skill in jurisdiction B
        assert db.get(StudentSkill, (student_a.id, skill_b.id)) is None

        # Sanity: the two curriculum skills are not the same row
        assert skill_a.id != skill_b.id
        # Both map to the same canonical skill
        mappings = db.scalars(
            select(CurriculumSkillMapping).where(
                CurriculumSkillMapping.canonical_skill_id == canonical.id,
            )
        ).all()
        assert {m.skill_id for m in mappings} == {skill_a.id, skill_b.id}

    def test_map_existing_skills_does_not_migrate_evidence(self, db: Session):
        """The existing cross-curriculum mapping script only adds mapping rows."""
        # Build a minimal curriculum that matches the script's EQUIVALENCES tuple.
        # The dev DB may already contain this curriculum; reuse it if present.
        curriculum = db.scalar(
            select(Curriculum).where(
                Curriculum.code == "MTH1W", Curriculum.version == "2021",
            )
        ) or Curriculum(
            id=uuid.uuid4(),
            code="MTH1W",
            name="Ontario Grade 9",
            jurisdiction="ON",
            version="2021",
        )
        db.add(curriculum)
        db.flush()

        skill = db.scalar(
            select(Skill).where(
                Skill.curriculum_id == curriculum.id,
                Skill.code == "MTH1W.B.NUM.INT",
            )
        ) or Skill(
            id=uuid.uuid4(),
            curriculum_id=curriculum.id,
            code="MTH1W.B.NUM.INT",
            name="Integer Operations",
        )
        db.add(skill)
        db.flush()

        student = _make_student(db, curriculum_id=curriculum.id)
        db.add(
            StudentSkill(
                student_id=student.id,
                skill_id=skill.id,
                mastery_score=Decimal("0.750"),
                confidence_score=Decimal("0.800"),
                attempt_count=3,
                correct_count=3,
                status=SkillStatus.LEARNING,
            )
        )
        db.flush()
        original_key = (student.id, skill.id)

        # Idempotent: may create 0 or 1 mappings depending on DB state.
        map_existing_skills(db)
        db.flush()

        evidence = db.get(StudentSkill, original_key)
        assert evidence is not None
        assert evidence.skill_id == skill.id
        assert evidence.mastery_score == Decimal("0.750")


# -----------------------------------------------------------------------------
# Canonical-ID read/write flows in Devin-owned code
# -----------------------------------------------------------------------------


class TestCanonicalIdReadWriteFlows:
    """Verify canonical IDs are read/written in expected places only."""

    def test_register_problem_families_creates_canonical_skills(self, db: Session):
        """`register_problem_families` writes CanonicalSkill and ProblemFamily rows."""
        register_problem_families(db)
        db.flush()

        # Registry is idempotent; on a seeded dev DB rows may already exist,
        # so assert every family generator key resolves rather than counting
        # newly created rows.
        family_codes = {
            row.code
            for row in db.scalars(select(ProblemFamily)).all()
        }
        assert set(FAMILIES.keys()) <= family_codes

        canonical_codes = db.scalars(select(CanonicalSkill.code)).all()
        assert canonical_codes
        assert all(code.startswith("MATH.") for code in canonical_codes)

    def test_materialize_problem_preserves_canonical_source_key(self, db: Session):
        """Canonical-generated problems carry the source skill and family in metadata."""
        _curriculum, skill = _make_curriculum_and_skill(db)
        # Pick the first available family to generate a real problem
        if not FAMILIES:
            pytest.skip("No canonical families defined")
        family_code = next(iter(FAMILIES.keys()))
        generated = generate(
            family_code,
            seed=f"test:{uuid.uuid4()}",
            difficulty=2,
            mode=LearningMode.DIAGNOSTIC,
        )
        problem = materialize_problem(
            db,
            generated=generated,
            curriculum_skill=skill,
        )
        assert problem.source_type == "CANONICAL_GENERATED"
        assert problem.solution is not None
        assert problem.solution.get("canonical_source_key")
        assert problem.solution.get("canonical_skill_code")
        assert problem.solution.get("family_code") == family_code

    def test_problem_family_metadata_consistent_across_source_types(self, db: Session):
        """Canonical-generated and generator problems share the 'problem_family' key."""
        _curriculum, skill = _make_curriculum_and_skill(db)

        if not FAMILIES:
            pytest.skip("No canonical families defined")
        family_code = next(iter(FAMILIES.keys()))
        generated = generate(
            family_code,
            seed=f"test:{uuid.uuid4()}",
            difficulty=2,
            mode=LearningMode.DIAGNOSTIC,
        )
        canonical_problem = materialize_problem(
            db, generated=generated, curriculum_skill=skill,
        )

        # Legacy generator uses the 'problem_family' key
        from app.services.problem_generation import generate_problem
        legacy_problem = generate_problem(
            db,
            skill_id=skill.id,
            difficulty=2,
        )
        if legacy_problem is not None:
            assert legacy_problem.solution is not None
            assert "problem_family" in legacy_problem.solution

        # Canonical adapter must expose the same key so consumers such as
        # _last_attempt_family treat both sources uniformly.
        assert canonical_problem.solution is not None
        assert canonical_problem.solution.get("family_code") == family_code
        assert canonical_problem.solution.get("problem_family") == family_code

    def test_last_attempt_family_sees_canonical_problem(self, db: Session):
        """`_last_attempt_family` resolves the family of a canonical-generated problem."""
        curriculum, skill = _make_curriculum_and_skill(db)
        student = _make_student(db, curriculum_id=curriculum.id)

        session = TutorSession(
            id=uuid.uuid4(),
            student_id=student.id,
            primary_skill_id=skill.id,
            active_skill_id=skill.id,
        )
        db.add(session)
        db.flush()

        if not FAMILIES:
            pytest.skip("No canonical families defined")
        family_code = next(iter(FAMILIES.keys()))
        generated = generate(
            family_code,
            seed=f"test:{uuid.uuid4()}",
            difficulty=2,
            mode=LearningMode.DIAGNOSTIC,
        )
        problem = materialize_problem(
            db, generated=generated, curriculum_skill=skill,
        )
        db.flush()

        db.add(
            Attempt(
                id=uuid.uuid4(),
                session_id=session.id,
                student_id=student.id,
                problem_id=problem.id,
                student_answer="x",
                is_correct=True,
                attempt_number=1,
            )
        )
        db.flush()

        assert _last_attempt_family(db, session.id) == family_code


# -----------------------------------------------------------------------------
# Assessment isolation and reconstruction
# -----------------------------------------------------------------------------


class TestAssessmentIsolationAndReconstruction:
    """Assessments must remain isolated and deterministic regardless of canonical IDs."""

    def test_assessment_guard_uses_curriculum_local_skill_id(self, db: Session):
        """Active assessment detection uses curriculum-local skill_id, not canonical."""
        curriculum, skill = _make_curriculum_and_skill(db)
        student = _make_student(db, curriculum_id=curriculum.id)

        # No active assessment
        assert check_assessment_guard(db, student_id=student.id).blocked is False

        # Create an in-progress assessment on the curriculum-local skill
        assessment = LearningAssessment(
            id=uuid.uuid4(),
            student_id=student.id,
            skill_id=skill.id,
            phase=AssessmentPhase.BASELINE,
            status=AssessmentStatus.IN_PROGRESS,
            scheduled_at=datetime.now(UTC),
            started_at=datetime.now(UTC),
        )
        db.add(assessment)
        db.flush()

        result = check_assessment_guard(db, student_id=student.id)
        assert result.blocked is True
        assert "independent assessment" in result.message.lower()

    def test_assessment_item_reconstructs_from_family_code_and_seed(self, db: Session):
        """`record_item_response` reconstructs the exact problem from stored provenance."""
        if not FAMILIES:
            pytest.skip("No canonical families defined")
        family_code = next(iter(FAMILIES.keys()))

        curriculum, skill = _make_curriculum_and_skill(db)
        student = _make_student(db, curriculum_id=curriculum.id)

        assessment = LearningAssessment(
            id=uuid.uuid4(),
            student_id=student.id,
            skill_id=skill.id,
            phase=AssessmentPhase.BASELINE,
            status=AssessmentStatus.IN_PROGRESS,
            scheduled_at=datetime.now(UTC),
            started_at=datetime.now(UTC),
        )
        db.add(assessment)
        db.flush()

        seed1 = "test:seed:1"
        problem1 = generate(
            family_code, seed=seed1, difficulty=2, mode=LearningMode.DIAGNOSTIC,
        )
        item = AssessmentItem(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            sequence_number=1,
            family_code=family_code,
            variant_id="variant-a",
            generation_seed=seed1,
            difficulty=2,
            prompt=problem1.prompt,
            canonical_answer=problem1.canonical_answer,
        )
        db.add(item)
        db.flush()

        answered = record_item_response(
            db, item=item, student_answer=problem1.canonical_answer,
        )
        assert answered.is_correct is True
        assert answered.assistance_level == 0

        # A mismatched stored canonical_answer triggers the integrity check —
        # provenance drift (e.g. after an alias rename) must not go unnoticed.
        problem2 = generate(
            family_code, seed="different:seed", difficulty=2,
            mode=LearningMode.DIAGNOSTIC,
        )
        item2 = AssessmentItem(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            sequence_number=2,
            family_code=family_code,
            variant_id="variant-a",
            generation_seed="different:seed",
            difficulty=2,
            prompt=problem2.prompt,
            # Sentinel value guaranteed to differ from the regenerated answer.
            canonical_answer=f"{problem2.canonical_answer}#mismatch",
        )
        db.add(item2)
        db.flush()
        with pytest.raises(RuntimeError, match="reconstruction mismatch"):
            record_item_response(db, item=item2, student_answer="x")

    def test_effectiveness_calculation_uses_curriculum_local_skill_id(self, db: Session):
        """Growth/retention metrics compare assessments on the same curriculum-local skill."""
        baseline = LearningAssessment(
            id=uuid.uuid4(),
            student_id=uuid.uuid4(),
            skill_id=uuid.uuid4(),
            phase=AssessmentPhase.BASELINE,
            status=AssessmentStatus.COMPLETED,
            scheduled_at=datetime.now(UTC),
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            items_total=5,
            items_answered=5,
            items_correct=2,
            score=Decimal("0.400"),
            independent_score=Decimal("0.400"),
        )
        post = LearningAssessment(
            id=uuid.uuid4(),
            student_id=baseline.student_id,
            skill_id=baseline.skill_id,
            phase=AssessmentPhase.POST_INSTRUCTION,
            status=AssessmentStatus.COMPLETED,
            scheduled_at=datetime.now(UTC),
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            items_total=5,
            items_answered=5,
            items_correct=4,
            score=Decimal("0.800"),
            independent_score=Decimal("0.800"),
        )
        metrics = compute_effectiveness(
            baseline=baseline,
            comparison=post,
            measurement_type="GROWTH",
            student_id=baseline.student_id,
            skill_id=baseline.skill_id,
        )
        assert metrics.observed_improvement == Decimal("0.400")
        assert metrics.baseline_assessment_id == baseline.id
        assert metrics.comparison_assessment_id == post.id

    def test_mastery_update_is_pure_function_no_canonical_query(self):
        """Mastery update is a deterministic math function; it does not query canonical IDs."""
        update = update_mastery(
            current_mastery=0.5,
            meaningful_attempts=3,
            correct=True,
            assistance_level=0,
            problem_difficulty=3,
            learner_level=3,
        )
        assert 0.0 <= update.mastery <= 1.0
        assert update.confidence > 0.0
        assert update.evidence > 0.0

    def test_parent_insight_uses_curriculum_local_evidence(self):
        """Parent-facing classification consumes curriculum-local evidence counts."""
        evidence = ParentSkillEvidence(
            attempt_count=5,
            independent_attempt_count=5,
            independent_correct_count=4,
            hinted_correct_count=0,
            status=SkillStatus.MASTERED,
        )
        insight = classify_parent_skill_progress(evidence)
        assert insight.learning_state == "INDEPENDENT_MASTERY"
        assert insight.assistance_signal == "NONE_OBSERVED"

    def test_attempt_records_curriculum_local_skill_id(self, db: Session):
        """An Attempt row stores the curriculum-local skill_id via its session."""
        curriculum, skill = _make_curriculum_and_skill(db)
        student = _make_student(db, curriculum_id=curriculum.id)
        session = TutorSession(
            id=uuid.uuid4(),
            student_id=student.id,
            primary_skill_id=skill.id,
            active_skill_id=skill.id,
        )
        db.add(session)
        db.flush()

        problem = Problem(
            id=uuid.uuid4(),
            primary_skill_id=skill.id,
            problem_type="TEST",
            difficulty=2,
            prompt="What is 2+2?",
            canonical_answer="4",
        )
        db.add(problem)
        db.flush()

        attempt = Attempt(
            id=uuid.uuid4(),
            session_id=session.id,
            student_id=student.id,
            problem_id=problem.id,
            student_answer="4",
            is_correct=True,
            attempt_number=1,
        )
        db.add(attempt)
        db.flush()

        # The skill is implicit via the session's curriculum-local skill ID,
        # not a canonical ID — and Attempt has no direct canonical reference.
        parent_session = db.get(TutorSession, attempt.session_id)
        assert parent_session.primary_skill_id == skill.id
        assert problem.primary_skill_id == skill.id

    def test_mastery_event_records_curriculum_local_skill(self, db: Session):
        """MasteryEvent.skill_id is the curriculum-local skill."""
        curriculum, skill = _make_curriculum_and_skill(db)
        student = _make_student(db, curriculum_id=curriculum.id)

        event = MasteryEvent(
            id=uuid.uuid4(),
            student_id=student.id,
            skill_id=skill.id,
            previous_score=Decimal("0.500"),
            new_score=Decimal("0.700"),
            previous_confidence=Decimal("0.600"),
            new_confidence=Decimal("0.700"),
            reason="test",
        )
        db.add(event)
        db.flush()

        assert event.skill_id == skill.id


# -----------------------------------------------------------------------------
# Fail-closed placeholders for Deliverable B
# -----------------------------------------------------------------------------


class TestDeliverableBFailClosedPlaceholders:
    """Consumers that will use the #282 mapping contract must fail closed now."""

    def test_no_implicit_alias_to_canonical_resolution_exists(self):
        """There is currently no consumer code that auto-resolves a pack alias."""
        # This test documents the gap. When Deliverable B lands, a resolution
        # module should exist and be exercised here; until then its absence is
        # the safe default.
        import importlib.util
        assert (
            importlib.util.find_spec("app.services.canonical_id_resolution")
            is None
        )

    def test_unknown_canonical_skill_code_fails_lookup(self, db: Session):
        """Looking up a non-existent CanonicalSkill returns None."""
        missing = db.scalar(
            select(CanonicalSkill).where(CanonicalSkill.code == "MATH.UNKNOWN.SKILL")
        )
        assert missing is None
