#!/usr/bin/env python3
"""Staging-only guarded commands. No remote Docker context or arbitrary Compose args."""
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "deploy/staging/compose.yml"
ENV = Path("/etc/mihur-staging/release.env")
MARKER = Path("/etc/mihur-staging/isolation.json")
PROJECT = "mihur-staging"
# Explicit environment prevents inherited DATABASE_URL/Compose/Docker overrides.
CLEAN = {"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
         "HOME": str(Path.home())}
DOCKER = ["docker", "--host", "unix:///var/run/docker.sock"]
COMPOSE = DOCKER + ["compose", "--project-name", PROJECT, "--env-file", str(ENV),
                    "-f", str(CONFIG)]


def run(args, capture=True):
    return subprocess.run(args, env=CLEAN, check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def secure(path):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0
            and stat.S_IMODE(info.st_mode) == 0o600,
            f"{path}: must be a root-owned regular file with mode 0600")


def values(text):
    result = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        require(key not in result, "Duplicate environment key")
        result[key] = value
    expected = {"STAGING_DB_PASSWORD", "STAGING_RELEASE_SHA"} | {
        f"STAGING_{name}_IMAGE" for name in
        ("API", "GATEWAY", "FRONTEND", "DB", "REDIS", "PROXY")}
    require(set(result) == expected, "Unexpected or missing environment keys")
    require(re.fullmatch(r"[a-f0-9]{64}", result["STAGING_DB_PASSWORD"]),
            "Password must be 64 random hex characters")
    require(re.fullmatch(r"[a-f0-9]{40}", result["STAGING_RELEASE_SHA"]), "Invalid SHA")
    for key, value in result.items():
        if key.endswith("_IMAGE"):
            require(re.fullmatch(r"[a-z0-9./:_-]+@sha256:[a-f0-9]{64}", value),
                    f"{key}: immutable digest required")
    return result


def inventory():
    ids = run(DOCKER + ["ps", "-aq"]).split()
    if ids:
        for item in json.loads(run(DOCKER + ["inspect", *ids])):
            labels = item["Config"].get("Labels") or {}
            require(labels.get("com.docker.compose.project") == PROJECT,
                    "Foreign container present; dedicated staging host required")
            for mount in item.get("Mounts", []):
                if mount["Type"] == "volume":
                    require(mount["Name"] in {PROJECT + "_" + n for n in
                            ("database", "proxy_data", "proxy_config")},
                            "Unexpected container volume")
                else:
                    require(mount["Type"] == "bind" and mount["Source"] ==
                            str(CONFIG.parent / "Caddyfile") and not mount["RW"],
                            "Unexpected bind mount")
    names = run(DOCKER + ["volume", "ls", "-q"]).split()
    if names:
        for volume in json.loads(run(DOCKER + ["volume", "inspect", *names])):
            require(volume["Name"] in {PROJECT + "_" + n for n in
                    ("database", "proxy_data", "proxy_config")}
                    and (volume.get("Labels") or {}).get("com.docker.compose.project")
                    == PROJECT and volume["Driver"] == "local" and not volume.get("Options"),
                    "Foreign/externally backed volume; STOP")


