"""Synthetic author tests. These are never independent release authorization."""
import base64
import copy
import json
import os
import uuid
from datetime import UTC
from fractions import Fraction

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import _problem_out
from app.content_models import ProblemContentMetadata
from app.core.database import Base, get_db
from app.curriculum_models import CanonicalSkill, CurriculumSkillMapping, ProblemFamily
from app.diagnostic_models import DiagnosticAttempt
from app.hint_models import HintEvent
from app.main import app
from app.models import (
    Attempt,
    Curriculum,
    MasteryEvent,
    Problem,
    Skill,
    Student,
    StudentSkill,
    TutorSession,
    TutorState,
    TutorTurn,
)
from app.services import content_publishing as publisher
from app.services.fraction_assessment_registry import AssessmentMode
from app.services.problem_selection import select_next_problem
from scripts.ops.publish_content import MANIFEST
from tests.auth_helpers import authenticate_parent_for_student


@compiles(JSONB, "sqlite")
def _json(*_args, **_kwargs):
    return "JSON"


@compiles(UUID, "sqlite")
def _uuid(*_args, **_kwargs):
    return "CHAR(36)"


@pytest.fixture
def signed(monkeypatch):
    manifest = json.loads(MANIFEST.read_text())
    # Synthetic signers exercise only the publisher mechanism. The checked-in
    # Ontario mapping remains PROVISIONAL_NOT_ACCEPTED and cannot activate.
    synthetic_source = copy.deepcopy(publisher.STANDARDS_PROVENANCE)
    synthetic_source["acceptance"] = "ACCEPTED"
    synthetic_source["disposition"] = "ACCEPTED"
    synthetic_source["coverage_credit"] = True
    synthetic_source["production_taxonomy_activation"] = True
    monkeypatch.setattr(publisher, "STANDARDS_PROVENANCE", synthetic_source)
    manifest["standards_provenance"] = synthetic_source
    manifest["activation"] = "staging"
    manifest["seed_count"] = 4
    private = {role: Ed25519PrivateKey.generate() for role in publisher.ROLES}
    keys = {role: {"principal": f"synthetic-reviewer-{role}", "roles": [role],
                   "public_key": base64.b64encode(key.public_key().public_bytes(
                       Encoding.Raw, PublicFormat.Raw)).decode()} for role, key in private.items()}
    policy = {"keys": keys, "authors": {manifest["generator_sha256"]: manifest["author_principals"]}}
    monkeypatch.delenv("MIHUR_CONTENT_REVIEW_POLICY_FILE", raising=False)
    monkeypatch.setenv("MIHUR_CONTENT_REVIEW_POLICY", json.dumps(policy))
    payload = {k: v for k, v in manifest.items() if k != "review_evidence"}
    for role, key in private.items():
        url = "https://github.com/AyalewGM/ai-tutor/issues/462#synthetic-test-only"
        manifest["review_evidence"].append({"role": role, "key_id": role, "evidence_url": url,
            "signature": base64.b64encode(key.sign(publisher.canonical({
                "manifest": payload, "role": role, "evidence_url": url}))).decode()})
    return manifest, policy


