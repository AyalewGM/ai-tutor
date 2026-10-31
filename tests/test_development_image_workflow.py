"""Run only the workflow preflight, with fixture-only GitHub responses.

These checks do not execute candidate code, build images, or authorize a release.
"""
import ast
import copy
import json
import subprocess
from pathlib import Path

import pytest
import yaml

SOURCE = "a" * 40
BRANCH = "proposal/dev-solo-owner-governance"
REPO = "repos/AyalewGM/ai-tutor"
WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/staging-images.yml"


def workflow():
    return yaml.safe_load(WORKFLOW.read_text())


def responses():
    rows = []
    for index, (name, app, run) in enumerate([
        ("test", 15368, 10), ("containers", 15368, 10),
        ("Semgrep SAST", 15368, 20),
        ("Trivy dependencies and secrets", 15368, 20), ("CodeQL", 57789, 30),
    ], 1):
        rows.append({"id": index, "name": name, "app": {"id": app}, "head_sha": SOURCE,
                     "status": "completed", "conclusion": "success",
                     "details_url": f"https://github.com/AyalewGM/ai-tutor/actions/runs/{run}/job/{index}"})
    result = {f"{REPO}/commits/{SOURCE}/check-runs?per_page=100":
              {"total_count": 5, "check_runs": rows}}
    for run, workflow_id, name in [(10, 356891953, "ci"), (20, 371762802, "security")]:
        result[f"{REPO}/actions/runs/{run}"] = {
            "id": run, "workflow_id": workflow_id, "path": f".github/workflows/{name}.yml",
            "event": "pull_request", "head_sha": SOURCE, "head_branch": BRANCH,
            "repository": {"id": 1367979340}, "head_repository": {"id": 1367979340},
            "status": "completed", "conclusion": "success"}
    for name in ["ci.yml", "security.yml"]:
        result[f"{REPO}/actions/workflows/{name}/runs?head_sha={SOURCE}&event=push&per_page=100"] = {
            "workflow_runs": [{"head_sha": SOURCE, "head_branch": "main", "run_number": 1,
                               "status": "completed", "conclusion": "success"}]}
    return result


def preflight(tmp_path, data=None, **changes):
    fixture = tmp_path / "responses.json"
    fixture.write_text(json.dumps(responses() if data is None else data))
    binary = tmp_path / "gh"
    binary.write_text("""#!/usr/bin/python3
import json, os, sys
from pathlib import Path
assert sys.argv[1:4] == ['api', '--hostname', 'github.com']
assert len(sys.argv) == 5
with open(os.environ['FIXTURE_LOG'], 'a') as output:
    output.write(sys.argv[4] + '\\n')
data = json.loads(Path(os.environ['FIXTURE_DATA']).read_text())
if sys.argv[4] not in data:
    raise SystemExit('Unconfigured endpoint')
print(json.dumps(data[sys.argv[4]]))
""")
    binary.chmod(0o700)
    log = tmp_path / "requests"
    env = {"PATH": f"{tmp_path}:/usr/bin:/bin", "REPOSITORY": "AyalewGM/ai-tutor",
           "RELEASE_SHA": SOURCE, "DEVELOPMENT_SOURCE_SHA": SOURCE,
           "RELEASE_REF": f"refs/heads/{BRANCH}", "RELEASE_BRANCH": BRANCH,
           "PRIVATE_PACKAGES_CONFIRMED": "true", "RUNNER_TEMP": str(tmp_path),
           "FIXTURE_DATA": str(fixture), "FIXTURE_LOG": str(log)}
    env.update(changes)
    script = workflow()["jobs"]["publish"]["steps"][0]["run"]
    result = subprocess.run(["/bin/bash", "-c", script], check=False, env=env,
                            capture_output=True, text=True, timeout=10)
    return result, log.read_text().splitlines() if log.exists() else []


def test_development_preflight_accepts_required_trusted_producers(tmp_path):
    result, requests = preflight(tmp_path)
    assert result.returncode == 0, result.stderr
    assert requests == [f"{REPO}/commits/{SOURCE}/check-runs?per_page=100",
                        f"{REPO}/actions/runs/10", f"{REPO}/actions/runs/20"]


