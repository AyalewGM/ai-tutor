"""Fixed development-only owner gate. Install reviewed copies through the owner console.

This module performs no operation on import. The CLI is not a production executor.
An agent retaining host root can replace local trust; enrollment must remove that
capability before this gate is considered an authentication boundary.
"""
from __future__ import annotations

import argparse
import ast
import base64
import contextlib
import fcntl
import hashlib
import io
import json
import os
import re
import ssl
import stat
import subprocess
import sys
import time
import types
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path("/opt/mihur-staging")
CANDIDATE_ROOT = Path("/opt/mihur-staging-candidate")
DIRECTORY = Path("/etc/mihur-staging/development-owner")
PINS = DIRECTORY / "operator-pins.json"
CANDIDATE = Path("/etc/mihur-staging/development-candidate.json")
ENV = Path("/etc/mihur-staging/release.env")
MARKER = Path("/etc/mihur-staging/isolation.json")
LIBRARY = Path("/usr/local/lib/mihur-development-release")
STATE = Path("/var/backups/mihur-content/owner-authorizations")
BACKUP = Path("/var/backups/mihur-content/development-restore-evidence.json")
BACKUP_ROOT = Path("/var/backups/mihur-content")
PUBLIC_API = "https://api.github.com/repos/AyalewGM/ai-tutor"
REPOSITORY_URL = "https://github.com/AyalewGM/ai-tutor.git"
CLEAN = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": "/root", "LANG": "C.UTF-8",
         "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
         "GIT_NO_LAZY_FETCH": "1", "GIT_NO_REPLACE_OBJECTS": "1",
         "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}
DOCKER = ["/usr/bin/docker", "--host", "unix:///var/run/docker.sock"]
IMAGE_NAMES = {key: "STAGING_" + key.upper() + "_IMAGE"
               for key in ("api", "gateway", "frontend", "db", "redis", "proxy")}
CHECKS = {"test": 15368, "containers": 15368, "Semgrep SAST": 15368,
          "Trivy dependencies and secrets": 15368, "CodeQL": 57789}
CHECK_WORKFLOWS = {
    "test": (356891953, ".github/workflows/ci.yml"),
    "containers": (356891953, ".github/workflows/ci.yml"),
    "Semgrep SAST": (371762802, ".github/workflows/security.yml"),
    "Trivy dependencies and secrets": (371762802, ".github/workflows/security.yml"),
}
RUNTIME_FILES = (
    "app/services/content_publishing.py", "app/services/fraction_assessment_registry.py",
    "app/services/fraction_scoring_handoff.py", "app/services/attempt_evidence.py",
    "app/services/awards.py", "app/services/problem_selection.py",
    "app/services/published_reasoning_probe.py", "app/adaptive_response_api.py",
    "app/hint_api.py", "app/workspace_api.py", "app/identity.py", "app/diagnostic_api.py",
    "app/api.py", "scripts/ops/publish_content.py", "scripts/ops/content_learner_probe.py",
    "deploy/staging/publish_content.py", ".github/workflows/content-publisher.yml",
    "app/services/development_content_authorization.py",
    "scripts/ops/development_release_authorization.py", "deploy/staging/development_release.py",
)


class Rejected(RuntimeError):
    """Fixed safe reason only; never return native output or secret configuration."""


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def owned_bytes(path, *, limit=2 * 1024**2, modes=(0o600, 0o644)):
    """No symlink traversal, hardlinks, non-root or writable trusted ancestors."""
    path = Path(path)
    require(path.is_absolute(), "absolute_fixed_path_required")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:-1]:
            require(part not in (".", ".."), "unsafe_trusted_path")
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
            info = os.fstat(fd)
            require(info.st_uid == 0 and not info.st_mode & 0o022, "untrusted_ancestor")
        source = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(source, "rb") as stream:
            info = os.fstat(stream.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
                    and stat.S_IMODE(info.st_mode) in modes, "untrusted_file")
            data = stream.read(limit + 1)
            require(len(data) <= limit, "trusted_input_budget")
            return data
    finally:
        os.close(fd)


def command(args, *, data=None):
    try:
        result = subprocess.run(args, input=data, capture_output=True, check=False,
                                timeout=180, env=CLEAN)
    except (OSError, subprocess.TimeoutExpired):
        raise Rejected("native_command_unavailable") from None
    require(result.returncode == 0, "native_command_failed")
    return result.stdout


