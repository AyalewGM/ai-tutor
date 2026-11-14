"""Synthetic command/network seams; never an authorization or live host test."""
import base64
import copy
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

SPEC = importlib.util.spec_from_file_location(
    "development_owner_operator", Path(__file__).parents[1] / "deploy/staging/development_release.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


@pytest.fixture
def setup():
    events = []
    context = {"source_sha": "a" * 40, "package_sha256": "b" * 64,
               "database": "mihur_staging", "database_cluster_id": "12345",
               "actions": ["deploy", "publish"]}
    policy = {"revoked": False, "operator_pins_sha256": gate.sha(gate.canonical({}))}
    payload = {**context, "nonce": "c" * 64, "expires_at": 2000, "runtime_expires_at": 10000}
    auth = SimpleNamespace(
        BINDINGS=set(context), MAX_BYTES=65536,
        ACTION_PLANS=(("deploy",), ("publish",), ("deploy", "publish"), ("rollback",)),
        strict_json=json.loads, digest=lambda value: gate.sha(gate.canonical(value)),
        protected_json=Mock(return_value=policy),
        validate_policy=lambda value: gate.require(value["revoked"] is False, "policy_revoked"),
        verify=Mock(side_effect=lambda *_args, **_kwargs: (events.append("verify") or SimpleNamespace(
            payload_sha256="d" * 64, nonce=payload["nonce"], expires_at=payload["expires_at"]))),
        reserve_nonce=Mock(side_effect=lambda *_args, **_kwargs: events.append("reserve")))
    operator = gate.Operator(auth, SimpleNamespace(), {})
    operator.collect = Mock(side_effect=lambda *_args: (events.append("collect") or (policy, context, {})))
    operator.backup = Mock(side_effect=lambda *_args: (events.append("backup") or {"restore_verified": True}))
    operator.deploy = Mock(side_effect=lambda *_args: events.append("deploy"))
    operator.reinspect = Mock(side_effect=lambda *_args: events.append("reinspect"))
    operator.write = Mock(side_effect=lambda path, data, *_args: events.append((path.name, data if path.name == "authorization.sig" else json.loads(data))))
    operator.revoke = Mock(side_effect=lambda: events.append("revoke"))
    operator.publish = Mock(side_effect=lambda *_args: events.append("publish_and_probe"))
    operator.rollback = Mock(side_effect=lambda *_args: events.append("rollback"))
    return operator, payload, context, events


def run(setup, actions, *, execute=True):
    operator, payload, context, _events = setup
    payload["actions"] = context["actions"] = actions
    return operator.execute(gate.canonical(payload), b"FIXTURE_SIGNATURE", {}, {}, execute=execute, now=1500)


def test_owner_authentication_precedes_native_metadata_and_check_has_no_effects(setup):
    operator, _payload, _context, events = setup
    assert run(setup, ["publish"], execute=False)["status"] == "CHECKED_NO_EFFECTS"
    assert events[:3] == ["verify", "collect", "verify"]
    operator.auth.reserve_nonce.assert_not_called()
    operator.write.assert_not_called()
    operator.publish.assert_not_called()


def test_invalid_owner_is_rejected_before_metadata_collection(setup):
    operator, _payload, _context, _events = setup
    operator.auth.verify.side_effect = gate.Rejected("fixture_invalid_owner")
    with pytest.raises(gate.Rejected, match="invalid_owner"):
        run(setup, ["publish"])
    operator.collect.assert_not_called()
    operator.auth.reserve_nonce.assert_not_called()


def test_deploy_publish_reserves_reinspects_then_issues_bounded_grant(setup):
    operator, payload, context, events = setup
    result = run(setup, ["deploy", "publish"])
    assert result["new_student_availability_claim"] is False
    assert events.index("reserve") < events.index("deploy") < events.index("reinspect")
    grants = [value for name, value in (event for event in events if type(event) is tuple)
              if name == "grant.json"]
    assert len(grants) == 2
    assert grants[0]["runtime_expires_at"] == 1800
    assert grants[0]["owner_runtime_expires_at"] == payload["runtime_expires_at"]
    assert grants[0]["release"] == context
    assert grants[1]["runtime_expires_at"] == payload["runtime_expires_at"]
    assert events.index(("grant.json", grants[0])) < events.index("publish_and_probe")
    assert events.index("publish_and_probe") < events.index(("grant.json", grants[1]))
    operator.auth.reserve_nonce.assert_called_once()


def test_long_deploy_gets_fresh_provisional_window_without_extending_owner_authority(setup):
    operator, payload, _context, events = setup
    payload["expires_at"] = 3000
    operator.deploy.side_effect = lambda *_args: setattr(operator, "clock", lambda: 1900)
    run(setup, ["deploy", "publish"])
    grants = [event[1] for event in events if type(event) is tuple and event[0] == "grant.json"]
    assert grants[0]["verified_at"] == 1900
    assert grants[0]["runtime_expires_at"] == 2200
    assert grants[0]["runtime_expires_at"] > grants[0]["verified_at"]
    assert grants[0]["owner_runtime_expires_at"] == payload["runtime_expires_at"]
    assert grants[1]["runtime_expires_at"] == payload["runtime_expires_at"]
    assert operator.auth.verify.call_count == 3
    assert operator.auth.verify.call_args.kwargs["now"] == 1900
    operator.auth.reserve_nonce.assert_called_once()


@pytest.mark.parametrize("actions", [["deploy"], ["rollback"]])
def test_deploy_or_rollback_never_issues_publishing_grant(setup, actions):
    operator, _payload, _context, events = setup
    run(setup, actions)
    operator.publish.assert_not_called()
    assert not any(type(event) is tuple and event[0] == "grant.json" for event in events)
    if actions == ["rollback"]:
        operator.deploy.assert_not_called()
        operator.rollback.assert_called_once()
    else:
        operator.rollback.assert_not_called()


def test_probe_failure_revokes_and_preserves_reservation(setup):
    operator, _payload, _context, events = setup
    operator.publish.side_effect = gate.Rejected("fixture_probe_failed")
    with pytest.raises(gate.Rejected, match="probe_failed"):
        run(setup, ["publish"])
    assert events[-1] == "revoke"
    operator.auth.reserve_nonce.assert_called_once()
    assert len([event for event in events if type(event) is tuple and event[0] == "grant.json"]) == 1


def test_operation_expiry_after_probe_does_not_extend_permission(setup):
    operator, _payload, _context, events = setup
    operator.publish.side_effect = lambda *_args: setattr(operator, "clock", lambda: 2000)
    with pytest.raises(gate.Rejected, match="operation_expired"):
        run(setup, ["publish"])
    assert events[-1] == "revoke"
    assert len([event for event in events if type(event) is tuple and event[0] == "grant.json"]) == 1


def test_replay_is_denied_before_deploy_or_publication(setup):
    operator, _payload, _context, _events = setup
    operator.auth.reserve_nonce.side_effect = gate.Rejected("already_reserved")
    with pytest.raises(gate.Rejected, match="already_reserved"):
        run(setup, ["deploy", "publish"])
    operator.deploy.assert_not_called()
    operator.publish.assert_not_called()
    operator.write.assert_not_called()


def test_failed_revocation_stops_only_inspected_api_identity(setup):
    operator, _payload, _context, _events = setup
    operator.revoke.side_effect = OSError("fixture_fs_failure")
    operator.api_identity = {"id": "a" * 64, "image": "sha256:" + "b" * 64,
                             "reference": "example.invalid/api@sha256:" + "c" * 64,
                             "source_sha": "d" * 40}
    target = operator.api_identity
    item = {"Id": target["id"], "Image": target["image"],
            "Config": {"Image": target["reference"],
                       "Labels": {"org.opencontainers.image.revision": target["source_sha"]}}}
    with patch.object(gate, "command", side_effect=[json.dumps([item]).encode(), b""]) as command:
        operator.revoke_or_stop()
        assert command.call_args_list[-1].args[0] == gate.DOCKER + ["stop", "--time", "5", target["id"]]
    item["Image"] = "unexpected"
    with patch.object(gate, "command", return_value=json.dumps([item]).encode()) as command, pytest.raises(gate.Rejected, match="emergency_hold"):
        operator.revoke_or_stop()
    command.assert_called_once()


def test_actual_database_identity_rejects_production_not_environment_flags(setup):
    operator, _payload, _context, _events = setup
    with patch.dict(os.environ, {"APP_ENV": "development", "DATABASE_URL": "fake"}), patch.object(
            gate, "command", return_value=gate.canonical({"database": "production",
            "database_role": "mihur_staging", "database_cluster_id": "12345"})), pytest.raises(gate.Rejected, match="native_database_identity"):
        operator.database_identity()


def test_native_database_identity_uses_catalog_builtins_and_fixed_search_path(setup):
    operator, _payload, _context, _events = setup
    value = {"database": "mihur_staging", "database_role": "mihur_staging", "database_cluster_id": "12345"}
    with patch.dict(os.environ, {"PGOPTIONS": "-c search_path=attacker"}), patch.object(
            gate, "command", return_value=gate.canonical(value)) as command:
        assert operator.database_identity() == value
    args = command.call_args.args[0]
    assert "env" in args and "-i" in args
    assert "PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=10000 -c search_path=pg_catalog" in args
    assert "pg_catalog.json_build_object(" in args[-1]
    assert "pg_catalog.current_database()" in args[-1]
    assert "FROM pg_catalog.pg_control_system()" in args[-1]
    assert "attacker" not in " ".join(args)


def ci_fixture():
    source, tree, base, merge = "a" * 40, "b" * 40, "c" * 40, "d" * 40
    pr = {"number": 516, "state": "open", "head": {"sha": source, "ref": "feature/source",
          "repo": {"id": 1367979340}},
          "base": {"ref": "feature/base", "sha": "0" * 40, "repo": {"id": 1367979340}},
          "merge_commit_sha": merge}
    rows = [{"id": index + 1, "name": name, "head_sha": source, "app": {"id": app},
             "status": "completed", "conclusion": "success", "pull_requests": [{"number": 516}]}
            for index, (name, app) in enumerate(gate.CHECKS.items())]
    runs = {}
    for name, (workflow_id, workflow_path) in gate.CHECK_WORKFLOWS.items():
        run_id = 100 if name in {"test", "containers"} else 200
        runs[run_id] = {"id": run_id, "workflow_id": workflow_id, "path": workflow_path,
                        "event": "pull_request", "head_sha": source, "head_branch": pr["head"]["ref"],
                        "head_repository": {"id": 1367979340}, "repository": {"id": 1367979340},
                        "status": "completed", "conclusion": "success", "pull_requests": [{"number": 516}]}
        next(row for row in rows if row["name"] == name)["details_url"] = (
            f"https://github.com/AyalewGM/ai-tutor/actions/runs/{run_id}/job/123")
    runs[300] = {"id": 300, "workflow_id": gate.CODEQL_WORKFLOW, "path": gate.CODEQL_PATH,
                 "event": "dynamic", "head_sha": source, "head_branch": pr["head"]["ref"],
                 "head_repository": {"id": 1367979340}, "repository": {"id": 1367979340},
                 "status": "completed", "conclusion": "success", "run_attempt": 1}
    jobs = []
    for index, name in enumerate(sorted(gate.CODEQL_NAMES), 1000):
        url = f"https://github.com/AyalewGM/ai-tutor/actions/runs/300/job/{index}"
        rows.append({"id": index, "name": name, "head_sha": source, "app": {"id": 15368},
                     "status": "completed", "conclusion": "success", "details_url": url})
        jobs.append({"id": index, "name": name, "run_id": 300, "run_attempt": 1,
                     "head_sha": source, "head_branch": pr["head"]["ref"],
                     "status": "completed", "conclusion": "success", "html_url": url,
                     "check_run_url": f"https://api.github.com/repos/AyalewGM/ai-tutor/check-runs/{index}"})
    def api(path):
        if path.startswith("actions/workflows/"):
            inventory = [run for run in runs.values() if run["id"] >= 300]
            return {"total_count": len(inventory), "workflow_runs": inventory}
        if "/attempts/" in path:
            return {"total_count": len(jobs), "jobs": jobs}
        if path == "":
            return {"id": 1367979340, "owner": {"id": 22088298}}
        if "/check-runs?" in path:
            return {"total_count": len(rows), "check_runs": rows}
        if "/pulls?" in path:
            return [pr]
        if path == "pulls/516":
            return pr
        if path.startswith("git/ref/heads/"):
            return {"object": {"sha": base}}
        if path == "commits/" + merge:
            return {"sha": merge, "commit": {"tree": {"sha": tree}},
                    "parents": [{"sha": base}, {"sha": source}]}
        if path.startswith("actions/runs/"):
            return runs[int(path.removeprefix("actions/runs/"))]
        raise AssertionError("unexpected fixture API path")
    api.runs = runs
    api.jobs = jobs
    return source, tree, base, pr, rows, api


def test_ci_uses_current_base_ref_and_proves_tested_tree_equals_head():
    source, tree, base, _pr, _rows, api = ci_fixture()
    with patch.object(gate, "github", side_effect=api), patch.object(gate, "git", return_value="") as git:
        proof = gate.verify_checks(source, tree, Path("/fixture"))
        git.assert_called_once_with(Path("/fixture"), "merge-base", "--is-ancestor", base, source)
    assert proof["head_and_test_merge_tree_equal"] is True


def test_ci_run_metadata_cache_is_invocation_local_and_shared_only_by_same_run():
    source, tree, _base, _pr, _rows, api = ci_fixture()
    with patch.object(gate, "github", side_effect=api) as request, patch.object(gate, "git", return_value=""):
        gate.verify_checks(source, tree, Path("/fixture"))
        gate.verify_checks(source, tree, Path("/fixture"))
    run_reads = [call.args[0] for call in request.call_args_list if call.args[0].startswith("actions/runs/")]
    assert run_reads.count("actions/runs/100") == 2
    assert run_reads.count("actions/runs/200") == 2


@pytest.mark.parametrize("field,value", [
    ("workflow_id", 1), ("path", ".github/workflows/impostor.yml"), ("event", "push"),
    ("head_sha", "f" * 40), ("head_branch", "impostor/source"),
    ("head_repository", {"id": 1}), ("repository", {"id": 1}),
    ("status", "in_progress"), ("conclusion", "failure"), ("pull_requests", [{"number": 1}]),
])
def test_same_actions_app_and_job_name_cannot_substitute_another_workflow_or_subject(field, value):
    source, tree, _base, _pr, _rows, api = ci_fixture()
    api.runs[100][field] = value
    with patch.object(gate, "github", side_effect=api), patch.object(gate, "git", return_value=""), pytest.raises(gate.Rejected, match="check_workflow_run_not_approved"):
        gate.verify_checks(source, tree, Path("/fixture"))


@pytest.mark.parametrize("url", [
    "https://github.com/other/repo/actions/runs/100/job/123",
    "https://attacker.invalid/actions/runs/100/job/123",
    "https://github.com/AyalewGM/ai-tutor/actions/runs/100",
    "https://github.com/AyalewGM/ai-tutor/actions/runs/100/job/123?extra=true",
])
def test_check_details_url_is_fixed_repository_action_run_not_an_impostor(url):
    source, tree, _base, _pr, rows, api = ci_fixture()
    rows[0]["details_url"] = url
    with patch.object(gate, "github", side_effect=api), patch.object(gate, "git", return_value=""), pytest.raises(gate.Rejected, match="check_details_not_trusted_run"):
        gate.verify_checks(source, tree, Path("/fixture"))


@pytest.mark.parametrize("changed", ["source", "head_ref", "base_ref", "base_commit"])
def test_source_or_current_ref_drift_during_evidence_collection_rejects(changed):
    source, tree, _base, pr, _rows, original_api = ci_fixture()
    reads = {"pr": 0, "base": 0}
    def drifting_api(path):
        value = original_api(path)
        if path == "pulls/516":
            reads["pr"] += 1
            if reads["pr"] == 2:
                value = copy.deepcopy(pr)
                if changed == "source":
                    value["head"]["sha"] = "f" * 40
                elif changed == "head_ref":
                    value["head"]["ref"] = "changed/source"
                elif changed == "base_ref":
                    value["base"]["ref"] = "changed/base"
        if path == "git/ref/heads/feature%2Fbase":
            reads["base"] += 1
            if reads["base"] == 2 and changed == "base_commit":
                value = {"object": {"sha": "f" * 40}}
        return value
    with patch.object(gate, "github", side_effect=drifting_api), patch.object(gate, "git", return_value=""), pytest.raises(gate.Rejected, match="pull_request_changed_during_check"):
        gate.verify_checks(source, tree, Path("/fixture"))


@pytest.mark.parametrize("failure", ["missing_codeql", "wrong_producer", "failed_latest", "different_tree"])
def test_ci_mandatory_provenance_and_tree_rejections(failure):
    source, tree, _base, _pr, rows, api = ci_fixture()
    if failure == "missing_codeql":
        rows[:] = [row for row in rows if row["name"] not in gate.CODEQL_NAMES]
    elif failure == "wrong_producer":
        next(row for row in rows if row["name"] == "Analyze (python)")["app"]["id"] = 1
    elif failure == "failed_latest":
        rows.append({**rows[0], "id": 100, "conclusion": "failure"})
    else:
        tree = "e" * 40
    with patch.object(gate, "github", side_effect=api), patch.object(gate, "git", return_value=""), pytest.raises(gate.Rejected):
        gate.verify_checks(source, tree, Path("/fixture"))


def test_ssh_protocol_rejects_command_or_path_injection(setup):
    operator, _payload, _context, _events = setup
    request = {"mode": "execute-plan", "command": "arbitrary", "envelope": "/root/private"}
    with patch.object(gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(gate.canonical(request)))), pytest.raises(gate.Rejected, match="ssh_request_fields"):
        gate.ssh_request(operator)


