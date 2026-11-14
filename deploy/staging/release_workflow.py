"""Hosted staging orchestration; never holds the owner signing key or runs remote shell."""
import argparse
import base64
import io
import json
import os
import re
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO = "AyalewGM/ai-tutor"
HOST = "40.160.97.126"
URL = "https://dev.mihureducation.com"
HOST_KEY = "SHA256:u3DFEz6/ESWWukGThMlhqZdp6707zgMcfNxDpOFpAeY"
CLIENT_KEY = "SHA256:6gJXneY2kh/lh3QGLrDLIwWw9l1pRAZqRBn4Bbu+s0o"
LIMIT = 65536


class WorkflowStopped(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise WorkflowStopped(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode()


def sha(value):
    require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value), "invalid_release_sha")
    return value


def run(args, data=None, timeout=60):
    result = subprocess.run(args, input=data, capture_output=True, timeout=timeout, check=False)
    require(result.returncode == 0, "command_failed_" + Path(args[0]).name)
    return result.stdout


def git(*args):
    return run(["git", *args]).decode().strip()


def classify(base, target):
    sha(base)
    sha(target)
    git("merge-base", "--is-ancestor", base, target)
    paths = run(["git", "diff", "--no-renames", "--name-only", "-z", base, target]).decode().split("\0")
    paths = sorted(p for p in paths if p)
    kinds = set()
    for path in paths:
        if path.startswith("alembic/"):
            kinds.add("database")
        elif path.startswith(("content_packages/", "curricula/", "curriculum/", "data/", "seeds/")):
            kinds.add("content")
        elif path.startswith("frontend/"):
            kinds.add("frontend")
        elif path.startswith(("app/", "services/")):
            kinds.add("backend")
        elif path.startswith("docs/") or path.endswith(".md"):
            kinds.add("documentation")
        else:
            kinds.add("operator_review")
    # Classification is advisory. Unknown files, deletions and renames are never ignored.
    return {"current_sha": base, "release_sha": target, "change_types": sorted(kinds),
            "changed_files": paths, "database_review_required": "database" in kinds,
            "frontend_only_delta": bool(paths) and kinds <= {"frontend", "documentation"},
            "deployment_scope": "all_three_application_images",
            "publication_requested": False, "automatic_rollback_supported": False,
            "authorization_required": True, "restore_evidence_required": True}


def api(path):
    return json.loads(run(["gh", "api", "--hostname", "github.com", f"repos/{REPO}/{path}"]))


def refresh_build(run_id, binding):
    fresh = api("actions/runs/" + run_id)
    require(all(fresh.get(k) == v for k, v in binding.items()), "image_build_changed")


