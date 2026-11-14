"""Synthetic orchestration tests; no VPS, GitHub writes or deployment."""
import base64
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("release_workflow", Path(__file__).with_name("release_workflow.py"))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
SHA, OLD = "a" * 40, "b" * 40
IMAGES = {k: f"ghcr.io/ayalewgm/ai-tutor/staging-{k}@sha256:" + "c" * 64
          for k in ("api", "gateway", "frontend")}


def request_fixture():
    images = {**IMAGES, **{k: "example/" + k + "@sha256:" + "d" * 64 for k in ("db", "redis", "proxy")}}
    payload = {"source_sha": SHA, "source_tree": "e" * 40, "package_sha256": "f" * 64,
               "runtime_sha256": "e" * 64, "images": images, "actions": ["deploy"],
               "repository": w.REPO, "environment": "development", "application_url": w.URL,
               "database": "mihur_staging", "database_role": "mihur_staging",
               "database_cluster_id": "123", "host_sha256": "d" * 64}
    req = {"mode": "execute-plan", "envelope": base64.b64encode(w.canonical(payload)).decode(),
           "signature": "fixture", "evidence": {}, "artifacts": {}}
    before = {"release_actions_performed": False, "current": {"source_sha": OLD, "images": images},
              "candidate": {k: payload[k] for k in ("source_sha", "source_tree", "package_sha256", "runtime_sha256", "images")},
              **{k: payload[k] for k in ("host_sha256", "database", "database_role", "database_cluster_id")}}
    return req, payload, before


class ClassifierTests(unittest.TestCase):
    def test_actual_git_deletion_rename_and_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            def git(*args):
                return subprocess.check_output(["git", "-C", tmp, *args], stderr=subprocess.DEVNULL).decode().strip()
            git("init")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "user.name", "Fixture")
            path = Path(tmp)
            (path / "frontend").mkdir()
            (path / "frontend/style.css").write_text("a{}")
            git("add", ".")
            git("commit", "-m", "base")
            base = git("rev-parse", "HEAD")
            (path / "alembic").mkdir()
            (path / "frontend/style.css").rename(path / "alembic/renamed.sql")
            git("add", "-A")
            git("commit", "-m", "move")
            target = git("rev-parse", "HEAD")
            original = w.run
            with patch.object(w, "run", side_effect=lambda args, *a, **kw: original(["git", "-C", tmp, *args[1:]], *a, **kw)):
                result = w.classify(base, target)
            self.assertTrue(result["database_review_required"])
            self.assertEqual(result["changed_files"], ["alembic/renamed.sql", "frontend/style.css"])
            self.assertFalse(result["automatic_rollback_supported"])

    def test_frontend_classification_never_waives_authorization(self):
        with patch.object(w, "git"), patch.object(w, "run", return_value=b"frontend/src/Login.tsx\0"):
            result = w.classify(OLD, SHA)
        self.assertTrue(result["frontend_only_delta"])
        self.assertTrue(result["authorization_required"])
        self.assertTrue(result["restore_evidence_required"])

    def test_unknown_files_escalate(self):
        with patch.object(w, "git"), patch.object(w, "run", return_value=b"scripts/seed.py\0"):
            self.assertEqual(w.classify(OLD, SHA)["change_types"], ["operator_review"])

    def test_invalid_sha_fails_before_git(self):
        with patch.object(w, "git") as git, self.assertRaises(ValueError):
            w.classify("--help", SHA)
        git.assert_not_called()


