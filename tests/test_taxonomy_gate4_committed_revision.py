"""Gate-4 committed-revision regression against an isolated PostgreSQL DB.

Requires TEST_DATABASE_URL and MIHUR_GATE4_ISOLATED_DB=1. The test constructs
all learner-evidence and variant fixtures it needs and deletes only its own rows.
No production use.
"""
import os
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import MetaData, Table, create_engine, delete, inspect, select
from sqlalchemy.orm import Session

from app.canonical_skill_taxonomy import (
    CanonicalSkillDefinition,
    CanonicalTaxonomy,
    SkillReviewState,
    TaxonomyError,
)
from app.canonical_taxonomy_reconciliation import (
    PersistedSkillIdentity,
    validate_identity_revision,
)
from app.curriculum_models import CanonicalSkill
from app.diagnostic_models import DiagnosticAttempt, DiagnosticSession
from app.models import (
    Attempt,
    MasteryEvent,
    Problem,
    Skill,
    Student,
    StudentSkill,
    TutorSession,
)
from scripts.validate_canonical_alias_map import validate_manifest


ALL_OF_PROFILE_CODES = {
    "MATH.ARITHMETIC.ADD_SUB_WITHIN_20",
    "MATH.NUMBER_SENSE.COUNT_COMPARE_TO_120",
}


def _table_rows(connection, table):
    """Return deterministic full-row snapshots, including every persisted column."""
    statement = select(table)
    primary_key = list(table.primary_key.columns)
    if primary_key:
        statement = statement.order_by(*primary_key)
    return [dict(row) for row in connection.execute(statement).mappings()]


def _database_snapshot(engine, table_names):
    with engine.connect() as connection:
        metadata = MetaData()
        return {
            name: _table_rows(
                connection,
                Table(name, metadata, autoload_with=connection),
            )
            for name in sorted(table_names)
        }


def _assert_reviewed_alias_authority(reviewed_code, draft_code):
    """Alias publication authority comes from reviewed taxonomy, never a draft."""
    reviewed = CanonicalSkillDefinition(
        code=reviewed_code,
        name="Reviewed synthetic skill",
        description="Gate-4 reviewed alias target",
        review_state=SkillReviewState.REVIEWED,
        reviewed_by="gate4-test-fixture",
    )
    draft = CanonicalSkillDefinition(
        code=draft_code,
        name="Draft synthetic skill",
        description="Gate-4 draft alias target",
        review_state=SkillReviewState.DRAFT,
    )
    taxonomy = CanonicalTaxonomy(
        "gate4-alias-authority",
        {reviewed_code: reviewed, draft_code: draft},
    )
    known_skills = {
        code for code in taxonomy.skills if taxonomy.contains(code, reviewed_only=True)
    }

    def manifest(target):
        return {
            "schema_version": 1,
            "mapping_version": "gate4-test-only",
            "aliases": [{
                "alias": "MATH.ELEMENTARY.TEST",
                "status": "REVIEWED",
                "relation": "ALL_OF",
                "target_skill_codes": [target],
                "evidence": ["synthetic Gate-4 contract evidence"],
                "reviewed_by": "gate4-test-fixture",
            }],
        }

    assert validate_manifest(
        manifest(reviewed_code),
        {"MATH.ELEMENTARY.TEST"},
        known_skills,
        publication_gate=True,
    ) == []
    assert any(
        "unknown application skill" in error
        for error in validate_manifest(
            manifest(draft_code),
            {"MATH.ELEMENTARY.TEST"},
            known_skills,
            publication_gate=True,
        )
    )


