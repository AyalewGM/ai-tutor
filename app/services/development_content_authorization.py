"""Revocable development-only package permission from a protected native receipt.

This module verifies the original detached owner proof on every package access,
without subprocesses or operation nonce consumption. Kernel host-mount admission
and capability separation are prerequisites; image-baked root-owned files do not
provide that admission. APP_ENV and DSN assertions never select authorization.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
import hmac
import os
import re
import stat
import struct
import sys
import time
from pathlib import Path

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from scripts.ops import development_release_authorization as owner

RUNTIME_DIRECTORY = Path("/run/mihur/development-owner")
HOST_MACHINE_ID = Path("/run/mihur/host-machine-id")
HOST_OWNER_SOURCE = "/etc/mihur-staging/development-owner"
HOST_MACHINE_SOURCE = "/etc/machine-id"
PROC_SUPER_MAGIC = 0x9FA0
GRANT_SCHEMA = "MIHUR_DEVELOPMENT_RUNTIME_GRANT_V1"
GRANT_FIELDS = frozenset({"schema", "state", "policy_sha256", "authorization_sha256",
                          "nonce", "verified_at", "runtime_expires_at", "owner_runtime_expires_at", "release"})


def configured():
    """Only fixed native mounts select this mode; malformed/partial state denies."""
    try:
        RUNTIME_DIRECTORY.lstat()
        return True
    except FileNotFoundError:
        try:
            HOST_MACHINE_ID.lstat()
        except FileNotFoundError:
            return False
        raise owner.AuthorizationRejected("development_runtime_incomplete") from None


def _readonly(fd):
    return bool(os.fstatvfs(fd).f_flag & os.ST_RDONLY)


def _kernel_mounts():
    """Read genuine procfs, not an image-provided /proc lookalike."""
    owner.require(sys.platform == "linux" and os.uname().machine == "x86_64"
                  and ctypes.sizeof(ctypes.c_long) == 8,
                  "unsupported_runtime_mount_platform")
    fd = os.open("/proc/self/mountinfo", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        library = ctypes.CDLL(None, use_errno=True)
        fstatfs = library.fstatfs
        fstatfs.argtypes = [ctypes.c_int, ctypes.c_void_p]
        fstatfs.restype = ctypes.c_int
        buffer = ctypes.create_string_buffer(256)
        owner.require(fstatfs(fd, buffer) == 0
                      and ctypes.c_long.from_buffer(buffer).value == PROC_SUPER_MAGIC,
                      "runtime_mountinfo_not_procfs")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(262145)
        owner.require(len(data) <= 262144, "runtime_mountinfo_size")
        return data.decode("utf-8")
    finally:
        os.close(fd)


def _require_host_mounts():
    expected = {str(RUNTIME_DIRECTORY): HOST_OWNER_SOURCE,
                str(HOST_MACHINE_ID): HOST_MACHINE_SOURCE}
    seen = set()
    for line in _kernel_mounts().splitlines():
        parts = line.split(" - ")
        owner.require(len(parts) == 2, "runtime_mountinfo_format")
        before, after = parts[0].split(), parts[1].split()
        owner.require(len(before) >= 6 and len(after) >= 3, "runtime_mountinfo_format")
        root, target, flags = before[3], before[4], set(before[5].split(","))
        if target.startswith(str(RUNTIME_DIRECTORY) + "/"):
            raise owner.AuthorizationRejected("runtime_nested_mount_not_allowed")
        if target not in expected:
            continue
        owner.require(target not in seen and root == expected[target]
                      and "ro" in flags and "rw" not in flags
                      and after[0] in {"ext4", "xfs"}, "runtime_host_mount_not_admitted")
        seen.add(target)
    owner.require(seen == set(expected), "runtime_host_mount_missing")


def _bytes_at(directory, name, maximum=owner.MAX_BYTES):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        owner.require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
                      and stat.S_IMODE(info.st_mode) in (0o600, 0o644),
                      "untrusted_development_runtime_file")
        owner.require(_readonly(stream.fileno()), "development_runtime_mount_not_readonly")
        data = stream.read(maximum + 1)
        owner.require(0 < len(data) <= maximum, "development_runtime_file_size")
        return data


def _load_runtime_state():
    _require_host_mounts()
    directory = owner._trusted_directory(RUNTIME_DIRECTORY)
    try:
        owner.require(stat.S_IMODE(os.fstat(directory).st_mode) == 0o755,
                      "untrusted_development_runtime_directory")
        owner.require(_readonly(directory), "development_runtime_mount_not_readonly")
        records = tuple(owner.strict_json(_bytes_at(directory, name))
                        for name in ("policy.json", "context.json", "grant.json"))
        return (*records, _bytes_at(directory, "authorization.json"),
                _bytes_at(directory, "authorization.sig", 8192))
    finally:
        os.close(directory)


class _SSHReader:
    """Bounded SSH wire reader for the sole supported Ed25519 SSHSIG v1 form."""
    def __init__(self, data):
        self.data, self.offset = data, 0

    def uint32(self):
        owner.require(self.offset + 4 <= len(self.data), "development_owner_signature_format")
        value = struct.unpack_from(">I", self.data, self.offset)[0]
        self.offset += 4
        return value

    def string(self):
        size = self.uint32()
        owner.require(size <= 8192 and self.offset + size <= len(self.data),
                      "development_owner_signature_format")
        value = self.data[self.offset:self.offset + size]
        self.offset += size
        return value

    def done(self):
        owner.require(self.offset == len(self.data), "development_owner_signature_trailing")


def _ssh_string(value):
    return struct.pack(">I", len(value)) + value


def _verify_owner_signature(envelope, signature, public_key):
    """OpenSSH PROTOCOL.sshsig, only pinned raw ssh-ed25519; no native execution."""
    try:
        owner.require(isinstance(envelope, bytes) and len(envelope) <= owner.MAX_BYTES
                      and isinstance(signature, bytes) and len(signature) <= 8192,
                      "development_owner_signature_size")
        armor = re.fullmatch(
            rb"-----BEGIN SSH SIGNATURE-----\n((?:[A-Za-z0-9+/]+={0,2}\n)+)"
            rb"-----END SSH SIGNATURE-----(?:\n)?", signature)
        owner.require(armor is not None, "development_owner_signature_armor")
        encoded = b"".join(armor[1].splitlines())
        raw = base64.b64decode(encoded, validate=True)
        owner.require(base64.b64encode(raw) == encoded and raw[:6] == b"SSHSIG",
                      "development_owner_signature_format")
        record = _SSHReader(raw[6:])
        owner.require(record.uint32() == 1, "development_owner_signature_version")
        key_blob, namespace, reserved = record.string(), record.string(), record.string()
        algorithm, signature_blob = record.string(), record.string()
        record.done()
        expected_blob = base64.b64decode(public_key.split()[1], validate=True)
        owner.require(hmac.compare_digest(key_blob, expected_blob)
                      and namespace == owner.NAMESPACE.encode() and reserved == b""
                      and algorithm in (b"sha256", b"sha512"),
                      "development_owner_signature_subject")
        key = _SSHReader(expected_blob)
        owner.require(key.string() == b"ssh-ed25519", "development_owner_key_type")
        public_bytes = key.string()
        key.done()
        owner.require(len(public_bytes) == 32, "development_owner_key_size")
        proof = _SSHReader(signature_blob)
        owner.require(proof.string() == b"ssh-ed25519", "development_owner_signature_type")
        signature_bytes = proof.string()
        proof.done()
        owner.require(len(signature_bytes) == 64, "development_owner_signature_size")
        message_digest = (hashlib.sha256(envelope).digest() if algorithm == b"sha256"
                          else hashlib.sha512(envelope).digest())
        message = (b"SSHSIG" + _ssh_string(namespace) + _ssh_string(reserved)
                   + _ssh_string(algorithm) + _ssh_string(message_digest))
        Ed25519PublicKey.from_public_bytes(public_bytes).verify(signature_bytes, message)
    except (ValueError, TypeError, IndexError, InvalidSignature, UnsupportedAlgorithm, struct.error):
        raise owner.AuthorizationRejected("development_owner_signature_invalid") from None


def _verify_signed_grant(policy, context, grant, envelope, signature):
    payload = owner.strict_json(envelope)
    owner.require(set(payload) == owner.AUTH_FIELDS and payload["schema"] == owner.AUTH_SCHEMA
                  and payload["namespace"] == owner.NAMESPACE,
                  "development_signed_authorization_fields")
    owner._scope(payload)
    owner.require(all(payload[key] == context[key] for key in owner.BINDINGS)
                  and payload["policy_sha256"] == owner.digest(policy)
                  and grant["authorization_sha256"] == hashlib.sha256(envelope).hexdigest()
                  and grant["nonce"] == payload["nonce"], "development_signed_authorization_subject")
    issued, operation_expires = payload["issued_at"], payload["expires_at"]
    runtime_expires, verified = payload["runtime_expires_at"], grant["verified_at"]
    owner.require(type(issued) is int and type(operation_expires) is int
                  and type(runtime_expires) is int and type(verified) is int
                  and 0 <= issued <= verified < operation_expires <= runtime_expires
                  and 0 < operation_expires - issued <= policy["max_age_seconds"]
                  and runtime_expires <= issued + policy["max_runtime_seconds"]
                  and runtime_expires == grant["owner_runtime_expires_at"],
                  "development_signed_runtime_lifetime")
    _verify_owner_signature(envelope, signature, policy["owner_public_key"])


def _machine_identity():
    directory = owner._trusted_directory(HOST_MACHINE_ID.parent)
    try:
        fd = os.open(HOST_MACHINE_ID.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            owner.require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
                          and stat.S_IMODE(info.st_mode) in (0o444, 0o600, 0o644)
                          and _readonly(stream.fileno()), "untrusted_development_machine_identity")
            value = stream.read(257)
            owner.require(len(value) <= 256, "development_machine_identity_size")
            machine_id = value.decode("utf-8").strip()
            owner.require(re.fullmatch(r"[a-f0-9]{32}", machine_id), "development_machine_identity")
            return hashlib.sha256(machine_id.encode("utf-8")).hexdigest()
    finally:
        os.close(directory)


def _database_identity(db):
    owner.require(db is not None and db.get_bind().dialect.name == "postgresql",
                  "development_postgresql_identity_required")
    try:
        row = db.execute(text(
            "SELECT pg_catalog.current_database() AS database, current_user AS database_role, "
            "system_identifier::text AS database_cluster_id FROM pg_catalog.pg_control_system()"
        )).mappings().one()
        return {key: row[key] for key in ("database", "database_role", "database_cluster_id")}
    except (SQLAlchemyError, KeyError, ValueError, TypeError):
        raise owner.AuthorizationRejected("development_database_identity_unavailable") from None


def authorize(manifest, package_digest, current_runtime_digest, db, *, now=None):
    """Read and revalidate every time; never consume a deployment/publication nonce."""
    policy, context, grant, envelope, signature = _load_runtime_state()
    owner.validate_policy(policy)
    owner.require(type(context) is dict and set(context) == owner.BINDINGS,
                  "development_context_fields")
    owner._scope(context)
    owner.require(type(grant) is dict and set(grant) == GRANT_FIELDS, "development_grant_fields")
    owner.require(grant["schema"] == GRANT_SCHEMA and grant["state"] == "ACTIVE",
                  "development_grant_not_active")
    owner.require(grant["policy_sha256"] == owner.digest(policy), "development_policy_changed")
    owner.require(grant["release"] == context, "development_grant_subject_changed")
    owner.require(owner._hex(grant["authorization_sha256"], 64)
                  and owner._hex(grant["nonce"], 64), "development_grant_provenance")
    owner.require(owner._hex(context["source_sha"], 40) and owner._hex(context["source_tree"], 40)
                  and owner._hex(context["evidence_sha256"], 64), "development_release_identity")
    images = context["images"]
    owner.require(type(images) is dict and set(images) == owner.IMAGE_KEYS
                  and all(isinstance(value, str) and re.fullmatch(
                      r"[a-z0-9./_-]+@sha256:[a-f0-9]{64}", value) for value in images.values()),
                  "development_image_identity")
    actions = context["actions"]
    owner.require(type(actions) is list and tuple(actions) in owner.ACTION_PLANS
                  and "publish" in actions, "development_package_not_authorized_for_publication")
    now = int(time.time()) if now is None else now
    verified, expires = grant["verified_at"], grant["runtime_expires_at"]
    owner_expires = grant["owner_runtime_expires_at"]
    owner.require(type(now) is int and type(verified) is int and type(expires) is int
                  and type(owner_expires) is int
                  and 0 <= verified <= now < expires <= owner_expires
                  <= verified + policy["max_runtime_seconds"],
                  "development_runtime_authorization_expired")
    _verify_signed_grant(policy, context, grant, envelope, signature)
    owner.require(context["package_sha256"] == package_digest
                  and context["runtime_sha256"] == current_runtime_digest,
                  "development_package_or_runtime_changed")
    owner.require(context["host_sha256"] == _machine_identity(), "development_host_changed")
    cluster = context["database_cluster_id"]
    owner.require(isinstance(cluster, str) and re.fullmatch(r"[1-9][0-9]{0,19}", cluster)
                  and int(cluster) < 2**64, "development_cluster_identity")
    owner.require(db is not None, "development_database_handle_required")
    actual = _database_identity(db)
    owner.require(actual == {key: context[key] for key in (
        "database", "database_role", "database_cluster_id")}, "development_database_changed")
    # Package activation/standards are checked by the existing publisher wrapper,
    # before this function. These explicit fields prevent a forged mixed policy.
    owner.require(manifest["activation"] == "staging" and manifest["review_evidence"] == [],
                  "development_package_disposition")
    return package_digest
