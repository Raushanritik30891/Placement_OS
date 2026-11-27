"""Trusted-operator CLI for promoting or demoting a PlacementOS user.

Run only from an authenticated server/local development shell.
There is intentionally no public HTTP endpoint for role escalation.
"""
import argparse

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.entities import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage PlacementOS user roles")
    parser.add_argument("action", choices=["promote-admin", "demote-admin"])
    parser.add_argument("email", help="Existing account email address")
    args = parser.parse_args()

    email = args.email.strip().lower()
    if input(f"Type {args.action.upper()} to confirm role change for {email}: ").strip() != args.action.upper():
        raise SystemExit("Confirmation did not match; no changes made.")

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            raise SystemExit("No user found with that email.")
        user.role = "admin" if args.action == "promote-admin" else "student"
        db.commit()
        print(f"Updated {email}: role={user.role}")


if __name__ == "__main__":
    main()