def test_empty_input_preserves_main_push_checks(tmp_path):
    result, requests = preflight(tmp_path, DEVELOPMENT_SOURCE_SHA="",
                                 RELEASE_REF="refs/heads/main", RELEASE_BRANCH="main")
    assert result.returncode == 0, result.stderr
    assert len(requests) == 2
    assert all("event=push" in request for request in requests)


@pytest.mark.parametrize("changes", [
    {"DEVELOPMENT_SOURCE_SHA": ""},
    {"RELEASE_REF": "refs/heads/main"},
    {"RELEASE_REF": "refs/heads/other"},
    {"DEVELOPMENT_SOURCE_SHA": "b" * 40},
    {"REPOSITORY": "fork/ai-tutor"},
    {"PRIVATE_PACKAGES_CONFIRMED": "false"},
    {"RELEASE_SHA": "main"},
])
def test_preflight_rejects_unapproved_context_before_api(tmp_path, changes):
    result, requests = preflight(tmp_path, **changes)
    assert result.returncode != 0
    assert requests == []


@pytest.mark.parametrize("defect", ["missing_codeql", "wrong_app", "failed_latest",
                                       "wrong_workflow", "wrong_path", "wrong_event",
                                       "wrong_source", "fork_run", "wrong_branch",
                                       "failed_run", "untrusted_details", "overflow"])
def test_preflight_rejects_invalid_evidence(tmp_path, defect):
    data = responses()
    checks = data[f"{REPO}/commits/{SOURCE}/check-runs?per_page=100"]
    run = data[f"{REPO}/actions/runs/10"]
    if defect == "missing_codeql":
        checks["check_runs"].pop()
    elif defect == "wrong_app":
        checks["check_runs"][-1]["app"]["id"] = 15368
    elif defect == "failed_latest":
        row = copy.deepcopy(checks["check_runs"][0])
        row.update(id=99, conclusion="failure")
        checks["check_runs"].append(row)
        checks["total_count"] += 1
    elif defect == "wrong_workflow":
        run["workflow_id"] = 1
    elif defect == "wrong_path":
        run["path"] = ".github/workflows/other.yml"
    elif defect == "wrong_event":
        run["event"] = "workflow_dispatch"
    elif defect == "wrong_source":
        run["head_sha"] = "b" * 40
    elif defect == "fork_run":
        run["head_repository"]["id"] = 1
    elif defect == "wrong_branch":
        run["head_branch"] = "other"
    elif defect == "failed_run":
        run["conclusion"] = "failure"
    elif defect == "untrusted_details":
        checks["check_runs"][0]["details_url"] = "https://example.com/runs/10"
    elif defect == "overflow":
        checks["total_count"] = 101
    result, _ = preflight(tmp_path, data=data)
    assert result.returncode != 0


def test_build_contract_keeps_protected_permissions_and_source_binding():
    config = workflow()
    event = config.get("on", config.get(True))
    assert set(event) == {"workflow_dispatch"}
    assert event["workflow_dispatch"]["inputs"]["development_source_sha"]["default"] == ""
    job = config["jobs"]["publish"]
    assert job["environment"] == "staging-images"
    assert job["permissions"] == {"contents": "read", "actions": "read", "packages": "write"}
    assert "inputs.development_source_sha == github.sha" in job["if"]
    assert "github.repository == 'AyalewGM/ai-tutor'" in job["if"]
    steps = job["steps"]
    assert steps[1]["with"]["persist-credentials"] is False
    assert steps[1]["with"]["ref"] == "${{ github.sha }}"
    gate = steps[2]["run"]
    program = gate.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    ast.parse(program)
    assert "gate.verify_checks(source, tree, root)" in program
    assert "gate.github = api" in program
    assert "'release_authorized': False" in program
    build = steps[3]["run"]
    assert '--tag "$image:$RELEASE_SHA"' in build
    assert '--provenance=mode=min' in build
    assert ':latest' not in build


