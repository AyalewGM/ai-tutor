"""Grant, revoke, or reset staff (admin) access. Operator-only.

Usage (inside the tutor-api container):
    python scripts/ops/make_admin.py admin@example.com            # grant (creates the account if new)
    python scripts/ops/make_admin.py admin@example.com --reset-mfa
    python scripts/ops/make_admin.py admin@example.com --revoke

Use a dedicated staff email. Family (parent) accounts are refused: staff and
family access are deliberately separate identities. Passwords are prompted,
never passed on the command line. Every change is written to the admin audit log.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from argon2 import PasswordHasher
from sqlalchemy import delete, func, select, update

from app.admin_models import AdminMfa
from app.auth_models import AuthSession
from app.core.database import SessionLocal
from app.credential_models import UserCredential
from app.models import User
from app.parent_models import ParentProfile
from app.services.admin_security import record_admin_action

ADMIN_ROLE = "ADMIN"
REVOKED_ROLE = "STAFF_REVOKED"
MIN_PASSWORD_LENGTH = 12
CLI_ACTOR = "operator-cli"


def _prompt_password() -> str:
    while True:
        first = getpass.getpass(f"New staff password (min {MIN_PASSWORD_LENGTH} chars): ")
        if len(first) < MIN_PASSWORD_LENGTH:
            print("Too short.", file=sys.stderr)
            continue
        if getpass.getpass("Repeat password: ") != first:
            print("Passwords do not match.", file=sys.stderr)
            continue
        return first


def grant(email: str) -> str:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(func.lower(User.email) == email))
        if user is not None and db.scalar(
            select(ParentProfile.id).where(ParentProfile.user_id == user.id)
        ):
            raise SystemExit(
                f"{email} is a family account. Use a separate staff email for admin access."
            )
        if user is None:
            password = _prompt_password()
            user = User(email=email, display_name="Mihur Staff", role=ADMIN_ROLE)
            db.add(user)
            db.flush()
            db.add(UserCredential(user_id=user.id, password_hash=PasswordHasher().hash(password)))
            before = None
        else:
            before = {"role": user.role}
            user.role = ADMIN_ROLE
        record_admin_action(
            db, actor_user_id=None, actor_label=CLI_ACTOR, action="staff.role_granted",
            target_type="user", target_id=str(user.id), before=before, after={"role": ADMIN_ROLE},
        )
        db.commit()
    return f"{email} is now an admin. Sign in, then enroll two-factor at /admin."


def reset_mfa(email: str) -> str:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(func.lower(User.email) == email))
        if user is None:
            raise SystemExit(f"No account for {email}")
        db.execute(delete(AdminMfa).where(AdminMfa.user_id == user.id))
        db.execute(
            update(AuthSession).where(AuthSession.user_id == user.id).values(mfa_verified_at=None)
        )
        record_admin_action(
            db, actor_user_id=None, actor_label=CLI_ACTOR, action="mfa.reset",
            target_type="user", target_id=str(user.id),
        )
        db.commit()
    return f"Two-factor reset for {email}. They must enroll again on next sign-in."


def revoke(email: str) -> str:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(func.lower(User.email) == email))
        if user is None:
            raise SystemExit(f"No account for {email}")
        before = {"role": user.role}
        user.role = REVOKED_ROLE
        db.execute(delete(AdminMfa).where(AdminMfa.user_id == user.id))
        db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
        record_admin_action(
            db, actor_user_id=None, actor_label=CLI_ACTOR, action="staff.role_revoked",
            target_type="user", target_id=str(user.id), before=before,
            after={"role": REVOKED_ROLE},
        )
        db.commit()
    return f"Staff access revoked for {email}; all sessions signed out."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("email")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--revoke", action="store_true", help="remove staff access")
    group.add_argument("--reset-mfa", action="store_true", help="clear the two-factor enrollment")
    args = parser.parse_args()
    email = args.email.strip().lower()
    if args.revoke:
        print(revoke(email))
    elif args.reset_mfa:
        print(reset_mfa(email))
    else:
        print(grant(email))


if __name__ == "__main__":
    main()