def _git_metadata(root, *, owner_uid=0):
    """Only standalone owner-enrolled clones; no shared/agent-writable Git metadata."""
    root = Path(root)
    require(root in (ROOT, CANDIDATE_ROOT), "fixed_git_checkout_required")
    config = root / ".git/config"
    # Validates every ancestor without following symlinks before reading any Git config.
    owned_bytes(config)
    count = 0
    pending = [root / ".git"]
    forbidden = {"commondir", "gitdir", "config.worktree", "alternates", "http-alternates", "grafts"}
    while pending:
        path = pending.pop()
        info = path.lstat()
        require(info.st_uid == owner_uid and not info.st_mode & 0o022
                and (stat.S_ISDIR(info.st_mode) or
                     (stat.S_ISREG(info.st_mode) and info.st_nlink == 1)),
                "untrusted_git_metadata")
        require(path.name not in forbidden, "external_git_metadata")
        count += 1
        require(count <= 50000, "git_metadata_budget")
        if stat.S_ISDIR(info.st_mode):
            pending.extend(path.iterdir())
    return config


def reject_git_filters(root):
    # --file/--no-includes makes config parsing inert, before any repository operation.
    config = _git_metadata(root)
    raw = command(["/usr/bin/git", "--no-pager", "-C", "/", "config", "--file", str(config), "--no-includes", "--null", "--list"])
    permitted = {"core.repositoryformatversion": "0", "core.filemode": "true", "core.bare": "false",
                 "core.logallrefupdates": "true", "remote.origin.url": REPOSITORY_URL,
                 "remote.origin.fetch": "+refs/heads/*:refs/remotes/origin/*"}
    seen = set()
    for item in raw.decode().split("\0"):
        if not item:
            continue
        key, separator, value = item.partition("\n")
        require(bool(separator) and key not in seen, "git_config_duplicate_or_invalid")
        seen.add(key)
        branch = re.fullmatch(r"branch\.[A-Za-z0-9._/-]+\.(remote|merge)", key)
        allowed_branch = branch and (value == "origin" if branch.group(1) == "remote" else
                                     re.fullmatch(r"refs/heads/[A-Za-z0-9._/-]+", value))
        require((key in permitted and value == permitted[key]) or allowed_branch,
                "unsafe_local_git_configuration")
    require({"core.repositoryformatversion", "core.bare"} <= seen, "git_configuration_incomplete")


def _git_command(root, args):
    reject_git_filters(root)
    return command(["/usr/bin/git", "--no-pager", "-C", str(root),
                    "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
                    "-c", "core.attributesFile=/dev/null", "-c", "credential.helper=",
                    "-c", "protocol.allow=never", "-c", "protocol.https.allow=always",
                    "-c", "protocol.ext.allow=never", "-c", "http.followRedirects=false",
                    "-c", "submodule.recurse=false", "-c", "http.extraHeader=", "-c", "http.proxy=",
                    "-c", "http.sslVerify=true", "-c", "http.sslCAInfo=/etc/ssl/certs/ca-certificates.crt", *args])


def git(root, *args):
    return _git_command(root, args).decode().strip()


def load_trusted():
    """The owner installs these pinned libraries; never import candidate code."""
    data = owned_bytes(PINS)
    pins = json.loads(data)
    require(canonical(pins) == data, "operator_pins_not_canonical")
    require(set(pins) == {"entrypoint_sha256", "authorization_sha256", "control_sha256"},
            "operator_pin_fields")
    require(pins["entrypoint_sha256"] == sha(owned_bytes(Path(__file__).resolve())),
            "operator_entrypoint_changed")
    modules = []
    for name, field in (("authorization", "authorization_sha256"), ("control", "control_sha256")):
        path = LIBRARY / (name + ".py")
        source = owned_bytes(path)
        require(sha(source) == pins[field], "operator_library_changed")
        module = types.ModuleType("mihur_owner_" + name)
        module.__file__ = str(path)
        sys.modules[module.__name__] = module
        # Only fixed owner-installed bytes whose exact SHA was just verified;
        # do not ask SourceFileLoader to select an unverified cached .pyc.
        exec(compile(source, str(path), "exec"), module.__dict__)  # noqa: S102 - owner-pinned verified bytes; no pycache
        modules.append(module)
    return pins, modules[0], modules[1]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, _request, _file, _code, _message, _headers, _new_url):
        return None


def github(suffix):
    """Fixed public repository API, system CA, no proxy, no credentials or redirects."""
    require(re.fullmatch(r"(?:commits/[a-f0-9]{40}(?:/check-runs\?per_page=100&page=[1-9][0-9]?|/pulls\?per_page=100)?|"
                         r"pulls/[1-9][0-9]*|git/ref/heads/[A-Za-z0-9%._/-]+|actions/runs/[1-9][0-9]*)?",
                         suffix) is not None, "github_path")
    url = PUBLIC_API + ("/" + suffix if suffix else "")
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(
            cafile="/etc/ssl/certs/ca-certificates.crt")))
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                  "User-Agent": "mihur-development-owner-gate"})
    try:
        with opener.open(request, timeout=15) as response:
            require(response.url == url, "github_redirect")
            data = response.read(2 * 1024**2 + 1)
            require(len(data) <= 2 * 1024**2, "github_response_budget")
            return json.loads(data)
    except (OSError, ValueError, urllib.error.HTTPError):
        raise Rejected("github_evidence_unavailable") from None