def test_runner_git_adapter_restricts_arguments_environment_and_worktree(tmp_path):
    """Exercise the actual embedded adapter without importing candidate modules."""
    import re
    from types import SimpleNamespace

    script = workflow()["jobs"]["publish"]["steps"][2]["run"]
    program = script.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    function = next(node for node in ast.parse(program).body
                    if isinstance(node, ast.FunctionDef) and node.name == "runner_git")
    calls = []

    def invoke(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(stdout="verified\n")

    clean = {"GIT_NO_LAZY_FETCH": "1", "GIT_CONFIG_NOSYSTEM": "1"}
    scope = {"Path": Path, "re": re, "root": tmp_path.resolve(), "source": SOURCE,
             "git_env": clean, "subprocess": SimpleNamespace(run=invoke)}
    # Execute only the checked-in adapter function with a subprocess spy, never candidate modules.
    exec(compile(ast.Module(body=[function], type_ignores=[]), "workflow-runner-git", "exec"), scope)  # noqa: S102
    git = scope["runner_git"]
    assert git(tmp_path, "rev-parse", "HEAD^{tree}") == "verified"
    assert git(tmp_path, "merge-base", "--is-ancestor", "b" * 40, SOURCE) == "verified"
    assert git(tmp_path, "status", "--porcelain", "--untracked-files=all") == "verified"
    for argv, kwargs in calls:
        assert argv[0] == "/usr/bin/git"
        assert "core.hooksPath=/dev/null" in argv
        assert "core.fsmonitor=false" in argv
        assert "protocol.allow=never" in argv
        assert "remote.origin.promisor=false" in argv
        assert kwargs["env"] is clean
        assert kwargs["cwd"] == tmp_path.resolve()
    for directory, args in [(tmp_path.parent, ("rev-parse", "HEAD")),
                            (tmp_path, ("fetch", "origin")),
                            (tmp_path, ("rev-parse", "main")),
                            (tmp_path, ("merge-base", "--is-ancestor", "main", SOURCE)),
                            (tmp_path, ("merge-base", "--is-ancestor", "b" * 40, "c" * 40))]:
        with pytest.raises(SystemExit):
            git(directory, *args)
    assert len(calls) == 3
    module = ast.parse(program)
    env_assignment = next(node for node in module.body if isinstance(node, ast.Assign)
                          and any(isinstance(name, ast.Name) and name.id == "git_env"
                                  for name in node.targets))
    keys = [item.value for item in env_assignment.value.keys]
    assert set(keys) == {"PATH", "HOME", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL",
                         "GIT_CONFIG_SYSTEM", "GIT_NO_LAZY_FETCH", "GIT_TERMINAL_PROMPT",
                         "GIT_OPTIONAL_LOCKS"}
    assert "gate.git = runner_git" in program


@pytest.mark.parametrize("changed", ["tracked", "untracked", "head", "tree"])
def test_post_import_source_guard_rejects_dirty_or_changed_checkout(tmp_path, changed):
    """Run the actual post-import guard with deterministic Git evidence."""
    script = workflow()["jobs"]["publish"]["steps"][2]["run"]
    program = script.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    module = ast.parse(program)
    function = next(node for node in module.body
                    if isinstance(node, ast.FunctionDef) and node.name == "verify_clean_checkout")
    tree = "b" * 40
    values = {("rev-parse", "HEAD"): SOURCE, ("rev-parse", "HEAD^{tree}"): tree,
              ("status", "--porcelain", "--untracked-files=all"): ""}

    def git(directory, *args):
        assert directory == tmp_path
        return values[args]

    scope = {"runner_git": git, "root": tmp_path, "source": SOURCE, "tree": tree}
    # Execute only the checked-in guard with fixture Git results, never candidate modules.
    exec(compile(ast.Module(body=[function], type_ignores=[]), "workflow-clean-checkout", "exec"), scope)  # noqa: S102
    scope["verify_clean_checkout"]()
    if changed == "tracked":
        values[("status", "--porcelain", "--untracked-files=all")] = " M Dockerfile"
    elif changed == "untracked":
        values[("status", "--porcelain", "--untracked-files=all")] = "?? unexpected-context.txt"
    elif changed == "head":
        values[("rev-parse", "HEAD")] = "c" * 40
    else:
        values[("rev-parse", "HEAD^{tree}")] = "c" * 40
    with pytest.raises(SystemExit, match="source changed"):
        scope["verify_clean_checkout"]()
    assert program.index("proof = gate.verify_checks") < program.index("verify_clean_checkout()\n")
