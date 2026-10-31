"""Disposable fixture keys only; these signatures are NOT release authorization."""
from __future__ import annotations

import copy
import hashlib
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ops import development_release_authorization as auth


class DevelopmentOwnerAuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix="synthetic-owner-governance-")
        cls.root = Path(cls.scratch.name)
        cls.key = cls.root / "FIXTURE_ONLY_NEVER_ENROLL"
        subprocess.run(["/usr/bin/ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(cls.key)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.public = " ".join(cls.key.with_suffix(".pub").read_text().split()[:2])

    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()

    def setUp(self):
        self.policy = {**auth.SCOPE, "schema": auth.POLICY_SCHEMA,
                       "owner_public_key": self.public, "revoked": False, "max_age_seconds": 3600,
                       "max_runtime_seconds": 86400, "operator_pins_sha256": "1" * 64}
        self.bundle = {"schema": auth.EVIDENCE_SCHEMA, "source_sha": "a" * 40,
                       "package_sha256": "b" * 64, "author_sessions": ["fixture-author"],
                       "reviews": []}
        self.artifacts = {}
        for role in sorted(auth.ROLES):
            artifact = ("FIXTURE ONLY; NOT A REAL REVIEW: " + role).encode()
            sha = hashlib.sha256(artifact).hexdigest()
            self.artifacts[sha] = artifact
            self.bundle["reviews"].append({"role": role, "session_id": "fixture-" + role,
                                           "verdict": "ACCEPT_BOUNDED", "artifact_sha256": sha})
        self.context = {**auth.SCOPE, "source_sha": "a" * 40, "source_tree": "c" * 40,
                        "package_sha256": "b" * 64, "runtime_sha256": "d" * 64,
                        "evidence_sha256": auth.digest(self.bundle), "actions": ["deploy", "publish"],
                        "database_cluster_id": "1234567890123456789",
                        "images": {key: "example.invalid/fixture-" + key + "@sha256:" + "e" * 64
                                   for key in auth.IMAGE_KEYS}}
        self.payload = {**self.context, "schema": auth.AUTH_SCHEMA, "namespace": auth.NAMESPACE,
                        "policy_sha256": auth.digest(self.policy), "issued_at": 1000,
                        "expires_at": 2000, "runtime_expires_at": 3000, "nonce": "f" * 64}

    def sign(self, payload=None, namespace=None, key=None):
        data = auth.canonical(self.payload if payload is None else payload)
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            path = Path(directory) / "fixture-payload"
            path.write_bytes(data)
            subprocess.run(["/usr/bin/ssh-keygen", "-Y", "sign", "-f", str(self.key if key is None else key),
                            "-n", namespace or auth.NAMESPACE, str(path)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return data, Path(str(path) + ".sig").read_bytes()

    def verify(self, *, payload=None, signature=None, policy=None, context=None,
               bundle=None, artifacts=None, now=1500):
        data, valid_signature = self.sign(payload)
        return auth.verify(data, valid_signature if signature is None else signature,
                           self.policy if policy is None else policy,
                           self.context if context is None else context,
                           self.bundle if bundle is None else bundle,
                           self.artifacts if artifacts is None else artifacts, now=now)

    def test_valid_detached_signature_is_verification_only(self):
        result = self.verify()
        self.assertEqual(result.nonce, self.payload["nonce"])
        self.assertEqual(result.payload_sha256, auth.digest(self.payload))
        self.assertEqual(set(self.root.iterdir()), {self.key, self.key.with_suffix(".pub")})

    def test_attacker_tmpdir_is_not_used_for_signature_verification(self):
        implementation = tempfile.TemporaryDirectory
        with (
            patch.dict(os.environ, {"TMPDIR": "/attacker-controlled-nonexistent"}),
            patch.object(auth.tempfile, "TemporaryDirectory", wraps=implementation) as scratch,
        ):
            self.verify()
            calls = [call for call in scratch.call_args_list
                     if call.kwargs.get("prefix") == "mihur-owner-verify-"]
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0].kwargs["dir"], "/tmp")

    def test_missing_invalid_wrong_namespace_and_tampered_signature_rejected(self):
        for signature in (b"", b"not a signature", self.sign(namespace="production")[1]):
            with self.subTest(signature_kind=len(signature)), self.assertRaises(auth.AuthorizationRejected):
                self.verify(signature=signature)
        data, signature = self.sign()
        changed = dict(self.payload, issued_at=1001)
        with self.assertRaisesRegex(auth.AuthorizationRejected, "owner_signature_invalid"):
            auth.verify(auth.canonical(changed), signature, self.policy, self.context,
                        self.bundle, self.artifacts, now=1500)
        self.assertNotEqual(data, auth.canonical(changed))

    def test_valid_signature_from_another_real_fixture_key_is_not_owner_authorization(self):
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            unauthorized_key = Path(directory) / "UNAUTHORIZED_FIXTURE_ONLY"
            subprocess.run(["/usr/bin/ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f",
                            str(unauthorized_key)], check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            data, signature = self.sign(key=unauthorized_key)
            with self.assertRaisesRegex(auth.AuthorizationRejected, "owner_signature_invalid"):
                auth.verify(data, signature, self.policy, self.context, self.bundle,
                            self.artifacts, now=1500)

    def test_changed_exact_subject_rejected_even_with_valid_owner_fixture_signature(self):
        changes = {"source_sha": "1" * 40, "source_tree": "2" * 40,
                   "package_sha256": "3" * 64, "runtime_sha256": "4" * 64,
                   "evidence_sha256": "5" * 64, "host_sha256": "6" * 64,
                   "repository_id": 1, "owner_id": 1, "application_url": "https://production.invalid",
                   "database": "production", "database_role": "production",
                   "database_cluster_id": "9876543210123456789", "environment": "production",
                   "actions": ["publish", "deploy"], "images": {}}
        for key, value in changes.items():
            with self.subTest(field=key), self.assertRaises(auth.AuthorizationRejected):
                self.verify(payload={**self.payload, key: value})

    def test_production_scope_rejected_even_when_expected_context_is_spoofed(self):
        for key, value in (("environment", "production"), ("database", "production"),
                           ("application_url", "https://production.invalid")):
            with self.subTest(field=key), self.assertRaises(auth.AuthorizationRejected):
                self.verify(payload={**self.payload, key: value}, context={**self.context, key: value})
        with patch.dict(os.environ, {"APP_ENV": "production", "DATABASE_URL": "production"}):
            # Ambient variables cannot grant authority or alter the fixed dev scope.
            self.assertEqual(self.verify().nonce, self.payload["nonce"])

    def test_signed_runtime_window_is_separate_bounded_and_tamper_rejected(self):
        result = self.verify()
        self.assertEqual(result.expires_at, 2000)
        self.assertEqual(result.runtime_expires_at, 3000)
        for runtime_expires in (1999, 1000 + 86401, True):
            with self.subTest(runtime_expires=runtime_expires), self.assertRaises(auth.AuthorizationRejected):
                self.verify(payload={**self.payload, "runtime_expires_at": runtime_expires})
        data, signature = self.sign()
        self.assertTrue(data)
        with self.assertRaisesRegex(auth.AuthorizationRejected, "owner_signature_invalid"):
            auth.verify(auth.canonical({**self.payload, "runtime_expires_at": 3001}), signature,
                        self.policy, self.context, self.bundle, self.artifacts, now=1500)

    def test_unknown_fields_duplicate_json_and_noncanonical_bytes_rejected(self):
        data, signature = self.sign()
        for bad in (data + b"\n", b'{"x":1,"x":2}', b'{"x":NaN}', b"[]"):
            with self.subTest(kind=bad[:12]), self.assertRaises(auth.AuthorizationRejected):
                auth.verify(bad, signature, self.policy, self.context, self.bundle, self.artifacts,
                            now=1500)
        with self.assertRaises(auth.AuthorizationRejected):
            self.verify(payload={**self.payload, "agent_approved": True})

    def test_policy_tampering_revocation_and_owner_id_type_rejected(self):
        for value in ({**self.policy, "revoked": True}, {**self.policy, "max_age_seconds": 7200},
                      {**self.policy, "owner_id": True}, {**self.policy, "owner_public_key": self.public + "\n"}):
            with self.subTest(policy_keys=sorted(value)), self.assertRaises(auth.AuthorizationRejected):
                self.verify(policy=value)
        with self.assertRaises(auth.AuthorizationRejected):
            self.verify(payload={**self.payload, "policy_sha256": "0" * 64})

    def test_cluster_identity_and_runtime_policy_bounds_rejected(self):
        for cluster in ("", "0", "01", "18446744073709551616", True):
            with self.subTest(cluster=cluster), self.assertRaises(auth.AuthorizationRejected):
                self.verify(payload={**self.payload, "database_cluster_id": cluster},
                            context={**self.context, "database_cluster_id": cluster})
        for maximum in (0, 604801, True):
            with self.subTest(maximum=maximum), self.assertRaises(auth.AuthorizationRejected):
                self.verify(policy={**self.policy, "max_runtime_seconds": maximum})

    def test_expiry_future_issue_and_unbounded_lifetime_rejected(self):
        for payload, now in ((self.payload, 2000), (self.payload, 999),
                             ({**self.payload, "expires_at": 5000}, 1500),
                             ({**self.payload, "issued_at": True}, 1500)):
            with self.subTest(now=now), self.assertRaises(auth.AuthorizationRejected):
                self.verify(payload=payload, now=now)

    def test_missing_tampered_self_or_duplicate_technical_reviews_rejected(self):
        variants = []
        missing = copy.deepcopy(self.bundle)
        missing["reviews"].pop()
        variants.append(missing)
        for field, value in (("session_id", "fixture-author"), ("role", "release"),
                             ("verdict", "REJECT"), ("artifact_sha256", "0" * 64)):
            changed = copy.deepcopy(self.bundle)
            changed["reviews"][0][field] = value
            variants.append(changed)
        duplicate = copy.deepcopy(self.bundle)
        duplicate["reviews"][0]["session_id"] = duplicate["reviews"][1]["session_id"]
        variants.append(duplicate)
        for changed in variants:
            with self.subTest(review_count=len(changed["reviews"])), self.assertRaises(auth.AuthorizationRejected):
                self.verify(bundle=changed)
        changed_artifacts = {key: value + b"tampered" for key, value in self.artifacts.items()}
        with self.assertRaises(auth.AuthorizationRejected):
            self.verify(artifacts=changed_artifacts)

    def test_empty_or_oversize_review_artifact_rejected_with_all_bindings_resigned(self):
        for artifact in (b"", b"x" * (auth.MAX_BYTES + 1)):
            with self.subTest(artifact_size=len(artifact)):
                sha = hashlib.sha256(artifact).hexdigest()
                bundle = copy.deepcopy(self.bundle)
                bundle["reviews"][0]["artifact_sha256"] = sha
                artifacts = {**self.artifacts, sha: artifact}
                context = {**self.context, "evidence_sha256": auth.digest(bundle)}
                payload = {**self.payload, "evidence_sha256": context["evidence_sha256"]}
                # self.verify signs the updated payload using the real fixture key.
                with self.assertRaisesRegex(auth.AuthorizationRejected, "review_artifact_mismatch"):
                    self.verify(payload=payload, context=context, bundle=bundle, artifacts=artifacts)

    def test_mutable_images_and_invalid_actions_rejected(self):
        for images in ({**self.context["images"], "api": "example.invalid/api:latest"},
                       {**self.context["images"], "unknown": "x"}):
            payload, context = {**self.payload, "images": images}, {**self.context, "images": images}
            with self.assertRaises(auth.AuthorizationRejected):
                self.verify(payload=payload, context=context)
        for actions in (["shell"], ["deploy", "deploy"], ["publish", "deploy"]):
            with self.subTest(actions=actions), self.assertRaises(auth.AuthorizationRejected):
                self.verify(payload={**self.payload, "actions": actions},
                            context={**self.context, "actions": actions})

    def test_existing_production_validator_rejects_development_authorization(self):
        from app.services.content_publishing import PublicationBlocked, validate

        with (
            patch.dict(os.environ, {"APP_ENV": "development", "MIHUR_CONTENT_REVIEW_POLICY": "{}"}),
            self.assertRaises(PublicationBlocked),
        ):
            validate(self.payload)

    def test_nonce_replay_and_expiry_rejected_and_reservation_persists(self):
        result = self.verify()
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            auth.reserve_nonce(result, directory, owner_uid=os.getuid(), now=1500)
            with self.assertRaisesRegex(auth.AuthorizationRejected, "already_reserved"):
                auth.reserve_nonce(result, directory, owner_uid=os.getuid(), now=1500)
            record = auth.strict_json((Path(directory) / (result.nonce + ".json")).read_bytes())
            self.assertEqual(record["status"], "RESERVED_NO_AUTOMATIC_RETRY")
            with self.assertRaises(auth.AuthorizationRejected):
                auth.reserve_nonce(result, directory, owner_uid=os.getuid(), now=2000)

    def test_concurrent_reservation_has_exactly_one_winner(self):
        result = self.verify()
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            barrier, outcomes = threading.Barrier(2), []
            def reserve():
                barrier.wait()
                try:
                    auth.reserve_nonce(result, directory, owner_uid=os.getuid(), now=1500)
                    outcomes.append("reserved")
                except auth.AuthorizationRejected:
                    outcomes.append("rejected")
            threads = [threading.Thread(target=reserve) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
            self.assertCountEqual(outcomes, ["reserved", "rejected"])

    def test_uncertain_fsync_failure_never_releases_nonce(self):
        result = self.verify()
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            with (
                patch.object(auth.os, "fsync", side_effect=OSError("fixture interruption")),
                self.assertRaises(OSError),
            ):
                auth.reserve_nonce(result, directory, owner_uid=os.getuid(), now=1500)
            with self.assertRaisesRegex(auth.AuthorizationRejected, "already_reserved"):
                auth.reserve_nonce(result, directory, owner_uid=os.getuid(), now=1500)

    def test_protected_files_reject_symlinks_hardlinks_permissions_and_wrong_owner(self):
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            path = Path(directory) / "policy.json"
            path.write_bytes(auth.canonical(self.policy))
            path.chmod(0o600)
            self.assertEqual(auth.protected_json(path, owner_uid=os.getuid()), self.policy)
            link = Path(directory) / "linked.json"
            link.symlink_to(path)
            with self.assertRaises((OSError, auth.AuthorizationRejected)):
                auth.protected_json(link, owner_uid=os.getuid())
            link.unlink()
            os.link(path, link)
            with self.assertRaises(auth.AuthorizationRejected):
                auth.protected_json(path, owner_uid=os.getuid())
            link.unlink()
            path.chmod(0o666)
            with self.assertRaises(auth.AuthorizationRejected):
                auth.protected_json(path, owner_uid=os.getuid())
            path.chmod(0o600)
            with self.assertRaises(auth.AuthorizationRejected):
                auth.protected_json(path, owner_uid=os.getuid() + 1)
            Path(directory).chmod(0o777)
            with self.assertRaises(auth.AuthorizationRejected):
                auth.protected_json(path, owner_uid=os.getuid())
            Path(directory).chmod(0o700)

    def test_fifo_inputs_are_rejected_without_waiting_for_a_writer(self):
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            path = Path(directory) / "fifo"
            os.mkfifo(path, 0o600)
            with self.assertRaises(auth.AuthorizationRejected):
                auth._input(path)
            with self.assertRaises(auth.AuthorizationRejected):
                auth.protected_json(path, owner_uid=os.getuid())

    def test_nonce_symlink_and_unsafe_state_directory_rejected(self):
        result = self.verify()
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            path = Path(directory)
            victim = path / "victim"
            victim.write_bytes(b"unchanged")
            (path / (result.nonce + ".json")).symlink_to(victim)
            with self.assertRaises(auth.AuthorizationRejected):
                auth.reserve_nonce(result, path, owner_uid=os.getuid(), now=1500)
            self.assertEqual(victim.read_bytes(), b"unchanged")
            path.chmod(0o755)
            with self.assertRaises(auth.AuthorizationRejected):
                auth.reserve_nonce(result, path, owner_uid=os.getuid(), now=1500)
            path.chmod(0o700)


if __name__ == "__main__":
    unittest.main()
