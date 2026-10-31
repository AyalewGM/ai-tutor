"""Detached owner authorization for fixed development-only release entrypoints.

The native operator collects its own context and reserves before effects.
Runtime package permission is separate and never consumes an operation nonce.
Pure verification does not authenticate caller-supplied context or agent provenance.
"""
from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

NAMESPACE = "mihur-development-owner-release-v1"
POLICY_SCHEMA = "MIHUR_DEVELOPMENT_OWNER_POLICY_V1"
AUTH_SCHEMA = "MIHUR_DEVELOPMENT_OWNER_AUTHORIZATION_V1"
EVIDENCE_SCHEMA = "MIHUR_CODEX_TECHNICAL_EVIDENCE_V1"
ROLES = frozenset({"math", "pedagogy", "standards", "security", "qa"})
POLICY_PATH = Path("/etc/mihur-staging/development-owner/policy.json")
CONTEXT_PATH = Path("/etc/mihur-staging/development-owner/context.json")
REPOSITORY = "AyalewGM/ai-tutor"
REPOSITORY_ID = 1367979340
OWNER_ID = 22088298
HOST = "3ee0437dd6184c8f150d0530093391fe7499cce86999f3c1a2e67dc0daec1c4b"
SCOPE = {"repository": REPOSITORY, "repository_id": REPOSITORY_ID, "owner_id": OWNER_ID,
         "environment": "development", "host_sha256": HOST,
         "application_url": "https://dev.mihureducation.com", "database": "mihur_staging",
         "database_role": "mihur_staging"}
BINDINGS = frozenset(SCOPE) | {"source_sha", "source_tree", "package_sha256", "runtime_sha256",
                                    "images", "evidence_sha256", "actions", "database_cluster_id"}
POLICY_FIELDS = frozenset(SCOPE) | {"schema", "owner_public_key", "revoked", "max_age_seconds",
                                           "max_runtime_seconds", "operator_pins_sha256"}
AUTH_FIELDS = BINDINGS | {"schema", "namespace", "policy_sha256", "issued_at", "expires_at",
                          "runtime_expires_at", "nonce"}
IMAGE_KEYS = frozenset({"api", "gateway", "frontend", "db", "redis", "proxy"})
ACTION_PLANS = (("deploy",), ("publish",), ("deploy", "publish"), ("rollback",))
MAX_BYTES = 65536


class AuthorizationRejected(ValueError):
    """Safe fixed rejection code; never interpolate payloads or native stderr."""


