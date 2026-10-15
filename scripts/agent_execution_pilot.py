"""Phase 2 isolated pilot: durable tasks, explicit runner registry, no AI credentials.

No merges, approvals, deployments, taxonomy or learner-state writes.
Only a pre-authorized adapter can execute a role. Demo adapter is inert.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time

ROLES = ("content", "math", "pedagogy", "engineering")
TRANSITIONS = {"content": "math", "math": "pedagogy", "pedagogy": "engineering"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
 id TEXT PRIMARY KEY, pr INTEGER NOT NULL, sha TEXT NOT NULL,
 role TEXT NOT NULL, status TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0,
 lease_until REAL, worker TEXT, evidence TEXT, updated REAL NOT NULL,
 UNIQUE(pr, sha, role)
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, event TEXT NOT NULL,
 detail TEXT NOT NULL, created REAL NOT NULL
);
"""

class Store:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript(SCHEMA)

    def event(self, tid: str, name: str, detail: str):
        self.db.execute("INSERT INTO events(task_id,event,detail,created) VALUES(?,?,?,?)",
                        (tid, name, detail, time.time()))

    def enqueue(self, pr: int, sha: str, role: str) -> str:
        if pr <= 0 or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            raise ValueError("Invalid PR/SHA")
        if role not in ROLES:
            raise ValueError("Unknown role")
        tid = f"{pr}:{sha}:{role}"
        self.db.execute("INSERT OR IGNORE INTO tasks(id,pr,sha,role,status,updated) VALUES(?,?,?,?,?,?)",
                        (tid, pr, sha, role, "queued", time.time()))
        return tid

    def claim(self, role: str, worker: str, ttl: int = 120):
        if not worker or ttl <= 0 or role not in ROLES:
            raise ValueError("Invalid lease")
        now = time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                """SELECT id,pr,sha,attempt FROM tasks WHERE role=?
                   AND (status='queued' OR (status='running' AND lease_until<?))
                   AND attempt<3 ORDER BY updated LIMIT 1""", (role, now)).fetchone()
            if row:
                self.db.execute(
                    """UPDATE tasks SET status='running',attempt=attempt+1,
                       lease_until=?,worker=?,updated=? WHERE id=?""",
                    (now + ttl, worker, now, row[0]))
            self.db.execute("COMMIT")
            return row
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def finish(self, tid: str, worker: str, verdict: str, evidence: str, live_sha: str):
        if verdict not in {"ACCEPT", "CHANGES_REQUIRED"} or not evidence.strip():
            raise ValueError("Explicit evidence and verdict required")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT pr,sha,role,status,worker,lease_until FROM tasks WHERE id=?",
                (tid,)).fetchone()
            if not row or row[3] != "running" or row[4] != worker or row[5] <= time.time():
                raise ValueError("Missing or expired ownership lease")
            if row[1] != live_sha:
                self.db.execute("UPDATE tasks SET status='stale',updated=? WHERE id=?",
                                (time.time(), tid))
                self.event(tid, "STALE", live_sha)
                self.db.execute("COMMIT")
                return "stale"
            status = "accepted" if verdict == "ACCEPT" else "changes_required"
            self.db.execute(
                "UPDATE tasks SET status=?,evidence=?,lease_until=NULL,updated=? WHERE id=?",
                (status, evidence, time.time(), tid))
            self.event(tid, verdict, evidence)
            if verdict == "ACCEPT" and row[2] in TRANSITIONS:
                # Next reviewer receives a task; the original author never approves themselves.
                self.enqueue(row[0], row[1], TRANSITIONS[row[2]])
            if verdict == "CHANGES_REQUIRED":
                # Corrections return to content author. A new review requires fresh SHA.
                self.event(tid, "RETURN_TO_AUTHOR", "Correction required at new commit SHA")
            self.db.execute("COMMIT")
            return status
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

def demo_adapter(role: str, pr: int, sha: str) -> tuple[str, str]:
    """Deterministic test adapter, NOT an AI agent or independent review."""
    return "ACCEPT", json.dumps({"mode": "simulation", "role": role, "pr": pr, "sha": sha})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="mihur-phase2-pilot.sqlite3")
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--demo", action="store_true", help="run inert simulation only")
    args = parser.parse_args()
    if not args.demo:
        parser.error("No real agent runner authorized; --demo is required")
    store = Store(args.db)
    store.enqueue(args.pr, args.sha, "content")
    for role in ROLES:
        row = store.claim(role, worker="demo-" + role)
        if row is None:
            break
        verdict, evidence = demo_adapter(role, row[1], row[2])
        store.finish(row[0], "demo-" + role, verdict, evidence, live_sha=args.sha)
    rows = store.db.execute("SELECT role,status,evidence FROM tasks ORDER BY updated").fetchall()
    print(json.dumps({"simulation_only": True, "tasks": rows}, indent=2))

if __name__ == "__main__":
    main()