def verify_checks(source_sha, source_tree, root):
    repo = github("")
    require(repo["id"] == 1367979340 and repo["owner"]["id"] == 22088298, "repository_identity")
    pulls = github(f"commits/{source_sha}/pulls?per_page=100")
    candidates = [pr for pr in pulls if pr.get("state") == "open"
                  and pr.get("head", {}).get("sha") == source_sha
                  and pr["head"].get("repo", {}).get("id") == 1367979340
                  and pr.get("base", {}).get("repo", {}).get("id") == 1367979340]
    require(len(candidates) == 1, "unique_current_pull_request_required")
    pr = github("pulls/" + str(candidates[0]["number"]))
    base_ref, merge_sha = pr["base"]["ref"], pr.get("merge_commit_sha", "")
    require(pr["state"] == "open" and pr["head"]["sha"] == source_sha
            and re.fullmatch(r"[A-Za-z0-9._/-]+", base_ref)
            and re.fullmatch(r"[a-f0-9]{40}", merge_sha), "pull_request_binding")
    reference = "git/ref/heads/" + urllib.parse.quote(base_ref, safe="")
    # base.sha in normalized PR snapshots can describe creation history: read the ref.
    base_sha = github(reference)["object"]["sha"]
    require(re.fullmatch(r"[a-f0-9]{40}", base_sha), "current_base_sha")
    git(root, "merge-base", "--is-ancestor", base_sha, source_sha)
    merged = github("commits/" + merge_sha)
    require(merged["sha"] == merge_sha and merged["commit"]["tree"]["sha"] == source_tree
            and [parent["sha"] for parent in merged["parents"]] == [base_sha, source_sha],
            "tested_merge_tree_differs_from_release")
    rows = []
    for page in range(1, 11):
        value = github(f"commits/{source_sha}/check-runs?per_page=100&page={page}")
        require(type(value.get("total_count")) is int and value["total_count"] <= 1000,
                "check_inventory_budget")
        rows.extend(value["check_runs"])
        if len(rows) >= value["total_count"]:
            break
    else:
        raise Rejected("incomplete_check_inventory")
    run_metadata = {}  # Invocation-local only; never reuse a positive decision across operations.
    for name, producer in CHECKS.items():
        matches = [row for row in rows if row.get("name") == name
                   and row.get("head_sha") == source_sha and row.get("app", {}).get("id") == producer]
        require(bool(matches), "mandatory_check_missing")
        latest = max(matches, key=lambda row: row["id"])
        require(latest.get("status") == "completed" and latest.get("conclusion") == "success",
                "mandatory_check_not_passed")
        if name in CHECK_WORKFLOWS:
            details = latest.get("details_url")
            match = re.fullmatch(
                r"https://github\.com/AyalewGM/ai-tutor/actions/runs/([1-9][0-9]*)/job/[1-9][0-9]*",
                details) if isinstance(details, str) else None
            require(match is not None, "check_details_not_trusted_run")
            run_id = int(match.group(1))
            if run_id not in run_metadata:
                run_metadata[run_id] = github("actions/runs/" + str(run_id))
            run = run_metadata[run_id]
            workflow_id, workflow_path = CHECK_WORKFLOWS[name]
            require(run.get("id") == run_id and run.get("workflow_id") == workflow_id
                    and run.get("path") == workflow_path and run.get("event") == "pull_request"
                    and run.get("head_sha") == source_sha
                    and run.get("head_branch") == pr["head"]["ref"]
                    and run.get("head_repository", {}).get("id") == 1367979340
                    and run.get("repository", {}).get("id") == 1367979340
                    and run.get("status") == "completed" and run.get("conclusion") == "success"
                    and any(item.get("number") == pr["number"] for item in run.get("pull_requests", [])),
                    "check_workflow_run_not_approved")
        if name in {"test", "containers"}:
            require(any(item.get("number") == pr["number"] for item in latest.get("pull_requests", [])),
                    "ci_check_not_bound_to_selected_pull_request")
    fresh = github("pulls/" + str(pr["number"]))
    require(fresh["head"]["sha"] == source_sha and fresh["head"]["ref"] == pr["head"]["ref"]
            and fresh["merge_commit_sha"] == merge_sha
            and fresh["base"]["ref"] == base_ref and github(reference)["object"]["sha"] == base_sha,
            "pull_request_changed_during_check")
    return {"pull_request": pr["number"], "head_sha": source_sha, "base_sha": base_sha,
            "test_merge_sha": merge_sha, "tested_tree": source_tree,
            "head_and_test_merge_tree_equal": True}