def test_ssh_protocol_ignores_original_command_and_passes_only_bounded_public_bytes(setup):
    operator, _payload, _context, _events = setup
    request = {"mode": "check", "envelope": base64.b64encode(b"FIXTURE_JSON").decode(),
               "signature": base64.b64encode(b"FIXTURE_SIG").decode(), "evidence": {},
               "artifacts": {hashlib.sha256(str(i).encode()).hexdigest(): base64.b64encode(
                   b"FIXTURE_REVIEW").decode() for i in range(5)}}
    with patch.dict(os.environ, {"SSH_ORIGINAL_COMMAND": "arbitrary shell"}), patch.object(
            gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(gate.canonical(request)))), patch.object(
            gate, "execute_serialized", return_value={"status": "fixture_check"}) as execute:
        assert gate.ssh_request(operator) == {"status": "CHECKED_NO_EFFECTS", "release_actions_performed": False}
        assert execute.call_args.args[1:3] == (b"FIXTURE_JSON", b"FIXTURE_SIG")
        assert execute.call_args.kwargs == {"execute": False}


def test_different_plans_cannot_execute_concurrently(setup, tmp_path):
    first, _payload, _context, _events = setup
    entered, release = threading.Event(), threading.Event()
    (tmp_path / "operation.lock").write_bytes(b"")
    (tmp_path / "operation.lock").chmod(0o600)
    first.auth._trusted_directory = lambda *_args, **_kwargs: os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    second = gate.Operator(first.auth, SimpleNamespace(), {})
    second.execute = Mock()
    outcomes = []
    def active(*_args, **_kwargs):
        entered.set()
        assert release.wait(3)
        return {"status": "fixture_plan"}
    first.execute = active
    real_stat = os.fstat
    def root_metadata_for_fixture(fd):
        info = real_stat(fd)
        # Owner metadata is a synthetic seam; locking itself is the real syscall.
        return SimpleNamespace(st_uid=0, st_nlink=info.st_nlink, st_mode=info.st_mode)
    def start():
        outcomes.append(gate.execute_serialized(first, b"first", b"sig", {}, {}, execute=True))
    with patch.object(gate, "STATE", tmp_path), patch.object(gate.os, "fstat", side_effect=root_metadata_for_fixture):
        thread = threading.Thread(target=start)
        thread.start()
        try:
            assert entered.wait(2)
            with pytest.raises(BlockingIOError):
                gate.execute_serialized(second, b"second", b"sig", {}, {}, execute=True)
            second.execute.assert_not_called()
        finally:
            release.set()
            thread.join(timeout=2)
        assert not thread.is_alive()
    assert outcomes == [{"status": "fixture_plan"}]