def test_committed_taxonomy_revision_preserves_evidence_variants_and_credit():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires TEST_DATABASE_URL for an isolated PostgreSQL DB")
    if os.getenv("MIHUR_GATE4_ISOLATED_DB") != "1":
        pytest.skip("Requires explicit MIHUR_GATE4_ISOLATED_DB=1 safety opt-in")
    assert url.startswith(
        ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")
    )
    engine = create_engine(url)

    suffix = uuid4().hex.upper()
    historical_code = f"MATH.TEST.GATE4.HISTORICAL.{suffix}"
    reviewed_code = f"MATH.TEST.GATE4.REVIEWED.{suffix}"
    draft_code = f"MATH.TEST.GATE4.DRAFT.{suffix}"
    historical_id = uuid4()
    reviewed_id = uuid4()
    variant_id = f"gate4-variant-{suffix.lower()}"
    fixture_ready = False
    committed = False
    fixture_ids = {}

    try:
        # Create deterministic evidence against an existing broad MATH.NS.* skill,
        # plus a persisted variant identifier associated to the historical identity.
        with Session(engine) as session:
            broad_skill = session.scalar(
                select(Skill).where(Skill.code.like("MATH.NS.%")).limit(1)
            )
            assert broad_skill is not None, "CI seed must include a broad MATH.NS.* skill"

            historical = CanonicalSkill(
                id=historical_id,
                code=historical_code,
                name="Gate-4 historical identity",
                description="Synthetic historical identity for isolated regression",
            )
            student = Student(first_name="Gate4 synthetic", grade_level="1")
            session.add_all([historical, student])
            session.flush()
            problem = Problem(
                primary_skill_id=broad_skill.id,
                problem_type="GATE4_TEST",
                difficulty=1,
                prompt="1+1?",
                canonical_answer="2",
                solution={
                    "variant_id": variant_id,
                    "canonical_skill_code": historical_code,
                    "parameters": {"left": 1, "right": 1},
                },
            )
            session.add(problem)
            session.flush()
            tutor = TutorSession(
                student_id=student.id,
                primary_skill_id=broad_skill.id,
            )
            diagnostic = DiagnosticSession(
                student_id=student.id,
                target_skill_id=broad_skill.id,
                current_skill_id=broad_skill.id,
            )
            session.add_all([tutor, diagnostic])
            session.flush()
            attempt = Attempt(
                session_id=tutor.id,
                student_id=student.id,
                problem_id=problem.id,
                student_answer="2",
                is_correct=True,
            )
            diagnostic_attempt = DiagnosticAttempt(
                diagnostic_session_id=diagnostic.id,
                skill_id=broad_skill.id,
                problem_id=problem.id,
                student_answer="2",
                is_correct=True,
                sequence_number=1,
            )
            session.add_all([attempt, diagnostic_attempt])
            session.flush()
            mastery = MasteryEvent(
                student_id=student.id,
                skill_id=broad_skill.id,
                attempt_id=attempt.id,
                previous_score=Decimal("0.100"),
                new_score=Decimal("0.200"),
                previous_confidence=Decimal("0.100"),
                new_confidence=Decimal("0.200"),
                reason="gate4-synthetic",
                metadata_json={
                    "variant_id": variant_id,
                    "canonical_skill_code": historical_code,
                },
            )
            session.add(mastery)
            session.flush()
            fixture_ids = {
                MasteryEvent: mastery.id,
                DiagnosticAttempt: diagnostic_attempt.id,
                Attempt: attempt.id,
                DiagnosticSession: diagnostic.id,
                TutorSession: tutor.id,
                Problem: problem.id,
                Student: student.id,
            }
            broad_skill_id = broad_skill.id
            session.commit()
            fixture_ready = True

        with engine.connect() as connection:
            names = set(inspect(connection).get_table_names())
        evidence_names = {"attempts", "diagnostic_attempts", "mastery_events"}
        assert evidence_names <= names
        variant_table_names = {name for name in names if "variant" in name.lower()}
        snapshot_names = evidence_names | variant_table_names | {
            "canonical_skills",
            "problems",
            "student_skills",
        }
        before = _database_snapshot(engine, snapshot_names)
        assert all(before[name] for name in evidence_names)

        with Session(engine) as session:
            original = {
                row.code: PersistedSkillIdentity(row.code, row.id)
                for row in session.scalars(select(CanonicalSkill))
            }
            assert original[historical_code].skill_id == historical_id
            definition = CanonicalSkillDefinition(
                code=reviewed_code,
                name="Gate-4 reviewed additive identity",
                description="Synthetic, isolated database test only",
                review_state=SkillReviewState.REVIEWED,
                reviewed_by="gate4-test-fixture",
            )
            taxonomy = CanonicalTaxonomy(
                "gate4-test-only",
                {reviewed_code: definition},
            )
            proposed = {
                **original,
                reviewed_code: PersistedSkillIdentity(reviewed_code, reviewed_id),
            }
            validate_identity_revision(original, proposed, taxonomy)
            session.add(
                CanonicalSkill(
                    id=reviewed_id,
                    code=reviewed_code,
                    name=definition.name,
                    description=definition.description,
                )
            )
            session.commit()  # A real committed revision, not flush/rollback.
            committed = True

        after = _database_snapshot(engine, snapshot_names)
        assert after["attempts"] == before["attempts"]
        assert after["diagnostic_attempts"] == before["diagnostic_attempts"]
        assert after["mastery_events"] == before["mastery_events"]
        assert after["student_skills"] == before["student_skills"]
        for name in variant_table_names:
            assert after[name] == before[name]

        with Session(engine) as session:
            persisted_problem = session.get(Problem, fixture_ids[Problem])
            assert persisted_problem.solution == {
                "variant_id": variant_id,
                "canonical_skill_code": historical_code,
                "parameters": {"left": 1, "right": 1},
            }
            persisted_event = session.get(MasteryEvent, fixture_ids[MasteryEvent])
            assert persisted_event.metadata_json == {
                "variant_id": variant_id,
                "canonical_skill_code": historical_code,
            }

            # A bounded child identity cannot inherit broad MATH.NS.* evidence.
            assert session.scalar(
                select(MasteryEvent.id).where(MasteryEvent.skill_id == reviewed_id)
            ) is None
            assert session.scalar(
                select(StudentSkill.student_id).where(StudentSkill.skill_id == reviewed_id)
            ) is None
            assert session.scalar(
                select(MasteryEvent.id).where(MasteryEvent.skill_id == broad_skill_id)
            ) == fixture_ids[MasteryEvent]

            # ALL_OF profiles are reporting-only: no canonical UUID, mastery,
            # independent variant namespace, or second credit-bearing event.
            assert not set(
                session.scalars(
                    select(CanonicalSkill.code).where(
                        CanonicalSkill.code.in_(ALL_OF_PROFILE_CODES)
                    )
                )
            )
            assert session.scalar(
                select(MasteryEvent.id).where(
                    MasteryEvent.reason.in_(ALL_OF_PROFILE_CODES)
                )
            ) is None
            assert len(after["mastery_events"]) == len(before["mastery_events"])
            assert len(after["student_skills"]) == len(before["student_skills"])

        _assert_reviewed_alias_authority(reviewed_code, draft_code)

        # Each rejected revision is checked against the real committed database
        # snapshot. Validation must fail before any persistence or evidence write.
        committed_identities = {
            **original,
            reviewed_code: PersistedSkillIdentity(reviewed_code, reviewed_id),
        }
        invalid_cases = [
            # Historical deletion.
            {k: v for k, v in committed_identities.items() if k != historical_code},
            # Historical UUID mutation.
            {
                **committed_identities,
                historical_code: PersistedSkillIdentity(historical_code, uuid4()),
            },
            # UUID reuse / duplicate proposed UUID.
            {
                **committed_identities,
                draft_code: PersistedSkillIdentity(draft_code, historical_id),
            },
            # Unreviewed addition.
            {
                **committed_identities,
                draft_code: PersistedSkillIdentity(draft_code, uuid4()),
            },
            # Mismatched map key.
            {
                **committed_identities,
                "MATH.TEST.GATE4.WRONG_KEY": PersistedSkillIdentity(draft_code, uuid4()),
            },
        ]
        stable_snapshot = _database_snapshot(engine, snapshot_names)
        empty_taxonomy = CanonicalTaxonomy("gate4-reject-unreviewed", {})
        for invalid in invalid_cases:
            with pytest.raises(TaxonomyError):
                validate_identity_revision(
                    committed_identities,
                    invalid,
                    empty_taxonomy,
                )
            assert _database_snapshot(engine, snapshot_names) == stable_snapshot

        with Session(engine) as session:
            current = {
                row.code: PersistedSkillIdentity(row.code, row.id)
                for row in session.scalars(select(CanonicalSkill))
            }
            assert all(current[key] == value for key, value in original.items())
            assert current[reviewed_code].skill_id == reviewed_id
    finally:
        if committed:
            with engine.begin() as connection:
                connection.execute(
                    delete(CanonicalSkill).where(
                        CanonicalSkill.id == reviewed_id,
                        CanonicalSkill.code == reviewed_code,
                    )
                )
        if fixture_ready:
            with engine.begin() as connection:
                for model, row_id in fixture_ids.items():
                    connection.execute(delete(model).where(model.id == row_id))
                connection.execute(
                    delete(CanonicalSkill).where(
                        CanonicalSkill.id == historical_id,
                        CanonicalSkill.code == historical_code,
                    )
                )
        engine.dispose()
