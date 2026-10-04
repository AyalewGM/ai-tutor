"""Grant, revoke, or reset staff (admin) access. Operator-only.

Usage (inside the tutor-api container):
    python scripts/ops/make_admin.py admin@example.com            # grant (creates the account if new)
    python scripts/ops/make_admin.py admin@example.com --reset-mfa
    python scripts/ops/make_admin.py admin@example.com --revoke

Use a dedicated staff email. Family (parent) accounts are refused: staff and
family access are deliberately separate identities. Passwords are prompted,
never passed on the command line. Every change is written to the admin audit log.

Roles: ADMIN (everything), SUPPORT (family approval queue), ANALYST
(read-only metrics + AI usage). Grant with --role SUPPORT or --role ANALYST;
re-running with a different --role changes the role.
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
from app.services.permissions import STAFF_ROLES

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


def grant(email: str, role: str = ADMIN_ROLE) -> None:
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
            user = User(email=email, display_name="Mihur Staff", role=role)
            db.add(user)
            db.flush()
            db.add(UserCredential(user_id=user.id, password_hash=PasswordHasher().hash(password)))
            before = None
        else:
            before = {"role": user.role}
            user.role = role
        record_admin_action(
            db, actor_user_id=None, actor_label=CLI_ACTOR, action="staff.role_granted",
            target_type="user", target_id=str(user.id), before=before, after={"role": role},
        )
        db.commit()


def reset_mfa(email: str) -> None:
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


def revoke(email: str) -> None:
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("email")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--revoke", action="store_true", help="remove staff access")
    group.add_argument("--reset-mfa", action="store_true", help="clear the two-factor enrollment")
    parser.add_argument(
        "--role", default=ADMIN_ROLE, choices=sorted(STAFF_ROLES),
        help="staff role to grant (default: ADMIN)",
    )
    args = parser.parse_args()
    email = args.email.strip().lower()
    # Status lines are built here from the email alone — nothing returned by
    # a function that handled credentials is ever printed.
    if args.revoke:
        revoke(email)
        print(f"Staff access revoked for {email}; all sessions signed out.")
    elif args.reset_mfa:
        reset_mfa(email)
        print(f"Two-factor cleared for {email}. They must enroll again on next sign-in.")
    else:
        grant(email, role=args.role)
        print(f"{email} is now {args.role}. Sign in, then enroll two-factor at /admin.")


if __name__ == "__main__":
    main()
