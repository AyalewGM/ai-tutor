"""Opt-in PostgreSQL integration for read-only synthetic rational assessment.

CI runs this only against its isolated migrated and seeded PostgreSQL database.
No learner fixture changes are committed: the outer transaction rolls back.
"""
import os
import uuid

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.answer_contracts import AnswerKind
from app.content_models import ProblemContentMetadata
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping
from app.hint_models import HintEvent
from app.models import (
    Attempt,
    Curriculum,
    MasteryEvent,
    Problem,
    Skill,
    Student,
    TutorSession,
    TutorState,
    TutorTurn,
)
from app.services.atomic_rational_attempt import record_rational_attempt
from app.services.family_activation_adapter import DENIED, FamilyRegistration
from app.services.fraction_assessment_registry import AssessmentMode, ReviewedFamily
from app.services.issued_rational_evidence import ISSUANCE_VERSION
from app.services.persisted_rational_resolution import (
    TrustedAssessmentContext,
    score_persisted_rational,
)
from app.services.question_package_release import PackageReleaseEvidence

_SHA = "a" * 40
_FAMILY = "SYNTHETIC.ON.RATIONAL"
_SKILL = "MATH.EE.EQUATION.TWO"
_MAPPING = "c" * 40
_STANDARDS = "d" * 40


def _source(curriculum_code):
    flags = {
        "package_sha": _SHA, "math_accepted_sha": _SHA, "pedagogy_accepted_sha": _SHA,
        "backend_scoring_sha": _SHA, "frontend_integration_sha": _SHA,
        "muse_qa_sha": _SHA, "engineering_authorized_sha": _SHA,
        "canonical_mapping_approved": True, "exact_scorer_verified": True,
        "response_schema_verified": True, "history_preservation_verified": True,
        "runtime_activation_approved": True,
    }
    row = FamilyRegistration(
        family=ReviewedFamily(
            _FAMILY, _SKILL, _SHA, frozenset({AssessmentMode.INDEPENDENT}),
            AnswerKind.VARIABLE_VALUE,
        ),
        evidence=PackageReleaseEvidence(**flags),
        scorer_revision="b" * 40,
        source_mapping_revision=_MAPPING,
        answer_variable="x", standards_manifest_sha=_STANDARDS,
        jurisdiction_code="CA.ON", curriculum_code=curriculum_code, local_skill_code="MTH1W.C.ALG.EQ2",
        mapping_disposition="ACCEPTED", coverage_credit=True,
    )

    class SyntheticApproval:
        def approved_records(self, *, service_principal):
            if service_principal != "synthetic-test-runner":
                raise PermissionError("unknown synthetic principal")
            return (row,)

    return SyntheticApproval()


