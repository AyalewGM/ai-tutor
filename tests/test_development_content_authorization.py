"""Synthetic runtime grants, mocked native identity/mounts; not live authorization.

Real publisher/selector/scorer and authenticated HTTP handlers use private SQLite.
Only native PostgreSQL identity and root-owned read-only mount metadata are mocked.
"""
import base64
import copy
import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.models import MasteryEvent, Problem, TutorState
from app.services import content_publishing as publisher
from app.services import development_content_authorization as development
from app.services.fraction_assessment_registry import AssessmentMode
from scripts.ops import development_release_authorization as owner
from scripts.ops.publish_content import MANIFEST
from tests import test_content_publishing as publisher_fixtures

_REAL_LOAD_RUNTIME_STATE = development._load_runtime_state


db = publisher_fixtures.db
signed = publisher_fixtures.signed
run_existing_http_journey = publisher_fixtures.test_real_selector_and_authenticated_response_feedback_and_replay


@pytest.fixture(scope="module")
def runtime_owner_key(tmp_path_factory):
    key = tmp_path_factory.mktemp("owner-signature-fixture") / "FIXTURE_ONLY_NEVER_ENROLL"
    subprocess.run(["/usr/bin/ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return key


@pytest.fixture
def development_state(monkeypatch, runtime_owner_key):
    manifest = json.loads(MANIFEST.read_text())
    manifest["activation"] = "staging"
    manifest["standards_provenance"]["acceptance"] = publisher.PARTIAL_PRACTICE_ACCEPTANCE
    manifest["review_evidence"] = []
    manifest["seed_count"] = 2
    manifest["runtime_sha256"] = publisher.runtime_digest()
    package_digest = publisher.validate(manifest, require_approvals=False)
    public = " ".join(runtime_owner_key.with_suffix(".pub").read_text().split()[:2])
    policy = {**owner.SCOPE, "schema": owner.POLICY_SCHEMA, "owner_public_key": public,
              "revoked": False, "max_age_seconds": 3600, "max_runtime_seconds": 86400,
              "operator_pins_sha256": "1" * 64}
    context = {**owner.SCOPE, "source_sha": "2" * 40, "source_tree": "3" * 40,
               "package_sha256": package_digest, "runtime_sha256": publisher.runtime_digest(),
               "database_cluster_id": "1234567890123456789", "evidence_sha256": "4" * 64,
               "actions": ["deploy", "publish"], "images": {
                   key: "example.invalid/synthetic-" + key + "@sha256:" + "5" * 64
                   for key in owner.IMAGE_KEYS}}
    now = int(time.time())
    grant = {"schema": development.GRANT_SCHEMA, "state": "ACTIVE",
             "policy_sha256": owner.digest(policy), "authorization_sha256": "6" * 64,
             "nonce": "7" * 64, "verified_at": now - 10, "runtime_expires_at": now + 3600,
             "owner_runtime_expires_at": now + 3600, "release": copy.deepcopy(context)}
    state = {"manifest": manifest, "policy": policy, "context": context, "grant": grant}
    def resign(*, namespace=owner.NAMESPACE, hash_algorithm="sha512", payload_changes=None):
        current_policy, current_grant = state["policy"], state["grant"]
        payload = {**state["context"], "schema": owner.AUTH_SCHEMA, "namespace": owner.NAMESPACE,
                   "policy_sha256": owner.digest(current_policy), "issued_at": now - 20,
                   "expires_at": now + 1800,
                   "runtime_expires_at": current_grant["owner_runtime_expires_at"],
                   "nonce": current_grant["nonce"]}
        payload.update(payload_changes or {})
        state["payload"] = payload
        state["envelope"] = owner.canonical(payload)
        current_grant["authorization_sha256"] = hashlib.sha256(state["envelope"]).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture-owner-authorization"
            path.write_bytes(state["envelope"])
            subprocess.run(["/usr/bin/ssh-keygen", "-Y", "sign", "-f", str(runtime_owner_key),
                            "-n", namespace, "-O", "hashalg=" + hash_algorithm, str(path)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            state["signature"] = Path(str(path) + ".sig").read_bytes()
    state["resign"] = resign
    resign()
    native_db = {key: context[key] for key in ("database", "database_role", "database_cluster_id")}
    monkeypatch.setattr(development, "configured", lambda: True)
    monkeypatch.setattr(development, "_load_runtime_state", lambda: tuple(
        copy.deepcopy(state[key]) for key in ("policy", "context", "grant", "envelope", "signature")))
    monkeypatch.setattr(development, "_machine_identity", lambda: owner.HOST)
    monkeypatch.setattr(development, "_database_identity", lambda _db: dict(native_db))
    return state


def test_development_grant_publishes_and_reads_without_consuming_operation_nonce(
    db, development_state, monkeypatch,
):
    def unexpected_operation_nonce(*_args, **_kwargs):
        raise AssertionError("runtime package permission consumed an operation nonce")
    monkeypatch.setattr(owner, "reserve_nonce", unexpected_operation_nonce)
    manifest = development_state["manifest"]
    assert publisher.authorize_package(manifest, db) == development_state["context"]["package_sha256"]
    report = publisher.publish(db, manifest)
    assert report["stored"] == 6
    problem = db.scalar(select(Problem).where(Problem.source_type == "PUBLISHED"))
    mode = problem.solution["mode"]
    assert publisher.permitted(db, problem, mode)
    assert publisher.permitted(db, problem, mode)
    decision = publisher.score_published(
        db, problem, problem.canonical_answer, AssessmentMode(mode), assisted=False)
    assert decision.correct and decision.independent_evidence_eligible is False
    assert db.scalar(select(func.count(MasteryEvent.id))) == 0


def test_provisional_runtime_permission_can_be_shorter_than_owner_signed_limit(
    db, development_state,
):
    original_owner_expiry = development_state["grant"]["owner_runtime_expires_at"]
    development_state["grant"]["runtime_expires_at"] = int(time.time()) + 30
    assert publisher.authorize_package(development_state["manifest"], db)
    assert development_state["grant"]["owner_runtime_expires_at"] == original_owner_expiry


@pytest.mark.parametrize("change", ["exceeds_owner", "exceeds_policy", "invalid_owner_type", "missing_owner_limit"])
def test_runtime_permission_cannot_exceed_original_owner_or_policy_limit(
    db, development_state, change,
):
    grant = development_state["grant"]
    if change == "exceeds_owner":
        grant["runtime_expires_at"] = grant["owner_runtime_expires_at"] + 1
    elif change == "exceeds_policy":
        grant["owner_runtime_expires_at"] = grant["verified_at"] + development_state["policy"]["max_runtime_seconds"] + 1
    elif change == "invalid_owner_type":
        grant["owner_runtime_expires_at"] = True
    else:
        grant.pop("owner_runtime_expires_at")
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(development_state["manifest"], db)


@pytest.mark.parametrize("change", ["revoked", "missing_grant", "expired", "policy_changed", "rotated_owner_key"])
def test_runtime_rechecks_revocation_after_prior_success(db, development_state, change):
    manifest = development_state["manifest"]
    publisher.publish(db, manifest)
    problem = db.scalar(select(Problem).where(Problem.source_type == "PUBLISHED"))
    mode = problem.solution["mode"]
    assert publisher.permitted(db, problem, mode)
    if change == "revoked":
        development_state["policy"]["revoked"] = True
    elif change == "missing_grant":
        development_state["grant"] = {}
    elif change == "expired":
        development_state["grant"]["runtime_expires_at"] = int(time.time()) - 1
    elif change == "policy_changed":
        development_state["policy"]["owner_public_key"] += "invalid"
    else:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

        development_state["policy"]["owner_public_key"] = Ed25519PrivateKey.generate().public_key()\
            .public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH).decode()
    assert not publisher.permitted(db, problem, mode)
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(manifest, db)


@pytest.mark.parametrize("field,value", [
    ("source_sha", "8" * 40), ("source_tree", "9" * 40),
    ("package_sha256", "a" * 64), ("runtime_sha256", "b" * 64),
    ("environment", "production"), ("database", "production"),
    ("database_role", "production"), ("database_cluster_id", "9876543210123456789"),
    ("host_sha256", "c" * 64), ("images", {}),
])
def test_changed_protected_subject_or_environment_is_denied(db, development_state, field, value):
    development_state["context"][field] = value
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(development_state["manifest"], db)
    assert db.scalar(select(func.count(Problem.id))) == 0


@pytest.mark.parametrize("field,value", [
    ("database", "other"), ("database_role", "postgres"),
    ("database_cluster_id", "9876543210123456789"),
])
def test_actual_native_database_identity_must_match(db, development_state, monkeypatch, field, value):
    actual = {key: development_state["context"][key] for key in (
        "database", "database_role", "database_cluster_id")}
    actual[field] = value
    monkeypatch.setattr(development, "_database_identity", lambda _db: actual)
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(development_state["manifest"], db)


def test_actual_native_machine_identity_must_match(db, development_state, monkeypatch):
    monkeypatch.setattr(development, "_machine_identity", lambda: "a" * 64)
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(development_state["manifest"], db)


@pytest.mark.parametrize("actions", [["deploy"], ["rollback"], ["publish", "deploy"]])
def test_deploy_only_or_rollback_grant_never_grants_package_permission(db, development_state, actions):
    development_state["context"]["actions"] = actions
    development_state["grant"]["release"]["actions"] = list(actions)
    development_state["resign"]()
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(development_state["manifest"], db)


@pytest.mark.parametrize("change", ["pending", "provisional", "fake_six_role_evidence"])
def test_runtime_never_promotes_package_disposition(db, development_state, change):
    manifest = development_state["manifest"]
    if change == "pending":
        manifest["activation"] = "pending"
    elif change == "provisional":
        manifest["standards_provenance"]["acceptance"] = "PROVISIONAL_NOT_ACCEPTED"
    else:
        manifest["review_evidence"] = [{"role": "math", "signature": "fake"}]
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(manifest, db)


def test_default_policy_stays_six_signatures_and_environment_flags_cannot_select_development(
    monkeypatch,
):
    manifest = json.loads(MANIFEST.read_text())
    manifest["runtime_sha256"] = publisher.runtime_digest()
    monkeypatch.setattr(development, "configured", lambda: False)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused/mihur_staging")
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(manifest)


def test_default_six_signature_policy_remains_valid_without_development_mount(signed, monkeypatch):
    manifest, _ = signed
    monkeypatch.setattr(development, "configured", lambda: False)
    monkeypatch.setenv("APP_ENV", "development")
    def unexpected_development(*_args, **_kwargs):
        raise AssertionError("environment variable selected development authorization")
    monkeypatch.setattr(development, "authorize", unexpected_development)
    assert publisher.authorize_package(manifest) == publisher.validate(manifest)


def test_partial_development_mount_does_not_fall_back_to_valid_six_signatures(signed, monkeypatch):
    manifest, _ = signed
    monkeypatch.setattr(development, "configured", lambda: True)
    def missing_native_state():
        raise FileNotFoundError("synthetic missing protected grant")
    monkeypatch.setattr(development, "_load_runtime_state", missing_native_state)
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(manifest)


def test_development_authorization_requires_actual_database_handle(development_state):
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(development_state["manifest"])


@pytest.mark.parametrize("correct", [True, False])
def test_real_authenticated_development_feedback_preserves_no_mastery_credit(
    db, development_state, monkeypatch, correct,
):
    # Existing real middleware, selector, Workspace and feedback handler; only the
    # native identity/mount boundary is explicitly mocked by this synthetic fixture.
    run_existing_http_journey(db, (development_state["manifest"], {}), monkeypatch,
                              TutorState.INDEPENDENT_PRACTICE, correct)


@pytest.mark.parametrize("hash_algorithm", ["sha256", "sha512"])
def test_runtime_ed25519_proof_accepts_actual_openssh_signatures_and_native_verification(
    development_state, tmp_path, hash_algorithm,
):
    development_state["resign"](hash_algorithm=hash_algorithm)
    allowed = tmp_path / "fixture-allowed-signers"
    allowed.write_text(f'owner-{owner.OWNER_ID} namespaces="{owner.NAMESPACE}" '
                       + development_state["policy"]["owner_public_key"] + "\n")
    signature = tmp_path / "fixture-owner.sig"
    signature.write_bytes(development_state["signature"])
    result = subprocess.run(["/usr/bin/ssh-keygen", "-Y", "verify", "-f", str(allowed),
                             "-I", f"owner-{owner.OWNER_ID}", "-n", owner.NAMESPACE,
                             "-s", str(signature)], input=development_state["envelope"],
                            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert result.returncode == 0
    development._verify_owner_signature(development_state["envelope"],
                                        development_state["signature"],
                                        development_state["policy"]["owner_public_key"])


@pytest.mark.parametrize("change", ["missing", "malformed", "armor_trailing", "blob_trailing", "version"])
def test_runtime_signature_parser_rejects_malformed_or_trailing_data(development_state, change):
    signature = development_state["signature"]
    if change == "missing":
        signature = b""
    elif change == "malformed":
        signature = b"not an SSH signature"
    elif change == "armor_trailing":
        signature += b"TRAILING"
    else:
        raw = base64.b64decode(b"".join(signature.splitlines()[1:-1]), validate=True)
        raw = raw + b"TRAILING" if change == "blob_trailing" else raw[:6] + b"\0\0\0\2" + raw[10:]
        signature = (b"-----BEGIN SSH SIGNATURE-----\n" + base64.b64encode(raw)
                     + b"\n-----END SSH SIGNATURE-----\n")
    with pytest.raises(owner.AuthorizationRejected):
        development._verify_owner_signature(development_state["envelope"], signature,
                                            development_state["policy"]["owner_public_key"])


def test_runtime_signature_rejects_authentic_wrong_namespace(development_state):
    development_state["resign"](namespace="mihur-production-owner-release-v1")
    with pytest.raises(owner.AuthorizationRejected):
        development._verify_owner_signature(development_state["envelope"],
                                            development_state["signature"],
                                            development_state["policy"]["owner_public_key"])


@pytest.mark.parametrize("change", ["source", "runtime_expiry", "signature", "owner_key"])
def test_runtime_rejects_changed_signed_subject_even_if_grant_metadata_is_rewritten(
    db, development_state, change,
):
    payload = copy.deepcopy(development_state["payload"])
    if change == "source":
        payload["source_sha"] = "f" * 40
        development_state["context"]["source_sha"] = payload["source_sha"]
        development_state["grant"]["release"]["source_sha"] = payload["source_sha"]
    elif change == "runtime_expiry":
        payload["runtime_expires_at"] += 1
        development_state["grant"]["owner_runtime_expires_at"] = payload["runtime_expires_at"]
    elif change == "signature":
        development_state["signature"] = b"forged"
    else:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

        development_state["policy"]["owner_public_key"] = Ed25519PrivateKey.generate().public_key()\
            .public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH).decode()
        payload["policy_sha256"] = owner.digest(development_state["policy"])
        development_state["grant"]["policy_sha256"] = payload["policy_sha256"]
    development_state["envelope"] = owner.canonical(payload)
    development_state["grant"]["authorization_sha256"] = hashlib.sha256(
        development_state["envelope"]).hexdigest()
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(development_state["manifest"], db)


def test_runtime_owner_permission_survives_expired_operation_window_without_replay(
    db, development_state, monkeypatch,
):
    now = int(time.time())
    development_state["grant"]["verified_at"] = now - 7190
    development_state["resign"](payload_changes={"issued_at": now - 7200, "expires_at": now - 3600})
    def unexpected_nonce(*_args, **_kwargs):
        raise AssertionError("runtime access attempted to replay an operation nonce")
    monkeypatch.setattr(owner, "reserve_nonce", unexpected_nonce)
    assert publisher.authorize_package(development_state["manifest"], db)


def test_sqlite_is_not_a_native_postgresql_identity(db):
    with pytest.raises(owner.AuthorizationRejected, match="postgresql_identity"):
        development._database_identity(db)


def test_native_database_identity_uses_catalog_control_function():
    captured = []
    class Result:
        def mappings(self):
            return self
        def one(self):
            return {"database": "mihur_staging", "database_role": "mihur_staging",
                    "database_cluster_id": "1234567890123456789"}
    class Database:
        def get_bind(self):
            return SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
        def execute(self, query):
            captured.append(str(query))
            return Result()
    result = development._database_identity(Database())
    assert "pg_catalog.pg_control_system()" in captured[0]
    assert result["database_cluster_id"] == "1234567890123456789"


@pytest.fixture
def native_mount_fixture(tmp_path, monkeypatch):
    original_fstat = os.fstat
    def root_metadata(fd):
        value = list(original_fstat(fd))
        value[4] = 0
        return os.stat_result(value)
    # Explicit native metadata mocks; no test claims that tmp_path is a real root
    # deployment mount. Actual O_NOFOLLOW, file modes and hardlinks still execute.
    monkeypatch.setattr(development.os, "fstat", root_metadata)
    monkeypatch.setattr(development, "_readonly", lambda _fd: True)
    monkeypatch.setattr(development, "RUNTIME_DIRECTORY", tmp_path)
    def mounts():
        return ("1 0 0:1 / / ro - overlay overlay ro\n"
                f"2 1 8:1 /etc/mihur-staging/development-owner {tmp_path} ro - ext4 /dev/sda1 rw\n"
                f"3 1 8:1 /etc/machine-id {development.HOST_MACHINE_ID} ro - ext4 /dev/sda1 rw\n")
    monkeypatch.setattr(development, "_kernel_mounts", mounts)
    tmp_path.chmod(0o755)
    for name in ("policy.json", "context.json", "grant.json"):
        path = tmp_path / name
        path.write_bytes(owner.canonical({"synthetic": name}))
        path.chmod(0o644)
    for name, data in (("authorization.json", b"{}"), ("authorization.sig", b"fixture-only")):
        path = tmp_path / name
        path.write_bytes(data)
        path.chmod(0o644)
    return tmp_path


def test_image_baked_readonly_owner_proof_cannot_activate_solo_policy(
    db, development_state, native_mount_fixture, monkeypatch,
):
    # All proof bytes and root/RO file properties can be attacker-baked into an
    # image, including a signature under the attacker's own policy key. The real
    # reader/parser must reject the missing native host bind mounts first.
    for name, key in (("policy.json", "policy"), ("context.json", "context"), ("grant.json", "grant")):
        (native_mount_fixture / name).write_bytes(owner.canonical(development_state[key]))
    (native_mount_fixture / "authorization.json").write_bytes(development_state["envelope"])
    (native_mount_fixture / "authorization.sig").write_bytes(development_state["signature"])
    monkeypatch.setattr(development, "_load_runtime_state", _REAL_LOAD_RUNTIME_STATE)
    monkeypatch.setattr(development, "_kernel_mounts", lambda: "1 0 0:1 / / ro - overlay overlay ro\n")
    with pytest.raises(publisher.PublicationBlocked):
        publisher.authorize_package(development_state["manifest"], db)


@pytest.mark.parametrize("change", ["missing_owner", "missing_machine", "wrong_root", "anonymous_volume",
                                   "writable", "tmpfs", "nested_overmount", "duplicate"])
def test_real_reader_requires_exact_kernel_host_mounts(native_mount_fixture, monkeypatch, change):
    lines = development._kernel_mounts().splitlines()
    if change == "missing_owner":
        lines.pop(1)
    elif change == "missing_machine":
        lines.pop(2)
    elif change == "wrong_root":
        lines[1] = lines[1].replace("/etc/mihur-staging/development-owner", "/image-fake-owner")
    elif change == "anonymous_volume":
        lines[1] = lines[1].replace("/etc/mihur-staging/development-owner", "/var/lib/docker/volumes/anon/_data")
    elif change == "writable":
        lines[1] = lines[1].replace(" ro - ext4", " rw - ext4")
    elif change == "tmpfs":
        lines[1] = lines[1].replace("- ext4", "- tmpfs")
    elif change == "duplicate":
        lines.append(lines[1])
    else:
        lines.append(f"4 2 8:1 /image-fake-owner {native_mount_fixture}/policy.json ro - ext4 /dev/sda1 rw")
    monkeypatch.setattr(development, "_kernel_mounts", lambda: "\n".join(lines) + "\n")
    with pytest.raises(owner.AuthorizationRejected):
        development._load_runtime_state()


def test_mountinfo_image_lookalike_is_not_accepted_as_kernel_procfs(tmp_path, monkeypatch):
    fake = tmp_path / "baked-mountinfo"
    fake.write_text("1 0 0:1 / / ro - overlay overlay ro\n")
    original_open = os.open
    def open_image_lookalike(path, flags, *args, **kwargs):
        return original_open(fake if path == "/proc/self/mountinfo" else path, flags, *args, **kwargs)
    monkeypatch.setattr(development.os, "open", open_image_lookalike)
    with pytest.raises(owner.AuthorizationRejected, match="not_procfs"):
        development._kernel_mounts()


def test_reader_rejects_non_readonly_or_malformed_mount(native_mount_fixture, monkeypatch):
    assert len(development._load_runtime_state()) == 5
    monkeypatch.setattr(development, "_readonly", lambda _fd: False)
    with pytest.raises(owner.AuthorizationRejected, match="readonly"):
        development._load_runtime_state()


@pytest.mark.parametrize("change", ["missing", "symlink", "hardlink", "writable", "duplicate_json"])
def test_reader_fails_closed_for_partial_or_mutable_state(native_mount_fixture, change):
    directory = native_mount_fixture
    path = directory / "grant.json"
    if change == "missing":
        path.unlink()
    elif change == "symlink":
        path.unlink()
        path.symlink_to(directory / "context.json")
    elif change == "hardlink":
        path.unlink()
        os.link(directory / "context.json", path)
    elif change == "writable":
        path.chmod(0o666)
    else:
        path.write_bytes(b'{"state":"ACTIVE","state":"ACTIVE"}')
    with pytest.raises((owner.AuthorizationRejected, OSError)):
        development._load_runtime_state()


def test_reader_rejects_symlinked_runtime_directory(native_mount_fixture, monkeypatch):
    link = native_mount_fixture.parent / "runtime-directory-link"
    link.symlink_to(native_mount_fixture, target_is_directory=True)
    monkeypatch.setattr(development, "RUNTIME_DIRECTORY", link)
    assert development.configured() is True
    with pytest.raises((owner.AuthorizationRejected, OSError)):
        development._load_runtime_state()


def test_reader_rejects_unprotected_directory(native_mount_fixture):
    native_mount_fixture.chmod(0o777)
    with pytest.raises(owner.AuthorizationRejected):
        development._load_runtime_state()


def test_mode_detection_rejects_partial_machine_mount(tmp_path, monkeypatch):
    monkeypatch.setattr(development, "RUNTIME_DIRECTORY", tmp_path / "missing")
    machine = tmp_path / "machine-id"
    monkeypatch.setattr(development, "HOST_MACHINE_ID", machine)
    assert development.configured() is False
    machine.write_text("a" * 32)
    with pytest.raises(owner.AuthorizationRejected, match="incomplete"):
        development.configured()


def test_machine_identity_is_native_stripped_machine_id_hash(native_mount_fixture, monkeypatch):
    machine = native_mount_fixture / "machine-id"
    machine.write_text("a" * 32 + "\n")
    machine.chmod(0o444)
    monkeypatch.setattr(development, "HOST_MACHINE_ID", machine)
    assert development._machine_identity() == hashlib.sha256(("a" * 32).encode()).hexdigest()
    machine.chmod(0o666)
    with pytest.raises(owner.AuthorizationRejected):
        development._machine_identity()