class BuildTests(unittest.TestCase):
    def fixture(self):
        meta = {"head_sha": SHA, "head_branch": "main", "path": ".github/workflows/staging-images.yml",
                "event": "workflow_dispatch", "repository": {"id": 1367979340},
                "head_repository": {"id": 1367979340}, "status": "completed", "conclusion": "success", "run_attempt": 2}
        listing = {"total_count": 1, "artifacts": [{"name": f"staging-images-{SHA}-123-2",
                   "expired": False, "id": 456, "size_in_bytes": 500}]}
        content = "STAGING_RELEASE_SHA=" + SHA + "\n" + "".join(
            f"STAGING_{k.upper()}_IMAGE={v}\n" for k, v in IMAGES.items())
        return meta, listing, content

    def execute(self, meta, listing, content):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("application-images.env", content)
        with patch.object(w, "api", side_effect=[meta, listing, meta]), patch.object(w, "run", return_value=buf.getvalue()):
            return w.build_manifest("123", SHA)

    def test_exact_successful_build(self):
        self.assertEqual(self.execute(*self.fixture())[0], IMAGES)

    def test_untrusted_builds(self):
        for key, value in (("head_sha", OLD), ("head_branch", "feature"), ("path", "evil.yml"),
                           ("event", "pull_request"), ("status", "queued"), ("conclusion", "failure"),
                           ("repository", {"id": 1}), ("head_repository", {"id": 1})):
            with self.subTest(key=key), self.assertRaises(ValueError):
                meta, listing, content = self.fixture()
                meta[key] = value
                self.execute(meta, listing, content)

    def test_old_attempt_missing_expired_and_incomplete_artifacts(self):
        for kind in ("attempt", "expired", "incomplete", "duplicate", "size"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                meta, listing, content = self.fixture()
                if kind == "attempt":
                    meta["run_attempt"] = 3
                elif kind == "expired":
                    listing["artifacts"][0]["expired"] = True
                elif kind == "incomplete":
                    listing["total_count"] = 2
                elif kind == "duplicate":
                    listing["artifacts"] *= 2
                    listing["total_count"] = 2
                else:
                    listing["artifacts"][0]["size_in_bytes"] = 2000000
                self.execute(meta, listing, content)

    def test_manifest_wrong_sha_mutable_or_duplicate(self):
        for kind in ("sha", "tag", "duplicate"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                meta, listing, content = self.fixture()
                if kind == "sha":
                    content = content.replace(SHA, OLD)
                elif kind == "tag":
                    content = content.replace("@sha256:" + "c" * 64, ":latest")
                else:
                    content += "STAGING_RELEASE_SHA=" + SHA + "\n"
                self.execute(meta, listing, content)


    def test_rerun_during_artifact_download_rejects(self):
        meta, listing, content = self.fixture()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("application-images.env", content)
        for changes in ({"run_attempt": 3}, {"status": "queued", "conclusion": None},
                        {"conclusion": "failure"}):
            with self.subTest(changes=changes), patch.object(w, "api", side_effect=[
                    meta, listing, {**meta, **changes}]), patch.object(w, "run", return_value=buf.getvalue()), \
                    self.assertRaisesRegex(ValueError, "image_build_changed"):
                w.build_manifest("123", SHA)


class RequestTests(unittest.TestCase):
    def test_scope_cannot_publish_or_target_production(self):
        for key, value in (("actions", ["deploy", "publish"]), ("source_sha", OLD),
                           ("environment", "production"), ("application_url", "https://mihureducation.com"),
                           ("database", "production"), ("repository", "other/repo")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                req, payload, _ = request_fixture()
                payload[key] = value
                req["envelope"] = base64.b64encode(w.canonical(payload)).decode()
                w.signed_request(json.dumps(req), SHA)

    def test_signed_request_is_not_locally_claimed_cryptographically_valid(self):
        req, payload, _ = request_fixture()
        self.assertEqual(w.signed_request(json.dumps(req), SHA), (req, payload))

    def test_inspection_bindings(self):
        _, payload, before = request_fixture()
        w.verify_inspection(before, OLD, SHA, IMAGES, payload)
        for key in ("source_sha", "source_tree", "package_sha256", "runtime_sha256"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                copy = json.loads(json.dumps(before))
                copy["candidate"][key] = "changed"
                w.verify_inspection(copy, OLD, SHA, IMAGES, payload)
        before["current"]["source_sha"] = SHA
        with self.assertRaises(ValueError):
            w.verify_inspection(before, OLD, SHA, IMAGES, payload)


class ExecutionTests(unittest.TestCase):
    def execute(self, answers, enabled="true", mode="deploy", build_changed=False):
        req, _payload, before = request_fixture()
        transport = Mock()
        transport.send.side_effect = [before, *answers]
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        env = {"GITHUB_REPOSITORY": w.REPO, "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": SHA,
               "GITHUB_STEP_SUMMARY": str(Path(temporary.name) / "summary"),
               "STAGING_DEPLOY_ENABLED": enabled, "SIGNED_REQUEST": json.dumps(req)}
        with patch.dict(os.environ, env), patch("sys.argv", ["tool", mode, "--current", OLD,
                "--release", SHA, "--build-run", "123"]), patch.object(w, "git", return_value=SHA), \
                patch.object(w, "api", return_value={"object": {"sha": SHA}}), \
                patch.object(w, "classify", return_value={"changed_files": ["frontend/style.css"]}), \
                patch.object(w, "build_manifest", return_value=(IMAGES, {})), \
                patch.object(w, "Transport", return_value=transport) as create, patch.object(w, "smoke") as smoke, \
                patch.object(w, "refresh_build", side_effect=w.WorkflowStopped("image_build_changed") if build_changed else None):
            error = None
            try:
                w.main()
            except Exception as exc:  # noqa: BLE001 - collect synthetic failures for assertions
                error = exc
            return transport, create.call_count, smoke.call_count, error

    def test_plan_never_opens_ssh(self):
        _, count, smoke, error = self.execute([], mode="plan")
        self.assertIsNone(error)
        self.assertEqual((count, smoke), (0, 0))

    def test_disabled_never_opens_ssh(self):
        _, count, _, error = self.execute([], enabled="false")
        self.assertIsInstance(error, ValueError)
        self.assertEqual(count, 0)

    def test_native_rejection_stops_before_execute(self):
        transport, _, smoke, error = self.execute([{"status": "REJECTED"}])
        self.assertIsInstance(error, ValueError)
        self.assertEqual([c.args[0]["mode"] for c in transport.send.call_args_list], ["inspect", "check"])
        self.assertEqual(smoke, 0)

    def test_success_order_and_release_identity(self):
        _, payload, _ = request_fixture()
        transport, _, smoke, error = self.execute([
            {"status": "CHECKED_NO_EFFECTS", "release_actions_performed": False},
            {"status": "EXECUTED_SIGNED_DEVELOPMENT_PLAN", "release_actions_performed": True},
            {"current": {"source_sha": SHA, "images": payload["images"]}}])
        self.assertIsNone(error)
        self.assertEqual([c.args[0]["mode"] for c in transport.send.call_args_list],
                         ["inspect", "check", "execute-plan", "inspect"])
        self.assertEqual(smoke, 1)

    def test_execution_connection_loss_never_retries(self):
        transport, _, smoke, error = self.execute([
            {"status": "CHECKED_NO_EFFECTS", "release_actions_performed": False}, TimeoutError()])
        self.assertIsInstance(error, TimeoutError)
        self.assertEqual(transport.send.call_count, 3)
        self.assertEqual(smoke, 0)


    def test_rerun_after_native_check_stops_before_execute(self):
        transport, _, smoke, error = self.execute([
            {"status": "CHECKED_NO_EFFECTS", "release_actions_performed": False}], build_changed=True)
        self.assertIsInstance(error, ValueError)
        self.assertEqual([c.args[0]["mode"] for c in transport.send.call_args_list], ["inspect", "check"])
        self.assertEqual(smoke, 0)

    def test_wrong_post_deploy_release_is_not_success(self):
        _, _, smoke, error = self.execute([
            {"status": "CHECKED_NO_EFFECTS", "release_actions_performed": False},
            {"status": "EXECUTED_SIGNED_DEVELOPMENT_PLAN", "release_actions_performed": True},
            {"current": {"source_sha": OLD, "images": {}}}])
        self.assertIsInstance(error, ValueError)
        self.assertEqual(smoke, 0)


class TransportTests(unittest.TestCase):
    def test_wrong_key_or_host_never_reaches_ssh(self):
        for output in ([b"256 SHA256:wrong fixture", b"256 " + w.HOST_KEY.encode() + b" fixture"],
                       [b"256 " + w.CLIENT_KEY.encode() + b" fixture", b"256 SHA256:wrong fixture"]):
            with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
                    "STAGING_INSPECTION_KEY": "fixture", "STAGING_KNOWN_HOSTS": "fixture"}), \
                    patch.object(w, "run", side_effect=output) as run, self.assertRaises(ValueError):
                w.Transport(tmp)
            self.assertTrue(all(c.args[0][0] == "ssh-keygen" for c in run.call_args_list))

    def test_transport_never_sends_remote_shell_command(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
                "STAGING_INSPECTION_KEY": "fixture", "STAGING_KNOWN_HOSTS": "fixture"}), \
                patch.object(w, "run", side_effect=[
                    b"256 " + w.CLIENT_KEY.encode() + b" fixture",
                    b"256 " + w.HOST_KEY.encode() + b" fixture", b'{}']) as run:
            t = w.Transport(tmp)
            self.assertEqual((Path(tmp) / "key").stat().st_mode & 0o777, 0o600)
            t.send({"mode": "inspect"})
            args = run.call_args.args[0]
            self.assertEqual(args[-1], "ubuntu@" + w.HOST)
            self.assertIn("StrictHostKeyChecking=yes", args)
            self.assertIn("IdentityAgent=none", args)
            self.assertEqual(run.call_args.args[1], b'{"mode":"inspect"}')


if __name__ == "__main__":
    unittest.main()
