"""Container-side publisher. Host operator command supplies verified backup receipt."""
import argparse
import json
import sys

from sqlalchemy import text

from app.core.database import SessionLocal
from app.services import development_content_authorization as development
from app.services.content_publishing import (
    ROOT,
    authorize_package,
    candidates,
    publish,
    report,
    rollback,
    validate,
)

MANIFEST = ROOT / "content_packages/mth1w-signed-two-step-v1.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["dry-run", "publish", "rollback", "report"])
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    package_digest = validate(manifest, require_approvals=False)
    if args.action == "publish" and not development.configured():
        # Preserve the default six-signature rejection before receipt/DB access.
        package_digest = validate(manifest)
    if args.action == "dry-run":
        try:
            with SessionLocal() as db:
                authorize_package(manifest, db)
            authorization = "APPROVED"
        except ValueError as exc:
            authorization = str(exc)
        print(json.dumps({"package_digest": package_digest, "authorization": authorization,
                          "planned_questions": len(candidates(manifest)), "database_mutated": False,
                          "staging_learner_verified": False}))
        return
    receipt = json.load(sys.stdin) if args.action in {"publish", "rollback"} else None
    if receipt is not None and (
        receipt.get("restore_verified") is not True or receipt.get("preflight") is not True
        or receipt.get("package_digest") != package_digest
        or not receipt.get("backup_sha256") or not receipt.get("release_sha")
    ):
        raise ValueError("Verified host backup/preflight receipt required")
    with SessionLocal.begin() as db:
        if db.scalar(text("select current_database()")) != "mihur_staging":
            raise ValueError("Dedicated staging database required")
        # Serialize all publisher operations, including retries and rollback.
        db.execute(text("select pg_advisory_xact_lock(462001)"))
        if args.action == "publish":
            result = publish(db, manifest)
        elif args.action == "rollback":
            result = {"disabled": rollback(db, package_digest), "package_digest": package_digest}
        else:
            result = report(db, manifest)
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - redact operator errors
        # Never expose DSNs, SQL parameters, credentials or subprocess stderr.
        from app.services.content_publishing import PublicationBlocked
        message = str(exc) if isinstance(exc, PublicationBlocked) else type(exc).__name__
        print(json.dumps({"status": "BLOCKED", "reason": message,
                          "staging_learner_verified": False}), file=sys.stderr)
        sys.exit(1)