def require(condition, code):
    if not condition:
        raise AuthorizationRejected(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    require(isinstance(data, bytes) and len(data) <= MAX_BYTES, "json_size_or_type")
    try:
        value = json.loads(data, object_pairs_hook=pairs,
                           parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
        require(type(value) is dict and canonical(value) == data, "noncanonical_json")
        return value
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        if isinstance(exc, AuthorizationRejected):
            raise
        raise AuthorizationRejected("invalid_json") from None


def _hex(value, length):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{" + str(length) + "}", value)


def _scope(value):
    for key, expected in SCOPE.items():
        require(type(value.get(key)) is type(expected) and value[key] == expected,
                "development_scope_mismatch")


def validate_policy(policy):
    require(type(policy) is dict and set(policy) == POLICY_FIELDS, "policy_fields")
    _scope(policy)
    require(_hex(policy["operator_pins_sha256"], 64), "operator_pins_digest")
    require(policy["schema"] == POLICY_SCHEMA and policy["revoked"] is False, "policy_revoked")
    require(type(policy["max_age_seconds"]) is int and 1 <= policy["max_age_seconds"] <= 3600,
            "policy_lifetime")
    require(type(policy["max_runtime_seconds"]) is int
            and 1 <= policy["max_runtime_seconds"] <= 604800, "policy_runtime_lifetime")
    key = policy["owner_public_key"]
    require(isinstance(key, str) and re.fullmatch(r"ssh-ed25519 [A-Za-z0-9+/]+={0,2}", key),
            "owner_public_key")
    try:
        require(len(base64.b64decode(key.split()[1], validate=True)) == 51, "owner_public_key")
    except ValueError:
        raise AuthorizationRejected("owner_public_key") from None


def validate_evidence(bundle, artifacts, payload):
    require(type(artifacts) is dict, "review_artifacts_type")
    require(type(bundle) is dict and set(bundle) == {
        "schema", "source_sha", "package_sha256", "author_sessions", "reviews"}, "evidence_fields")
    require(bundle["schema"] == EVIDENCE_SCHEMA and bundle["source_sha"] == payload["source_sha"]
            and bundle["package_sha256"] == payload["package_sha256"], "evidence_subject")
    authors = bundle["author_sessions"]
    require(type(authors) is list and authors and all(isinstance(v, str) and v for v in authors)
            and len(set(authors)) == len(authors), "evidence_authors")
    reviews = bundle["reviews"]
    require(type(reviews) is list and len(reviews) == len(ROLES), "missing_technical_review")
    covered, sessions = set(), set()
    for review in reviews:
        require(type(review) is dict and set(review) == {
            "role", "session_id", "verdict", "artifact_sha256"}, "review_fields")
        role, session = review["role"], review["session_id"]
        require(isinstance(role, str) and role in ROLES and role not in covered,
                "duplicate_or_unknown_review")
        require(isinstance(session, str) and session and session not in sessions
                and session not in authors, "review_session_conflict")
        require(review["verdict"] in ("ACCEPT", "ACCEPT_BOUNDED"), "technical_review_rejected")
        sha = review["artifact_sha256"]
        require(_hex(sha, 64) and isinstance(artifacts.get(sha), bytes)
                and 0 < len(artifacts[sha]) <= MAX_BYTES
                and hashlib.sha256(artifacts[sha]).hexdigest() == sha, "review_artifact_mismatch")
        covered.add(role)
        sessions.add(session)
    require(covered == ROLES and digest(bundle) == payload["evidence_sha256"], "evidence_mismatch")
    # Completeness/integrity, not proof that a session actually ran independently.


@dataclass(frozen=True)
class VerifiedAuthorization:
    payload_sha256: str
    nonce: str
    expires_at: int
    runtime_expires_at: int


def verify(envelope, signature, policy, expected_context, bundle, artifacts, *, now=None):
    """Verify data against a separately trusted context; never perform an action.

    An attacker can call this pure function with their own key/context. That call
    has no authority. Only a capability-isolated operator may supply live policy
    and native context, fresh authenticated CI evidence and the owner trust anchor.
    """
    payload = strict_json(envelope)
    validate_policy(policy)
    require(set(payload) == AUTH_FIELDS, "authorization_fields")
    require(payload["schema"] == AUTH_SCHEMA and payload["namespace"] == NAMESPACE,
            "authorization_namespace")
    _scope(payload)
    require(type(expected_context) is dict and set(expected_context) == BINDINGS,
            "trusted_context_fields")
    _scope(expected_context)
    require(all(payload[key] == expected_context[key] for key in BINDINGS), "release_subject_changed")
    require(payload["policy_sha256"] == digest(policy), "policy_changed")
    require(_hex(payload["source_sha"], 40) and _hex(payload["source_tree"], 40), "source_sha")
    cluster = payload["database_cluster_id"]
    require(isinstance(cluster, str) and re.fullmatch(r"[1-9][0-9]{0,19}", cluster)
            and int(cluster) < 2**64, "database_cluster_id")
    for key in ("package_sha256", "runtime_sha256", "evidence_sha256", "policy_sha256", "nonce"):
        require(_hex(payload[key], 64), "digest_or_nonce")
    images = payload["images"]
    require(type(images) is dict and set(images) == IMAGE_KEYS, "image_fields")
    require(all(isinstance(v, str) and re.fullmatch(
        r"[a-z0-9./_-]+@sha256:[a-f0-9]{64}", v) for v in images.values()), "immutable_images")
    actions = payload["actions"]
    require(type(actions) is list and tuple(actions) in ACTION_PLANS, "action_plan")
    now = int(time.time()) if now is None else now
    issued, expires = payload["issued_at"], payload["expires_at"]
    require(type(now) is int and type(issued) is int and type(expires) is int
            and issued <= now < expires and 0 < expires - issued <= policy["max_age_seconds"],
            "authorization_time")
    runtime_expires = payload["runtime_expires_at"]
    require(type(runtime_expires) is int and expires <= runtime_expires
            <= issued + policy["max_runtime_seconds"], "runtime_authorization_time")
    validate_evidence(bundle, artifacts, payload)
    require(isinstance(signature, bytes) and 0 < len(signature) <= 8192, "signature_missing")
    trusted_tmp = _trusted_directory(Path("/tmp"), owner_uid=0)
    os.close(trusted_tmp)
    with tempfile.TemporaryDirectory(prefix="mihur-owner-verify-", dir="/tmp") as directory:
        directory = Path(directory)
        allowed = directory / "allowed_signers"
        allowed.write_text(f'owner-{OWNER_ID} namespaces="{NAMESPACE}" '
                           + policy["owner_public_key"] + "\n")
        sig = directory / "owner.sig"
        sig.write_bytes(signature)
        try:
            result = subprocess.run(
                ["/usr/bin/ssh-keygen", "-Y", "verify", "-f", str(allowed),
                 "-I", f"owner-{OWNER_ID}", "-n", NAMESPACE, "-s", str(sig)],
                input=envelope, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=False, timeout=10,
                env={"PATH": "/usr/bin:/bin", "HOME": str(directory), "LANG": "C"})
            require(result.returncode == 0, "owner_signature_invalid")
        except (OSError, subprocess.TimeoutExpired):
            raise AuthorizationRejected("owner_signature_unavailable") from None
    return VerifiedAuthorization(hashlib.sha256(envelope).hexdigest(), payload["nonce"],
                                 expires, runtime_expires)


def _trusted_directory(path, *, owner_uid=0, private=False):
    """Pin directory descriptors and reject symlinks and writable ancestors."""
    path = Path(path)
    require(path.is_absolute(), "absolute_trust_path_required")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in path.parts[1:]:
            require(component not in (".", ".."), "unsafe_path_component")
            nxt = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
            info = os.fstat(fd)
            sticky_root = info.st_uid == 0 and stat.S_IMODE(info.st_mode) == 0o1777
            require(info.st_uid in (0, owner_uid) and
                    (not info.st_mode & 0o022 or sticky_root), "untrusted_path_ancestor")
        info = os.fstat(fd)
        require(info.st_uid == owner_uid and (not private or stat.S_IMODE(info.st_mode) == 0o700),
                "untrusted_directory")
        return fd
    except Exception:
        os.close(fd)
        raise


def protected_json(path, *, owner_uid=0):
    path = Path(path)
    parent = _trusted_directory(path.parent, owner_uid=owner_uid)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == owner_uid and info.st_nlink == 1
                    and stat.S_IMODE(info.st_mode) in (0o600, 0o644), "untrusted_policy_file")
            return strict_json(stream.read(MAX_BYTES + 1))
    finally:
        os.close(parent)


def reserve_nonce(authorization, state_directory, *, owner_uid=0, now=None):
    """Native trusted adapter only: reserve before FIRST effect; never undo.

    A process crash, partial write or uncertain operation burns this nonce.
    Ordinary runtime package checks must not call this operation primitive.
    owner_uid is a fixture hook; the live verify-only CLI never exposes it.
    """
    require(type(authorization) is VerifiedAuthorization and _hex(authorization.nonce, 64)
            and _hex(authorization.payload_sha256, 64), "unverified_reservation")
    now = int(time.time()) if now is None else now
    require(type(now) is int and now < authorization.expires_at, "reservation_expired")
    directory = _trusted_directory(state_directory, owner_uid=owner_uid, private=True)
    try:
        fcntl.flock(directory, fcntl.LOCK_EX)
        try:
            fd = os.open(authorization.nonce + ".json",
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600,
                         dir_fd=directory)
        except FileExistsError:
            raise AuthorizationRejected("authorization_already_reserved") from None
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical({"status": "RESERVED_NO_AUTOMATIC_RETRY",
                                    "payload_sha256": authorization.payload_sha256}))
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(directory)
    finally:
        os.close(directory)