def build_manifest(run_id, target):
    require(re.fullmatch(r"[1-9][0-9]*", run_id), "invalid_build_run")
    meta = api("actions/runs/" + run_id)
    require(meta.get("head_sha") == target and meta.get("head_branch") == "main"
            and meta.get("path") == ".github/workflows/staging-images.yml"
            and meta.get("event") == "workflow_dispatch"
            and meta.get("repository", {}).get("id") == 1367979340
            and meta.get("head_repository", {}).get("id") == 1367979340
            and meta.get("status") == "completed" and meta.get("conclusion") == "success",
            "successful_exact_main_image_build_required")
    listing = api(f"actions/runs/{run_id}/artifacts?per_page=100")
    require(listing["total_count"] == len(listing["artifacts"]) <= 100, "artifact_inventory_incomplete")
    expected = f"staging-images-{target}-{run_id}-{meta['run_attempt']}"
    matches = [a for a in listing["artifacts"] if a["name"] == expected and not a["expired"]]
    require(len(matches) == 1 and matches[0]["size_in_bytes"] <= 1024 * 1024, "build_artifact_missing_or_large")
    archive = run(["gh", "api", "--hostname", "github.com",
                   f"repos/{REPO}/actions/artifacts/{matches[0]['id']}/zip"])
    require(len(archive) <= 1024 * 1024, "artifact_budget")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        members = [i for i in z.infolist() if i.filename == "application-images.env"]
        require(len(members) == 1 and members[0].file_size <= 4096, "manifest_missing_or_large")
        lines = z.read(members[0]).decode().splitlines()
    values = {}
    for line in lines:
        key, value = line.split("=", 1)
        require(key not in values, "duplicate_manifest_field")
        values[key] = value
    require(set(values) == {"STAGING_RELEASE_SHA", "STAGING_API_IMAGE", "STAGING_GATEWAY_IMAGE",
                            "STAGING_FRONTEND_IMAGE"} and values["STAGING_RELEASE_SHA"] == target,
            "build_manifest_subject")
    images = {}
    for service in ("api", "gateway", "frontend"):
        value = values[f"STAGING_{service.upper()}_IMAGE"]
        require(re.fullmatch(r"ghcr\.io/ayalewgm/ai-tutor/staging-" + service + r"@sha256:[a-f0-9]{64}", value),
                "immutable_staging_image_required")
        images[service] = value
    binding = {k: meta[k] for k in ("head_sha", "head_branch", "path", "event", "repository",
                                   "head_repository", "status", "conclusion", "run_attempt")}
    refresh_build(run_id, binding)
    return images, binding


def signed_request(text, target):
    require(len(text.encode()) <= LIMIT, "request_budget")
    request = json.loads(text)
    require(set(request) == {"mode", "envelope", "signature", "evidence", "artifacts"}
            and request["mode"] == "execute-plan", "signed_deploy_request_required")
    payload = json.loads(base64.b64decode(request["envelope"], validate=True))
    require(payload.get("source_sha") == target and payload.get("actions") == ["deploy"]
            and payload.get("repository") == REPO and payload.get("environment") == "development"
            and payload.get("application_url") == URL and payload.get("database") == "mihur_staging",
            "request_scope_mismatch")
    require(len(canonical(request)) <= LIMIT, "request_budget")
    # Signature, reviewers, expiry, host identity and recovery receipt are verified by the native gate.
    return request, payload


def verify_inspection(value, base, target, images, payload):
    require(value.get("release_actions_performed") is False
            and value.get("current", {}).get("source_sha") == base,
            "running_release_changed")
    candidate = value.get("candidate", {})
    require(candidate.get("source_sha") == target, "candidate_not_prepared")
    for key in ("source_sha", "source_tree", "package_sha256", "runtime_sha256", "images"):
        require(candidate.get(key) == payload.get(key), "signed_candidate_mismatch")
    require(all(candidate["images"].get(k) == v for k, v in images.items()), "candidate_build_mismatch")
    require(all(candidate["images"].get(k) == value["current"]["images"].get(k)
                for k in ("db", "redis", "proxy")), "infrastructure_change_forbidden")
    for key in ("host_sha256", "database", "database_role", "database_cluster_id"):
        require(value.get(key) == payload.get(key), "signed_host_mismatch")


class Transport:
    def __init__(self, directory):
        root = Path(directory)
        key, known = root / "key", root / "known_hosts"
        key.write_text(os.environ["STAGING_INSPECTION_KEY"])
        known.write_text(os.environ["STAGING_KNOWN_HOSTS"])
        key.chmod(0o600)
        known.chmod(0o600)
        require(run(["ssh-keygen", "-lf", str(key)]).decode().split()[1] == CLIENT_KEY,
                "wrong_inspection_key")
        fingerprints = run(["ssh-keygen", "-lf", str(known)]).decode().splitlines()
        require(len(fingerprints) == 1 and fingerprints[0].split()[1] == HOST_KEY,
                "wrong_host_key")
        self.args = ["ssh", "-F", "/dev/null", "-T", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
                     "-o", "IdentityAgent=none", "-o", "StrictHostKeyChecking=yes",
                     "-o", f"UserKnownHostsFile={known}", "-o", "GlobalKnownHostsFile=/dev/null",
                     "-o", "ControlMaster=no", "-o", "ControlPath=none", "-o", "ConnectTimeout=15",
                     "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=3",
                     "-i", str(key), "ubuntu@" + HOST]

    def send(self, request, timeout=120):
        output = run(self.args, canonical(request), timeout)
        require(len(output) <= LIMIT, "response_budget")
        return json.loads(output)


