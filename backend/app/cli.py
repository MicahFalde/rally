"""CLI for Rally administrative tasks.

Usage:
    python -m app.cli import-voters --state OH --file /path/to/voters.csv [--geocode]
    python -m app.cli create-admin --email admin@example.com --password secret --name "Admin User"
"""
import argparse
import asyncio
import sys

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_password
from app.models import PlatformRole, User
from app.services.voter_import import import_voter_file


async def cmd_import_voters(args):
    print(f"Importing voter file: {args.file} for state: {args.state}")
    async with async_session() as db:
        stats = await import_voter_file(
            db, args.file, args.state, geocode=args.geocode
        )
        print(f"Import complete: {stats}")


async def cmd_create_admin(args):
    async with async_session() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == args.email))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"User {args.email} already exists")
            sys.exit(1)

        user = User(
            email=args.email,
            hashed_password=hash_password(args.password),
            full_name=args.name,
            platform_role=PlatformRole.PLATFORM_ADMIN,
        )
        db.add(user)
        await db.commit()
        print(f"Created platform admin: {args.email} (id: {user.id})")


def main():
    parser = argparse.ArgumentParser(description="Rally CLI")
    subparsers = parser.add_subparsers(dest="command")

    # import-voters
    import_cmd = subparsers.add_parser("import-voters", help="Import a state voter file")
    import_cmd.add_argument("--state", required=True, help="Two-letter state code")
    import_cmd.add_argument("--file", required=True, help="Path to voter file")
    import_cmd.add_argument("--geocode", action="store_true", help="Geocode addresses via Geocodio")

    # create-admin
    admin_cmd = subparsers.add_parser("create-admin", help="Create a platform admin user")
    admin_cmd.add_argument("--email", required=True)
    admin_cmd.add_argument("--password", required=True)
    admin_cmd.add_argument("--name", required=True)

    args = parser.parse_args()

    if args.command == "import-voters":
        asyncio.run(cmd_import_voters(args))
    elif args.command == "create-admin":
        asyncio.run(cmd_create_admin(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
