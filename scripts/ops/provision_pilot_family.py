"""F-026: Provision a pilot family (parent + learner) for the private pilot.

This script is run by the operator on the VPS. It does NOT accept command-line
secrets — it prompts interactively or reads from stdin.

Usage:
    python scripts/ops/provision_pilot_family.py

The script will:
1. Prompt for parent email and display name.
2. Generate a secure temporary password (or accept one).
3. Prompt for learner first name and curriculum.
4. Create the parent user, credential, and parent profile.
5. Create the learner and link them via ParentStudentRelationship.
6. Print credentials once — they are not stored in plaintext.
7. Optionally print a claim token for the learner to link to the parent.

After running, give the parent the email and temporary password. They should
change the password on first login.
"""

from __future__ import annotations

import secrets
import sys
import uuid

from argon2 import PasswordHasher
from sqlalchemy import select

from app.core.database import SessionLocal
from app.credential_models import UserCredential
from app.models import Curriculum, Student, User
from app.parent_models import ParentProfile, ParentStudentRelationship
from app.services.child_link_claims import issue_child_link_claim

_passwords = PasswordHasher()


def _prompt(msg: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{msg}{suffix}: ").strip()
    return value or default or ""


def _list_curricula() -> list[tuple[uuid.UUID, str, str | None, str | None]]:
    with SessionLocal() as db:
        rows = db.scalars(select(Curriculum).where(Curriculum.active)).all()
        return [(c.id, c.code, c.jurisdiction, c.grade_level) for c in rows]


def _pick_curriculum() -> uuid.UUID:
    curricula = _list_curricula()
    if not curricula:
        print("No active curricula found. Run seed scripts first.", file=sys.stderr)
        sys.exit(1)
    print("\nAvailable curricula:")
    for i, (cid, code, jurisdiction, grade) in enumerate(curricula, 1):
        grade_str = f"Grade {grade}" if grade else "—"
        jur_str = jurisdiction or "—"
        print(f"  {i}. {code} ({jur_str}, {grade_str})")
    choice = _prompt("Select curriculum number", "1")
    try:
        idx = int(choice) - 1
        return curricula[idx][0]
    except (ValueError, IndexError):
        print("Invalid selection.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    print("=== Pilot Family Provisioning ===")
    print("This tool creates a parent account and learner profile.")
    print("Do NOT use real learner names in tests; use synthetic data.\n")

    parent_email = _prompt("Parent email").lower()
    if not parent_email or "@" not in parent_email:
        print("Valid email is required.", file=sys.stderr)
        sys.exit(1)

    parent_name = _prompt("Parent display name", parent_email.split("@")[0])
    temp_password = secrets.token_urlsafe(16)
    print(f"\nGenerated temporary password: {temp_password}")
    print("(The parent should change this on first login.)\n")

    learner_name = _prompt("Learner first name")
    curriculum_id = _pick_curriculum()

    link_token = None
    if _prompt("Generate child link claim token? (y/n)", "n").lower().startswith("y"):
        link_token = "pending"

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == parent_email))
        if existing:
            print(f"Parent account already exists: {existing.id}", file=sys.stderr)
            sys.exit(1)

        user = User(email=parent_email, display_name=parent_name, role="PARENT")
        db.add(user)
        db.flush()

        credential = UserCredential(
            user_id=user.id,
            password_hash=_passwords.hash(temp_password),
        )
        db.add(credential)

        profile = ParentProfile(user_id=user.id)
        db.add(profile)
        db.flush()

        curriculum = db.get(Curriculum, curriculum_id)
        student = Student(
            parent_id=user.id,
            curriculum_id=curriculum_id,
            first_name=learner_name,
            grade_level=curriculum.grade_level if curriculum else "UNSPECIFIED",
            school_system=None,
        )
        db.add(student)
        db.flush()

        rel = ParentStudentRelationship(
            parent_profile_id=profile.id,
            student_id=student.id,
            relationship_type="GUARDIAN",
            active=True,
        )
        db.add(rel)
        db.flush()

        db.commit()

        print("\n=== Provisioning complete ===")
        print(f"Parent user ID:    {user.id}")
        print(f"Parent email:      {parent_email}")
        print(f"Learner ID:        {student.id}")
        print(f"Learner name:      {learner_name}")
        print(f"Curriculum:        {curriculum.code if curriculum else '—'}")

        if link_token == "pending":
            token = issue_child_link_claim(db, student_id=student.id, lifetime_minutes=60)
            db.commit()
            print(f"\nChild link claim token (expires in 60 min): {token}")
            print("Share this token securely with the parent to link the learner.")

        print("\nNext steps:")
        print("1. Share the email + temporary password with the parent.")
        print("2. Parent logs in at /login and changes their password.")
        print("3. If a claim token was issued, parent uses it to link the child.")
        print("4. Run smoke tests: ./scripts/ops/smoke_test.sh")


if __name__ == "__main__":
    main()