class Operator:
    """Fixed methods are test-seamed, not selectable commands or contexts from clients."""
    def __init__(self, auth, control, pins):
        self.auth, self.control, self.pins = auth, control, pins
        self.clock = lambda: int(time.time())
        self.deadline = None
        self.policy_digest = None
        self.api_identity = None
        self.ci_evidence = None

    def authenticate_owner(self, envelope, signature, payload, bundle, artifacts):
        policy = self.auth.protected_json(DIRECTORY / "policy.json")
        require(policy["operator_pins_sha256"] == self.auth.digest(self.pins), "operator_policy_changed")
        projection = {key: payload[key] for key in self.auth.BINDINGS}
        # This proves the detached owner signature ONLY. It is not native target evidence.
        self.auth.verify(envelope, signature, policy, projection, bundle, artifacts, now=self.clock())

    def guard_effect(self):
        require(self.deadline is not None and self.clock() < self.deadline, "operation_expired")
        policy = self.auth.protected_json(DIRECTORY / "policy.json")
        self.auth.validate_policy(policy)
        require(self.auth.digest(policy) == self.policy_digest, "operation_policy_revoked_or_changed")

    def read_configuration(self, payload):
        policy = self.auth.protected_json(DIRECTORY / "policy.json")
        require(policy["operator_pins_sha256"] == self.auth.digest(self.pins), "operator_policy_changed")
        self.auth.validate_policy(policy)
        marker = json.loads(owned_bytes(MARKER))
        machine = owned_bytes(Path("/etc/machine-id"), modes=(0o444, 0o644)).decode().strip()
        require(sha(machine.encode()) == self.auth.HOST and marker.get("machine_id") == machine
                and marker.get("environment") == "staging"
                and marker.get("dedicated_nonproduction_host") is True
                and marker.get("synthetic_data_only") is True
                and marker.get("no_production_credentials_or_mounts") is True
                and bool(marker.get("owner_inventory_evidence")), "native_isolation_identity")
        current = self.control.values(owned_bytes(ENV).decode())
        if "deploy" in payload["actions"]:
            candidate = self.auth.protected_json(CANDIDATE)
            require(set(candidate) == {"source_sha", "images"}, "candidate_fields")
            require(all(candidate["images"][key] == current[field]
                        for key, field in IMAGE_NAMES.items() if key in {"db", "redis", "proxy"}),
                    "infrastructure_upgrade_outside_ontario_plan")
            root, target = CANDIDATE_ROOT, candidate
        else:
            root = ROOT
            target = {"source_sha": current["STAGING_RELEASE_SHA"],
                      "images": {key: current[field] for key, field in IMAGE_NAMES.items()}}
        return policy, current, root, target

    def source_context(self, root):
        reject_git_filters(root)
        require(git(root, "rev-parse", "--show-toplevel") == str(root), "git_worktree_redirect")
        require(not git(root, "status", "--porcelain"), "source_checkout_dirty")
        source_sha, tree = git(root, "rev-parse", "HEAD"), git(root, "rev-parse", "HEAD^{tree}")
        require(re.fullmatch(r"[a-f0-9]{40}", source_sha) and re.fullmatch(r"[a-f0-9]{40}", tree),
                "native_source_identity")
        # No candidate Python imports/eval, arbitrary paths or external filters.
        publisher = owned_bytes(root / "app/services/content_publishing.py")
        parsed = ast.parse(publisher)
        declared = [ast.literal_eval(node.value) for node in parsed.body
                    if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                    and target.id == "RUNTIME_FILES" for target in node.targets)]
        require(len(declared) == 1 and type(declared[0]) is tuple
                and len(declared[0]) == len(RUNTIME_FILES)
                and all(type(path) is str for path in declared[0])
                and set(declared[0]) == set(RUNTIME_FILES), "runtime_file_inventory")
        runtime = self.auth.digest({path: sha(owned_bytes(root / path)) for path in RUNTIME_FILES})
        manifest = json.loads(owned_bytes(root / "content_packages/mth1w-signed-two-step-v1.json"))
        require(manifest["runtime_sha256"] == runtime
                and sha(owned_bytes(root / "scripts/author_ontario_linear_depth.py"))
                == manifest["generator_sha256"], "native_package_runtime_changed")
        revision = manifest["content_revision"]
        require(re.fullmatch(r"[a-f0-9]{40}", revision), "content_revision")
        git(root, "merge-base", "--is-ancestor", revision, source_sha)
        require(sha(_git_command(root, ["show", revision + ":scripts/author_ontario_linear_depth.py"]))
                == manifest["generator_sha256"], "content_revision_bytes")
        package = self.auth.digest({key: value for key, value in manifest.items() if key != "review_evidence"})
        return {"source_sha": source_sha, "source_tree": tree,
                "package_sha256": package, "runtime_sha256": runtime}

    def database_identity(self):
        raw = command(DOCKER + ["exec", "mihur-staging-db-1", "env", "-i",
                      "PATH=/usr/local/bin:/usr/bin:/bin", "PGHOST=/var/run/postgresql",
                      "PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=10000 -c search_path=pg_catalog",
                      "psql", "-X", "-w", "-qAt", "-v", "ON_ERROR_STOP=1", "-U", "mihur_staging",
                      "-d", "mihur_staging", "-c", ("SELECT pg_catalog.json_build_object('database',pg_catalog.current_database(),"
                      "'database_role',current_user,'database_cluster_id',system_identifier::text) "
                      "FROM pg_catalog.pg_control_system()") ])
        identity = json.loads(raw)
        require(identity.get("database") == "mihur_staging"
                and identity.get("database_role") == "mihur_staging"
                and re.fullmatch(r"[0-9]{1,20}", identity.get("database_cluster_id", "")),
                "native_database_identity")
        return identity

    def images(self, references, source_sha, *, running):
        require(type(references) is dict and set(references) == set(IMAGE_NAMES), "native_image_fields")
        services = {"api": "tutor-api", "gateway": "llm-gateway", "frontend": "frontend",
                    "db": "db", "redis": "redis", "proxy": "proxy"}
        for key, reference in references.items():
            require(isinstance(reference, str) and re.fullmatch(
                r"[a-z0-9./_-]+@sha256:[a-f0-9]{64}", reference), "immutable_image_required")
            image = json.loads(command(DOCKER + ["image", "inspect", reference]))[0]
            require(reference in image.get("RepoDigests", []), "image_digest_not_local")
            if key in {"api", "gateway", "frontend"}:
                require(reference.startswith("ghcr.io/ayalewgm/ai-tutor/staging-" + key + "@"),
                        "application_image_repository")
                require((image.get("Config", {}).get("Labels") or {}).get(
                    "org.opencontainers.image.revision") == source_sha, "image_source_revision")
            if running:
                name = "mihur-staging-" + services[key] + "-1"
                item = json.loads(command(DOCKER + ["inspect", name]))[0]
                require(item["State"]["Running"] and item["Image"] == image["Id"]
                        and item["Config"]["Image"] == reference, "running_image_changed")
                if key == "api":
                    self.api_identity = {"id": item["Id"], "image": image["Id"],
                                         "reference": reference, "source_sha": source_sha}

    def backup(self, context, now):
        directory = self.auth._trusted_directory(BACKUP_ROOT, owner_uid=0, private=True)
        os.close(directory)
        value = self.auth.protected_json(BACKUP)
        require(set(value) == {"schema", "created_at", "source_database", "database_cluster_id",
                              "archive", "archive_sha256", "restore_verified", "disposable_restore"},
                "backup_evidence_fields")
        path = Path(value["archive"])
        require(value["schema"] == "MIHUR_DEVELOPMENT_RESTORE_EVIDENCE_V1"
                and value["source_database"] == context["database"]
                and value["database_cluster_id"] == context["database_cluster_id"]
                and value["restore_verified"] is True and value["disposable_restore"] is True
                and type(value["created_at"]) is int and 0 <= now - value["created_at"] <= 3600
                and path.parent == BACKUP_ROOT and re.fullmatch(r"[a-f0-9-]+\.dump", path.name),
                "backup_not_current_verified_disposable")
        require(sha(owned_bytes(path, limit=64 * 1024**2, modes=(0o600,))) == value["archive_sha256"],
                "backup_archive_changed")
        return {"preflight": True, "restore_verified": True, "release_sha": context["source_sha"],
                "package_digest": context["package_sha256"], "backup_sha256": value["archive_sha256"]}

    def collect(self, payload, bundle):
        self.configure_control(overlay=False)
        self.preflight()
        policy, current, root, target = self.read_configuration(payload)
        self.images({key: current[field] for key, field in IMAGE_NAMES.items()},
                    current["STAGING_RELEASE_SHA"], running=True)
        context = {**self.auth.SCOPE, **self.source_context(root), **self.database_identity(),
                   "images": target["images"], "evidence_sha256": self.auth.digest(bundle),
                   "actions": payload["actions"]}
        if "publish" in payload["actions"]:
            manifest = json.loads(owned_bytes(root / "content_packages/mth1w-signed-two-step-v1.json"))
            provenance = manifest.get("standards_provenance", {})
            require(manifest.get("activation") == "staging" and manifest.get("review_evidence") == []
                    and provenance.get("acceptance") == "ACCEPTED_PARTIAL_PRACTICE"
                    and provenance.get("coverage_credit") is False
                    and provenance.get("production_taxonomy_activation") is False,
                    "package_not_accepted_for_development_publication")
        require(context["source_sha"] == target["source_sha"], "candidate_source_changed")
        self.images(context["images"], context["source_sha"], running="deploy" not in payload["actions"])
        self.ci_evidence = verify_checks(context["source_sha"], context["source_tree"], root)
        remote = github("commits/" + context["source_sha"])
        require(remote["sha"] == context["source_sha"]
                and remote["commit"]["tree"]["sha"] == context["source_tree"], "remote_source_changed")
        return policy, context, current

    def configure_control(self, *, overlay=True):
        control = self.control
        control.ROOT, control.CONFIG, control.ENV, control.MARKER = ROOT, ROOT / "deploy/staging/compose.yml", ENV, MARKER
        control.DOCKER = DOCKER
        control.CLEAN = CLEAN
        def fixed_run(args, capture=True):
            if args[0] in ("git", "/usr/bin/git"):
                require(len(args) >= 4 and args[1:3] == ["-C", str(ROOT)], "control_git_path")
                reject_git_filters(ROOT)
                value = git(ROOT, *args[3:])
            else:
                executable = (args[0] if args[0].startswith("/") else
                              "/usr/sbin/swapon" if args[0] == "swapon" else "/usr/bin/" + args[0])
                require(executable in {"/usr/bin/docker", "/usr/bin/free", "/usr/bin/nproc",
                                       "/usr/bin/df", "/usr/sbin/swapon", "/usr/bin/ss"},
                        "control_executable")
                value = command([executable, *args[1:]]).decode()
            return value if capture else None
        control.run = fixed_run
        control.COMPOSE = DOCKER + ["compose", "--project-name", "mihur-staging", "--env-file", str(ENV),
                                    "-f", str(control.CONFIG)]
        if overlay:
            control.COMPOSE += ["-f", str(ROOT / "deploy/staging/compose.development-owner.yml")]

    def preflight(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.control.preflight()

    def deploy(self, context, current):
        # Exact signed target only, after nonce reservation. Never seed learner data.
        self.guard_effect()
        self.configure_control(overlay=False)
        command(self.control.COMPOSE + ["stop", "proxy", "frontend", "tutor-api", "llm-gateway", "redis"])
        self.guard_effect()
        git(ROOT, "fetch", "--no-tags", REPOSITORY_URL, context["source_sha"])
        git(ROOT, "checkout", "--detach", context["source_sha"])
        target = {**current, "STAGING_RELEASE_SHA": context["source_sha"],
                  **{field: context["images"][key] for key, field in IMAGE_NAMES.items()}}
        self.write(ENV, "".join(key + "=" + target[key] + "\n" for key in sorted(target)).encode(), 0o600)
        self.configure_control()
        self.preflight()
        compose = self.control.COMPOSE
        for args in (["--profile", "tools", "pull"],
                     ["up", "-d", "--no-build", "--wait", "db"],
                     ["run", "--rm", "--no-deps", "migrate"],
                     ["up", "-d", "--no-build", "--wait", "--wait-timeout", "180"]):
            self.guard_effect()
            command(compose + args)

    def reinspect(self, context):
        actual = {**self.source_context(ROOT), **self.database_identity()}
        require(all(context[key] == value for key, value in actual.items()), "post_deploy_subject_changed")
        self.images(context["images"], context["source_sha"], running=True)
        # Inspect actual image bytes with fixed stdlib code, not an image label alone.
        script = ("import hashlib,json;from pathlib import Path\n"
                  "paths=" + repr(RUNTIME_FILES) + "\n"
                  "v={p:hashlib.sha256((Path('/app')/p).read_bytes()).hexdigest() for p in paths}\n"
                  "print(hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),"
                  "ensure_ascii=False).encode()).hexdigest())\n").encode()
        measured = command(DOCKER + ["exec", "-i", "mihur-staging-tutor-api-1",
                                     "python", "-I", "-S", "-B", "-"], data=script).decode().strip()
        require(measured == context["runtime_sha256"], "running_runtime_changed")
        self.configure_control()
        self.preflight()

    def write(self, path, data, mode=0o644):
        """Atomic, no-follow root-directory write. Caller never supplies a path."""
        directory = self.auth._trusted_directory(path.parent, owner_uid=0)
        temporary = ".pending-" + os.urandom(16).hex()
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         mode, dir_fd=directory)
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), mode)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            os.close(directory)

    def revoke(self):
        self.write(DIRECTORY / "grant.json", canonical({"schema": "MIHUR_DEVELOPMENT_RUNTIME_GRANT_V1",
                                                       "state": "REVOKED"}))

    def revoke_or_stop(self):
        try:
            self.revoke()
            return
        except (OSError, ValueError, Rejected):
            self._stop_inspected_api()

    def _stop_inspected_api(self):
        # Never stop a project-wide collection or an uninspected replacement.
        target = self.api_identity
        require(target is not None, "emergency_hold_no_inspected_api")
        try:
            item = json.loads(command(DOCKER + ["inspect", target["id"]]))[0]
            require(item["Id"] == target["id"] and item["Image"] == target["image"]
                    and item["Config"]["Image"] == target["reference"]
                    and (item["Config"].get("Labels") or {}).get("org.opencontainers.image.revision")
                    == target["source_sha"], "emergency_hold_api_changed")
            command(DOCKER + ["stop", "--time", "5", target["id"]])
        except (OSError, ValueError, KeyError, IndexError, TypeError, Rejected):
            raise Rejected("emergency_hold_revoke_and_exact_api_stop_failed") from None

    def publish(self, context, receipt):
        self.configure_control()
        prefix = self.control.COMPOSE + ["exec", "-T", "tutor-api", "python", "-m"]
        self.guard_effect()
        command(prefix + ["scripts.ops.publish_content", "publish"], data=canonical(receipt))
        self.guard_effect()
        probe = json.loads(command(prefix + ["scripts.ops.content_learner_probe"]))
        require(probe.get("passed") is True, "synthetic_learner_probe_failed")

    def rollback(self, receipt):
        self.guard_effect()
        self.configure_control()
        command(self.control.COMPOSE + ["exec", "-T", "tutor-api", "python", "-m",
                                        "scripts.ops.publish_content", "rollback"], data=canonical(receipt))

    def execute(self, envelope, signature, bundle, artifacts, *, execute=False, now=None):
        self.clock = (lambda: now) if now is not None else lambda: int(time.time())
        payload = self.auth.strict_json(envelope)
        require(tuple(payload.get("actions", [])) in self.auth.ACTION_PLANS, "unsupported_action_plan")
        self.authenticate_owner(envelope, signature, payload, bundle, artifacts)
        policy, context, current = self.collect(payload, bundle)
        verified_at = self.clock()
        verified = self.auth.verify(envelope, signature, policy, context, bundle, artifacts, now=verified_at)
        receipt = self.backup(context, self.clock())
        if not execute:
            return {"status": "CHECKED_NO_EFFECTS", "source_sha": context["source_sha"],
                    "ci_binding": self.ci_evidence}
        self.auth.reserve_nonce(verified, STATE, now=self.clock())
        self.deadline, self.policy_digest = payload["expires_at"], self.auth.digest(policy)
        # After this line every error burns the authorization, including crashes.
        try:
            if "deploy" in payload["actions"]:
                self.revoke()
                self.deploy(context, current)
            self.reinspect(context)
            if "publish" in payload["actions"]:
                self.guard_effect()
                grant_verified_at = self.clock()
                current_policy = self.auth.protected_json(DIRECTORY / "policy.json")
                fresh_verified = self.auth.verify(envelope, signature, current_policy, context,
                                                  bundle, artifacts, now=grant_verified_at)
                self.guard_effect()
                grant = {"schema": "MIHUR_DEVELOPMENT_RUNTIME_GRANT_V1", "state": "ACTIVE",
                         "policy_sha256": self.auth.digest(current_policy),
                         "authorization_sha256": fresh_verified.payload_sha256, "nonce": payload["nonce"],
                         "verified_at": grant_verified_at,
                         "owner_runtime_expires_at": payload["runtime_expires_at"],
                         "runtime_expires_at": min(payload["runtime_expires_at"], self.deadline,
                                                   grant_verified_at + 300),
                         "release": context}
                self.write(DIRECTORY / "authorization.json", envelope)
                self.write(DIRECTORY / "authorization.sig", signature)
                self.write(DIRECTORY / "context.json", canonical(context))
                self.write(DIRECTORY / "grant.json", canonical(grant))
                self.publish(context, receipt)
                self.guard_effect()
                grant["runtime_expires_at"] = payload["runtime_expires_at"]
                self.write(DIRECTORY / "grant.json", canonical(grant))
            elif payload["actions"] == ["rollback"]:
                self.revoke()
                self.rollback(receipt)
        except Exception:
            self.revoke_or_stop()
            raise
        return {"status": "EXECUTED_SIGNED_DEVELOPMENT_PLAN", "source_sha": context["source_sha"],
                "authorization_sha256": verified.payload_sha256,
                "ci_binding": self.ci_evidence,
                "new_student_availability_claim": False}


