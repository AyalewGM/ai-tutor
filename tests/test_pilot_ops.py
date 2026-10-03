"""Tests for F-026 operational-readiness artifacts."""

import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_pilot_compose_file_is_valid_yaml() -> None:
    """docker-compose.pilot.yml must be parseable YAML."""
    import yaml

    with open(REPO_ROOT / "docker-compose.pilot.yml") as f:
        doc = yaml.safe_load(f)
    assert "services" in doc
    assert "migrate" in doc["services"]
    assert "tutor-api" in doc["services"]
    assert "db" in doc["services"]


def test_pilot_compose_migrate_runs_alembic() -> None:
    """The migrate service must run alembic upgrade head."""
    import yaml

    with open(REPO_ROOT / "docker-compose.pilot.yml") as f:
        doc = yaml.safe_load(f)
    migrate = doc["services"]["migrate"]
    assert migrate["command"] == ["alembic", "upgrade", "head"]
    assert migrate["restart"] == "no"


def test_pilot_compose_uses_env_file() -> None:
    """Pilot services must read secrets from .env.pilot, not the repo."""
    import yaml

    with open(REPO_ROOT / "docker-compose.pilot.yml") as f:
        doc = yaml.safe_load(f)
    for name in ("db", "migrate", "tutor-api", "frontend"):
        assert doc["services"][name].get("env_file") == ".env.pilot"


def test_pilot_compose_log_rotation() -> None:
    """All services must have JSON log rotation configured."""
    import yaml

    with open(REPO_ROOT / "docker-compose.pilot.yml") as f:
        doc = yaml.safe_load(f)
    for name in ("db", "migrate", "llm-gateway", "tutor-api", "frontend"):
        logging_cfg = doc["services"][name].get("logging", {})
        assert logging_cfg.get("driver") == "json-file"
        options = logging_cfg.get("options", {})
        assert "max-size" in options
        assert "max-file" in options


def test_pilot_env_example_exists() -> None:
    """The pilot env template must exist and document required vars."""
    example = REPO_ROOT / ".env.pilot.example"
    assert example.exists()
    content = example.read_text()
    for var in ("POSTGRES_PASSWORD", "SESSION_COOKIE_SECURE", "LLM_GATEWAY_PROVIDER"):
        assert var in content


def test_ops_scripts_exist_and_are_executable() -> None:
    """All ops scripts must exist and have the executable bit."""
    scripts = [
        "scripts/ops/backup_db.sh",
        "scripts/ops/restore_db.sh",
        "scripts/ops/deploy.sh",
        "scripts/ops/smoke_test.sh",
    ]
    for script in scripts:
        path = REPO_ROOT / script
        assert path.exists(), f"Missing: {script}"
        assert path.stat().st_mode & stat.S_IXUSR, f"Not executable: {script}"


def test_provision_script_importable() -> None:
    """The provisioning script must import cleanly."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "provision_pilot_family",
        REPO_ROOT / "scripts/ops/provision_pilot_family.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)


def test_backup_script_syntax() -> None:
    """Shell scripts must parse without errors."""
    for script in ("backup_db.sh", "restore_db.sh", "deploy.sh", "smoke_test.sh"):
        result = subprocess.run(
            ["bash", "-n", str(REPO_ROOT / "scripts/ops" / script)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"{script}: {result.stderr}"


def test_runbook_exists_and_covers_scope() -> None:
    """The operator runbook must cover all required topics."""
    runbook = REPO_ROOT / "docs/operations/PILOT_DEPLOYMENT.md"
    assert runbook.exists()
    content = runbook.read_text().lower()
    for topic in ("deploy", "verify", "backup", "restore", "rollback", "troubleshoot", "restart"):
        assert topic in content, f"Runbook missing: {topic}"


def test_seed_all_curricula_steps_resolve() -> None:
    """Every orchestrator step must resolve to a module exposing seed()."""
    import importlib

    from scripts.ops.seed_all_curricula import STEPS

    assert len(STEPS) >= 10
    for module_name, label in STEPS:
        module = importlib.import_module(f"scripts.{module_name}")
        assert callable(getattr(module, "seed", None)), f"{module_name} lacks seed(): {label}"


def test_seed_all_curricula_list_flag_is_side_effect_free(capsys) -> None:
    """--list prints the plan without touching the database."""
    import sys

    from scripts.ops import seed_all_curricula

    argv = sys.argv
    try:
        sys.argv = ["seed_all_curricula.py", "--list"]
        assert seed_all_curricula.main() == 0
    finally:
        sys.argv = argv
    out = capsys.readouterr().out
    assert "seed_sprint1" in out and "seed_all_elementary_packs" in out


def test_dockerfile_ships_elementary_packs() -> None:
    """seed_all_elementary_packs reads docs/curriculum/packs at deploy time —
    the API image must copy it or the loader cannot run in production."""
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    assert "docs/curriculum/packs" in dockerfile


def test_deploy_script_seeds_curricula() -> None:
    """Deploy must run the orchestrator so authored content reaches the pilot."""
    deploy = (REPO_ROOT / "scripts/ops/deploy.sh").read_text()
    assert "seed_all_curricula" in deploy
    assert deploy.index("run --rm migrate") < deploy.index("seed_all_curricula")