@pytest.fixture
def db():
    pg_url = os.environ.get("MIHUR_PUBLISHER_TEST_DATABASE_URL")
    admin, schema, original_types = None, None, {}
    if pg_url:
        schema = "publisher_test_" + uuid.uuid4().hex
        admin = create_engine(pg_url)
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(pg_url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        from sqlalchemy import DateTime, event
        from sqlalchemy.types import TypeDecorator

        class SQLiteUTC(TypeDecorator):
            impl = DateTime
            cache_ok = True

            def process_result_value(self, value, _dialect):
                return value.replace(tzinfo=UTC) if value is not None and value.tzinfo is None else value

        for table in Base.metadata.tables.values():
            for column in table.columns:
                if isinstance(column.type, DateTime):
                    original_types[column] = column.type
                    column.type = SQLiteUTC(timezone=True)

        @event.listens_for(engine, "connect")
        def sqlite_functions(connection, _record):
            connection.create_function("timezone", 2, lambda _zone, value: value)

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        curriculum = Curriculum(code="MTH1W", name="Synthetic Ontario", version="2021", active=True)
        session.add(curriculum)
        session.flush()
        skill = Skill(curriculum_id=curriculum.id, code="MTH1W.C.ALG.EQ2", name="Two step equations")
        canonical = CanonicalSkill(code="MATH.EE.EQUATION.TWO", name="Two step", subject="MATHEMATICS")
        session.add_all([skill, canonical])
        session.flush()
        session.add(CurriculumSkillMapping(skill_id=skill.id, canonical_skill_id=canonical.id))
        session.commit()
        yield session
    for column, original_type in original_types.items():
        column.type = original_type
    engine.dispose()
    if admin is not None:
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def test_pending_and_forged_approvals_fail_closed(signed, monkeypatch):
    manifest, policy = signed
    assert publisher.validate(manifest)
    pending = json.loads(MANIFEST.read_text())
    pending["standards_provenance"] = publisher.STANDARDS_PROVENANCE
    with pytest.raises(publisher.PublicationBlocked, match="pending"):
        publisher.validate(pending)
    for field, value in [
        ("seed_count", 5), ("local_skill", "OTHER"), ("content_revision", "a" * 40),
        ("standards_provenance", {}),
    ]:
        forged = copy.deepcopy(manifest)
        forged[field] = value
        with pytest.raises(publisher.PublicationBlocked):
            publisher.validate(forged)
    forged = copy.deepcopy(manifest)
    forged["review_evidence"][0]["signature"] = "AAAA"
    with pytest.raises(publisher.PublicationBlocked):
        publisher.validate(forged)
    role = manifest["review_evidence"][0]["key_id"]
    policy["keys"][role]["principal"] = manifest["author_principals"][0]
    monkeypatch.setenv("MIHUR_CONTENT_REVIEW_POLICY", json.dumps(policy))
    with pytest.raises(publisher.PublicationBlocked, match="author-owned"):
        publisher.validate(manifest)
    manifest["author_principals"] = ["fake-author"]
    with pytest.raises(publisher.PublicationBlocked):
        publisher.validate(manifest)


def test_insert_only_reseed_mode_isolation_rollback_and_tampering(db, signed):
    manifest, _ = signed
    report = publisher.publish(db, manifest)
    db.commit()
    assert report["stored"] == report["authorized"] == 12
    assert report["learner_selectable"] == {"diagnostic": 4, "guided": 4, "independent": 4}
    rows = db.scalars(select(Problem)).all()
    provenance = db.scalars(select(ProblemContentMetadata)).all()
    assert all(meta.provenance_json["standards"] == publisher.STANDARDS_PROVENANCE
               for meta in provenance)
    assert all(row.solution["manifest"]["standards_provenance"]
               == publisher.STANDARDS_PROVENANCE for row in rows)
    ids = {p.id for p in rows}
    assert len({p.solution["task_fingerprint"] for p in rows}) == 12
    skill = db.scalar(select(Skill))
    assert select_next_problem(db, skill_id=skill.id, current_problem_id=None,
        current_difficulty=3, state=TutorState.DIAGNOSE, allow_published=False) is None
    family = db.scalar(select(ProblemFamily))
    family.active = False
    assert not publisher.permitted(db, rows[0], rows[0].solution["mode"])
    family.active = True
    assert publisher.publish(db, manifest) == report
    assert {p.id for p in db.scalars(select(Problem))} == ids
    problem = rows[0]
    mode = AssessmentMode(problem.solution["mode"])
    expected = Fraction(problem.canonical_answer.split("=")[1])
    alternate = f"x={expected.numerator * 3}/{expected.denominator * 3}"
    result = publisher.score_published(db, problem, alternate, mode, assisted=False)
    assert result.correct
    assert result.independent_evidence_eligible is False
    assert not publisher.score_published(db, problem, "x=99999999", mode, assisted=False).correct
    assert not publisher.score_published(db, problem, alternate, mode, assisted=True).independent_evidence_eligible
    other = AssessmentMode.GUIDED if mode != AssessmentMode.GUIDED else AssessmentMode.INDEPENDENT
    with pytest.raises(publisher.PublicationBlocked):
        publisher.score_published(db, problem, alternate, other, assisted=False)
    public = _problem_out(problem).model_dump(mode="json")
    assert not {"canonical_answer", "solution", "manifest"}.intersection(public)
    problem.canonical_answer = "x=99999999"
    assert not publisher.permitted(db, problem, mode.value)
    db.rollback()
    assert publisher.rollback(db, report["package_digest"]) == 12
    db.commit()
    assert db.scalar(select(func.count(Problem.id))) == 12
    assert publisher.report(db, manifest)["authorized"] == 0
    with pytest.raises(publisher.PublicationBlocked, match="disabled"):
        publisher.publish(db, manifest)


def test_real_selector_and_authenticated_response_feedback_and_replay(db, signed, monkeypatch):
    from sqlalchemy.orm import sessionmaker
    for module in ("app.auth", "app.adaptive_response_api", "app.diagnostic_api",
                   "app.middleware.geo_restriction"):
        monkeypatch.setattr(module + ".SessionLocal", sessionmaker(bind=db.get_bind()))
    manifest, _ = signed
    publisher.publish(db, manifest)
    db.commit()
    skill = db.scalar(select(Skill))
    student = Student(curriculum_id=skill.curriculum_id, first_name="Synthetic QA", grade_level="9")
    db.add(student)
    db.flush()
    db.add(StudentSkill(student_id=student.id, skill_id=skill.id, current_difficulty=3))
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            authenticate_parent_for_student(client, db, student)
            start = client.post("/api/v1/adaptive-tutor/sessions", json={
                "student_id": str(student.id), "skill_id": str(skill.id)})
            assert start.status_code == 200, start.text
            body = start.json()
            from scripts.ops.content_learner_probe import assert_public
            assert_public(body)
            session_id = body["session_id"]
            problem_id = body["problem"]["id"]
            problem = db.get(Problem, __import__("uuid").UUID(problem_id))
            response = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={
                "problem_id": problem_id, "answer": problem.canonical_answer})
            assert response.status_code == 200, response.text
            assert response.json()["evaluation"]["correct"] is True
            assert response.json()["xp_earned"] == 0
            assert response.json()["new_awards"] == []
            assert response.json()["tutor"]["message"]
            assert_public(response.json())
            assert db.scalar(select(func.count(Attempt.id))) == 1
            # Scoring feedback must not become independent mastery via the
            # separate persisted-attempt evidence loader.
            from app.services.mastery_gate_evidence import load_mastery_gate_evidence

            gate_evidence = load_mastery_gate_evidence(
                db, student_id=student.id, skill_id=skill.id,
            )
            assert gate_evidence.independent_correct_count == 0
            assert gate_evidence.strong_help_seen is False
            replay = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={
                "problem_id": problem_id, "answer": problem.canonical_answer})
            assert replay.status_code == 409
            legacy = client.post(f"/api/v1/tutor/sessions/{session_id}/respond", json={
                "problem_id": problem_id, "answer": problem.canonical_answer})
            assert legacy.status_code in {404, 409}
            next_problem = select_next_problem(db, skill_id=skill.id,
                current_problem_id=problem.id, current_difficulty=3, state=TutorState.DIAGNOSE,
                student_id=student.id)
            assert next_problem is not None and next_problem.id != problem.id
            # Separate mode pools remain disjoint after an actual persisted attempt.
            guided = select_next_problem(db, skill_id=skill.id, current_problem_id=None,
                current_difficulty=3, state=TutorState.GUIDED_PRACTICE, student_id=student.id)
            independent = select_next_problem(db, skill_id=skill.id, current_problem_id=None,
                current_difficulty=3, state=TutorState.INDEPENDENT_PRACTICE, student_id=student.id)
            assert guided.solution["mode"] == "guided"
            assert independent.solution["mode"] == "independent"
            # The publisher is feedback-only. A correct response is not
            # evidence of completed diagnosis, repair, or fresh transfer.
            # Do not invent a next task when the authenticated state machine
            # withholds one pending the reviewed learner journey.
            if response.json()["next_problem"] is not None:
                assert_public(response.json()["next_problem"])
            progress = db.get(StudentSkill, {"student_id": student.id, "skill_id": skill.id})
            assert progress.independent_correct_count == 0
            assert progress.independent_attempt_count == 0
            assert progress.attempt_count == 0
            # Reseeding cannot change existing history or materialized variant identities.
            history = db.scalars(select(Attempt.id)).all()
            publisher.publish(db, manifest)
            assert db.scalars(select(Attempt.id)).all() == history
            assert db.scalar(select(func.count(TutorSession.id))) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("confirm", [False, True])
