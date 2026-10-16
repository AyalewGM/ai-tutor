"""Run a local two-browser check against synthetic, in-memory family data.

Requires backend dev dependencies, frontend npm ci, e2e npm ci, and Chromium.
Never points at a real account or deployment. Both servers are local subprocesses.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def serve(config_path):
    import pytest
    import uvicorn

    from app.auth import SESSION_COOKIE
    from tests.test_collaboration import create_board, family

    patches = pytest.MonkeyPatch()
    fixture = family.__wrapped__(patches)
    client, _factory, child, *_ = next(fixture)
    path = create_board(client, child)
    Path(config_path).write_text(
        json.dumps({"board": path.rsplit("/", 1)[-1], "parent": client.cookies.get(SESSION_COOKIE)})
    )
    try:
        uvicorn.run(client.app, host="127.0.0.1", port=8002, log_level="warning")
    finally:
        fixture.close()
        patches.undo()


def run():
    with tempfile.TemporaryDirectory(prefix="mihur-together-") as temporary:
        config = str(Path(temporary) / "family.json")
        with open(Path(temporary) / "servers.log", "w+") as log:
            backend = subprocess.Popen(
                [sys.executable, __file__, "--serve", config], cwd=ROOT, stdout=log, stderr=log
            )
            frontend = subprocess.Popen(
                [
                    "npm",
                    "run",
                    "dev",
                    "--prefix",
                    "frontend",
                    "--",
                    "--host",
                    "127.0.0.1",
                    "--strictPort",
                ],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            try:
                for _ in range(80):
                    if backend.poll() is not None or frontend.poll() is not None:
                        raise RuntimeError("A test server exited before becoming ready")
                    try:
                        urllib.request.urlopen("http://127.0.0.1:5173", timeout=1).close()
                        urllib.request.urlopen("http://127.0.0.1:8002/docs", timeout=1).close()
                        break
                    except OSError:
                        time.sleep(0.25)
                else:
                    raise RuntimeError("Test servers did not become ready")
                return subprocess.run(
                    ["node", "e2e/learn-together-browser.cjs"],
                    cwd=ROOT,
                    env={**os.environ, "MIHUR_TOGETHER_FIXTURE": config},
                    timeout=100,
                    check=False,
                ).returncode
            finally:
                backend.terminate()
                os.killpg(frontend.pid, 15)
                backend.wait(timeout=10)
                frontend.wait(timeout=10)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--serve":
        serve(sys.argv[2])
    else:
        raise SystemExit(run())