@pytest.mark.parametrize("configuration", [
    '[url "ext::/bin/sh HELPER"]\n insteadOf = https://github.com/\n',
    '[protocol "ext"]\n allow = always\n',
    '[include]\n path = /etc/gitconfig\n',
    '[includeIf "gitdir:*"]\n path = /etc/gitconfig\n',
    '[core]\n sshCommand = /bin/sh HELPER\n',
])
def test_real_git_local_rewrite_and_helpers_rejected_before_fetch(tmp_path, monkeypatch, configuration):
    # The enclosing disposable namespace supplies process/network isolation. The
    # ownership-only seam admits this temporary non-root fixture; the real Git
    # parser, config rejection and command builder are exercised, not mocked.
    root = tmp_path / "checkout"
    subprocess.run(["/usr/bin/git", "init", "--quiet", str(root)], env=gate.CLEAN, check=True,
                   capture_output=True, timeout=10)
    sentinel = tmp_path / "helper-executed"
    helper = tmp_path / "helper"
    helper.write_text("#!/bin/sh\nprintf unsafe > " + str(sentinel) + "\n")
    helper.chmod(0o700)
    config = root / ".git/config"
    with config.open("a") as stream:
        stream.write(configuration.replace("HELPER", str(helper)))
    monkeypatch.setattr(gate, "_git_metadata", lambda path: config)
    with pytest.raises(gate.Rejected, match="unsafe_local_git_configuration"):
        gate.git(root, "fetch", "--no-tags", gate.REPOSITORY_URL, "a" * 40)
    assert not sentinel.exists()