def execute_serialized(operator, envelope, signature, bundle, artifacts, *, execute=False):
    if not execute:
        return operator.execute(envelope, signature, bundle, artifacts)
    directory = operator.auth._trusted_directory(STATE, owner_uid=0, private=True)
    lock = None
    try:
        # The owner creates this lock during enrollment; unauthenticated requests
        # must not create privileged state before preliminary signature checking.
        lock = os.open("operation.lock", os.O_RDWR | os.O_NOFOLLOW, dir_fd=directory)
        info = os.fstat(lock)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
                and stat.S_IMODE(info.st_mode) == 0o600, "operation_lock_identity")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return operator.execute(envelope, signature, bundle, artifacts, execute=True)
    finally:
        if lock is not None:
            os.close(lock)
        os.close(directory)


def ssh_request(operator):
    """A forced command ignores SSH_ORIGINAL_COMMAND and accepts no filesystem paths."""
    request = operator.auth.strict_json(sys.stdin.buffer.read(operator.auth.MAX_BYTES + 1))
    mode = request.get("mode")
    if mode == "inspect":
        require(set(request) == {"mode"}, "inspect_fields")
        machine_hash = sha(owned_bytes(Path("/etc/machine-id"), modes=(0o444, 0o644)).strip())
        require(machine_hash == operator.auth.HOST, "inspect_development_host_only")
        cfg = operator.control.values(owned_bytes(ENV).decode())
        result = {"current": {"source_sha": git(ROOT, "rev-parse", "HEAD"),
                              "images": {key: cfg[field] for key, field in IMAGE_NAMES.items()}},
                  **operator.database_identity(),
                  "host_sha256": machine_hash,
                  "release_actions_performed": False}
        try:
            candidate = operator.auth.protected_json(CANDIDATE)
        except FileNotFoundError:
            result["candidate"] = {"status": "NOT_PREPARED"}
        else:
            require(set(candidate) == {"source_sha", "images"}, "candidate_fields")
            preview = operator.source_context(CANDIDATE_ROOT)
            require(preview["source_sha"] == candidate["source_sha"], "candidate_source_changed")
            operator.images(candidate["images"], preview["source_sha"], running=False)
            result["candidate"] = {**preview, "images": candidate["images"]}
        return result
    require(mode in {"check", "execute-plan"} and set(request) == {
        "mode", "envelope", "signature", "evidence", "artifacts"}, "ssh_request_fields")
    require(type(request["artifacts"]) is dict and len(request["artifacts"]) == 5,
            "ssh_review_inventory")
    def decoded(value, limit):
        require(isinstance(value, str), "ssh_encoded_input")
        try:
            data = base64.b64decode(value, validate=True)
        except ValueError:
            raise Rejected("ssh_encoded_input") from None
        require(0 < len(data) <= limit, "ssh_input_budget")
        return data
    envelope = decoded(request["envelope"], operator.auth.MAX_BYTES)
    signature = decoded(request["signature"], 8192)
    artifacts = {}
    for digest, value in request["artifacts"].items():
        require(re.fullmatch(r"[a-f0-9]{64}", digest), "ssh_artifact_name")
        artifacts[digest] = decoded(value, operator.auth.MAX_BYTES)
    return execute_serialized(operator, envelope, signature, request["evidence"], artifacts,
                              execute=mode == "execute-plan")


