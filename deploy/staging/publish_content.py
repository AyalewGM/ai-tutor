"""One command on the dedicated staging host; uses existing guarded Compose stack.

sudo python deploy/staging/publish_content.py publish --sha <exact deployed SHA>
"""
import argparse
import fcntl
import hashlib
import json
import re
import stat
import subprocess
import sys
import uuid
from pathlib import Path

import control


def command(args, *, data=None):
    return subprocess.run(args, input=data, capture_output=True,
                          check=True, env=control.CLEAN).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["dry-run", "publish", "rollback", "report"])
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    control.require(re.fullmatch(r"[a-f0-9]{40}", args.sha), "Exact 40-character SHA required")
    with Path("/run/lock/mihur-content-publisher.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        control.preflight()
        cfg = control.values(control.ENV.read_text())
        control.require(cfg["STAGING_RELEASE_SHA"] == args.sha, "Requested SHA is not deployed")
        manifest = json.loads((control.ROOT / "content_packages/mth1w-signed-two-step-v1.json").read_text())
        revision = manifest["content_revision"]
        control.require(re.fullmatch(r"[a-f0-9]{40}", revision), "Invalid content revision")
        command(["git", "-C", str(control.ROOT), "merge-base", "--is-ancestor", revision, args.sha])
        source = command(["git", "-C", str(control.ROOT), "show",
                          revision + ":scripts/author_ontario_linear_depth.py"])
        control.require(hashlib.sha256(source).hexdigest() == manifest["generator_sha256"],
                        "Content source differs from reviewed revision")
        policy = Path("/etc/mihur-staging/content-review-policy.json")
        policy_info = policy.lstat()
        control.require(stat.S_ISREG(policy_info.st_mode) and policy_info.st_uid == 0
                        and stat.S_IMODE(policy_info.st_mode) == 0o644,
                        "Public review policy must be root-owned regular file, mode 0644")
        ids = control.run(control.COMPOSE + ["ps", "-q", "tutor-api"]).split()
        control.require(len(ids) == 1, "Exactly one running API container required")
        info = json.loads(control.run(control.DOCKER + ["inspect", ids[0]]))[0]
        control.require(info["Config"]["Image"] == cfg["STAGING_API_IMAGE"], "Wrong API image")
        image = json.loads(control.run(control.DOCKER + ["image", "inspect", cfg["STAGING_API_IMAGE"]]))[0]
        control.require(image["Config"]["Labels"].get("org.opencontainers.image.revision") == args.sha,
                        "API image revision differs from requested SHA")
        api = control.COMPOSE + ["exec", "-T", "tutor-api"]
        module = ["python", "-m", "scripts.ops.publish_content"]
        preview = json.loads(command(api + module + ["dry-run"]))
        if args.action == "dry-run":
            print(json.dumps(preview))
            return
        if args.action == "report":
            print(command(api + module + ["report"]).decode())
            return
        if args.action == "publish":
            control.require(preview["authorization"] == "APPROVED", preview["authorization"])
        db = control.COMPOSE + ["exec", "-T", "db"]
        suffix = uuid.uuid4().hex
        backup_dir = Path("/var/backups/mihur-content")
        backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        dump = command(db + ["pg_dump", "-U", "mihur_staging", "-d", "mihur_staging", "-Fc"])
        control.require(len(dump) > 100, "Empty backup")
        backup = backup_dir / f"{args.sha}-{suffix}.dump"
        backup.write_bytes(dump)
        backup.chmod(0o600)
        command(db + ["pg_restore", "--list"], data=dump)
        scratch = "mihur_restore_" + suffix
        command(db + ["createdb", "-U", "mihur_staging", scratch])
        try:
            command(db + ["pg_restore", "-U", "mihur_staging", "-d", scratch,
                          "--exit-on-error", "--no-owner", "--no-privileges"], data=dump)
        finally:
            command(db + ["dropdb", "-U", "mihur_staging", scratch])
        receipt = {"preflight": True, "restore_verified": True, "release_sha": args.sha,
                   "package_digest": preview["package_digest"],
                   "backup_sha256": hashlib.sha256(dump).hexdigest(), "backup": str(backup)}
        result = json.loads(command(api + module + [args.action], data=json.dumps(receipt).encode()))
        # Publication is provisional until the live learner probe succeeds.
        if args.action == "publish":
            try:
                probe = json.loads(command(api + ["python", "-m", "scripts.ops.content_learner_probe"]))
                control.require(probe.get("passed") is True, "Live learner probe failed")
                result["staging_learner_verified"] = True
                result["learner_probe"] = probe
            except Exception:  # noqa: BLE001 - rollback/redact at command boundary
                command(api + module + ["rollback"], data=json.dumps(receipt).encode())
                raise RuntimeError("Live learner probe failed; package disabled; inspect synthetic evidence") from None
        result["release_sha"] = args.sha
        (backup_dir / f"{suffix}.json").write_text(json.dumps({"receipt": receipt, "result": result}))
        print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - redact operator errors
        message = str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__
        print(f"BLOCKED: {message}; no student-readiness claim", file=sys.stderr)
        sys.exit(1)