def test_native_git_forces_https_only_no_helpers_redirects_or_ambient_config(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    subprocess.run(["/usr/bin/git", "init", "--quiet", str(root)], env=gate.CLEAN, check=True,
                   capture_output=True, timeout=10)
    monkeypatch.setattr(gate, "_git_metadata", lambda path: root / ".git/config")
    real_command = gate.command
    calls = []
    def record(args, **kwargs):
        calls.append(args)
        return real_command(args, **kwargs)
    monkeypatch.setattr(gate, "command", record)
    gate.git(root, "rev-parse", "--git-dir")
    actual = calls[-1]
    assert "protocol.allow=never" in actual
    assert "protocol.https.allow=always" in actual
    assert "protocol.ext.allow=never" in actual
    assert "http.followRedirects=false" in actual
    assert gate.CLEAN["GIT_CONFIG_NOSYSTEM"] == "1"
    assert gate.CLEAN["GIT_CONFIG_GLOBAL"] == "/dev/null"


def test_git_metadata_rejects_indirection_and_agent_writable_entries(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    metadata = root / ".git"
    metadata.mkdir(parents=True)
    (metadata / "config").write_text("[core]\n repositoryformatversion = 0\n bare = false\n")
    monkeypatch.setattr(gate, "ROOT", root)
    monkeypatch.setattr(gate, "owned_bytes", lambda path: Path(path).read_bytes())
    (metadata / "commondir").write_text("/other")
    with pytest.raises(gate.Rejected, match="external_git_metadata"):
        gate._git_metadata(root, owner_uid=os.getuid())
    (metadata / "commondir").unlink()
    (metadata / "config").chmod(0o666)
    with pytest.raises(gate.Rejected, match="untrusted_git_metadata"):
        gate._git_metadata(root, owner_uid=os.getuid())


@pytest.fixture
def public_inspection_fixture(setup, monkeypatch):
    operator, _payload, _context, _events = setup
    secret = "QA_SECRET_SENTINEL_DO_NOT_PRINT"
    machine = b"0123456789abcdef0123456789abcdef"
    source = "a" * 40
    reference = "example.invalid/public@sha256:" + "b" * 64
    images = {key: reference for key in gate.IMAGE_NAMES}
    operator.auth.HOST = gate.sha(machine)
    operator.control.values = Mock(return_value={"STAGING_DB_PASSWORD": secret})
    operator.auth.protected_json = Mock(return_value={"source_sha": source, "images": images})
    operator.source_context = Mock(return_value={
        "source_sha": source, "source_tree": "c" * 40, "package_sha256": "d" * 64,
        "runtime_sha256": "e" * 64, "private_native_context": secret})
    operator.database_identity = Mock(return_value={
        "database": "mihur_staging", "database_role": "mihur_staging",
        "database_cluster_id": "12345", "private_native_context": secret})
    operator.images = Mock()
    def public_file(path, **_kwargs):
        assert path != gate.ENV, "Public inspection must never read secret-bearing release.env"
        assert path == Path("/etc/machine-id")
        return machine
    monkeypatch.setattr(gate, "owned_bytes", public_file)
    monkeypatch.setattr(gate, "git", Mock(return_value=source))
    monkeypatch.setattr(gate, "command", Mock(return_value=reference.encode()))
    return operator, secret, images


def test_inspection_stdout_uses_only_explicit_public_fields(public_inspection_fixture, monkeypatch, capsys):
    operator, secret, images = public_inspection_fixture
    monkeypatch.setattr(gate, "load_trusted", lambda: ({}, operator.auth, operator.control))
    monkeypatch.setattr(gate, "Operator", lambda *_args: operator)
    monkeypatch.setattr(gate.os, "geteuid", lambda: 0)
    monkeypatch.setattr(gate.sys, "argv", ["development_release.py", "ssh-request"])
    monkeypatch.setattr(gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b'{"mode":"inspect"}')))
    with patch.dict(os.environ):
        gate.main()
    output = capsys.readouterr().out
    assert secret not in output
    value = json.loads(output)
    assert set(value) == {"current", "database", "database_role", "database_cluster_id",
                          "host_sha256", "release_actions_performed", "candidate"}
    assert value["current"] == {"source_sha": "a" * 40, "images": images}
    assert value["candidate"] == {"source_sha": "a" * 40, "source_tree": "c" * 40,
        "package_sha256": "d" * 64, "runtime_sha256": "e" * 64, "images": images}
    assert value["database"] == value["database_role"] == "mihur_staging"
    assert value["database_cluster_id"] == "12345"
    operator.control.values.assert_not_called()
    assert gate.command.call_count == 6
    assert all(call.args[0][3:6] == ["inspect", "--format", "{{.Config.Image}}"]
               for call in gate.command.call_args_list)