def test_authenticated_published_reasoning_requires_stored_answer_and_oracle_choice(
    db, signed, monkeypatch, confirm,
):
    """A client's choice cannot invent a misconception or grant mastery."""
    from sqlalchemy.orm import sessionmaker

    from app.models import TutorTurn
    from app.services.fraction_assessment_registry import score_fraction

    for module in ("app.auth", "app.adaptive_response_api", "app.diagnostic_api",
                   "app.middleware.geo_restriction"):
        monkeypatch.setattr(module + ".SessionLocal", sessionmaker(bind=db.get_bind()))
    manifest, _ = signed
    publisher.publish(db, manifest)
    db.commit()
    skill = db.scalar(select(Skill))
    student = Student(curriculum_id=skill.curriculum_id, first_name="Synthetic QA", grade_level="9")
    db.add(student)
    db.flush()
    db.add(StudentSkill(student_id=student.id, skill_id=skill.id, current_difficulty=3))
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            authenticate_parent_for_student(client, db, student)
            start = client.post("/api/v1/adaptive-tutor/sessions", json={
                "student_id": str(student.id), "skill_id": str(skill.id),
            })
            assert start.status_code == 200, start.text
            session_id = start.json()["session_id"]
            problem = db.get(Problem, uuid.UUID(start.json()["problem"]["id"]))
            item = next(
                candidate for mode, candidate in publisher.candidates(manifest)
                if mode == problem.solution["mode"]
                and candidate["variant_id"] == problem.solution["variant_id"]
            )
            signal = item["diagnostic_contract_for_author_review"]["signals"][0]
            answer = signal["candidate_response"]
            assert not score_fraction(answer, problem.canonical_answer, variable="x")
            path = f"/api/v1/adaptive-tutor/sessions/{session_id}/published-reasoning"
            assert client.get(path, params={"problem_id": str(problem.id)}).status_code == 409
            first = client.post(f"/api/v1/adaptive-tutor/sessions/{session_id}/respond", json={
                "problem_id": str(problem.id), "answer": answer,
            })
            assert first.status_code == 200, first.text
            assert first.json()["evaluation"]["correct"] is False
            probe_response = client.get(path, params={"problem_id": str(problem.id)})
            assert probe_response.status_code == 200, probe_response.text
            probe = probe_response.json()
            assert probe["stage"] == "CONFIRM_REASONING"
            assert "misconception_code" not in json.dumps(probe)
            assert "canonical_answer" not in json.dumps(probe)
            assert probe["independent_evidence_eligible"] is False
            wrong_choice = next(
                c["id"] for c in probe["choices"]
                if c["id"] != signal["confirmation_evidence_choice_for_author_review"]
            )
            choice_id = (
                signal["confirmation_evidence_choice_for_author_review"]
                if confirm else wrong_choice
            )
            result = client.post(path, json={
                "problem_id": str(problem.id), "choice_id": choice_id,
            })
            assert result.status_code == 200, result.text
            assert result.json()["independent_evidence_eligible"] is False
            if confirm:
                assert result.json()["stage"] == "REPAIR_PENDING_GUIDED_RETEST"
                assert "misconception_code" not in json.dumps(result.json())
                assert db.scalar(select(func.count(TutorTurn.id)).where(
                    TutorTurn.pedagogical_action == "PUBLISHED_REASONING_CONFIRMED",
                )) == 1
            else:
                assert result.json()["stage"] == "PRACTICE_RETRY"
                assert db.scalar(select(func.count(TutorTurn.id)).where(
                    TutorTurn.pedagogical_action == "PUBLISHED_REASONING_CONFIRMED",
                )) == 0
            # Even a second, now-correct choice cannot brute-force the probe.
            assert client.post(path, json={
                "problem_id": str(problem.id),
                "choice_id": signal["confirmation_evidence_choice_for_author_review"],
            }).status_code == 409
            progress = db.get(StudentSkill, {"student_id": student.id, "skill_id": skill.id})
            assert progress.independent_correct_count == 0
            assert progress.independent_attempt_count == 0
    finally:
        app.dependency_overrides.clear()