def smoke():
    # Fixed URLs only: no invitations, cookies, credentials or learner identifiers.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for path in ("/healthz", "/backend-health", "/"):
        with opener.open(URL + path, timeout=20) as response:
            require(response.url == URL + path and response.status == 200, "public_smoke_failed")
            body = response.read(65537)
            require(len(body) <= 65536, "smoke_response_budget")
            if path == "/healthz":
                require(body.strip() == b"ok", "frontend_health_failed")
            if path == "/backend-health":
                require(json.loads(body).get("status") == "ok", "backend_health_failed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("plan", "deploy"))
    parser.add_argument("--current", required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--build-run", required=True)
    args = parser.parse_args()
    require(os.environ.get("GITHUB_REPOSITORY") == REPO
            and os.environ.get("GITHUB_REF") == "refs/heads/main"
            and os.environ.get("GITHUB_SHA") == sha(args.release)
            and git("rev-parse", "HEAD") == args.release, "main_workflow_required")
    require(api("git/ref/heads/main")["object"]["sha"] == args.release, "main_advanced_rebuild_required")
    plan = classify(args.current, args.release)
    images, build_binding = build_manifest(args.build_run, args.release)
    summary = Path(os.environ["GITHUB_STEP_SUMMARY"])
    with summary.open("a") as out:
        out.write("## Staging release plan\n\n```json\n" + json.dumps(plan, indent=2) + "\n```\n")
        out.write("Classification does not waive installed authorization or restore requirements.\n")
    if args.mode == "plan":
        return
    require(os.environ.get("STAGING_DEPLOY_ENABLED") == "true", "owner_enrollment_required")
    require(bool(plan["changed_files"]), "already_current")
    request, payload = signed_request(os.environ.get("SIGNED_REQUEST", ""), args.release)
    # Secrets are only used in this protected job and never printed or uploaded.
    with tempfile.TemporaryDirectory(prefix="mihur-ssh-") as directory:
        transport = Transport(directory)
        before = transport.send({"mode": "inspect"})
        verify_inspection(before, args.current, args.release, images, payload)
        checked = transport.send({**request, "mode": "check"})
        require(checked == {"status": "CHECKED_NO_EFFECTS", "release_actions_performed": False},
                "native_check_failed")
        refresh_build(args.build_run, build_binding)
        result = transport.send(request, timeout=1800)  # Exactly once; never retry a spent nonce.
        require(result == {"status": "EXECUTED_SIGNED_DEVELOPMENT_PLAN", "release_actions_performed": True},
                "native_deploy_not_confirmed")
        after = transport.send({"mode": "inspect"})
        require(after["current"]["source_sha"] == args.release
                and after["current"]["images"] == payload["images"], "deployed_identity_mismatch")
        smoke()
    with summary.open("a") as out:
        out.write(f"\nDeployed `{args.release}`; image identity and public HTTPS smoke passed.\n"
                  "Browser/Muse acceptance is separate. No content publication performed.\n")


if __name__ == "__main__":
    try:
        main()
    except WorkflowStopped as error:
        print("Staging workflow stopped: " + str(error))
        raise SystemExit(1) from None
    except Exception:  # noqa: BLE001 - never expose sensitive native stderr or inputs
        # Do not leak signed evidence, native stderr, private keys or arbitrary API content.
        print("Staging workflow stopped. No automatic retry or database rollback. Inspect native state before retrying.")
        raise SystemExit(1) from None