@pytest.mark.parametrize("mode", ["check", "execute-plan"])
def test_ssh_stdout_discards_opaque_native_results(setup, monkeypatch, capsys, mode):
    operator, _payload, _context, _events = setup
    secret = "QA_NATIVE_SECRET_SENTINEL_DO_NOT_PRINT"
    request = {"mode": mode, "envelope": base64.b64encode(b"FIXTURE_JSON").decode(),
               "signature": base64.b64encode(b"FIXTURE_SIG").decode(), "evidence": {},
               "artifacts": {hashlib.sha256(str(i).encode()).hexdigest(): base64.b64encode(
                   b"FIXTURE_REVIEW").decode() for i in range(5)}}
    monkeypatch.setattr(gate, "execute_serialized", Mock(return_value={
        "status": secret, "source_sha": secret, "private_configuration": secret}))
    monkeypatch.setattr(gate, "load_trusted", lambda: ({}, operator.auth, operator.control))
    monkeypatch.setattr(gate, "Operator", lambda *_args: operator)
    monkeypatch.setattr(gate.os, "geteuid", lambda: 0)
    monkeypatch.setattr(gate.sys, "argv", ["development_release.py", "ssh-request"])
    monkeypatch.setattr(gate.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(gate.canonical(request))))
    with patch.dict(os.environ):
        gate.main()
    output = capsys.readouterr().out
    assert secret not in output
    assert json.loads(output) == {
        "status": "EXECUTED_SIGNED_DEVELOPMENT_PLAN" if mode == "execute-plan" else "CHECKED_NO_EFFECTS",
        "release_actions_performed": mode == "execute-plan"}