@pytest.mark.skipif(
    os.getenv("MIHUR_GATE4_ISOLATED_DB") != "1" or not os.getenv("TEST_DATABASE_URL"),
    reason="requires isolated migrated PostgreSQL with explicit opt-in",
)
def test_postgres_two_students_two_sessions_no_history_writes():
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(bind=connection) as db:
                curriculum = Curriculum(
                    code=f"SYNTHETIC_RATIONAL_{uuid.uuid4().hex[:10].upper()}",
                    name="Synthetic rational resolution curriculum", version="v1",
                    country_code="CA", region_code="ON",
                )
                db.add(curriculum)
                db.flush()
                skill = Skill(curriculum_id=curriculum.id, code="MTH1W.C.ALG.EQ2", name="Synthetic rational")
                db.add(skill)
                db.flush()
                canonical = db.scalar(
                    select(CanonicalSkill).where(CanonicalSkill.code == _SKILL)
                )
                if canonical is None:
                    canonical = CanonicalSkill(
                        code=_SKILL, name="Synthetic canonical equation skill",
                    )
                    db.add(canonical)
                    db.flush()
                db.add(CurriculumSkillMapping(
                    skill_id=skill.id, canonical_skill_id=canonical.id,
                    mapping_type="EQUIVALENT",
                    provenance_json={
                        "source_mapping_revision": _MAPPING,
                        "standards_manifest_sha": _STANDARDS,
                        "disposition": "ACCEPTED", "coverage_credit": True,
                    },
                ))
                db.flush()
                problem = Problem(
                    primary_skill_id=skill.id, problem_type="SYNTHETIC_RATIONAL",
                    difficulty=3, prompt="Solve a synthetic equation",
                    canonical_answer="x=-3/4", answer_kind="VARIABLE_VALUE",
                    solution={"variant_id": "synthetic-v1", "task_fingerprint": "synthetic-fp"},
                )
                db.add(problem)
                db.flush()
                db.add(ProblemContentMetadata(
                    problem_id=problem.id, curriculum_id=curriculum.id,
                    objective="synthetic", evaluation_type="EXACT",
                    independent_eligible=True,
                    provenance_json={
                        "family_id": _FAMILY, "content_sha": _SHA,
                        "source_mapping_revision": _MAPPING,
                        "standards_manifest_sha": _STANDARDS,
                    },
                ))
                students = []
                sessions = []
                for n in range(2):
                    student = Student(
                        curriculum_id=curriculum.id, first_name=f"SYNTHETIC-{n}",
                        grade_level="9", school_system="SYNTHETIC",
                    )
                    db.add(student)
                    db.flush()
                    sess = TutorSession(
                        student_id=student.id, primary_skill_id=skill.id,
                        curriculum_id=curriculum.id, current_state=TutorState.INDEPENDENT_PRACTICE,
                        status="ACTIVE",
                    )
                    db.add(sess)
                    db.flush()
                    students.append(student)
                    sessions.append(sess)
                    db.add(TutorTurn(
                        session_id=sess.id, problem_id=problem.id, role="SYSTEM",
                        message="Synthetic server issuance",
                        state=TutorState.INDEPENDENT_PRACTICE,
                        pedagogical_action="ISSUE_ASSESSMENT",
                        metadata_json={
                            "issuance_contract": ISSUANCE_VERSION,
                            "student_id": str(student.id), "problem_id": str(problem.id),
                            "variant_id": "synthetic-v1",
                            "task_fingerprint": "synthetic-fp",
                            "mode": "independent",
                        },
                    ))
                db.flush()

                def history_counts():
                    return tuple(db.scalar(select(func.count()).select_from(model)) for model in (
                        Attempt, MasteryEvent,
                    ))

                before = history_counts()
                source = _source(curriculum.code)
                first = TrustedAssessmentContext(
                    students[0].id, sessions[0].id, problem.id, AssessmentMode.INDEPENDENT,
                )
                args = {
                    "approval_source": source,
                    "service_principal": "synthetic-test-runner",
                }
                a = score_persisted_rational(db, context=first, submission="X=6/-8", **args)
                b = score_persisted_rational(db, context=first, submission="x=-9/12", **args)
                assert a.eligible and a.correct and not a.independent_evidence_eligible
                assert b == a
                cross_student = TrustedAssessmentContext(
                    students[1].id, sessions[0].id, problem.id, AssessmentMode.INDEPENDENT,
                )
                assert score_persisted_rational(
                    db, context=cross_student, submission="x=-3/4", **args,
                ) == DENIED
                wrong_mode = TrustedAssessmentContext(
                    students[0].id, sessions[0].id, problem.id, AssessmentMode.MASTERY,
                )
                assert score_persisted_rational(
                    db, context=wrong_mode, submission="x=-3/4", **args,
                ) == DENIED
                assisted = TrustedAssessmentContext(
                    students[0].id, sessions[0].id, problem.id,
                    AssessmentMode.INDEPENDENT, assisted=True,
                )
                decision = score_persisted_rational(
                    db, context=assisted, submission="x=-3/4", **args,
                )
                assert decision.eligible and decision.correct and not decision.independent_evidence_eligible
                # Missing release principal must deny, even for otherwise eligible item.
                assert score_persisted_rational(
                    db, context=first, submission="x=-3/4",
                    approval_source=source, service_principal="unrecognized-service",
                ) == DENIED
                # A new learner's own session must be valid but may not grant
                # mastery from scoring alone; do not touch existing attempts.
                second = TrustedAssessmentContext(
                    students[1].id, sessions[1].id, problem.id,
                    AssessmentMode.INDEPENDENT,
                )
                second_result = score_persisted_rational(
                    db, context=second, submission="x=-3/4", **args,
                )
                assert second_result.eligible and second_result.correct
                assert not second_result.independent_evidence_eligible
                # Persisted hints are stronger evidence than caller assisted=False.
                # They must deny a later independent score even with a valid
                # issuance marker and an otherwise eligible reviewed family.
                db.add(HintEvent(
                    session_id=sessions[0].id, student_id=students[0].id,
                    skill_id=skill.id, problem_id=problem.id,
                    level=1, trigger="synthetic-hint",
                ))
                db.flush()
                assert score_persisted_rational(
                    db, context=first, submission="x=-3/4", **args,
                ) == DENIED
                assert history_counts() == before
                assert not db.dirty

                # Incorrect answers must also persist as incorrect attempts,
                # without mastery writes, and remain caller-rollback-safe.
                with db.begin_nested() as nested:
                    incorrect = record_rational_attempt(
                        db, context=second, submission="x=999", **args,
                    )
                    assert incorrect.decision.eligible
                    assert incorrect.decision.correct is False
                    assert incorrect.decision.independent_evidence_eligible is False
                    assert incorrect.attempt_id is not None
                    stored = db.get(Attempt, incorrect.attempt_id)
                    assert stored.is_correct is False
                    assert stored.student_id == students[1].id
                    assert stored.assistance_level == 0
                    assert history_counts()[0] == before[0] + 1
                    assert history_counts()[1] == before[1]
                    nested.rollback()
                assert history_counts() == before

                # An eligible attempt is flushed inside a caller-owned
                # PostgreSQL savepoint and cannot survive its rollback.
                with db.begin_nested() as nested:
                    second_write = record_rational_attempt(
                        db, context=second, submission="x=-3/4", **args,
                    )
                    assert second_write.decision.eligible
                    assert second_write.decision.correct
                    assert not second_write.decision.independent_evidence_eligible
                    assert second_write.attempt_id is not None
                    assert history_counts()[0] == before[0] + 1
                    assert history_counts()[1] == before[1]
                    assert record_rational_attempt(
                        db, context=second, submission="x=-3/4", **args,
                    ).decision == DENIED
                    nested.rollback()
                assert history_counts() == before
        finally:
            transaction.rollback()
    engine.dispose()