def main():
    parser = argparse.ArgumentParser(description="Owner-only fixed development release gate")
    parser.add_argument("mode", choices=["check", "execute-plan", "ssh-request"])
    for name in ("envelope", "signature", "evidence", "artifacts"):
        parser.add_argument("--" + name)
    args = parser.parse_args()
    require(os.geteuid() == 0, "trusted_owner_operator_required")
    os.environ.clear()
    os.environ.update(CLEAN)
    pins, auth, control = load_trusted()
    operator = Operator(auth, control, pins)
    if args.mode == "ssh-request":
        require(all(getattr(args, name) is None for name in ("envelope", "signature", "evidence", "artifacts")),
                "ssh_paths_forbidden")
        print(json.dumps(ssh_request(operator)))
        return
    require(all(getattr(args, name) for name in ("envelope", "signature", "evidence", "artifacts")),
            "operator_input_required")
    envelope = auth._input(args.envelope)
    bundle = auth.strict_json(auth._input(args.evidence))
    artifacts = {}
    for review in bundle.get("reviews", []):
        digest = review.get("artifact_sha256") if type(review) is dict else None
        require(isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest), "artifact_name")
        artifacts[digest] = auth._input(Path(args.artifacts) / (digest + ".txt"))
    result = execute_serialized(operator, envelope, auth._input(args.signature, 8192),
                                bundle, artifacts, execute=args.mode == "execute-plan")
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - no native stderr, DSNs, passwords or private paths
        reason = str(exc) if isinstance(exc, Rejected) else "development_gate_rejected"
        print(json.dumps({"status": "REJECTED", "reason": reason}), file=sys.stderr)
        raise SystemExit(1) from None