def test_console_stdout_discards_opaque_native_result(setup, monkeypatch, capsys):
    operator, _payload, _context, _events = setup
    secret = "QA_CONSOLE_SECRET_SENTINEL_DO_NOT_PRINT"
    operator.auth._input = lambda *_args: b'{"reviews":[]}'
    monkeypatch.setattr(gate, "execute_serialized", Mock(return_value={"private_configuration": secret}))
    monkeypatch.setattr(gate, "load_trusted", lambda: ({}, operator.auth, operator.control))
    monkeypatch.setattr(gate, "Operator", lambda *_args: operator)
    monkeypatch.setattr(gate.os, "geteuid", lambda: 0)
    monkeypatch.setattr(gate.sys, "argv", ["development_release.py", "check", "--envelope", "public.json",
        "--signature", "public.sig", "--evidence", "public-evidence.json", "--artifacts", "public-reviews"])
    with patch.dict(os.environ):
        gate.main()
    output = capsys.readouterr().out
    assert secret not in output
    assert json.loads(output) == {"status": "CHECKED_NO_EFFECTS", "release_actions_performed": False}


def main_ci_fixture():
    source, tree, _base, _pr, rows, original = ci_fixture()
    for run in original.runs.values():
        run.update(event="dynamic" if run["id"] >= 300 else "push", head_branch="main", pull_requests=[])
    for job in original.jobs:
        job["head_branch"] = "main"
    for row in rows:
        row["pull_requests"] = []
    def api(path):
        if path == "git/ref/heads/main":
            return {"object": {"sha": source}}
        if path == "commits/" + source:
            return {"sha": source, "commit": {"tree": {"sha": tree}}}
        return original(path)
    api.jobs = original.jobs
    return source, tree, rows, original.runs, api


