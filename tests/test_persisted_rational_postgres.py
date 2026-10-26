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
from app.models import Attempt, Curriculum, MasteryEvent, Problem, Skill, Student, TutorSession, TutorState
from app.services.family_activation_adapter import DENIED, FamilyRegistration
from app.services.fraction_assessment_registry import AssessmentMode, ReviewedFamily
from app.services.persisted_rational_resolution import TrustedAssessmentContext, score_persisted_rational
from app.services.question_package_release import PackageReleaseEvidence

_SHA = "a" * 40
_FAMILY = "SYNTHETIC.ON.RATIONAL"
_SKILL = "MATH.EE.EQUATION.TWO"


def _source():
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
        source_mapping_revision="c" * 40,
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
                    code=f"SYNTHETIC-RATIONAL-{uuid.uuid4().hex[:10]}",
                    name="Synthetic rational resolution curriculum", version="v1",
                )
                db.add(curriculum)
                db.flush()
                skill = Skill(curriculum_id=curriculum.id, code=_SKILL, name="Synthetic rational")
                db.add(skill)
                db.flush()
                problem = Problem(
                    primary_skill_id=skill.id, problem_type="SYNTHETIC_RATIONAL",
                    difficulty=3, prompt="Solve a synthetic equation",
                    canonical_answer="x=-3/4", answer_kind="VARIABLE_VALUE",
                )
                db.add(problem)
                db.flush()
                db.add(ProblemContentMetadata(
                    problem_id=problem.id, curriculum_id=curriculum.id,
                    objective="synthetic", evaluation_type="EXACT",
                    independent_eligible=True,
                    provenance_json={"family_id": _FAMILY, "content_sha": _SHA},
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
                db.flush()

                def history_counts():
                    return tuple(db.scalar(select(func.count()).select_from(model)) for model in (
                        Attempt, MasteryEvent,
                    ))

                before = history_counts()
                source = _source()
                first = TrustedAssessmentContext(
                    students[0].id, sessions[0].id, problem.id, AssessmentMode.INDEPENDENT,
                )
                args = {
                    "approval_source": source,
                    "service_principal": "synthetic-test-runner",
                }
                a = score_persisted_rational(db, context=first, submission="X=6/-8", **args)
                b = score_persisted_rational(db, context=first, submission="x=-9/12", **args)
                assert a.eligible and a.correct and a.independent_evidence_eligible
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
                assert history_counts() == before
                assert db.dirty == set()
        finally:
            transaction.rollback()
    engine.dispose()