def _input(path, limit=MAX_BYTES):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "input_not_regular")
        data = stream.read(limit + 1)
        require(len(data) <= limit, "input_too_large")
        return data


def main():
    parser = argparse.ArgumentParser(description="Verify-only; no release effects")
    for name in ("envelope", "signature", "evidence", "artifacts"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    require(os.geteuid() == 0, "trusted_operator_required")
    policy = protected_json(POLICY_PATH)
    context = protected_json(CONTEXT_PATH)
    envelope = _input(args.envelope)
    bundle = strict_json(_input(args.evidence))
    artifacts = {}
    for review in bundle.get("reviews", []):
        sha = review.get("artifact_sha256") if type(review) is dict else None
        require(_hex(sha, 64), "review_artifact_name")
        artifacts[sha] = _input(Path(args.artifacts) / (sha + ".txt"))
    verify(envelope, _input(args.signature, 8192), policy, context, bundle, artifacts)
    print(json.dumps({"status": "VERIFIED_ONLY", "deployment_performed": False,
                      "publication_performed": False, "nonce_reserved": False}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - never expose native output or payload values
        reason = str(exc) if isinstance(exc, AuthorizationRejected) else "verification_failed"
        print(json.dumps({"status": "REJECTED", "reason": reason}), file=__import__("sys").stderr)
        raise SystemExit(1) from None