def test_authenticated_published_step_and_photo_assistance_fail_without_history(
    db, signed, monkeypatch,
):
    """Synthetic HTTP denial: unreviewed support must not grade, scan, or write evidence."""
    from sqlalchemy.orm import sessionmaker

    from app import adaptive_response_api

    for module in ("app.auth", "app.adaptive_response_api", "app.diagnostic_api",
                   "app.middleware.geo_restriction"):
        monkeypatch.setattr(module + ".SessionLocal", sessionmaker(bind=db.get_bind()))
    manifest, _ = signed
    publisher.publish(db, manifest)
    db.commit()
    skill = db.scalar(select(Skill))
    student = Student(
        curriculum_id=skill.curriculum_id, first_name="Synthetic QA", grade_level="9",
    )
    db.add(student)
    db.flush()
    db.add(StudentSkill(student_id=student.id, skill_id=skill.id, current_difficulty=3))
    db.commit()

    def history_snapshot():
        progress = db.get(
            StudentSkill, {"student_id": student.id, "skill_id": skill.id},
        )
        return (
            *(db.scalar(select(func.count(model.id))) for model in (
                Attempt, DiagnosticAttempt, HintEvent, MasteryEvent, TutorTurn,
            )),
            progress.attempt_count,
            progress.correct_count,
            progress.independent_attempt_count,
            progress.independent_correct_count,
            progress.mastery_score,
            progress.confidence_score,
        )

    def forbidden_support(*_args, **_kwargs):
        raise AssertionError("published unreviewed step assistance was invoked")

    class ForbiddenOcr:
        def scan(self, *_args, **_kwargs):
            raise AssertionError("published photo OCR was invoked")

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[adaptive_response_api.photo_ocr.get_ocr_provider] = ForbiddenOcr
    try:
        with TestClient(app) as client:
            authenticate_parent_for_student(client, db, student)
            start = client.post("/api/v1/adaptive-tutor/sessions", json={
                "student_id": str(student.id), "skill_id": str(skill.id),
            })
            assert start.status_code == 200, start.text
            session_id = start.json()["session_id"]
            problem_id = start.json()["problem"]["id"]
            problem = db.get(Problem, uuid.UUID(problem_id))
            assert problem.source_type == "PUBLISHED"
            before = history_snapshot()
            with monkeypatch.context() as patch:
                patch.setattr(
                    adaptive_response_api.stepwork, "problem_supports_steps",
                    forbidden_support,
                )
                typed = client.post(
                    f"/api/v1/adaptive-tutor/sessions/{session_id}/work-step",
                    json={"problem_id": problem_id, "line": "x=1"},
                )
                assert typed.status_code == 409, typed.text
                assert "not yet authorized" in typed.json()["detail"]
                assert history_snapshot() == before

                photo = client.post(
                    f"/api/v1/adaptive-tutor/sessions/{session_id}/work-photo/scan",
                    data={"problem_id": problem_id},
                    files={"file": ("synthetic.jpg", b"not-an-image", "image/jpeg")},
                )
                assert photo.status_code == 409, photo.text
                assert "not yet authorized" in photo.json()["detail"]
                assert history_snapshot() == before
    finally:
        app.dependency_overrides.clear()


def test_revoked_authority_and_tampered_runtime_deny_selection(db, signed, monkeypatch):
    manifest, _ = signed
    publisher.publish(db, manifest)
    db.commit()
    skill = db.scalar(select(Skill))
    monkeypatch.setenv("MIHUR_CONTENT_REVIEW_POLICY", "{}")
    assert publisher.report(db, manifest)["authorized"] == 0
    assert select_next_problem(db, skill_id=skill.id, current_problem_id=None,
        current_difficulty=3, state=TutorState.GUIDED_PRACTICE) is None
    with pytest.raises(publisher.PublicationBlocked):
        publisher.publish(db, manifest)
    changed = copy.deepcopy(manifest)
    changed["runtime_sha256"] = "0" * 64
    with pytest.raises(publisher.PublicationBlocked, match="Runtime contract"):
        publisher.validate(changed)


def test_actual_provisional_ontario_mapping_is_never_authorized():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["standards_provenance"]["acceptance"] == "PROVISIONAL_NOT_ACCEPTED"
    manifest["activation"] = "staging"
    with pytest.raises(publisher.PublicationBlocked, match="not independently accepted"):
        publisher.validate(manifest)
