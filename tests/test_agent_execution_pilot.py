"""Isolated Phase 2 state-machine regression tests."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location(
    "pilot", Path(__file__).resolve().parents[1] / "scripts" / "agent_execution_pilot.py"
)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
SHA = "a" * 40

def store(tmp_path):
    return pilot.Store(str(tmp_path / "state.db"))

def test_exact_sha_dedup_and_sequential_roles(tmp_path):
    s = store(tmp_path)
    tid = s.enqueue(385, SHA, "content")
    assert tid == s.enqueue(385, SHA, "content")
    assert s.claim("math", "other") is None
    row = s.claim("content", "author")
    assert row[0] == tid
    assert s.claim("content", "racer") is None
    assert s.finish(tid, "author", "ACCEPT", "author output", SHA) == "accepted"
    assert s.claim("math", "reviewer")[0].endswith(":math")
    assert s.db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 2

def test_stale_sha_blocks_dispatch(tmp_path):
    s = store(tmp_path)
    tid = s.enqueue(385, SHA, "content")
    s.claim("content", "author")
    assert s.finish(tid, "author", "ACCEPT", "evidence", "b" * 40) == "stale"
    assert s.claim("math", "reviewer") is None

def test_correction_does_not_autopass(tmp_path):
    s = store(tmp_path)
    tid = s.enqueue(385, SHA, "content")
    s.claim("content", "author")
    s.finish(tid, "author", "CHANGES_REQUIRED", "fix needed", SHA)
    assert s.claim("math", "reviewer") is None

def test_cannot_forge_owner_or_verdict(tmp_path):
    s = store(tmp_path)
    tid = s.enqueue(385, SHA, "content")
    s.claim("content", "author")
    with pytest.raises(ValueError):
        s.finish(tid, "other", "ACCEPT", "proof", SHA)
    with pytest.raises(ValueError):
        s.finish(tid, "author", "APPROVE", "proof", SHA)
    with pytest.raises(ValueError):
        s.finish(tid, "author", "ACCEPT", "", SHA)

def test_expired_lease_recovers_at_most_three_attempts(tmp_path):
    s = store(tmp_path)
    tid = s.enqueue(385, SHA, "content")
    for idx in range(3):
        row = s.claim("content", f"worker-{idx}", ttl=1)
        assert row is not None
        s.db.execute("UPDATE tasks SET lease_until=0 WHERE id=?", (tid,))
    assert s.claim("content", "fourth") is None

def test_invalid_sha_rejected(tmp_path):
    s = store(tmp_path)
    with pytest.raises(ValueError):
        s.enqueue(12, "not-a-sha", "content")