def test_current_main_accepts_exact_push_checks_without_open_pr():
    source, tree, _rows, _runs, api = main_ci_fixture()
    with patch.object(gate, "github", side_effect=api):
        assert gate.verify_checks(source, tree, Path("/fixture")) == {
            "head_sha": source, "tested_tree": tree, "branch": "main", "event": "push"}


@pytest.mark.parametrize("field,value", [
    ("event", "pull_request"), ("event", "workflow_dispatch"),
    ("head_sha", "f" * 40), ("head_branch", "other"),
    ("workflow_id", 123), ("path", ".github/workflows/untrusted.yml"),
    ("repository", {"id": 123}), ("head_repository", {"id": 123}),
    ("status", "in_progress"), ("conclusion", "failure"),
])
def test_main_rejects_untrusted_or_incomplete_workflow(field, value):
    source, tree, _rows, runs, api = main_ci_fixture()
    runs[100][field] = value
    with patch.object(gate, "github", side_effect=api), pytest.raises(gate.Rejected):
        gate.verify_checks(source, tree, Path("/fixture"))


@pytest.mark.parametrize("change", ["tree", "ref", "newer_failure", "missing_check", "producer"])
def test_main_rejects_drift_and_invalid_checks(change):
    source, tree, rows, _runs, original = main_ci_fixture()
    if change == "newer_failure":
        rows.append({**rows[0], "id": 999, "conclusion": "failure"})
    if change == "missing_check":
        rows.pop()
    if change == "producer":
        rows[0]["app"] = {"id": 123}
    reads = 0
    def api(path):
        nonlocal reads
        if path == "git/ref/heads/main":
            reads += 1
            if change == "ref" and reads == 2:
                return {"object": {"sha": "f" * 40}}
        return original(path)
    with patch.object(gate, "github", side_effect=api), pytest.raises(gate.Rejected):
        gate.verify_checks(source, "f" * 40 if change == "tree" else tree, Path("/fixture"))


@pytest.mark.parametrize("field,value", [
    ("workflow_id", 123), ("path", ".github/workflows/codeql.yml"), ("event", "push"),
    ("head_sha", "f" * 40), ("head_branch", "other"), ("repository", {"id": 1}),
    ("head_repository", {"id": 1}), ("status", "in_progress"), ("conclusion", "failure"),
    ("run_attempt", 0), ("run_attempt", True),
])
def test_codeql_run_provenance_is_required(field, value):
    source, tree, _rows, runs, api = main_ci_fixture()
    runs[300][field] = value
    with patch.object(gate, "github", side_effect=api), pytest.raises(gate.Rejected):
        gate.verify_checks(source, tree, Path("/fixture"))


@pytest.mark.parametrize("status,conclusion", [("completed", "failure"), ("in_progress", None)])
def test_codeql_newer_failed_or_pending_run_blocks_older_success(status, conclusion):
    source, tree, _rows, runs, api = main_ci_fixture()
    runs[301] = {**runs[300], "id": 301, "status": status, "conclusion": conclusion}
    with patch.object(gate, "github", side_effect=api), pytest.raises(gate.Rejected):
        gate.verify_checks(source, tree, Path("/fixture"))


@pytest.mark.parametrize("field,value", [
    ("run_id", 299), ("run_attempt", 2), ("head_sha", "f" * 40),
    ("head_branch", "other"), ("status", "queued"), ("conclusion", "failure"),
    ("html_url", "https://github.com.attacker.invalid/AyalewGM/ai-tutor/actions/runs/300/job/1000"),
    ("check_run_url", "https://api.github.com/repos/other/repo/check-runs/1000"),
])
def test_codeql_jobs_cannot_mix_run_attempt_subject_or_urls(field, value):
    source, tree, _rows, _runs, api = main_ci_fixture()
    api.jobs[0][field] = value
    with patch.object(gate, "github", side_effect=api), pytest.raises(gate.Rejected):
        gate.verify_checks(source, tree, Path("/fixture"))