def preflight():
    require(os.geteuid() == 0, "Run via sudo on the verified dedicated staging VPS")
    for path in (ENV, MARKER):
        secure(path)
    cfg = values(ENV.read_text())
    marker = json.loads(MARKER.read_text())
    require(marker.get("machine_id") == Path("/etc/machine-id").read_text().strip()
            and marker.get("environment") == "staging"
            and marker.get("dedicated_nonproduction_host") is True
            and marker.get("synthetic_data_only") is True
            and marker.get("no_production_credentials_or_mounts") is True
            and bool(marker.get("owner_inventory_evidence")),
            "Missing verified host isolation attestation; STOP")
    require(run(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).strip()
            == cfg["STAGING_RELEASE_SHA"], "Checkout and release SHA differ")
    require(not run(["git", "-C", str(ROOT), "status", "--porcelain"]),
            "Checkout must be clean")
    run(DOCKER + ["compose", "version"], False)
    info = json.loads(run(DOCKER + ["info", "--format", "{{json .}} "]))
    require(info.get("MemoryLimit") and info.get("SwapLimit"),
            "Docker memory/swap limit support required")
    inventory()
    mem = dict(re.findall(r"^(\w+):\s+(\d+)", Path("/proc/meminfo").read_text(), re.M))
    require(int(mem["MemTotal"]) >= 1800000, "Less than nominal 2 GB RAM")
    running = bool(run(DOCKER + ["ps", "-q"]).strip())
    require(int(mem["MemAvailable"]) >= (256000 if running else 1400000),
            "Insufficient available memory")
    require(int(mem["SwapTotal"]) >= 1000000, "At least 1 GB swap required; configure manually")
    require(shutil.disk_usage(info["DockerRootDir"]).free >= 10 * 1024**3,
            "Need at least 10 GiB free Docker disk")
    for cmd in (["free", "-h"], ["nproc"], ["df", "-h"], ["swapon", "--show"],
                ["ss", "-ltn"]):
        run(cmd, False)
    if not running:
        listeners = run(["ss", "-H", "-ltn"])
        require(not re.search(r":8443\s", listeners), "Port 8443 already occupied")
    run(COMPOSE + ["config", "--quiet"])
    print("Preflight PASS: host attestation + local Docker inventory; not runtime acceptance.")


def main():
    action = sys.argv[1] if len(sys.argv) == 2 else ""
    require(action in {"preflight", "pull", "start-db", "migrate", "seed", "start", "stop",
                       "smoke", "metrics"}, "Unsupported staging action")
    preflight()
    commands = {
        "pull": ["--profile", "tools", "pull"],
        "start-db": ["up", "-d", "--no-build", "--wait", "db"],
        "migrate": ["run", "--rm", "--no-deps", "migrate"],
        "seed": ["run", "--rm", "--no-deps", "migrate", "python", "scripts/seed_sprint1.py"],
        "start": ["up", "-d", "--no-build", "--wait", "--wait-timeout", "180"],
        "stop": ["stop", "proxy", "frontend", "tutor-api", "llm-gateway", "redis"],
    }
    if action in {"migrate", "seed"}:
        active = run(COMPOSE + ["ps", "--services", "--status", "running"]).split()
        require(set(active) <= {"db"}, "Stop application before migration/seed")
    if action in commands:
        run(COMPOSE + commands[action], False)
    elif action == "smoke":
        for service, port, paths in [("tutor-api", 8000, ["health", "ready"]),
                                     ("llm-gateway", 8001, ["health", "ready"])]:
            for path in paths:
                run(COMPOSE + ["exec", "-T", service, "python", "-c",
                    "import urllib.request; "
                    f"urllib.request.urlopen('http://localhost:{port}/{path}', timeout=5)"], False)
                print(f"PASS {service}/{path}")
        for path in ["healthz", "backend-health", "", "login", "learn", "parent"]:
            run(COMPOSE + ["exec", "-T", "frontend", "wget", "-q", "-O", "/dev/null",
                           f"http://localhost:8080/{path}"], False)
            print(f"PASS frontend/{path}")
        print("Internal smoke PASS; TLS/browser/gateway rendering require Muse validation.")
    elif action == "metrics":
        ids = run(COMPOSE + ["ps", "-q"]).split()
        require(bool(ids), "No running staging containers")
        run(DOCKER + ["stats", "--no-stream", *ids], False)
        run(DOCKER + ["inspect", "--format",
            "{{.Name}} OOM={{.State.OOMKilled}} restarts={{.RestartCount}} image={{.Image}}",
            *ids], False)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as error:
        # Never print command/environment dumps containing credentials.
        print(f"STOP: {error if isinstance(error, RuntimeError) else type(error).__name__}",
              file=sys.stderr)
        sys.exit(1)
