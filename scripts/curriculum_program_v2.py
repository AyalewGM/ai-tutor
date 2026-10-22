"""V2 durable, source-gated curriculum work planner; no autonomous model calls.

Uses stdlib SQLite only for local prototype. Never assumes grades have a
single math course or generates source expectations from an LLM guess.
Only source-reviewed manifest entries become work units.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

_STATES = {"QUEUED", "IN_PROGRESS", "REVIEW_REQUIRED", "CHANGES_REQUIRED", "APPROVED"}
_ALLOWED = {
    "QUEUED": {"IN_PROGRESS"},
    "IN_PROGRESS": {"REVIEW_REQUIRED", "CHANGES_REQUIRED"},
    "REVIEW_REQUIRED": {"APPROVED", "CHANGES_REQUIRED"},
    "CHANGES_REQUIRED": {"IN_PROGRESS"},
    "APPROVED": set(),
}
_GOAL = re.compile(r"(?i)\bontario\b.*\b(?:math|mathematics)\b.*\bgrades?\s*(\d+)\s*(?:-|–|to|through)\s*(\d+)\b")


def parse_goal(text: str) -> dict:
    if not isinstance(text, str) or len(text) > 4000:
        raise ValueError("invalid natural language goal")
    normalized = " ".join(text.split())
    m = _GOAL.search(normalized)
    if not m:
        raise ValueError("unrecognized goal; require explicit Ontario mathematics Grades X–Y")
    start, end = map(int, m.groups())
    if not 1 <= start <= end <= 12:
        raise ValueError("Ontario grade range must be 1–12")
    return {"jurisdiction": "Ontario", "subject": "Mathematics",
            "grades": list(range(start, end + 1)),
            "goal_text": normalized, "curriculum_source_status": "UNVERIFIED"}


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS programs (
          id TEXT PRIMARY KEY, goal_json TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS work_items (
          id TEXT PRIMARY KEY,
          program_id TEXT NOT NULL REFERENCES programs(id),
          grade INTEGER NOT NULL,
          course_code TEXT NOT NULL,
          expectation_code TEXT NOT NULL,
          approved_source_url TEXT NOT NULL,
          source_version TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'QUEUED',
          version INTEGER NOT NULL DEFAULT 0,
          UNIQUE(program_id,grade,course_code,expectation_code,source_version)
        );
        CREATE TABLE IF NOT EXISTS worker_leases (
          work_id TEXT PRIMARY KEY REFERENCES work_items(id),
          owner TEXT NOT NULL,
          fencing_token INTEGER NOT NULL,
          expires_at INTEGER NOT NULL,
          attempt_count INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          work_id TEXT NOT NULL REFERENCES work_items(id),
          old_status TEXT NOT NULL,
          new_status TEXT NOT NULL,
          actor TEXT NOT NULL,
          evidence_ref TEXT NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    return db


def _identity(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:24]


def register_goal(db: sqlite3.Connection, text: str) -> dict:
    goal = parse_goal(text)
    program_id = "program-" + _identity(goal["jurisdiction"], goal["subject"], str(goal["grades"]))
    db.execute("INSERT OR IGNORE INTO programs(id,goal_json) VALUES(?,?)",
               (program_id, json.dumps(goal, sort_keys=True)))
    db.commit()
    return {"program_id": program_id, "goal": goal,
            "state": "AWAITING_OFFICIAL_SOURCE_INVENTORY",
            "work_items": count_items(db, program_id)}


def count_items(db: sqlite3.Connection, program_id: str) -> int:
    return db.execute("SELECT COUNT(*) FROM work_items WHERE program_id=?",
                      (program_id,)).fetchone()[0]


def import_manifest(db: sqlite3.Connection, program_id: str, manifest: dict) -> dict:
    """Only separately source-reviewed curriculum identifiers are accepted."""
    record = db.execute("SELECT goal_json FROM programs WHERE id=?", (program_id,)).fetchone()
    if not record:
        raise ValueError("unknown program")
    goal = json.loads(record[0])
    if manifest.get("verification_state") != "SOURCE_REVIEWED":
        raise PermissionError("manifest lacks source-review gate")
    reviewer = manifest.get("reviewer_identity")
    evidence = manifest.get("review_evidence_url")
    if not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(evidence, str) or not evidence.startswith("https://"):
        raise ValueError("source review identity/evidence required")
    items = manifest.get("expectations")
    if not isinstance(items, list) or not items:
        raise ValueError("nonempty official expectation inventory required")
    validated = []
    for item in items:
        if not isinstance(item, dict):
            raise TypeError("invalid expectation")
        grade = item.get("grade")
        code = item.get("expectation_code")
        course = item.get("course_code")
        version = item.get("source_version")
        url = item.get("official_source_url")
        if (type(grade) is not int or grade not in goal["grades"]
                or not all(isinstance(x, str) and 1 <= len(x) <= 120
                           for x in [code, course, version])
                or not isinstance(url, str) or not url.startswith("https://")):
            raise ValueError("unsupported or unverified expectation metadata")
        item_id = "unit-" + _identity(program_id, str(grade), course, code, version)
        validated.append((item_id, program_id, grade, course, code, url, version))
    with db:
        db.executemany("""INSERT OR IGNORE INTO work_items
            (id,program_id,grade,course_code,expectation_code,approved_source_url,source_version)
            VALUES(?,?,?,?,?,?,?)""", validated)
    return {"program_id": program_id, "submitted": len(validated),
            "total": count_items(db, program_id), "execution": "NOT_STARTED",
            "approval_authority": "NONE"}


def next_task(db: sqlite3.Connection, program_id: str) -> dict | None:
    row = db.execute("""SELECT id,grade,course_code,expectation_code,source_version
      FROM work_items WHERE program_id=? AND status='QUEUED'
      ORDER BY grade,course_code,expectation_code LIMIT 1""",
                     (program_id,)).fetchone()
    if row is None:
        return None
    return dict(zip(["id", "grade", "course_code", "expectation_code", "source_version"], row))


def transition(db: sqlite3.Connection, item_id: str, status: str,
               actor: str, evidence_ref: str, expected_version: int) -> dict:
    if status not in _STATES or not isinstance(actor, str) or not actor.strip():
        raise ValueError("invalid transition")
    if not isinstance(evidence_ref, str) or not evidence_ref.startswith("https://"):
        raise ValueError("auditable evidence URL required")
    if type(expected_version) is not int or expected_version < 0:
        raise ValueError("invalid expected version")
    with db:
        row = db.execute("SELECT status,version FROM work_items WHERE id=?", (item_id,)).fetchone()
        if row is None:
            raise ValueError("unknown unit")
        old, version = row
        if version != expected_version or status not in _ALLOWED[old]:
            raise ValueError("invalid or stale state transition")
        db.execute("UPDATE work_items SET status=?,version=version+1 WHERE id=?",
                   (status, item_id))
        db.execute("""INSERT INTO audit_events(work_id,old_status,new_status,actor,evidence_ref)
                      VALUES(?,?,?,?,?)""", (item_id, old, status, actor, evidence_ref))
    return {"id": item_id, "from": old, "to": status, "version": version + 1,
            "content_runtime_activated": False}




def claim_next(db: sqlite3.Connection, program_id: str, owner: str,
               now_epoch: int, ttl_seconds: int = 300,
               max_attempts: int = 3) -> dict | None:
    """Atomically claim eligible queued work (offline SQLite prototype only).

    Lease token monotonically increases across retries; a stale worker cannot
    complete work using an earlier token. This is not a distributed PG worker.
    """
    if (not isinstance(owner, str) or not owner.strip() or len(owner) > 120
            or type(now_epoch) is not int or now_epoch < 0
            or type(ttl_seconds) is not int or not 30 <= ttl_seconds <= 3600
            or type(max_attempts) is not int or not 1 <= max_attempts <= 20):
        raise ValueError("invalid lease request")
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute("""
          SELECT w.id, l.fencing_token, l.attempt_count
          FROM work_items w LEFT JOIN worker_leases l ON l.work_id=w.id
          WHERE w.program_id=? AND w.status='QUEUED'
            AND (l.work_id IS NULL OR l.expires_at <= ?)
            AND (l.work_id IS NULL OR l.attempt_count < ?)
          ORDER BY w.grade,w.course_code,w.expectation_code LIMIT 1
        """, (program_id, now_epoch, max_attempts)).fetchone()
        if row is None:
            db.commit()
            return None
        work_id, old_token, attempts = row
        token = (old_token or 0) + 1
        db.execute("""
          INSERT INTO worker_leases(work_id,owner,fencing_token,expires_at,attempt_count)
          VALUES(?,?,?,?,?)
          ON CONFLICT(work_id) DO UPDATE SET
            owner=excluded.owner, fencing_token=excluded.fencing_token,
            expires_at=excluded.expires_at, attempt_count=excluded.attempt_count
        """, (work_id, owner, token, now_epoch + ttl_seconds, (attempts or 0) + 1))
        db.commit()
        return {"work_id": work_id, "owner": owner, "fencing_token": token,
                "expires_at": now_epoch + ttl_seconds, "attempt": (attempts or 0) + 1,
                "worker_invoked": False}
    except BaseException:
        db.rollback()
        raise


def complete_claim(db: sqlite3.Connection, work_id: str, owner: str,
                   fencing_token: int, now_epoch: int,
                   *, evidence_ref: str) -> dict:
    """Fence stale workers; stage only for review, never approve or release."""
    if (not isinstance(owner, str) or not owner.strip()
            or type(fencing_token) is not int or fencing_token < 1
            or type(now_epoch) is not int or now_epoch < 0
            or not isinstance(evidence_ref, str)
            or not evidence_ref.startswith("https://")):
        raise ValueError("invalid completion evidence")
    db.execute("BEGIN IMMEDIATE")
    try:
        lease = db.execute("""SELECT owner,fencing_token,expires_at
            FROM worker_leases WHERE work_id=?""", (work_id,)).fetchone()
        current = db.execute("SELECT status,version FROM work_items WHERE id=?",
                             (work_id,)).fetchone()
        if (lease is None or current is None or lease[0] != owner
                or lease[1] != fencing_token or lease[2] <= now_epoch
                or current[0] != "QUEUED"):
            raise ValueError("stale, expired or unauthorized claim")
        db.execute("""UPDATE work_items
            SET status='REVIEW_REQUIRED',version=version+1 WHERE id=?""", (work_id,))
        db.execute("""INSERT INTO audit_events(work_id,old_status,new_status,actor,evidence_ref)
            VALUES(?,?,?,?,?)""", (work_id, "QUEUED", "REVIEW_REQUIRED",
                                   owner, evidence_ref))
        db.execute("DELETE FROM worker_leases WHERE work_id=?", (work_id,))
        db.commit()
        return {"work_id": work_id, "status": "REVIEW_REQUIRED",
                "review_accepted": False, "release_authority": "NONE"}
    except BaseException:
        db.rollback()
        raise

def main() -> None:
    p = argparse.ArgumentParser(description="Mihur V2 durable curriculum-planning slice")
    p.add_argument("--database", type=Path, required=True)
    sub = p.add_subparsers(dest="command", required=True)
    make = sub.add_parser("goal")
    make.add_argument("description")
    imp = sub.add_parser("import-source-manifest")
    imp.add_argument("--program-id", required=True)
    imp.add_argument("--manifest", type=Path, required=True)
    nxt = sub.add_parser("next")
    nxt.add_argument("--program-id", required=True)
    args = p.parse_args()
    with connect(args.database) as db:
        if args.command == "goal":
            result = register_goal(db, args.description)
        elif args.command == "import-source-manifest":
            result = import_manifest(db, args.program_id,
                                     json.loads(args.manifest.read_text()))
        else:
            result = next_task(db, args.program_id)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