@pytest.mark.parametrize("change", ["missing_language", "duplicate_language", "wrong_producer", "wrong_sha",
                                     "spoof_url", "newer_failed_check", "mixed_run_check"])
def test_codeql_requires_all_languages_and_exact_check_job_binding(change):
    source, tree, rows, _runs, api = main_ci_fixture()
    row = next(row for row in rows if row["name"] == api.jobs[0]["name"])
    if change == "missing_language": api.jobs.pop()
    if change == "duplicate_language": api.jobs.append({**api.jobs[0], "id": 8888})
    if change == "wrong_producer": row["app"] = {"id": 57789}
    if change == "wrong_sha": row["head_sha"] = "f" * 40
    if change == "spoof_url": row["details_url"] += "?trusted=true"
    if change == "mixed_run_check": row["details_url"] = row["details_url"].replace("/300/", "/299/")
    if change == "newer_failed_check": rows.append({**row, "id": 9999, "conclusion": "failure"})
    with patch.object(gate, "github", side_effect=api), pytest.raises(gate.Rejected):
        gate.verify_checks(source, tree, Path("/fixture"))


@pytest.mark.parametrize("change", ["new_run", "attempt", "pending"])
def test_codeql_rerun_drift_during_evidence_collection_rejects(change):
    source, tree, _rows, runs, original = main_ci_fixture()
    reads = 0
    def api(path):
        nonlocal reads
        if path.startswith("actions/workflows/"):
            reads += 1
            if reads == 2:
                if change == "new_run": runs[301] = {**runs[300], "id": 301}
                if change == "attempt": runs[300] = {**runs[300], "run_attempt": 2}
                if change == "pending": runs[300] = {**runs[300], "status": "queued", "conclusion": None}
        return original(path)
    with patch.object(gate, "github", side_effect=api), pytest.raises(gate.Rejected):
        gate.verify_checks(source, tree, Path("/fixture"))


@pytest.mark.parametrize("kind", ["workflow_runs", "jobs"])
@pytest.mark.parametrize("change", ["changed_total", "duplicate", "empty", "over_budget"])
def test_codeql_inventory_rejects_pagination_inconsistency(kind, change):
    pages = [{"total_count": 2, kind: [{"id": 1}]}, {"total_count": 2, kind: [{"id": 2}]}]
    if change == "changed_total": pages[1]["total_count"] = 3
    if change == "duplicate": pages[1][kind][0]["id"] = 1
    if change == "empty": pages[1][kind] = []
    if change == "over_budget": pages[0]["total_count"] = 1001
    with patch.object(gate, "github", side_effect=pages), pytest.raises(gate.Rejected):
        gate.github_inventory("fixture?key=value", kind)


def test_codeql_inventory_collects_multiple_pages():
    pages = [{"total_count": 2, "jobs": [{"id": 1}]}, {"total_count": 2, "jobs": [{"id": 2}]}]
    with patch.object(gate, "github", side_effect=pages) as request:
        assert gate.github_inventory("fixture?key=value", "jobs") == [{"id": 1}, {"id": 2}]
    assert [call.args[0] for call in request.call_args_list] == [
        "fixture?key=value&per_page=100&page=1", "fixture?key=value&per_page=100&page=2"]


@pytest.mark.parametrize("suffix", [
    "actions/workflows/371754568/runs?head_sha=" + "a" * 40 + "&per_page=100&page=1",
    "actions/runs/300/attempts/2/jobs?filter=all&per_page=100&page=2",
])
def test_real_github_accepts_fixed_codeql_routes(suffix):
    response = Mock()
    response.url = gate.PUBLIC_API + "/" + suffix
    response.read.return_value = b'{"total_count": 0}'
    context = Mock()
    context.__enter__ = Mock(return_value=response)
    context.__exit__ = Mock(return_value=False)
    opener = Mock()
    opener.open.return_value = context
    with patch.object(gate.urllib.request, "build_opener", return_value=opener):
        assert gate.github(suffix) == {"total_count": 0}
    assert opener.open.call_args.args[0].full_url == response.url


@pytest.mark.parametrize("suffix", [
    "actions/workflows/123/runs?head_sha=" + "a" * 40 + "&per_page=100&page=1",
    "actions/runs/300/attempts/0/jobs?filter=all&per_page=100&page=1",
    "actions/runs/300/attempts/1/jobs?filter=all&per_page=100&page=1&redirect=evil",
])
def test_real_github_rejects_untrusted_codeql_routes_before_network(suffix):
    with patch.object(gate.urllib.request, "build_opener") as opener, pytest.raises(gate.Rejected):
        gate.github(suffix)
    opener.assert_not_called()
